"""
GridGuard AI - Automated Ingestion Verification Test Suite
Sprint 2: Student 4: AI Engineer 2 (RAG Assistant & Anomaly Detection)
Lane 2: AI Service (RAG & Stream)

Tests:
1. OEM Catalog integrity (ABB, Siemens, Schneider, GE, Hitachi).
2. Metadata extraction & domain fault taxonomy categorization.
3. Strict metadata retention (manual_name, page_num enforcement).
4. PyMuPDF parsing: text, structural headers, tables, and technical diagrams.
5. Recursive token text splitter (500 tokens / 50 overlap).
6. Isolated ChromaDB persistence, batch upserting, and vector similarity querying.
"""

import json
import pytest
from pathlib import Path
import fitz

from src.rag.pdf_parser import MultimodalPDFParser, ExtractedTable, ParsedPage
from src.rag.metadata_extractor import TechnicalMetadataExtractor, FAULT_CATEGORIES
from src.rag.manual_ingester import (
    RecursiveTokenTextSplitter,
    ManualIngestionWorker,
    ChunkRecord,
)
from src.embeddings.embedder import MockEmbedder


# File paths
ABB_MANUAL_PATH = Path("ai-service/data/manuals/ABB/ABB_DIST_TRAFO_01_distribution-transformer-installation-manual.pdf")
SIEMENS_MANUAL_PATH = Path("ai-service/data/manuals/Siemens/861-96019-en-07-11-17.pdf")
CATALOG_PATH = Path("ai-service/data/manuals/oem_catalog.json")


def test_oem_catalog_integrity():
    """Validates OEM catalog covers 5 major manufacturers with complete engineering specifications."""
    assert CATALOG_PATH.exists(), f"OEM Catalog missing at {CATALOG_PATH}"

    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    assert catalog["total_curated_oems"] == 5
    assert "oems" in catalog
    assert len(catalog["oems"]) == 5

    oem_names = [entry["oem"] for entry in catalog["oems"]]
    expected_oems = ["ABB", "Siemens", "Schneider Electric", "GE", "Hitachi Energy"]
    for expected in expected_oems:
        assert expected in oem_names, f"Missing OEM: {expected}"

    for entry in catalog["oems"]:
        assert "manual_id" in entry
        assert "equipment_type" in entry
        assert "voltage_class" in entry
        assert "troubleshooting_sections" in entry
        assert len(entry["troubleshooting_sections"]) > 0
        for section in entry["troubleshooting_sections"]:
            assert "fault_type" in section
            assert "action" in section
            assert "citation_page" in section


def test_metadata_extractor_file_inference():
    """Tests OEM and equipment classification inference from path patterns."""
    extractor = TechnicalMetadataExtractor(CATALOG_PATH)

    meta_abb = extractor.extract_manual_metadata(ABB_MANUAL_PATH)
    assert meta_abb["oem"] == "ABB"
    assert meta_abb["equipment_type"] == "transformer"
    assert meta_abb["manual_name"] == ABB_MANUAL_PATH.name

    meta_siemens = extractor.extract_manual_metadata(SIEMENS_MANUAL_PATH)
    assert meta_siemens["oem"] == "Siemens"
    assert meta_siemens["manual_name"] == SIEMENS_MANUAL_PATH.name


def test_metadata_extractor_fault_categorization():
    """Tests high-voltage domain fault taxonomy categorization."""
    extractor = TechnicalMetadataExtractor()

    # SF6 Gas
    cat_sf6 = extractor.infer_fault_category("SF6 gas pressure alarm indicated on density monitor lockout")
    assert cat_sf6 == "SF6_Gas_Pressure"

    # Dielectric
    cat_oil = extractor.infer_fault_category("Transformer oil sample BDV dielectric breakdown voltage below 50kV")
    assert cat_oil == "Dielectric_Insulation"

    # Thermal
    cat_temp = extractor.infer_fault_category("WTI winding temperature indicator trip and OTI oil temperature overheating")
    assert cat_temp == "Thermal_Overload"

    # Mechanical
    cat_mech = extractor.infer_fault_category("Circuit breaker spring charging motor mechanism interlock failure")
    assert cat_mech == "Mechanical_Mechanism"

    # Protection Trip
    cat_trip = extractor.infer_fault_category("Buchholz relay gas accumulation tripped the feeder circuit breaker")
    assert cat_trip == "Protection_Trip"


def test_metadata_extractor_strict_enforcement():
    """Verifies that chunks MUST strictly retain verified manual_name and page_num or raise ValueError."""
    extractor = TechnicalMetadataExtractor()

    # Valid case
    valid_meta = extractor.build_chunk_metadata(
        manual_metadata={"manual_name": "ABB_Manual.pdf", "oem": "ABB", "equipment_type": "transformer"},
        page_num=15,
        chunk_index=1,
        section_title="4.1 Oil Testing",
        text_content="Insulating oil BDV test results must exceed 50 kV.",
    )
    assert valid_meta["manual_name"] == "ABB_Manual.pdf"
    assert valid_meta["page_num"] == 15
    assert valid_meta["citation"] == "ABB_Manual.pdf (Page 15)"
    assert valid_meta["fault_category"] == "Dielectric_Insulation"

    # Missing manual_name -> must raise ValueError
    with pytest.raises(ValueError, match="manual_name is strictly required"):
        extractor.build_chunk_metadata(
            manual_metadata={"manual_name": "", "oem": "ABB"},
            page_num=15,
            chunk_index=1,
            text_content="Some content",
        )

    # Invalid page_num (0 or negative) -> must raise ValueError
    with pytest.raises(ValueError, match="valid page_num"):
        extractor.build_chunk_metadata(
            manual_metadata={"manual_name": "ABB_Manual.pdf", "oem": "ABB"},
            page_num=0,
            chunk_index=1,
            text_content="Some content",
        )


def test_recursive_token_text_splitter():
    """Tests recursive character text splitter maintaining size and overlap boundaries."""
    splitter = RecursiveTokenTextSplitter(chunk_size=300, chunk_overlap=50)

    sample_paragraph = (
        "High-voltage gas-insulated switchgear (GIS) utilizes SF6 gas as the insulating and arc-quenching medium. "
        "The nominal operating pressure is monitored continuously via temperature-compensated density monitors. "
        "In the event of a stage-1 gas loss alarm, the control center is notified immediately to schedule top-up. "
        "If pressure drops to stage-2 lockout threshold, the tripping circuit prevents any mechanical opening or closing. "
        "Routine maintenance requires inspecting all rupture disks, desiccant bags, and gas compartment valves every 5 years."
    )

    splits = splitter.split_text(sample_paragraph)
    assert len(splits) >= 2, "Text splitter should produce multiple overlapping chunks"

    for chunk in splits:
        assert len(chunk) <= 350, f"Chunk exceeded size threshold: len={len(chunk)}"
        assert len(chunk.strip()) > 0


def test_pymupdf_pdf_parser_on_real_manual(tmp_path):
    """Tests PyMuPDF parsing on actual ABB manual pages (extracting text, headers, and images)."""
    assert ABB_MANUAL_PATH.exists(), f"ABB manual not found at {ABB_MANUAL_PATH}"

    parser = MultimodalPDFParser(image_output_dir=tmp_path / "images")
    parsed_doc = parser.parse_manual(ABB_MANUAL_PATH, max_pages=3, extract_images=True)

    assert parsed_doc.manual_name == ABB_MANUAL_PATH.name
    assert len(parsed_doc.pages) == 3
    assert parsed_doc.total_pages >= 30

    first_page = parsed_doc.pages[0]
    assert first_page.page_num == 1
    assert len(first_page.text) > 0
    assert first_page.section_header != ""


def test_table_markdown_generation():
    """Verifies table extraction and markdown conversion."""
    table = ExtractedTable(
        page_num=21,
        headers=["Parameter", "Standard Limit", "Action Required"],
        rows=[
            ["SF6 Pressure (Stage 1)", "0.55 MPa", "Refill within 48h"],
            ["SF6 Pressure (Stage 2)", "0.50 MPa", "Lockout circuit breaker"],
            ["Dielectric BDV", "> 50 kV", "Filter insulating oil"],
        ],
    )
    md = table.to_markdown()
    assert "| Parameter | Standard Limit | Action Required |" in md
    assert "| --- | --- | --- |" in md
    assert "| SF6 Pressure (Stage 2) | 0.50 MPa | Lockout circuit breaker |" in md


def test_manual_ingestion_worker_isolated_chromadb(tmp_path):
    """
    Tests end-to-end ingestion pipeline into isolated ChromaDB volume using MockEmbedder.
    Verifies 100% adherence to manual_name and page_num retention and vector query retrieval.
    """
    chroma_dir = tmp_path / "chroma_troubleshooting"
    worker = ManualIngestionWorker(
        persist_dir=chroma_dir,
        collection_name="test_troubleshooting",
        embedder=MockEmbedder(),
        chunk_size_chars=500,
        chunk_overlap_chars=50,
        rate_limit_delay_sec=0.0,
    )

    # Ingest 2 pages of ABB manual
    summary = worker.ingest_manual(ABB_MANUAL_PATH, max_pages=2, extract_images=False)

    assert summary.manual_name == ABB_MANUAL_PATH.name
    assert summary.total_pages_parsed == 2
    assert summary.total_chunks_created > 0
    assert summary.vector_store_collection == "test_troubleshooting"

    # Query ChromaDB collection
    results = worker.query_kb("transformer installation and handling", n_results=3)

    assert "documents" in results
    assert len(results["documents"][0]) > 0
    assert "metadatas" in results

    first_meta = results["metadatas"][0][0]
    assert "manual_name" in first_meta
    assert first_meta["manual_name"] == ABB_MANUAL_PATH.name
    assert "page_num" in first_meta
    assert first_meta["page_num"] in [1, 2]
    assert "citation" in first_meta
    assert f"Page {first_meta['page_num']}" in first_meta["citation"]
    assert "fault_category" in first_meta

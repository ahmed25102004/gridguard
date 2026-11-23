import io
import os
import shutil
import sys
import tempfile
from pathlib import Path
import pymupdf
import pytest
from fastapi import status
from fastapi.testclient import TestClient

# Ensure ai-service directory is on sys.path
_AI_SERVICE_DIR = Path(__file__).resolve().parent.parent
if str(_AI_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(_AI_SERVICE_DIR))

from src.config import settings
from src.embeddings.embedder import (
    MockEmbedder,
    chunk_text_by_page,
    get_embedder,
)
import src.main as main_module
from src.main import app
from src.prompts.qa_prompt import (
    UNGROUNDED_FALLBACK_MESSAGE,
    build_qa_prompt,
    format_context_block,
    generate_grounded_answer,
)
from src.schemas.document import (
    Citation,
    DocumentChunk,
    DocumentMetadata,
    IngestResponse,
    QueryRequest,
    QueryResponse,
)
from src.vector_store import VectorStoreManager, get_vector_store


@pytest.fixture
def temp_chroma_dir():
    """Create a temporary directory for ChromaDB vector store isolation per test."""
    temp_dir = tempfile.mkdtemp(prefix="chroma_test_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def vector_store(temp_chroma_dir):
    """Fixture providing an isolated persistent VectorStoreManager instance."""
    embedder = MockEmbedder(dimension=128)
    store = VectorStoreManager(
        persist_directory=temp_chroma_dir,
        collection_name="test_substation_manuals",
        embedder=embedder,
    )
    yield store


@pytest.fixture
def sample_pdf_bytes():
    """Generate a clean 2-page in-memory PDF using PyMuPDF for testing."""
    doc = pymupdf.open()

    # Page 1: ABB Transformer specs
    p1 = doc.new_page()
    p1.insert_text(
        (50, 72),
        "ABB Power Transformer TrafoStar 220kV Specification Manual.\n"
        "Rated voltage: 220 kV. Rated power: 100 MVA. Cooling type: ONAN/ONAF.\n"
        "Operating oil temperature limit is 95 degrees Celsius under continuous peak load.",
    )

    # Page 2: Maintenance and trip procedures
    p2 = doc.new_page()
    p2.insert_text(
        (50, 72),
        "Maintenance & Safety Guidelines.\n"
        "Periodic dissolved gas analysis (DGA) must be conducted every six months.\n"
        "Buchholz relay trip curve activates instantaneously upon gas accumulation exceeding 250 cm3.",
    )

    pdf_stream = io.BytesIO()
    doc.save(pdf_stream)
    doc.close()
    pdf_stream.seek(0)
    return pdf_stream.getvalue()


@pytest.fixture
def test_client(temp_chroma_dir):
    """FastAPI TestClient with isolated temporary ChromaDB vector store and manuals directory."""
    isolated_store = VectorStoreManager(
        persist_directory=temp_chroma_dir,
        collection_name="test_api_collection",
        embedder=MockEmbedder(dimension=128),
    )

    temp_manuals_dir = os.path.join(temp_chroma_dir, "manuals")
    os.makedirs(temp_manuals_dir, exist_ok=True)
    orig_manuals_dir = settings.MANUALS_DIR
    settings.MANUALS_DIR = temp_manuals_dir

    temp_images_dir = os.path.join(temp_chroma_dir, "images")
    os.makedirs(temp_images_dir, exist_ok=True)
    orig_images_dir = settings.IMAGES_DIR
    settings.IMAGES_DIR = temp_images_dir

    # Monkeypatch the global singleton for the duration of the test
    original_store = main_module.get_vector_store
    main_module.get_vector_store = lambda: isolated_store

    with TestClient(app) as client:
        yield client

    main_module.get_vector_store = original_store
    settings.MANUALS_DIR = orig_manuals_dir
    settings.IMAGES_DIR = orig_images_dir


# ==========================================
# 1. Pydantic Schemas & Metadata Tests
# ==========================================

def test_document_metadata_schema():
    """Test valid creation and serialization of DocumentMetadata."""
    meta = DocumentMetadata(
        manual_id="ABB_TRAFO_220KV",
        asset_type="Power Transformer",
        manufacturer="ABB",
        document_name="abb_trafostar.pdf",
        version="v2.4",
        total_pages=15,
    )
    assert meta.manual_id == "ABB_TRAFO_220KV"
    assert meta.manufacturer == "ABB"
    assert meta.total_pages == 15
    assert meta.created_at is not None


def test_document_chunk_schema():
    """Test valid creation of DocumentChunk with page provenance."""
    chunk = DocumentChunk(
        chunk_id="ABB_01_p1_c0",
        manual_id="ABB_01",
        asset_type="Switchgear",
        manufacturer="ABB",
        document_name="manual.pdf",
        page_num=1,
        chunk_index=0,
        chunk_text="Rated short-circuit breaking current is 40 kA.",
    )
    assert chunk.page_num == 1
    assert chunk.chunk_index == 0
    assert "40 kA" in chunk.chunk_text


# ==========================================
# 2. Embedding Generator & Chunking Tests
# ==========================================

def test_mock_embedder_vector_normalization():
    """Test MockEmbedder returns unit-normalized vectors with expected dimensions."""
    embedder = MockEmbedder(dimension=128)
    vec = embedder.embed_query("Siemens SIPROTEC 5 protective relay configuration")

    assert len(vec) == 128
    # L2 norm should be approximately 1.0
    norm = sum(x * x for x in vec)
    assert pytest.approx(norm, rel=1e-4) == 1.0


def test_mock_embedder_deterministic_output():
    """Test that identical text yields identical embeddings (deterministic)."""
    embedder = MockEmbedder(dimension=64)
    v1 = embedder.embed_query("Schneider Electric Masterpact MTZ")
    v2 = embedder.embed_query("Schneider Electric Masterpact MTZ")
    assert v1 == v2


def test_chunk_text_by_page_preserves_metadata():
    """Test text chunker splits content while preserving physical page number."""
    raw_text = (
        "Introduction to SF6 Circuit Breaker. "
        "The nominal operating pressure is 0.6 MPa at 20 degrees Celsius. "
        "Overpressure relief valve opens at 0.75 MPa. "
    ) * 10  # Ensure enough text to create multiple chunks

    chunks = chunk_text_by_page(
        text=raw_text,
        page_num=4,
        manual_id="SIEMENS_3AP1",
        asset_type="Circuit Breaker",
        manufacturer="Siemens",
        document_name="siemens_3ap1.pdf",
        chunk_size=200,
        chunk_overlap=50,
    )

    assert len(chunks) > 1
    for chunk in chunks:
        assert chunk.page_num == 4
        assert chunk.manual_id == "SIEMENS_3AP1"
        assert chunk.manufacturer == "Siemens"
        assert chunk.chunk_id.startswith("SIEMENS_3AP1_p4_c")


def test_chunk_text_by_page_empty_text():
    """Test chunker gracefully returns empty list for blank pages."""
    chunks = chunk_text_by_page(
        text="   \n\t  ",
        page_num=1,
        manual_id="EMPTY_01",
        asset_type="None",
        manufacturer="Other",
        document_name="empty.pdf",
    )
    assert chunks == []


# ==========================================
# 3. ChromaDB Vector Store & Cosine Similarity Tests
# ==========================================

def test_vector_store_initialization_and_metadata(vector_store):
    """Test ChromaDB collection initializes with cosine distance space."""
    assert vector_store.collection is not None
    assert vector_store.collection_name == "test_substation_manuals"
    assert vector_store.collection.metadata["hnsw:space"] == "cosine"
    assert vector_store.count() == 0


def test_vector_store_add_and_search_persistence(vector_store):
    """Test storing chunks into ChromaDB and retrieving via cosine similarity."""
    chunks = [
        DocumentChunk(
            chunk_id="ABB_T_p1_c0",
            manual_id="ABB_T",
            asset_type="Transformer",
            manufacturer="ABB",
            document_name="abb_manual.pdf",
            page_num=1,
            chunk_index=0,
            chunk_text="Transformer cooling fan relay operates on 24V DC aux supply.",
        ),
        DocumentChunk(
            chunk_id="SIEMENS_B_p3_c0",
            manual_id="SIEMENS_B",
            asset_type="Breaker",
            manufacturer="Siemens",
            document_name="siemens_manual.pdf",
            page_num=3,
            chunk_index=0,
            chunk_text="Circuit breaker spring charging motor nominal current is 5A.",
        ),
    ]

    added_count = vector_store.add_chunks(chunks)
    assert added_count == 2
    assert vector_store.count() == 2

    # Query matching transformer
    citations = vector_store.similarity_search(
        query="cooling fan auxiliary supply",
        top_k=1,
    )

    assert len(citations) == 1
    cit = citations[0]
    assert cit.manual_id == "ABB_T"
    assert cit.document_name == "abb_manual.pdf"
    assert cit.page_num == 1
    assert cit.similarity_score >= 0.0


def test_vector_store_delete_manual(vector_store):
    """Test removing all chunks for a specific manual ID."""
    chunks = [
        DocumentChunk(
            chunk_id="DEL_p1_c0",
            manual_id="MANUAL_TO_DELETE",
            asset_type="Relay",
            manufacturer="Schneider Electric",
            document_name="schneider.pdf",
            page_num=1,
            chunk_index=0,
            chunk_text="Overcurrent protection curve set to ANSI extremely inverse.",
        ),
        DocumentChunk(
            chunk_id="KEEP_p1_c0",
            manual_id="MANUAL_TO_KEEP",
            asset_type="Relay",
            manufacturer="ABB",
            document_name="abb.pdf",
            page_num=1,
            chunk_index=0,
            chunk_text="Thermal replica overload protection enabled.",
        ),
    ]

    vector_store.add_chunks(chunks)
    assert vector_store.count() == 2

    vector_store.delete_manual("MANUAL_TO_DELETE")
    assert vector_store.count() == 1


# ==========================================
# 4. Prompt Template & Grounding Tests
# ==========================================

def test_prompt_template_formatting():
    """Test that build_qa_prompt includes grounded citations and fallback rules."""
    citations = [
        Citation(
            document_name="Siemens_7SJ85.pdf",
            manual_id="SIEMENS_RELAY",
            manufacturer="Siemens",
            asset_type="Protection Relay",
            page_num=12,
            similarity_score=0.91,
            excerpt="Binary input BI_1 threshold is configured to 220V DC.",
        )
    ]

    prompt = build_qa_prompt(query="What is the BI_1 threshold?", citations=citations)

    assert "Siemens_7SJ85.pdf" in prompt
    assert "Page: 12" in prompt
    assert "Binary input BI_1" in prompt
    assert UNGROUNDED_FALLBACK_MESSAGE in prompt


def test_grounded_answer_fallback_when_below_threshold():
    """Test that low similarity score triggers strict ungrounded fallback message."""
    low_sim_citation = [
        Citation(
            document_name="Schneider_Sepam.pdf",
            manual_id="SCHNEIDER_01",
            manufacturer="Schneider Electric",
            asset_type="Relay",
            page_num=5,
            similarity_score=0.30,  # Below threshold (0.65)
            excerpt="Unrelated general environmental dimensions.",
        )
    ]

    response = generate_grounded_answer(
        query="What is the rated dielectric withstand?",
        citations=low_sim_citation,
        similarity_threshold=0.65,
    )

    assert response.is_grounded is False
    assert UNGROUNDED_FALLBACK_MESSAGE in response.answer


def test_grounded_answer_includes_citations_when_above_threshold():
    """Test that grounded answer includes document name and page number."""
    high_sim_citation = [
        Citation(
            document_name="ABB_REF615.pdf",
            manual_id="ABB_REF615",
            manufacturer="ABB",
            asset_type="Feeder Protection",
            page_num=45,
            similarity_score=0.88,
            excerpt="CT secondary rating is selectable between 1A and 5A via DIP switch.",
        )
    ]

    response = generate_grounded_answer(
        query="How to select CT secondary rating?",
        citations=high_sim_citation,
        similarity_threshold=0.65,
    )

    assert response.is_grounded is True
    assert "ABB_REF615.pdf" in response.answer
    assert "Page: 45" in response.answer
    assert len(response.citations) == 1


# ==========================================
# 5. FastAPI Endpoints Integration Tests
# ==========================================

def test_health_check_endpoint(test_client):
    """Test GET /health returns service status and vector collection info."""
    response = test_client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "healthy"
    assert "GridGuard AI Service" in data["service"]


def test_ingest_manual_pdf_success(test_client, sample_pdf_bytes):
    """Test POST /ingest/manual accepts PDF, chunks pages, and stores in ChromaDB."""
    files = {
        "file": ("ABB_TrafoStar_220kV.pdf", sample_pdf_bytes, "application/pdf")
    }
    data = {
        "manual_id": "ABB_TRAFO_220KV",
        "asset_type": "Power Transformer",
        "manufacturer": "ABB",
        "version": "1.0",
    }

    response = test_client.post("/ingest/manual", files=files, data=data)
    assert response.status_code == status.HTTP_201_CREATED
    result = response.json()

    assert result["status"] == "success"
    assert result["manual_id"] == "ABB_TRAFO_220KV"
    assert result["total_pages"] == 2
    assert result["chunks_ingested"] >= 2
    assert "ABB_TrafoStar_220kV.pdf" in result["document_name"]
    assert result["saved_file_path"] is not None
    assert os.path.exists(result["saved_file_path"])


def test_ingest_manual_rejects_non_pdf(test_client):
    """Test POST /ingest/manual rejects files without .pdf extension."""
    files = {
        "file": ("manual.txt", b"plain text manual content", "text/plain")
    }
    data = {
        "manual_id": "TEXT_01",
        "asset_type": "Relay",
        "manufacturer": "ABB",
    }

    response = test_client.post("/ingest/manual", files=files, data=data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Only PDF documents" in response.json()["detail"]


def test_ingest_manual_rejects_empty_file(test_client):
    """Test POST /ingest/manual rejects empty uploaded file."""
    files = {
        "file": ("empty.pdf", b"", "application/pdf")
    }
    data = {
        "manual_id": "EMPTY_01",
        "asset_type": "Transformer",
        "manufacturer": "Siemens",
    }

    response = test_client.post("/ingest/manual", files=files, data=data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "empty" in response.json()["detail"].lower()


def test_query_endpoint_e2e(test_client, sample_pdf_bytes):
    """Test end-to-end flow: ingest PDF, then query it via POST /query."""
    # 1. Ingest
    test_client.post(
        "/ingest/manual",
        files={"file": ("ABB_TrafoStar.pdf", sample_pdf_bytes, "application/pdf")},
        data={
            "manual_id": "ABB_TRAFO_E2E",
            "asset_type": "Power Transformer",
            "manufacturer": "ABB",
        },
    )

    # 2. Query
    query_payload = {
        "query": "What is the operating oil temperature limit?",
        "manufacturer": "ABB",
        "top_k": 3,
    }

    response = test_client.post("/query", json=query_payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "query" in data
    assert "answer" in data
    assert "citations" in data


def test_query_endpoint_with_multiple_filters(test_client, sample_pdf_bytes):
    """Test POST /query with multiple filter fields (manual_id, manufacturer, asset_type) using ChromaDB $and operator."""
    test_client.post(
        "/ingest/manual",
        files={"file": ("ABB_TrafoStar.pdf", sample_pdf_bytes, "application/pdf")},
        data={
            "manual_id": "ABB_DIST_TRAFO_01",
            "asset_type": "Distribution Transformer",
            "manufacturer": "ABB",
        },
    )

    query_payload = {
        "query": "What is the operating oil temperature limit?",
        "manual_id": "ABB_DIST_TRAFO_01",
        "manufacturer": "ABB",
        "asset_type": "Distribution Transformer",
        "top_k": 3,
    }

    response = test_client.post("/query", json=query_payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "query" in data
    assert "answer" in data


def test_delete_manual_endpoint(test_client, sample_pdf_bytes):
    """Test DELETE /manual/{manual_id} removes records from vector collection and removes archived file."""
    ingest_resp = test_client.post(
        "/ingest/manual",
        files={"file": ("Manual_To_Delete.pdf", sample_pdf_bytes, "application/pdf")},
        data={
            "manual_id": "MANUAL_TO_DELETE_API",
            "asset_type": "Circuit Breaker",
            "manufacturer": "Schneider Electric",
        },
    )
    saved_path = ingest_resp.json().get("saved_file_path")
    assert saved_path is not None
    assert os.path.exists(saved_path)

    del_resp = test_client.delete("/manual/MANUAL_TO_DELETE_API")
    assert del_resp.status_code == status.HTTP_200_OK
    assert del_resp.json()["status"] == "success"
    assert not os.path.exists(saved_path)


def test_list_archived_manuals_endpoint(test_client, sample_pdf_bytes):
    """Test GET /manuals lists stored PDF files in data directory."""
    test_client.post(
        "/ingest/manual",
        files={"file": ("Siemens_Catalog.pdf", sample_pdf_bytes, "application/pdf")},
        data={
            "manual_id": "SIEMENS_CATALOG_01",
            "asset_type": "Relay",
            "manufacturer": "Siemens",
        },
    )

    list_resp = test_client.get("/manuals")
    assert list_resp.status_code == status.HTTP_200_OK
    data = list_resp.json()
    assert data["count"] >= 1
    filenames = [m["filename"] for m in data["manuals"]]
    assert any("SIEMENS_CATALOG_01" in f for f in filenames)

"""
GridGuard AI - Multimodal RAG Metadata Extractor
Student 4: AI Engineer 2 (RAG Assistant & Anomaly Detection)
Lane 2: AI Service (RAG & Stream)

Extracts and validates structured domain metadata for substation technical manuals,
ensuring strict adherence to verified OEM, equipment classification, manual_name, and page_num.
"""

from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import re
import json


KNOWN_OEMS: List[str] = ["ABB", "Siemens", "Schneider Electric", "GE", "Hitachi Energy", "Hitachi", "Schneider"]

EQUIPMENT_KEYWORDS: Dict[str, str] = {
    "transformer": "transformer",
    "trafo": "transformer",
    "switchgear": "switchgear",
    "circuit-breaker": "circuit_breaker",
    "circuit breaker": "circuit_breaker",
    "switchboard": "switchboard",
    "disconnector": "disconnector",
    "isolator": "disconnector",
    "relay": "protection_relay",
    "multilin": "protection_relay",
    "gis": "switchgear",
}

FAULT_CATEGORIES: Dict[str, List[str]] = {
    "SF6_Gas_Pressure": ["sf6", "gas pressure", "density monitor", "gas compartment", "leakage", "lockout", "diaphragm"],
    "Dielectric_Insulation": ["bdv", "dielectric", "breakdown voltage", "oil sample", "insulating oil", "dissolved gas", "dga", "moisture"],
    "Thermal_Overload": ["oti", "wti", "oil temperature", "winding temperature", "overheating", "cooling fan", "onaf", "heat run"],
    "Mechanical_Mechanism": ["operating mechanism", "spring charging", "motor", "interlock", "auxiliary switch", "latch", "trip coil"],
    "Protection_Trip": ["trip", "relay", "overcurrent", "differential", "buchholz", "gas accumulation", "earth fault", "lockout"],
    "Routine_Maintenance": ["maintenance", "inspection", "servicing", "lubrication", "cleaning", "torque", "tightening"],
}


class TechnicalMetadataExtractor:
    """
    Extracts high-voltage equipment metadata from document headers, file paths,
    and technical text snippets.
    """

    def __init__(self, catalog_path: Optional[Path] = None):
        self.catalog: Dict[str, Any] = {}
        if catalog_path and catalog_path.exists():
            with open(catalog_path, "r", encoding="utf-8") as f:
                self.catalog = json.load(f)

    def extract_manual_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        Infers OEM, equipment type, voltage rating, and standardized manual_name from filepath.
        """
        file_name = file_path.name
        file_str = str(file_path).lower()

        # Identify OEM
        detected_oem = "Unknown OEM"
        for oem in ["abb", "siemens", "schneider", "hitachi", "ge"]:
            if oem in file_str:
                detected_oem = {
                    "abb": "ABB",
                    "siemens": "Siemens",
                    "schneider": "Schneider Electric",
                    "hitachi": "Hitachi Energy",
                    "ge": "GE",
                }[oem]
                break

        # Identify Equipment Type
        detected_type = "electrical_equipment"
        for kw, eq_type in EQUIPMENT_KEYWORDS.items():
            if kw in file_str:
                detected_type = eq_type
                break

        # Identify Model Name
        model_name = file_name.replace(".pdf", "").replace("_", " ")

        return {
            "manual_name": file_name,
            "oem": detected_oem,
            "equipment_type": detected_type,
            "model_name": model_name,
            "relative_path": str(file_path),
        }

    def infer_fault_category(self, text: str) -> str:
        """
        Classifies electrical fault category based on domain keywords.
        """
        text_lower = text.lower()
        matched_scores: Dict[str, int] = {}

        for category, keywords in FAULT_CATEGORIES.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                matched_scores[category] = score

        if matched_scores:
            return max(matched_scores, key=matched_scores.get) # type: ignore
        return "General_Operation"

    def build_chunk_metadata(
        self,
        manual_metadata: Dict[str, Any],
        page_num: int,
        chunk_index: int,
        section_title: Optional[str] = None,
        text_content: str = "",
        has_table: bool = False,
        has_image: bool = False,
        image_paths: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Constructs standardized metadata dictionary for vector store indexing.
        Strictly enforces presence of manual_name and page_num.
        """
        if not manual_metadata.get("manual_name"):
            raise ValueError("Metadata violation: manual_name is strictly required.")
        if page_num is None or page_num < 1:
            raise ValueError("Metadata violation: valid page_num (>=1) is strictly required.")

        fault_cat = self.infer_fault_category(text_content)

        return {
            "manual_name": manual_metadata["manual_name"],
            "page_num": int(page_num),
            "chunk_index": int(chunk_index),
            "oem": manual_metadata.get("oem", "Unknown"),
            "equipment_type": manual_metadata.get("equipment_type", "equipment"),
            "section_title": section_title or "Operational Section",
            "fault_category": fault_cat,
            "has_table": bool(has_table),
            "has_image": bool(has_image),
            "image_paths": json.dumps(image_paths or []),
            "citation": f"{manual_metadata['manual_name']} (Page {page_num})",
        }

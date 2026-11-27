"""
GridGuard AI - Multimodal PyMuPDF Technical Manual Parser
Student 4: AI Engineer 2 (RAG Assistant & Anomaly Detection)
Lane 2: AI Service (RAG & Stream)

Extracts text, structural section headers, equipment fault tables,
and diagrams/schematics from high-voltage electrical equipment PDF manuals.
"""

from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path
import re
import fitz  # PyMuPDF
from pydantic import BaseModel, Field


class ExtractedTable(BaseModel):
    """Structured representation of an equipment fault/specification table."""
    page_num: int
    headers: List[str] = Field(default_factory=list)
    rows: List[List[Optional[str]]] = Field(default_factory=list)
    markdown: str = ""

    def to_markdown(self) -> str:
        if self.markdown:
            return self.markdown
        if not self.headers and not self.rows:
            return ""
        
        cols = self.headers if self.headers else [f"Col_{i+1}" for i in range(len(self.rows[0]) if self.rows else 0)]
        header_line = "| " + " | ".join(str(c or "").replace("\n", " ").strip() for c in cols) + " |"
        sep_line = "| " + " | ".join(["---"] * len(cols)) + " |"
        row_lines = []
        for r in self.rows:
            row_lines.append("| " + " | ".join(str(cell or "").replace("\n", " ").strip() for cell in r) + " |")
        
        self.markdown = "\n".join([header_line, sep_line] + row_lines)
        return self.markdown


class ExtractedImage(BaseModel):
    """Metadata representing an extracted technical schematic or equipment diagram."""
    page_num: int
    image_path: str
    width: int
    height: int
    image_format: str


class ParsedPage(BaseModel):
    """Complete multimodal content extracted from an individual PDF page."""
    page_num: int
    text: str
    section_header: str = ""
    tables: List[ExtractedTable] = Field(default_factory=list)
    images: List[ExtractedImage] = Field(default_factory=list)


class ParsedManual(BaseModel):
    """Aggregated parsed document representation."""
    manual_name: str
    file_path: str
    total_pages: int
    pages: List[ParsedPage] = Field(default_factory=list)
    tables_count: int = 0
    images_count: int = 0


class MultimodalPDFParser:
    """
    High-performance PyMuPDF document worker extracting text,
    markdown tables, and diagrams with page-level provenance.
    """

    def __init__(self, image_output_dir: Optional[Path] = None):
        self.image_output_dir = image_output_dir or Path("ai-service/data/images")
        self.image_output_dir.mkdir(parents=True, exist_ok=True)

    def parse_page_header(self, text: str) -> str:
        """
        Infers the structural section header (e.g. '41 Maintenance', 'Section 3.2')
        using pattern matching on top lines.
        """
        lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
        header_patterns = [
            r"^([0-9]+(\.[0-9]+)*\s+[A-Za-z\s]{3,40})$",
            r"^(Section\s+[0-9]+.*)$",
            r"^(Chapter\s+[0-9]+.*)$",
            r"^([A-Z\s]{4,35})$",
        ]
        for line in lines[:5]:
            for pat in header_patterns:
                if re.match(pat, line, re.IGNORECASE) and len(line) > 3:
                    return line
        return lines[0] if lines else "General Section"

    def parse_page(
        self,
        doc: fitz.Document,
        page_idx: int,
        manual_slug: str,
        extract_images: bool = True,
    ) -> ParsedPage:
        """
        Parses text, tables, and images from a single PDF page.
        """
        page = doc[page_idx]
        page_num = page_idx + 1

        # 1. Extract plain text
        raw_text = page.get_text("text").strip()
        section_header = self.parse_page_header(raw_text)

        # 2. Extract tables via PyMuPDF find_tables()
        extracted_tables: List[ExtractedTable] = []
        try:
            tab_finder = page.find_tables()
            if tab_finder and tab_finder.tables:
                for tab in tab_finder.tables:
                    raw_data = tab.extract()
                    if raw_data and len(raw_data) > 0:
                        headers = [str(c or "").strip() for c in raw_data[0]]
                        rows = [[str(cell or "").strip() for cell in r] for r in raw_data[1:]]
                        table_obj = ExtractedTable(page_num=page_num, headers=headers, rows=rows)
                        table_obj.to_markdown()
                        extracted_tables.append(table_obj)
        except Exception:
            pass  # Fall back gracefully if page has irregular geometry

        # 3. Extract technical diagrams / images
        extracted_images: List[ExtractedImage] = []
        if extract_images:
            try:
                img_list = page.get_images(full=True)
                doc_img_dir = self.image_output_dir / manual_slug
                doc_img_dir.mkdir(parents=True, exist_ok=True)

                for img_idx, img_info in enumerate(img_list):
                    xref = img_info[0]
                    base_img = doc.extract_image(xref)
                    if base_img:
                        img_bytes = base_img["image"]
                        img_ext = base_img["ext"]
                        width = base_img["width"]
                        height = base_img["height"]

                        # Filter out tiny logos / icons
                        if width >= 100 and height >= 100:
                            img_filename = f"page_{page_num}_img_{img_idx}.{img_ext}"
                            img_dest = doc_img_dir / img_filename
                            with open(img_dest, "wb") as f_img:
                                f_img.write(img_bytes)

                            extracted_images.append(
                                ExtractedImage(
                                    page_num=page_num,
                                    image_path=str(img_dest),
                                    width=width,
                                    height=height,
                                    image_format=img_ext,
                                )
                            )
            except Exception:
                pass

        return ParsedPage(
            page_num=page_num,
            text=raw_text,
            section_header=section_header,
            tables=extracted_tables,
            images=extracted_images,
        )

    def parse_manual(
        self,
        file_path: Path,
        max_pages: Optional[int] = None,
        extract_images: bool = True,
    ) -> ParsedManual:
        """
        Parses an entire technical manual PDF.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"PDF manual file '{file_path}' does not exist.")

        doc = fitz.open(file_path)
        total_doc_pages = len(doc)
        pages_to_process = min(total_doc_pages, max_pages) if max_pages else total_doc_pages

        manual_slug = file_path.stem
        parsed_pages: List[ParsedPage] = []
        total_tables = 0
        total_images = 0

        for idx in range(pages_to_process):
            p_obj = self.parse_page(doc, idx, manual_slug, extract_images=extract_images)
            total_tables += len(p_obj.tables)
            total_images += len(p_obj.images)
            parsed_pages.append(p_obj)

        doc.close()

        return ParsedManual(
            manual_name=file_path.name,
            file_path=str(file_path),
            total_pages=total_doc_pages,
            pages=parsed_pages,
            tables_count=total_tables,
            images_count=total_images,
        )

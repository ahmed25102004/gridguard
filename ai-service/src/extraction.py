import os
from typing import List, Optional, Tuple
import pymupdf


def extract_page_content_and_media(
    doc: pymupdf.Document,
    page_idx: int,
    manual_id: str,
    images_base_dir: str,
) -> Tuple[str, List[str], List[str]]:
    """
    Extract text, structured markdown tables, and technical diagrams/images from a single PDF page.

    Returns:
        Tuple of:
        - combined_text: Full page text enhanced with structured Markdown tables
        - image_urls: List of relative static URLs for diagrams/figures extracted on this page
        - tables_markdown: List of individual Markdown tables found on the page
    """
    page = doc.load_page(page_idx)
    page_num = page_idx + 1

    # 1. Extract raw body text
    raw_text = page.get_text("text") or ""

    # 2. Extract structured tables using PyMuPDF TableFinder
    tables_markdown: List[str] = []
    try:
        table_finder = page.find_tables()
        if table_finder and table_finder.tables:
            for tab in table_finder.tables:
                md_tab = tab.to_markdown()
                if md_tab and md_tab.strip():
                    tables_markdown.append(md_tab.strip())
    except Exception:
        # Fallback if table parsing fails on non-standard layout
        pass

    # 3. Extract technical diagrams and images
    manual_img_dir = os.path.join(images_base_dir, manual_id.strip())
    os.makedirs(manual_img_dir, exist_ok=True)
    image_urls: List[str] = []

    # A. Check for embedded raster images (photos, nameplates, meters)
    try:
        img_list = page.get_images(full=True)
        for idx, img in enumerate(img_list):
            xref = img[0]
            base_img = doc.extract_image(xref)
            if base_img:
                img_bytes = base_img.get("image")
                img_ext = base_img.get("ext", "png")
                width = base_img.get("width", 0)
                height = base_img.get("height", 0)

                # Filter out tiny icons, transparent spacers, or decorative bullets (< 50x50 px or < 1KB)
                if img_bytes and len(img_bytes) > 1024 and width >= 50 and height >= 50:
                    filename = f"page_{page_num}_img_{idx}.{img_ext}"
                    filepath = os.path.join(manual_img_dir, filename)
                    with open(filepath, "wb") as f_img:
                        f_img.write(img_bytes)
                    image_urls.append(f"/images/{manual_id.strip()}/{filename}")
    except Exception:
        pass

    # B. If no raster images were extracted, but the page has significant CAD/vector drawings
    # (e.g. schematics, 3D wiring diagrams, exploded views), render a crisp diagram preview
    try:
        drawings = page.get_drawings()
        if len(drawings) >= 15 and len(image_urls) == 0:
            diag_filename = f"page_{page_num}_diagram.png"
            diag_filepath = os.path.join(manual_img_dir, diag_filename)
            pix = page.get_pixmap(dpi=150)
            pix.save(diag_filepath)
            image_urls.append(f"/images/{manual_id.strip()}/{diag_filename}")
    except Exception:
        pass

    # 4. Integrate structured tables into text for RAG indexing
    if tables_markdown:
        tables_section = "\n\n### Technical Data Tables:\n" + "\n\n".join(tables_markdown)
        combined_text = raw_text.strip() + "\n" + tables_section
    else:
        combined_text = raw_text.strip()

    return combined_text, image_urls, tables_markdown

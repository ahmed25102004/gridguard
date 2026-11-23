import io
import os
from contextlib import asynccontextmanager
from typing import Optional
import pymupdf
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .embeddings.embedder import chunk_text_by_page, get_embedder
from .prompts.qa_prompt import generate_grounded_answer
from .schemas.document import (
    IngestResponse,
    QueryRequest,
    QueryResponse,
)
from .vector_store import VectorStoreManager, get_vector_store


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Initializes vector store on startup and ensures persistence and data directories exist.
    """
    os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
    os.makedirs(settings.MANUALS_DIR, exist_ok=True)
    # Warm up vector store instance
    get_vector_store()
    yield


app = FastAPI(
    title=settings.SERVICE_NAME,
    description="Smart Grid Asset Platform - AI & RAG Engine for Substation Equipment Documentation",
    version=settings.SERVICE_VERSION,
    lifespan=lifespan,
)

# CORS configuration allowing dashboard and client connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["System"])
def health_check():
    """
    Liveness and readiness probe for Docker and Kubernetes orchestration.
    """
    vstore = get_vector_store()
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "chroma_collection": settings.CHROMA_COLLECTION_NAME,
        "total_chunks_indexed": vstore.count(),
    }


@app.post(
    "/ingest/manual",
    response_model=IngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest Substation Equipment PDF Manual",
    tags=["Ingestion"],
)
async def ingest_manual(
    file: UploadFile = File(..., description="PDF manual or datasheet file (ABB, Siemens, Schneider Electric)"),
    manual_id: str = Form(..., description="Unique equipment manual identifier (e.g. ABB_RELION_670)"),
    asset_type: str = Form(..., description="Type of substation asset (e.g. Protective Relay, Circuit Breaker)"),
    manufacturer: str = Form(..., description="Manufacturer (e.g. ABB, Siemens, Schneider Electric)"),
    version: Optional[str] = Form(default=None, description="Document revision or release version"),
):
    """
    Ingest and index a PDF manual for substation equipment.
    Extracts text page by page using PyMuPDF, chunks text preserving exact page provenance,
    generates vector embeddings, and stores them in persistent ChromaDB.
    """
    # 1. Validate file extension
    filename = file.filename or "manual.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file format: '{filename}'. Only PDF documents (.pdf) are supported.",
        )

    # 2. Read PDF binary content into memory
    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded PDF file is empty (0 bytes).",
        )

    try:
        pdf_doc = pymupdf.open(stream=content, filetype="pdf")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse PDF document: {str(exc)}",
        )

    total_pages = len(pdf_doc)
    if total_pages == 0:
        pdf_doc.close()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded PDF document contains no readable pages.",
        )

    all_chunks = []

    # 3. Extract text page-by-page preserving 1-based page numbers
    for page_idx in range(total_pages):
        page = pdf_doc.load_page(page_idx)
        page_text = page.get_text("text") or ""
        page_num = page_idx + 1

        chunks = chunk_text_by_page(
            text=page_text,
            page_num=page_num,
            manual_id=manual_id.strip(),
            asset_type=asset_type.strip(),
            manufacturer=manufacturer.strip(),
            document_name=filename,
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
        )
        all_chunks.extend(chunks)

    pdf_doc.close()

    if not all_chunks:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "No readable textual content could be extracted from this PDF. "
                "Scanned image-only PDFs without OCR are not supported in baseline ingestion."
            ),
        )

    # 4. Save the catalog / manual PDF file to data/manuals/
    os.makedirs(settings.MANUALS_DIR, exist_ok=True)
    safe_filename = f"{manual_id.strip()}_{os.path.basename(filename)}"
    saved_file_path = os.path.join(settings.MANUALS_DIR, safe_filename)
    try:
        with open(saved_file_path, "wb") as f_out:
            f_out.write(content)
    except Exception as exc:
        # If disk write fails, continue with vector ingestion but log or keep path None
        saved_file_path = None

    # 5. Store in ChromaDB persistent vector collection
    vstore = get_vector_store()
    chunks_stored = vstore.add_chunks(all_chunks)

    return IngestResponse(
        status="success",
        manual_id=manual_id.strip(),
        document_name=filename,
        asset_type=asset_type.strip(),
        manufacturer=manufacturer.strip(),
        total_pages=total_pages,
        chunks_ingested=chunks_stored,
        saved_file_path=saved_file_path,
        message=f"Successfully ingested {chunks_stored} chunks across {total_pages} pages into ChromaDB and archived catalog PDF.",
    )


@app.get(
    "/manuals",
    summary="List Archived Manuals & Catalogs",
    tags=["Ingestion"],
)
def list_archived_manuals():
    """
    List all archived PDF manuals and datasheets stored in the data directory.
    """
    if not os.path.exists(settings.MANUALS_DIR):
        return {"manuals": [], "count": 0}

    files = []
    for f in os.listdir(settings.MANUALS_DIR):
        if f.lower().endswith(".pdf"):
            f_path = os.path.join(settings.MANUALS_DIR, f)
            stats = os.stat(f_path)
            files.append({
                "filename": f,
                "size_bytes": stats.st_size,
                "last_modified": stats.st_mtime,
                "path": f_path,
            })
    return {"manuals": files, "count": len(files)}


@app.post(
    "/query",
    response_model=QueryResponse,
    summary="Query Grounded Substation Knowledge Base",
    tags=["RAG Query"],
)
def query_knowledge_base(request: QueryRequest):
    """
    Query the ingested equipment manuals using cosine distance similarity search.
    Enforces strict grounding and returns citations with exact document names and page numbers.
    """
    vstore = get_vector_store()

    # Build metadata filter if specified
    filter_dict = {}
    if request.manual_id:
        filter_dict["manual_id"] = request.manual_id
    if request.manufacturer:
        filter_dict["manufacturer"] = request.manufacturer
    if request.asset_type:
        filter_dict["asset_type"] = request.asset_type

    citations = vstore.similarity_search(
        query=request.query,
        top_k=request.top_k,
        filter_dict=filter_dict if filter_dict else None,
    )

    return generate_grounded_answer(
        query=request.query,
        citations=citations,
        similarity_threshold=settings.SIMILARITY_THRESHOLD,
    )


@app.delete(
    "/manual/{manual_id}",
    summary="Remove an Ingested Manual",
    tags=["Ingestion"],
)
def delete_manual_endpoint(manual_id: str):
    """
    Delete all vector records associated with a manual ID and remove the archived file.
    """
    vstore = get_vector_store()
    vstore.delete_manual(manual_id)

    # Clean up physical catalog PDF file from manuals directory
    if os.path.exists(settings.MANUALS_DIR):
        for f_name in os.listdir(settings.MANUALS_DIR):
            if f_name.startswith(f"{manual_id.strip()}_"):
                try:
                    os.remove(os.path.join(settings.MANUALS_DIR, f_name))
                except OSError:
                    pass

    return {
        "status": "success",
        "manual_id": manual_id,
        "message": f"All vectors and archived files for manual '{manual_id}' have been removed.",
    }

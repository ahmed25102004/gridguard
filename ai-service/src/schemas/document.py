from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ManufacturerEnum(str, Enum):
    """Supported smart grid equipment manufacturers."""
    ABB = "ABB"
    SIEMENS = "Siemens"
    SCHNEIDER = "Schneider Electric"
    GENERAL_ELECTRIC = "General Electric"
    OTHER = "Other"


class DocumentMetadata(BaseModel):
    """
    Metadata representation of an ingested substation equipment manual.
    """
    model_config = ConfigDict(from_attributes=True)

    manual_id: str = Field(..., description="Unique alphanumeric identifier for the equipment manual")
    asset_type: str = Field(..., description="Category of substation asset (e.g. Transformer, Circuit Breaker, Relay)")
    manufacturer: str = Field(..., description="Equipment manufacturer (e.g. ABB, Siemens, Schneider Electric)")
    document_name: str = Field(..., description="Original filename of the technical documentation or datasheet")
    version: Optional[str] = Field(default=None, description="Equipment manual revision or version string")
    total_pages: int = Field(default=1, ge=1, description="Total number of pages extracted from the PDF")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the manual was ingested",
    )


class DocumentChunk(BaseModel):
    """
    Represents an individual text chunk extracted from a manual page with full provenance metadata.
    """
    model_config = ConfigDict(from_attributes=True)

    chunk_id: str = Field(..., description="Unique deterministic identifier for this chunk (e.g. manualId_p1_c0)")
    manual_id: str = Field(..., description="Foreign key reference to parent equipment manual")
    asset_type: str = Field(..., description="Asset type classification (e.g. SF6 Circuit Breaker)")
    manufacturer: str = Field(..., description="Manufacturer of the equipment")
    document_name: str = Field(..., description="Name of the source document")
    page_num: int = Field(..., ge=1, description="1-indexed physical page number in the original PDF manual")
    chunk_index: int = Field(..., ge=0, description="Sequential index of the chunk within the document page")
    chunk_text: str = Field(..., min_length=1, description="The textual content of the chunk")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary additional chunk metadata")


class IngestResponse(BaseModel):
    """
    Response schema returned after successful manual PDF ingestion and vector storage.
    """
    status: str = Field(default="success", description="Status code string of the operation")
    manual_id: str = Field(..., description="Unique identifier of the ingested manual")
    document_name: str = Field(..., description="Original PDF file name")
    asset_type: str = Field(..., description="Asset type of the equipment")
    manufacturer: str = Field(..., description="Manufacturer of the equipment")
    total_pages: int = Field(..., description="Number of pages successfully parsed")
    chunks_ingested: int = Field(..., description="Total count of text chunks embedded and stored in ChromaDB")
    saved_file_path: Optional[str] = Field(default=None, description="Local filesystem path where the uploaded PDF catalog is archived")
    message: str = Field(..., description="Human-readable summary of the ingestion result")


class Citation(BaseModel):
    """
    Grounded source citation referencing an exact manual, manufacturer, and page number.
    """
    document_name: str = Field(..., description="Original name of the referenced equipment manual")
    manual_id: str = Field(..., description="Manual identifier")
    manufacturer: str = Field(..., description="Equipment manufacturer")
    asset_type: str = Field(..., description="Associated asset type")
    page_num: int = Field(..., description="1-based page number where the fact was cited from")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Cosine similarity score (0.0 to 1.0)")
    excerpt: str = Field(..., description="Relevant text excerpt supporting the citation")


class QueryRequest(BaseModel):
    """
    Incoming payload schema for querying technical manuals via RAG.
    """
    query: str = Field(..., min_length=3, description="Technical question or troubleshooting query")
    manual_id: Optional[str] = Field(default=None, description="Optional filter to restrict search to a specific manual")
    manufacturer: Optional[str] = Field(default=None, description="Optional filter by manufacturer (e.g. ABB, Siemens)")
    asset_type: Optional[str] = Field(default=None, description="Optional filter by asset type")
    top_k: int = Field(default=4, ge=1, le=20, description="Number of relevant chunks to retrieve")


class QueryResponse(BaseModel):
    """
    Grounded answer schema strictly citing document names and page numbers.
    """
    query: str = Field(..., description="The original user query")
    answer: str = Field(..., description="Grounded technical answer with inline citations or fallback message")
    citations: List[Citation] = Field(default_factory=list, description="List of source citations with exact page numbers")
    is_grounded: bool = Field(..., description="True if answer is backed by relevant manual context above threshold")
    max_similarity: float = Field(..., description="Highest cosine similarity score among retrieved chunks")

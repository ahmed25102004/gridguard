"""
GridGuard AI - Multimodal Technical Manual Ingestion Pipeline
Student 4: AI Engineer 2 (RAG Assistant & Anomaly Detection)
Lane 2: AI Service (RAG & Stream)

Chunks technical manuals using recursive text splitting (500 tokens / 50 overlap),
generates dense vector embeddings, and upserts with verified page-level metadata into ChromaDB.
"""

from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path
import time
import json
import chromadb
from chromadb.config import Settings as ChromaSettings
from pydantic import BaseModel, Field

from .pdf_parser import MultimodalPDFParser, ParsedManual, ParsedPage
from .metadata_extractor import TechnicalMetadataExtractor
from ..embeddings.embedder import BaseEmbedder, get_embedder


DEFAULT_TROUBLESHOOTING_DIR = Path("ai-service/data/chroma_db_troubleshooting")
DEFAULT_COLLECTION_NAME = "equipment_troubleshooting"


class ChunkRecord(BaseModel):
    """Standardized representation of a single vector store document chunk."""
    chunk_id: str
    text: str
    metadata: Dict[str, Any]


class IngestionSummary(BaseModel):
    """Audit report returned upon completing technical manual ingestion."""
    manual_name: str
    total_pages_parsed: int
    total_chunks_created: int
    tables_indexed: int
    images_indexed: int
    vector_store_collection: str
    elapsed_seconds: float


class RecursiveTokenTextSplitter:
    """
    Splits technical text recursively along structural boundaries:
    Paragraphs -> Sentences -> Words -> Characters.
    Configured for ~500 tokens (approx 2000 chars) with 50 tokens (approx 200 chars) overlap.
    """

    def __init__(
        self,
        chunk_size: int = 2000,
        chunk_overlap: int = 200,
        separators: Optional[List[str]] = None,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", "; ", ", ", " ", ""]

    def split_text(self, text: str) -> List[str]:
        if not text or not text.strip():
            return []

        if len(text) <= self.chunk_size:
            return [text.strip()]

        # Split on the most prominent separator
        chosen_sep = ""
        for sep in self.separators:
            if sep in text:
                chosen_sep = sep
                break

        splits = text.split(chosen_sep) if chosen_sep else list(text)

        chunks: List[str] = []
        current_chunk: List[str] = []
        current_len = 0

        for part in splits:
            part_len = len(part) + len(chosen_sep)
            if current_len + part_len > self.chunk_size and current_chunk:
                merged = chosen_sep.join(current_chunk).strip()
                if merged:
                    chunks.append(merged)
                # Apply overlap by keeping trailing tokens/parts
                overlap_len = 0
                overlap_parts = []
                for p in reversed(current_chunk):
                    if overlap_len + len(p) <= self.chunk_overlap:
                        overlap_parts.insert(0, p)
                        overlap_len += len(p)
                    else:
                        break
                current_chunk = overlap_parts
                current_len = sum(len(p) for p in current_chunk)

            current_chunk.append(part)
            current_len += len(part)

        if current_chunk:
            final_merged = chosen_sep.join(current_chunk).strip()
            if final_merged:
                chunks.append(final_merged)

        return chunks


class ManualIngestionWorker:
    """
    Orchestrates parsing, splitting, embedding, and batch upserting into ChromaDB.
    Enforces isolated volume persistence, rate limiting, and strict metadata retention.
    """

    def __init__(
        self,
        persist_dir: Optional[Path] = None,
        collection_name: str = DEFAULT_COLLECTION_NAME,
        embedder: Optional[BaseEmbedder] = None,
        chunk_size_chars: int = 2000,
        chunk_overlap_chars: int = 200,
        rate_limit_delay_sec: float = 0.05,
    ):
        self.persist_dir = persist_dir or DEFAULT_TROUBLESHOOTING_DIR
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name
        self.embedder = embedder or get_embedder()
        self.rate_limit_delay_sec = rate_limit_delay_sec

        self.pdf_parser = MultimodalPDFParser()
        self.metadata_extractor = TechnicalMetadataExtractor()
        self.splitter = RecursiveTokenTextSplitter(
            chunk_size=chunk_size_chars,
            chunk_overlap=chunk_overlap_chars,
        )

        # Isolated ChromaDB persistent client instance
        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def prepare_page_chunks(
        self,
        page: ParsedPage,
        manual_metadata: Dict[str, Any],
        global_chunk_counter: int,
    ) -> Tuple[List[ChunkRecord], int]:
        """
        Creates multimodal text and table chunk records for a single page.
        """
        records: List[ChunkRecord] = []
        counter = global_chunk_counter
        p_num = page.page_num

        # 1. Text chunks
        if page.text.strip():
            raw_splits = self.splitter.split_text(page.text)
            for split_idx, split_text in enumerate(raw_splits):
                counter += 1
                meta = self.metadata_extractor.build_chunk_metadata(
                    manual_metadata=manual_metadata,
                    page_num=p_num,
                    chunk_index=counter,
                    section_title=page.section_header,
                    text_content=split_text,
                    has_table=len(page.tables) > 0,
                    has_image=len(page.images) > 0,
                    image_paths=[img.image_path for img in page.images],
                )
                cid = f"{manual_metadata['manual_name']}_p{p_num}_c{split_idx}"
                records.append(ChunkRecord(chunk_id=cid, text=split_text, metadata=meta))

        # 2. Table chunks (Dedicated high-priority table representations)
        for t_idx, table in enumerate(page.tables):
            counter += 1
            table_md = table.to_markdown()
            if table_md.strip():
                table_text = f"[TABLE: {page.section_header}]\n{table_md}"
                meta = self.metadata_extractor.build_chunk_metadata(
                    manual_metadata=manual_metadata,
                    page_num=p_num,
                    chunk_index=counter,
                    section_title=f"{page.section_header} (Table {t_idx+1})",
                    text_content=table_text,
                    has_table=True,
                    has_image=False,
                )
                cid = f"{manual_metadata['manual_name']}_p{p_num}_tab{t_idx}"
                records.append(ChunkRecord(chunk_id=cid, text=table_text, metadata=meta))

        return records, counter

    def batch_upsert_chunks(self, chunks: List[ChunkRecord], batch_size: int = 50) -> int:
        """
        Embeds and upserts chunks in batches with rate-limiting delay.
        """
        if not chunks:
            return 0

        total_upserted = 0
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            texts = [c.text for c in batch]
            ids = [c.chunk_id for c in batch]
            metadatas = [c.metadata for c in batch]

            embeddings = self.embedder.embed_documents(texts)

            self.collection.upsert(
                ids=ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas,
            )

            total_upserted += len(batch)
            if self.rate_limit_delay_sec > 0:
                time.sleep(self.rate_limit_delay_sec)

        return total_upserted

    def ingest_manual(
        self,
        file_path: Path,
        max_pages: Optional[int] = None,
        extract_images: bool = True,
    ) -> IngestionSummary:
        """
        Executes end-to-end ingestion of a single technical manual.
        """
        start_time = time.time()
        parsed_doc = self.pdf_parser.parse_manual(file_path, max_pages=max_pages, extract_images=extract_images)
        manual_meta = self.metadata_extractor.extract_manual_metadata(file_path)

        all_chunks: List[ChunkRecord] = []
        counter = 0

        for page in parsed_doc.pages:
            p_chunks, counter = self.prepare_page_chunks(page, manual_meta, counter)
            all_chunks.extend(p_chunks)

        upserted_count = self.batch_upsert_chunks(all_chunks)
        elapsed = time.time() - start_time

        return IngestionSummary(
            manual_name=parsed_doc.manual_name,
            total_pages_parsed=len(parsed_doc.pages),
            total_chunks_created=upserted_count,
            tables_indexed=parsed_doc.tables_count,
            images_indexed=parsed_doc.images_count,
            vector_store_collection=self.collection_name,
            elapsed_seconds=round(elapsed, 2),
        )

    def query_kb(
        self,
        query: str,
        n_results: int = 5,
        oem_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Queries the ChromaDB collection using cosine similarity.
        """
        query_emb = self.embedder.embed_query(query)
        where_filter = {"oem": oem_filter} if oem_filter else None

        results = self.collection.query(
            query_embeddings=[query_emb],
            n_results=n_results,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )
        return results

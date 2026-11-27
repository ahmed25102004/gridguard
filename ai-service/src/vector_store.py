import json
from typing import Any, Dict, List, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings

from .config import settings
from .embeddings.embedder import BaseEmbedder, get_embedder
from .schemas.document import Citation, DocumentChunk


class VectorStoreManager:
    """
    Manages persistent ChromaDB vector storage with cosine distance metric
    for substation equipment manuals and datasheets.
    """

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: Optional[str] = None,
        embedder: Optional[BaseEmbedder] = None,
    ):
        self.persist_directory = persist_directory or settings.CHROMA_PERSIST_DIR
        self.collection_name = collection_name or settings.CHROMA_COLLECTION_NAME
        self.embedder = embedder or get_embedder()

        # Initialize persistent ChromaDB client instance
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=ChromaSettings(anonymized_telemetry=False),
        )

        # Enforce cosine distance metric for technical document similarity
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add_chunks(
        self,
        chunks: List[DocumentChunk],
        embeddings: Optional[List[List[float]]] = None,
    ) -> int:
        """
        Store a batch of document chunks with embeddings and metadata in ChromaDB.
        """
        if not chunks:
            return 0

        # Generate embeddings if not pre-computed
        if embeddings is None:
            texts = [c.chunk_text for c in chunks]
            embeddings = self.embedder.embed_documents(texts)

        ids = [c.chunk_id for c in chunks]
        documents = [c.chunk_text for c in chunks]
        metadatas: List[Dict[str, Any]] = [
            {
                "manual_id": c.manual_id,
                "asset_type": c.asset_type,
                "manufacturer": c.manufacturer,
                "document_name": c.document_name,
                "page_num": int(c.page_num),
                "chunk_index": int(c.chunk_index),
                "images": json.dumps(c.images),
            }
            for c in chunks
        ]

        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

        return len(chunks)

    def similarity_search(
        self,
        query: str,
        top_k: Optional[int] = None,
        filter_dict: Optional[Dict[str, Any]] = None,
        query_embedding: Optional[List[float]] = None,
    ) -> List[Citation]:
        """
        Query ChromaDB using cosine distance and return formatted citations with page numbers.
        Cosine distance in ChromaDB is in [0, 2], where 0 = identical.
        Similarity score is converted as: max(0.0, 1.0 - distance).
        """
        k = top_k or settings.DEFAULT_TOP_K

        if query_embedding is None:
            query_embedding = self.embedder.embed_query(query)

        query_args: Dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": min(k, max(1, self.collection.count())),
            "include": ["documents", "metadatas", "distances"],
        }

        if filter_dict:
            # ChromaDB requires $and logical operator when filtering on multiple fields
            items = [{k: v} for k, v in filter_dict.items() if v is not None and str(v).strip()]
            if len(items) == 1:
                query_args["where"] = items[0]
            elif len(items) > 1:
                query_args["where"] = {"$and": items}

        # If collection is empty, return empty list
        if self.collection.count() == 0:
            return []

        results = self.collection.query(**query_args)

        citations: List[Citation] = []
        if not results or not results.get("ids") or not results["ids"][0]:
            return citations

        ids = results["ids"][0]
        docs = results["documents"][0] if results.get("documents") else []
        metas = results["metadatas"][0] if results.get("metadatas") else []
        dists = results["distances"][0] if results.get("distances") else []

        for i in range(len(ids)):
            meta = metas[i] if i < len(metas) else {}
            doc_text = docs[i] if i < len(docs) else ""
            distance = dists[i] if i < len(dists) else 1.0

            # Convert cosine distance to a [0.0, 1.0] similarity metric
            similarity = max(0.0, min(1.0, 1.0 - distance))

            raw_images = meta.get("images", "[]")
            try:
                cit_images = json.loads(raw_images) if isinstance(raw_images, str) else []
            except Exception:
                cit_images = []

            citations.append(
                Citation(
                    document_name=str(meta.get("document_name", "Unknown Manual")),
                    manual_id=str(meta.get("manual_id", "")),
                    manufacturer=str(meta.get("manufacturer", "Unknown")),
                    asset_type=str(meta.get("asset_type", "General Substation Asset")),
                    page_num=int(meta.get("page_num", 1)),
                    similarity_score=round(similarity, 4),
                    excerpt=doc_text,
                    images=cit_images,
                )
            )

        return citations

    def delete_manual(self, manual_id: str) -> None:
        """
        Delete all chunks associated with a specific manual ID from ChromaDB.
        """
        self.collection.delete(where={"manual_id": manual_id})

    def count(self) -> int:
        """Return total number of stored chunks in the collection."""
        return self.collection.count()

    def reset(self) -> None:
        """Clear all stored documents and recreate the collection."""
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )


# Global singleton instance for the application
_vector_store_instance: Optional[VectorStoreManager] = None


def get_vector_store() -> VectorStoreManager:
    """Return or initialize global VectorStoreManager singleton."""
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStoreManager()
    return _vector_store_instance

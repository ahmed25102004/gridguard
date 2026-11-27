import hashlib
import math
import re
from abc import ABC, abstractmethod
from typing import List, Optional
from ..config import settings
from ..schemas.document import DocumentChunk


class BaseEmbedder(ABC):
    """
    Abstract interface for generating vector embeddings from text strings.
    """

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate vector embeddings for a batch of text chunks."""
        pass

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """Generate a vector embedding for a single search query."""
        pass


class MockEmbedder(BaseEmbedder):
    """
    Deterministic pseudo-embedding generator producing unit-normalized 384-dimensional vectors.
    Useful for unit tests, offline development, and CI/CD pipelines without external API costs.
    """

    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    def _generate_vector(self, text: str) -> List[float]:
        cleaned = text.strip().lower()
        if not cleaned:
            return [0.0] * self.dimension

        # Generate deterministic floats seeded from sha256 of text tokens
        words = re.findall(r"\w+", cleaned)
        vector = [0.0] * self.dimension

        for word in words:
            h = hashlib.sha256(word.encode("utf-8")).digest()
            for j in range(self.dimension):
                byte_val = h[j % len(h)]
                val = (byte_val - 128) / 128.0
                vector[j] += val

        # Normalize to unit length (L2 norm) for cosine distance
        norm = math.sqrt(sum(x * x for x in vector))
        if norm > 0:
            return [x / norm for x in vector]
        return [1.0 / math.sqrt(self.dimension)] * self.dimension

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._generate_vector(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._generate_vector(text)


class GeminiEmbedder(BaseEmbedder):
    """
    Embedding generator using Google Gemini's text-embedding-004 model.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model_name or settings.EMBEDDING_MODEL_NAME

        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured in settings or environment.")

        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self._client = genai
        except ImportError:
            raise ImportError(
                "google-generativeai package is required for Gemini embeddings. "
                "Install it using: pip install google-generativeai"
            )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        results = []
        batch_size = 25
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            response = self._client.embed_content(
                model=self.model_name,
                content=batch,
                task_type="retrieval_document",
            )
            embs = response.get("embedding", [])
            for e in embs:
                if isinstance(e, dict) and "values" in e:
                    e = e["values"]
                results.append(e)
        return results

    def embed_query(self, text: str) -> List[float]:
        response = self._client.embed_content(
            model=self.model_name,
            content=text,
            task_type="retrieval_query",
        )
        emb = response.get("embedding", [])
        if isinstance(emb, dict) and "values" in emb:
            emb = emb["values"]
        return emb


class OpenAIEmbedder(BaseEmbedder):
    """
    Embedding generator using OpenAI's embedding API.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: str = "text-embedding-3-small"):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model_name = model_name

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not configured in settings or environment.")

        try:
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError(
                "openai package is required for OpenAI embeddings. "
                "Install it using: pip install openai"
            )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        response = self._client.embeddings.create(input=texts, model=self.model_name)
        return [item.embedding for item in response.data]

    def embed_query(self, text: str) -> List[float]:
        response = self._client.embeddings.create(input=[text], model=self.model_name)
        return response.data[0].embedding


def get_embedder(provider: Optional[str] = None) -> BaseEmbedder:
    """
    Factory function returning the configured BaseEmbedder instance.
    Falls back gracefully to MockEmbedder if remote credentials are not supplied.
    """
    selected_provider = (provider or settings.EMBEDDING_PROVIDER).lower()

    if selected_provider == "gemini":
        if settings.GEMINI_API_KEY:
            return GeminiEmbedder()
        return MockEmbedder()
    elif selected_provider == "openai":
        if settings.OPENAI_API_KEY:
            return OpenAIEmbedder()
        return MockEmbedder()
    else:
        return MockEmbedder()


def chunk_text_by_page(
    text: str,
    page_num: int,
    manual_id: str,
    asset_type: str,
    manufacturer: str,
    document_name: str,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
    images: Optional[List[str]] = None,
    tables: Optional[List[str]] = None,
) -> List[DocumentChunk]:
    """
    Chunk raw extracted page text into overlapping windows, strictly preserving
    the physical PDF page number and all equipment provenance metadata.
    """
    size = chunk_size or settings.CHUNK_SIZE
    overlap = chunk_overlap or settings.CHUNK_OVERLAP
    page_images = images or []
    page_tables = tables or []

    if not text or not text.strip():
        return []

    cleaned_text = re.sub(r"\s+", " ", text).strip()
    chunks: List[DocumentChunk] = []

    start = 0
    chunk_idx = 0
    text_length = len(cleaned_text)

    while start < text_length:
        end = min(start + size, text_length)

        # Break at sentence or word boundary if not at end of text
        if end < text_length:
            # Look for sentence boundary (. or ? or !) in the last 25% of the window
            sentence_end = max(
                cleaned_text.rfind(". ", start, end),
                cleaned_text.rfind(".\n", start, end),
                cleaned_text.rfind("; ", start, end),
            )
            if sentence_end > start + (size * 0.6):
                end = sentence_end + 1
            else:
                last_space = cleaned_text.rfind(" ", start, end)
                if last_space > start + (size // 2):
                    end = last_space

        chunk_segment = cleaned_text[start:end].strip()
        if chunk_segment:
            chunk_id = f"{manual_id}_p{page_num}_c{chunk_idx}"
            chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    manual_id=manual_id,
                    asset_type=asset_type,
                    manufacturer=manufacturer,
                    document_name=document_name,
                    page_num=page_num,
                    chunk_index=chunk_idx,
                    chunk_text=chunk_segment,
                    images=page_images,
                    tables=page_tables,
                    metadata={
                        "manual_id": manual_id,
                        "asset_type": asset_type,
                        "manufacturer": manufacturer,
                        "document_name": document_name,
                        "page_num": page_num,
                        "chunk_index": chunk_idx,
                    },
                )
            )
            chunk_idx += 1

        if end >= text_length:
            break

        # Calculate next start position using overlap without cutting mid-word
        next_start = max(start + 1, end - overlap)
        if next_start < text_length:
            # Advance next_start to the next space or word boundary so chunks never start mid-word
            space_pos = cleaned_text.find(" ", next_start)
            if space_pos != -1 and space_pos < next_start + 40:
                next_start = space_pos + 1
        start = next_start

    return chunks

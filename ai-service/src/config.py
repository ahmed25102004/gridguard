import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

_BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """
    Configuration settings for GridGuard AI Service & RAG Engine.
    Loads configurations from environment variables or .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Service configuration
    SERVICE_NAME: str = "GridGuard AI Service"
    SERVICE_VERSION: str = "1.0.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8001

    # Data & Catalogs Storage Configuration
    DATA_DIR: str = str(_BASE_DIR / "data")
    MANUALS_DIR: str = str(_BASE_DIR / "data" / "manuals")

    # Vector Database (ChromaDB) Configuration
    CHROMA_PERSIST_DIR: str = str(_BASE_DIR / "data" / "chroma_db")
    CHROMA_COLLECTION_NAME: str = "substation_manuals"

    # Embedding Provider ("mock", "gemini", "openai")
    EMBEDDING_PROVIDER: str = "mock"
    EMBEDDING_MODEL_NAME: str = "models/text-embedding-004"
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    # Text Chunking Settings
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 150

    # RAG Retrieval & Grounding Thresholds
    # Cosine distance ranges from 0 (identical) to 2 (opposite).
    # Similarity score is defined as: 1.0 - distance.
    SIMILARITY_THRESHOLD: float = 0.65
    DEFAULT_TOP_K: int = 4


settings = Settings()

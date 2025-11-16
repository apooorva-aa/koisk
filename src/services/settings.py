"""
Application settings and environment configuration for the offline kiosk.

Uses:
- pgvector (IVFFLAT indexing)
- TinyLlama 1.1B (Q4_K_M) locally via llama.cpp
- Pydantic BaseSettings for .env + environment overrides
"""

from __future__ import annotations
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Kiosk configuration"""

    # Basic app config
    APP_NAME: str = "kiosk assistant"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    ENV: str = "PROD"

    # ---- Local LLM (TinyLlama) ----
    LLM_MODEL_PATH: str = Field(
        default="./models/TinyLlama-1.1B-Chat-v1.0.Q4_K_M.gguf",
        description="Path to TinyLlama 1.1B (Q4_K_M) model for llama.cpp.",
    )

    LLM_THREADS: int = Field(
        default=4,
        description="Number of CPU threads for inference on Raspberry Pi 4.",
    )

    LLM_CONTEXT_SIZE: int = Field(
        default=2048,
        description="Context window for TinyLlama.",
    )

    # ---- RAG pipeline settings ----
    SCRAPED_DATA_DIR: str = Field(
        default="./scraped_data",
        description="Directory containing scraped pages before embedding.",
    )

    EMBEDDING_MODEL: str = Field(
        default="all-MiniLM-L6-v2",
        description="Local embedding model (384-dim MiniLM).",
    )

    CHUNK_SIZE: int = Field(
        default=800,
        description="Chunk size for splitting museum/tourism text.",
    )

    CHUNK_OVERLAP: int = Field(
        default=150,
        description="Overlap between consecutive text chunks.",
    )

    VECTOR_DIMENSIONS: int = Field(
        default=384,
        description="Embedding dimension for MiniLM model.",
    )

    # ---- Vector DB ----
    VECTOR_DB_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/kiosk_db",
        description="PostgreSQL database URL with pgvector enabled.",
    )

    USE_IVFFLAT: bool = Field(
        default=True,
        description="Enable IVF_FLAT ANN indexing using pgvector.",
    )

    IVFFLAT_CLUSTER_COUNT: int = Field(
        default=100,
        description="Number of IVF clusters (increase for large corpora).",
    )

    RAG_ENABLED: bool = Field(
        default=True,
        description="Enable RAG: vector search + context injection into TinyLlama.",
    )

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()

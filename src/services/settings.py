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
        default="BAAI/bge-large-en-v1.5",
        description="BGE-Large embedding model (1024-dim) - better retrieval performance than MiniLM.",
    )

    CHUNK_SIZE: int = Field(
        default=512,
        description="Optimal chunk size for better context preservation (research-recommended).",
    )

    CHUNK_OVERLAP: int = Field(
        default=50,
        description="Overlap between consecutive text chunks.",
    )

    VECTOR_DIMENSIONS: int = Field(
        default=1024,
        description="Embedding dimension for BGE-Large model.",
    )
    
    # ---- Contextual Retrieval Settings ----
    USE_CONTEXTUAL_EMBEDDINGS: bool = Field(
        default=True,
        description="Enable contextual embeddings - prepend context to chunks before embedding.",
    )
    
    CONTEXT_INSTRUCTION_TEMPLATE: str = Field(
        default="""<document>
{WHOLE_DOCUMENT}
</document>

Here is the chunk we want to situate within the whole document:
<chunk>
{CHUNK_CONTENT}
</chunk>

Please give a short succinct context to situate this chunk within the overall document for the purposes of improving search retrieval of the chunk. Answer only with the succinct context and nothing else.""",
        description="Template for generating contextual information for chunks.",
    )
    
    # ---- Hybrid Search Settings ----
    USE_HYBRID_SEARCH: bool = Field(
        default=True,
        description="Enable hybrid search combining semantic + BM25 lexical search.",
    )
    
    USE_BM25: bool = Field(
        default=True,
        description="Enable BM25 for keyword-based retrieval alongside embeddings.",
    )
    
    # ---- Reranking Settings ----
    USE_RERANKER: bool = Field(
        default=True,
        description="Enable reranking to improve result relevance.",
    )
    
    RERANKER_MODEL: str = Field(
        default="BAAI/bge-reranker-large",
        description="Reranker model for refining retrieval results.",
    )
    
    INITIAL_RETRIEVAL_K: int = Field(
        default=20,
        description="Initial number of chunks to retrieve before reranking.",
    )
    
    FINAL_TOP_K: int = Field(
        default=5,
        description="Final number of top chunks to pass to LLM after reranking.",
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

"""Schemas for knowledge base documents and vector storage."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class KnowledgeDocument(BaseModel):
    """Schema for a single document in the knowledge base."""
    
    id: UUID = Field(..., description="Unique identifier for the document")
    content: str = Field(..., description="Text content of the document chunk")
    metadata: Dict[str, Any] = Field(..., description="Metadata associated with the document")
    embedding: List[float] = Field(..., description="Vector embedding for similarity search")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="When the document was created")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="When the document was last updated")


class DocumentMetadata(BaseModel):
    """Metadata schema for knowledge base documents."""
    
    source: str = Field(..., description="Source URL or identifier")
    rule_id: str = Field(..., description="Unique identifier for the document")
    chunk_index: int = Field(..., description="Index of this chunk within the source document")
    total_chunks: int = Field(..., description="Total number of chunks for this source")
    title: Optional[str] = Field(default=None, description="Title of the source document")
    category: Optional[str] = Field(default=None, description="Primary category (general, services, help, etc.)")
    framework: Optional[str] = Field(default=None, description="Information framework (Campus, Academic, etc.)")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    language: str = Field(default="en", description="Language of the content (en, hi, etc.)")
    created_at: Optional[str] = Field(default=None, description="When the document was created")
    updated_at: Optional[str] = Field(default=None, description="When the document was last updated")


class VectorSearchRequest(BaseModel):
    """Request for vector similarity search."""
    
    query_text: str = Field(..., description="Text to search for similar documents")
    k: int = Field(default=5, ge=1, le=50, description="Number of similar documents to return")
    filter_metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional metadata filters for the search"
    )
    similarity_threshold: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score threshold"
    )


class VectorSearchResult(BaseModel):
    """Result of a vector similarity search."""
    
    document: KnowledgeDocument = Field(..., description="The matching document")
    similarity_score: float = Field(..., description="Similarity score (0-1, higher is more similar)")
    rank: int = Field(..., description="Rank of this result (1-based)")


class VectorSearchResponse(BaseModel):
    """Response for vector similarity search."""
    
    query: str = Field(..., description="The original query text")
    results: List[VectorSearchResult] = Field(..., description="List of similar documents")
    total_results: int = Field(..., description="Total number of results found")
    search_time_ms: float = Field(..., description="Time taken for the search in milliseconds")


class KnowledgeBaseStats(BaseModel):
    """Statistics about the knowledge base."""
    
    total_documents: int = Field(..., description="Total number of documents in the knowledge base")
    total_chunks: int = Field(..., description="Total number of text chunks")
    unique_sources: int = Field(..., description="Number of unique source documents")
    frameworks: List[str] = Field(..., description="List of information frameworks represented")
    categories: List[str] = Field(..., description="List of content categories")
    last_updated: datetime = Field(..., description="When the knowledge base was last updated")
    embedding_model: str = Field(..., description="Model used for generating embeddings")
    vector_dimensions: int = Field(..., description="Dimension of the vector embeddings")


class DocumentIngestionRequest(BaseModel):
    """Request for ingesting documents into the knowledge base."""
    
    source_url: str = Field(..., description="URL of the source document")
    title: Optional[str] = Field(default=None, description="Title of the document")
    category: Optional[str] = Field(default=None, description="Category of the content")
    framework: Optional[str] = Field(default=None, description="Information framework (Campus, Academic, etc.)")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    force_refresh: bool = Field(default=False, description="Force refresh even if document exists")


class DocumentIngestionResponse(BaseModel):
    """Response for document ingestion."""
    
    document_id: UUID = Field(..., description="ID of the ingested document")
    chunks_created: int = Field(..., description="Number of chunks created from the document")
    source_url: str = Field(..., description="Source URL of the document")
    status: str = Field(..., description="Status of the ingestion process")
    message: str = Field(..., description="Additional information about the ingestion")


class RAGContextRequest(BaseModel):
    """Request for RAG context retrieval."""
    
    query: str = Field(..., description="User query to retrieve context for")
    k: int = Field(default=5, ge=1, le=20, description="Number of relevant documents to retrieve")
    focus_areas: Optional[List[str]] = Field(
        default=None,
        description="Specific areas to focus the search on"
    )
    frameworks: Optional[List[str]] = Field(
        default=None,
        description="Specific information frameworks to prioritize"
    )


class RAGContextResponse(BaseModel):
    """Response for RAG context retrieval."""
    
    context: str = Field(..., description="Retrieved context for the user query")
    sources: List[str] = Field(..., description="Source URLs of the retrieved documents")
    frameworks: List[str] = Field(..., description="Frameworks represented in the context")
    confidence_score: float = Field(..., description="Overall confidence in the retrieved context")
    retrieval_time_ms: float = Field(..., description="Time taken for context retrieval")

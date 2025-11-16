"""Repository for knowledge base documents using PostgreSQL with pgvector."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import asyncpg
from asyncpg import Connection

from services.settings import get_settings
from schemas.knowledge_base import (
    DocumentMetadata,
    KnowledgeDocument,
    KnowledgeBaseStats,
    VectorSearchResult,
)

logger = logging.getLogger(__name__)


class KnowledgeBaseRepository:
    """Repository for managing knowledge base documents in PostgreSQL with pgvector."""

    def __init__(self):
        """Initialize the knowledge base repository."""
        self.settings = get_settings()
        self._connection_pool: Optional[asyncpg.Pool] = None

    async def initialize(self) -> None:
        """Initialize the database connection pool and create tables if needed."""
        try:
            self._connection_pool = await asyncpg.create_pool(
                self.settings.VECTOR_DB_URL,
                min_size=1,
                max_size=10
            )
            
            # Create tables and indexes
            await self._create_tables()
            logger.info("Knowledge base repository initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize knowledge base repository: {e}")
            raise

    async def close(self) -> None:
        """Close the database connection pool."""
        if self._connection_pool:
            await self._connection_pool.close()
            
    async def _has_documents(self) -> bool:
        """Check if there are any documents in the knowledge base.
        
        Returns:
            bool: True if documents exist, False otherwise
        """
        if not self._connection_pool:
            await self.initialize()
            
        async with self._connection_pool.acquire() as conn:
            try:
                count = await conn.fetchval("""
                    SELECT COUNT(*) > 0 
                    FROM knowledge_documents
                    LIMIT 1
                """)
                return bool(count)
            except Exception as e:
                logger.error(f"Error checking for documents: {str(e)}")
                return False

    async def _create_tables(self) -> None:
        """Create the necessary tables and indexes for the knowledge base."""
        async with self._connection_pool.acquire() as conn:
            # Enable pgvector extension
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            
            # Create documents table
            vector_dim = self.settings.VECTOR_DIMENSIONS
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS knowledge_documents (
                    id UUID PRIMARY KEY,
                    content TEXT NOT NULL,
                    metadata JSONB NOT NULL,
                    embedding vector({vector_dim}) NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)
            
            # Create indexes for better performance
            if self.settings.USE_IVFFLAT:
                cluster_count = self.settings.IVFFLAT_CLUSTER_COUNT
                await conn.execute(f"""
                    CREATE INDEX IF NOT EXISTS knowledge_documents_embedding_ivfflat
                        ON knowledge_documents USING ivfflat (embedding vector_cosine_ops)
                        WITH (lists = {cluster_count});
                """)
            else:
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS knowledge_documents_embedding_hnsw
                        ON knowledge_documents USING hnsw (embedding vector_cosine_ops);
                """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS knowledge_documents_metadata_gin
                    ON knowledge_documents USING gin (metadata);
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS knowledge_documents_source
                    ON knowledge_documents ((metadata->>'source'));
            """)

            await conn.execute("""
                CREATE INDEX IF NOT EXISTS knowledge_documents_category
                ON knowledge_documents ((metadata->>'category'));
            """)

            await conn.execute("""
                CREATE INDEX IF NOT EXISTS knowledge_documents_framework
                ON knowledge_documents ((metadata->>'framework'));
            """)
            
            logger.info("Knowledge base tables and indexes created")

    async def create_document(
        self,
        content: str,
        metadata: DocumentMetadata,
        embedding: List[float]
    ) -> KnowledgeDocument:
        """Create a new knowledge document."""
        document_id = uuid4()
        now = datetime.now(UTC)
    
        try:
            # Convert metadata to dict and ensure all values are JSON serializable
            metadata_dump = metadata.model_dump()
        
            # Convert the embedding list to a string format for pgvector
            embedding_str = '[' + ','.join(map(str, embedding)) + ']'
        
            async with self._connection_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO knowledge_documents (id, content, metadata, embedding, created_at, updated_at)
                    VALUES ($1, $2, $3::jsonb, $4::vector, $5, $6)
                """, 
                    document_id, 
                    content, 
                    json.dumps(metadata_dump),
                    embedding_str,
                    now, 
                    now
                )
        
            logger.info(f"Successfully inserted document {document_id}")
        
            return KnowledgeDocument(
                id=document_id,
                content=content,
                metadata=metadata_dump,
                embedding=embedding,
                created_at=now,
                updated_at=now
            )
        
        except Exception as e:
            logger.error(f"Error inserting document: {str(e)}")
            logger.error(f"Document content length: {len(content)}")
            logger.error(f"Embedding length: {len(embedding) if embedding else 0}")
            logger.error(f"Metadata: {metadata.model_dump()}")
            raise

    async def get_document(self, document_id: UUID) -> Optional[KnowledgeDocument]:
        """Get a document by ID."""
        async with self._connection_pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT id, content, metadata, embedding, created_at, updated_at
                FROM knowledge_documents
                WHERE id = $1::uuid
            """, str(document_id))
            
            if not row:
                return None
            
            # Handle embedding conversion
            embedding = None
            if row['embedding'] is not None:
                if isinstance(row['embedding'], (list, tuple)):
                    embedding = [float(x) for x in row['embedding']]
                elif hasattr(row['embedding'], 'to_list'):  # Handle pgvector vector type
                    embedding = row['embedding'].to_list()
            
            # Handle metadata conversion
            metadata = row['metadata']
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse metadata JSON for document {document_id}")
                    metadata = {}
            
            return KnowledgeDocument(
                id=row['id'],
                content=row['content'],
                metadata=metadata,
                embedding=embedding,
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )

    async def search_similar_documents(
        self,
        query_embedding: List[float],
        k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
        similarity_threshold: Optional[float] = None
    ) -> List[VectorSearchResult]:
        """Search for similar documents using vector similarity."""
        async with self._connection_pool.acquire() as conn:
            # String representation of the vector
            embedding_str = '[' + ','.join(f"{float(x):.18f}" for x in query_embedding) + ']'
            
            # Build the query with optional filters
            where_clause = ""
            params = [embedding_str, k]
            param_count = 2
            
            if filter_metadata:
                for key, value in filter_metadata.items():
                    param_count += 1
                    # Use proper JSONB operator and parameter
                    where_clause += f" AND metadata->>'{key}' = ${param_count}::text"
                    params.append(str(value))
            
            if similarity_threshold is not None:
                param_count += 1
                where_clause += f" AND 1 - (embedding <=> $1::vector) > ${param_count}::float"
                params.append(float(similarity_threshold))
            
            query = f"""
                SELECT id, content, metadata, embedding, created_at, updated_at,
                       1 - (embedding <=> $1::vector) as similarity_score,
                       ROW_NUMBER() OVER (ORDER BY embedding <=> $1::vector) as rank
                FROM knowledge_documents
                WHERE 1=1 {where_clause}
                ORDER BY embedding <=> $1::vector
                LIMIT $2::int
            """
            
            logger.debug(f"Executing vector search with query: {query}")
            logger.debug(f"Parameters: {params}")
            
            rows = await conn.fetch(query, *params)
            
            results = []
            for row in rows:
                # Handle embedding conversion - ensure we always return a list
                embedding = []
                if row['embedding'] is not None:
                    try:
                        # Handles case when already stored as list:
                        if isinstance(row['embedding'], (list, tuple)):
                            embedding = [float(x) for x in row['embedding']]
                        # Handles pgvector type:
                        elif hasattr(row['embedding'], 'to_list'):
                            embedding = row['embedding'].to_list()
                        # Handle string representation:
                        elif isinstance(row['embedding'], str):  
                            embedding = [float(x) for x in row['embedding'].strip('[]').split(',') if x.strip()]
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Error converting embedding: {e}")
                        embedding = []
                
                # Ensure metadata is a dictionary
                metadata = row['metadata']
                if isinstance(metadata, str):
                    try:
                        metadata = json.loads(metadata)
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse metadata JSON: {metadata}")
                        metadata = {}
                
                try:
                    document = KnowledgeDocument(
                        id=row['id'],
                        content=row['content'],
                        metadata=metadata,
                        embedding=embedding,
                        created_at=row['created_at'],
                        updated_at=row['updated_at']
                    )
                except Exception as e:
                    logger.error(f"Error creating KnowledgeDocument: {e}")
                    logger.error(f"Document ID: {row['id']}")
                    logger.error(f"Content length: {len(row['content']) if row['content'] else 0}")
                    logger.error(f"Metadata type: {type(metadata)}")
                    logger.error(f"Embedding type: {type(embedding)}, length: {len(embedding) if embedding else 0}")
                    raise
                
                results.append(VectorSearchResult(
                    document=document,
                    similarity_score=float(row['similarity_score']),
                    rank=int(row['rank'])
                ))
            
            return results

    async def get_documents_by_source(self, source: str) -> List[KnowledgeDocument]:
        """Get all documents from a specific source."""
        async with self._connection_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, content, metadata, embedding, created_at, updated_at
                FROM knowledge_documents
                WHERE metadata->>'source' = $1
                ORDER BY COALESCE((metadata->>'chunk_index')::int, 0)
            """, source)
            
            documents = []
            for row in rows:
                embedding = []
                if row['embedding'] is not None:
                    try:
                        # Handles case when already stored as list:
                        if isinstance(row['embedding'], (list, tuple)):
                            embedding = [float(x) for x in row['embedding']]
                        # Handles pgvector type:
                        elif hasattr(row['embedding'], 'to_list'):
                            embedding = row['embedding'].to_list()
                        # Handle string representation:
                        elif isinstance(row['embedding'], str):  
                            embedding = [float(x) for x in row['embedding'].strip('[]').split(',') if x.strip()]
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Error converting embedding: {e}")
                        embedding = []
                
                # Ensure metadata is a dictionary
                metadata = row['metadata']
                if isinstance(metadata, str):
                    try:
                        metadata = json.loads(metadata)
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse metadata JSON: {metadata}")
                        metadata = {}
                
                try:
                    document = KnowledgeDocument(
                        id=row['id'],
                        content=row['content'],
                        metadata=metadata,
                        embedding=embedding, 
                        created_at=row['created_at'],
                        updated_at=row['updated_at']
                    )
                except Exception as e:
                    logger.error(f"Error creating KnowledgeDocument: {e}")
                    logger.error(f"Document ID: {row['id']}")
                    logger.error(f"Content length: {len(row['content']) if row['content'] else 0}")
                    logger.error(f"Metadata type: {type(metadata)}")
                    logger.error(f"Embedding type: {type(embedding)}, length: {len(embedding) if embedding else 0}")
                    raise
            
                documents.append(document)
            
            return documents

    async def delete_documents_by_source(self, source: str) -> int:
        """Delete all documents from a specific source."""
        async with self._connection_pool.acquire() as conn:
            result = await conn.execute("""
                DELETE FROM knowledge_documents
                WHERE metadata->>'source' = $1
            """, source)
            
            return int(result.split()[-1])

    async def get_knowledge_base_stats(self) -> KnowledgeBaseStats:
        """Get statistics about the knowledge base."""
        async with self._connection_pool.acquire() as conn:
            total_docs = await conn.fetchval("SELECT COUNT(*) FROM knowledge_documents")
            
            unique_sources = await conn.fetchval("""
                SELECT COUNT(DISTINCT metadata->>'source') 
                FROM knowledge_documents
            """)
            
            frameworks = await conn.fetch("""
                SELECT DISTINCT metadata->>'framework' as framework
                FROM knowledge_documents
                WHERE metadata->>'framework' IS NOT NULL
            """)
            
            categories = await conn.fetch("""
                SELECT DISTINCT metadata->>'category' as category
                FROM knowledge_documents
                WHERE metadata->>'category' IS NOT NULL
            """)

            last_updated = await conn.fetchval("""
                SELECT MAX(updated_at) FROM knowledge_documents
            """)
            
            return KnowledgeBaseStats(
                total_documents=total_docs,
                total_chunks=total_docs,
                unique_sources=unique_sources,
                frameworks=[row['framework'] for row in frameworks],
                categories=[row['category'] for row in categories],
                last_updated=last_updated or datetime.now(UTC),
                embedding_model=self.settings.EMBEDDING_MODEL,
                vector_dimensions=self.settings.VECTOR_DIMENSIONS
            )

    async def health_check(self) -> bool:
        """Check if the repository is healthy."""
        try:
            async with self._connection_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Knowledge base repository health check failed: {e}")
            return False

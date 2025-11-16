import logging
from typing import Optional, List, Dict
from sentence_transformers import SentenceTransformer
from repositories.knowledge_base_repository import KnowledgeBaseRepository
from services.settings import get_settings

logger = logging.getLogger(__name__)


class RAGComponent:
    def __init__(self, config):
        self.config = config
        self.repository = None
        self.embedding_model = None
        self.settings = None
        self.is_initialized = False
        
    async def initialize(self):
        try:
            logger.info("Initializing RAG component with PostgreSQL + pgvector...")
            self.settings = get_settings()
            self.repository = KnowledgeBaseRepository()
            await self.repository.initialize()
            logger.info("Knowledge base repository initialized")
            model_name = self.config.get('models', {}).get('embedding_model', self.settings.EMBEDDING_MODEL)
            logger.info(f"Loading embedding model: {model_name}")
            self.embedding_model = SentenceTransformer(model_name)
            has_docs = await self.repository._has_documents()
            if not has_docs:
                logger.warning("Knowledge base is empty. Run the scraper to ingest data.")
            else:
                stats = await self.repository.get_knowledge_base_stats()
                logger.info(f"Knowledge base: {stats.total_documents} documents from {stats.unique_sources} sources")
            
            self.is_initialized = True
            logger.info("RAG component initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG: {e}")
            raise
    
    
    async def search(self, query: str, limit: int = 5, category: Optional[str] = None, language: Optional[str] = None, similarity_threshold: float = 0.3) -> List[Dict]:
        if not self.is_initialized:
            logger.warning("RAG not initialized")
            return []
        try:
            logger.info(f"Searching for: {query}")
            query_embedding = self.embedding_model.encode(query).tolist()
            filter_metadata = {}
            if category:
                filter_metadata['category'] = category
            if language:
                filter_metadata['language'] = language
            results = await self.repository.search_similar_documents(
                query_embedding=query_embedding,
                k=limit,
                filter_metadata=filter_metadata if filter_metadata else None,
                similarity_threshold=similarity_threshold
            )
            
            logger.info(f"Found {len(results)} relevant documents")
            documents = []
            for result in results:
                documents.append({
                    'id': str(result.document.id),
                    'title': result.document.metadata.get('title', 'Untitled'),
                    'content': result.document.content,
                    'similarity': result.similarity_score,
                    'rank': result.rank,
                    'category': result.document.metadata.get('category', 'general'),
                    'source': result.document.metadata.get('source', 'unknown'),
                    'framework': result.document.metadata.get('framework', 'Campus'),
                    'tags': result.document.metadata.get('tags', [])
                })
            
            return documents
            
        except Exception as e:
            logger.error(f"Error in RAG search: {e}")
            return []
    
    async def get_context_for_query(self, query: str, max_context_length: int = 2000) -> str:
        documents = await self.search(query, limit=5)
        if not documents:
            return "No relevant information found in the knowledge base."
        context_parts = []
        current_length = 0
        for i, doc in enumerate(documents, 1):
            doc_context = f"\n[Source {i}: {doc['title']} (relevance: {doc['similarity']:.2f})]\n{doc['content']}\n"
            if current_length + len(doc_context) > max_context_length:
                break
            context_parts.append(doc_context)
            current_length += len(doc_context)
        context = "\n".join(context_parts)
        logger.info(f"Generated context with {len(context_parts)} documents ({current_length} chars)")
        return context
    
    async def get_stats(self) -> Dict:
        if not self.is_initialized:
            return {"error": "RAG not initialized"}
        try:
            stats = await self.repository.get_knowledge_base_stats()
            return {
                "total_documents": stats.total_documents,
                "unique_sources": stats.unique_sources,
                "categories": stats.categories,
                "frameworks": stats.frameworks,
                "last_updated": stats.last_updated.isoformat(),
                "embedding_model": stats.embedding_model,
                "vector_dimensions": stats.vector_dimensions
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"error": str(e)}
    
    
    async def cleanup(self):
        if self.repository:
            await self.repository.close()
        self.embedding_model = None
        logger.info("RAG component cleaned up")

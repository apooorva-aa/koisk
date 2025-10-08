"""
Retrieval Augmented Generation (RAG) Component.
Uses consolidated database models for knowledge base retrieval.
"""

import asyncio
import logging
from typing import Optional, List, Dict
from sentence_transformers import SentenceTransformer
from database.models import DatabaseManager, DocumentModel

logger = logging.getLogger(__name__)


class RAGComponent:
    """RAG component for knowledge base retrieval and augmentation."""
    
    def __init__(self, config):
        self.config = config
        self.db_manager = None
        self.document_model = None
        self.embedding_model = None
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize the RAG component."""
        try:
            logger.info("Initializing RAG component...")
            
            # Initialize database
            db_path = self.config.get('rag', {}).get('knowledge_base_path', 'data/kiosk_llm.db')
            self.db_manager = DatabaseManager(db_path)
            self.db_manager.connect()
            self.db_manager.initialize_schema()
            
            # Initialize document model
            self.document_model = DocumentModel(self.db_manager)
            
            # Load embedding model
            model_name = self.config.get('models', {}).get('embedding_model', 'all-MiniLM-L6-v2')
            logger.info(f"Loading embedding model: {model_name}")
            
            self.embedding_model = SentenceTransformer(model_name)
            
            # Add some sample data for testing
            await self._add_sample_data()
            
            self.is_initialized = True
            logger.info("RAG component initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG: {e}")
            raise
    
    async def _add_sample_data(self):
        """Add sample data for testing."""
        sample_docs = [
            {
                "title": "Welcome to Kiosk",
                "content": "This is an AI-powered kiosk that can help you with various queries. You can ask questions about services, products, or general information.",
                "metadata": {"category": "general", "language": "en"},
                "category": "general",
                "language": "en"
            },
            {
                "title": "Services Available",
                "content": "Our kiosk provides information about banking services, healthcare facilities, government services, and retail information.",
                "metadata": {"category": "services", "language": "en"},
                "category": "services",
                "language": "en"
            },
            {
                "title": "How to Use",
                "content": "Simply speak or type your question. The kiosk will understand your query and provide relevant information. You can ask in English or Hindi.",
                "metadata": {"category": "help", "language": "en"},
                "category": "help",
                "language": "en"
            }
        ]
        
        for doc in sample_docs:
            # Generate embedding
            embedding = self.embedding_model.encode(doc["content"])
            await self.add_document(
                doc["title"], 
                doc["content"], 
                embedding.tolist(),
                doc["metadata"],
                doc["category"],
                doc["language"]
            )
    
    async def add_document(self, title: str, content: str, embedding: List[float], 
                          metadata: Optional[Dict] = None, category: str = "general", 
                          language: str = "en") -> int:
        """Add a document to the knowledge base."""
        try:
            doc_id = self.document_model.add_document(
                title, content, embedding, metadata, category, language
            )
            logger.debug(f"Added document: {title} (ID: {doc_id})")
            return doc_id
            
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            raise
    
    async def search(self, query: str, limit: int = 3, category: Optional[str] = None, 
                    language: Optional[str] = None) -> List[Dict]:
        """
        Search for relevant documents.
        
        Args:
            query: Search query
            limit: Maximum number of results
            category: Optional category filter
            language: Optional language filter
            
        Returns:
            List of relevant documents
        """
        if not self.is_initialized:
            logger.warning("RAG not initialized")
            return []
        
        try:
            logger.debug(f"Searching for: {query}")
            
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query)
            
            # Search using document model
            results = self.document_model.search_documents(
                query_embedding.tolist(), limit, category, language
            )
            
            logger.debug(f"Found {len(results)} relevant documents")
            return results
            
        except Exception as e:
            logger.error(f"Error in RAG search: {e}")
            return []
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.db_manager:
            self.db_manager.disconnect()
        self.embedding_model = None
        logger.info("RAG component cleaned up")

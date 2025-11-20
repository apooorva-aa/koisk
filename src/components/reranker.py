"""
Reranker component for improving retrieval relevance in RAG pipeline.

Uses cross-encoder models to rerank retrieved documents based on query relevance.
Supports both local models (BGE reranker) and API-based rerankers.
"""

import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class RerankerComponent:
    """Reranks retrieved documents using cross-encoder models for better relevance."""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the reranker component.
        
        Args:
            config: Configuration dictionary with reranker settings
        """
        self.config = config or {}
        self.model = None
        self.is_initialized = False
        self.use_reranker = self.config.get('use_reranker', True)
        self.model_name = self.config.get('reranker_model', 'BAAI/bge-reranker-base')
        self.top_k = self.config.get('final_top_k', 5)
        
    async def initialize(self):
        """Initialize the reranker model."""
        if not self.use_reranker:
            logger.info("Reranker is disabled in configuration")
            self.is_initialized = True
            return
            
        try:
            logger.info(f"Initializing reranker with model: {self.model_name}")
            
            # Import here to avoid dependency issues if not used
            from sentence_transformers import CrossEncoder
            
            # Load the cross-encoder model
            self.model = CrossEncoder(self.model_name, max_length=512)
            
            self.is_initialized = True
            logger.info(f"Reranker initialized successfully with {self.model_name}")
            
        except ImportError:
            logger.warning(
                "sentence-transformers not installed. Reranking disabled. "
                "Install with: pip install sentence-transformers"
            )
            self.use_reranker = False
            self.is_initialized = False
        except Exception as e:
            logger.error(f"Failed to initialize reranker: {e}")
            self.use_reranker = False
            self.is_initialized = False
    
    async def rerank(
        self, 
        query: str, 
        documents: List[Dict],
        top_k: Optional[int] = None
    ) -> List[Dict]:
        """
        Rerank documents based on relevance to the query.
        
        Args:
            query: The search query
            documents: List of document dicts with 'content' field
            top_k: Number of top results to return (defaults to config value)
            
        Returns:
            List of reranked documents with added 'rerank_score' field
        """
        if not self.use_reranker or not self.is_initialized:
            logger.debug("Reranker not available, returning documents as-is")
            return documents[:top_k or self.top_k]
        
        if not documents:
            return []
        
        try:
            k = top_k or self.top_k
            
            # Prepare query-document pairs for cross-encoder
            pairs = [[query, doc.get('content', '')] for doc in documents]
            
            # Get relevance scores from cross-encoder
            scores = self.model.predict(pairs)
            
            # Add rerank scores to documents
            for doc, score in zip(documents, scores):
                doc['rerank_score'] = float(score)
            
            # Sort by rerank score (descending)
            reranked_docs = sorted(
                documents, 
                key=lambda x: x.get('rerank_score', -float('inf')), 
                reverse=True
            )
            
            # Return top-k results
            top_results = reranked_docs[:k]
            
            if top_results:
                logger.info(
                    f"Reranked {len(documents)} documents to top {len(top_results)}. "
                    f"Top score: {top_results[0]['rerank_score']:.3f}"
                )
            
            return top_results
            
        except Exception as e:
            logger.error(f"Error during reranking: {e}")
            # Fallback to original ranking
            return documents[:top_k or self.top_k]
    
    def rerank_sync(
        self, 
        query: str, 
        documents: List[Dict],
        top_k: Optional[int] = None
    ) -> List[Dict]:
        """
        Synchronous version of rerank for compatibility.
        
        Args:
            query: The search query
            documents: List of document dicts with 'content' field
            top_k: Number of top results to return
            
        Returns:
            List of reranked documents
        """
        if not self.use_reranker or not self.is_initialized:
            return documents[:top_k or self.top_k]
        
        if not documents:
            return []
        
        try:
            k = top_k or self.top_k
            
            # Prepare query-document pairs
            pairs = [[query, doc.get('content', '')] for doc in documents]
            
            # Get scores
            scores = self.model.predict(pairs)
            
            # Add scores and sort
            for doc, score in zip(documents, scores):
                doc['rerank_score'] = float(score)
            
            reranked_docs = sorted(
                documents, 
                key=lambda x: x.get('rerank_score', -float('inf')), 
                reverse=True
            )
            
            return reranked_docs[:k]
            
        except Exception as e:
            logger.error(f"Error during reranking: {e}")
            return documents[:top_k or self.top_k]
    
    async def cleanup(self):
        """Clean up resources."""
        if self.model is not None:
            del self.model
            self.model = None
        self.is_initialized = False
        logger.info("Reranker component cleaned up")


def create_reranker(config: Optional[Dict] = None) -> RerankerComponent:
    """
    Factory function to create a reranker component.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        RerankerComponent instance
    """
    return RerankerComponent(config)

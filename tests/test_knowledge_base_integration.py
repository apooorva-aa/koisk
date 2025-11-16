#!/usr/bin/env python3
"""
Integration test for Knowledge Base Repository with pgvector.
Tests that the scraper can successfully ingest documents into PostgreSQL.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from repositories.knowledge_base_repository import KnowledgeBaseRepository
from schemas.knowledge_base import DocumentMetadata
from services.settings import get_settings
from sentence_transformers import SentenceTransformer


async def test_integration():
    """Test the complete integration flow."""
    print("=" * 80)
    print("Knowledge Base Integration Test")
    print("=" * 80)
    
    # Load settings
    settings = get_settings()
    print(f"\n✓ Settings loaded:")
    print(f"  - Database URL: {settings.VECTOR_DB_URL}")
    print(f"  - Embedding Model: {settings.EMBEDDING_MODEL}")
    print(f"  - Vector Dimensions: {settings.VECTOR_DIMENSIONS}")
    print(f"  - Use IVFFLAT: {settings.USE_IVFFLAT}")
    
    # Initialize repository
    print("\n1. Initializing repository...")
    repo = KnowledgeBaseRepository()
    try:
        await repo.initialize()
        print("   ✓ Repository initialized successfully")
    except Exception as e:
        print(f"   ✗ Failed to initialize repository: {e}")
        return False
    
    # Load embedding model
    print("\n2. Loading embedding model...")
    try:
        embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
        print(f"   ✓ Embedding model loaded: {settings.EMBEDDING_MODEL}")
    except Exception as e:
        print(f"   ✗ Failed to load embedding model: {e}")
        await repo.close()
        return False
    
    # Create test document
    print("\n3. Creating test document...")
    test_content = """
    ABV-IIITM Gwalior is a premier technical institution located in Gwalior, Madhya Pradesh.
    The institute offers undergraduate and postgraduate programs in computer science,
    engineering, and information technology. The campus features modern facilities including
    a well-equipped library, sports complex, and student hostels.
    """
    
    try:
        # Generate embedding
        embedding = embedding_model.encode(test_content).tolist()
        print(f"   ✓ Generated embedding (dim: {len(embedding)})")
        
        # Create metadata
        metadata = DocumentMetadata(
            source="https://iiitm.ac.in/test",
            rule_id="test_001",
            chunk_index=0,
            total_chunks=1,
            title="Test Document - IIITM Overview",
            category="general",
            framework="Campus",
            tags=["test", "campus", "education"],
            language="en",
            created_at="2025-11-16T00:00:00Z",
            updated_at="2025-11-16T00:00:00Z"
        )
        print(f"   ✓ Created metadata: {metadata.title}")
        
        # Insert document
        document = await repo.create_document(
            content=test_content,
            metadata=metadata,
            embedding=embedding
        )
        print(f"   ✓ Document inserted with ID: {document.id}")
        
    except Exception as e:
        print(f"   ✗ Failed to create document: {e}")
        import traceback
        traceback.print_exc()
        await repo.close()
        return False
    
    # Test search
    print("\n4. Testing vector search...")
    try:
        query = "Tell me about IIITM campus facilities"
        query_embedding = embedding_model.encode(query).tolist()
        
        results = await repo.search_similar_documents(
            query_embedding=query_embedding,
            k=5
        )
        
        print(f"   ✓ Search completed, found {len(results)} results")
        if results:
            print(f"   ✓ Top result similarity: {results[0].similarity_score:.4f}")
            print(f"   ✓ Top result title: {results[0].document.metadata.get('title', 'N/A')}")
    
    except Exception as e:
        print(f"   ✗ Search failed: {e}")
        import traceback
        traceback.print_exc()
        await repo.close()
        return False
    
    # Get stats
    print("\n5. Getting knowledge base statistics...")
    try:
        stats = await repo.get_knowledge_base_stats()
        print(f"   ✓ Total documents: {stats.total_documents}")
        print(f"   ✓ Unique sources: {stats.unique_sources}")
        print(f"   ✓ Categories: {stats.categories}")
        print(f"   ✓ Frameworks: {stats.frameworks}")
    except Exception as e:
        print(f"   ✗ Failed to get stats: {e}")
        await repo.close()
        return False
    
    # Cleanup
    print("\n6. Cleaning up test data...")
    try:
        deleted = await repo.delete_documents_by_source("https://iiitm.ac.in/test")
        print(f"   ✓ Deleted {deleted} test document(s)")
    except Exception as e:
        print(f"   ✗ Failed to cleanup: {e}")
    
    await repo.close()
    print("\n" + "=" * 80)
    print("✓ All tests passed successfully!")
    print("=" * 80)
    return True


async def main():
    """Main entry point."""
    try:
        success = await test_integration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

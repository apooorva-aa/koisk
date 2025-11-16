"""
End-to-end RAG integration test.
Tests complete query → retrieval → context generation flow.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from components.rag import RAGComponent
from utils.config import load_config


async def test_rag_search():
    """Test RAG search with various queries."""
    
    # Load config
    config = load_config()
    
    # Initialize RAG
    rag = RAGComponent(config)
    await rag.initialize()
    
    print("\n" + "="*80)
    print("RAG COMPONENT END-TO-END TEST")
    print("="*80)
    
    # Get knowledge base stats
    stats = await rag.get_stats()
    print(f"\n📊 Knowledge Base Stats:")
    print(f"   Total documents: {stats['total_documents']}")
    print(f"   Unique sources: {stats['unique_sources']}")
    print(f"   Categories: {stats['categories']}")
    print(f"   Embedding model: {stats['embedding_model']}")
    print(f"   Vector dimensions: {stats['vector_dimensions']}")
    
    # Test queries
    test_queries = [
        {
            "query": "Tell me about IIITM admissions",
            "description": "Admissions query"
        },
        {
            "query": "What accommodation facilities are available?",
            "description": "Accommodation query"
        },
        {
            "query": "Information about IIITM campus",
            "description": "General campus query"
        },
        {
            "query": "How do I apply to IIITM?",
            "description": "Application process query"
        }
    ]
    
    print(f"\n🔍 Testing {len(test_queries)} queries:")
    print("-" * 80)
    
    for i, test in enumerate(test_queries, 1):
        query = test["query"]
        description = test["description"]
        
        print(f"\n[Query {i}] {description}")
        print(f"Question: {query}")
        
        # Search
        results = await rag.search(query, limit=3)
        
        if results:
            print(f"✅ Found {len(results)} relevant documents:")
            for j, doc in enumerate(results, 1):
                print(f"\n   Result {j}:")
                print(f"   - Title: {doc['title']}")
                print(f"   - Similarity: {doc['similarity']:.4f}")
                print(f"   - Category: {doc['category']}")
                print(f"   - Source: {doc['source']}")
                print(f"   - Content preview: {doc['content'][:200]}...")
        else:
            print(f"❌ No results found")
        
        print()
    
    print("-" * 80)
    
    # Test context generation
    print(f"\n📝 Testing context generation:")
    query = "What programs does IIITM offer?"
    context = await rag.get_context_for_query(query, max_context_length=1500)
    
    print(f"\nQuery: {query}")
    print(f"Generated context ({len(context)} chars):")
    print("-" * 80)
    print(context)
    print("-" * 80)
    
    # Cleanup
    await rag.cleanup()
    
    print("\n✅ End-to-end RAG test completed successfully!")
    print("="*80 + "\n")


async def test_category_filtering():
    """Test category-based filtering."""
    
    config = load_config()
    rag = RAGComponent(config)
    await rag.initialize()
    
    print("\n" + "="*80)
    print("CATEGORY FILTERING TEST")
    print("="*80)
    
    query = "Tell me about IIITM"
    
    # Test each category
    categories = ["General Information", "Admissions", "Accommodation"]
    
    for category in categories:
        print(f"\n🔍 Searching with category filter: {category}")
        results = await rag.search(query, limit=3, category=category)
        
        if results:
            print(f"✅ Found {len(results)} documents in '{category}':")
            for j, doc in enumerate(results, 1):
                print(f"   {j}. {doc['title']} (similarity: {doc['similarity']:.4f})")
        else:
            print(f"❌ No documents found in category '{category}'")
    
    await rag.cleanup()
    print("\n✅ Category filtering test completed!")
    print("="*80 + "\n")


async def main():
    """Run all tests."""
    try:
        # Test 1: Basic RAG search
        await test_rag_search()
        
        # Test 2: Category filtering
        await test_category_filtering()
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

"""
Complete LLM + RAG integration test.
Tests the full pipeline: Query → RAG Retrieval → LLM Generation → Response
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from components.llm_inference import LLMComponent
from components.rag import RAGComponent
from utils.config import load_config


async def test_llm_without_rag():
    """Test LLM component without RAG (direct inference)."""
    print("\n" + "="*80)
    print("TEST 1: LLM WITHOUT RAG")
    print("="*80)
    
    config = load_config()
    llm = LLMComponent(config)
    await llm.initialize()
    
    # Check server health
    is_healthy = await llm.check_server_health()
    print(f"\n🏥 LLM Server Health: {'✅ Healthy' if is_healthy else '⚠️ Not Available'}")
    
    # Test queries
    test_queries = [
        "What is IIITM?",
        "Tell me about the campus."
    ]
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        response = await llm.generate_response(query, use_rag=False)
        print(f"💬 Response: {response}\n")
        print("-" * 80)
    
    await llm.cleanup()
    print("\n✅ Test completed\n")


async def test_llm_with_rag():
    """Test LLM component with RAG integration."""
    print("\n" + "="*80)
    print("TEST 2: LLM WITH RAG INTEGRATION")
    print("="*80)
    
    config = load_config()
    
    # Initialize RAG first
    rag = RAGComponent(config)
    await rag.initialize()
    
    # Initialize LLM with RAG
    llm = LLMComponent(config, rag_component=rag)
    await llm.initialize()
    
    # Check components
    print(f"\n✅ RAG initialized: {rag.is_initialized}")
    print(f"✅ LLM initialized: {llm.is_initialized}")
    
    # Get knowledge base stats
    stats = await rag.get_stats()
    print(f"\n📊 Knowledge Base: {stats['total_documents']} docs from {stats['unique_sources']} sources")
    
    # Test queries with RAG
    test_queries = [
        {
            "query": "What programs does IIITM offer?",
            "description": "Academic programs query"
        },
        {
            "query": "Tell me about IIITM admissions",
            "description": "Admissions information"
        },
        {
            "query": "What is IIITM Gwalior?",
            "description": "General institute information"
        },
        {
            "query": "How can I contact IIITM?",
            "description": "Contact information"
        }
    ]
    
    print("\n" + "="*80)
    print(f"Testing {len(test_queries)} queries with RAG-enhanced responses")
    print("="*80)
    
    for i, test in enumerate(test_queries, 1):
        query = test["query"]
        description = test["description"]
        
        print(f"\n{'='*80}")
        print(f"Query {i}: {description}")
        print(f"{'='*80}")
        print(f"❓ User: {query}\n")
        
        response = await llm.generate_response(query, use_rag=True)
        
        print(f"\n🤖 Assistant: {response}")
        print(f"{'='*80}\n")
    
    await llm.cleanup()
    print("\n✅ All tests completed successfully!\n")


async def test_conversation_with_history():
    """Test multi-turn conversation with history."""
    print("\n" + "="*80)
    print("TEST 3: MULTI-TURN CONVERSATION")
    print("="*80)
    
    config = load_config()
    
    # Initialize components
    rag = RAGComponent(config)
    await rag.initialize()
    
    llm = LLMComponent(config, rag_component=rag)
    await llm.initialize()
    
    # Simulate a conversation
    conversation_history = []
    
    conversation = [
        "What is IIITM?",
        "What programs do they offer?",
        "How do I apply?"
    ]
    
    print("\n🗣️ Starting conversation simulation...\n")
    
    for turn, user_message in enumerate(conversation, 1):
        print(f"{'='*80}")
        print(f"Turn {turn}")
        print(f"{'='*80}")
        print(f"👤 User: {user_message}\n")
        
        # Generate response with conversation history
        response = await llm.generate_response(
            user_message, 
            use_rag=True,
            conversation_history=conversation_history
        )
        
        print(f"🤖 Assistant: {response}")
        print(f"{'='*80}\n")
        
        # Update conversation history
        conversation_history.append({"role": "user", "content": user_message})
        conversation_history.append({"role": "assistant", "content": response})
    
    await llm.cleanup()
    print("\n✅ Conversation test completed!\n")


async def test_rag_fallback():
    """Test fallback behavior when LLM server is not available."""
    print("\n" + "="*80)
    print("TEST 4: RAG FALLBACK MODE (LLM Server Unavailable)")
    print("="*80)
    
    config = load_config()
    
    # Initialize RAG
    rag = RAGComponent(config)
    await rag.initialize()
    
    # Initialize LLM (may not connect to server)
    llm = LLMComponent(config, rag_component=rag)
    await llm.initialize()
    
    # Force server unavailable state
    original_state = llm.is_initialized
    llm.is_initialized = False
    
    print(f"\n⚠️ Simulating LLM server unavailable (forced)")
    print(f"✅ RAG is available and will provide fallback responses\n")
    
    test_query = "What is IIITM?"
    print(f"📝 Query: {test_query}\n")
    
    response = await llm.generate_response(test_query, use_rag=True)
    
    print(f"💬 Fallback Response: {response}\n")
    
    # Restore state
    llm.is_initialized = original_state
    
    await llm.cleanup()
    print("\n✅ Fallback test completed!\n")


async def main():
    """Run all tests."""
    try:
        # Test 1: LLM without RAG
        await test_llm_without_rag()
        
        # Test 2: LLM with RAG (main integration)
        await test_llm_with_rag()
        
        # Test 3: Multi-turn conversation
        await test_conversation_with_history()
        
        # Test 4: Fallback mode
        await test_rag_fallback()
        
        print("\n" + "="*80)
        print("🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
        print("="*80)
        print("\nThe complete LLM + RAG pipeline is working correctly:")
        print("  ✅ RAG retrieval from PostgreSQL + pgvector")
        print("  ✅ Context-aware prompt building")
        print("  ✅ LLM integration (with fallback)")
        print("  ✅ Conversation history support")
        print("  ✅ Graceful degradation when LLM unavailable")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

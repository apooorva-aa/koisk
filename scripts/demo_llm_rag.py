import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from components.llm_inference import LLMComponent
from components.rag import RAGComponent
from utils.config import load_config

async def main():
    config = load_config()
    print("\nInitializing RAG component...")
    rag = RAGComponent(config)
    await rag.initialize()
    stats = await rag.get_stats()
    print(f"Knowledge Base: {stats['total_documents']} documents loaded")
    print("\nInitializing LLM component...")
    llm = LLMComponent(config, rag_component=rag)
    await llm.initialize()
    
    server_healthy = await llm.check_server_health()
    if server_healthy:
        print("LLM Server: Running")
    else:
        print("LLM Server: Not available (will use RAG fallback mode)")
    
    print("\n" + "="*80)
    print("Demo Query")
    print("="*80)
    query = "What programs does IIITM offer?"
    print(f"\nUser: {query}\n")
    response = await llm.generate_response(query, use_rag=True) 
    print(f"Assistant: {response}\n")
    print("="*80)
    await llm.cleanup()
    print("\nDemo completed successfully.\n")

if __name__ == "__main__":
    asyncio.run(main())

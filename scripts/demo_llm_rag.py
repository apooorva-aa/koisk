import asyncio
import sys
from pathlib import Path
from typing import List, Dict

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from components.llm_inference import LLMComponent
from components.rag import RAGComponent
from components.reranker import RerankerComponent
from utils.config import load_config


class ConversationalChatbot:
    """Interactive chatbot with conversation history."""
    
    def __init__(self, llm: LLMComponent, rag: RAGComponent):
        self.llm = llm
        self.rag = rag
        self.conversation_history: List[Dict[str, str]] = []
        self.max_history = 10  # Keep last 10 exchanges
    
    def add_to_history(self, role: str, content: str):
        """Add a message to conversation history."""
        self.conversation_history.append({
            "role": role,
            "content": content
        })
        # Keep only recent history
        if len(self.conversation_history) > self.max_history * 2:
            self.conversation_history = self.conversation_history[-self.max_history * 2:]
    
    def print_welcome(self):
        """Print welcome message."""
        print("\n" + "="*80)
        print("🤖 IIITM Gwalior Information Assistant")
        print("="*80)
        print("Ask me anything about IIITM Gwalior!")
        print("Type 'done' or 'exit' to quit")
        print("Type 'clear' to clear conversation history")
        print("="*80 + "\n")
    
    async def chat(self):
        """Main chat loop."""
        self.print_welcome()
        
        while True:
            try:
                # Get user input
                user_input = input("You: ").strip()
                
                # Check for exit commands
                if user_input.lower() in ['done', 'exit', 'quit', 'bye']:
                    print("\nGoodbye! Thank you for using the IIITM Information Assistant.\n")
                    break
                
                # Check for clear command
                if user_input.lower() == 'clear':
                    self.conversation_history.clear()
                    print("\n✓ Conversation history cleared.\n")
                    continue
                
                # Skip empty input
                if not user_input:
                    continue
                
                # Add user message to history
                self.add_to_history("user", user_input)
                
                # Generate response
                print("\nThinking...\n")
                response = await self.llm.generate_response(
                    user_input, 
                    use_rag=True,
                    conversation_history=self.conversation_history
                )
                
                if response:
                    # Add assistant response to history
                    self.add_to_history("assistant", response)
                    
                    # Print response
                    print(f"Assistant: {response}\n")
                else:
                    print("Assistant: I apologize, but I couldn't generate a response. Please try again.\n")
                
                print("-" * 80 + "\n")
                
            except KeyboardInterrupt:
                print("\n\nInterrupted. Goodbye!\n")
                break
            except Exception as e:
                print(f"\nError: {e}\n")
                print("Please try again.\n")


async def main():
    """Initialize components and start chatbot."""
    config = load_config()
    
    print("\nInitializing IIITM Information Assistant...")
    print("=" * 80)
    
    # Initialize RAG
    print("\nLoading knowledge base...")
    rag = RAGComponent(config)
    await rag.initialize()
    stats = await rag.get_stats()
    print(f"✓ Loaded {stats['total_documents']} documents")
    
    # Initialize Reranker
    print("\nreranker...")
    rag_config = config.get('rag', {})
    reranker = RerankerComponent(rag_config)
    await reranker.initialize()
    print("✓ Reranker ready")
    
    # Initialize LLM
    print("\nInitializing language model...")
    llm = LLMComponent(config, rag_component=rag, reranker_component=reranker)
    await llm.initialize()
    
    # Check server health
    server_healthy = await llm.check_server_health()
    if server_healthy:
        print("✓ LLM Server running")
    else:
        print("⚠ LLM Server not available (using RAG fallback mode)")
    
    print("\n" + "=" * 80)
    
    # Start chatbot
    chatbot = ConversationalChatbot(llm, rag)
    await chatbot.chat()
    
    # Cleanup
    print("Cleaning up...")
    await llm.cleanup()
    await rag.cleanup()
    await reranker.cleanup()
    print("✓ Done!\n")


if __name__ == "__main__":
    asyncio.run(main())

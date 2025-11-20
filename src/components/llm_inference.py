import logging
import requests
from typing import Optional, List, Dict
import time

logger = logging.getLogger(__name__)


class LLMComponent:
    def __init__(self, config, rag_component=None, reranker_component=None):
        self.config = config
        self.rag_component = rag_component
        self.reranker_component = reranker_component
        self.server_url = None
        self.max_tokens = None
        self.temperature = None
        self.is_initialized = False
        self.use_rag = True
        self.use_reranker = config.get('rag', {}).get('use_reranker', True) if config else True
        
    async def initialize(self):
        try:
            logger.info("Initializing LLM component...")
            llm_config = self.config.get('llm', {})
            self.server_url = llm_config.get('server_url', 'http://localhost:8080')
            self.max_tokens = llm_config.get('max_tokens', 150)
            self.temperature = llm_config.get('temperature', 0.7)
            try:
                response = requests.get(f"{self.server_url}/v1/models", timeout=5)
                if response.status_code == 200:
                    logger.info(f"Llama.cpp server is running at {self.server_url}")
                    self.is_initialized = True
                else:
                    logger.warning(f"Llama.cpp server responded with status {response.status_code}")
                    self.is_initialized = False
            except requests.exceptions.RequestException as e:
                logger.warning(f"Llama.cpp server not available at {self.server_url}: {e}")
                logger.info("Will attempt to start server or use fallback mode")
                self.is_initialized = False
            if self.rag_component and not self.rag_component.is_initialized:
                logger.info("Initializing RAG component...")
                await self.rag_component.initialize()
                logger.info("RAG component initialized successfully")
            
            if self.reranker_component and not self.reranker_component.is_initialized:
                logger.info("Initializing reranker component...")
                await self.reranker_component.initialize()
                logger.info("Reranker component initialized successfully")
            
            logger.info("LLM component initialization complete")
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            raise
    
    def _build_system_prompt(self) -> str:
        return """You are an IIITM Gwalior information assistant.
Answer questions using ONLY the CONTEXT below. Be brief and accurate.
If the answer isn't in the CONTEXT, say "I don't have that information."
Do NOT start with "According to" or "Based on" - answer directly."""

    def _format_rag_context(self, rag_results: List[Dict], use_rerank_order: bool = False) -> str:
        """Format RAG results with improved context presentation."""
        if not rag_results:
            return ""
        
        # IMPORTANT: Don't re-sort if using reranked results!
        # Reranked results are already in optimal order
        if not use_rerank_order:
            # Only sort by similarity if NOT reranked
            sorted_results = sorted(rag_results, key=lambda x: x.get('similarity', 0), reverse=True)
        else:
            # Use the order as-is (already reranked)
            sorted_results = rag_results
        
        context_parts = ["CONTEXT:"]
        for i, doc in enumerate(sorted_results[:5], 1):
            # Include source attribution for better traceability
            source = doc.get('title', 'Unknown')
            content = doc['content'][:600]  # Slightly longer chunks
            
            # Show rerank score if available, otherwise similarity
            score_info = ""
            if 'rerank_score' in doc:
                score_info = f" (relevance: {doc['rerank_score']:.3f})"
            elif 'similarity' in doc:
                score_info = f" (similarity: {doc['similarity']:.3f})"
            
            context_parts.append(f"\n[Source {i}: {source}{score_info}]\n{content}")
        
        return "\n".join(context_parts)

    def _build_prompt(self, user_query: str, rag_context: str, conversation_history: Optional[List[Dict]] = None) -> str:
        prompt_parts = [self._build_system_prompt()]
        if rag_context:
            prompt_parts.append(f"\n{rag_context}")
        prompt_parts.append(f"\n\nQuestion: {user_query}")
        prompt_parts.append("Answer:")
        return "\n".join(prompt_parts)

    async def generate_response(self, prompt: str, use_rag: bool = True, conversation_history: Optional[List[Dict]] = None) -> Optional[str]:
        try:
            start_time = time.time()
            logger.info(f"Processing query: {prompt}")
            rag_context = ""
            rag_results = None
            if use_rag and self.rag_component:
                logger.info("Searching knowledge base...")
                # Retrieve more results initially (20) for better coverage
                rag_results = await self.rag_component.search(
                    prompt, 
                    limit=20,  # Increased from 5 to 20 for reranking
                    similarity_threshold=0.3  # Lowered threshold to get more candidates
                )
                if rag_results:
                    logger.info(f"Found {len(rag_results)} relevant documents (top similarity: {rag_results[0]['similarity']:.3f})")
                    
                    # Track if we used reranking
                    used_reranking = False
                    
                    # Apply reranking if available
                    if self.use_reranker and self.reranker_component and self.reranker_component.is_initialized:
                        logger.info("Applying reranking to improve relevance...")
                        rag_results = await self.reranker_component.rerank(
                            query=prompt,
                            documents=rag_results,
                            top_k=5
                        )
                        if rag_results:
                            used_reranking = True
                            logger.info(f"Reranked to top {len(rag_results)} documents (top rerank score: {rag_results[0].get('rerank_score', 'N/A'):.3f})")
                            
                            # DEBUG: Log reranked order
                            logger.debug("Reranked document order:")
                            for i, doc in enumerate(rag_results[:5], 1):
                                logger.debug(f"  {i}. [Rerank: {doc.get('rerank_score', 0):.3f}] {doc.get('title', 'Unknown')[:50]}")
                    else:
                        # Fallback: take top 5 from the 20 results without reranking
                        rag_results = rag_results[:5]
                    
                    # Format context - preserve rerank order!
                    rag_context = self._format_rag_context(rag_results, use_rerank_order=used_reranking)
                    
                    # DEBUG: Log what's being sent to LLM
                    logger.debug(f"Context being sent to LLM (first 500 chars):\n{rag_context[:500]}")
                else:
                    logger.info("No relevant documents found in knowledge base")
            full_prompt = self._build_prompt(prompt, rag_context, conversation_history)
            logger.debug(f"Full prompt length: {len(full_prompt)} chars")
            if self.is_initialized:
                logger.info("Generating response from LLM...")
                response_text = await self._call_llm_server(full_prompt)
            else:
                logger.warning("LLM server not available, using fallback mode")
                response_text = self._generate_fallback_response(prompt, rag_results if use_rag else None)
            
            elapsed = time.time() - start_time
            logger.info(f"Response generated in {elapsed:.2f}s")
            logger.debug(f"Response preview: {response_text[:100]}...")
            
            return response_text
            
        except Exception as e:
            logger.error(f"Error in LLM generation: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def _call_llm_server(self, prompt: str) -> str:
        try:
            payload = {
                "prompt": prompt,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "top_p": 0.9,
                "top_k": 40, 
                "repeat_penalty": 1.1,
                "stop": [
                    "User:", "Assistant:", 
                    "\n\nUser:", "\n\nAssistant:",
                    "===", "[END]", 
                    "\n\n\n"
                ],
                "stream": False
            }
            
            response = requests.post(
                f"{self.server_url}/v1/completions",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                choices = result.get("choices", [])
                if choices:
                    generated_text = choices[0].get("text", "").strip()
                    generated_text = self._post_process_response(generated_text)
                    return generated_text if generated_text else "I'm sorry, I couldn't generate a response."
                else:
                    return "I'm sorry, I couldn't generate a response."
            else:
                logger.error(f"LLM server error: {response.status_code} - {response.text}")
                return "I'm experiencing technical difficulties. Please try again."
                
        except requests.exceptions.Timeout:
            logger.error("LLM server timeout")
            return "The request took too long. Please try a simpler question."
        except Exception as e:
            logger.error(f"Error calling LLM server: {e}")
            raise
    
    def _post_process_response(self, text: str) -> str:
        for marker in ["User:", "Assistant:", "CONTEXT", "===", "[Document"]:
            if marker in text:
                text = text.split(marker)[0]
        while "\n\n\n" in text:
            text = text.replace("\n\n\n", "\n\n")
        text = text.strip()
        avoid_phrases = [
            "based on the context",
            "according to the provided information",
            "from the knowledge base",
            "the context shows"
        ]
        
        text_lower = text.lower()
        for phrase in avoid_phrases:
            if text_lower.startswith(phrase):
                parts = text.split(":", 1)
                if len(parts) > 1:
                    text = parts[1].strip()
                    if text:
                        text = text[0].upper() + text[1:]
        return text

    def _generate_fallback_response(self, query: str, rag_results: Optional[List[Dict]] = None) -> str:
        if rag_results and len(rag_results) > 0:
            top_result = rag_results[0]
            return f"Based on the knowledge base: {top_result['content'][:200]}... (Source: {top_result['title']})"
        else:
            return "I apologize, but I'm unable to process your request at the moment. The LLM server is not available and I couldn't find relevant information in the knowledge base."
    
    async def check_server_health(self) -> bool:
        try:
            response = requests.get(f"{self.server_url}/v1/models", timeout=2)
            return response.status_code == 200
        except Exception:
            return False

    async def cleanup(self):
        if self.rag_component:
            await self.rag_component.cleanup()
        if self.reranker_component:
            await self.reranker_component.cleanup()
        logger.info("LLM component cleaned up")

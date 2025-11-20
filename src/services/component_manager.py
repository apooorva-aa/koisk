from components.face_detection import FaceDetector
from components.asr import ASRComponent
from components.llm_inference import LLMComponent
from components.rag import RAGComponent
from components.reranker import RerankerComponent
from components.tts import TTSComponent
from components.session_manager import SessionManager

class ComponentManager:
    def __init__(self, config):
        self.config = config
        self.face_detector = FaceDetector(config)
        self.asr = ASRComponent(config)
        self.rag = RAGComponent(config)
        
        # Initialize reranker component
        rag_config = config.get('rag', {})
        self.reranker = RerankerComponent(rag_config)
        
        # Pass both RAG and reranker to LLM component
        self.llm = LLMComponent(config, rag_component=self.rag, reranker_component=self.reranker)
        
        self.tts = TTSComponent(config)
        self.session_manager = SessionManager(config)

    async def initialize_all(self):
        await self.asr.initialize()
        await self.rag.initialize()
        await self.reranker.initialize()
        await self.llm.initialize()
        await self.tts.initialize()
        await self.session_manager.initialize()

    async def cleanup_all(self):
        await self.session_manager.cleanup()
        await self.tts.cleanup()
        await self.llm.cleanup()
        await self.reranker.cleanup()
        await self.asr.cleanup()
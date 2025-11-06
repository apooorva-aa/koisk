from components.face_detection import FaceDetector
from components.asr import ASRComponent
from components.llm_inference import LLMComponent
from components.rag import RAGComponent
from components.tts import TTSComponent
from components.session_manager import SessionManager

class ComponentManager:
    def __init__(self, config):
        self.config = config
        self.face_detector = FaceDetector(config)
        self.asr = ASRComponent(config)
        self.llm = LLMComponent(config)
        self.rag = RAGComponent(config)
        self.tts = TTSComponent(config)
        self.session_manager = SessionManager(config)

    async def initialize_all(self):
        await self.asr.initialize()
        await self.llm.initialize()
        await self.rag.initialize()
        await self.tts.initialize()
        await self.session_manager.initialize()

    async def cleanup_all(self):
        await self.session_manager.cleanup()
        await self.tts.cleanup()
        await self.llm.cleanup()
        await self.asr.cleanup()
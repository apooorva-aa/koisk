# Components package
# Use lazy imports to avoid loading all dependencies when only one component is needed

__all__ = [
    'ASRComponent',
    'FaceDetector',
    'LLMComponent',
    'RAGComponent',
    'RerankerComponent',
    'SessionManager',
    'TTSComponent',
]

def __getattr__(name):
    """Lazy import components to avoid loading unnecessary dependencies."""
    if name == 'ASRComponent':
        from .asr import ASRComponent
        return ASRComponent
    elif name == 'FaceDetector':
        from .face_detection import FaceDetector
        return FaceDetector
    elif name == 'LLMComponent':
        from .llm_inference import LLMComponent
        return LLMComponent
    elif name == 'RAGComponent':
        from .rag import RAGComponent
        return RAGComponent
    elif name == 'RerankerComponent':
        from .reranker import RerankerComponent
        return RerankerComponent
    elif name == 'SessionManager':
        from .session_manager import SessionManager
        return SessionManager
    elif name == 'TTSComponent':
        from .tts import TTSComponent
        return TTSComponent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

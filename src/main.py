import asyncio
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

from utils.config import load_config
from utils.logging import setup_logging
from services.audio_recorder import record_user_voice
from services.component_manager import ComponentManager

# Setup logging
logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager: initialize components on startup and cleanup on shutdown.

    Uses app.state.components to store the ComponentManager instance so handlers can access it.
    """
    logger.info("Starting Koisk LLM system...")
    try:
        config = load_config()
        app.state.components = ComponentManager(config)
        await app.state.components.initialize_all()
        logger.info("All components initialized successfully!")
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        # If startup fails, exit the process with non-zero code
        sys.exit(1)

    try:
        yield # App runs here
    finally:
        logger.info("Shutting down Koisk LLM system...")
        comps = getattr(app.state, "components", None)
        if comps:
            await comps.cleanup_all()


app = FastAPI(
    title="Koisk LLM API",
    description="Fine-tuned LLM Koisk for India - Multilingual AI Assistant",
    version="0.1.0",
    lifespan=lifespan,
)
@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Koisk LLM API is running!", "status": "healthy"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    comps = getattr(app.state, "components", None)
    return {
        "status": "healthy",
        "components": {
            "face_detection": bool(getattr(comps, "face_detector", None)),
            "asr": bool(getattr(comps, "asr", None)),
            "llm": bool(getattr(comps, "llm", None)),
            "rag": bool(getattr(comps, "rag", None)),
            "tts": bool(getattr(comps, "tts", None)),
            "session_manager": bool(getattr(comps, "session_manager", None)),
        },
    }


@app.post("/interact")
async def interact(text: str = None):
    """Main interaction endpoint."""
    try:
        comps = getattr(app.state, "components", None)
        if not comps or not getattr(comps, "session_manager", None):
            raise HTTPException(status_code=503, detail="Session manager not initialized")
        
        # case 1 : text input bypasses ASR
        if text:
            user_input = text.strip()
        # case 2 : send to whisper ASR if audio file is provided
        else :
            if not getattr(comps, "asr", None):
                raise HTTPException(status_code=503, detail="ASR component not initialized")

            print("How may I help you? (Waiting for voice input...)")

            # start recording
            audio_np, sr = await record_user_voice(duration=5)

            # transcribe
            user_input = await comps.asr.transcribe_audio(audio_np, sr)

            if not user_input:
                raise HTTPException(status_code=500, detail="Voice not detected or transcription failed")
        
        # pass input to session manager for processing
        response = await comps.session_manager.process_interaction(user_input)

        return {
            "user_input": user_input,
            "response": response,
            "session_id": comps.session_manager.current_session_id,
        }
        
    except Exception as e:
        logger.error(f"Error in interaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def main():
    """Main application entry point."""
    
    logger.info("Starting Koisk LLM application...")
    
    # Run the FastAPI server
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())

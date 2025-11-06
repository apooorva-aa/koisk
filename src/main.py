#!/usr/bin/env python3
"""
Main application entry point for Koisk LLM system.
"""

import asyncio
import sys

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

from utils.config import load_config
from utils.logging import setup_logging
from services.audio_recorder import record_user_voice
from services.component_manager import ComponentManager

# Setup logging
logger = setup_logging()

app = FastAPI(
    title="Koisk LLM API",
    description="Fine-tuned LLM Koisk for India - Multilingual AI Assistant",
    version="0.1.0"
)

components = None

@app.on_event("startup")
async def startup_event():
    """Initialize all components on startup."""
    
    global components
    
    try:
        logger.info("Starting Koisk LLM system...")
        
        config = load_config()
        components = ComponentManager(config)    
        
        await components.initialize_all()
        
        logger.info("All components initialized successfully!")
        
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        sys.exit(1)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Koisk LLM system...")
    
    if components:
        await components.cleanup_all()


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Koisk LLM API is running!", "status": "healthy"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "components": {
            "face_detection": components.face_detector is not None,
            "asr": components.asr is not None,
            "llm": components.llm is not None,
            "rag": components.rag is not None,
            "tts": components.tts is not None,
            "session_manager": components.session_manager is not None
        }
    }


@app.post("/interact")
async def interact(text: str = None):
    """Main interaction endpoint."""
    try:
        if not components.session_manager:
            raise HTTPException(status_code=503, detail="Session manager not initialized")
        
        # case 1 : text input bypasses ASR
        if text:
            user_input = text.strip()
        # case 2 : send to whisper ASR if audio file is provided
        else :
            if not components.asr:
                raise HTTPException(status_code=503, detail="ASR component not initialized")

            print("How may I help you? (Waiting for voice input...)")

            # start recording
            audio_np, sr = await record_user_voice(duration=5)

            # transcribe
            user_input = await components.asr.transcribe_audio(audio_np, sr)

            if not user_input:
                raise HTTPException(status_code=500, detail="Voice not detected or transcription failed")
        
        # pass input to session manager for processing
        response = await components.session_manager.process_interaction(user_input)
        
        return {
            "user_input": user_input,
            "response": response,
            "session_id": components.session_manager.current_session_id
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

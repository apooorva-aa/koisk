#!/usr/bin/env python3
"""
Main application entry point for Koisk LLM system.
"""

import asyncio
import logging
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

from components.face_detection import FaceDetectionComponent
from components.asr import ASRComponent
from components.llm_inference import LLMComponent
from components.rag import RAGComponent
from components.tts import TTSComponent
from components.session_manager import SessionManager
from utils.config import load_config
from utils.logging import setup_logging

# Setup logging
logger = setup_logging()

app = FastAPI(
    title="Koisk LLM API",
    description="Fine-tuned LLM Koisk for India - Multilingual AI Assistant",
    version="0.1.0"
)

# Global components (will be initialized in startup)
face_detector = None
asr_component = None
llm_component = None
rag_component = None
tts_component = None
session_manager = None


@app.on_event("startup")
async def startup_event():
    """Initialize all components on startup."""
    global face_detector, asr_component, llm_component, rag_component, tts_component, session_manager
    
    try:
        logger.info("Starting Koisk LLM system...")
        
        # Load configuration
        config = load_config()
        
        # Initialize components
        face_detector = FaceDetectionComponent(config)
        asr_component = ASRComponent(config)
        llm_component = LLMComponent(config)
        rag_component = RAGComponent(config)
        tts_component = TTSComponent(config)
        session_manager = SessionManager(config)
        
        # Initialize components
        await face_detector.initialize()
        await asr_component.initialize()
        await llm_component.initialize()
        await rag_component.initialize()
        await tts_component.initialize()
        await session_manager.initialize()
        
        logger.info("All components initialized successfully!")
        
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        sys.exit(1)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Koisk LLM system...")
    
    if session_manager:
        await session_manager.cleanup()
    if tts_component:
        await tts_component.cleanup()
    if llm_component:
        await llm_component.cleanup()
    if asr_component:
        await asr_component.cleanup()
    if face_detector:
        await face_detector.cleanup()


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
            "face_detection": face_detector is not None,
            "asr": asr_component is not None,
            "llm": llm_component is not None,
            "rag": rag_component is not None,
            "tts": tts_component is not None,
            "session_manager": session_manager is not None
        }
    }


@app.post("/interact")
async def interact(text: str = None, audio_file: str = None):
    """Main interaction endpoint."""
    try:
        if not session_manager:
            raise HTTPException(status_code=503, detail="Session manager not initialized")
        
        # Process input (text or audio)
        if audio_file:
            # TODO: Process audio file through ASR
            user_input = "Hello from audio input"  # Placeholder
        elif text:
            user_input = text
        else:
            raise HTTPException(status_code=400, detail="Either text or audio_file must be provided")
        
        # Generate response
        response = await session_manager.process_interaction(user_input)
        
        return {
            "user_input": user_input,
            "response": response,
            "session_id": session_manager.current_session_id
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

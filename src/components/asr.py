"""
Automatic Speech Recognition (ASR) Component using Whisper.
Simplified implementation for initial development.
"""

import asyncio
import logging
import tempfile
from pathlib import Path
from typing import Optional
import whisper
import numpy as np

logger = logging.getLogger(__name__)


class ASRComponent:
    """ASR component using Whisper for speech-to-text conversion."""
    
    def __init__(self, config):
        self.config = config
        self.model = None
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize the ASR component."""
        try:
            logger.info("Initializing ASR component...")
            
            # Load Whisper model
            model_name = self.config.get('models', {}).get('whisper_model', 'base')
            logger.info(f"Loading Whisper model: {model_name}")
            
            self.model = whisper.load_model(model_name)
            
            self.is_initialized = True
            logger.info("ASR component initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize ASR: {e}")
            raise
    
    async def transcribe_audio(self, audio_data: np.ndarray, sample_rate: int = 16000) -> Optional[str]:
        """
        Transcribe audio data to text.
        
        Args:
            audio_data: Audio data as numpy array
            sample_rate: Sample rate of the audio
            
        Returns:
            Transcribed text or None if failed
        """
        if not self.is_initialized:
            logger.warning("ASR not initialized")
            return None
        
        try:
            logger.debug("Transcribing audio...")
            
            # Save audio to temporary file for Whisper
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_path = Path(temp_file.name)
                
                # Convert numpy array to audio file
                import soundfile as sf
                sf.write(temp_path, audio_data, sample_rate)
                
                # Transcribe using Whisper
                result = self.model.transcribe(str(temp_path))
                
                # Clean up temporary file
                temp_path.unlink()
                
                text = result["text"].strip()
                logger.debug(f"Transcribed text: {text}")
                
                return text if text else None
                
        except Exception as e:
            logger.error(f"Error in audio transcription: {e}")
            return None
    
    async def transcribe_file(self, audio_file_path: str) -> Optional[str]:
        """
        Transcribe audio file to text.
        
        Args:
            audio_file_path: Path to audio file
            
        Returns:
            Transcribed text or None if failed
        """
        if not self.is_initialized:
            logger.warning("ASR not initialized")
            return None
        
        try:
            logger.debug(f"Transcribing audio file: {audio_file_path}")
            
            result = self.model.transcribe(audio_file_path)
            text = result["text"].strip()
            
            logger.debug(f"Transcribed text: {text}")
            return text if text else None
            
        except Exception as e:
            logger.error(f"Error in file transcription: {e}")
            return None
    
    async def cleanup(self):
        """Cleanup resources."""
        self.model = None
        logger.info("ASR component cleaned up")

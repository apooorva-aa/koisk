"""
Configuration management utilities.
"""

import yaml
from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def load_config(config_path: str = "config/config.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
    """
    try:
        config_file = Path(config_path)
        
        if not config_file.exists():
            logger.warning(f"Config file not found: {config_path}, using defaults")
            return get_default_config()
        
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        logger.info(f"Loaded configuration from {config_path}")
        return config
        
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return get_default_config()


def get_default_config() -> Dict[str, Any]:
    """Get default configuration."""
    return {
        "hardware": {
            "camera_index": 0,
            "audio_device": "default"
        },
        "models": {
            "whisper_model": "base",
            "llm_model": "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
            "tts_voice": "en_US-ljspeech-medium",
            "embedding_model": "all-MiniLM-L6-v2"
        },
        "llm": {
            "server_url": "http://localhost:8080",
            "max_tokens": 150,
            "temperature": 0.7
        },
        "session": {
            "timeout_seconds": 300,
            "max_history": 10
        },
        "performance": {
            "max_memory_mb": 3072,
            "llm_threads": 4
        }
    }

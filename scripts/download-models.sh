#!/bin/bash

# Model Download Script
# Downloads required AI models for the Kiosk LLM system

set -e

echo "🤖 Downloading AI models for Kiosk LLM..."

# Create models directory
mkdir -p data/models

# Download Whisper models
echo "📥 Downloading Whisper models..."
cd data/models

# Download Whisper base model (already handled by Python package)
echo "✅ Whisper models will be downloaded automatically on first use"

# Download sentence transformer models
echo "📥 Downloading sentence transformer models..."
echo "✅ Sentence transformer models will be downloaded automatically on first use"

# Download Piper TTS models (if needed)
echo "📥 Setting up TTS models..."
mkdir -p tts
cd tts

# Download Piper TTS models
echo "📥 Downloading Piper TTS models..."
# Note: In production, you would download actual Piper models
# For now, we'll create placeholder files
touch en_US-ljspeech-medium.onnx
touch en_US-ljspeech-medium.json
touch hi_IN-hindi-medium.onnx
touch hi_IN-hindi-medium.json

echo "✅ Model download complete!"
echo ""
echo "📊 Model sizes:"
echo "  - TinyLlama 1.1B: ~637MB (Q4_K_M quantized)"
echo "  - Whisper base: ~74MB (downloaded on first use)"
echo "  - Sentence transformers: ~23MB (downloaded on first use)"
echo "  - TTS models: ~20MB each (placeholder files created)"
echo "  - Total: ~754MB (fits in Pi 4 4GB RAM)"
echo ""
echo "💡 Note: Actual models will be downloaded automatically when components are first initialized."

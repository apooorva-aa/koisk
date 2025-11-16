#!/bin/bash
# Setup Llama.cpp server with TinyLlama model

set -e

echo "=========================================="
echo "Setting up Llama.cpp Server with TinyLlama"
echo "=========================================="

# Create models directory
MODELS_DIR="data/models"
mkdir -p "$MODELS_DIR"

# Model configuration
MODEL_NAME="tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
MODEL_URL="https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/${MODEL_NAME}"
MODEL_PATH="$MODELS_DIR/$MODEL_NAME"

# Check if model already exists
if [ -f "$MODEL_PATH" ]; then
    echo "✅ Model already exists at $MODEL_PATH"
else
    echo "📥 Downloading TinyLlama model..."
    echo "Source: $MODEL_URL"
    echo "Destination: $MODEL_PATH"
    
    # Download using wget or curl
    if command -v curl &> /dev/null; then
        curl -L -o "$MODEL_PATH" "$MODEL_URL" --progress-bar
    else
        echo "❌ Error: Neither wget nor curl is available"
        exit 1
    fi
    
    echo "✅ Model downloaded successfully"
fi

# Check model file size
MODEL_SIZE=$(du -h "$MODEL_PATH" | cut -f1)
echo "📦 Model size: $MODEL_SIZE"

echo ""
echo "=========================================="
echo "Installing llama-cpp-python"
echo "=========================================="

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Install llama-cpp-python with server support
echo "Installing llama-cpp-python..."
pip install llama-cpp-python[server]

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "To start the Llama.cpp server, run:"
echo ""
echo "  python -m llama_cpp.server \\"
echo "    --model $MODEL_PATH \\"
echo "    --host 0.0.0.0 \\"
echo "    --port 8080 \\"
echo "    --n_ctx 2048 \\"
echo "    --n_threads 4"
echo ""
echo "Or use the provided start script:"
echo "  ./scripts/start-llama-server.sh"
echo ""

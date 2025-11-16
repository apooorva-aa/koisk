#!/bin/bash
# Start Llama.cpp server for TinyLlama inference

set -e

MODEL_PATH="data/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"

# Check if model exists
if [ ! -f "$MODEL_PATH" ]; then
    echo "❌ Model not found at $MODEL_PATH"
    echo "Run ./scripts/setup-llama-server.sh first to download the model"
    exit 1
fi

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

echo "=========================================="
echo "Starting Llama.cpp Server"
echo "=========================================="
echo "Model: $MODEL_PATH"
echo "Port: 8080"
echo "Context size: 2048 tokens"
echo "Threads: 4"
echo ""
echo "Server will be available at: http://localhost:8080"
echo "Press Ctrl+C to stop the server"
echo "=========================================="
echo ""

# Start the server
python -m llama_cpp.server \
    --model "$MODEL_PATH" \
    --host 0.0.0.0 \
    --port 8080 \
    --n_ctx 2048 \
    --n_threads 4 \
    --n_gpu_layers 0

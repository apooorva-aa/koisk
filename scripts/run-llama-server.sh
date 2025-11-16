#!/bin/bash
# Quick command to start the Llama.cpp server
# Run this in a separate terminal: ./scripts/run-llama-server.sh

cd "$(dirname "$0")/.."
source .venv/bin/activate

echo "Starting Llama.cpp server on http://localhost:8080"
echo "Press Ctrl+C to stop"

python -m llama_cpp.server \
    --model data/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf \
    --host 0.0.0.0 \
    --port 8080 \
    --n_ctx 2048 \
    --n_threads 4

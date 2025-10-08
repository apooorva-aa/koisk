#!/bin/bash

# Development Environment Setup Script
# This script sets up the development environment for Kiosk LLM

set -e

echo "🚀 Setting up Kiosk LLM Development Environment..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not available. Please install Docker Compose."
    exit 1
fi

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv (fast Python package manager)..."
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        # Windows
        powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    else
        # Linux/Mac
        curl -LsSf https://astral.sh/uv/install.sh | sh
    fi
fi

# Create necessary directories
echo "📁 Creating project directories..."
mkdir -p data/models
mkdir -p data/knowledge_base
mkdir -p data/logs
mkdir -p tests

# Set up Python environment
echo "🐍 Setting up Python environment..."
if command -v uv &> /dev/null; then
    uv pip install -e .
else
    echo "⚠️  uv not available, using pip..."
    pip install -e .
fi

# Build Docker images
echo "🐳 Building Docker images..."
docker-compose -f docker-compose.dev.yml build

echo "✅ Development environment setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Start development environment: docker-compose -f docker-compose.dev.yml up"
echo "2. Run tests: docker-compose -f docker-compose.dev.yml exec kiosk-llm pytest"
echo "3. Access API: http://localhost:8000"
echo "4. View logs: docker-compose -f docker-compose.dev.yml logs -f"
echo ""
echo "🔧 Development commands:"
echo "  Start: docker-compose -f docker-compose.dev.yml up -d"
echo "  Stop:  docker-compose -f docker-compose.dev.yml down"
echo "  Logs:  docker-compose -f docker-compose.dev.yml logs -f"
echo "  Shell: docker-compose -f docker-compose.dev.yml exec kiosk-llm bash"

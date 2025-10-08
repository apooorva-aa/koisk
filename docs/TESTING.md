# Koisk LLM API Testing Guide

This guide provides instructions for testing the Koisk LLM FastAPI endpoints.

## Quick Start

### 1. Start the API Server

```bash
# Build and start the Docker container
docker-compose -f docker-compose.prod.yml up --build

# Or run directly with Python (development)
cd src && python main.py
```

### 2. Test the API

#### Option A: Using the Test Script (Recommended)

```bash
# Install requests if not already installed
pip install requests

# Run the test script
python test_api.py
```

#### Option B: Using Postman

1. Import the collection: `Kiosk_LLM_API.postman_collection.json`
2. Set the base URL to `http://localhost:8000`
3. Run the collection

#### Option C: Using curl

```bash
# Test basic endpoints
curl http://localhost:8000/
curl http://localhost:8000/health

# Test interaction
curl -X POST "http://localhost:8000/interact" \
     -H "Content-Type: application/json" \
     -d '{"text": "Hello, how are you?"}'
```

## Available Endpoints

### Health & Status

- `GET /` - Basic API status
- `GET /health` - Component health check

### Interaction

- `POST /interact` - Main interaction endpoint
  - Body: `{"text": "your message"}` or `{"audio_file": "path/to/audio.wav"}`

### Documentation

- `GET /docs` - Swagger UI (interactive documentation)
- `GET /redoc` - ReDoc documentation
- `GET /openapi.json` - OpenAPI specification

## Expected Responses

### Health Check Response

```json
{
  "status": "healthy",
  "components": {
    "face_detection": true,
    "asr": true,
    "llm": true,
    "rag": true,
    "tts": true,
    "session_manager": true
  }
}
```

### Interaction Response

```json
{
  "user_input": "Hello, how are you?",
  "response": "Hello! I'm your AI assistant. How can I help you today?",
  "session_id": "uuid-string"
}
```

## Testing Scenarios

### 1. Basic Functionality

- ✅ API server starts successfully
- ✅ Health check shows all components as healthy
- ✅ Basic text interactions work
- ✅ Session management maintains conversation history

### 2. Mock Responses

The current implementation returns mock responses for:

- **Greeting**: "Hello! I'm your AI assistant. How can I help you today?"
- **Help requests**: "I can help you with information about services, products, or general questions. What would you like to know?"
- **Thank you**: "You're welcome! Is there anything else I can help you with?"
- **General questions**: "I understand your question. Let me provide you with some information about that topic."

### 3. Error Handling

- ✅ Empty requests return 400 error
- ✅ Invalid endpoints return 404 error
- ✅ Malformed JSON returns 422 error

## Current Limitations

### Not Yet Implemented (Mock Mode)

- **Real AI responses**: Currently returns predefined mock responses
- **Audio processing**: ASR and TTS are in mock mode
- **Face detection**: Returns mock face detection results
- **Knowledge base**: Limited sample data only

### Missing Dependencies

- `soundfile` package for audio processing
- Actual model files (Whisper, LLM, TTS models)
- Hardware drivers for camera/audio

## Troubleshooting

### Connection Refused

```bash
# Check if container is running
docker ps

# Check logs
docker-compose -f docker-compose.prod.yml logs

# Restart if needed
docker-compose -f docker-compose.prod.yml restart
```

### Port Already in Use

```bash
# Check what's using port 8000
lsof -i :8000

# Kill the process or change port in docker-compose.prod.yml
```

### Missing Dependencies

```bash
# Install missing Python packages
pip install requests soundfile

# Or rebuild the Docker container
docker-compose -f docker-compose.prod.yml up --build
```

## Performance Notes

- **Startup time**: ~10-15 seconds for full initialization
- **Response time**: ~100-500ms for mock responses
- **Memory usage**: ~200-300MB for basic operation
- **CPU usage**: Low for mock mode, higher when real models are loaded

## Next Steps

1. **Add real model files** to `data/models/` directory
2. **Install missing dependencies** (soundfile, etc.)
3. **Configure hardware access** for camera/microphone
4. **Implement actual AI inference** instead of mock responses
5. **Add knowledge base data** for RAG functionality

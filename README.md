# Kiosk LLM - Fine-Tuned AI Assistant for India

A privacy-preserving kiosk assistant running on Raspberry Pi 4, powered by local LLM with multilingual support (English/Hindi). Features face detection, speech input, RAG-powered responses, and text-to-speech output - all running locally for complete privacy and offline capability.

## Quick Start

### Prerequisites

- **Docker** and **Docker Compose**
- **WSL** if you are on Windows (do not use Docker Desktop please)
- **uv** (fast Python package manager)
- **Git**

### Development Setup

1. **Clone and setup**:

   ```bash
   git clone <your-repo-url> kiosk-llm
   cd kiosk-llm
   ./scripts/setup-dev.sh
   ```

2. **Start development environment**:

   ```bash
   docker-compose -f docker-compose.dev.yml up
   ```

3. **Test the API**:
   ```bash
   curl http://localhost:8000/health
   curl -X POST http://localhost:8000/interact -d "text=Hello"
   ```

### Raspberry Pi Deployment

1. **Setup on Pi**:

   ```bash
   curl -fsSL https://raw.githubusercontent.com/your-repo/kiosk-llm/main/scripts/setup-pi.sh | bash
   ```

2. **Start service**:
   ```bash
   sudo systemctl start kiosk-llm
   ```

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Face Detection │    │   Session Mgmt   │    │   Audio I/O     │
│   (OpenCV)      │────│   (Timeout)      │────│ (PyAudio/Piper) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│      ASR        │    │    LLM Engine    │    │      RAG        │
│   (Whisper)     │────│   (Llama.cpp)    │────│  (SQLite-vec)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Project Structure

```
kiosk-llm/
├── src/
│   ├── main.py                 # FastAPI application
│   ├── components/             # Core AI components
│   │   ├── face_detection.py  # OpenCV face detection
│   │   ├── asr.py            # Whisper speech-to-text
│   │   ├── llm_inference.py  # Llama.cpp LLM server
│   │   ├── rag.py            # SQLite vector search
│   │   ├── tts.py            # Piper text-to-speech
│   │   └── session_manager.py # User session handling
│   ├── database/              # Database models and management
│   │   └── models.py         # Consolidated database schema
│   └── utils/
│       ├── config.py         # Configuration management
│       └── logging.py        # Logging setup
├── config/
│   └── config.yaml           # Application configuration
├── scripts/
│   ├── setup-dev.sh         # Development setup
│   ├── setup-pi.sh          # Pi deployment
│   └── download-models.sh   # Model downloading
├── docker-compose.dev.yml   # Development environment
├── docker-compose.prod.yml  # Production environment
└── data/                    # Models, logs, knowledge base
    ├── models/              # AI model files
    ├── knowledge_base/      # RAG knowledge base
    └── logs/               # Application logs
```

##  Development Workflow

### Local Development

```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Access container shell
docker-compose -f docker-compose.dev.yml exec kiosk-llm bash

# Stop environment
docker-compose -f docker-compose.dev.yml down
```

### Cross-Platform Building

```bash
# Build for multiple architectures
docker buildx build --platform linux/amd64,linux/arm64 -t kiosk-llm:latest .

# Test ARM64 build locally
docker run --platform linux/arm64 kiosk-llm:latest
```

##  Database Schema

The system uses a consolidated SQLite database with the following tables:

### Core Tables

- **`documents`**: Knowledge base documents with embeddings
- **`sessions`**: User interaction sessions
- **`conversations`**: Chat history and responses
- **`face_events`**: Face detection events and analytics
- **`audio_events`**: Speech processing events
- **`performance_metrics`**: System performance tracking

### Database Features

- **Vector Search**: Cosine similarity for document retrieval
- **Session Management**: Complete user interaction tracking
- **Analytics**: Performance metrics and usage statistics
- **Multi-language**: Support for English and Hindi content
- **Categorization**: Document organization by category

##  AI Models & Sources

### Required Models

| Component      | Model                   | Size       | Source                                                                                 | Purpose           |
| -------------- | ----------------------- | ---------- | -------------------------------------------------------------------------------------- | ----------------- |
| **LLM**        | TinyLlama 1.1B (Q4_K_M) | ~637MB     | [Hugging Face](https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF)          | Text generation   |
| **ASR**        | Whisper Base            | ~74MB      | [OpenAI Whisper](https://github.com/openai/whisper)                                    | Speech-to-text    |
| **TTS**        | Piper Voices            | ~20MB each | [Piper TTS](https://github.com/rhasspy/piper)                                          | Text-to-speech    |
| **Embeddings** | all-MiniLM-L6-v2        | ~23MB      | [Sentence Transformers](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) | Vector embeddings |

### Model Download Sources

#### TinyLlama Models

- **Primary**: [Hugging Face - TheBloke](https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF)
- **Quantized**: Q4_K_M for optimal Pi 4 4GB performance
- **License**: Apache 2.0 License
- **Optimized for**: Raspberry Pi 4 4GB RAM model

#### Whisper Models

- **Repository**: [OpenAI Whisper](https://github.com/openai/whisper)
- **Models**: tiny, base, small, medium, large
- **Recommended**: base (74MB) for Pi 4
- **License**: MIT License

#### Piper TTS Models

- **Repository**: [Piper TTS](https://github.com/rhasspy/piper)
- **Voices**: English (en_US-ljspeech), Hindi (hi_IN-hindi)
- **Format**: ONNX models with JSON configs
- **License**: MIT License

#### Sentence Transformers

- **Repository**: [Sentence Transformers](https://github.com/UKPLab/sentence-transformers)
- **Model**: all-MiniLM-L6-v2 (multilingual)
- **License**: Apache 2.0

### Model Optimization for Pi 4 (4GB RAM)

- **Quantization**: 4-bit quantization for TinyLlama (Q4_K_M)
- **Memory Management**: Lazy loading and cleanup for 4GB constraint
- **Threading**: Optimized for 4-core ARM processor
- **Swap Configuration**: 1GB swap for model loading
- **Total Model Size**: ~754MB (TinyLlama + Whisper + Embeddings + TTS)
- **Available RAM**: ~3GB for system and application

##  Configuration

Edit `config/config.yaml` to customize:

- **Hardware**: Camera index, audio device
- **Models**: Whisper, LLM, TTS, embedding models
- **Performance**: Memory limits, thread counts
- **Session**: Timeout, conversation history
- **Database**: SQLite configuration and paths

##  API Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- `POST /interact` - Main interaction endpoint
  ```json
  {
    "text": "Hello, how can you help me?",
    "audio_file": "path/to/audio.wav" // optional
  }
  ```

##  Key Features

- ** Privacy-First**: All processing happens locally
- ** Multilingual**: English and Hindi support
- ** Offline Capable**: Works without internet
- ** Cost-Effective**: ~Rs. 10,500 per unit (4GB Pi 4 model)
- ** Voice + Text**: Flexible interaction methods
- ** RAG-Powered**: Context-aware responses
- ** Face Detection**: Automatic session management

##  Deployment

### Development

```bash
./scripts/setup-dev.sh
docker-compose -f docker-compose.dev.yml up
```

### Production (Raspberry Pi)

```bash
./scripts/setup-pi.sh
sudo systemctl start kiosk-llm
```

##  Performance (Pi 4 4GB)

- **Face Detection**: ~15-20 FPS
- **ASR**: ~2-3x real-time processing
- **LLM Inference**: ~3-5 tokens/second (TinyLlama 1.1B)
- **TTS**: ~3-5x real-time synthesis
- **Total Response Time**: 2-5 seconds
- **Memory Usage**: ~2.5GB peak (within 4GB limit)

##  Monitoring

```bash
# Check service status
sudo systemctl status kiosk-llm

# View logs
sudo journalctl -u kiosk-llm -f

# Check Docker containers
docker-compose -f docker-compose.prod.yml ps
```

##  Database Management

### Database Operations

```bash
# Access database directly
sqlite3 data/kiosk_llm.db

# View database schema
sqlite3 data/kiosk_llm.db ".schema"

# Check table contents
sqlite3 data/kiosk_llm.db "SELECT COUNT(*) FROM documents;"
sqlite3 data/kiosk_llm.db "SELECT COUNT(*) FROM sessions;"

# Export data
sqlite3 data/kiosk_llm.db ".dump" > backup.sql

# Import data
sqlite3 data/kiosk_llm.db < backup.sql
```

### Database Analytics

```sql
-- Session analytics
SELECT
    DATE(started_at) as date,
    COUNT(*) as sessions,
    AVG(duration_seconds) as avg_duration,
    SUM(interaction_count) as total_interactions
FROM sessions
WHERE ended_at IS NOT NULL
GROUP BY DATE(started_at);

-- Popular queries
SELECT
    user_input,
    COUNT(*) as frequency
FROM conversations
GROUP BY user_input
ORDER BY frequency DESC
LIMIT 10;

-- Performance metrics
SELECT
    component,
    metric_name,
    AVG(metric_value) as avg_value,
    MAX(metric_value) as max_value
FROM performance_metrics
GROUP BY component, metric_name;
```

##  Troubleshooting

### Common Issues

1. **Camera not detected**: Check camera permissions and device index
2. **Audio issues**: Verify audio device configuration
3. **Memory errors**: Adjust memory limits in config
4. **Model loading**: Ensure models are downloaded
5. **Database errors**: Check SQLite file permissions and disk space
6. **Vector search issues**: Verify embedding model is loaded
7. **Session timeouts**: Adjust session timeout in configuration

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
docker-compose -f docker-compose.dev.yml up
```

##  Next Steps

1. **Customize Knowledge Base**: Add domain-specific information
2. **Train Custom Models**: Fine-tune for specific use cases
3. **Add Languages**: Extend multilingual support
4. **Scale Deployment**: Deploy to multiple kiosks
5. **Monitor & Analytics**: Add usage tracking

##  Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

##  License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

##  Acknowledgments

- [Llama.cpp](https://github.com/ggerganov/llama.cpp) for efficient LLM inference
- [Whisper](https://github.com/openai/whisper) for speech recognition
- [Piper](https://github.com/rhasspy/piper) for text-to-speech
- [OpenCV](https://opencv.org/) for computer vision
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework

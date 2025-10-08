# Fine-Tuned LLM Koisk Implementation Guide - Complete Project Documentation

## Table of Contents

1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [3-4 Week Implementation Plan](#3-4-week-implementation-plan)
4. [Development Environment Setup](#development-environment-setup)
5. [Core Component Implementation](#core-component-implementation)
6. [Development Workflow](#development-workflow)
7. [Testing Strategy](#testing-strategy)
8. [Deployment Guide](#deployment-guide)
9. [Performance Optimization](#performance-optimization)

---

## Project Overview

### Project Brief

Develop a fine-tuned Large Language Model (LLM) system for AI kiosks in India, running on Raspberry Pi 4. The system supports multilingual interactions (speech + text) with hybrid online-offline capability to ensure uninterrupted service in varying connectivity conditions.

### Core Problems Addressed

1. **Connectivity Independence**: Remove cloud dependency for rural/urban India with poor connectivity
2. **Cost-Effective Scaling**: Affordable solution for retail, healthcare, banking, hospitality sectors
3. **Multilingual Support**: Handle Hindi, English, and regional languages
4. **Privacy Preservation**: Edge deployment keeps sensitive data local

### Key Features

- **Dual-Mode Operation**: Online multilingual LLM with offline single-language fallback
- **Face Detection**: Automatic session management based on user presence
- **Voice + Text Input**: Flexible interaction methods
- **Retrieval Augmented Generation (RAG)**: Context-aware responses using local knowledge base
- **Text-to-Speech Output**: Natural language responses
- **Cost-Effective Hardware**: Total cost ~Rs. 13,100 per unit

### System Flow

```
User Approaches → Face Detection → Session Start → Input (Voice/Text)
→ ASR (if voice) → LLM + RAG → Response Generation → TTS → Audio Output
→ Session Monitoring → Auto-Timeout/Manual Exit
```

---

## System Architecture

### Hardware Requirements

- **Raspberry Pi 4 (8GB RAM)** - SBC core
- **MicroSD Card (64GB+)** - Storage
- **USB Camera/Pi Camera** - Face detection
- **USB Microphone** - Voice input
- **Speaker** - Audio output
- **Touch Screen Display** - User interaction
- **Total Estimated Cost**: Rs. 10,500 (4GB Pi 4 model)

### Software Stack

- **OS**: Raspberry Pi OS (64-bit)
- **Runtime**: Python 3.11+ with uv package manager
- **ML Models**: TinyLlama 1.1B (quantized), Whisper, Sentence Transformers
- **Database**: SQLite with vector search
- **Speech**: Whisper.cpp (ASR), Piper (TTS)
- **Vision**: OpenCV for face detection
- **Deployment**: Docker + systemd services

### Core Components Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Face Detection │    │   Session Mgmt   │    │   Audio I/O     │
│   (OpenCV)      │────│   (Timeout)      │────│ (PyAudio/Piper) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│      ASR        │    │    LLM Engine    │    │      RAG        │
│   (Whisper)     │<──>│   (Llama.cpp)    │<──>│  (SQLite-vec)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

---

## 3-4 Week Implementation Plan

### Week 1: Foundation & Core Setup

**Objectives**: Environment setup, basic component development

**Team Distribution**:

- **Developer 1**: Environment setup, Docker configuration, basic project structure
- **Developer 2**: Face detection component, camera integration
- **Developer 3**: ASR component, audio input handling
- **Developer 4**: Basic LLM integration, model setup

**Deliverables**:

- [ ] Multi-platform development environment with Docker
- [ ] Basic face detection working on all platforms
- [ ] Audio recording and Whisper ASR functional
- [ ] LLM server responding to basic queries
- [ ] Project structure and CI/CD pipeline

### Week 2: Core Integration & RAG

**Objectives**: Integrate core components, implement RAG system

**Team Distribution**:

- **Developer 1**: Session management, main application loop
- **Developer 2**: RAG implementation, vector database setup
- **Developer 3**: TTS integration, audio output
- **Developer 4**: LLM prompt engineering, conversation context

**Deliverables**:

- [ ] End-to-end conversation flow working
- [ ] Knowledge base integration with RAG
- [ ] TTS generating and playing responses
- [ ] Session timeout and face detection loop
- [ ] Basic error handling and logging

### Week 3: Polish & Optimization

**Objectives**: Performance optimization, testing, deployment preparation

**Team Distribution**:

- **Developer 1**: Deployment scripts, Pi configuration
- **Developer 2**: Performance optimization, model quantization
- **Developer 3**: UI/UX improvements, error handling
- **Developer 4**: Testing, documentation, knowledge base creation

**Deliverables**:

- [ ] Optimized for Raspberry Pi performance
- [ ] Comprehensive testing on actual Pi hardware
- [ ] Deployment automation scripts
- [ ] Complete knowledge base with FAQ data
- [ ] User interface improvements

### Week 4: Testing & Deployment

**Objectives**: Final testing, deployment, demo preparation

**Team Focus**: All hands on deck for integration testing and demo prep

- [ ] End-to-end testing on multiple Pi devices
- [ ] Performance benchmarking and optimization
- [ ] Demo preparation with sample interactions
- [ ] Documentation completion
- [ ] Deployment to final hardware

---

## Development Environment Setup

### Multi-Platform Development Strategy

Since your team uses AMD64 Windows/Linux + M4 MacBook → deploy to ARM64 Pi, you'll use a **containerized development approach** with cross-platform building.

### Initial Setup (All Platforms)

```bash
# 1. Install Docker Desktop (Windows/Mac) or Docker Engine (Linux)
# Windows: Download from docker.com
# Mac: Download Docker Desktop for Apple Silicon
# Linux: Use package manager

# 2. Install uv (fast Python package manager)
# Windows (PowerShell):
irm https://astral.sh/uv/install.ps1 | iex

# Mac/Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. Verify installations
docker --version
uv --version
```

### Project Structure

```
koisk-llm/
├── pyproject.toml              # Python dependencies
├── docker-compose.dev.yml     # Development environment
├── docker-compose.prod.yml    # Production environment
├── Dockerfile.dev              # Development image
├── Dockerfile.prod             # Production image (ARM64)
├── .devcontainer/              # VS Code dev containers
├── src/
│   ├── main.py                 # Main application
│   ├── components/             # Core components
│   │   ├── face_detection.py
│   │   ├── asr.py
│   │   ├── llm_inference.py
│   │   ├── rag.py
│   │   ├── tts.py
│   │   └── session_manager.py
│   └── utils/
│       ├── config.py
│       ├── audio.py
│       └── logging.py
├── config/
│   └── config.yaml             # Application configuration
├── scripts/
│   ├── setup-dev.sh           # Development setup
│   ├── setup-pi.sh            # Pi deployment setup
│   └── download-models.sh     # Model downloading
├── tests/                      # Test files
├── data/
│   ├── models/                # AI models
│   ├── knowledge_base/        # FAQ and information
│   └── logs/                  # Application logs
└── deployment/
    ├── ansible/               # Pi deployment automation
    └── systemd/              # Service files
```

---

## Core Component Implementation

### Simplified Component Architecture

To meet the 3-4 week timeline, we'll implement a **simplified but functional** system focusing on core features:

### 1. Face Detection Component (OpenCV-based)

```python
# Simplified face detection with basic session management
# Uses OpenCV Haar cascades (faster than deep learning models)
# Basic presence detection with configurable timeout
```

**Key Features**:

- Simple Haar cascade face detection
- Session start/stop based on face presence
- Configurable timeout (default: 10 seconds)

### 2. ASR Component (Whisper-based)

```python
# Audio recording with silence detection
# Whisper model integration (base model for speed)
# Support for Hindi and English
```

**Simplified Approach**:

- Use Whisper "base" model (balance of speed/accuracy)
- Record audio in chunks with silence detection
- Primary languages: English, Hindi

### 3. LLM Component (Llama.cpp server)

```python
# Quantized TinyLlama 1.1B model
# Simple prompt engineering for koisk interactions
# Context management for conversations
```

**Implementation Strategy**:

- Use pre-quantized GGUF models (Q4_K_M for Pi 4 4GB optimization)
- Simple system prompts for koisk context
- Basic conversation memory (last 3-4 exchanges)

### 4. RAG Component (SQLite + Embeddings)

```python
# Local vector database using SQLite
# Simple similarity search
# FAQ and information retrieval
```

**Simplified Design**:

- Store embeddings as JSON in SQLite (avoid complex vector extensions)
- Use sentence-transformers for embeddings
- Cosine similarity for search

### 5. TTS Component (Piper)

```python
# Piper TTS for natural speech synthesis
# Support for English and Hindi voices
# Async audio playback
```

**Basic Features**:

- Piper TTS integration
- Queue-based audio playback
- Voice selection based on detected language

---

## Development Workflow

### Multi-Platform Development Process

### 1. Local Development (All Platforms)

```bash
# Clone repository
git clone <repo-url> koisk-llm
cd koisk-llm

# Setup development environment
./scripts/setup-dev.sh

# Start development containers
docker-compose -f docker-compose.dev.yml up -d

# Develop with hot reload
uv run python src/main.py
```

### 2. Cross-Platform Testing

```bash
# Build for multiple architectures
docker buildx build --platform linux/amd64,linux/arm64 -t koisk-llm:latest .

# Test ARM64 build locally (emulated)
docker run --platform linux/arm64 koisk-llm:latest
```

### 3. Pi Deployment Testing

```bash
# Deploy to test Pi (automated)
ansible-playbook deployment/ansible/deploy.yml -i deployment/ansible/pi-hosts

# Monitor deployment
ssh pi@<pi-ip> "sudo systemctl status koisk-llm"
```

### Daily Workflow

1. **Morning**: Pull latest changes, start dev containers
2. **Development**: Work on assigned component with live reload
3. **Testing**: Run component tests locally
4. **Integration**: Test with other components via Docker Compose
5. **Evening**: Push changes, automated CI/CD runs

### Feature Development Process

```
feature/component-name branch → local testing → cross-platform build →
Pi deployment test → code review → merge to main
```

---

## Testing Strategy

### 3-Tier Testing (Simplified for Timeline)

### Tier 1: Local Unit Testing (Fast)

```bash
# Component-specific tests
pytest tests/test_face_detection.py
pytest tests/test_asr.py
pytest tests/test_llm.py

# Mock hardware dependencies for speed
```

### Tier 2: Integration Testing (Docker)

```bash
# Full system test in containers
docker-compose -f docker-compose.test.yml up --abort-on-container-exit

# Cross-platform compatibility
docker buildx build --platform linux/arm64 --load -t koisk-test .
```

### Tier 3: Hardware Testing (Real Pi)

```bash
# Automated deployment to test Pi
ansible-playbook deployment/ansible/test-deploy.yml

# Performance and functionality validation
ssh pi@test-pi "cd /opt/koisk-llm && ./scripts/run-tests.sh"
```

### Continuous Integration

```yaml
# GitHub Actions workflow
name: Build and Test
on: [push, pull_request]
jobs:
  test:
    strategy:
      matrix:
        platform: [linux/amd64, linux/arm64]
    steps:
      - name: Build multi-platform
      - name: Run tests
      - name: Deploy to test Pi (on main branch)
```

---

## Deployment Guide

### Raspberry Pi Setup Automation

### 1. Initial Pi Configuration

```bash
# Run on fresh Pi OS installation
curl -fsSL https://raw.githubusercontent.com/your-repo/koisk-llm/main/scripts/setup-pi.sh | bash

# What this script does:
# - Install Docker and dependencies
# - Configure hardware (camera, audio)
# - Setup systemd services
# - Download and optimize models
# - Configure auto-start
```

### 2. Application Deployment

```yaml
# Ansible playbook for deployment
- name: Deploy Koisk LLM
  hosts: raspberry_pis
  tasks:
    - name: Pull latest Docker images
    - name: Update configuration
    - name: Restart services
    - name: Verify deployment
```

### 3. Production Configuration

```yaml
# config/production.yaml
hardware:
  camera_index: 0
  audio_device: "default"

performance:
  max_memory_mb: 6144 # Reserve 2GB for system
  llm_threads: 4 # Use all Pi cores

models:
  llm_model: "llama-2-7b-chat.Q4_K_M.gguf"
  whisper_model: "base"
  tts_voice: "en_US-ljspeech-medium"
```

---

## Performance Optimization

### Pi-Specific Optimizations

### 1. Model Optimization

- **LLM**: Use Q4_K_M quantization (4-bit) for TinyLlama 1.1B
- **Whisper**: Use "base" model (74MB) instead of "large"
- **Embeddings**: Use lightweight sentence-transformers model

### 2. Memory Management

```python
# Lazy loading of components
# Memory cleanup after sessions
# Model caching strategies
# Swap configuration for large models
```

### 3. CPU Optimization

```bash
# Set CPU governor to performance
echo 'performance' | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Optimize Python for Pi
export PYTHONOPTIMIZE=1
export OMP_NUM_THREADS=4
```

### Expected Performance (Pi 4 4GB)

- **Face Detection**: ~15-20 FPS
- **ASR**: ~2-3x real-time processing
- **LLM Inference**: ~3-5 tokens/second (TinyLlama 1.1B)
- **TTS**: ~3-5x real-time synthesis
- **Total Response Time**: 2-5 seconds
- **Memory Usage**: ~2.5GB peak

---

## Simplified Implementation Details

### Core Technologies (Finalized)

- **Python 3.11** + **uv** for fast dependency management
- **Docker** for multi-platform development and deployment
- **OpenCV** for face detection (Haar cascades)
- **Whisper** (base model) for ASR
- **Llama.cpp** server for LLM inference
- **Piper** for TTS
- **SQLite** for data storage and vector search
- **FastAPI** for internal service communication

### Model Selection (Optimized for Pi 4 4GB)

- **LLM**: TinyLlama 1.1B Chat (Q4_K_M quantized) ~637MB
- **ASR**: Whisper Base (~74MB)
- **TTS**: Piper voices (~20MB each)
- **Embeddings**: all-MiniLM-L6-v2 (~23MB)
- **Total**: ~754MB (fits comfortably in 4GB RAM)

### Development Tools

- **VS Code** with Dev Containers extension
- **Docker Desktop** (Windows/Mac) or Docker Engine (Linux)
- **GitHub Actions** for CI/CD
- **Ansible** for Pi deployment
- **pytest** for testing

### Key Simplifications for 3-4 Week Timeline

1. **Face Detection**: Use OpenCV Haar cascades instead of deep learning models
2. **Language Support**: Focus on English + Hindi initially
3. **UI**: Command-line interface with audio feedback (no complex GUI)
4. **Database**: Simple SQLite with JSON embeddings (no complex vector DB)
5. **Deployment**: Single Pi deployment initially (not fleet management)
6. **Monitoring**: Basic logging (not full observability stack)

### Success Metrics

- [ ] **Functionality**: End-to-end conversation works on Pi
- [ ] **Performance**: <5 second average response time
- [ ] **Reliability**: 95%+ successful interactions
- [ ] **Usability**: Non-technical users can interact naturally
- [ ] **Scalability**: Deployment process works for multiple Pis

This implementation plan balances functionality, performance, and development timeline constraints while providing a solid foundation that can be extended post-delivery.

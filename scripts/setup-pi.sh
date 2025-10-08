#!/bin/bash

# Raspberry Pi Setup Script
# This script sets up the Kiosk LLM system on a Raspberry Pi

set -e

echo "🍓 Setting up Kiosk LLM on Raspberry Pi..."

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required system packages
echo "🔧 Installing system dependencies..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    docker.io \
    docker-compose \
    git \
    curl \
    wget \
    build-essential \
    cmake \
    pkg-config \
    libjpeg-dev \
    libtiff5-dev \
    libpng-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libgtk-3-dev \
    libatlas-base-dev \
    gfortran \
    portaudio19-dev \
    espeak-ng \
    espeak-ng-data \
    libespeak-ng1 \
    alsa-utils \
    pulseaudio

# Add user to docker group
echo "🐳 Setting up Docker..."
sudo usermod -aG docker $USER
sudo systemctl enable docker
sudo systemctl start docker

# Install uv
echo "📦 Installing uv..."
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env

# Configure audio
echo "🔊 Configuring audio..."
sudo usermod -a -G audio $USER

# Enable camera
echo "📷 Enabling camera..."
sudo raspi-config nonint do_camera 0

# Configure GPU memory split (for better performance)
echo "⚡ Configuring GPU memory split..."
sudo raspi-config nonint do_memory_split 128

# Create systemd service
echo "🔧 Creating systemd service..."
sudo tee /etc/systemd/system/kiosk-llm.service > /dev/null <<EOF
[Unit]
Description=Kiosk LLM Service
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/kiosk-llm
ExecStart=/usr/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/bin/docker-compose -f docker-compose.prod.yml down
User=pi
Group=pi

[Install]
WantedBy=multi-user.target
EOF

# Enable service
sudo systemctl daemon-reload
sudo systemctl enable kiosk-llm.service

# Create application directory
echo "📁 Creating application directory..."
sudo mkdir -p /opt/kiosk-llm
sudo chown pi:pi /opt/kiosk-llm

# Clone repository (if not already present)
if [ ! -d "/opt/kiosk-llm/.git" ]; then
    echo "📥 Cloning repository..."
    cd /opt/kiosk-llm
    git clone <your-repo-url> .
fi

# Set up environment
echo "🌍 Setting up environment..."
cd /opt/kiosk-llm
./scripts/setup-dev.sh

# Download models
echo "🤖 Downloading AI models..."
./scripts/download-models.sh

# Configure for production
echo "⚙️  Configuring for production..."
cp config/config.yaml config/production.yaml
sed -i 's/camera_index: 0/camera_index: 0/' config/production.yaml
sed -i 's/audio_device: "default"/audio_device: "plughw:1,0"/' config/production.yaml

echo "✅ Raspberry Pi setup complete!"
echo ""
echo "🚀 To start the service:"
echo "  sudo systemctl start kiosk-llm"
echo ""
echo "📊 To check status:"
echo "  sudo systemctl status kiosk-llm"
echo ""
echo "📝 To view logs:"
echo "  sudo journalctl -u kiosk-llm -f"
echo ""
echo "🔄 To restart:"
echo "  sudo systemctl restart kiosk-llm"

#!/bin/bash
# VLA Task - Docker Setup Script
# Helper script for setting up Docker environment with X11 forwarding

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=============================================="
echo "VLA Task - Docker Setup"
echo "=============================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "[ERROR] Docker is not installed. Please install Docker first."
    exit 1
fi

echo "[OK] Docker is installed"

# Check if NVIDIA Docker is available
if ! docker run --rm --gpus all nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04 nvidia-smi &> /dev/null; then
    echo "[WARNING] NVIDIA GPU support may not be available"
    echo "          Make sure you have nvidia-docker2 installed and configured"
else
    echo "[OK] NVIDIA GPU support is available"
fi

# Check if Docker Compose is installed
if ! command -v docker compose &> /dev/null; then
    echo "[WARNING] Docker Compose v2 not found. Trying docker-compose..."
    if ! command -v docker-compose &> /dev/null; then
        echo "[ERROR] Neither docker compose nor docker-compose found"
        exit 1
    fi
    # Create alias for docker compose
    alias docker compose="docker-compose"
else
    echo "[OK] Docker Compose is installed"
fi

# Setup X11 forwarding
echo ""
echo "Setting up X11 forwarding..."

# Allow Docker to connect to X server
xhost +local:docker 2>/dev/null && echo "[OK] X11 access granted for Docker" || {
    echo "[WARNING] xhost command failed. You may need to manually run:"
    echo "          xhost +local:docker"
}

# Set DISPLAY environment variable
if [ -z "$DISPLAY" ]; then
    export DISPLAY=:0
    echo "[INFO] DISPLAY set to :0"
else
    echo "[OK] DISPLAY is set to $DISPLAY"
fi

# Create .Xauthority if it doesn't exist
if [ ! -f "$HOME/.Xauthority" ]; then
    touch "$HOME/.Xauthority"
    echo "[INFO] Created $HOME/.Xauthority"
fi

echo ""
echo "=============================================="
echo "Setup Complete!"
echo "=============================================="
echo ""
echo "Quick Start Guide:"
echo "------------------"
echo "1. Build the image:"
echo "   cd $PROJECT_ROOT"
echo "   make build"
echo ""
echo "2. Run with GUI:"
echo "   make run-gui"
echo ""
echo "3. Run a task:"
echo "   make run-task PROMPT=\"Pick up the red cube and place it in the blue bowl\""
echo ""
echo "4. Stop the container:"
echo "   make stop"
echo ""
echo "5. Clean up:"
echo "   make clean"
echo ""
echo "For more options, run: make help"
echo ""

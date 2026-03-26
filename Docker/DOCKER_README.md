# VLA Task - Docker Setup Guide

This guide explains how to run the VLA Pick and Place project using Docker.

## Prerequisites

- **NVIDIA GPU** with drivers installed (470.x or newer)
- **Docker** (20.10 or newer)
- **NVIDIA Container Toolkit** (nvidia-docker2)
- **X11 server** (for GUI support with PyBullet)

### Installing NVIDIA Container Toolkit

```bash
# Ubuntu/Debian
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/nvidia-container-toolkit.list | \
    sudo sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

Verify GPU access in Docker:
```bash
docker run --rm --gpus all nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04 nvidia-smi
```

## Quick Start

### 1. Setup X11 Forwarding (Linux)

```bash
xhost +local:docker
```

### 2. Build the Image

```bash
make build
```

### 3. Run the Container

**With GUI (recommended):**
```bash
make run-gui
```

**Headless (no GUI):**
```bash
make run-headless
```

### 4. Run a Task

```bash
make run-task PROMPT="Pick up the red cube and place it in the blue bowl"
```

Or attach to the running container:
```bash
make shell
python run.py --prompt "Pick up the red cube and place it in the blue bowl"
```

## Makefile Targets

| Target | Description |
|--------|-------------|
| `build` | Build the Docker image |
| `run` / `run-gui` | Run container with GUI support |
| `run-headless` | Run container without GUI |
| `run-task PROMPT="..."` | Run a specific task prompt |
| `stop` | Stop running container |
| `restart` | Restart the container |
| `clean` | Remove container and image |
| `prune` | Remove all unused Docker resources |
| `logs` | View container logs |
| `shell` / `bash` | Open shell in container |
| `ps` | Show container status |
| `test` | Run test command |
| `help` | Show all available targets |

## Using Docker Compose Directly

```bash
# Start with GUI
docker compose up -d vla-task

# Start headless
docker compose up -d vla-task-headless

# View logs
docker compose logs -f

# Stop
docker compose stop

# Remove
docker compose down
```

## Environment Variables

The following environment variables can be set in `.env` file:

```bash
# API Keys (optional)
OPENAI_API_KEY=your-key-here
GEMINI_API_KEY=your-key-here

# Display (for X11)
DISPLAY=:0
```

## Troubleshooting

### X11/GUI Issues

**Error: "Cannot open display"**
```bash
# Ensure X11 forwarding is enabled
xhost +local:docker
export DISPLAY=:0
```

**PyBullet GUI not showing**
- Make sure you're using `make run-gui` (not headless)
- Check that `$DISPLAY` is set correctly
- Verify X11 socket is mounted: `ls -la /tmp/.X11-unix/`

### GPU Issues

**Error: "could not select device driver"**
```bash
# Verify NVIDIA Container Toolkit is installed
docker run --rm --gpus all nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04 nvidia-smi
```

**CUDA out of memory**
- Reduce batch sizes or model complexity
- Ensure no other GPU processes are running

### Permission Issues

**Error: "Permission denied"**
```bash
# Fix X11 permissions
xhost +local:docker

# Fix .Xauthority permissions
chmod 644 ~/.Xauthority
```

## Architecture

The Docker image includes:
- **Python 3.12** with CUDA 12.1 support
- **PyTorch 2.5.1** with CUDA support
- **GroundingDINO** for object detection
- **PyBullet** for physics simulation
- **OpenCV** for image processing

## File Structure

```
vla_task/
├── Dockerfile              # Docker image definition
├── docker-compose.yml      # Docker Compose configuration
├── Makefile                # Make targets for Docker operations
├── .dockerignore           # Files excluded from Docker build
├── DOCKER_README.md        # This file
├── scripts/
│   └── docker-setup.sh     # Setup helper script
└── ... (project files)
```

## Customization

### Modifying the Dockerfile

To change the CUDA version, edit the `CUDA_VERSION` argument in Dockerfile:
```dockerfile
ARG CUDA_VERSION=12.1.1
```

### Adding Custom Models

Mount models directory at runtime:
```bash
docker run --rm -v ./models:/app/models:ro ...
```

### Production Deployment

For production, consider:
1. Using a smaller base image (e.g., `nvidia/cuda:12.1.1-runtime-ubuntu22.04`)
2. Multi-stage builds to reduce image size
3. Running in headless mode
4. Setting resource limits in docker-compose.yml

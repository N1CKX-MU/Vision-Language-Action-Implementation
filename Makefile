# VLA Task - Makefile for Docker Operations
# Provides convenient targets for building, running, and managing the Docker container

.PHONY: help build run run-gui run-headless stop clean logs shell bash test

# Variables
IMAGE_NAME := vla-task
CONTAINER_NAME := vla-task-container
DOCKERFILE := Docker/Dockerfile
COMPOSE_FILE := docker-compose.yml

# Default target
help:
	@echo "VLA Task - Docker Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  build          - Build the Docker image"
	@echo "  run            - Run container with GUI support (default)"
	@echo "  run-gui        - Run container with X11 forwarding for PyBullet GUI"
	@echo "  run-headless   - Run container without GUI (headless mode)"
	@echo "  stop           - Stop running container"
	@echo "  restart        - Restart the container"
	@echo "  clean          - Remove container and image"
	@echo "  prune          - Remove all unused Docker resources"
	@echo "  logs           - View container logs"
	@echo "  shell          - Open shell in running container"
	@echo "  bash           - Alias for shell"
	@echo "  test           - Run a test command in the container"
	@echo "  run-task       - Run with a specific prompt (use: make run-task PROMPT=\"your prompt\")"
	@echo "  ps             - Show container status"
	@echo "  pull           - Pull base NVIDIA CUDA image"
	@echo ""
	@echo "Example usage:"
	@echo "  make build"
	@echo "  make run-gui"
	@echo "  make run-task PROMPT=\"Pick up the red cube and place it in the blue bowl\""
	@echo ""

# Pull base images
pull:
	@echo "Pulling base NVIDIA CUDA image..."
	docker pull nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04

# Build the Docker image
build:
	@echo "Building Docker image..."
	docker build -t $(IMAGE_NAME) -f $(DOCKERFILE) .
	@echo "Build complete!"

# Run with GUI support (X11 forwarding)
run-gui:
	@echo "Starting container with GUI support..."
	@echo "Make sure to run 'xhost +local:docker' first if you get X11 errors"
	xhost +local:docker 2>/dev/null || true
	docker compose -f $(COMPOSE_FILE) up -d vla-task
	@echo "Container started. Attach with: make shell"

# Run headless (no GUI)
run-headless:
	@echo "Starting headless container..."
	docker compose -f $(COMPOSE_FILE) up -d vla-task-headless
	@echo "Container started. Attach with: make shell"

# Default run target (GUI)
run: run-gui

# Stop the container
stop:
	@echo "Stopping containers..."
	docker compose -f $(COMPOSE_FILE) stop
	@echo "Containers stopped."

# Restart the container
restart: stop run

# Clean up container and image
clean:
	@echo "Removing containers and networks..."
	docker compose -f $(COMPOSE_FILE) down --remove-orphans
	docker rm -f $(CONTAINER_NAME) 2>/dev/null || true
	@echo "Cleanup complete."

# Remove all unused Docker resources (careful!)
prune:
	@echo "Pruning unused Docker resources..."
	docker system prune -f
	@echo "Prune complete."

# View logs
logs:
	docker compose -f $(COMPOSE_FILE) logs -f

# Open shell in running container
shell:
	docker exec -it $(CONTAINER_NAME) bash || \
	docker compose -f $(COMPOSE_FILE) run --rm vla-task bash

bash: shell

# Run a specific task prompt
run-task:
ifndef PROMPT
	$(error PROMPT is not set. Usage: make run-task PROMPT="your prompt")
endif
	@echo "Running task: $(PROMPT)"
	xhost +local:docker 2>/dev/null || true
	docker run --rm --gpus all \
		-e DISPLAY=$(DISPLAY) \
		-v /tmp/.X11-unix:/tmp/.X11-unix:rw \
		-v $(HOME)/.Xauthority:/root/.Xauthority:ro \
		-v $(PWD)/.env:/app/.env:ro \
		--ipc=host \
		$(IMAGE_NAME) \
		python run.py --prompt "$(PROMPT)"

# Test the container
test:
	@echo "Running test in container..."
	docker run --rm --gpus all \
		-e DISPLAY=$(DISPLAY) \
		-v /tmp/.X11-unix:/tmp/.X11-unix:rw \
		$(IMAGE_NAME) \
		python -c "import torch; print('PyTorch version:', torch.__version__); print('CUDA available:', torch.cuda.is_available())"

# Show container status
ps:
	docker compose -f $(COMPOSE_FILE) ps

# Interactive run (foreground)
run-interactive:
	xhost +local:docker 2>/dev/null || true
	docker compose -f $(COMPOSE_FILE) run --rm vla-task

# Build without cache (fresh build)
build-no-cache:
	@echo "Building Docker image without cache..."
	docker build --no-cache -t $(IMAGE_NAME) -f $(DOCKERFILE) .
	@echo "Build complete!"

.PHONY: build clean docker docker-down docker-build perception projection controller sim run shell check-gpu help

# ───────── VARIABLES ─────────
IMAGE     := vla-task
CONTAINER := vla-task-container
SHELL     := /bin/bash

# ───────── BUILD ─────────

build:
	@echo "Building Docker image..."
	docker build -t $(IMAGE) -f Docker/Dockerfile .

clean:
	@echo "Cleaning up containers and pycache..."
	docker compose down --remove-orphans
	find . -type d -name "__pycache__" -exec rm -rf {} +

# ───────── DOCKER ─────────

docker:
	xhost +local:docker 2>/dev/null || true
	docker compose up -d
	@sleep 2
	docker exec -it $(CONTAINER) bash

docker-down:
	docker compose down

docker-build:
	docker build --no-cache -t $(IMAGE) -f Docker/Dockerfile .

# ───────── RUN MODULES (Testing) ─────────

perception:
	docker exec -it $(CONTAINER) python src/perception.py

projection:
	docker exec -it $(CONTAINER) python src/projection.py

controller:
	docker exec -it $(CONTAINER) python src/robot_controller.py

sim:
	docker exec -it $(CONTAINER) python starter_code/sim_env.py

# ───────── FULL TASK ─────────

# Usage: make run PROMPT="Pick up the red cube"
run:
	xhost +local:docker 2>/dev/null || true
	docker exec -it $(CONTAINER) python run.py --prompt "$(PROMPT)"

# ───────── DEBUG & UTILS ─────────

shell:
	docker exec -it $(CONTAINER) bash

check-gpu:
	docker exec -it $(CONTAINER) nvidia-smi

# ───────── HELP ─────────

help:
	@echo "VLA Project Commands:"
	@echo "  make build         - Build Docker image"
	@echo "  make docker        - Start container and enter shell"
	@echo "  make run PROMPT='' - Run the full VLA task"
	@echo "  make perception    - Test GroundingDINO/Ollama"
	@echo "  make sim           - Test PyBullet environment"
	@echo "  make check-gpu     - Verify NVIDIA passthrough"
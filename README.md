# Vision-Language-Action (VLA) Pick and Place Pipeline

A modular robotic pipeline that uses open-vocabulary object detection to perform physics-simulated pick-and-place tasks via natural language commands. The system utilizes GroundingDINO for text-prompted visual perception, PyBullet for robot simulation (Franka Panda arm), and precise coordinate projection to map 2D bounding boxes seamlessly into 3D world space for Inverse Kinematics (IK) grasp execution.

## Key Features
- **Natural Language Parsing**: Identify source and destination objects from an input prompt (e.g., `"Pick up the red cube and place it in the blue bowl"`).
- **Open-Vocabulary Perception**: Powered by GroundingDINO processing RGB images to detect target objects.
- **Physical Simulation**: Realistic environment built with PyBullet featuring a 7-DOF Franka Panda arm.
- **2D-to-3D Projection**: Utilizes depth camera parameters and intrinsics to project pixel coordinates natively into PyBullet 3D space.
- **Custom Object Support**: Includes customized URDFs (like an octagonal hollow bowl) and randomized, collision-aware object spawning.
- **Containerized for Reproducibility**: Includes a fully-managed Docker setup utilizing NVIDIA GPUs with robust X11 window forwarding for real-time GUI visualization.

---

## 🚀 Quick Start (Docker - Recommended)
The easiest way to run the pipeline while avoiding CUDA mismatch issues is via the provided Docker configuration.

### Prerequisites
1. [Docker Engine](https://docs.docker.com/engine/install/)
2. [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) (for GPU acceleration)

### Usage
```bash
# Allow local X11 connections so the Docker container can open PyBullet windows
xhost +local:docker

# Build the docker image
make build

# Run the PyBullet simulation dynamically via the Makefile GUI handler
make run-task PROMPT="Pick up the red cube and place it in the blue bowl"
```
*Note: For detailed Docker troubleshooting (headless servers vs GUI), refer to `Docker/DOCKER_README.md`.*

---

## 💻 Local Setup (UV Package Manager)
If you prefer running it locally on your machine, Python 3.12+ and `uv` are recommended.

### Installation
```bash
# Clone the repository
git clone https://github.com/N1CKX-MU/Vision-Language-Action-Implementation.git
cd Vision-Language-Action-Implementation

# Sync the environment using the incredibly fast UV package manager
uv sync

# Make sure you fetch GroundingDINO without build isolation so its CUDA C++ Extensions compile locally
uv pip install --no-build-isolation "groundingdino @ git+https://github.com/IDEA-Research/GroundingDINO.git@856dde20aee659246248e20734ef9ba5214f5e44"
```

*Note: You may need to download the GroundingDINO Swin-T weights (`groundingdino_swint_ogc.pth`) to `models/grounding_dino/` before running if it's not present.*

### Usage
Run the root script with your desired natural language prompt:
```bash
uv run python3 run.py --prompt "Pick up the yellow cube and place it in the blue bowl"
```

---

## 📁 System Architecture & Structure
This pipeline emphasizes modularity.

* `run.py` - The main entry point initializing and launching the CLI sequence.
* `src/pipeline.py` - Core logic mapping the perception outputs to 3D projection, then directly to robot motion controllers.
* `src/perception.py` - Loads GroundingDINO and parses text bounding boxes.
* `src/projection.py` - Takes a 2D pixel `(u, v)`, reads the corresponding depth pixel, and applies `depth * inv(K)` to get the real-world 3D location constraint `(x, y, z)`.
* `src/robot_control.py` - Solves Inverse Kinematics recursively using PyBullet iteratively and commands the Panda joints using explicit positional force constraints.
* `starter_code/sim_env.py` - Sets up the ground plane, table, camera setup/intrinsics, randomly collision-spawns test items, and sets up IK configuration constraints.
* `urdf/` / `models/` / `Docker/` - Holds 3D mesh blueprints, local model configs, and the dedicated container logic.

---

## 🛠️ Modifying the Scene
To change the items spawned in the PyBullet simulation, modify the `colours` dictionary in `starter_code/sim_env.py` inside the `_spawn_objects` function:
```python
colours = {
    "red_cube":    ([1, 0, 0, 1],    "cube"),
    "blue_bowl":   ([0, 0.4, 1, 1],  "bowl"), # Uses urdf/bowl.urdf
    "green_cube":  ([0, 0.8, 0, 1],  "cube"),
    "yellow_cube": ([1, 0.9, 0, 1],  "cube"),
}
```
*Note: Due to our robust procedural randomized area constraints, no matter how many items you add, they'll dynamically shift to avoid overlapping physics anomalies!*
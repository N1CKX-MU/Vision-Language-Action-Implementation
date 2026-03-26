ARG CUDA_VERSION=12.1.1
FROM nvidia/cuda:${CUDA_VERSION}-cudnn8-devel-ubuntu22.04 AS base

# 1. Official UV Binary (The best way)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# 2. System Deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.12 python3.12-dev python3-pip git wget curl \
    libgl1-mesa-glx libglib2.0-0 libsm6 libxrender1 libxext6 \
    libegl1 libxcb1 libxkbcommon0 libdbus-1-3 x11-apps xvfb \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3.12 /usr/bin/python

WORKDIR /app

# 3. Cache Heavy Dependencies (Torch/CUDA)
# Copying these first means we don't re-download 5GB of Torch every time you change code
COPY pyproject.toml uv.lock ./
RUN uv pip install --system --no-cache \
    torch==2.5.1+cu121 torchvision==0.20.1+cu121 \
    --index-url https://download.pytorch.org/whl/cu121

RUN uv pip install --system --no-cache \
    "numpy<2" "transformers<=4.39.3" timm supervision \
    opencv-python pycocotools pybullet setuptools wheel

# 4. Compile GroundingDINO (Fixed path)
ENV CUDA_HOME=/usr/local/cuda
ENV BUILD_WITH_CUDA=1
# We install from the specific commit to ensure stability
RUN uv pip install --system --no-build-isolation --no-cache \
    "git+https://github.com/IDEA-Research/GroundingDINO.git@856dde20aee659246248e20734ef9ba5214f5e44"

# 5. Final Code Copy
# Move these to the bottom so code changes only trigger a 2-second build
COPY src/ ./src/
COPY starter_code/ ./starter_code/
COPY models/ ./models/
COPY urdf/ ./urdf/
COPY run.py ./

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV CUDA_VISIBLE_DEVICES=0

CMD ["python", "run.py", "--help"]
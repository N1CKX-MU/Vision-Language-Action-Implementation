ARG CUDA_VERSION=12.1.1
FROM nvidia/cuda:${CUDA_VERSION}-cudnn8-devel-ubuntu22.04 AS base

# 1. Official UV Binary (The best way)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# 2. System Deps
# 2. System Deps (Updated for Python 3.12 on Ubuntu 22.04)
# 2. System Deps (Fixed for Python 3.12)
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa -y && \
    apt-get update && apt-get install -y --no-install-recommends \
    python3.12 \
    python3.12-dev \
    python3.12-venv \
    git wget curl \
    libgl1-mesa-glx libglib2.0-0 libsm6 libxrender1 libxext6 \
    libegl1 libxcb1 libxkbcommon0 libdbus-1-3 x11-apps xvfb \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3.12 /usr/bin/python
WORKDIR /app

# 3. Cache Heavy Dependencies (Torch/CUDA)
# Copying these first means we don't re-download 5GB of Torch every time you change code
COPY pyproject.toml uv.lock ./
ENV UV_HTTP_TIMEOUT=300
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

# --- OLLAMA & LLM INTEGRATION ---
# 6. Install System Dependencies (Separate from Ollama)
RUN apt-get update && apt-get install -y --no-install-recommends \
    zstd curl wget && \
    rm -rf /var/lib/apt/lists/*

# 7. Install Ollama Binary with a Timeout/Retry
# --connect-timeout 10 ensures we don't hang forever
RUN curl -fsSLv --connect-timeout 10 --retry 5 https://ollama.com/install.sh | sh -x
# 7. Pre-pull Qwen 2.5 0.5B (Baked into the image)
# We start the server, wait for it to initialize, pull the 400MB model, then kill it.
RUN ollama serve & sleep 5 && ollama pull qwen2.5:0.5b

# 8. Ensure 'requests' is available for the PerceptionModule
RUN uv pip install --system requests

# 9. Execution Wrapper
# We need a shell form to run Ollama as a background process before the Python script starts
ENTRYPOINT ["sh", "-c", "ollama serve & sleep 3 && python run.py \"$@\"", "--"]

CMD ["python", "run.py", "--help"]
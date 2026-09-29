FROM pytorch/pytorch:2.4.0-cuda12.1-cudnn9-runtime

WORKDIR /workspace

# System deps: git (pip installs from VCS / repo convenience), build tools for
# any packages without prebuilt wheels.
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first so this layer is cached across code-only changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Repo code. data/, reproduce_main_data/, results/, .hf_cache/ are intentionally
# left out (see .dockerignore) -- pull/mount those at container start, see
# docs/VASTAI.md.
COPY . .

ENV PYTHONUNBUFFERED=1 \
    HUGGINGFACE_CACHE_DIR=/workspace/.hf_cache \
    TOKENIZERS_PARALLELISM=false

CMD ["/bin/bash"]

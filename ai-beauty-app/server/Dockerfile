# GPU 推理服务镜像（CUDA 12.1）
# 构建: docker build -t beauty-server ./server
# 无 GPU 的 CPU 演示模式同样可用本镜像（需有 nvidia-container-toolkit 才能用 GPU）
FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_INDEX_URL=https://pypi.org/simple

RUN apt-get update && apt-get install -y --no-install-recommends \
      python3.11 python3.11-venv python3-pip libglib2.0-0 libgl1 libgomp1 \
    && ln -sf /usr/bin/python3.11 /usr/local/bin/python \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /srv

# 先装 torch（CUDA 12.1 对应 whl），再装其余依赖，利用层缓存
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cu121

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

VOLUME ["/models"]
EXPOSE 8000

# 默认启动 API；worker 用同一镜像覆盖 command 启动（见 deploy/docker-compose.yml）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

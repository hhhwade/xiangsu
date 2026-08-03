# -*- coding: utf-8 -*-
"""
全局配置。所有配置项均可通过环境变量或 .env 文件覆盖（见 deploy/.env.example）。
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ---- 鉴权 ----
    api_token: str = "change-me-dev-token"          # Bearer token，生产必须修改

    # ---- 队列 / 缓存 ----
    redis_url: str = "redis://localhost:6379/0"

    # ---- 对象存储（MinIO / S3 兼容） ----
    s3_endpoint: str = "http://localhost:9000"      # SDK 访问地址（容器内）
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin123"
    s3_bucket: str = "beauty"
    presign_expire_seconds: int = 7 * 24 * 3600     # 结果 URL 有效期

    # ---- 模型 ----
    model_dir: str = "/models"                      # 模型权重目录（docker 挂载）
    # SD 底模：支持本地路径 或 HuggingFace repo id（H100/8-12G 用 fp16）
    sd_base_model: str = "stable-diffusion-v1-5/stable-diffusion-v1-5"
    sd_inpaint_model: str = "stable-diffusion-v1-5/stable-diffusion-v1-5-inpainting"
    lora_qstyle_path: str = ""                       # 像素/卡哇伊 LoRA 权重文件（.safetensors），留空则用底模直出像素提示词
    ip_adapter_repo: str = "h94/IP-Adapter"          # 保身份用，留空不启用
    ip_adapter_weight_file: str = "models/ip-adapter_sd15.bin"
    animegan_onnx: str = "animegan_v2.onnx"          # 位于 model_dir 下
    u2net_parsing_onnx: str = "u2net_parsing.onnx"   # 人体/发区解析，位于 model_dir 下（可选）

    # ---- 运行模式 ----
    # auto: 有 CUDA 且有 SD 权重 → sd；有 animegan → lite；否则 mock（CPU 演示，文档注明降级）
    mode: str = "auto"                               # auto | sd | lite | mock

    # ---- 图片限制 ----
    max_image_mb: int = 16
    max_side: int = 2048

    # ---- 任务 ----
    celery_worker_concurrency: int = 1               # 8-12G 显存单并发，防 OOM
    task_soft_time_limit: int = 600                  # 软超时秒
    task_time_limit: int = 900                       # 硬超时秒
    task_max_retries: int = 1


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

# -*- coding: utf-8 -*-
"""
FastAPI 入口：
  uvicorn app.main:app --host 0.0.0.0 --port 8000
Worker（同镜像）：
  celery -A app.workers.tasks.celery_app worker --loglevel=info --concurrency=1
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings

app = FastAPI(
    title="AI 美颜修图 后端推理服务",
    version="1.0.0",
    description="Q 版像素风 + AI 自动美化。当前推理模式见 /api/health 的 mode 字段：sd（最佳）/ lite（轻量）/ mock（CPU 演示降级）。",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产建议收敛到你自己的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def root():
    return {
        "name": "ai-beauty-server",
        "docs": "/docs",
        "mode": settings.mode,
        "note": "所有 /api/** 需 Authorization: Bearer <token>",
    }

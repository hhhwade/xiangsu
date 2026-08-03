# -*- coding: utf-8 -*-
"""
REST API（v1） ：/api/qstyle /api/beautify /api/task/{id} /api/health
"""
import json
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.core.auth import require_token
from app.core.config import settings
from app.models.registry import registry
from app.workers.tasks import celery_app, task_beautify, task_qstyle

router = APIRouter(prefix="/api", dependencies=[Depends(require_token)])


class TaskCreate(BaseModel):
    task_id: str


@router.post("/qstyle", response_model=TaskCreate, summary="图片 → Q 版像素可爱风")
async def qstyle(
    file: UploadFile = File(...),
    params: str = Form(default="{}", description="JSON: pixel_size(int 4..64), strength(0.2..0.9), keep_bg(bool), mode(sd|lite|mock|auto), ip_scale(0..1)"),
):
    data = await file.read()
    try:
        p = json.loads(params)
    except json.JSONDecodeError:
        raise HTTPException(400, "params must be JSON string")
    t = task_qstyle.delay(data, p)
    return TaskCreate(task_id=t.id)


@router.post("/beautify", response_model=TaskCreate, summary="AI 自动美化 P 图（可勾选组合）")
async def beautify(
    file: UploadFile = File(...),
    params: str = Form(default="{}", description='JSON: {"ops": {"whiten":0.6,"smooth":0.7,...}} 值 0~1，缺省=关闭'),
):
    data = await file.read()
    try:
        p = json.loads(params)
    except json.JSONDecodeError:
        raise HTTPException(400, "params must be JSON string")
    p = {"ops": {k: float(v) if not isinstance(v, list) else v for k, v in p.get("ops", {}).items()}}
    t = task_beautify.delay(data, p)
    return TaskCreate(task_id=t.id)


@router.get("/task/{task_id}", summary="轮询任务进度与结果 URL")
async def task_status(task_id: str):
    res = celery_app.AsyncResult(task_id)
    state = res.state
    if state == "PENDING":
        return {"status": "queued", "progress": 0.0}
    if state == "RUNNING":
        info = res.info or {}
        return {"status": "running", "progress": info.get("progress", 0.0) if isinstance(info, dict) else 0.0}
    if state == "SUCCESS":
        r = res.result or {}
        return {
            "status": "done",
            "progress": 1.0,
            "mode": r.get("mode"),
            "original_url": r.get("original_url"),
            "result_url": r.get("result_url"),
            "notices": r.get("notices", []),
        }
    # FAILURE 等
    return {"status": "failed", "progress": 0.0, "error": str(res.info)[:500]}


class Health(BaseModel):
    status: str
    mode: str
    gpu: bool
    queue_len: int


@router.get("/health", response_model=Health, summary="健康检查（含当前推理模式）")
async def health():
    import torch
    try:
        insp = celery_app.control.inspect(timeout=0.5)
        reserved = insp.reserved() or {}
        queue_len = sum(len(v) for v in reserved.values())
    except Exception:
        queue_len = -1
    return Health(status="ok", mode=registry.mode, gpu=torch.cuda.is_available(), queue_len=queue_len)

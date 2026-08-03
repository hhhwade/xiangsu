# -*- coding: utf-8 -*-
"""
Celery 异步任务：
- task_qstyle / task_beautify
- 进度通过 task.update_state 上报 → GET /api/task/{id} 轮询
- 结果写成 PNG 上传 MinIO，返回预签 URL
"""
import numpy as np
from celery import Celery
from celery.utils.log import get_task_logger

from app.core.config import settings
from app.core.imageio import decode_upload, encode_png
from app.core.storage import presigned_url, upload_image_bytes
from app.models.registry import registry

celery_app = Celery("beauty_tasks", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(
    task_soft_time_limit=settings.task_soft_time_limit,
    task_time_limit=settings.task_time_limit,
    worker_prefetch_multiplier=1,     # 8-12G 显存：串行消费，防显存竞争
    task_acks_late=True,
    result_expires=settings.presign_expire_seconds,
)
logger = get_task_logger(__name__)


def _progress(task, ratio: float):
    task.update_state(state="RUNNING", meta={"progress": round(float(ratio), 2)})


def _finalize(task, original_bytes: bytes, out: np.ndarray, mode: str) -> dict:
    in_key = upload_image_bytes(original_bytes, "input", "png")
    res_bytes = encode_png(out)
    res_key = upload_image_bytes(res_bytes, "result", "png")
    return {
        "progress": 1.0,
        "mode": mode,
        "original_url": presigned_url(in_key),
        "result_url": presigned_url(res_key),
    }


@celery_app.task(bind=True, max_retries=settings.task_max_retries, name="tasks.qstyle")
def task_qstyle(self, image_bytes: bytes, params: dict):
    try:
        img = decode_upload(image_bytes)
        _progress(self, 0.1)
        mode_requested = params.get("mode", "auto")
        mode = registry.mode if mode_requested == "auto" else mode_requested

        pixel = int(params.get("pixel_size", 12))
        strength = float(params.get("strength", 0.55))
        keep_bg = bool(params.get("keep_bg", False))

        if mode == "sd":
            from app.pipeline.qstyle_sd import run_qstyle_sd
            out = run_qstyle_sd(img, pixel, strength, keep_bg,
                                ip_scale=float(params.get("ip_scale", 0.6)),
                                progress_cb=lambda r: _progress(self, 0.1 + 0.8 * r))
        elif mode == "lite":
            from app.pipeline.qstyle_lite import run_qstyle_lite
            out = run_qstyle_lite(img, pixel, strength, keep_bg)
        else:  # mock：CPU 演示，真实生成建议部署 GPU 后切换
            from app.pipeline.cv_utils import cartoon_mock
            out = cartoon_mock(img, pixel)
        return _finalize(self, image_bytes, out, mode)
    except Exception as exc:  # noqa
        logger.exception("qstyle task failed")
        raise self.retry(exc=exc, countdown=5)


@celery_app.task(bind=True, max_retries=settings.task_max_retries, name="tasks.beautify")
def task_beautify(self, image_bytes: bytes, params: dict):
    """
    ops 例：{"whiten":0.6,"smooth":0.7,"smooth_keep_texture":0.35,
             "hair_level":0.5,"hair_color":[88,56,40],"hair_gloss":0.3,
             "hair_fill":0.6,"slim_face":0.4,"big_eye":0.3,"lip":0.3,"brow":0.2,
             "slim_body":0.4,"slim_leg":0.5}
    值为 0/缺省 = 关闭该子功能。
    """
    try:
        ops: dict = params.get("ops", {})
        img = decode_upload(image_bytes)
        _progress(self, 0.1)
        out = img
        mode_used = "classic"
        notices = []

        # 1) 面部经典项（形变→肤质→彩妆）
        from app.pipeline.beautify_classic import apply_face_ops
        out = apply_face_ops(out, ops, progress_cb=lambda r: _progress(self, 0.1 + 0.4 * r))

        # 2) 人体项
        from app.pipeline.beautify_body import apply_body_ops
        out = apply_body_ops(out, ops, progress_cb=lambda r: _progress(self, 0.5 + 0.2 * r))

        # 3) 美发
        from app.pipeline.hair_pipeline import recolor_hair, fill_hair
        if ops.get("hair_level", 0.0) > 0 or ops.get("hair_gloss", 0.0) > 0:
            color = tuple(ops.get("hair_color", [88, 56, 40]))
            out = recolor_hair(out, ops.get("hair_level", 0.5),
                               target_rgb=(int(color[0]), int(color[1]), int(color[2])),
                               gloss=ops.get("hair_gloss", 0.3))
        _progress(self, 0.75)

        # 4) 补发（唯一必须 SD 模式的功能）
        if ops.get("hair_fill", 0.0) > 0:
            filled = fill_hair(out, ops["hair_fill"], progress_cb=lambda r: _progress(self, 0.75 + 0.2 * r))
            if filled is None:
                notices.append("hair_fill_skipped: 补发生成需要后端 MODE=sd 且已挂载 SD inpainting 权重")
            else:
                out = filled
                mode_used = "classic+sd_inpaint"

        result = _finalize(self, image_bytes, out, mode_used)
        if notices:
            result["notices"] = notices
        return result
    except Exception as exc:  # noqa
        logger.exception("beautify task failed")
        raise self.retry(exc=exc, countdown=5)

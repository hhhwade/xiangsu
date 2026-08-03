# -*- coding: utf-8 -*-
"""
图片读取 / 校验 / 缩放 / 编解码工具。
"""
import io
from typing import Tuple

import numpy as np
from PIL import Image
from fastapi import HTTPException

from app.core.config import settings


def decode_upload(data: bytes) -> np.ndarray:
    """字节流 → RGB ndarray (H,W,3)。做体积与格式校验。"""
    mb = len(data) / (1024 * 1024)
    if mb > settings.max_image_mb:
        raise HTTPException(status_code=413, detail=f"image too large: {mb:.1f}MB > {settings.max_image_mb}MB")
    try:
        img = Image.open(io.BytesIO(data)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="unsupported image format (need jpg/png/webp)")
    arr = np.array(img)
    return resize_if_needed(arr)


def resize_if_needed(arr: np.ndarray) -> np.ndarray:
    h, w = arr.shape[:2]
    m = settings.max_side
    scale = min(1.0, m / max(h, w))
    if scale >= 1.0:
        return arr
    img = Image.fromarray(arr).resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    return np.array(img)


def encode_png(arr: np.ndarray) -> bytes:
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, format="PNG")
    return buf.getvalue()


def pil_to_np(img: Image.Image) -> np.ndarray:
    return np.array(img.convert("RGB"))


def np_to_pil(arr: np.ndarray) -> Image.Image:
    return Image.fromarray(np.ascontiguousarray(arr))

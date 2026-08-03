# -*- coding: utf-8 -*-
"""
功能一（轻量路线）：AnimeGANv2 ONNX → 像素化，4GB 显存甚至 CPU 可用。
AnimeGAN 对「人像」效果最好；宠物/风景可用但风格化较淡。
"""
from typing import Optional

import cv2
import numpy as np

from app.models.registry import registry
from app.pipeline.cv_utils import pixelate, posterize, soft_blend


def _animegan_forward(img: np.ndarray) -> np.ndarray:
    """AnimeGANv2(face v2/onnx) 标准前处理：等比缩到 512 短边对齐 16 倍数。"""
    sess = registry.get_animegan()
    inp_name = sess.get_inputs()[0].name
    h, w = img.shape[:2]
    scale = 512.0 / min(h, w)
    nh, nw = int(h * scale), int(w * scale)
    nh, nw = (nh // 16) * 16, (nw // 16) * 16
    x = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_AREA).astype(np.float32)
    x = (x - 127.5) / 127.5
    x = x.transpose(2, 0, 1)[None, ...]
    y = sess.run(None, {inp_name: x})[0][0]
    y = ((y + 1.0) * 127.5).clip(0, 255).astype(np.uint8)
    y = y.transpose(1, 2, 0)
    return cv2.resize(y, (w, h), interpolation=cv2.INTER_LANCZOS4)


def run_qstyle_lite(
    img: np.ndarray,
    pixel_size: int = 10,
    strength: float = 0.7,
    keep_bg: bool = False,
    **_,
) -> np.ndarray:
    strength = float(min(max(strength, 0.0), 1.0))
    styled = _animegan_forward(img)
    # 强度=风格图与原图混合比；Q 化度再加清淡色阶（色块更「像素感」）
    mixed = (styled.astype(np.float32) * strength + img.astype(np.float32) * (1 - strength)).clip(0, 255).astype(np.uint8)
    mixed = posterize(mixed, levels=max(10, int(28 - 12 * strength)))
    mixed = pixelate(mixed, pixel_size)

    if keep_bg:
        from app.pipeline.qstyle_sd import _person_mask  # 复用主体掩码
        mask = _person_mask(img)
        mixed = soft_blend(img, mixed, mask)
    return mixed

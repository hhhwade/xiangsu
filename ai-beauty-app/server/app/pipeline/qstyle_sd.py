# -*- coding: utf-8 -*-
"""
功能一（SD 路线）：图片 → Q 版像素可爱风
- SD1.5 img2img，叠加像素/卡哇伊 LoRA（可选）
- 像素颗粒度 = 结果后处理像素块大小（pixel_size）
- Q 化强度 = img2img strength
- keep_bg=True：用 MediaPipe Selfie Segmentation 抠出主体，仅主体重绘，背景保留原图
"""
from typing import Optional

import numpy as np

from app.core.imageio import np_to_pil, pil_to_np
from app.models.registry import registry
from app.pipeline.cv_utils import pixelate, soft_blend

PROMPT_Q = (
    "cute chibi pixel art portrait, big sparkling eyes, round sweet face, "
    "kawaii proportions, vibrant pastel colors, 16-bit pixel blocks, clean edges, "
    "trending on artstation, masterpiece"
)
NEG_Q = "lowres, bad anatomy, extra fingers, blurry, jpeg artifacts, watermark, text, deformed"


def _person_mask(img: np.ndarray) -> np.ndarray:
    """MediaPipe selfie segmentation 主体掩码（CPU，几十毫秒）。"""
    import cv2
    import mediapipe as mp
    h, w = img.shape[:2]
    with mp.solutions.selfie_segmentation.SelfieSegmentation(model_selection=1) as seg:
        res = seg.process(img)
    mask = (res.segmentation_mask > 0.2).astype(np.uint8) * 255
    mask = cv2.medianBlur(mask, 7)
    mask = cv2.GaussianBlur(mask, (0, 0), 4)
    return mask


def run_qstyle_sd(
    img: np.ndarray,
    pixel_size: int = 12,
    strength: float = 0.55,
    keep_bg: bool = False,
    ip_scale: float = 0.6,
    seed: Optional[int] = None,
    progress_cb=None,
) -> np.ndarray:
    """
    img:   RGB uint8
    pixel_size: 像素颗粒度（块大小），4..64
    strength:   Q 化强度 0.2..0.9，越大越萌越不像原图
    keep_bg:    保留背景（主体重绘 + 背景原样）
    ip_scale:   IP-Adapter 权重（保真度），0..1；未加载 IP-Adapter 时忽略
    """
    import torch
    from PIL import Image

    pipe = registry.get_sd_img2img()
    strength = float(min(max(strength, 0.2), 0.9))
    pixel_size = int(min(max(pixel_size, 2), 64))

    gen = torch.Generator(device="cpu")
    if seed is not None:
        gen.manual_seed(int(seed))

    import mediapipe as mp  # noqa (主体掩码前计算，避免 SD 常驻显存时重复分配)
    src_pil = np_to_pil(img)
    w, h = src_pil.size
    # 对齐到 8 的倍数（diffusers 要求）
    W, H = (w // 8) * 8, (h // 8) * 8
    src_pil = src_pil.resize((W, H), Image.LANCZOS)

    kwargs = dict(
        prompt=PROMPT_Q,
        negative_prompt=NEG_Q,
        image=src_pil,
        strength=strength,
        num_inference_steps=28,
        guidance_scale=7.0,
        generator=gen,
    )
    # 挂了 IP-Adapter 才注入参考图（保身份）
    if getattr(pipe, "_ip_adapter_scales", None) or hasattr(pipe, "set_ip_adapter_scale"):
        try:
            pipe.set_ip_adapter_scale(float(ip_scale))
            kwargs["ip_adapter_image"] = src_pil
        except Exception:
            pass

    if progress_cb:
        progress_cb(0.35)
    out = pipe(**kwargs).images[0]
    if progress_cb:
        progress_cb(0.8)

    out_np = pil_to_np(out).astype(np.uint8)
    out_np = pixelate(out_np, pixel_size)  # 像素颗粒度后处理

    if keep_bg:
        mask = _person_mask(np.array(src_pil))
        # 主体区域用重绘结果，背景用原图（边缘羽化过渡）
        out_np = soft_blend(np.array(src_pil), out_np, mask)

    return out_np

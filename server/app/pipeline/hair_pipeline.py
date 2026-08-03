# -*- coding: utf-8 -*-
"""
功能二（头发）：美发（发色/光泽） + 补发（发际线 inpainting 生成）
- 发区分割：优先 U2Net human-parsing ONNX；模型缺失时退化为
  「脸廓上方 + 肤色掩码取反」启发式发区（仍可用，精度略低，日志注明）
- 美发：Lab 色彩迁移 + 高光增强
- 补发：SD inpaint 用发际线 mask 生成填充；非 sd 模式返回 None,
        由上层如实告知客户端该功能未启用
"""
from typing import Optional, Tuple

import cv2
import numpy as np

from app.core.imageio import np_to_pil, pil_to_np
from app.models.registry import registry
from app.pipeline.beautify_classic import FACE_OVAL, FaceData, detect_face
from app.pipeline.cv_utils import polygon_mask, skin_mask_ycbcr, soft_blend

# u2net human parsing 类别（常用定义）：2=hair, 1=hat
HAIR_CLASSES = (1, 2)


def _u2net_hair_mask(img: np.ndarray) -> Optional[np.ndarray]:
    try:
        sess = registry.get_u2net_parsing()
    except FileNotFoundError:
        return None
    inp = sess.get_inputs()[0]
    size = inp.shape[2] or 320
    h, w = img.shape[:2]
    x = cv2.resize(img, (size, size)).astype(np.float32) / 255.0
    mean = np.array([0.485, 0.456, 0.406], np.float32)
    std = np.array([0.229, 0.224, 0.225], np.float32)
    x = ((x - mean) / std).transpose(2, 0, 1)[None]
    logits = sess.run(None, {inp.name: x})[0][0]
    labels = logits.argmax(0).astype(np.uint8)
    labels = cv2.resize(labels, (w, h), interpolation=cv2.INTER_NEAREST)
    mask = np.isin(labels, HAIR_CLASSES).astype(np.uint8) * 255
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    return cv2.GaussianBlur(mask, (0, 0), 2)


def _heuristic_hair_mask(img: np.ndarray, face: FaceData) -> np.ndarray:
    """启发式发区：头廓（脸廓多边形向上外扩 1.6 倍）内 − 脸 − 皮肤。"""
    h, w = img.shape[:2]
    lm = face.lm
    cx, cy = lm[FACE_OVAL].mean(axis=0)
    head_pts = (lm[FACE_OVAL] - [cx, cy]) * [1.35, 1.55] + [cx, cy]
    head = polygon_mask((h, w), head_pts)
    face_m = cv2.dilate(face.oval_mask, np.ones((7, 7), np.uint8))
    skin = skin_mask_ycbcr(img)
    hair = cv2.bitwise_and(head, cv2.bitwise_not(face_m))
    hair = cv2.bitwise_and(hair, cv2.bitwise_not(skin))
    hair = cv2.morphologyEx(hair, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    return cv2.GaussianBlur(hair, (0, 0), 2)


def hair_mask(img: np.ndarray) -> Tuple[np.ndarray, str]:
    """返回 (mask, 来源:u2net/heuristic/none)。"""
    m = _u2net_hair_mask(img)
    if m is not None and m.sum() > 0:
        return m, "u2net"
    face = detect_face(img)
    if face is None:
        return np.zeros(img.shape[:2], np.uint8), "none"
    return _heuristic_hair_mask(img, face), "heuristic"


# ---------------- 美发 ----------------
def recolor_hair(
    img: np.ndarray,
    level: float = 0.5,
    target_rgb: Tuple[int, int, int] = (88, 56, 40),
    gloss: float = 0.3,
) -> np.ndarray:
    """
    发色调整：发区 mask 内向 target_rgb 做色彩迁移 + 高光增强。
    level 0~1，target_rgb 目标发色，gloss 光泽度 0~1。
    """
    if level <= 0 and gloss <= 0:
        return img
    mask, _src = hair_mask(img)
    if mask.sum() == 0:
        return img
    out = img.copy()
    if level > 0:
        # Lab 色迁移：发区像素 a/b 通道向目标色靠拢（保留 L 亮度→保留发丝纹理）
        lab_img = cv2.cvtColor(img, cv2.COLOR_RGB2LAB).astype(np.float32)
        lab_tgt = cv2.cvtColor(np.uint8([[target_rgb]]), cv2.COLOR_RGB2LAB)[0, 0].astype(np.float32)
        mask01 = (mask.astype(np.float32) / 255.0)[..., None] * level
        delta = (lab_tgt - lab_img.mean(axis=(0, 1)))
        lab_img[..., 1:] += mask01 * delta[1:]
        # 色相受控迁移：混合而非覆盖，防假面
        recolor = cv2.cvtColor(lab_img.clip(0, 255).astype(np.uint8), cv2.COLOR_LAB2RGB)
        out = soft_blend(img, recolor, (mask.astype(np.float32) * level).clip(0, 255).astype(np.uint8))
    if gloss > 0:
        blur = cv2.GaussianBlur(out, (0, 0), 3)
        high = cv2.addWeighted(out, 1.0 + 0.6 * gloss, blur, -0.6 * gloss, 0)  # USM 锐化=发丝高光
        out = soft_blend(out, high, mask)
    return out


# ---------------- 补发（需 sd 模式） ----------------
def fill_hair(img: np.ndarray, level: float = 0.6, progress_cb=None) -> Optional[np.ndarray]:
    """
    发际线/稀疏区域生成填充。
    mask 构造：发区上边界带 →女→ 向上膨出/内透 forehead 一定高度（按脸宽比例）。
    非 sd 模式返回 None → 上层如实反馈"该功能需要 GPU/SD 模式"。
    """
    if registry.mode != "sd":
        return None
    mask_hair, _ = hair_mask(img)
    face = detect_face(img)
    if face is None:
        return None
    lm = face.lm
    face_w = float(np.linalg.norm(lm[234] - lm[454]))
    pad = int(face_w * 0.10 * (0.5 + level))  # 生成带宽度随 level 放大

    # 发区 mask 的种子线 + 向上膨出 forehead 区域
    seed = cv2.dilate(mask_hair, np.ones((pad * 2 + 1, pad * 2 + 1), np.uint8))
    top_band = np.zeros_like(mask_hair)
    h, w = img.shape[:2]
    head_top_y = int(max(0, lm[FACE_OVAL][:, 1].min()))
    top_band[max(0, head_top_y - pad): int(head_top_y + pad * 2), :] = 255
    mask = cv2.bitwise_and(seed, cv2.bitwise_or(mask_hair, top_band))
    mask = cv2.GaussianBlur(mask, (0, 0), 3)

    pipe = registry.get_sd_inpaint()
    src = np_to_pil(img)
    W, H = (w // 8) * 8, (h // 8) * 8
    if (W, H) != (w, h):
        import PIL.Image as Image  # noqa
        src = src.resize((W, H))
        mask = cv2.resize(mask, (W, H), interpolation=cv2.INTER_NEAREST)
    out = pipe(
        prompt="dense healthy scalp hair with natural hairline, realistic strand details, "
               "seamlessly blending with surrounding hair, studio light",
        negative_prompt="bald spot, thinning hair, blur, wig, artificial edge, watermark",
        image=src,
        mask_image=np_to_pil(mask),
        num_inference_steps=30,
        guidance_scale=7.0,
        strength=0.95,
    ).images[0]
    if progress_cb:
        progress_cb(0.75)
    out_np = pil_to_np(out)
    if (W, H) != (w, h):
        import PIL.Image as Image  # noqa
        from app.core.imageio import np_to_pil as _p
        out_np = pil_to_np(_p(out_np).resize((w, h)))
    # 羽化 mask 混合，保证边界自然
    return soft_blend(img, out_np, mask)

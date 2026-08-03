# -*- coding: utf-8 -*-
"""
功能二（经典 CV，无需 GPU 即可运行）：
- MediaPipe Face Mesh(478点，含虹膜) 定位
- 美白 / 磨皮 / 瘦脸 / 大眼 / 唇色·眉形
设计原则：所有形变只搬动像素、不生成像素，结果可控真实，彻底避开鬼图风险。
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

from app.pipeline.cv_utils import (
    local_scale_warp, local_translation_warp, polygon_mask,
    skin_mask_ycbcr, soft_blend,
)

# MediaPipe face mesh 常用索引
FACE_OVAL = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365,
             379, 378, 400, 377, 152, 148, 176, 149, 150, 136, 172, 58, 132, 93,
             234, 127, 162, 21, 54, 103, 67, 109]
LEFT_EYE_C, RIGHT_EYE_C = 468, 473           # 虹膜中心（refine_landmarks=True）
LEFT_EYE_IN, LEFT_EYE_OUT = 133, 33
RIGHT_EYE_IN, RIGHT_EYE_OUT = 362, 263
JAW_LEFT, JAW_RIGHT, CHIN = 454, 234, 152    # 注意：镜像坐标下 234 是画面右侧，454 是画面左侧
UPPER_LIP, LOWER_LIP = 0, 17
LIPS_OUTER = [61, 185, 40, 39, 37, 0, 267, 269, 270, 409, 291, 375, 321, 405, 314, 17, 84, 181, 91, 146]
LEFT_BROW = [70, 63, 105, 66, 107, 55, 65, 52, 53, 46]
RIGHT_BROW = [300, 283, 295, 282, 334, 285, 336, 300, 293, 300]


@dataclass
class FaceData:
    lm: np.ndarray            # (478,2) 像素坐标
    oval_mask: np.ndarray     # 0/255 脸部轮廓掩码
    h: int
    w: int


def detect_face(img: np.ndarray) -> Optional[FaceData]:
    import mediapipe as mp
    h, w = img.shape[:2]
    with mp.solutions.face_mesh.FaceMesh(
        static_image_mode=True, max_num_faces=1,
        refine_landmarks=True, min_detection_confidence=0.5,
    ) as mesh:
        res = mesh.process(img)
    if not res.multi_face_landmarks:
        return None
    pts = res.multi_face_landmarks[0].landmark
    lm = np.array([[p.x * w, p.y * h] for p in pts], dtype=np.float32)
    oval = polygon_mask((h, w), lm[FACE_OVAL])
    oval = cv2.GaussianBlur(oval, (0, 0), 5)
    return FaceData(lm=lm, oval_mask=oval, h=h, w=w)


# ---------------- 美白 ----------------
def whiten_face(img: np.ndarray, face: FaceData, level: float) -> np.ndarray:
    """Lab 空间肤色区域提亮；level 0~1 → 亮度增益最多 +35%（clamp 防过曝）。"""
    if level <= 0:
        return img
    skin = skin_mask_ycbcr(img, face.oval_mask)
    lab = cv2.cvtColor(img, cv2.COLOR_RGB2LAB).astype(np.float32)
    gain = 1.0 + 0.35 * level
    lab[..., 0] = np.clip(lab[..., 0] * gain, 0, 255)
    out = cv2.cvtColor(lab.clip(0, 255).astype(np.uint8), cv2.COLOR_LAB2RGB)
    # a/b 通道轻微向"红润明亮"方向校正
    return soft_blend(img, out, skin)


# ---------------- 磨皮 ----------------
def smooth_face(img: np.ndarray, face: FaceData, level: float, keep_texture: float = 0.35) -> np.ndarray:
    """
    双边滤波去痘印/细纹；keep_texture 控制高频纹理回混比例（越高越不塑料脸）。
    """
    if level <= 0:
        return img
    smooth = cv2.bilateralFilter(img, d=13, sigmaColor=45, sigmaSpace=45)
    smooth = cv2.bilateralFilter(smooth, d=13, sigmaColor=45, sigmaSpace=45)
    # 高频细节层（原图-平滑图，含毛孔/纹理），部分加回
    high = (img.astype(np.int16) - smooth.astype(np.int16))
    restored = np.clip(smooth.astype(np.int16) + high * keep_texture, 0, 255).astype(np.uint8)
    alpha = (face.oval_mask.astype(np.float32) / 255.0)[..., None] * level
    return (restored * alpha + img * (1 - alpha)).clip(0, 255).astype(np.uint8)


# ---------------- 瘦脸 ----------------
def slim_face(img: np.ndarray, face: FaceData, level: float) -> np.ndarray:
    """两腮向内收 + 下颌微收。level 0~1。只移动像素，不做生成。"""
    if level <= 0:
        return img
    lm = face.lm
    cx = float((lm[JAW_LEFT][0] + lm[JAW_RIGHT][0]) / 2)
    fl = float(np.linalg.norm(lm[JAW_LEFT][0] - lm[JAW_RIGHT][0]))  # 脸宽
    out = img
    for idx, sgn in ((JAW_LEFT, -1), (JAW_RIGHT, 1)):   # sgn: 向面轴方向
        p = lm[idx]
        target = (p[0] + (cx - p[0]) * 0.18 * level, p[1] - fl * 0.01 * level)
        out = local_translation_warp(out, tuple(p), target, radius=fl * 0.22)
    # 下颌轻收（第176/400点为两腮下缘）
    for idx in (176, 400):
        p = lm[idx]
        target = (p[0] + (cx - p[0]) * 0.15 * level, p[1])
        out = local_translation_warp(out, tuple(p), target, radius=fl * 0.18)
    return out


# ---------------- 大眼 ----------------
def enlarge_eyes(img: np.ndarray, face: FaceData, level: float) -> np.ndarray:
    if level <= 0:
        return img
    lm = face.lm
    out = img
    for eye_c, c_in, c_out in ((LEFT_EYE_C, LEFT_EYE_IN, LEFT_EYE_OUT),
                               (RIGHT_EYE_C, RIGHT_EYE_IN, RIGHT_EYE_OUT)):
        r = float(np.linalg.norm(lm[c_in] - lm[c_out])) * 0.95  # 以眼宽为半径
        out = local_scale_warp(out, tuple(lm[eye_c]), r, strength=0.18 * level)
    return out


# ---------------- 唇色 / 眉形 ----------------
def lipstick(img: np.ndarray, face: FaceData, level: float, hue_shift: float = -6.0) -> np.ndarray:
    """唇部区域内提升饱和度并稍微偏红润；hue_shift 受控，不做假口红面具。"""
    if level <= 0:
        return img
    mask = polygon_mask((face.h, face.w), face.lm[LIPS_OUTER])
    mask = cv2.GaussianBlur(mask, (0, 0), 2)
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV).astype(np.float32)
    hsv[..., 1] = np.clip(hsv[..., 1] * (1 + 0.45 * level), 0, 255)
    hsv[..., 2] = np.clip(hsv[..., 2] * (1 + 0.06 * level), 0, 255)
    hsv[..., 0] = (hsv[..., 0] + hue_shift * level) % 180
    out = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)
    return soft_blend(img, out, mask)


def eyebrow_shaping(img: np.ndarray, face: FaceData, level: float) -> np.ndarray:
    """眉形微调：眉峰轻抬、尾部下拉，营造"更精神"的眉。"""
    if level <= 0:
        return img
    out = img
    for brow in (LEFT_BROW, RIGHT_BROW):
        peak = face.lm[brow[len(brow) // 2]]
        fl = float(np.linalg.norm(face.lm[JAW_LEFT] - face.lm[JAW_RIGHT]))
        target = (peak[0], peak[1] - fl * 0.015 * level)
        out = local_translation_warp(out, tuple(peak), target, radius=fl * 0.08)
    return out


# ---------------- 组合流水线 ----------------
def apply_face_ops(img: np.ndarray, ops: Dict[str, float], progress_cb=None) -> np.ndarray:
    """
    ops 为"强度"字典（0~1），键名即子功能；未给出的键视为关闭。
    操作顺序：形变（瘦脸/大眼）→ 肤质（磨皮/美白）→ 彩妆（唇/眉）
    ——先形变后滤波，防止把磨皮纹理再搬动导致不自然。
    """
    face = detect_face(img)
    out = img
    if face is None:
        return out  # 非人像：面部类操作安全跳过

    out = slim_face(out, face, ops.get("slim_face", 0.0))
    if progress_cb: progress_cb(0.45)
    out = enlarge_eyes(out, face, ops.get("big_eye", 0.0))
    out = smooth_face(out, face, ops.get("smooth", 0.0))
    if progress_cb: progress_cb(0.65)
    out = whiten_face(out, face, ops.get("whiten", 0.0))
    out = lipstick(out, face, ops.get("lip", 0.0))
    out = eyebrow_shaping(out, face, ops.get("brow", 0.0))
    return out

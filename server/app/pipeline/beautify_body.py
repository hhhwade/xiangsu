# -*- coding: utf-8 -*-
"""
功能二（人体部分）：瘦身 / 瘦腿
- MediaPipe Pose（33 关键点，Apache-2.0）定位肩、髋、膝、踝
- 瘦身：躯干左右轮廓带形变内收
- 瘦腿：髋关节以下按垂直 factor 拉长 + 腿外侧内收
人体掩码用 Selfie Segmentation 约束 warp 作用范围，避免背景大面积跟着走。
"""
from typing import Optional

import cv2
import numpy as np

from app.pipeline.cv_utils import local_translation_warp, vertical_stretch


def _person_mask(img: np.ndarray) -> np.ndarray:
    import mediapipe as mp
    with mp.solutions.selfie_segmentation.SelfieSegmentation(model_selection=1) as seg:
        res = seg.process(img)
    m = (res.segmentation_mask > 0.25).astype(np.uint8) * 255
    return cv2.GaussianBlur(cv2.medianBlur(m, 9), (0, 0), 4)


def _pose_lm(img: np.ndarray) -> Optional[np.ndarray]:
    import mediapipe as mp
    h, w = img.shape[:2]
    with mp.solutions.pose.Pose(static_image_mode=True, model_complexity=1,
                                min_detection_confidence=0.5) as pose:
        res = pose.process(img)
    if not res.pose_landmarks:
        return None
    lm = np.array([[p.x * w, p.y * h, p.visibility] for p in res.pose_landmarks.landmark],
                  dtype=np.float32)
    return lm


# MediaPipe Pose 索引：11左肩 12右肩 23左髋 24右髋 25左膝 26右膝 27左踝 28右踝
def slim_body(img: np.ndarray, level: float) -> np.ndarray:
    """躯干/手臂区域横向内收。level 0~1。不生成新像素，warp 无背景横线时用羽化掩码压边。"""
    if level <= 0:
        return img
    lm = _pose_lm(img)
    if lm is None:
        return img
    h, w = img.shape[:2]
    ls, rs = lm[11], lm[12]
    lh, rh = lm[23], lm[24]
    if min(ls[2], rs[2], lh[2], rh[2]) < 0.4:
        return img
    mid_x = float((ls[0] + rs[0]) / 2)
    torso_w = float(abs(rs[0] - ls[0]))
    out = img
    # 左/右躯干轮廓（肩、髋、肋侧中点）各做一次内收平移 warp
    for side_pts in ((ls, lh), (rs, rh)):
        s, hp = side_pts
        edge = np.array([(s[0] + hp[0]) / 2, (s[1] + hp[1]) / 2], np.float32)
        target = (edge[0] + (mid_x - edge[0]) * 0.22 * level, edge[1])
        out = local_translation_warp(out, tuple(edge), target, radius=torso_w * 0.55)
    return out


def slim_leg(img: np.ndarray, level: float) -> np.ndarray:
    """腿部拉长塑形：髋线以下拉高（最多 +12%），腿外侧轻收。"""
    if level <= 0:
        return img
    lm = _pose_lm(img)
    if lm is None:
        return img
    lh, rh = lm[23], lm[24]
    la, ra = lm[27], lm[28]
    if min(lh[2], rh[2], la[2], ra[2]) < 0.3:
        return img
    hip_y = int((lh[1] + rh[1]) / 2)
    out = vertical_stretch(img, hip_y, factor=1.0 + 0.12 * level)

    # 外侧轮廓向内收（左右腿外缘中点）
    h, w = img.shape[:2]
    hip_w = abs(rh[0] - lh[0])
    mid_left = np.array([min(lh[0], la[0]) - hip_w * 0.18, (lh[1] + la[1]) / 2], np.float32)
    mid_right = np.array([max(rh[0], ra[0]) + hip_w * 0.18, (rh[1] + ra[1]) / 2], np.float32)
    center_x = (lh[0] + rh[0]) / 2
    for p in (mid_left, mid_right):
        target = (p[0] + (center_x - p[0]) * 0.14 * level, p[1])
        out = local_translation_warp(out, tuple(p), target, radius=hip_w * 0.8)
    return out


def apply_body_ops(img: np.ndarray, ops: dict, progress_cb=None) -> np.ndarray:
    out = slim_body(img, ops.get("slim_body", 0.0))
    if progress_cb: progress_cb(0.5)
    out = slim_leg(out, ops.get("slim_leg", 0.0))
    return out

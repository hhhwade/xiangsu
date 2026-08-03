# -*- coding: utf-8 -*-
"""
通用 CV 工具：局部形变 warp、掩码、像素化、mock 卡通化。
所有函数输入/输出均为 RGB uint8 ndarray。
"""
from typing import Optional, Sequence, Tuple

import cv2
import numpy as np

Pt = Tuple[float, float]


# ---------- 形变 ----------
def local_translation_warp(img: np.ndarray, start: Pt, end: Pt, radius: float) -> np.ndarray:
    """
    以 start 为圆心、radius 为半径的局部平移形变（向 end 方向拉动）。
    场强按 (1 - (r/R)^2)^2 衰减，中心最大，边缘平滑趋零——经典瘦脸/大眼 warp 公式。
    """
    h, w = img.shape[:2]
    sx, sy = start
    r_outer = max(radius, 8.0)
    x0 = int(max(0, sx - r_outer)); x1 = int(min(w, sx + r_outer))
    y0 = int(max(0, sy - r_outer)); y1 = int(min(h, sy + r_outer))
    if x1 <= x0 or y1 <= y0:
        return img
    dx, dy = end[0] - sx, end[1] - sy
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    r2 = (xx - sx) ** 2 + (yy - sy) ** 2
    inside = r2 < (r_outer * r_outer)
    s = np.zeros_like(r2)
    s[inside] = ((1 - r2[inside] / (r_outer * r_outer)) ** 2)
    map_x = xx + dx * s
    map_y = yy + dy * s
    fig = img.copy()
    roi = cv2.remap(
        fig[y0:y1, x0:x1], map_x.astype(np.float32), map_y.astype(np.float32),
        interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101,
    )
    fig[y0:y1, x0:x1] = roi
    return fig


def local_scale_warp(img: np.ndarray, center: Pt, radius: float, strength: float) -> np.ndarray:
    """
    以 center 为圆心的缩/放形变：strength>0 放大（大眼），<0 缩小（瘦脸）。
    使用 |strength| <= 0.35，场分布同 translation warp。
    """
    if abs(strength) < 1e-6:
        return img
    h, w = img.shape[:2]
    cx, cy = center
    R = max(radius, 8.0)
    x0 = int(max(0, cx - R)); x1 = int(min(w, cx + R))
    y0 = int(max(0, cy - R)); y1 = int(min(h, cy + R))
    if x1 <= x0 or y1 <= y0:
        return img
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    r2 = (xx - cx) ** 2 + (yy - cy) ** 2
    inside = r2 < (R * R)
    s = np.zeros_like(r2)
    s[inside] = ((1 - r2[inside] / (R * R)) ** 2)
    k = s * strength
    map_x = xx * (1 - k) + cx * k
    map_y = yy * (1 - k) + cy * k
    fig = img.copy()
    roi = cv2.remap(
        fig[y0:y1, x0:x1], map_x.astype(np.float32), map_y.astype(np.float32),
        interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101,
    )
    fig[y0:y1, x0:x1] = roi
    return fig


def vertical_stretch(img: np.ndarray, start_y: int, factor: float) -> np.ndarray:
    """腿部拉长：start_y 以下整体向下拉长 factor 倍（>1 生效）。"""
    if factor <= 1.0 or start_y <= 0:
        return img
    h, w = img.shape[:2]
    start_y = int(min(start_y, h - 2))
    map_x, map_y = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    below = map_y > start_y
    map_y2 = map_y.copy()
    map_y2[below] = start_y + (map_y[below] - start_y) / factor
    return cv2.remap(img, map_x, map_y2, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)


# ---------- 掩码 ----------
def skin_mask_ycbcr(img: np.ndarray, roi_mask: Optional[np.ndarray] = None) -> np.ndarray:
    """YCbCr 肤色分割 → 0/255 掩码；可再与 roi_mask 相交（限定脸部等）。牛顿色校documented range。"""
    ycrcb = cv2.cvtColor(img, cv2.COLOR_RGB2YCrCb)
    lower = np.array([0, 133, 77], dtype=np.uint8)
    upper = np.array([255, 180, 135], dtype=np.uint8)
    mask = cv2.inRange(ycrcb, lower, upper)
    if roi_mask is not None:
        mask = cv2.bitwise_and(mask, roi_mask.astype(np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    mask = cv2.GaussianBlur(mask, (0, 0), sigmaX=2)
    return mask


def polygon_mask(shape: Sequence[int], points: np.ndarray) -> np.ndarray:
    m = np.zeros(shape[:2], np.uint8)
    cv2.fillConvexPoly(m, points.astype(np.int32), 255)
    return m


def soft_blend(base: np.ndarray, top: np.ndarray, mask: np.ndarray) -> np.ndarray:
    m = (mask.astype(np.float32) / 255.0)[..., None]
    return (top.astype(np.float32) * m + base.astype(np.float32) * (1 - m)).clip(0, 255).astype(np.uint8)


# ---------- 像素 & 卡通 ----------
def pixelate(img: np.ndarray, block: int) -> np.ndarray:
    """颗粒度 block（建议 4~48）。area 降采样 + nearest 还原。"""
    if block <= 1:
        return img
    h, w = img.shape[:2]
    small = cv2.resize(img, (max(1, w // block), max(1, h // block)), interpolation=cv2.INTER_AREA)
    return cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)


def posterize(img: np.ndarray, levels: int = 24) -> np.ndarray:
    levels = max(2, int(levels))
    div = 255.0 / (levels - 1)
    q = (img.astype(np.float32) / div).round() * div
    return np.clip(q, 0, 255).astype(np.uint8)


def cartoon_mock(img: np.ndarray, pixel: int = 8) -> np.ndarray:
    """
    mock 模式降级演示（无 GPU 时用，打通链路）：双边滤波平滑 + 边缘描线 + 降色阶 + 像素块。
    生产请使用 sd / lite 路线（结果带 mode 标记，文档如实标注降级）。
    """
    smooth = cv2.bilateralFilter(img, d=9, sigmaColor=60, sigmaSpace=60)
    smooth = cv2.bilateralFilter(smooth, d=9, sigmaColor=60, sigmaSpace=60)
    smooth = posterize(smooth, levels=12)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    edges = cv2.adaptiveThreshold(cv2.medianBlur(gray, 5), 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                  cv2.THRESH_BINARY, 9, 6)
    cartoon = cv2.bitwise_and(smooth, smooth, mask=edges)
    cartoon = cv2.detailEnhance(cartoon, sigma_s=10, sigma_r=0.15)
    return pixelate(cartoon, pixel)

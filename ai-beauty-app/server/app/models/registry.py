# -*- coding: utf-8 -*-
"""
模型注册表：
- 运行模式判定（sd / lite / mock）
- SD img2img、SD inpainting、IP-Adapter、LoRA 按需加载
- 8–12GB 显存策略：fp16 + enable_model_cpu_offload + LRU（GPU 上最多常驻 1 个 SD pipeline）
- ONNX 模型（AnimeGAN / U2Net-parsing）惰性加载
"""
import os
import threading
from collections import OrderedDict
from typing import Optional

from app.core.config import settings

_lock = threading.RLock()


def _has_cuda() -> bool:
    try:
        import torch
        return torch.cuda.is_available()
    except Exception:
        return False


def _file_in_model_dir(name: str) -> Optional[str]:
    p = os.path.join(settings.model_dir, name)
    return p if os.path.exists(p) else None


def resolve_mode(requested: str = "auto") -> str:
    """auto 模式下自动选择当前机器能跑的最优路线。"""
    if requested != "auto":
        return requested
    if _has_cuda():
        return "sd"
    if _file_in_model_dir(settings.animegan_onnx):
        return "lite"
    return "mock"


class ModelRegistry:
    """惰性加载 + LRU 显存管理。所有 getter 线程安全。"""

    _MAX_GPU_SD_PIPES = 1   # 8-12G 显存：任一时刻只常驻 1 个 SD pipeline

    def __init__(self):
        self._sd_pipes: OrderedDict[str, object] = OrderedDict()   # key -> diffusers pipeline
        self._onnx: OrderedDict[str, object] = OrderedDict()       # key -> onnxruntime session
        self.mode = resolve_mode(settings.mode)

    # ---------------- SD ----------------
    def _device(self):
        import torch
        return ("cuda", torch.float16) if _has_cuda() else ("cpu", torch.float32)

    def _maybe_offload_oldest(self):
        from diffusers import StableDiffusionImg2ImgPipeline, StableDiffusionInpaintPipeline  # noqa: F401
        while len(self._sd_pipes) > self._MAX_GPU_SD_PIPES:
            _, pipe = self._sd_pipes.popitem(last=False)
            del pipe
            try:
                import torch
                torch.cuda.empty_cache()
            except Exception:
                pass

    def _load_sd(self, key: str, model_id: str, cls):
        from diffusers.utils import load_utils  # noqa
        device, dtype = self._device()
        import torch
        pipe = cls.from_pretrained(model_id, torch_dtype=dtype, safety_checker=None)
        if device == "cuda":
            # cpu_offload 可以在 8-12G 显存下运作，同时减少常驻占用
            pipe.enable_model_cpu_offload()
            pipe.enable_vae_tiling()
        else:
            pipe = pipe.to(device)
        pipe.set_progress_bar_config(disable=True)
        self._sd_pipes[key] = pipe
        self._maybe_offload_oldest()
        return pipe

    def get_sd_img2img(self):
        with _lock:
            key = "sd15_img2img"
            pipe = self._sd_pipes.get(key)
            if pipe is not None:
                self._sd_pipes.move_to_end(key)
                return pipe
            from diffusers import StableDiffusionImg2ImgPipeline
            pipe = self._load_sd(key, settings.sd_base_model, StableDiffusionImg2ImgPipeline)

            # LoRA（像素/卡哇伊）：模型文件放 model_dir
            lora = settings.lora_qstyle_path
            lp = os.path.join(settings.model_dir, lora) if lora and not os.path.isabs(lora) else lora
            if lp and os.path.exists(lp):
                pipe.load_lora_weights(lp, adapter_name="qstyle")
            # IP-Adapter 保身份（可选）
            if settings.ip_adapter_repo:
                try:
                    pipe.load_ip_adapter(
                        settings.ip_adapter_repo,
                        subfolder="models",
                        weight_name=settings.ip_adapter_weight_file.split("/")[-1],
                    )
                except Exception as e:
                    print(f"[registry] skip IP-Adapter: {e}")
            return pipe

    def get_sd_inpaint(self):
        with _lock:
            key = "sd15_inpaint"
            pipe = self._sd_pipes.get(key)
            if pipe is not None:
                self._sd_pipes.move_to_end(key)
                return pipe
            from diffusers import StableDiffusionInpaintPipeline
            return self._load_sd(key, settings.sd_inpaint_model, StableDiffusionInpaintPipeline)

    # ---------------- ONNX ----------------
    def _get_ort_session(self, key: str, filename: str, gpu: bool = True):
        import onnxruntime as ort
        path = _file_in_model_dir(filename)
        if path is None:
            raise FileNotFoundError(
                f"model file not found: {os.path.join(settings.model_dir, filename)}；"
                f"请运行 scripts/download_models.sh 下载权重"
            )
        if key in self._onnx:
            self._onnx.move_to_end(key)
            return self._onnx[key]
        providers = ["CUDAExecutionProvider", "CPUExecutionProvider"] if gpu and _has_cuda() else ["CPUExecutionProvider"]
        sess = ort.InferenceSession(path, providers=providers)
        self._onnx[key] = sess
        while len(self._onnx) > 3:
            self._onnx.popitem(last=False)
        return sess

    def get_animegan(self):
        with _lock:
            return self._get_ort_session("animegan", settings.animegan_onnx, gpu=True)

    def get_u2net_parsing(self):
        with _lock:
            return self._get_ort_session("u2net", settings.u2net_parsing_onnx, gpu=True)


registry = ModelRegistry()

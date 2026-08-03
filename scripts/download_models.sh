#!/usr/bin/env bash
# 模型权重一键下载 → 放入 deploy/models/（与 .env 的 MODEL_DIR 对应）
# 用法: bash scripts/download_models.sh [models_dir]
# 注意: SD 底模/IP-Adapter 存于 HuggingFace；worker 首次启动也可自动下载，
#       本脚本只是提前落盘（网络受限机器尤其需要）。
set -euo pipefail
DIR="${1:-deploy/models}"
mkdir -p "$DIR"

echo "==> 1) AnimeGANv2 ONNX（轻量风格迁移，MIT，可商用）"
if [ ! -f "$DIR/animegan_v2.onnx" ]; then
  mkdir -p "$DIR"
  # 官方/社区保持的 face v2 onnx（若链接失效见 docs/部署与打包手册 §3.2 备选地址）
  curl -L --fail -o "$DIR/animegan_v2.onnx" \
    "https://github.com/TachibanaYoshino/AnimeGANv2/raw/master/onnx/animegan_v2.onnx" \
  || echo "  ⚠️ 下载失败；请查看 docs/部署与打包手册 §3.2 手动下载 AnimeGANv2 onnx"
else echo "  skip (exists)"; fi

echo "==> 2) U²-Net human parsing ONNX（发区/人体分割，Apache-2.0，可商用）"
if [ ! -f "$DIR/u2net_parsing.onnx" ]; then
  curl -L --fail -o "$DIR/u2net_parsing.onnx" \
    "https://github.com/levindabhi/onnx-human-parsing/raw/main/u2net_parsing.onnx" \
  || echo "  ⚠️ 下载失败；手册 §3.2 给了备选地址；缺失也不影响主流程（美发走启发式发区）"
else echo "  skip (exists)"; fi

echo "==> 3) SD 底模 + IP-Adapter（HuggingFace，需同意 HuggingFace 条款；CreativeML OpenRAIL-M，可商用）"
python - <<'PY' || echo "  ⚠️ pip install 'huggingface_hub[cli]' 后重试本步"
import os
from huggingface_hub import snapshot_download

cache = os.environ.get("HF_HOME", os.path.expanduser("~/.cache/huggingface"))
print("HF cache:", cache, "（此目录已被 docker-compose 挂进 worker，无需再搬文件）")
for repo in (
    "stable-diffusion-v1-5/stable-diffusion-v1-5",
    "stable-diffusion-v1-5/stable-diffusion-v1-5-inpainting",
    "h94/IP-Adapter",
):
    print("downloading", repo)
    snapshot_download(repo_id=repo)
PY

echo "==> 4) Q 版像素 LoRA（.safetensors → 需手动放 $DIR/chibi_pixel_lora.safetensors）"
echo "   获取方式二选一："
echo "   a) Civitai 搜 'chibi pixel art LoRA'（务必逐项核对许可条款，允许商用才纳入）"
echo "   b) 用 training/ 里的训练指引自训（自有版权）"
echo "   并在 deploy/.env 中设 LORA_QSTYLE_PATH=chibi_pixel_lora.safetensors"
echo "   （不配置也能跑：底模 + 像素提示词直出，效果略弱）"

echo ""
echo "完成。GFPGAN/MediaPipe/RTMPose 等由 pip 依赖自带权重自动下载，无需手动操作。"

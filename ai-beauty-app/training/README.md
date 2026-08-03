# training/ —「学习 P 图师」训练模块（占位指引）

> 用户选型确认：**暂不实现训练脚本**，推理全部使用现成权重。
> 本目录保留接入钩子与完整指引，日后需要时按本节扩展即可。

## 1. “学习专业修图师效果”的正确理解

模型 **不会实时联网** 向 P 图师学习；正确做法是：用「原图 →修图师成品」**前后对比数据对** 微调生成模型，让其输出逼近修图师水准。本工程推理管线已留三个挂载点：

| 挂载点 | 位置 | 用途 |
|---|---|---|
| LoRA 权重 | `LORA_QSTYLE_PATH`（qstyle_sd.py `load_lora_weights`） | Q版像素风定制风格 / 整体修图风格 |
| IP-Adapter scale | `POST /api/qstyle` 参数 `ip_scale` | 身份保真 vs 风格化权衡 |
| hair_fill inpainting | hair_pipeline.py | 用自家数据微调 inpaint 模型直接替换权重 |

## 2. 数据建议（风格 LoRA 最简起步）

- 收集 200–1000 对「原图/精修图」（向修图师购买版权或自有素材；爬取他人作品需授权）
- 格式：`data/train/{img}.jpg + {img}.txt`（txt 为统一触发词，如 `"pro retouch, natural skin texture, studio quality"`）
- 训练骨架（蹲 Kohya sd-scripts 最稳定）：
  ```bash
  accelerate launch sdxl_train_network.py \
    --pretrained_model_name=<SD15路径> \
    --train_data_dir=data/train --resolution=768 \
    --network_dim=16 --network_alpha=8 \
    --max_train_epochs=10 --learning_rate=1e-4 \
    --output_dir=out/ --save_model_as=safetensors
  ```
- 产出 `.safetensors` → 放 `deploy/models/` → `.env` 填 `LORA_QSTYLE_PATH` → 重启 worker

## 3. 许可红线（必看）

- Civitai 等站点的现成 LoRA，多数 **禁止商用** 或仅研究用途 —— 每个文件单独核对
- 自训数据务必拥有肖像权/版权授权
- 可商用底座推荐 SD1.5（OpenRAIL-M）与本工程已选的可商用模型（见 docs/01 §5）

# AI 美颜修图 — 完整可打包工程

一体机交付：**Flutter 双端 APP + FastAPI GPU 推理后端 + 打包脚本 + 部署文档**。

- 🎨 **Q 版像素风**：任意图（人像/宠物/风景）→ 大眼圆脸像素可爱风；参数可调颗粒度/强度/保背景
- 💅 **AI 美颜 P 图**：美白·磨皮·美发·补发·瘦脸·瘦身·瘦腿·大眼·唇眉，勾选组合 + 强度滑块
- 🖼 前后对比拖动滑块、历史记录、保存相册、系统分享
- ⚙️ SD+LoRA（GPU 精处理）与 AnimeGAN（轻量）**双模式自动切换**；纯 CV 美颜功能无 GPU 也能用

## 目录速览

| 目录 | 内容 |
|---|---|
| `server/` | 后端推理服务（FastAPI + Celery + MinIO + diffusers/MediaPipe 管线） |
| `app/` | Flutter 移动端（Android/iOS 一套代码） |
| `deploy/` | docker-compose + nginx + `.env.example` 一键部署 |
| `scripts/` | `download_models.sh` / `build_android.sh` / `build_ios.sh` |
| `training/` | 「学习P图师」微调接入指引（本期未启用训练模块） |
| `docs/01-技术方案与模型清单.md` | 架构、API、模型权限清单 |
| `docs/部署与打包手册.md` | **从 0 到装上手机的全流程** |
| `otherModels.txt` | 模型清单速查 + 许可红线 |

## 最快的 3 步

```bash
# 1) 后端（GPU 服务器，无 GPU 自动降级 mock/lite）
cd deploy && cp .env.example .env   # 改 API_TOKEN/S3_SECRET_KEY
docker compose up -d --build

# 2) 模型
bash scripts/download_models.sh

# 3) APP
cd ../app && flutter pub get && flutter run   # 设置页填服务器地址+token
```

打包：见 `scripts/build_android.sh`（debug/apk/aab）与 `scripts/build_ios.sh`（IPA）。
详细每步：`docs/部署与打包手册.md`。

## 诚实说明

- 本仓库**不含**可直接安装的二进制包——APK/IPA 由你在打包机执行 §5 产出（iOS 需 macOS+签名）
- 核心生成能力依赖后端 GPU；无 GPU 自动降级并在结果里如实标注 `mode`
- 各模型许可与商用风险见模型清单；Civitai 第三方 LoRA 需**逐个核许可**

---

## 新增：行迹智能旅游路线规划软件

独立的 Vue 3 + FastAPI 子工程位于 [`travel-planner/`](travel-planner/)，包含高德地图 JS API 2.0 集成、POI/距离矩阵适配、K-Means + 最近邻 + 2-opt 路径优化、PostGIS 数据库设计、Docker 部署与测试。

- [快速开始与项目说明](travel-planner/README.md)
- [系统架构与路线算法](travel-planner/docs/architecture.md)
- [API / 数据库 / 部署文档](travel-planner/docs/)

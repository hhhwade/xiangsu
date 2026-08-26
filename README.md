# 行迹｜智能旅游路线规划软件

一套面向自由行用户的智能行程规划产品：输入目的地、停留时间、景点偏好和出行方式，自动生成按天拆分、区域集中、**无回头路 / 无交叉 / 不超时**的旅行路线。

本仓库当前交付包含：

- **Web 规划器**：Vue 3 + TypeScript + 高德 JS API 2.0 适配，位于 [`travel-planner/frontend`](travel-planner/frontend)。
- **FastAPI 路线服务**：高德 POI/距离矩阵适配、K-Means、最近邻、2-opt、营业时间和 Buffer 校验，位于 [`travel-planner/backend`](travel-planner/backend)。
- **Android APK 壳**：Flutter WebView 打包的离线优先行程软件，位于 [`app`](app)，由根目录 GitHub Actions 的 **Build Android APK** 工作流构建。
- **原生高德 Android 路径**：Capacitor + Android AMap SDK bridge，位于 [`travel-planner/frontend/android`](travel-planner/frontend/android)，Key 仅在 Gradle 构建时注入。

## 快速入口

| 目标 | 文档 / 目录 |
|---|---|
| Web 与 API 快速开始 | [travel-planner/README.md](travel-planner/README.md) |
| 系统架构、算法、数据流 | [architecture.md](travel-planner/docs/architecture.md) |
| API 契约 | [api.md](travel-planner/docs/api.md) |
| PostGIS 数据库设计 | [database.sql](travel-planner/docs/database.sql) |
| Docker / Nginx 部署 | [deployment.md](travel-planner/docs/deployment.md) |
| **APK 打包与高德 Key 边界** | [mobile-apk.md](travel-planner/docs/mobile-apk.md) |

## 验证

```bash
cd travel-planner/frontend && npm ci && npm run build
cd ../backend && PYTHONPATH=. .venv/bin/python -W error -m pytest -q
```

已生成的原生高德地图安装包位于 [`travel-planner/release/xingji-smart-travel-amap-v1.0.6-debug.apk`](travel-planner/release/xingji-smart-travel-amap-v1.0.6-debug.apk)。它使用竖屏上路线、下高德地图的可滑动布局，支持全国城市扩展、1–30 天与交通方式重算；完整的 APK 验证、安装、重签名和高德 Key 绑定说明见 [mobile-apk.md](travel-planner/docs/mobile-apk.md)。

## 高德 Key 安全原则

- **Web 服务 Key** 只放在 FastAPI 运行环境 `AMAP_WEB_SERVICE_KEY`，绝不进入 APK 或前端 Bundle。
- **Android 平台 Key** 只通过 `AMAP_ANDROID_KEY` 在原生 Android Gradle 构建时注入，绝不提交源码。
- **JS API Key** 仅可作为受 Referer 限制的前端构建变量使用。

历史美颜模块的源码仍保留在仓库中，但当前 Android 入口与根 README 已切换为行迹智能旅行产品。

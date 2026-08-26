# 行迹｜智能旅游路线规划软件

> 输入目的地与偏好，自动生成按天拆分、**不绕路 / 不回头 / 无交叉**的行程；左侧可编辑路线，右侧高德地图同步联动。

这是与仓库原有移动端工程并存的独立 Web + API 子工程，采用 **Vue 3 + TypeScript + Vite**、**FastAPI**、高德地图 JS API 2.0 / Web Service API，以及自研 K-Means + 最近邻 + 2-opt 路径优化器。

## 已实现

- 完整输入参数：目的地自动建议、天数/小时、10 类偏好、出行方式、每日时长、预算、同行人、无障碍、出发时间、特殊需求。
- 按天区域聚类、簇内最近邻排序、开放路径 2-opt、几何交叉复核、每日硬时长与 15 分钟 Buffer 校验。
- 营业时间 / 周闭馆日检查，午间休息预留，以及候选不足提示。
- 左侧路线卡片支持点击联动和原生拖拽排序；右侧地图支持每日/全部路线切换、点位弹窗、时间线联动。
- 未配置 Key 时可用高质量离线演示 POI 与地图预览；配置 Key 后切换到高德 JS 底图，后端使用高德 POI/地理编码/距离矩阵。
- Docker、Nginx、PostGIS 数据模型、接口文档、算法单测均已包含。

## 快速开始（演示模式）

### 1. 前端

```bash
cd travel-planner/frontend
cp .env.example .env             # 可先保持 Key 为空，使用地图预览模式
npm install
npm run dev                       # http://localhost:5173
```

在 **Vite 开发模式** 中，未设置 `VITE_API_BASE_URL` 会使用内置演示数据，因此可以独立审阅 UI；生产构建在该变量为空时会请求同源 `/api`（由 Nginx 代理到 FastAPI）。要在本地开发时连接 API：

```bash
# frontend/.env
VITE_API_BASE_URL=http://localhost:8000
VITE_AMAP_JS_KEY=你的_JS_API_Key
VITE_AMAP_SECURITY_JS_CODE=你的_安全密钥
```

### 2. 后端

```bash
cd travel-planner/backend
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

打开 `http://localhost:8000/docs` 可试用 OpenAPI。`AMAP_WEB_SERVICE_KEY` 为空时服务返回本地演示 POI；生产环境必须填写该**服务端** Key。

### 3. 验证

```bash
cd travel-planner/frontend && npm run build
cd ../backend && PYTHONPATH=. .venv/bin/pytest -q
```

## 高德 Key 安全边界

| 使用位置 | 环境变量 | 作用 | 约束 |
|---|---|---|---|
| 前端 | `VITE_AMAP_JS_KEY` | JS API 2.0 底图、标记、路线绘制 | 在高德控制台限制 Referer / 部署域名；浏览器 Key 本身可见是正常设计 |
| 前端 | `VITE_AMAP_SECURITY_JS_CODE` | JS API 安全密钥 | 构建时注入，不提交 `.env` |
| 后端 | `AMAP_WEB_SERVICE_KEY` | POI、输入提示、地理编码、距离矩阵 | **永不**响应给浏览器、永不放进 Vite 环境变量 |

申请入口：[高德开放平台](https://lbs.amap.com/)。详见 [部署方案](docs/deployment.md)。

## 目录

```text
travel-planner/
├── frontend/                 # Vue 3 单页应用与 AMap JS 2.0 组件
├── backend/                  # FastAPI 规划 API、AMap adapter、优化器
│   ├── app/services/optimizer.py  # K-Means / NN / 2-opt / 时间营业校验
│   └── tests/                # 路径无交叉、时长边界、集成测试
├── deploy/                   # Docker Compose + Nginx
└── docs/
    ├── architecture.md       # 系统架构设计
    ├── api.md                # REST API 契约
    ├── database.sql          # PostgreSQL + PostGIS DDL
    └── deployment.md         # 生产部署与运维
```

## 关键文档

- [系统架构与路线算法](docs/architecture.md)
- [数据库设计（PostGIS）](docs/database.sql)
- [API 设计](docs/api.md)
- [部署方案](docs/deployment.md)

## 产品约束落实表

| 硬约束 | 实现位置 |
|---|---|
| 同区域集中、避免折返 | `geographic_clusters` + `ordered_clusters` |
| 无交叉路线 | `two_opt` + `route_has_crossings`，输出前二次复核 |
| 每日总时长不超限 | `schedule_route` 的 `cutoff` 硬边界 |
| 每段 15 分钟 Buffer | `BUFFER_MINUTES = 15`，并计入每日预算 |
| 到达时营业 | `opening_adjusted_arrival` + 闭馆日检查 |
| 3–6 个景点体验均衡 | 每簇上限 6、稀疏日补位与明确告警 |
| 地图 / 列表双向联动 | `MapCanvas.vue`、`ItineraryPanel.vue`、`TimelineStrip.vue` |

> 路径优化是近似算法；实时道路封闭、临时营业调整和票务规则须以高德/景点官方信息为准。

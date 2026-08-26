# 部署与运维方案

本文给出从本地验收到生产的推荐部署方式。组件：Vue 静态站点 + Nginx、FastAPI、Redis（生产建议）、PostgreSQL/PostGIS（账户/保存版本）。

---

## 1. 前置条件

| 项 | 最低建议 |
|---|---|
| OS | Ubuntu 22.04+ / 任意 Docker 兼容 Linux |
| Docker | Engine 24+ 与 Compose v2 |
| 域名 | 例如 `trip.example.com`，已可配置 TLS |
| 高德账号 | 已申请 **JS API 2.0 Key**、**Web 服务 Key** |
| 生产数据 | 托管 PostgreSQL 16 + PostGIS 3 或独立数据库集群 |
| Redis | 托管 Redis 或 Compose 内 Redis（单机演示） |

### 1.1 高德控制台配置

1. 到 [高德开放平台](https://lbs.amap.com/) 创建应用。
2. 创建 **JS API** Key：启用 Maps JS API 2.0；把 `https://trip.example.com` 加入 Referer/域名白名单。
3. 若控制台要求安全密钥，记录 `securityJsCode`。
4. 创建独立的 **Web 服务** Key：启用地点搜索、输入提示、地理编码、距离测量/路径规划等需要的服务。
5. 给 Web 服务 Key 设置日配额告警；不要与其他产品共享同一个 Key。
6. 不要把 Web 服务 Key 放入 `VITE_*`、前端打包文件、截图或工单。

> JS Key 可在浏览器请求中看到，这是地图厂商的正常模式；安全性来自域名限制、配额与定期轮换。Web 服务 Key 必须仅在后端环境变量中存在。

---

## 2. 本地开发

### API

```bash
cd travel-planner/backend
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env：本地可留 AMAP_WEB_SERVICE_KEY 为空，使用确定性演示 POI
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

检查：

```bash
curl http://127.0.0.1:8000/api/v1/health
curl -s http://127.0.0.1:8000/openapi.json | head
```

### Web

```bash
cd travel-planner/frontend
cp .env.example .env
# 连接本地 API 时：VITE_API_BASE_URL=http://localhost:8000
npm install
npm run dev -- --host 0.0.0.0
```

在预览或容器环境，不要让浏览器前端调用 `localhost`；使用 Nginx 的相对 `/api` 代理。

---

## 3. Docker Compose（单机）

```bash
cd travel-planner/deploy
cp .env.example .env
chmod 600 .env
# 填写 VITE_AMAP_JS_KEY / VITE_AMAP_SECURITY_JS_CODE / AMAP_WEB_SERVICE_KEY
# CORS_ORIGINS 应是用户实际访问的 https 域名
docker compose up -d --build
docker compose ps
curl http://127.0.0.1:8080/api/v1/health
```

浏览器访问 `http://<host>:8080`。开发/演示允许 Key 为空：前端会显示地图预览，后端使用内置 POI。生产不能以此替代真实高德集成。

### 3.1 Compose 拓扑

```text
Internet → edge Nginx / Load Balancer → web:80
                                     └→ web /api/* → backend:8000
backend → Redis（候选池、距离矩阵、规划缓存）
backend → managed Postgres/PostGIS（账户版）
backend → AMap Web Service HTTPS
browser → AMap JS CDN HTTPS
```

`frontend/nginx.conf` 将 `/api/` 同源代理给 `backend`，满足 iframe/live-preview 和浏览器网络边界要求。容器内服务只在私网，不暴露 API 8000 和 Redis 6379 到公网。

### 3.2 生产 TLS

将 `deploy/nginx.edge.example.conf` 放到边缘 Nginx / Ingress 后：

```nginx
server {
  listen 443 ssl http2;
  server_name trip.example.com;
  ssl_certificate     /etc/letsencrypt/live/trip.example.com/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/trip.example.com/privkey.pem;

  add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
  add_header X-Content-Type-Options nosniff always;
  add_header Referrer-Policy strict-origin-when-cross-origin always;
  add_header Content-Security-Policy "default-src 'self'; script-src 'self' https://webapi.amap.com; connect-src 'self' https://restapi.amap.com https://webapi.amap.com; img-src 'self' data: https:; style-src 'self' 'unsafe-inline' https://webapi.amap.com;" always;

  location / {
    proxy_pass http://127.0.0.1:8080;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  }
}
```

根据实际 AMap 资源域名调整 CSP；先以 report-only 模式验证，避免误伤地图瓦片资源。

---

## 4. 环境变量清单

| 变量 | 位置 | 必填 | 说明 |
|---|---|---:|---|
| `VITE_AMAP_JS_KEY` | Web build arg | 生产是 | 受域名限制的 JS API Key |
| `VITE_AMAP_SECURITY_JS_CODE` | Web build arg | 按高德配置 | JS API 安全密钥 |
| `VITE_API_BASE_URL` | Web build arg | 否 | 同源代理时保持空字符串 |
| `AMAP_WEB_SERVICE_KEY` | Backend runtime | 生产是 | 仅后端，POI/矩阵等服务 |
| `CORS_ORIGINS` | Backend runtime | 是 | 逗号分隔精确 Origin，勿长期用 `*` |
| `REDIS_URL` | Backend runtime | Beta/生产建议 | 例如 `rediss://:password@cache.example:6380/0` |
| `REQUEST_TIMEOUT_SECONDS` | Backend runtime | 否 | 上游 AMap 请求超时，默认 8 |
| `PLANNING_CACHE_TTL_SECONDS` | Backend runtime | 否 | 默认 900 秒 |
| `DATABASE_URL` | Backend runtime | 账户版是 | 建议 Secret manager 注入 |

### Secret 管理

- 本地 `.env` 必须在 `.gitignore` 中；仓库仅提交 `.env.example`。
- 云端使用 AWS Secrets Manager、GCP Secret Manager、Kubernetes Secret + External Secrets 或 Vault。
- Web build arg 会进入打包产物；只放预期公开的 **受限 JS Key**，绝不放服务端 Key。
- Key 轮换：添加新 Key → 滚动发布 → 验证指标 → 在高德控制台撤销旧 Key。

---

## 5. 数据库与 Redis

### 5.1 PostGIS 初始化

```bash
createdb travel_planner
psql "$DATABASE_URL" -f travel-planner/docs/database.sql
```

账户/保存功能上线后把 database migration 迁至 Alembic/Flyway，禁止在生产每次启动直接执行 DDL。每天备份：逻辑备份 + WAL/PITR；季度执行恢复演练。

### 5.2 Redis 策略

| 数据 | TTL | Key 示例 | 失效方式 |
|---|---:|---|---|
| 地理编码 | 7 天 | `geo:杭州西湖` | 地点变更/手动刷新 |
| POI 候选 | 15–60 分钟 | `poi:330100:natural,museum` | 正常过期 |
| 距离矩阵 | 5–15 分钟 | `matrix:driving:hash` | 方式/时间桶变化 |
| 规划结果 | 5–15 分钟 | `plan:hash` | 参数变化/POI snapshot 变更 |
| 速率限制 | 1 分钟 | `ratelimit:user:...` | 正常过期 |

目前代码在未连接 Redis 时使用有界内存 TTL cache，保证开发和演示可运行。生产应把该 cache interface 接到 Redis，并设置 `maxmemory-policy allkeys-lru`、TLS、密码和网络 ACL。

---

## 6. CI/CD 与发布流程

### 6.1 推荐流水线

```text
PR → npm ci + npm run build → pytest → dependency/SAST scan
   → build immutable images → push registry
   → staging deploy → smoke test /api/v1/health + browser E2E
   → canary 5% → monitor 15 min → 100% rollout
```

最低检查：

```bash
cd travel-planner/frontend && npm ci && npm run build
cd ../backend && python -m pip install -r requirements.txt && PYTHONPATH=. pytest -q
```

### 6.2 健康检查与回滚

- `GET /api/v1/health`：容器 liveness。
- 生产拆分 `/live`（进程活着）和 `/ready`（Redis/DB/关键配置可用）。
- 镜像按 Git SHA 标记；保留前 3 个可用版本。
- AMap 错误率、规划 P95、无路线率高于阈值时：熔断外部调用 → cache/估算降级 → 必要时回滚。

---

## 7. 监控与告警

| 告警 | 参考阈值 | 行动 |
|---|---:|---|
| API 5xx 比例 | > 1% / 5min | 检查部署、依赖、错误追踪 |
| AMap 429/配额 | > 0 / 5min | 降低并发、核对配额、启用缓存 |
| 规划 P95 | > 4s / 10min | 分析外部 I/O、缓存命中、worker |
| `backtrackCheck=warning` | > 0 | 阻断发布，检查几何校验 |
| Redis memory | > 80% | 扩容/缩短 TTL |
| 地图 JS 加载失败 | > 2% | 检查 Referer、CSP、Key 轮换 |

日志需要结构化字段：`request_id`、`user_id_hash`、`destination_adcode`、`poi_count`、`day_count`、`mode`、`source`、`amap_latency_ms`。不得记录完整 Key、原始特殊需求文本或精确家庭住址。

---

## 8. 上线验收清单

- [ ] JS Key 只允许正式域名，Web Service Key 未出现在前端 bundle。
- [ ] HTTPS、HSTS、CSP、精确 CORS Origin 已启用。
- [ ] 所有 `/api` 走相对 URL，浏览器无 `localhost` 请求。
- [ ] `npm run build` 和 `pytest -q` 全绿。
- [ ] 高德 POI、距离矩阵、超时和限流降级分别演练。
- [ ] 测试 1/3/7 天、小时模式、老人无障碍、闭馆日、主题乐园和候选不足。
- [ ] 地图 Marker/卡片/时间轴点击与拖拽均联动。
- [ ] 输出路径的无交叉、每日预算、营业时间不变量有自动化测试。
- [ ] PostgreSQL/Redis 备份、恢复、密钥轮换和告警负责人已明确。

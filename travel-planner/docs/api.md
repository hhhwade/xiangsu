# REST API 设计

Base URL：`/api/v1`  
传输：HTTPS + JSON UTF-8  
交互文档：启动 API 后访问 `/docs`（FastAPI OpenAPI）

> 字段均为 camelCase。后端 Pydantic 模型支持 snake_case 内部实现，但公网契约以本文和 OpenAPI 为准。

---

## 1. 通用约定

### 1.1 响应头

| Header | 说明 |
|---|---|
| `Content-Type: application/json` | 所有 JSON 响应 |
| `X-Request-ID`（生产建议） | 贯穿 Nginx / API / AMap 调用，便于排障 |
| `Cache-Control: no-store` | 涉及私有行程的响应建议设置 |

### 1.2 错误码

| HTTP | code | 说明 | 前端策略 |
|---:|---|---|---|
| 400 | `INVALID_REQUEST` | 语义错误，例如预算上下界倒置 | 高亮字段 |
| 401/403 | `UNAUTHORIZED` | 登录/分享权限不足（账户版） | 引导登录 |
| 404 | `PLAN_NOT_FOUND` | 行程或短链不存在 | 返回列表 |
| 422 | FastAPI validation | 类型、范围、必填校验失败 | 显示字段错误 |
| 429 | `RATE_LIMITED` | 用户或上游高德限流 | 使用缓存/稍后重试 |
| 502 | `AMAP_UNAVAILABLE` | 高德不可用且无可用降级 | 保留表单、提示重试 |
| 503 | `PLANNER_BUSY` | 队列/依赖拥堵 | 指数退避重试 |

建议错误体：

```json
{
  "error": {
    "code": "AMAP_UNAVAILABLE",
    "message": "地图服务暂时不可用，请稍后重试。",
    "requestId": "req_01J...",
    "retryable": true
  }
}
```

---

## 2. 目的地自动补全

### `GET /destinations/autocomplete`

调用高德输入提示；无服务 Key 时返回本地演示城市匹配项。

**Query**

| 参数 | 类型 | 必填 | 约束 | 示例 |
|---|---|---:|---|---|
| `q` | string | 是 | 1–80 字 | `杭州西` |

**200 Response**

```json
[
  {
    "name": "杭州西湖风景名胜区",
    "district": "西湖区",
    "location": { "lng": 120.1309, "lat": 30.2377 }
  }
]
```

前端使用建议：输入防抖 250–350ms；取消过时请求；用户选定项后提交文本 + 可选 `startLocation`。

---

## 3. 生成路线

### `POST /plans`

创建一个**无状态**规划结果。账户版可在此基础上追加 `POST /plans/{id}/save`；MVP 直接返回可渲染 JSON。

**Request body**

```json
{
  "destination": "杭州",
  "duration": { "value": 3, "unit": "days" },
  "preferences": ["natural", "culture", "food", "museum"],
  "transportMode": "driving",
  "dailyHours": 8,
  "budget": { "min": 1200, "max": 3000 },
  "groupSize": { "adults": 2, "children": 0, "elderly": false, "accessible": false },
  "startDate": "2026-10-01T09:00:00+08:00",
  "startLocation": { "lng": 120.155, "lat": 30.274 },
  "specialNeeds": "素食优先，避开太拥挤的景点"
}
```

**字段定义**

| 字段 | 类型 | 必填 | 规则 |
|---|---|---:|---|
| `destination` | string | 是 | 1–120 字，城市/区域/景区 |
| `duration.value` | number | 是 | `days` 为 1–30；`hours` 为 1–720 |
| `duration.unit` | `days` / `hours` | 是 | 小时模式最后一天可短于 dailyHours |
| `preferences` | string[] | 否 | `natural/culture/food/family/shopping/trending/museum/themePark/outdoor/temple` |
| `transportMode` | enum | 否 | `walking/riding/driving/transit`，默认 `driving` |
| `dailyHours` | number | 否 | 2–16，默认 8 |
| `budget` | object | 否 | `min/max >= 0` 且 min ≤ max |
| `groupSize` | object | 否 | `adults/children/elderly/accessible` |
| `startDate` | ISO 8601 datetime | 否 | 用于营业时间、第一日开始时间 |
| `startLocation` | `{lng,lat}` | 否 | 影响第一日区域与路线起点 |
| `specialNeeds` | string | 否 | 最大 500 字，作为候选过滤/提示输入 |

**200 Response（节选）**

```json
{
  "destination": "杭州",
  "totalDays": 3,
  "routes": [
    {
      "day": 1,
      "title": "西湖经典环线",
      "color": "#DE7444",
      "spots": [
        {
          "id": "B000A8UIN8",
          "name": "断桥残雪",
          "type": "自然风光",
          "location": { "lng": 120.15, "lat": 30.26 },
          "estimatedDuration": 45,
          "priority": 1,
          "arrivalTime": "09:00",
          "leaveTime": "09:45",
          "nextSpot": "白堤",
          "nextDistance": "0.8km",
          "nextDuration": "步行 10分钟",
          "tips": "建议清晨前往，避开人流高峰。",
          "openHours": "全天开放"
        }
      ],
      "totalDistance": "6.5km",
      "totalVisitDuration": "5.5h",
      "totalTransportDuration": "1.2h",
      "summary": "围绕西湖一周，经典景点全覆盖。",
      "notices": ["每两处景点间已预留 15 分钟弹性缓冲。"]
    }
  ],
  "overallStats": {
    "totalDistance": "18.5km",
    "totalSpots": 12,
    "backtrackCheck": "passed",
    "totalDuration": "24.0h"
  },
  "generatedAt": "2026-08-26T10:00:00Z",
  "source": "amap",
  "warnings": []
}
```

### 输出保证

1. `routes[day].spots` 是地图连接顺序，`priority` 从 1 开始连续。
2. 若 `backtrackCheck = passed`，每条输出折线已无非相邻边交叉。
3. 每条非空日程均满足 `last.leaveTime - first.arrivalTime <= dailyHours`（含交通、Buffer 与休息）。
4. 返回的 `warnings` 不应被忽略：它可能表示候选不足、降级估算或时段冲突。
5. 字符串距离/时长面向显示；后续分析应使用持久化 schema 的数值字段或扩展 API。

### 典型前端调用

```ts
const response = await fetch('/api/v1/plans', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(form),
})
if (!response.ok) throw new Error(await response.text())
const plan = await response.json()
```

同源 `/api` 由 Nginx 转发到 FastAPI，禁止在浏览器写 `http://localhost:8000`。

---

## 4. 拖拽重排

### `POST /plans/reorder`

用于用户在路线列表中拖拽后请求服务端重新校验顺序与时间。当前前端先乐观重绘地图，再调用此接口替换为服务端结果。

**Request body**

```json
{
  "request": {
    "destination": "杭州",
    "duration": { "value": 3, "unit": "days" },
    "preferences": ["natural", "culture"],
    "transportMode": "walking",
    "dailyHours": 8
  },
  "day": 1,
  "orderedSpotIds": ["B000A8UIN8", "HZ-BAIDI", "HZ-PHQY"]
}
```

**200 Response**：与 `POST /plans` 相同。

**规则**：未知 ID 会忽略；未提交的原有 ID 追加到末尾，避免客户端竞态导致丢景点。生产增强版应把 `planId` 和 `planRevision` 放入请求，若 revision 不匹配返回 `409 PLAN_CONFLICT`。

---

## 5. 健康检查

### `GET /health`

**200 Response**

```json
{
  "status": "ok",
  "service": "travel-route-planner",
  "amapWebServiceConfigured": true,
  "optimizer": "geographic-kmeans + nearest-neighbor + 2-opt"
}
```

用于容器 liveness/readiness 的简版检查。生产建议追加 Redis ping、数据库连接、上游熔断状态，分别暴露 `/live` 和 `/ready`。

---

## 6. 未来资源接口

| Endpoint | 方法 | 用途 |
|---|---|---|
| `/plans/{planId}` | GET | 读取已保存计划 |
| `/plans/{planId}` | PATCH | 修改偏好/停留时长，乐观锁 `revision` |
| `/plans/{planId}/recalculate` | POST | 实时路况/日期变化后局部重算 |
| `/plans/{planId}/export?format=pdf` | GET | 后端生成 PDF/图片行程单 |
| `/plans/{planId}/share` | POST | 生成带过期和权限的短链 |
| `/ws/plans/{planId}` | WebSocket | 协作编辑、异步重算进度 |

账户、保存、分享接口需要 JWT/OIDC、对象级授权、审计日志和删除/导出个人数据能力。

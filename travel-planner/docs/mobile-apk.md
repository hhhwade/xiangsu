# Android 安装包、高德 POI 与签名说明

## 已生成：Release 签名 APK v1.1.1

下载文件：

```text
travel-planner/release/xingji-smart-travel-amap-v1.1.1-release.apk
```

| 项 | 值 |
|---|---|
| 应用名 | 行迹智能旅行 |
| 包名 | `com.xingji.travel` |
| 最低 Android | API 21 / Android 5.0 |
| target SDK | API 34 |
| APK SHA-256 | `68da23a2d8d39c6b8d5a908dc7b259a920de9d327fd2dbb6cad71d587f13ad59` |
| 签名 | RSA-3072 Release 签名，v1 / v2 / v3 已验证 |

## 景点坐标精度与描述

v1.1.1 将地点来源拆成两层：

1. **高德 POI 实时层（优先）**：用户重新生成路线时，原生 Android 通过 AMap Search SDK 以城市和偏好查询真实 POI。返回的景点名称、类型和 GCJ-02 坐标同时进入路线卡片与原生 MapView；地址只作为地址提示保留；
2. **景点概述层**：经典路线使用编辑式景点概括；高德实时 POI 使用“它是什么、在城市中扮演什么角色、为什么值得游览”的概括，避免把地址摘要当作景点介绍；
3. **离线兜底层**：网络/搜索异常时，使用内置城市中心和精选景点池，保证路线仍可生成，并提供按类型生成的概述。

因此上方路线和下方地图不再分别使用两套坐标。每个景点现在有：

```text
名称 / 类型 / 景点概述 / 到达与离开时间 / 游览时长 / 地址提示 / 下一段交通
```

## 安装前必做

### 1. 卸载旧 Debug 包

Debug 包与 Release 包签名不同，Android 不允许覆盖升级：

```text
设置 → 应用 → 行迹智能旅行 → 卸载
```

### 2. 更新高德 Android Key 的发布 SHA1

在高德控制台的 Android Key 配置中添加：

```text
PackageName: com.xingji.travel
发布版安全码 SHA1: 88:A8:50:03:77:C8:86:35:A0:9D:1F:CF:D7:54:0E:AE:12:58:2E:00
```

并确保该 Key 允许 Android 地图/搜索服务。未绑定 Release SHA1 时，APK 可以安装，但高德地图或 POI 查询会鉴权失败。

## 路线与地图同步机制

1. **相同 POI 数据源**：高德 POI 搜索结果同时用于路线和地图；
2. **相同编号**：路线卡片第 N 站，对应地图中同色圆形 Marker N；
3. **方向箭头**：每条 Marker 间 Polyline 有方向箭头，清楚显示 N → N+1；
4. **Revision 防竞态**：每次 Day、交通方式、重新规划或拖拽后递增 route revision；原生层忽略旧回调。

## 手机产品能力

| 用户需求 | v1.1.1 实现 |
|---|---|
| 手机布局 | 竖屏，上方可滚动路线面板，下方固定高德地图 |
| 城市 | 高德 Search SDK 实时 POI 优先；全国城市中心建议和离线扩展兜底 |
| 停留天数 | 1–30 天，动态 Day Tab |
| 交通方式 | 步行、骑行、自驾、公交重算顺序、距离、时间、地图线条样式 |
| 景点描述 | 每个景点展示高德摘要或离线实用描述 |
| 编号同步 | 路线第 N 站与高德地图编号 N Marker 一一对应，并有方向箭头 |

## 关于“高风险应用 / 未查询到 ICP”

Release 签名和 target SDK 34 已修复 APK 自身能修复的风险因素。设备仍提示“未查询到 ICP 备案信息”时，这是中国 Android 厂商对未上架侧载 App 的分发信任提示，不能通过篡改 APK 合法消除。

需要厂商低风险/可信分发状态时，应使用固定 Release 签名、视实际分发地区完成 ICP 备案，并提交官方应用商店或厂商安全检测渠道。不要关闭设备保护或安装来源不明的替换包。

## 关键源文件

```text
travel-planner/native-amap/MainActivity.java          # MapView、POI 搜索、Marker/Polyline、revision
travel-planner/native-amap/web/index.html             # 手机端卡片 UI
travel-planner/native-amap/web/route-panel.js         # 城市、路线、POI 回调、描述
travel-planner/native-amap/build-native-amap-apk.sh   # Key/证书/SDK 通过环境变量注入
```

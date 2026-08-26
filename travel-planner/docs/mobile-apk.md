# Android APK 打包与高德 Key 说明

## 已生成：应用内原生高德地图 APK

本次已完成并输出原生高德地图版本：

```text
travel-planner/release/xingji-smart-travel-amap-v1.0.2-debug.apk
```

- 应用名：**行迹智能旅行**
- 包名：`com.xingji.travel`
- 最低 Android：5.0 / API 21
- SHA-256：`7b7f514e0675155421311d25834e50ed91c4bc75197c35c2030512f7c6956a8e`
- 已验证：ZIP 对齐与 v1 / v2 / v3 debug 签名

这个版本按产品规格固定为**横屏双栏**：

| 区域 | 内容 |
|---|---|
| 左侧 40% | 目的地、偏好、出行方式、按日路线、景点顺序与时间线 |
| 右侧 60% | **应用内高德 Android MapView**、景点 Marker、按天颜色路线 Polyline、缩放和拖动 |

前端路线发生生成、日期切换或拖拽重排时，会通过 `XingjiNativeMap` bridge 将坐标、颜色、顺序发送给原生地图，右侧高德地图会立即重绘。它不是跳转到外部高德 App。

首次安装时，请在 Android 系统中允许对应文件管理器/浏览器“安装未知应用”。

> 这是 debug 签名包，适合安装测试；生产发布和应用商店上架必须使用自己的 release keystore 重签名。

## Key 的正确边界

截图中存在不同平台的 Key，不能混用：

| Key 类型 | 使用位置 | 是否应写入源码 / Vue bundle |
|---|---|---:|
| **Web 服务 Key** | FastAPI `AMAP_WEB_SERVICE_KEY`，用于 POI、地理编码、距离矩阵 | **否** |
| **Android 平台 Key** | 本 APK 的原生 Android AMap SDK `AndroidManifest.xml` | **否**；仅在构建时注入最终 APK |
| **JS API Key** | 浏览器版本的高德 JS API 2.0 | 只能作为受 Referer 限制的构建变量 |

当前版本使用的是你刚创建的 **Android 平台 Key**。Key 没有保存到 Git、`.env`、TypeScript 或 Java 源码；它只被构建流程写入最终 APK 的 AndroidManifest，这是 Android 地图 SDK 的正常机制。

## 高德控制台必须绑定

Android Key 必须配置：

```text
PackageName: com.xingji.travel
调试版 SHA1: 5D:08:26:4B:44:E0:E5:3F:BC:CC:70:B4:F0:16:47:4C:C6:C5:AB:5C
```

正式发布时，改用自己的 release keystore，并把 release SHA1 填入高德控制台的“发布版安全码 SHA1”。包名或 SHA1 不匹配时，APK 可以安装，但原生高德底图会显示鉴权错误。

## 实现位置

```text
travel-planner/native-amap/MainActivity.java      # 原生 MapView、Marker/Polyline、Vue bridge
travel-planner/frontend/src/components/MapCanvas.vue # route 数据发布到原生 map
travel-planner/native-amap/README.md              # 原生宿主说明
```

原生地图宿主负责 AMap 生命周期、Marker、按日期颜色的 Polyline、镜头自动适配；Vue 仍负责表单、算法结果、拖拽和时间线。

## 轻量 WebView APK（保留）

`xingji-smart-travel-v1.0.1-debug.apk` 是不含原生地图 SDK 的轻量离线版本，保留用于低体积演示。需要旅游路线右侧直接展示高德地图时，请使用 v1.0.2 原生 AMap APK。

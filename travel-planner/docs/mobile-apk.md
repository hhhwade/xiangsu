# Android APK 打包与高德 Key 说明

## 已生成：原生高德地图 APK v1.0.5

下载文件：

```text
travel-planner/release/xingji-smart-travel-amap-v1.0.5-debug.apk
```

- 应用名：**行迹智能旅行**
- 包名：`com.xingji.travel`
- 最低 Android：5.0 / API 21
- SHA-256：`76b6ab5c86e2778859484dc14a764f67f5f910cec72a9b9c0a3a2eb2079940a8`
- 已验证：ZIP 对齐和 v1 / v2 / v3 debug 签名。

## v1.0.5 交互规格

| 用户需求 | 实现 |
|---|---|
| 竖屏可滑动 | `MainActivity` 改为上 56% 路线面板 + 下 44% 原生 AMap `MapView`；路线区域独立滚动。 |
| 全国城市 | 输入框内置全国城市中心建议；热门城市有真实景点种子池，其余城市按城市中心、偏好与区域生成离线扩展路线。部署 FastAPI + AMap Web 服务后可替换为实时 POI。 |
| 任意天数 | 支持 1–30 天；日数改变后动态生成 Day Tab，每天依据每日时长分配 3–5 个景点。 |
| 交通方式影响路线 | 步行、骑行、自驾、公交会使用不同道路系数、速度、候选排序和等待时间，重算景点顺序、路线距离、交通时长；高德地图的线宽/虚线样式也会同步区分。 |

路线面板通过 `XingjiNativeMap` JavaScript bridge 将当前日路线、交通方式、Marker 坐标与日期颜色发送给原生 Android 层。原生层在应用内绘制高德 Marker 和 Polyline，不会跳转外部高德 App。每个 Marker 会渲染与上方经典路线一致的圆形编号：路线第 1 站对应地图编号 1，依此类推。

## 高德 Key 绑定

Android Key 必须配置：

```text
PackageName: com.xingji.travel
调试版 SHA1: 5D:08:26:4B:44:E0:E5:3F:BC:CC:70:B4:F0:16:47:4C:C6:C5:AB:5C
```

- **Web 服务 Key**：只属于 FastAPI `AMAP_WEB_SERVICE_KEY`，不能写入 APK；
- **Android 平台 Key**：仅在构建时写入最终 APK 的 AndroidManifest；
- **JS API Key**：只用于浏览器版高德 JS API，不能替代 Android Key。

包名或 SHA1 不匹配时，APK 可以安装，但原生高德底图会显示鉴权错误。

## 关键源文件

```text
travel-planner/native-amap/MainActivity.java          # 竖屏原生 MapView、Marker/Polyline
travel-planner/native-amap/web/index.html             # Android WebView 兼容路线面板
travel-planner/native-amap/web/route-panel.js         # 全国城市、任意天数、交通方式重算
travel-planner/native-amap/build-native-amap-apk.sh   # 不含 Key 的受控构建脚本
```

首次安装时，请在 Android 系统中允许对应文件管理器/浏览器“安装未知应用”。这是 debug 签名包；正式发布请使用 release keystore 重签名，并将新的 SHA1 填入高德控制台。

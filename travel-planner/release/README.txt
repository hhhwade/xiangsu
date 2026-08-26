行迹智能旅行 v1.0.8 — 路线编号同步 Release 包

文件：xingji-smart-travel-amap-v1.0.8-release.apk
包名：com.xingji.travel
最低 Android：5.0（API 21）
目标 Android API：34
APK SHA-256：ed37dbab6d1c249019ef42fb43518db9c64abdcfa44757c1cb4bfcf6179785d5

本版专门修复“上方经典路线与下方地图对不上”的问题：
- 地图顶部显示当前 Day、经典路线名称、交通方式和“编号已同步”状态；
- 每个地图 Marker 使用与路线卡片一致的 Day 色圆形编号；
- 每一段路线增加方向箭头，明确显示 1 → 2 → 3 的游览顺序；
- 路线 bridge 加入 revision，快速切换 Day / 交通方式时不会被旧回调覆盖；
- MapView 在 WebView 前初始化，避免首次路线同步的启动竞态。

安装前：
1. 卸载旧 Debug 包；
2. 高德 Android Key 的“发布版安全码 SHA1”必须包含：
   88:A8:50:03:77:C8:86:35:A0:9D:1F:CF:D7:54:0E:AE:12:58:2E:00

已进行 ZIP 对齐与 v1/v2/v3 Release 签名校验。

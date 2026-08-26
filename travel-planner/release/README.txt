行迹智能旅行 v1.0.3 — 原生高德地图 APK

文件：xingji-smart-travel-amap-v1.0.3-debug.apk
包名：com.xingji.travel
最低 Android：5.0（API 21）
SHA-256：9d199e879999661b99984ecfd235cc4681320a69eb4a38e590a43dfea428e1b2

此版本修复了 v1.0.2 左侧 WebView 空白问题：左栏使用兼容 Android WebView 的内置路线面板，不依赖 ES Module 加载。

横屏双栏：
- 左侧：目的地、偏好、出行方式、Day Tab、景点列表和拖拽排序；
- 右侧：应用内原生高德地图、Marker、按日期颜色的路线 Polyline。

切换日期、生成路线或拖拽排序时，右侧高德地图立即同步更新。

已进行 ZIP 对齐与 v1/v2/v3 debug 签名校验。首次安装时，请在 Android 系统中允许相应文件管理器/浏览器“安装未知应用”。

注意：这是 debug 签名包；生产上架请使用自己的 release keystore 重签名，并在高德控制台绑定新的 SHA1。
高德 Key 没有保存到源码或 Git；它只被构建时写入最终 APK 的 AndroidManifest。

行迹智能旅行 v1.2.3 — 全国城市真实路线增强 Release 包

文件：xingji-smart-travel-amap-v1.2.3-release.apk
包名：com.xingji.travel
最低 Android：5.0（API 21）
目标 Android API：34
APK SHA-256：39244b904fae146d25e6afc3235aea92e1dfb51b39158977a37ea00aafa2a7b3

v1.2.3 解决“九江等城市只有泛化名称”问题：
- 369 城市中心表覆盖全国目的地识别；
- 高德 POI 搜索并行查询旅游景点、博物馆、美食，得到真实景点名称和坐标；
- 对旧版 Android 高德 Search SDK 仅放行 amap.com/autonavi.com 域名的必要网络请求，不开放全局明文流量；
- 启动地图使用 HTTPS；
- 九江增加浔阳楼、锁江楼、琵琶亭、烟水亭、庐山、白鹿洞书院、东林寺等真实离线兜底景点；
- 查询失败时页面明确显示离线状态，避免用“城市博物馆/慢游点”等泛化名称伪装真实 POI。

重要安装和高德配置：
1. 本包使用新的 Release 签名；请先卸载此前的 Release/Debug 包后安装；
2. 在高德 Android Key 的“发布版安全码 SHA1”添加：
   F6:D0:77:4F:D2:A6:C7:BC:F7:EC:70:A2:56:1E:5E:5E:28:AF:10:80

已进行 ZIP 对齐与 v1/v2/v3 Release 签名校验。

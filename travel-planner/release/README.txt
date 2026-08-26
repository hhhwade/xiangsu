行迹智能旅行 v1.1.3 — 已核对实拍图 Release 包

文件：xingji-smart-travel-amap-v1.1.3-release.apk
包名：com.xingji.travel
最低 Android：5.0（API 21）
目标 Android API：34
APK SHA-256：2935b2a23951960bb41cbd1a510f41254a225c91629910a3d15ba352104dc1f4

v1.1.3 图片精度修复：
- 删除所有 AI 生成和泛化类型图片；
- 高德 POI 返回的景点图片优先显示；
- 内置经典路线仅使用已核对的 Wikimedia Commons 实拍图；
- 无法核对到该景点实拍图时，明确显示“暂无该景点实拍图”，不再使用不相干图片冒充；
- 每个图片来源记录在 assets/www/images/landmarks/CREDITS.md。

点击景点卡片可打开实拍图、景点概述、地址和地图定位详情。

安装前：卸载旧 Debug 包；高德 Android Key 的“发布版安全码 SHA1”必须包含：
88:A8:50:03:77:C8:86:35:A0:9D:1F:CF:D7:54:0E:AE:12:58:2E:00

已进行 ZIP 对齐与 v1/v2/v3 Release 签名校验。

行迹智能旅行 v1.1.0 — 高德 POI 精确定位与景点描述 Release 包

文件：xingji-smart-travel-amap-v1.1.0-release.apk
包名：com.xingji.travel
最低 Android：5.0（API 21）
目标 Android API：34
APK SHA-256：41f196ea7af133b56d88ae3db331ab96acb04212a358a883170e091af7059880

v1.1.0 地点精度升级：
- 用户点击“生成智能路线”后，应用通过 Android 高德 Search SDK 搜索当前城市的真实 POI；
- 返回的名称、类型、GCJ-02 经纬度和地址摘要会替换离线种子坐标；
- 路线和地图使用同一份实时 POI 列表，避免“上方景点”和“下方地图点”漂移；
- 每个景点卡片新增完整的景点描述；高德返回摘要优先展示，离线时使用按类型生成的实用描述；
- 搜索不可用时自动保留离线城市路线，确保行程界面不会空白。

安装前：卸载旧 Debug 包；高德 Android Key 的“发布版安全码 SHA1”必须包含：
88:A8:50:03:77:C8:86:35:A0:9D:1F:CF:D7:54:0E:AE:12:58:2E:00

已进行 ZIP 对齐与 v1/v2/v3 Release 签名校验。

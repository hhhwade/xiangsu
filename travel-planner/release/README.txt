行迹智能旅行 v1.0.7 — Release 签名安装包

文件：xingji-smart-travel-amap-v1.0.7-release.apk
包名：com.xingji.travel
最低 Android：5.0（API 21）
目标 Android API：34
APK SHA-256：a1af07cbe49a31af73cdb2181e92996a681b77457a0de9aff863492ae62c22c5

此版本相对 debug 包的安全修复：
- 使用独立的 Release RSA-3072 签名，不再使用 Android Debug 证书；
- targetSdkVersion 升级到 34；
- 禁止明文 HTTP 流量；
- 保持竖屏手机 UI、上路线下高德地图、全国城市扩展、1–30 天与交通方式重算。

安装前必须做两件事：
1. 卸载旧的 debug 包（旧包和此 release 包签名不同，Android 不允许覆盖升级）；
2. 在高德控制台为 Android Key 的“发布版安全码 SHA1”增加：
   88:A8:50:03:77:C8:86:35:A0:9D:1F:CF:D7:54:0E:AE:12:58:2E:00

未绑定该 release SHA1 时，软件可以安装，但原生高德底图会鉴权失败。

说明：设备提示“未查询到 ICP 备案信息”是中国 Android 厂商对未上架侧载 App 的分发信任提示，无法仅靠修改 APK 消除。要获得厂商白名单/低风险分发状态，需要使用固定 release 签名、ICP备案（如适用）并提交至官方应用商店或厂商安全检测平台。

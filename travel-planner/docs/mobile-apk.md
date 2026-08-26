# Android 安装包、签名与高德 Key 说明

## 已生成：Release 签名 APK v1.0.7

下载文件：

```text
travel-planner/release/xingji-smart-travel-amap-v1.0.7-release.apk
```

| 项 | 值 |
|---|---|
| 应用名 | 行迹智能旅行 |
| 包名 | `com.xingji.travel` |
| 最低 Android | API 21 / Android 5.0 |
| target SDK | API 34 |
| APK SHA-256 | `a1af07cbe49a31af73cdb2181e92996a681b77457a0de9aff863492ae62c22c5` |
| 签名 | RSA-3072 Release 签名，v1 / v2 / v3 已验证 |

此版本不再使用 `Android Debug` 证书，关闭明文 HTTP，并将 target SDK 升级到 34，以减少侧载时因 debug 签名和过低 target SDK 触发的风险提示。

## 安装前必做

### 1. 卸载旧 Debug 包

此前的 `v1.0.6-debug.apk` 签名与 Release 包不同。Android 不允许不同签名覆盖升级：

```text
设置 → 应用 → 行迹智能旅行 → 卸载
```

然后再安装 v1.0.7 Release 包。

### 2. 更新高德 Android Key 的发布 SHA1

在高德控制台的 Android Key 配置中，填写：

```text
PackageName: com.xingji.travel
发布版安全码 SHA1: 88:A8:50:03:77:C8:86:35:A0:9D:1F:CF:D7:54:0E:AE:12:58:2E:00
```

没有绑定这个 Release SHA1 时，APK 仍可安装，但应用内高德地图会提示鉴权异常。

## 关于“高风险应用 / 未查询到 ICP”

截图中的提示包含两类完全不同的问题：

1. **Debug/未知签名与旧 target SDK**：v1.0.7 已通过 Release 签名和 target SDK 34 修复；
2. **未查询到 ICP 备案信息**：这是部分中国 Android 厂商对未上架、侧载应用的分发信任提示，不能通过篡改 APK 或关闭系统防护来合法消除。

要获得厂商侧的低风险/可信分发状态，需要：

- 使用固定的 release keystore 持续签名；
- 视分发地区与业务情况完成 ICP 备案；
- 提交到应用宝、华为、小米、OPPO、vivo 等官方应用市场或厂商安全检测渠道；
- 使用与上架包一致的包名、证书和隐私政策。

不要为了绕过系统安全提示而关闭设备保护或安装来源不明的替换包。

## 产品能力

| 用户需求 | v1.0.7 实现 |
|---|---|
| 手机布局 | 竖屏，上方可滚动路线面板，下方固定高德地图 |
| 城市 | 全国城市中心建议；热门城市景点种子池；其余城市离线扩展路线；部署 API 后可切换实时高德 POI |
| 停留天数 | 1–30 天，动态 Day Tab |
| 交通方式 | 步行、骑行、自驾、公交重算顺序、距离、时间、地图线条样式 |
| 编号同步 | 路线第 N 站与高德地图编号 N Marker 一一对应 |

## 关键源文件

```text
travel-planner/native-amap/MainActivity.java          # MapView、Marker/Polyline、桥接
travel-planner/native-amap/web/index.html             # 手机端卡片 UI
travel-planner/native-amap/web/route-panel.js         # 城市、天数、交通方式重算
travel-planner/native-amap/build-native-amap-apk.sh   # Key/证书均通过环境变量注入
```

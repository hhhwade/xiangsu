# Android 安装包、签名与高德 Key 说明

## 已生成：Release 签名 APK v1.0.9

下载文件：

```text
travel-planner/release/xingji-smart-travel-amap-v1.0.9-release.apk
```

| 项 | 值 |
|---|---|
| 应用名 | 行迹智能旅行 |
| 包名 | `com.xingji.travel` |
| 最低 Android | API 21 / Android 5.0 |
| target SDK | API 34 |
| APK SHA-256 | `381c0234cab176e416bc71e48e56ca12207c4fafabec016216bd7a35e50c6cbe` |
| 签名 | RSA-3072 Release 签名，v1 / v2 / v3 已验证 |

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

未绑定 Release SHA1 时，APK 可以安装，但应用内高德底图会鉴权失败。

## 路线与地图同步机制

v1.0.9 对同步链路增加了三个保证：

1. **相同编号**：路线卡片第 N 站，对应地图中同色圆形 Marker N；
2. **方向箭头**：每条 Marker 间 Polyline 有方向箭头，清楚显示 N → N+1；
3. **Revision 防竞态**：每次 Day、交通方式、重新规划或拖拽后递增 route revision；原生层忽略旧回调，防止旧路线覆盖新路线。

地图顶部会显示：

```text
Day N · 当前经典路线 · 当前交通方式 · 编号已同步
```

## 手机产品能力

| 用户需求 | v1.0.9 实现 |
|---|---|
| 手机布局 | 竖屏，上方可滚动路线面板，下方固定高德地图 |
| 城市 | 全国城市中心建议；热门城市景点种子池；其余城市离线扩展路线；部署 API 后可切换实时高德 POI |
| 停留天数 | 1–30 天，动态 Day Tab |
| 交通方式 | 步行、骑行、自驾、公交重算顺序、距离、时间、地图线条样式 |
| 编号同步 | 路线第 N 站与高德地图编号 N Marker 一一对应，并有方向箭头 |

## 关于“高风险应用 / 未查询到 ICP”

Release 签名和 target SDK 34 已修复 APK 自身能修复的风险因素。设备仍提示“未查询到 ICP 备案信息”时，这是中国 Android 厂商对未上架侧载 App 的分发信任提示，不能通过篡改 APK 合法消除。

需要厂商低风险/可信分发状态时，应使用固定 Release 签名、视实际分发地区完成 ICP 备案，并提交官方应用商店或厂商安全检测渠道。不要关闭设备保护或安装来源不明的替换包。

## 关键源文件

```text
travel-planner/native-amap/MainActivity.java          # MapView、编号 Marker、箭头、revision
travel-planner/native-amap/web/index.html             # 手机端卡片 UI
travel-planner/native-amap/web/route-panel.js         # 城市、天数、交通方式与 revision
travel-planner/native-amap/build-native-amap-apk.sh   # Key/证书均通过环境变量注入
```

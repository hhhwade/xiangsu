# Android APK 打包与高德 Key 说明

## 已生成 APK

本次已在本地完成一个可安装的 Android debug APK：

```text
travel-planner/release/xingji-smart-travel-v1.0.0-debug.apk
```

- 应用名：**行迹智能旅行**
- 包名：`com.xingji.travel`
- 最低 Android：5.0 / API 21
- 签名：已通过 ZIP 对齐和 v1 / v2 / v3 debug 签名验证
- SHA-256：见同目录 `.sha256` 文件

该 APK 把 Vue 路线规划 UI、离线候选池、路线卡片、拖拽排序、时间线和地图预览全部打入软件，不依赖 `localhost` 或本地后端。首次安装时，请在 Android 系统中允许对应浏览器/文件管理器“安装未知应用”。

> 这是 debug 签名包，适合安装测试；生产发布和应用商店上架必须使用你自己保存的 release keystore 重签名。

## 轻量 APK 构建路径

最终 APK 使用预编译 Android WebView runtime 打包静态网页资源，不需要在本机安装 Flutter、Gradle 或完整 Android SDK。

配置文件：

```text
travel-planner/frontend/nitron.config.json
```

构建前先生成 APK 专用静态资源：

```bash
cd travel-planner/frontend
npm ci
npm run build:apk
```

然后使用 Node 18+、Java 8+ 和 [Nitron](https://www.npmjs.com/package/nitron) 打包：

```bash
npx --yes nitron@2.0.2 build
# 输出 dist/app.apk
```

当前交付物由该命令构建后复制到 `travel-planner/release/`。`build:apk` 使用 `.env.apk` 的 `VITE_DEMO_MODE=true`，所以 APK 是离线优先的；未来若有已部署的 HTTPS FastAPI 服务，可在专门发布配置中明确设置 `VITE_API_BASE_URL`。

## Key 的正确边界

截图中存在两个不同平台的 Key，不能混用：

| Key 类型 | 使用位置 | 是否应写入源码 / Vue bundle |
|---|---|---:|
| **Web 服务 Key** | FastAPI `AMAP_WEB_SERVICE_KEY`，用于 POI、地理编码、距离矩阵 | **否** |
| **Android 平台 Key** | 原生 Android AMap SDK 的 `AndroidManifest.xml` | **否**；只在原生构建时注入 |
| **JS API Key** | 浏览器的高德 JS API 2.0 | 只能作为受 Referer 限制的构建变量 |

因此，截图里的 Web 服务 Key 不会被放入 APK；Android Key 也不能直接作为 WebView 的 JS Key 使用。这样做会泄露服务端能力或导致高德鉴权失败。

## 原生高德地图 APK（生产建议）

要在 Android 真机内使用用户提供的 **Android 平台 Key** 和原生高德底图，请使用 Capacitor 原生工程：

```text
travel-planner/frontend/android/
```

关键实现：

- `src/components/MapCanvas.vue`：Android 上检测 Capacitor、展示高德隐私同意卡、同意后创建原生 `MapView`；
- `android/app/build.gradle`：从 `AMAP_ANDROID_KEY` 或不提交的 `local.properties` 读取 Key；
- `android/app/src/main/AndroidManifest.xml`：使用 `${AMAP_ANDROID_KEY}` placeholder；
- `@snewbie/capacitor-amap`：高德 Android 地图 SDK bridge；
- `.env.apk`：构建离线优先的 UI bundle。

### 高德控制台必须绑定

原生地图工程的 application ID 是：

```text
com.xingji.travel
```

请在高德控制台为 Android Key 配置：

1. 包名 `com.xingji.travel`；
2. 用于签名 APK 的证书 SHA1；
3. Android 地图 SDK 服务。

包名或 SHA1 不匹配时，应用仍会保留完整的路线 UI 和离线地图预览，但原生底图会鉴权失败。

### 原生 AMap 本地构建

要求：Node 22、JDK 17、Android SDK（platform 33+ / build-tools 33.0.2）。

```bash
cd travel-planner/frontend
npm ci
export AMAP_ANDROID_KEY='你的 Android 平台 Key'
npm run mobile:sync
cd android
./gradlew assembleDebug
# 输出：app/build/outputs/apk/debug/app-debug.apk
```

仓库还提供 CI 模板：

```text
travel-planner/deploy/build-native-amap-apk.yml.example
```

将其复制到拥有 GitHub Actions workflow 权限的仓库后，配置 Actions Secret `AMAP_ANDROID_KEY`。它不会把 Key 写进日志或源码。

## 隐私与降级

高德 Android SDK 必须先完成隐私披露/同意再创建地图。Capacitor 版本会在用户点选“同意并开启”后调用 `AMap.updatePrivacyShow/Agree`。若网络、Key 绑定或 SDK 初始化失败，软件自动保留路线规划和离线预览，不会阻断用户编辑行程。

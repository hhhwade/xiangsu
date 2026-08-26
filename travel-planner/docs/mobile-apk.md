# Android APK 打包与高德 Key 说明

本次交付包含两条移动端路径：

1. **已交付 APK 路径（Flutter 壳）**：`app/` 将 Vue 旅行规划 UI 打入本地 WebView；内置离线候选池、路线卡片、拖拽、时间线与地图预览，因此不依赖公网后端也可安装体验。
2. **原生高德地图路径（Capacitor）**：`travel-planner/frontend/android/` 集成了高德 Android SDK bridge；Android Key 仅在 Gradle 构建时注入，Android 真机可显示原生 MapView，并在 Web 层叠加路线颜色、序号与详情卡。

## Key 的正确边界

截图中存在两个不同平台的 Key，不能混用：

| Key 类型 | 使用位置 | 是否应写入源码 / Vue bundle |
|---|---|---:|
| **Web 服务 Key** | FastAPI `AMAP_WEB_SERVICE_KEY`，用于 POI、地理编码、距离矩阵 | **否** |
| **Android 平台 Key** | 原生 Android AMap SDK 的 `AndroidManifest.xml` | **否**；构建时注入，最终 APK 的 Manifest 含该 Key 属 SDK 正常行为 |

因此 Web 服务 Key 不会被放入 APK。Android Key 也绝不提交到 Git、`.env` 或 TypeScript 源码，而是由 Gradle 读取 `AMAP_ANDROID_KEY`。

## 已交付 APK：Flutter 壳

根目录已有 GitHub Actions 工作流 `.github/workflows/build_apk.yml`，它会构建当前的 `app/` 目录。该目录已从原入口改为 **行迹智能旅行** APK，并加载：

```text
app/assets/travel_web/
```

其中是以 `VITE_DEMO_MODE=true` 构建的相对路径 Vue 静态资源，适配 Android WebView 本地加载。

### 下载步骤

1. GitHub → **Actions** → **Build Android APK**；
2. 运行或打开当前分支对应的 workflow run；
3. 下载 artifact `ai-beauty-app-debug`；
4. 将其中的 `app-debug.apk` 安装到 Android 手机。

虽然历史 artifact 名称仍是 `ai-beauty-app-debug`，APK 内实际应用标题和包名已经是：

```text
行迹智能旅行
com.xingji.travel
```

这是可安装的 arm64 debug APK。首次从浏览器/文件管理器安装时，需要在 Android 系统中允许该来源“安装未知应用”。

## 原生高德地图 APK（生产建议）

Capacitor Android 工程位于：

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

仓库还提供了可复制到拥有 workflow 权限仓库的 CI 模板：

```text
travel-planner/deploy/build-native-amap-apk.yml.example
```

该模板读取 GitHub Actions Secret `AMAP_ANDROID_KEY`，不会把 Key 写进日志或源码。

### 本地构建命令

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

生产环境请使用自己持久保存的 release keystore，并把 release SHA1 加入高德 Android Key 白名单。绝不能提交 keystore 或 Key 到仓库。

## 隐私与降级

高德 Android SDK 必须先完成隐私披露/同意再创建地图。Capacitor 版本会在用户点选“同意并开启”后调用 `AMap.updatePrivacyShow/Agree`。若网络、Key 绑定或 SDK 初始化失败，软件自动保留路线规划和离线预览，不会阻断用户编辑行程。

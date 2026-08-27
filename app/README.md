# 行迹智能旅行 APK 壳

此 Flutter 工程是 Android APK 的交付入口。它使用 `webview_flutter` 加载打包进应用资源的 Vue 旅行路线规划界面：

```text
assets/travel_web/
```

- 离线优先：资源由 `travel-planner/frontend/.env.apk` 以 `VITE_DEMO_MODE=true` 构建，首次打开不依赖 `localhost`、后端或浏览器。
- 原生外壳：处理启动页、返回导航、WebView 错误兜底，以及 Android APK 打包。
- 真正的高德 Android SDK 集成与 Key 注入方案在 [`../travel-planner/docs/mobile-apk.md`](../travel-planner/docs/mobile-apk.md)。

## 构建

```bash
flutter pub get
flutter build apk --debug --target-platform android-arm64
```

APK 输出：

```text
build/app/outputs/flutter-apk/app-debug.apk
```

根目录 GitHub Actions 的 **Build Android APK** workflow 会执行同样的构建。

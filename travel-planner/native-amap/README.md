# 原生高德地图宿主

`MainActivity.java` 是 APK 中的原生 Android 双栏宿主：

- 横屏左侧：Vue 旅游路线表单、日期 Tab、景点顺序和时间线；
- 横屏右侧：高德 Android `MapView`；
- `web/index.html`：为 `file:///android_asset` 设计的无模块路线面板，保证左栏在 Android WebView 内不会空白；
- `XingjiNativeMap` JavaScript bridge：前端生成/切换/拖拽路线后，向原生地图发送景点坐标、日期颜色和顺序；
- 原生层绘制 Marker、按日期配色的 Polyline，并自动缩放到全部景点范围。

## 安全约束

高德 Android Key 不在此目录、Git 或前端 Bundle 中。构建流程仅从环境变量读取：

```bash
export AMAP_ANDROID_KEY='你的 Android 平台 Key'
```

最终 AndroidManifest 使用：

```xml
<meta-data android:name="com.amap.api.v2.apikey" android:value="${AMAP_ANDROID_KEY}" />
```

当前已交付的原生地图 APK 使用包名 `com.xingji.travel` 和 debug 证书 SHA1。生产发布必须使用自有 release keystore，重新绑定高德控制台的 SHA1 后重签名。

> AMap SDK 二进制及原生 `.so` 不提交到仓库；它们应从高德官方 SDK 或合规依赖源在受控构建环境中获取。

## 受控构建

`build-native-amap-apk.sh` 是不含 Key 的构建脚本。它要求通过环境变量提供 SDK 二进制和构建工具路径：

```bash
export AMAP_ANDROID_KEY='Android 平台 Key'
export AMAP_SDK_JAR=/secure/sdk/AMap3DMap.jar
export AMAP_ARM64_SO=/secure/sdk/arm64-v8a/libAMapSDK_MAP.so
export AMAP_ARMV7_SO=/secure/sdk/armeabi-v7a/libAMapSDK_MAP.so
export ANDROID_JAR=/secure/android-sdk/platforms/android-34/android.jar
export AAPT2=/secure/android-sdk/build-tools/34.0.0/aapt2
export DX_JAR=/secure/android-tools/dx.jar
export APK_SIGNER_JAR=/secure/android-tools/apk-signer.jar
export JAVA_HOME=/path/to/jdk17
bash build-native-amap-apk.sh
```

这些路径及 Android Key 都不应提交到仓库。

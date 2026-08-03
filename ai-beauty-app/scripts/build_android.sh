#!/usr/bin/env bash
# Android 打包：debug APK（快测） / release APK / AAB（Play 渠道）
# 用法:
#   bash scripts/build_android.sh debug|apk|aab
# 前置:
#   1. 本机安装 Flutter SDK (stable, >=3.24) 与 JDK 17
#      brew install flutter  /  见 https://docs.flutter.dev/get-started/install
#   2. cd app && flutter pub get
#   3. release 包需先生成签名:
#        keytool -genkey -v -keystore app/android/app/key.jks -keyalg RSA -keysize 2048 -validity 10000 -alias beauty
#        cp app/android/key.properties.example app/android/key.properties  # 填口令
#      并在 app/android/app/build.gradle.kts 的 android {} 内加入签名块（部署与打包手册 §5.1 有成品代码）
set -euo pipefail
MODE="${1:-apk}"
cd "$(dirname "$0")/../app"

flutter pub get

case "$MODE" in
  debug)
    flutter build apk --debug
    OUT="build/app/outputs/flutter-apk/app-debug.apk"
    ;;
  apk)
    if [ ! -f android/key.properties ]; then
      echo "⚠️ 缺 android/key.properties（签名配置）。见 scripts/build_android.sh 顶部注释第 3 点。"
      echo "    先出 debug 包测试: bash scripts/build_android.sh debug"
      exit 1
    fi
    flutter build apk --release
    OUT="build/app/outputs/flutter-apk/app-release.apk"
    ;;
  aab)
    if [ ! -f android/key.properties ]; then
      echo "⚠️ 缺 android/key.properties（签名配置）。"
      exit 1
    fi
    flutter build appbundle --release
    OUT="build/app/outputs/bundle/release/app-release.aab"
    ;;
  *)
    echo "usage: $0 debug|apk|aab"; exit 1;;
esac

echo "✅ 打包完成: app/$OUT"

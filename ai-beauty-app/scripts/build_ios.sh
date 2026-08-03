#!/usr/bin/env bash
# iOS 打包：生成 IPA（开发签名可用本机 Apple 账号；上架/TF 需 99$/年开发者账号）
# 用法（macOS + Xcode 环境）:
#   bash scripts/build_ios.sh
# 前置:
#   1. Xcode 15+，CocoaPods: sudo gem install cocoapods
#   2. 在 Xcode 打开 app/ios/Runner.xcworkspace:
#      - Signing & Capabilities: 勾选 Automatically manage signing，选你的 Team
#      - Bundle ID 改成唯一（如 com.yourname.beauty）
#   3. 把 app/ios/ExportOptions.plist 中的 YOUR_TEAM_ID 改成你的 Team ID
set -euo pipefail
cd "$(dirname "$0")/../app"

flutter pub get

echo "==> flutter build ipa （自动 archive + export）"
flutter build ipa --export-options-plist=ios/ExportOptions.plist

echo ""
echo "✅ IPA 输出目录: app/build/ios/ipa/"
ls -lh build/ios/ipa/ || true
echo ""
echo "下一步（按需）:"
echo "  • 装到自己手机: Xcode → Devices and Simulators → 拖动 .ipa"
echo "  • 发 TestFlight: xcrun altool --upload-app 或 Xcode Organizer → Distribute App"

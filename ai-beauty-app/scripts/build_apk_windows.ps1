<#
  AI 美颜修图 — Windows 一键打包 debug APK
  用法：把 ai-beauty-app 整个文件夹放到任意位置，右键用 PowerShell 运行本脚本：
      powershell -ExecutionPolicy Bypass -File scripts\build_apk_windows.ps1
  无需管理员、无需装 Android Studio（自动下载便携 JDK17 + Flutter + Android SDK 命令行工具）
  全程约 20-30 分钟（大头是下载）；完成后提示 APK 路径，传到手机即装。
#>
$ErrorActionPreference = 'Stop'
$ProgressPreference    = 'SilentlyContinue'   # 关闭进度条，IWR 提速 10 倍

$BuildRoot = "$env:USERPROFILE\.beauty-sdk"
$JdkDir    = "$BuildRoot\jdk"
$FlDir     = "$BuildRoot\flutter"
$SdkDir    = "$BuildRoot\android-sdk"
$ProjDir   = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)   # 工程根（scripts 的上一级）
$AppDir    = Join-Path $ProjDir 'app'

function Note($m) { Write-Host "`n==> $m" -ForegroundColor Cyan }

New-Item -Force -ItemType Directory $BuildRoot, $JdkDir, "$SdkDir\cmdline-tools" | Out-Null

# ---------- 1) JDK 17（便携解压，不动系统环境） ----------
if (-not (Test-Path "$JdkDir\bin\java.exe")) {
    Note "下载 JDK 17 (Temurin, ~190MB)"
    $f = "$BuildRoot\jdk.zip"
    Invoke-WebRequest -Uri 'https://api.adoptium.net/v3/binary/latest/17/ga/windows/x64/jdk/hotspot/normal/eclipse' -OutFile $f
    tar -xf $f -C "$BuildRoot\jdk-tmp"
    New-Item -Force -ItemType Directory $JdkDir | Out-Null
    Copy-Item "$BuildRoot\jdk-tmp\jdk-*\*" -Destination $JdkDir -Recurse
    Remove-Item $f, "$BuildRoot\jdk-tmp" -Recurse -Force
} else { Note "JDK 已就绪" }

# ---------- 2) Flutter SDK ----------
if (-not (Test-Path "$FlDir\bin\flutter.bat")) {
    Note "下载 Flutter stable (~1.5GB，慢属正常)"
    $f = "$BuildRoot\flutter.zip"
    Invoke-WebRequest -Uri 'https://storage.googleapis.com/flutter_infra_release/releases/stable/windows/flutter_windows_3.44.8-stable.zip' -OutFile $f
    tar -xf $f -C $BuildRoot      # 解压出 flutter\ 目录
    Remove-Item $f -Force
} else { Note "Flutter 已就绪" }

# ---------- 3) Android SDK 命令行工具 ----------
$SdkMgr = "$SdkDir\cmdline-tools\latest\bin\sdkmanager.bat"
if (-not (Test-Path $SdkMgr)) {
    Note "下载 Android 命令行工具 (~130MB)"
    $f = "$BuildRoot\ct.zip"
    Invoke-WebRequest -Uri 'https://dl.google.com/android/repository/commandlinetools-win-11076708_latest.zip' -OutFile $f
    tar -xf $f -C "$SdkDir\cmdline-tools"
    Move-Item "$SdkDir\cmdline-tools\cmdline-tools" "$SdkDir\cmdline-tools\latest"
    Remove-Item $f -Force
} else { Note "SDK 工具已就绪" }

# ---------- 4) 环境变量（仅本会话生效） ----------
$env:JAVA_HOME    = $JdkDir
$env:ANDROID_HOME = $SdkDir
$env:ANDROID_SDK_ROOT = $SdkDir
$env:Path = "$JdkDir\bin;$FlDir\bin;$SdkDir\cmdline-tools\latest\bin;$SdkDir\platform-tools;$env:Path"

# ---------- 5) SDK 组件 + 协议 ----------
Note "接受协议 + 安装 platform/build-tools (首次约 2-5 分钟)"
1..30 | ForEach-Object { 'y' } | & $SdkMgr --licenses | Out-Null
1..30 | ForEach-Object { 'y' } | & $SdkMgr 'platform-tools' 'platforms;android-35' 'build-tools;34.0.0' | Out-Null

# ---------- 6) Flutter 配置 + 构建 ----------
Note "flutter doctor（忽略 Android Studio 未安装的提示）"
& "$FlDir\bin\flutter" config --android-sdk $SdkDir --no-analytics | Out-Null
& "$FlDir\bin\flutter" doctor

Push-Location $AppDir
Note "pub get"
& "$FlDir\bin\flutter" pub get
Note "开始打包 APK（首次约 5-15 分钟）"
& "$FlDir\bin\flutter" build apk --debug --target-platform android-arm64
Pop-Location

$Apk = "$AppDir\build\app\outputs\flutter-apk\app-debug.apk"
if (Test-Path $Apk) {
    Note "✅ 成功！APK 位置：$Apk"
    explorer (Split-Path $Apk)   # 自动打开所在文件夹，拖到 QQ/网盘发手机即可
} else {
    Write-Host "未找到 APK，请把上面报错截图发我" -ForegroundColor Red
    exit 1
}

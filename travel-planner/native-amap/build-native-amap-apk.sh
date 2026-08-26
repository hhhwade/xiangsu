#!/usr/bin/env bash
# Build the native AMap split-screen APK without committing either an AMap key or
# proprietary SDK binaries. See README.md in this directory for required inputs.
set -euo pipefail

: "${AMAP_ANDROID_KEY:?Set the Android-platform AMap key in the environment}"
: "${AMAP_SDK_JAR:?Path to AMap3DMap Android SDK JAR}"
: "${AMAP_SEARCH_JAR:?Path to AMap Search Android SDK JAR}"
: "${AMAP_ARM64_SO:?Path to arm64-v8a libAMapSDK_MAP*.so}"
: "${AMAP_ARMV7_SO:?Path to armeabi-v7a libAMapSDK_MAP*.so}"
: "${ANDROID_JAR:?Path to Android platform android.jar}"
: "${AAPT2:?Path to aapt2 binary}"
: "${DX_JAR:?Path to a Java dx/D8-compatible dex compiler JAR}"
: "${APK_SIGNER_JAR:?Path to an APK signing tool JAR}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
WEB_DIR="${NATIVE_AMAP_WEB_DIR:-$SCRIPT_DIR/web}"
FRONTEND_DIR="$REPO_ROOT/travel-planner/frontend"
OUT_DIR="${NATIVE_AMAP_BUILD_DIR:-$REPO_ROOT/travel-planner/release/.native-amap-build}"
OUTPUT_APK="${NATIVE_AMAP_OUTPUT:-$REPO_ROOT/travel-planner/release/xingji-smart-travel-amap.apk}"
JAVA_BIN="${JAVA_HOME:+$JAVA_HOME/bin/}java"
# The temporary manifest contains the Android SDK key. Remove it automatically
# unless an explicitly private build directory was requested for troubleshooting.
if [[ "${KEEP_NATIVE_AMAP_BUILD:-false}" != "true" ]]; then
  trap 'rm -rf "$OUT_DIR"' EXIT
fi
JAVAC_BIN="${JAVA_HOME:+$JAVA_HOME/bin/}javac"

command -v "$JAVA_BIN" >/dev/null
command -v "$JAVAC_BIN" >/dev/null
command -v zip >/dev/null
command -v unzip >/dev/null

# The native host intentionally uses a plain ES5/HTML route panel. Unlike a Vite
# module bundle, it is reliable under file:///android_asset on old and new WebViews.
test -f "$WEB_DIR/index.html"

rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR/classes" "$OUT_DIR/apk/res/values" "$OUT_DIR/apk/assets/www" \
  "$OUT_DIR/apk/lib/arm64-v8a" "$OUT_DIR/apk/lib/armeabi-v7a"

"$JAVAC_BIN" -encoding UTF-8 -source 8 -target 8 \
  -bootclasspath "$ANDROID_JAR" \
  -classpath "$AMAP_SDK_JAR:$AMAP_SEARCH_JAR" \
  -d "$OUT_DIR/classes" "$SCRIPT_DIR/MainActivity.java"

"$JAVA_BIN" -cp "$DX_JAR" com.android.dx.command.Main \
  --dex --output="$OUT_DIR/apk/classes.dex" "$OUT_DIR/classes" "$AMAP_SDK_JAR" "$AMAP_SEARCH_JAR"

cp -R "$FRONTEND_DIR/android/app/src/main/res"/mipmap-* "$OUT_DIR/apk/res/" 2>/dev/null || true
cat > "$OUT_DIR/apk/res/values/strings.xml" <<'EOF'
<resources><string name="app_name">行迹智能旅行</string></resources>
EOF
cat > "$OUT_DIR/apk/res/values/colors.xml" <<'EOF'
<resources><color name="ic_launcher_background">#143031</color></resources>
EOF
cat > "$OUT_DIR/apk/res/values/styles.xml" <<'EOF'
<resources><style name="AppTheme" parent="android:style/Theme.Material.Light.NoActionBar"><item name="android:fontFamily">sans</item><item name="android:colorAccent">#D46F3F</item></style></resources>
EOF
cat > "$OUT_DIR/AndroidManifest.xml" <<EOF
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.xingji.travel" android:versionCode="10101" android:versionName="1.1.1">
 <uses-sdk android:minSdkVersion="21" android:targetSdkVersion="34" />
 <uses-permission android:name="android.permission.INTERNET" />
 <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
 <uses-permission android:name="android.permission.ACCESS_WIFI_STATE" />
 <uses-permission android:name="android.permission.CHANGE_WIFI_STATE" />
 <application android:label="@string/app_name" android:icon="@mipmap/ic_launcher" android:theme="@style/AppTheme" android:hardwareAccelerated="true" android:usesCleartextTraffic="false">
  <meta-data android:name="com.amap.api.v2.apikey" android:value="${AMAP_ANDROID_KEY}" />
  <activity android:name="com.xingji.travel.MainActivity" android:exported="true" android:screenOrientation="portrait" android:configChanges="orientation|keyboardHidden|keyboard|screenSize|smallestScreenSize|uiMode">
   <intent-filter><action android:name="android.intent.action.MAIN" /><category android:name="android.intent.category.LAUNCHER" /></intent-filter>
  </activity>
 </application>
</manifest>
EOF

"$AAPT2" compile --dir "$OUT_DIR/apk/res" -o "$OUT_DIR/compiled.zip"
"$AAPT2" link "$OUT_DIR/compiled.zip" --manifest "$OUT_DIR/AndroidManifest.xml" -I "$ANDROID_JAR" -o "$OUT_DIR/resources.apk"
unzip -qo "$OUT_DIR/resources.apk" -d "$OUT_DIR/apk"

cp -R "$WEB_DIR/." "$OUT_DIR/apk/assets/www/"
mkdir -p "$OUT_DIR/amap-assets"
unzip -qo "$AMAP_SDK_JAR" 'assets/*' -d "$OUT_DIR/amap-assets"
cp -R "$OUT_DIR/amap-assets/assets/." "$OUT_DIR/apk/assets/"
cp "$AMAP_ARM64_SO" "$OUT_DIR/apk/lib/arm64-v8a/"
cp "$AMAP_ARMV7_SO" "$OUT_DIR/apk/lib/armeabi-v7a/"

rm -rf "$OUT_DIR/apk/META-INF"
(
  cd "$OUT_DIR/apk"
  zip -qr -0 "$OUT_DIR/unsigned.apk" . -x 'META-INF/*'
)
mkdir -p "$OUT_DIR/signed"
SIGN_ARGS=(--apks "$OUT_DIR/unsigned.apk" --out "$OUT_DIR/signed" --allowResign)
# Release signing is opt-in. CI/local callers pass these values from a secret store;
# debug signing remains available only for developer preview builds.
if [[ -n "${NATIVE_AMAP_KEYSTORE:-}" ]]; then
  : "${NATIVE_AMAP_KEY_ALIAS:?Set the release keystore alias}"
  : "${NATIVE_AMAP_STORE_PASSWORD:?Set the release keystore password}"
  : "${NATIVE_AMAP_KEY_PASSWORD:?Set the release key password}"
  SIGN_ARGS+=(--ks "$NATIVE_AMAP_KEYSTORE" --ksAlias "$NATIVE_AMAP_KEY_ALIAS" --ksPass "$NATIVE_AMAP_STORE_PASSWORD" --ksKeyPass "$NATIVE_AMAP_KEY_PASSWORD")
fi
"$JAVA_BIN" -jar "$APK_SIGNER_JAR" "${SIGN_ARGS[@]}" >/dev/null
cp "$(find "$OUT_DIR/signed" -type f -name '*.apk' | head -1)" "$OUTPUT_APK"
echo "Built native AMap APK: $OUTPUT_APK"

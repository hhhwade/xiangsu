import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  return {
    // A local Flutter WebView loads APK assets from a file URL, so its chunk URLs
    // must be relative. Browser/Capacitor builds retain the root-relative default.
    base: mode === 'apk' ? './' : '/',
    plugins: [vue()],
    server: {
      host: '0.0.0.0',
      port: 5173,
      // Arena preview hosts are intentionally accepted during development.
      allowedHosts: true,
      proxy: {
        '/api': {
          // This is a Vite-server hop, not a browser-facing localhost URL.
          target: env.VITE_API_PROXY_TARGET || 'http://127.0.0.1:8000',
          changeOrigin: true,
        },
      },
    },
  }
})

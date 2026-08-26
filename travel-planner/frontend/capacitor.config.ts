import type { CapacitorConfig } from '@capacitor/cli'

/**
 * Android packaging deliberately uses a same-origin, bundled build. The application
 * can plan with its offline candidate pool before a hosted FastAPI endpoint is set.
 */
const config: CapacitorConfig = {
  appId: 'com.xingji.travel',
  appName: '行迹智能旅行',
  webDir: 'dist',
  android: {
    backgroundColor: '#F5F4EF',
  },
}

export default config

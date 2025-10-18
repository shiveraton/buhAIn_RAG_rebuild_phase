import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.baybayin.learningapp',
  appName: 'buhAIn',
  webDir: 'www',
  server: {
    allowNavigation: ['*']
  },
  android: {
    allowMixedContent: true,
    captureInput: true
  },
  plugins: {
    CapacitorHttp: {
      enabled: true
    }
  }
};

export default config;

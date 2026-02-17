import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';
import pkg from './package.json';

export default defineConfig({
  plugins: [react()],
  define: {
    __APP_VERSION__: JSON.stringify(pkg.version),
    __GIT_SHA__: JSON.stringify(process.env.GIT_SHA || 'dev'),
    __BUILD_DATE__: JSON.stringify(process.env.BUILD_DATE || 'unknown'),
  },
  server: {
    open: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  publicDir: 'public',
  build: {
    assetsDir: 'assets'
  },
  resolve: {
    alias: {
      '@images': resolve(__dirname, './public/images')
    }
  }
});

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

export default defineConfig({
  plugins: [react()],
  server: {
    open: true, // Automatically open browser
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

import path from 'node:path';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Single FastAPI backend (:8002). In dev we proxy /api so the browser talks to
// one origin (Vite on :3000) with no hardcoded backend hostnames or CORS.
export default defineConfig(() => ({
  // nginx serves the build from the web root, so assets live at '/'.
  base: '/',
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8002',
        changeOrigin: true,
        // SSE: don't buffer the streamed response.
        configure: (proxy) => {
          proxy.on('proxyRes', (proxyRes) => {
            proxyRes.headers['cache-control'] = 'no-cache';
          });
        },
      },
    },
  },
  build: {
    outDir: 'build',
    emptyOutDir: true,
  },
}));

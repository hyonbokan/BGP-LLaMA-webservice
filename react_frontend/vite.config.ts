import path from 'node:path';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// The Django backend (:8001) and FastAPI agent (:8002) run separately.
// In dev we proxy so the browser talks to a single origin (Vite on :3000) —
// this keeps session cookies / CSRF same-origin without CORS gymnastics and
// means no hardcoded backend hostnames leak into the app.
export default defineConfig(({ command }) => ({
  // In a production build, assets are emitted under /static/ so Django's
  // STATIC_URL serves them; the dev server stays at the root.
  base: command === 'build' ? '/static/' : '/',
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': { target: 'http://localhost:8001', changeOrigin: true },
      '/agent': {
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
  // Django serves the production bundle from this directory (see project_1/settings).
  build: {
    outDir: 'build',
    emptyOutDir: true,
  },
}));

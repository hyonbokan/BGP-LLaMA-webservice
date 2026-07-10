// Central runtime config. In dev, leave API_BASE empty so requests go to the
// Vite dev-server proxy (same origin → /api, see vite.config.ts). Override via
// .env only when pointing at a non-proxied backend:
//
//   VITE_API_URL=http://localhost:8002

const stripTrailingSlash = (s: string) => s.replace(/\/$/, '');

/** Base for the API. Empty string → same-origin (proxied) `/api`. */
export const API_BASE = stripTrailingSlash(import.meta.env.VITE_API_URL ?? '');

/** Full URL to an API endpoint under `/api/`. */
export const apiUrl = (path: string) => `${API_BASE}/api/${path.replace(/^\//, '')}`;

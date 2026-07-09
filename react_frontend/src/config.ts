// Central runtime config. In dev, leave these empty so requests go to the Vite
// dev-server proxy (same origin → /api and /agent, see vite.config.ts). Override
// via .env only when pointing at a non-proxied backend.
//
//   VITE_API_URL=http://localhost:8001   VITE_AGENT_URL=http://localhost:8002

const stripTrailingSlash = (s: string) => s.replace(/\/$/, '');

/** Base for the Django REST API. Empty string → same-origin (proxied) `/api`. */
export const API_BASE = stripTrailingSlash(import.meta.env.VITE_API_URL ?? '');

/** Base for the FastAPI SSE agent. Empty string → same-origin (proxied) `/agent`. */
export const AGENT_BASE = stripTrailingSlash(import.meta.env.VITE_AGENT_URL ?? '');

/** Full URL to the REST API root (always ends without a trailing slash). */
export const apiUrl = (path: string) => `${API_BASE}/api/${path.replace(/^\//, '')}`;

/** Full URL to a FastAPI agent endpoint. */
export const agentUrl = (path: string) => `${AGENT_BASE}/agent/${path.replace(/^\//, '')}`;

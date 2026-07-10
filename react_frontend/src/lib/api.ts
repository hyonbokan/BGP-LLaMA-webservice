import axios from 'axios';
import { API_BASE } from '@/config';

// Same-origin in dev (Vite proxy rewrites /api -> :8002). API_BASE is only set
// when talking to a remote backend. The API is currently open (no auth/CSRF).
export const api = axios.create({
  baseURL: `${API_BASE}/api/`,
  headers: {
    'Content-Type': 'application/json',
    'X-Requested-With': 'XMLHttpRequest',
  },
});

import axios from 'axios';
import Cookies from 'js-cookie';
import { API_BASE } from '@/config';

// Same-origin in dev (Vite proxy rewrites /api -> :8001), so cookies and CSRF
// "just work" without CORS. API_BASE is only set when talking to a remote backend.
export const api = axios.create({
  baseURL: `${API_BASE}/api/`,
  headers: {
    'Content-Type': 'application/json',
    'X-Requested-With': 'XMLHttpRequest',
  },
  withCredentials: true,
});

// Django expects the CSRF token echoed back in a header on unsafe requests.
api.interceptors.request.use((config) => {
  const token = Cookies.get('csrftoken');
  if (token) {
    config.headers['X-CSRFToken'] = token;
  }
  return config;
});

/** Prime the CSRF cookie. Call once on app mount. */
export async function fetchCsrfToken(): Promise<void> {
  try {
    await api.get('get_csrf_token/');
  } catch (error) {
    console.error('Error fetching CSRF token:', error);
  }
}

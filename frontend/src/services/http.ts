import { API_BASE_URL } from '../shared/config';
import { getToken, isTokenExpired, logout } from './authService';

export async function authFetch(path: string, options: RequestInit = {}) {
  const token = getToken();
  if (!token || isTokenExpired()) {
    logout();
    throw new Error('Sesión expirada. Inicia sesión nuevamente.');
  }
  const headers = new Headers(options.headers || {});
  headers.set('Authorization', `Bearer ${token}`);
  const res = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
  if (res.status === 401) {
    logout();
    throw new Error('No autorizado. Inicia sesión nuevamente.');
  }
  return res;
}
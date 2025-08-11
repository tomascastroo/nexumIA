import { API_BASE_URL } from '../shared/config';

export function getToken(): string | null {
  return localStorage.getItem('token');
}

export function getTokenExpiry(): number | null {
  const val = localStorage.getItem('expires_at');
  return val ? Number(val) : null;
}

export function isTokenExpired(): boolean {
  const exp = getTokenExpiry();
  if (!exp) return false;
  const now = Math.floor(Date.now() / 1000);
  return now >= exp;
}

export async function loginUser(email: string, password: string) {
  const res = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Error de autenticación");
  }
  const { access_token, token_type, expires_at } = await res.json();
  localStorage.setItem('token', access_token);
  localStorage.setItem('token_type', token_type);
  localStorage.setItem('expires_at', String(expires_at));
  return { access_token, token_type, expires_at };
}

export async function registerUser(email: string, password: string) {
  const res = await fetch(`${API_BASE_URL}/api/v1/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Error de registro");
  }
  return res.json();
}

export function logout() {
  localStorage.removeItem('token');
  localStorage.removeItem('token_type');
  localStorage.removeItem('expires_at');
} 
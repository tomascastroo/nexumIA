const API_URL = "http://localhost:8000"; // Cambia si tu backend está en otro puerto

export async function loginUser(email: string, password: string) {
  const res = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const data = await res.json();
    throw new Error(data.detail || "Error de autenticación");
  }
  const { access_token, token_type, expires_at } = await res.json();
  localStorage.setItem('token', access_token);
  localStorage.setItem('token_type', token_type);
  localStorage.setItem('expires_at', expires_at.toString()); // Store expiration as string
  return { access_token, token_type, expires_at };
}

export async function registerUser(email: string, password: string) {
  const res = await fetch(`${API_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const data = await res.json();
    throw new Error(data.detail || "Error de registro");
  }
  return res.json();
}

export function logout() {
  localStorage.removeItem('token');
  localStorage.removeItem('token_type');
  localStorage.removeItem('expires_at');
} 
const API_URL = "http://localhost:8000";

export interface Debtor {
  id?: number;
  dni?: string;
  name: string;
  email?: string;
  phone: string;
  amount?: number;
  status?: string;
}

export async function fetchDebtors(): Promise<Debtor[]> {
  const token = localStorage.getItem('token');
  const res = await fetch(`${API_URL}/debtor`, {
    headers: token ? { 'Authorization': `Bearer ${token}` } : {},
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: 'Error desconocido al obtener deudores.' }));
    throw new Error(errorData.detail || 'No se pudieron obtener los deudores');
  }
  return res.json();
}

export async function createDebtor(debtor: Omit<Debtor, 'id'>): Promise<Debtor> {
  const token = localStorage.getItem('token');
  const res = await fetch(`${API_URL}/debtor`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(debtor),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: 'Error desconocido en la creación.' }));
    throw new Error(errorData.detail || 'No se pudo crear el deudor.');
  }
  return res.json();
}

export async function updateDebtor(id: number, debtor: Omit<Debtor, 'id' | 'dni'>): Promise<Debtor> {
  if (typeof id !== 'number' || isNaN(id)) {
    throw new Error('ID de deudor inválido para actualización.');
  }
  const token = localStorage.getItem('token');
  const res = await fetch(`${API_URL}/debtor/${id}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(debtor),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: 'Error desconocido en la actualización.' }));
    throw new Error(errorData.detail || 'No se pudo actualizar el deudor.');
  }
  return res.json();
}

export async function deleteDebtor(id: number): Promise<void> {
  if (typeof id !== 'number' || isNaN(id)) {
    throw new Error('ID de deudor inválido para eliminación.');
  }
  const token = localStorage.getItem('token');
  const res = await fetch(`${API_URL}/debtor/${id}`, {
    method: 'DELETE',
    headers: token ? { 'Authorization': `Bearer ${token}` } : {},
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: 'Error desconocido en la eliminación.' }));
    throw new Error(errorData.detail || 'No se pudo eliminar el deudor.');
  }
} 
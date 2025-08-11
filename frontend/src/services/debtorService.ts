import { API_BASE_URL } from '../shared/config';
import { getToken } from './authService';

export interface Debtor {
  id?: number;
  phone: string;
  state: string;
  debtor_dataset_id?: number;
  custom_data: { [key: string]: any };
}

export interface DebtorFilters {
  search?: string; // Generic search term for all fields
  state?: string; // Filter by state
  min_amount?: number; // Filter by minimum debt amount
  max_amount?: number; // Filter by maximum debt amount
  // Add more filter fields as needed for custom data
  [key: string]: any; // Allow for dynamic custom data filters
}

export interface DebtorSort {
  field: string; // The field to sort by (e.g., 'phone', 'name', 'deuda')
  direction: 'asc' | 'desc'; // Sort direction
}

export async function fetchDebtors(datasetId: number, filters?: DebtorFilters, sort?: DebtorSort): Promise<Debtor[]> {
  const token = getToken();
  let url = `${API_BASE_URL}/debtor?dataset_id=${datasetId}`;

  // Add filters to URL
  if (filters) {
    for (const key in filters) {
      if (filters.hasOwnProperty(key) && filters[key] !== undefined && filters[key] !== null && filters[key] !== '') {
        url += `&${key}=${encodeURIComponent(filters[key])}`;
      }
    }
  }

  // Add sort to URL
  if (sort) {
    url += `&sort_by=${encodeURIComponent(sort.field)}&sort_direction=${encodeURIComponent(sort.direction)}`;
  }

  console.log('debtorService - Fetching debtors from URL:', url);

  const res = await fetch(url, {
    headers: token ? { 'Authorization': `Bearer ${token}` } : {},
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: 'Error desconocido al obtener deudores.' }));
    console.error('debtorService - Error response:', errorData);
    throw new Error(errorData.detail || 'No se pudieron obtener los deudores');
  }
  return res.json();
}

export async function createDebtor(debtor: Omit<Debtor, 'id'>): Promise<Debtor> {
  const token = getToken();
  const res = await fetch(`${API_BASE_URL}/debtor`, {
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
  const token = getToken();
  const res = await fetch(`${API_BASE_URL}/debtor/${id}`, {
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

export async function deleteDebtor(id: number, datasetId: number): Promise<void> {
  if (typeof id !== 'number' || isNaN(id)) {
    throw new Error('ID de deudor inválido para eliminación.');
  }
  if (typeof datasetId !== 'number' || isNaN(datasetId)) {
    throw new Error('ID de dataset inválido para eliminación.');
  }
  const token = getToken();
  const res = await fetch(`${API_BASE_URL}/debtor/${id}?dataset_id=${datasetId}`, {
    method: 'DELETE',
    headers: token ? { 'Authorization': `Bearer ${token}` } : {},
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: 'Error desconocido en la eliminación.' }));
    throw new Error(errorData.detail || 'No se pudo eliminar el deudor.');
  }
} 
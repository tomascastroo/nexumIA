import { authFetch } from './http';

export interface Debtor {
  id?: number;
  phone: string;
  state: string;
  debtor_dataset_id?: number;
  custom_data: { [key: string]: any };
}

export interface DebtorFilters {
  search?: string;
  state?: string;
  min_amount?: number;
  max_amount?: number;
  [key: string]: any;
}

export interface DebtorSort {
  field: string;
  direction: 'asc' | 'desc';
}

export async function fetchDebtors(datasetId: number, filters?: DebtorFilters, sort?: DebtorSort): Promise<Debtor[]> {
  let url = `/api/v1/debtor?dataset_id=${datasetId}`;
  if (filters) {
    for (const key in filters) {
      if (Object.prototype.hasOwnProperty.call(filters, key)) {
        const val = (filters as any)[key];
        if (val !== undefined && val !== null && val !== '') {
          url += `&${encodeURIComponent(key)}=${encodeURIComponent(val)}`;
        }
      }
    }
  }
  if (sort) {
    url += `&sort_by=${encodeURIComponent(sort.field)}&sort_direction=${encodeURIComponent(sort.direction)}`;
  }
  const res = await authFetch(url);
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: 'Error desconocido al obtener deudores.' }));
    throw new Error(errorData.detail || 'No se pudieron obtener los deudores');
  }
  return res.json();
}

export async function createDebtor(debtor: Omit<Debtor, 'id'>): Promise<Debtor> {
  const res = await authFetch(`/api/v1/debtor`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(debtor),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: 'Error desconocido en la creación.' }));
    throw new Error(errorData.detail || 'No se pudo crear el deudor.');
  }
  return res.json();
}

export async function updateDebtor(id: number, debtor: Omit<Debtor, 'id' | 'dni'>): Promise<Debtor> {
  const res = await authFetch(`/api/v1/debtor/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(debtor),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: 'Error desconocido en la actualización.' }));
    throw new Error(errorData.detail || 'No se pudo actualizar el deudor.');
  }
  return res.json();
}

export async function deleteDebtor(id: number, datasetId: number): Promise<void> {
  const res = await authFetch(`/api/v1/debtor/${id}?dataset_id=${datasetId}`, { method: 'DELETE' });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: 'Error desconocido en la eliminación.' }));
    throw new Error(errorData.detail || 'No se pudo eliminar el deudor.');
  }
} 
import { API_BASE_URL } from '../shared/config';
import { getToken } from './authService';

export interface DebtorDataset {
  id: number;
  name: string;
  created_at: string;
  updated_at: string;
}

export interface DebtorCustomField {
  id: number;
  name: string;
  field_type: string;
  debtor_dataset_id: number;
}

export const getDebtorDatasets = async (): Promise<DebtorDataset[]> => {
  const token = getToken();
  const response = await fetch(`${API_BASE_URL}/debtor-datasets/`, {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error(`Error fetching debtor datasets: ${response.statusText}`);
  }
  return response.json();
};

export const uploadDebtorDataset = async (file: File, datasetName: string): Promise<any> => {
  const token = getToken();
  const formData = new FormData();
  formData.append('file', file);
  formData.append('dataset_name', datasetName);

  const response = await fetch(`${API_BASE_URL}/debtor-datasets/upload-dataset/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Error uploading debtor dataset: ${response.statusText}`);
  }
  return response.json();
};

export const getDebtorCustomFields = async (datasetId: number): Promise<DebtorCustomField[]> => {
  const token = getToken();
  const response = await fetch(`${API_BASE_URL}/debtor-datasets/${datasetId}/custom-fields/`, {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  });

  if (response.status === 404) {
    console.warn(`No custom fields found for dataset ID ${datasetId}. Returning empty array.`);
    return [];
  }

  if (!response.ok) {
    throw new Error(`Error fetching debtor custom fields: ${response.statusText}`);
  }
  return response.json();
}; 
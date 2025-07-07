import axios from 'axios';

export interface Strategy {
  id: number;
  name: string;
  initial_prompt: string;
  rules_by_state: {
    [key: string]: {
      prompt: string;
      condicionales: Array<{
        si: string;
        accion: string;
      }>;
    };
  } | null;
  created_at: string;
  updated_at: string;
}

const API_URL = "http://localhost:8000";

console.log('API_URL:', API_URL);

export const createStrategy = async (strategyData: any, token: string) => {
  try {
    const response = await axios.post<Strategy>(`${API_URL}/strategy/`, strategyData, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    return response.data;
  } catch (error) {
    console.error('Error creating strategy:', error);
    throw error;
  }
};

export const getStrategies = async (token: string): Promise<Strategy[]> => {
  try {
    const response = await axios.get<Strategy[]>(`${API_URL}/strategy/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching strategies:', error);
    throw error;
  }
};

export const updateStrategy = async (strategyId: number, strategyData: any, token: string) => {
  try {
    const response = await axios.post<Strategy>(`${API_URL}/strategy/${strategyId}`, strategyData, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    return response.data;
  } catch (error) {
    console.error('Error updating strategy:', error);
    throw error;
  }
};

export const deleteStrategy = async (strategyId: number, token: string) => {
  try {
    const response = await axios.delete<Strategy>(`${API_URL}/strategy/${strategyId}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    return response.data;
  } catch (error) {
    console.error('Error deleting strategy:', error);
    throw error;
  }
}; 
import axios from 'axios';
import { API_BASE_URL } from '../shared/config';

export interface Campaign {
  id: number;
  name: string;
  bot_id: number;
  strategy_id: number;
  status?: string;
  start_date?: string; // or Date, depending on your backend
  end_date?: string;
  created_at?: string;
  updated_at?: string;
  debtor_dataset_id: number;
  // Optionally, add these if you use them in the frontend:
  // strategy?: any;
  // bot?: any;
  // debtor_dataset?: any;
}

export interface Bot {
  id: number;
  name: string;
}

export const getBots = async (token: string): Promise<Bot[]> => {
  const response = await axios.get<Bot[]>(`${API_BASE_URL}/bot/`, {
    headers: { 'Authorization': `Bearer ${token}` },
  });
  return response.data;
};

export const getCampaigns = async (token: string): Promise<Campaign[]> => {
  const response = await axios.get<Campaign[]>(`${API_BASE_URL}/campaign/`, {
    headers: { 'Authorization': `Bearer ${token}` },
  });
  return response.data;
};

export const createCampaign = async (campaignData: any, token: string) => {
  const response = await axios.post(`${API_BASE_URL}/campaign/`, campaignData, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });
  return response.data;
};

export const updateCampaign = async (campaignId: number, campaignData: any, token: string) => {
  const response = await axios.put(`${API_BASE_URL}/campaign/${campaignId}`, campaignData, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });
  return response.data;
};

export const deleteCampaign = async (campaignId: number, token: string) => {
  const response = await axios.delete(`${API_BASE_URL}/campaign/${campaignId}`, {
    headers: { 'Authorization': `Bearer ${token}` },
  });
  return response.data;
};

export const launchCampaign = async (campaignId: number, token: string) => {
  const response = await axios.get(`${API_BASE_URL}/campaign/throw-campaign/${campaignId}`, {
    headers: { 'Authorization': `Bearer ${token}` },
  });
  return response.data;
}; 
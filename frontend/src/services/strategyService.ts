import axios from 'axios';

const API_URL = "http://localhost:8000";

export interface ConditionalRule {
  condition: string;
  response: string;
  retry_in_days?: number | null;
  close_case?: boolean;
  escalate_to_human?: boolean;
}

export interface AdvancedConditionalRule {
  name: string;
  conditions: {
    operator: 'AND' | 'OR';
    conditions: any[];
  };
  response: string;
  retry_in_days?: number;
  escalate_to_human: boolean;
  close_case: boolean;
  priority: number;
}

export interface EvaluableRule {
  name: string;
  condition: string;
  response: string;
  strict: boolean;
  priority: number;
  enabled: boolean;
}

export interface StateRules {
  prompt?: string;
  rules: ConditionalRule[];
  advanced_rules: AdvancedConditionalRule[];
}

export interface Strategy {
  id: number;
  name: string;
  initial_prompt: string;
  rules_by_state: {
    [state: string]: StateRules;
  };
  evaluable_rules: EvaluableRule[];
  strict_mode: boolean;
  fallback_prompt: string;
  created_at: string;
  updated_at: string;
}

export const createStrategy = async (strategyData: any, token: string) => {
  const response = await axios.post<Strategy>(`${API_URL}/api/v1/strategy/`, strategyData, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });
  return response.data;
};

export const getStrategies = async (token: string): Promise<Strategy[]> => {
  const response = await axios.get<Strategy[]>(`${API_URL}/api/v1/strategy/`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  return response.data;
};

export const updateStrategy = async (strategyId: number, strategyData: any, token: string) => {
  const response = await axios.post<Strategy>(`${API_URL}/api/v1/strategy/${strategyId}`, strategyData, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });
  return response.data;
};

export const deleteStrategy = async (strategyId: number, token: string) => {
  const response = await axios.delete<Strategy>(`${API_URL}/strategies/${strategyId}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  return response.data;
}; 
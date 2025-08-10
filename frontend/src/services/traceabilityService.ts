import axios from 'axios';

const API_URL = 'http://localhost:8000';

export interface TraceDecision {
  timestamp: string;
  debtor_id: number;
  strategy_id: number;
  user_message: string;
  llm_response: string;
  decision: {
    action_type: string;
    action_description: string;
    triggered_rule: any;
    applicable_rules: any[];
    restrictions: string[];
    allowed_responses: string[];
    reasoning: string;
    fallback_reason?: string;
  };
  context: any;
  metadata: any;
}

export interface TraceAnalytics {
  total_decisions: number;
  action_types: Record<string, number>;
  fallback_rate: number;
  strict_rules_usage: number;
  average_rules_per_decision: number;
  recent_decisions: TraceDecision[];
}

export const getDecisionHistory = async (
  token: string,
  params: { debtor_id?: number; strategy_id?: number; limit?: number }
): Promise<TraceDecision[]> => {
  const res = await axios.get(`${API_URL}/traceability/decisions`, {
    headers: { Authorization: `Bearer ${token}` },
    params,
  });
  return (res.data as { data: TraceDecision[] }).data;
};

export const getDecisionAnalytics = async (
  token: string,
  params: { debtor_id?: number; strategy_id?: number }
): Promise<TraceAnalytics> => {
  const res = await axios.get(`${API_URL}/api/v1/traceability/analytics`, {
    headers: { Authorization: `Bearer ${token}` },
    params,
  });
  return (res.data as { data: TraceAnalytics }).data;
}; 
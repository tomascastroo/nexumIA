import { authFetch } from './http';

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

function toQuery(params?: Record<string, any>): string {
  if (!params) return '';
  const usp = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') usp.append(k, String(v));
  });
  const s = usp.toString();
  return s ? `?${s}` : '';
}

export const getDecisionHistory = async (
  params?: { debtor_id?: number; strategy_id?: number; limit?: number }
): Promise<TraceDecision[]> => {
  const res = await authFetch(`/traceability/decisions${toQuery(params)}`, { method: 'GET' });
  if (!res.ok) throw new Error('Error obteniendo historial');
  return (await res.json() as { data: TraceDecision[] }).data;
};

export const getDecisionAnalytics = async (
  params?: { debtor_id?: number; strategy_id?: number }
): Promise<TraceAnalytics> => {
  const res = await authFetch(`/api/v1/traceability/analytics${toQuery(params)}`, { method: 'GET' });
  if (!res.ok) throw new Error('Error obteniendo analíticas');
  return (await res.json() as { data: TraceAnalytics }).data;
}; 
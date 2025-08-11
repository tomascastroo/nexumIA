import React, { useEffect, useState } from 'react';
import { getDecisionHistory, getDecisionAnalytics, TraceDecision, TraceAnalytics } from '../services/traceabilityService';

interface Props {
  strategyId: number;
}

const StrategyTraceability: React.FC<Props> = ({ strategyId }) => {
  const [decisions, setDecisions] = useState<TraceDecision[]>([]);
  const [analytics, setAnalytics] = useState<TraceAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    setLoading(true);
    Promise.all([
      getDecisionHistory({ strategy_id: strategyId, limit: 20 }),
      getDecisionAnalytics({ strategy_id: strategyId })
    ])
      .then(([decisions, analytics]) => {
        setDecisions(decisions);
        setAnalytics(analytics);
        setLoading(false);
      })
      .catch((e) => {
        setError(e.message);
        setLoading(false);
      });
  }, [strategyId]);

  if (loading) return <div className="text-gray-500">Cargando trazabilidad...</div>;
  if (error) return <div className="text-red-500">Error: {error}</div>;

  return (
    <div className="mt-8">
      <h3 className="text-lg font-bold mb-2">Trazabilidad de Decisiones</h3>
      {analytics && (
        <div className="mb-4 flex flex-wrap gap-4">
          <div className="bg-blue-100 text-blue-800 px-3 py-1 rounded">Total decisiones: {analytics.total_decisions}</div>
          <div className="bg-green-100 text-green-800 px-3 py-1 rounded">Fallback: {analytics.fallback_rate.toFixed(1)}%</div>
          <div className="bg-yellow-100 text-yellow-800 px-3 py-1 rounded">Reglas estrictas: {analytics.strict_rules_usage.toFixed(1)}%</div>
          <div className="bg-gray-100 text-gray-800 px-3 py-1 rounded">Prom. reglas/decisión: {analytics.average_rules_per_decision.toFixed(2)}</div>
        </div>
      )}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 text-xs">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-2 py-2 text-left">Fecha</th>
              <th className="px-2 py-2 text-left">Mensaje</th>
              <th className="px-2 py-2 text-left">Regla activada</th>
              <th className="px-2 py-2 text-left">Acción</th>
              <th className="px-2 py-2 text-left">Respuesta LLM</th>
              <th className="px-2 py-2 text-left">Razonamiento</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-100">
            {decisions.map((d, i) => (
              <tr key={i}>
                <td className="px-2 py-1 whitespace-nowrap">{new Date(d.timestamp).toLocaleString()}</td>
                <td className="px-2 py-1 max-w-xs truncate" title={d.user_message}>{d.user_message}</td>
                <td className="px-2 py-1">{d.decision.triggered_rule?.name || '-'}</td>
                <td className="px-2 py-1">{d.decision.action_description}</td>
                <td className="px-2 py-1 max-w-xs truncate" title={d.llm_response}>{d.llm_response}</td>
                <td className="px-2 py-1 max-w-xs truncate" title={d.decision.reasoning}>{d.decision.reasoning}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {decisions.length === 0 && <div className="text-gray-400 mt-4">No hay decisiones registradas aún.</div>}
    </div>
  );
};

export default StrategyTraceability; 
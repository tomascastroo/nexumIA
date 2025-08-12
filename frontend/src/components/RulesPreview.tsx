import React from 'react';
import { AdvancedConditionalRule } from './ConditionBuilder';

interface RulesPreviewProps {
  rules: AdvancedConditionalRule[];
  onEditRule: (index: number) => void;
  onDeleteRule: (index: number) => void;
  onDuplicateRule: (index: number) => void;
}

const RulesPreview: React.FC<RulesPreviewProps> = ({
  rules,
  onEditRule,
  onDeleteRule,
  onDuplicateRule
}) => {
  const formatCondition = (condition: any): string => {
    if (condition.field && condition.operator && condition.value !== undefined) {
      const fieldLabels: { [key: string]: string } = {
        deuda: 'Deuda',
        ciudad: 'Ciudad',
        sexo: 'Sexo',
        edad: 'Edad',
        fecha_registro: 'Fecha de Registro',
        estado_actual: 'Estado Actual'
      };

      const operatorLabels: { [key: string]: string } = {
        '>': 'mayor que',
        '<': 'menor que',
        '=': 'igual a',
        '>=': 'mayor o igual que',
        '<=': 'menor o igual que',
        'igual a': 'igual a',
        'diferente de': 'diferente de',
        'antes de': 'antes de',
        'después de': 'después de'
      };

      return `${fieldLabels[condition.field] || condition.field} ${operatorLabels[condition.operator] || condition.operator} ${condition.value}`;
    }
    return 'Condición inválida';
  };

  const formatConditions = (conditions: any[]): string => {
    if (!conditions || conditions.length === 0) {
      return 'Sin condiciones';
    }

    return conditions.map(formatCondition).join(' Y ');
  };

  const getActionText = (rule: AdvancedConditionalRule): string => {
    const actions = [];
    
    if (rule.retry_in_days) {
      actions.push(`Reintentar en ${rule.retry_in_days} días`);
    }
    
    if (rule.escalate_to_human) {
      actions.push('Escalar a humano');
    }
    
    if (rule.close_case) {
      actions.push('Cerrar caso');
    }
    
    return actions.length > 0 ? actions.join(', ') : 'Sin acciones';
  };

  if (rules.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <p>No hay reglas configuradas</p>
        <p className="text-sm">Agrega reglas para personalizar las respuestas del bot</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200">
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-medium text-gray-900">Vista Previa de Reglas</h3>
        <p className="text-sm text-gray-500 mt-1">
          {rules.length} regla{rules.length !== 1 ? 's' : ''} configurada{rules.length !== 1 ? 's' : ''}
        </p>
      </div>
      
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Prioridad
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Nombre
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Condiciones
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Respuesta
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Acciones
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Acciones
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {rules
              .sort((a, b) => a.priority - b.priority)
              .map((rule, index) => (
                <tr key={index} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      {rule.priority}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {rule.name}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900 max-w-xs">
                    <div className="truncate" title={formatConditions(rule.conditions.conditions)}>
                      {formatConditions(rule.conditions.conditions)}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900 max-w-xs">
                    <div className="truncate" title={rule.response}>
                      {rule.response}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {getActionText(rule)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => onEditRule(index)}
                        className="text-blue-600 hover:text-blue-900 text-xs"
                      >
                        Editar
                      </button>
                      <button
                        onClick={() => onDuplicateRule(index)}
                        className="text-green-600 hover:text-green-900 text-xs"
                      >
                        Duplicar
                      </button>
                      <button
                        onClick={() => onDeleteRule(index)}
                        className="text-red-600 hover:text-red-900 text-xs"
                      >
                        Eliminar
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default RulesPreview; 
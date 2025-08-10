import React, { useState } from 'react';

export interface Condition {
  field: 'deuda' | 'ciudad' | 'sexo' | 'edad' | 'fecha_registro' | 'estado_actual';
  operator: string;
  value: any;
}

export interface ConditionGroup {
  operator: 'AND' | 'OR';
  conditions: (Condition | ConditionGroup)[];
}

export interface AdvancedConditionalRule {
  name: string;
  conditions: ConditionGroup;
  response: string;
  retry_in_days?: number;
  escalate_to_human: boolean;
  close_case: boolean;
  priority: number;
}

interface ConditionBuilderProps {
  rule: AdvancedConditionalRule;
  onRuleChange: (rule: AdvancedConditionalRule) => void;
  onDelete: () => void;
  onDuplicate: () => void;
}

const fieldOptions = [
  { value: 'deuda', label: 'Deuda' },
  { value: 'ciudad', label: 'Ciudad' },
  { value: 'sexo', label: 'Sexo' },
  { value: 'edad', label: 'Edad' },
  { value: 'fecha_registro', label: 'Fecha de Registro' },
  { value: 'estado_actual', label: 'Estado Actual' }
];

const operatorOptions = {
  deuda: [
    { value: '>', label: 'Mayor que' },
    { value: '<', label: 'Menor que' },
    { value: '=', label: 'Igual a' },
    { value: '>=', label: 'Mayor o igual que' },
    { value: '<=', label: 'Menor o igual que' }
  ],
  ciudad: [
    { value: 'igual a', label: 'Igual a' },
    { value: 'diferente de', label: 'Diferente de' }
  ],
  sexo: [
    { value: 'igual a', label: 'Igual a' },
    { value: 'diferente de', label: 'Diferente de' }
  ],
  edad: [
    { value: '>', label: 'Mayor que' },
    { value: '<', label: 'Menor que' },
    { value: '=', label: 'Igual a' },
    { value: '>=', label: 'Mayor o igual que' },
    { value: '<=', label: 'Menor o igual que' }
  ],
  fecha_registro: [
    { value: 'antes de', label: 'Antes de' },
    { value: 'después de', label: 'Después de' }
  ],
  estado_actual: [
    { value: 'igual a', label: 'Igual a' },
    { value: 'diferente de', label: 'Diferente de' }
  ]
};

const ConditionBuilder: React.FC<ConditionBuilderProps> = ({
  rule,
  onRuleChange,
  onDelete,
  onDuplicate
}) => {
  const [isExpanded, setIsExpanded] = useState(true);

  const updateRule = (updates: Partial<AdvancedConditionalRule>) => {
    onRuleChange({ ...rule, ...updates });
  };

  const addCondition = () => {
    const newCondition: Condition = {
      field: 'deuda',
      operator: '>',
      value: ''
    };
    
    const newConditions = [...rule.conditions.conditions, newCondition];
    updateRule({
      conditions: {
        ...rule.conditions,
        conditions: newConditions
      }
    });
  };

  const updateCondition = (index: number, condition: Condition) => {
    const newConditions = [...rule.conditions.conditions];
    newConditions[index] = condition;
    updateRule({
      conditions: {
        ...rule.conditions,
        conditions: newConditions
      }
    });
  };

  const removeCondition = (index: number) => {
    const newConditions = rule.conditions.conditions.filter((_, i) => i !== index);
    updateRule({
      conditions: {
        ...rule.conditions,
        conditions: newConditions
      }
    });
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 mb-4">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-gray-500 hover:text-gray-700"
          >
            {isExpanded ? '▼' : '▶'}
          </button>
          <input
            type="text"
            value={rule.name}
            onChange={(e) => updateRule({ name: e.target.value })}
            placeholder="Nombre de la regla"
            className="text-lg font-medium border-none focus:ring-0 p-0"
          />
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={onDuplicate}
            className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
          >
            Duplicar
          </button>
          <button
            onClick={onDelete}
            className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200"
          >
            Eliminar
          </button>
        </div>
      </div>

      {isExpanded && (
        <div className="space-y-4">
          {/* Condiciones */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <h4 className="font-medium text-gray-700">Condiciones</h4>
              <button
                onClick={addCondition}
                className="px-3 py-1 text-sm bg-green-100 text-green-700 rounded hover:bg-green-200"
              >
                + Agregar Condición
              </button>
            </div>
            
            <div className="mb-3">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Operador lógico
              </label>
              <select
                value={rule.conditions.operator}
                onChange={(e) => updateRule({
                  conditions: {
                    ...rule.conditions,
                    operator: e.target.value as 'AND' | 'OR'
                  }
                })}
                className="w-32 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="AND">Y (AND)</option>
                <option value="OR">O (OR)</option>
              </select>
            </div>

            <div className="space-y-2">
              {rule.conditions.conditions.map((condition, index) => (
                <div key={index} className="flex items-center space-x-2 p-3 bg-gray-50 rounded">
                  <select
                    value={(condition as Condition).field}
                    onChange={(e) => updateCondition(index, {
                      ...(condition as Condition),
                      field: e.target.value as any
                    })}
                    className="w-32 px-2 py-1 border border-gray-300 rounded text-sm"
                  >
                    {fieldOptions.map(option => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>

                  <select
                    value={(condition as Condition).operator}
                    onChange={(e) => updateCondition(index, {
                      ...(condition as Condition),
                      operator: e.target.value
                    })}
                    className="w-32 px-2 py-1 border border-gray-300 rounded text-sm"
                  >
                    {operatorOptions[(condition as Condition).field]?.map(option => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>

                  <input
                    type="number"
                    value={(condition as Condition).value || ''}
                    onChange={(e) => updateCondition(index, {
                      ...(condition as Condition),
                      value: e.target.value === '' ? '' : Number(e.target.value) || ''
                    })}
                    placeholder="Valor"
                    className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
                  />

                  <button
                    onClick={() => removeCondition(index)}
                    className="px-2 py-1 text-red-600 hover:text-red-800"
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Respuesta del bot */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Respuesta del bot
            </label>
            <textarea
              value={rule.response}
              onChange={(e) => updateRule({ response: e.target.value })}
              placeholder="Escribe la respuesta que el bot debe dar cuando se cumplan estas condiciones..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={3}
            />
          </div>

          {/* Acciones de seguimiento */}
          <div>
            <h4 className="font-medium text-gray-700 mb-2">Acciones de seguimiento</h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Reintentar en días
                </label>
                <input
                  type="number"
                  value={rule.retry_in_days || ''}
                  onChange={(e) => updateRule({ 
                    retry_in_days: e.target.value ? parseInt(e.target.value) || undefined : undefined 
                  })}
                  placeholder="Número de días"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  checked={rule.escalate_to_human}
                  onChange={(e) => updateRule({ escalate_to_human: e.target.checked })}
                  className="mr-2"
                />
                <label className="text-sm font-medium text-gray-700">
                  Escalar a humano
                </label>
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  checked={rule.close_case}
                  onChange={(e) => updateRule({ close_case: e.target.checked })}
                  className="mr-2"
                />
                <label className="text-sm font-medium text-gray-700">
                  Cerrar caso
                </label>
              </div>
            </div>
          </div>

          {/* Prioridad */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Prioridad
            </label>
            <input
              type="number"
              value={rule.priority || ''}
              onChange={(e) => updateRule({ 
                priority: e.target.value ? parseInt(e.target.value) || 1 : 1 
              })}
              min="1"
              className="w-32 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <p className="text-xs text-gray-500 mt-1">Menor número = mayor prioridad</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default ConditionBuilder; 
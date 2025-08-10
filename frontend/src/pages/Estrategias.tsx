import React, { useState, useEffect, useCallback } from 'react';
import { createStrategy, getStrategies, updateStrategy, deleteStrategy, Strategy, EvaluableRule } from '../services/strategyService';
import { useNavigate } from 'react-router-dom';
import ConditionBuilder, { AdvancedConditionalRule, ConditionGroup } from '../components/ConditionBuilder';
import RulesPreview from '../components/RulesPreview';
import StrategyTraceability from '../components/StrategyTraceability';

interface GlobalEvaluableRule extends AdvancedConditionalRule {
  strict: boolean;
  enabled: boolean;
}

interface FormState {
  name: string;
  initialPrompt: string;
  fallbackPrompt: string;
  strictMode: boolean;
  rulesByState: Strategy['rules_by_state'];
  evaluableRules: GlobalEvaluableRule[];
  activeTab: string;
  advancedRules: AdvancedConditionalRule[];
}

const DEFAULT_RULES_BY_STATE = {
  VERDE: { prompt: "", rules: [], advanced_rules: [] },
  AMARILLO: { prompt: "", rules: [], advanced_rules: [] },
  ROJO: { prompt: "", rules: [], advanced_rules: [] },
  GRIS: { prompt: "", rules: [], advanced_rules: [] },
};

const DEFAULT_FORM_STATE: FormState = {
  name: '',
  initialPrompt: '',
  fallbackPrompt: '',
  strictMode: false,
  rulesByState: DEFAULT_RULES_BY_STATE,
  evaluableRules: [],
  activeTab: 'VERDE',
  advancedRules: [],
};

const Estrategias: React.FC = () => {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [currentStrategy, setCurrentStrategy] = useState<Strategy | null>(null);
  const [formState, setFormState] = useState<FormState>(DEFAULT_FORM_STATE);
  const [modalLoading, setModalLoading] = useState(false);
  const [modalError, setModalError] = useState('');
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [toDelete, setToDelete] = useState<number | null>(null);

  const navigate = useNavigate();
  const token = localStorage.getItem('token');

  const states = ['VERDE', 'AMARILLO', 'ROJO', 'GRIS'];
  const stateColors = {
    VERDE: 'bg-green-100 text-green-800',
    AMARILLO: 'bg-yellow-100 text-yellow-800',
    ROJO: 'bg-red-100 text-red-800',
    GRIS: 'bg-gray-100 text-gray-800'
  };

  useEffect(() => {
    if (!token) {
      navigate('/login');
      return;
    }
    loadStrategies();
  }, [token, navigate]);

  const loadStrategies = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await getStrategies(token as string);
      setStrategies(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const conditionGroupToString = useCallback((group: ConditionGroup): string => {
    if (!group?.conditions?.length) return '';
    
    const conditions = group.conditions
      .map(cond => {
        if (!cond) return '';
        
        if ('operator' in cond) {
          const inner = conditionGroupToString(cond as ConditionGroup);
          return inner ? `(${inner})` : '';
        }
        
        const c = cond as any;
        if (!c.field || !c.operator) return '';
        
        if (typeof c.value === 'number' && !isNaN(c.value)) {
          return `${c.field} ${c.operator} ${c.value}`;
        }
        
        if (typeof c.value === 'string' && c.value.trim()) {
          return `${c.field} ${c.operator} '${c.value.trim()}'`;
        }
        
        return '';
      })
      .filter(Boolean);

    return conditions.length ? conditions.join(` ${group.operator} `) : '';
  }, []);

  const createDefaultConditionGroup = useCallback((): ConditionGroup => ({
    operator: 'AND',
    conditions: [{
      field: 'deuda',
      operator: '>',
      value: 0
    }]
  }), []);

  const normalizeConditionGroup = useCallback((conditions: any): ConditionGroup => {
    if (conditions && typeof conditions === 'object' && 'operator' in conditions && Array.isArray(conditions.conditions)) {
      return conditions;
    }
    
    if (conditions && typeof conditions === 'object' && 'field' in conditions && 'operator' in conditions) {
      return {
        operator: 'AND',
        conditions: [conditions]
      };
    }
    
    return createDefaultConditionGroup();
  }, [createDefaultConditionGroup]);

  const hasValidConditions = useCallback((rule: GlobalEvaluableRule): boolean => {
    // Si no hay condiciones, es inválida
    if (!rule.conditions) return false;
    
    const group = rule.conditions as ConditionGroup;
    if (!group?.conditions?.length) return false;

    // Verificar que al menos una condición sea válida
    return group.conditions.some(cond => {
      if (!cond) return false;
      
      // Si es una condición anidada (otro grupo)
      if ('operator' in cond && 'conditions' in cond) {
        return hasValidConditions({ ...rule, conditions: cond as ConditionGroup });
      }
      
      // Si es una condición simple
      const c = cond as any;
      if (!c.field || !c.operator) return false;
      
      // Validar el valor según el tipo
      if (c.value === null || c.value === undefined) return false;
      
      // Si es número, debe ser válido
      if (typeof c.value === 'number') {
        return !isNaN(c.value);
      }
      
      // Si es string, debe tener contenido
      if (typeof c.value === 'string') {
        return c.value.trim().length > 0;
      }
      
      // Para otros tipos, consideramos válido si existe
      return true;
    });
  }, []);

  const validateForm = useCallback((): { isValid: boolean; errors: string[] } => {
    const errors: string[] = [];
    
    if (!formState.name.trim()) {
      errors.push('El nombre de la estrategia es requerido');
    }
    
    // Solo validar reglas que tengan condiciones
    const invalidRules = formState.evaluableRules.filter(rule => {
      if (!rule.conditions) return true;
      const group = rule.conditions as ConditionGroup;
      if (!group?.conditions?.length) return true;
      
      // Si tiene al menos una condición, considerarla válida
      return false;
    });
    
    if (invalidRules.length > 0) {
      errors.push(`${invalidRules.length} regla(s) global(es) tienen condiciones inválidas`);
    }
    
    return { isValid: errors.length === 0, errors };
  }, [formState.name, formState.evaluableRules]);

  const handleCreateOrUpdate = async () => {
    if (!token) return;
    
    const validation = validateForm();
    if (!validation.isValid) {
      setModalError(validation.errors.join('. '));
      return;
    }

    setModalLoading(true);
    setModalError('');
    
    try {
      const updatedRulesByState = {
        ...formState.rulesByState,
        [formState.activeTab]: {
          ...formState.rulesByState[formState.activeTab],
          advanced_rules: formState.advancedRules
        }
      };

      const evaluableRules: EvaluableRule[] = formState.evaluableRules
        .map(rule => ({
          name: rule.name,
          condition: conditionGroupToString(rule.conditions),
          response: rule.response,
          strict: rule.strict,
          priority: rule.priority,
          enabled: rule.enabled
        }))
        .filter(rule => rule.condition.trim());

      const strategyData = {
        name: formState.name.trim(),
        initial_prompt: formState.initialPrompt,
        rules_by_state: updatedRulesByState,
        evaluable_rules: evaluableRules,
        strict_mode: formState.strictMode,
        fallback_prompt: formState.fallbackPrompt
      };

      if (currentStrategy) {
        await updateStrategy(currentStrategy.id, strategyData, token);
      } else {
        await createStrategy(strategyData, token);
      }
      
      resetForm();
      loadStrategies();
    } catch (e: any) {
      setModalError(e.message);
    } finally {
      setModalLoading(false);
    }
  };

  const resetForm = useCallback(() => {
    setModalOpen(false);
    setCurrentStrategy(null);
    setFormState(DEFAULT_FORM_STATE);
    setModalError('');
  }, []);

  const handleDeleteConfirm = async () => {
    if (!token || typeof toDelete !== 'number') return;
    
    setError('');
    try {
      await deleteStrategy(toDelete, token);
      setConfirmOpen(false);
      setToDelete(null);
      loadStrategies();
    } catch (e: any) {
      setError(e.message);
    }
  };

  const openCreateModal = useCallback(() => {
    setCurrentStrategy(null);
    setFormState(DEFAULT_FORM_STATE);
    setModalError('');
    setModalOpen(true);
  }, []);

  const openEditModal = useCallback((strategy: Strategy) => {
    setCurrentStrategy(strategy);
    
    const evaluableRules: GlobalEvaluableRule[] = (strategy.evaluable_rules || []).map((rule: any) => ({
      name: rule.name,
      conditions: normalizeConditionGroup(rule.conditions),
      response: rule.response || '',
      strict: rule.strict ?? true,
      enabled: rule.enabled ?? true,
      escalate_to_human: rule.escalate_to_human ?? false,
      close_case: rule.close_case ?? false,
      retry_in_days: rule.retry_in_days,
      priority: rule.priority || 1
    }));

    setFormState({
      name: strategy.name,
      initialPrompt: strategy.initial_prompt,
      fallbackPrompt: strategy.fallback_prompt || '',
      strictMode: strategy.strict_mode || false,
      rulesByState: strategy.rules_by_state || DEFAULT_RULES_BY_STATE,
      evaluableRules,
      activeTab: 'VERDE',
      advancedRules: strategy.rules_by_state?.VERDE?.advanced_rules || []
    });
    
    setModalError('');
    setModalOpen(true);
  }, [normalizeConditionGroup]);

  const openDeleteConfirm = useCallback((strategyId: number) => {
    setToDelete(strategyId);
    setConfirmOpen(true);
  }, []);

  const updateFormState = useCallback((updates: Partial<FormState>) => {
    setFormState(prev => ({ ...prev, ...updates }));
  }, []);

  const addAdvancedRule = useCallback(() => {
    const newRule: AdvancedConditionalRule = {
      name: `Nueva Regla ${formState.advancedRules.length + 1}`,
      conditions: createDefaultConditionGroup(),
      response: '',
      retry_in_days: undefined,
      escalate_to_human: false,
      close_case: false,
      priority: formState.advancedRules.length + 1
    };
    
    updateFormState({
      advancedRules: [...formState.advancedRules, newRule]
    });
  }, [formState.advancedRules.length, createDefaultConditionGroup, updateFormState]);

  const updateAdvancedRule = useCallback((index: number, rule: AdvancedConditionalRule) => {
    const newRules = [...formState.advancedRules];
    newRules[index] = rule;
    updateFormState({ advancedRules: newRules });
  }, [formState.advancedRules, updateFormState]);

  const deleteAdvancedRule = useCallback((index: number) => {
    updateFormState({
      advancedRules: formState.advancedRules.filter((_, i) => i !== index)
    });
  }, [formState.advancedRules, updateFormState]);

  const duplicateAdvancedRule = useCallback((index: number) => {
    const ruleToDuplicate = formState.advancedRules[index];
    const duplicatedRule: AdvancedConditionalRule = {
      ...ruleToDuplicate,
      name: `${ruleToDuplicate.name} (copia)`,
      priority: formState.advancedRules.length + 1
    };
    
    updateFormState({
      advancedRules: [...formState.advancedRules, duplicatedRule]
    });
  }, [formState.advancedRules, updateFormState]);

  const handleTabChange = useCallback((state: string) => {
    const updatedRulesByState = {
      ...formState.rulesByState,
      [formState.activeTab]: {
        ...formState.rulesByState[formState.activeTab],
        advanced_rules: formState.advancedRules
      }
    };

    const newStateRules = formState.rulesByState[state]?.advanced_rules || [];
    
    updateFormState({
      rulesByState: updatedRulesByState,
      activeTab: state,
      advancedRules: newStateRules
    });
  }, [formState.activeTab, formState.advancedRules, formState.rulesByState, updateFormState]);

  const addEvaluableRule = useCallback(() => {
    const newRule: GlobalEvaluableRule = {
      name: '',
      conditions: createDefaultConditionGroup(),
      response: '',
      strict: true,
      priority: formState.evaluableRules.length + 1,
      enabled: true,
      escalate_to_human: false,
      close_case: false,
      retry_in_days: undefined
    };
    
    updateFormState({
      evaluableRules: [...formState.evaluableRules, newRule]
    });
  }, [formState.evaluableRules.length, createDefaultConditionGroup, updateFormState]);

  const updateEvaluableRule = useCallback((index: number, updates: Partial<GlobalEvaluableRule>) => {
    const newRules = [...formState.evaluableRules];
    newRules[index] = { ...newRules[index], ...updates };
    updateFormState({ evaluableRules: newRules });
  }, [formState.evaluableRules, updateFormState]);

  const deleteEvaluableRule = useCallback((index: number) => {
    updateFormState({
      evaluableRules: formState.evaluableRules.filter((_, i) => i !== index)
    });
  }, [formState.evaluableRules, updateFormState]);

  const duplicateEvaluableRule = useCallback((index: number) => {
    const ruleToDuplicate = formState.evaluableRules[index];
    const duplicatedRule: GlobalEvaluableRule = {
      ...ruleToDuplicate,
      name: `${ruleToDuplicate.name} (copia)`,
      priority: formState.evaluableRules.length + 1
    };
    
    updateFormState({
      evaluableRules: [...formState.evaluableRules, duplicatedRule]
    });
  }, [formState.evaluableRules, updateFormState]);

  return (
    <div className="max-w-7xl mx-auto pt-28 px-4">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Estrategias</h1>
        <button
          onClick={openCreateModal}
          className="px-4 py-2 rounded-full bg-blue-600 text-white hover:bg-blue-700 text-sm font-medium"
        >
          Crear Nueva Estrategia
        </button>
      </div>

      {loading && <div className="text-center text-gray-500">Cargando estrategias...</div>}
      {error && <div className="text-center text-red-500">Error: {error}</div>}

      <div className="bg-white shadow overflow-hidden sm:rounded-lg">
        <div className="overflow-x-auto w-full">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Nombre
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Prompt Inicial
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Reglas por Estado
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Fecha Creación
                </th>
                <th scope="col" className="relative px-6 py-3">
                  <span className="sr-only">Acciones</span>
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {strategies.map((strategy) => (
                <tr key={strategy.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {strategy.name}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900 max-w-xs">
                    <div className="truncate" title={strategy.initial_prompt}>
                      {strategy.initial_prompt}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <div className="flex space-x-1">
                      {states.map((state) => {
                        const stateRules = strategy.rules_by_state?.[state];
                        const ruleCount = (stateRules?.rules?.length || 0) + (stateRules?.advanced_rules?.length || 0);
                        return (
                          <span
                            key={state}
                            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${stateColors[state as keyof typeof stateColors]}`}
                            title={`${state}: ${ruleCount} reglas`}
                          >
                            {ruleCount}
                          </span>
                        );
                      })}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(strategy.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button
                      onClick={() => openEditModal(strategy)}
                      className="text-blue-600 hover:text-blue-900 mr-4"
                    >
                      Editar
                    </button>
                    <button
                      onClick={() => openDeleteConfirm(strategy.id)}
                      className="text-red-600 hover:text-red-900"
                    >
                      Eliminar
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {modalOpen && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-6xl shadow-lg rounded-md bg-white">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-medium text-gray-900">
                {currentStrategy ? 'Editar Estrategia' : 'Crear Nueva Estrategia'}
              </h3>
              <button
                onClick={resetForm}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Nombre de la Estrategia
                  </label>
                  <input
                    type="text"
                    value={formState.name}
                    onChange={(e) => updateFormState({ name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Ej: Estrategia Agresiva"
                  />
                </div>
                <div className="flex items-center space-x-4 mt-4 md:mt-0">
                  <input
                    type="checkbox"
                    checked={formState.strictMode}
                    onChange={(e) => updateFormState({ strictMode: e.target.checked })}
                    className="mr-2"
                  />
                  <label className="text-sm font-medium text-gray-700">Modo Estricto Global</label>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Prompt Inicial
                </label>
                <textarea
                  value={formState.initialPrompt}
                  onChange={(e) => updateFormState({ initialPrompt: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={3}
                  placeholder="Escribe el mensaje inicial que el bot enviará al deudor..."
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Prompt Fallback (cuando no se cumplen reglas)
                </label>
                <textarea
                  value={formState.fallbackPrompt}
                  onChange={(e) => updateFormState({ fallbackPrompt: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={2}
                  placeholder="Mensaje a usar si no se cumple ninguna regla evaluable..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Reglas Evaluables Globales (se evalúan antes que las reglas por estado)
                </label>
                <div className="space-y-4 mb-4">
                  {formState.evaluableRules.map((rule, idx) => (
                    <div key={idx} className="border border-gray-200 rounded p-3 bg-gray-50 mb-2">
                      <div className="flex items-center mb-2">
                        <input
                          type="text"
                          value={rule.name}
                          onChange={(e) => updateEvaluableRule(idx, { name: e.target.value })}
                          placeholder="Nombre de la regla"
                          className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm mr-2"
                        />
                        <input
                          type="number"
                          value={rule.priority || ''}
                          min={1}
                          onChange={(e) => updateEvaluableRule(idx, { 
                            priority: e.target.value ? parseInt(e.target.value) || 1 : 1 
                          })}
                          className="w-20 px-2 py-1 border border-gray-300 rounded text-sm mr-2"
                        />
                        <label className="flex items-center mr-2">
                          <input
                            type="checkbox"
                            checked={rule.strict}
                            onChange={(e) => updateEvaluableRule(idx, { strict: e.target.checked })}
                            className="mr-1"
                          />
                          Estricta
                        </label>
                        <button
                          onClick={() => deleteEvaluableRule(idx)}
                          className="px-2 py-1 text-red-600 hover:text-red-800"
                        >
                          ✕
                        </button>
                      </div>
                      
                      <ConditionBuilder
                        rule={rule}
                        onRuleChange={(updatedRule) => updateEvaluableRule(idx, updatedRule)}
                        onDelete={() => deleteEvaluableRule(idx)}
                        onDuplicate={() => duplicateEvaluableRule(idx)}
                      />
                      
                      <div className="mt-2">
                        <label className="block text-xs font-medium text-gray-700 mb-1">Respuesta predefinida</label>
                        <input
                          type="text"
                          value={rule.response}
                          onChange={(e) => updateEvaluableRule(idx, { response: e.target.value })}
                          placeholder="Respuesta predefinida"
                          className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                        />
                      </div>
                    </div>
                  ))}
                  
                  <div className="flex gap-2">
                    <button
                      onClick={addEvaluableRule}
                      className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 text-sm font-medium"
                    >
                      + Agregar Regla Global
                    </button>
                    <button
                      onClick={() => {
                        const exampleRule: GlobalEvaluableRule = {
                          name: 'Descuento para deudas altas',
                          conditions: createDefaultConditionGroup(),
                          response: 'Te ofrezco un 15% de descuento en tu deuda de ${deuda}.',
                          strict: true,
                          priority: 1,
                          enabled: true,
                          escalate_to_human: false,
                          close_case: false,
                          retry_in_days: undefined
                        };
                        updateFormState({
                          evaluableRules: [...formState.evaluableRules, exampleRule]
                        });
                      }}
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm font-medium"
                    >
                      + Agregar Regla de Ejemplo
                    </button>
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Reglas por Estado
                </label>
                <div className="border-b border-gray-200">
                  <nav className="-mb-px flex space-x-8">
                    {states.map((state) => (
                      <button
                        key={state}
                        onClick={() => handleTabChange(state)}
                        className={`py-2 px-1 border-b-2 font-medium text-sm ${
                          formState.activeTab === state
                            ? 'border-blue-500 text-blue-600'
                            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                        }`}
                      >
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium mr-2 ${stateColors[state as keyof typeof stateColors]}`}>
                          {state}
                        </span>
                        {state}
                      </button>
                    ))}
                  </nav>
                </div>

                <div className="mt-6">
                  <div className="flex items-center justify-between mb-4">
                    <h4 className="text-lg font-medium text-gray-900">
                      Reglas para estado: {formState.activeTab}
                    </h4>
                    <button
                      onClick={addAdvancedRule}
                      className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 text-sm font-medium"
                    >
                      + Agregar Regla
                    </button>
                  </div>

                  <div className="space-y-4 mb-6">
                    {formState.advancedRules.map((rule, index) => (
                      <ConditionBuilder
                        key={index}
                        rule={rule}
                        onRuleChange={(updatedRule) => updateAdvancedRule(index, updatedRule)}
                        onDelete={() => deleteAdvancedRule(index)}
                        onDuplicate={() => duplicateAdvancedRule(index)}
                      />
                    ))}
                  </div>

                  <RulesPreview
                    rules={formState.advancedRules}
                    onEditRule={(index) => {
                      const ruleElement = document.querySelector(`[data-rule-index="${index}"]`);
                      ruleElement?.scrollIntoView({ behavior: 'smooth' });
                    }}
                    onDeleteRule={deleteAdvancedRule}
                    onDuplicateRule={duplicateAdvancedRule}
                  />
                </div>
              </div>
            </div>

            <div className="flex justify-end space-x-3 mt-6 pt-6 border-t border-gray-200">
              <button
                onClick={resetForm}
                className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Cancelar
              </button>
              <button
                onClick={handleCreateOrUpdate}
                disabled={modalLoading}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm font-medium disabled:opacity-50"
              >
                {modalLoading ? 'Guardando...' : (currentStrategy ? 'Actualizar' : 'Crear')}
              </button>
            </div>

            {modalError && (
              <div className="mt-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
                {modalError}
              </div>
            )}
          </div>
        </div>
      )}

      {confirmOpen && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3 text-center">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Confirmar eliminación
              </h3>
              <p className="text-sm text-gray-500 mb-6">
                ¿Estás seguro de que quieres eliminar esta estrategia? Esta acción no se puede deshacer.
              </p>
              <div className="flex justify-center space-x-3">
                <button
                  onClick={() => setConfirmOpen(false)}
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  Cancelar
                </button>
                <button
                  onClick={handleDeleteConfirm}
                  className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 text-sm font-medium"
                >
                  Eliminar
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
      {currentStrategy && (
        <StrategyTraceability strategyId={currentStrategy.id} />
      )}
    </div>
  );
};

export default Estrategias; 
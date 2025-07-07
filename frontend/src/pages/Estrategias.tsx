import React, { useState, useEffect } from 'react';
import { createStrategy, getStrategies, updateStrategy, deleteStrategy, Strategy } from '../services/strategyService';
import { useNavigate } from 'react-router-dom';
import ConditionalModal from '../components/ConditionalModal';

interface Conditional {
  si: string;
  accion: string;
}

const Estrategias: React.FC = () => {
  const DEFAULT_RULES_BY_STATE: NonNullable<Strategy['rules_by_state']> = {
    "VERDE": { prompt: "", condicionales: [] },
    "AMARILLO": { prompt: "", condicionales: [] },
    "ROJO": { prompt: "", condicionales: [] },
    "GRIS": { prompt: "", condicionales: [] },
  };

  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [currentStrategy, setCurrentStrategy] = useState<Strategy | null>(null);
  const [formName, setFormName] = useState('');
  const [formInitialPrompt, setFormInitialPrompt] = useState('');
  const [formRulesByState, setFormRulesByState] = useState<Strategy['rules_by_state']>(DEFAULT_RULES_BY_STATE);
  const [modalLoading, setModalLoading] = useState(false);
  const [modalError, setModalError] = useState('');
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [toDelete, setToDelete] = useState<number | null>(null);

  // State for ConditionalModal
  const [isConditionalModalOpen, setIsConditionalModalOpen] = useState(false);
  const [currentConditional, setCurrentConditional] = useState<Conditional | null>(null);
  const [editingStateKey, setEditingStateKey] = useState<string | null>(null);
  const [editingConditionalIndex, setEditingConditionalIndex] = useState<number | null>(null);

  const navigate = useNavigate();
  const token = localStorage.getItem('token');

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

  const handleCreateOrUpdate = async () => {
    if (!token) return;
    setModalLoading(true);
    setModalError('');
    try {
      const strategyData = {
        name: formName,
        initial_prompt: formInitialPrompt,
        rules_by_state: formRulesByState,
      };

      if (currentStrategy) {
        await updateStrategy(currentStrategy.id, strategyData, token);
      } else {
        await createStrategy(strategyData, token);
      }
      setModalOpen(false);
      setCurrentStrategy(null);
      setFormName('');
      setFormInitialPrompt('');
      setFormRulesByState(DEFAULT_RULES_BY_STATE);
      loadStrategies();
    } catch (e: any) {
      setModalError(e.message);
    } finally {
      setModalLoading(false);
    }
  };

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

  const openCreateModal = () => {
    setCurrentStrategy(null);
    setFormName('');
    setFormInitialPrompt('');
    setFormRulesByState(DEFAULT_RULES_BY_STATE);
    setModalError('');
    setModalOpen(true);
  };

  const openEditModal = (strategy: Strategy) => {
    setCurrentStrategy(strategy);
    setFormName(strategy.name);
    setFormInitialPrompt(strategy.initial_prompt);
    setFormRulesByState(strategy.rules_by_state);
    setModalError('');
    setModalOpen(true);
  };

  const openDeleteConfirm = (strategyId: number) => {
    setToDelete(strategyId);
    setConfirmOpen(true);
  };

  const openConditionalModal = (stateKey: string, conditional?: Conditional, index?: number) => {
    setEditingStateKey(stateKey);
    setCurrentConditional(conditional || null);
    setEditingConditionalIndex(typeof index === 'number' ? index : null);
    setIsConditionalModalOpen(true);
  };

  const closeConditionalModal = () => {
    setIsConditionalModalOpen(false);
    setEditingStateKey(null);
    setCurrentConditional(null);
    setEditingConditionalIndex(null);
  };

  const handleSaveConditional = (newConditional: Conditional) => {
    if (!editingStateKey) return;

    setFormRulesByState((prev) => {
      const currentRules = prev || {};
      const currentState = currentRules[editingStateKey] || { prompt: "", condicionales: [] };
      const newCondicionales = [...(currentState.condicionales || [])];

      if (typeof editingConditionalIndex === 'number' && editingConditionalIndex !== null) {
        // Editing existing conditional
        newCondicionales[editingConditionalIndex] = newConditional;
      } else {
        // Adding new conditional
        newCondicionales.push(newConditional);
      }

      return {
        ...currentRules,
        [editingStateKey]: {
          ...currentState,
          condicionales: newCondicionales,
        },
      } as typeof prev;
    });
    closeConditionalModal();
  };

  const handleDeleteConditional = (stateKey: string, indexToDelete: number) => {
    setFormRulesByState((prev) => {
      const currentRules = prev || {};
      const currentState = currentRules[stateKey] || { prompt: "", condicionales: [] };
      const newCondicionales = (currentState.condicionales || []).filter(
        (_: any, i: number) => i !== indexToDelete
      );

      return {
        ...currentRules,
        [stateKey]: {
          ...currentState,
          condicionales: newCondicionales,
        },
      } as typeof prev;
    });
  };

  return (
    <div className="max-w-5xl mx-auto pt-28 px-4">
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

      {!loading && !error && strategies.length === 0 && (
        <div className="text-center text-gray-500">No hay estrategias creadas.</div>
      )}

      {!loading && !error && strategies.length > 0 && (
        <div className="bg-white shadow-lg rounded-2xl p-6 mb-8">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nombre</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Prompt Inicial</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fecha Creación</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fecha Actualización</th>
                  <th className="relative px-6 py-3"><span className="sr-only">Acciones</span></th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {strategies.map((strategy) => (
                  <tr key={strategy.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{strategy.name}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 max-w-xs truncate">{strategy.initial_prompt}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{new Date(strategy.created_at).toLocaleDateString()}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{new Date(strategy.updated_at).toLocaleDateString()}</td>
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
      )}

      {/* Create/Edit Strategy Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/30">
          <div className="bg-white rounded-2xl shadow-lg p-8 w-full max-w-md flex flex-col relative max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex-shrink-0">
              {currentStrategy ? 'Editar Estrategia' : 'Crear Nueva Estrategia'}
            </h2>
            <form onSubmit={(e) => { e.preventDefault(); handleCreateOrUpdate(); }} className="flex flex-col gap-4 flex-grow">
              <div className="flex-grow pr-2">
                <div>
                  <label htmlFor="name" className="block text-sm font-medium text-gray-700">Nombre</label>
                  <input
                    type="text"
                    id="name"
                    value={formName}
                    onChange={(e) => setFormName(e.target.value)}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    required
                  />
                </div>
                <div>
                  <label htmlFor="initialPrompt" className="block text-sm font-medium text-gray-700">Prompt Inicial</label>
                  <textarea
                    id="initialPrompt"
                    rows={4}
                    value={formInitialPrompt}
                    onChange={(e) => setFormInitialPrompt(e.target.value)}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  ></textarea>
                </div>

                {/* Structured Rules by State Input */}
                <div className="space-y-8 mt-6">
                  <h3 className="text-lg font-medium text-gray-900">Reglas por Estado</h3>
                  {Object.keys(formRulesByState || {}).map((stateKey) => {
                    const textColorClass = {
                      "VERDE": "text-green-600",
                      "AMARILLO": "text-yellow-600",
                      "ROJO": "text-red-600",
                      "GRIS": "text-gray-600",
                    }[stateKey] || "text-gray-900";
                    return (
                      <div key={stateKey} className="rounded-lg p-4 space-y-4">
                        <h4 className={`text-md font-semibold mb-2 ${textColorClass}`}>{stateKey}</h4>
                        <div className="pb-4">
                          <label htmlFor={`${stateKey}-prompt`} className="block text-sm font-medium text-gray-700">Prompt para {stateKey}</label>
                          <textarea
                            id={`${stateKey}-prompt`}
                            rows={2}
                            value={formRulesByState?.[stateKey]?.prompt || ''}
                            onChange={(e) =>
                              setFormRulesByState((prev) => {
                                const currentRules = prev || {};
                                const currentState = currentRules[stateKey] || { prompt: "", condicionales: [] };

                                return {
                                  ...currentRules,
                                  [stateKey]: {
                                    ...currentState,
                                    prompt: e.target.value,
                                  },
                                } as typeof prev;
                              })
                            }
                            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                          ></textarea>
                        </div>

                        <h5 className="text-sm font-medium text-gray-700">Condicionales</h5>
                        <div className="space-y-2">
                        {(formRulesByState?.[stateKey]?.condicionales || []).map((conditional, index) => (
                          <div key={index} className="flex gap-2 items-center justify-between p-2 rounded-md">
                            <span className="text-sm text-gray-800 flex-grow">
                              <span className="font-semibold">Si:</span> {conditional.si} <br />
                              <span className="font-semibold">Acción:</span> {conditional.accion}
                            </span>
                            <div className="flex gap-2">
                              <button
                                type="button"
                                onClick={() => openConditionalModal(stateKey, conditional, index)}
                                className="p-1 rounded-full text-blue-600 hover:bg-blue-100"
                              >
                                <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" /></svg>
                              </button>
                              <button
                                type="button"
                                onClick={() => handleDeleteConditional(stateKey, index)}
                                className="p-1 rounded-full text-red-600 hover:bg-red-100"
                              >
                                <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                              </button>
                            </div>
                          </div>
                        ))}
                        </div>
                        <button
                          type="button"
                          onClick={() => openConditionalModal(stateKey)}
                          className="px-3 py-1 rounded-full bg-gray-100 text-gray-700 hover:bg-gray-200 text-sm"
                        >
                          + Añadir Condicional
                        </button>
                      </div>
                    );
                  })}
                </div>
              </div>
              <div className="flex justify-end gap-3 mt-4 flex-shrink-0">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="px-4 py-2 rounded-full border border-gray-200 text-gray-700 hover:bg-gray-100 text-sm font-medium"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-full bg-gray-100 text-gray-700 hover:bg-gray-200 border border-gray-200 text-sm font-medium"
                  disabled={modalLoading}
                >
                  {modalLoading ? 'Guardando...' : 'Guardar'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {confirmOpen && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/30">
          <div className="bg-white rounded-2xl shadow-lg p-8 w-full max-w-xs flex flex-col gap-4 relative">
            <div className="text-lg text-gray-900 text-center">¿Está seguro que desea eliminar esta estrategia?</div>
            <div className="flex gap-4 justify-center mt-2">
              <button onClick={() => setConfirmOpen(false)} className="px-4 py-2 rounded-full border border-gray-200 text-gray-700 hover:bg-gray-100">Cancelar</button>
              <button onClick={handleDeleteConfirm} className="px-4 py-2 rounded-full bg-red-600 text-white hover:bg-red-700">Eliminar</button>
            </div>
          </div>
        </div>
      )}

      <ConditionalModal
        isOpen={isConditionalModalOpen}
        onClose={closeConditionalModal}
        onSave={handleSaveConditional}
        initialConditional={currentConditional || undefined}
      />
    </div>
  );
};

export default Estrategias; 
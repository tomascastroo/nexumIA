import React, { useState, useEffect } from "react";
import { ConditionalRule } from "../services/strategyService";

interface RuleModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (rule: ConditionalRule) => void;
  initialRule?: ConditionalRule;
}

const RuleModal: React.FC<RuleModalProps> = ({
  isOpen,
  onClose,
  onSave,
  initialRule,
}) => {
  const [condition, setCondition] = useState("");
  const [response, setResponse] = useState("");
  const [retryInDays, setRetryInDays] = useState<number | "">("");
  const [closeCase, setCloseCase] = useState(false);
  const [escalateToHuman, setEscalateToHuman] = useState(false);

  useEffect(() => {
    if (isOpen && initialRule) {
      setCondition(initialRule.condition || "");
      setResponse(initialRule.response || "");
      setRetryInDays(initialRule.retry_in_days ?? "");
      setCloseCase(initialRule.close_case ?? false);
      setEscalateToHuman(initialRule.escalate_to_human ?? false);
    } else if (isOpen) {
      setCondition("");
      setResponse("");
      setRetryInDays("");
      setCloseCase(false);
      setEscalateToHuman(false);
    }
  }, [isOpen, initialRule]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave({
      condition,
      response,
      retry_in_days: retryInDays === "" ? null : Number(retryInDays),
      close_case: closeCase,
      escalate_to_human: escalateToHuman,
    });
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
      <div className="bg-white rounded-2xl shadow-lg p-6 w-full max-w-md flex flex-col relative">
        <h3 className="text-lg font-bold text-gray-900 mb-4">
          {initialRule ? "Editar Regla" : "Añadir Regla"}
        </h3>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Condición (ej: deuda &lt; 10000)
            </label>
            <input
              type="text"
              value={condition}
              onChange={(e) => setCondition(e.target.value)}
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Respuesta del bot
            </label>
            <textarea
              value={response}
              onChange={(e) => setResponse(e.target.value)}
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Reintentar en (días)
            </label>
            <input
              type="number"
              min={0}
              value={retryInDays === null || retryInDays === "" ? "" : retryInDays}
              onChange={(e) =>
                setRetryInDays(e.target.value === "" ? "" : Number(e.target.value) || "")
              }
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
              placeholder="Dejar vacío para no reintentar"
            />
          </div>
          <div className="flex items-center gap-4">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={closeCase}
                onChange={(e) => setCloseCase(e.target.checked)}
                className="mr-2"
              />
              Cerrar caso
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={escalateToHuman}
                onChange={(e) => setEscalateToHuman(e.target.checked)}
                className="mr-2"
              />
              Escalar a humano
            </label>
          </div>
          <div className="flex justify-end gap-3 mt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-full border border-gray-200 text-gray-700 hover:bg-gray-100 text-sm font-medium"
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="px-4 py-2 rounded-full bg-blue-600 text-white hover:bg-blue-700 text-sm font-medium"
            >
              Guardar
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default RuleModal; 
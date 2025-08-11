import React, { useState, useEffect } from 'react';

interface Conditional {
  si: string;
  accion: string;
}

interface ConditionalModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (conditional: Conditional) => void;
  initialConditional?: Conditional;
}

const ConditionalModal: React.FC<ConditionalModalProps> = ({
  isOpen,
  onClose,
  onSave,
  initialConditional,
}) => {
  const [si, setSi] = useState('');
  const [accion, setAccion] = useState('');

  useEffect(() => {
    if (isOpen && initialConditional) {
      setSi(initialConditional.si);
      setAccion(initialConditional.accion);
    } else if (isOpen) {
      setSi('');
      setAccion('');
    }
  }, [isOpen, initialConditional]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave({ si, accion });
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
      <div className="bg-white rounded-2xl shadow-lg p-6 w-full max-w-sm flex flex-col relative">
        <h3 className="text-lg font-bold text-gray-900 mb-4">
          {initialConditional ? 'Editar Condicional' : 'Añadir Condicional'}
        </h3>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div>
            <label htmlFor="si" className="block text-sm font-medium text-gray-700">Si</label>
            <input
              type="text"
              id="si"
              value={si}
              onChange={(e) => setSi(e.target.value)}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-blue-500 focus:border-blue-500 sm:text-sm"
              required
            />
          </div>
          <div>
            <label htmlFor="accion" className="block text-sm font-medium text-gray-700">Acción</label>
            <input
              type="text"
              id="accion"
              value={accion}
              onChange={(e) => setAccion(e.target.value)}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              required
            />
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
              className="px-4 py-2 rounded-full bg-gray-100 text-gray-700 hover:bg-gray-200 border border-gray-200 text-sm font-medium"
            >
              Guardar
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ConditionalModal; 
import React, { useState, useEffect } from 'react';
import { Debtor } from '../services/debtorService';
import { DebtorCustomField } from '../services/debtorDatasetService';

interface Props {
  open: boolean;
  onClose: () => void;
  onSave: (debtor: Omit<Debtor, 'id'>) => void;
  initial?: Partial<Debtor> | null;
  loading?: boolean;
  title: string;
  errorMsg?: string;
  customFields: DebtorCustomField[];
}

const DebtorModal: React.FC<Props> = ({ open, onClose, onSave, initial, loading, title, errorMsg, customFields }) => {
  // Top-level fields
  const [phone, setPhone] = useState('');
  const [status, setStatus] = useState('GRIS'); // Maps to top-level 'state'
  const [customData, setCustomData] = useState<{ [key: string]: any }>({}); // For all dynamic custom fields
  const [error, setError] = useState('');

  useEffect(() => {
    console.log('DebtorModal - [DEBUG] useEffect triggered. Open:', open, 'Initial:', initial, 'CustomFields:', customFields);
    if (open) {
      setPhone(initial?.phone || '');
      setStatus(initial?.state || 'GRIS');

      const newCustomData: { [key: string]: any } = {};

      // Populate or initialize customData based on customFields
      customFields.forEach(field => {
        if (initial) {
          // For edit mode, try to get value from initial custom_data
          newCustomData[field.name] = initial.custom_data?.[field.name] !== undefined ? initial.custom_data[field.name] : '';
        } else {
          // For add mode, initialize with empty string
          newCustomData[field.name] = '';
        }
      });
      setCustomData(newCustomData);

      setError('');
    }
  }, [initial, open, customFields]); // Dependencies: initial, open, and customFields

  const handleCustomFieldChange = (fieldName: string, value: any) => {
    setCustomData(prev => ({
      ...prev,
      [fieldName]: value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    const dataToSend = {
      phone: phone,
      state: status, // Top-level state from modal's status
      custom_data: customData, // All dynamic fields are now in customData
      // Include debtor_dataset_id if in edit mode
      ...(initial && initial.debtor_dataset_id !== undefined ? { debtor_dataset_id: initial.debtor_dataset_id } : {}),
    };

    try {
      await onSave(dataToSend as Omit<Debtor, 'id'>);
      onClose();
    } catch (e: any) {
      setError(e.message);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-30 flex items-center justify-center bg-black/30">
      <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-lg p-8 w-full max-w-md flex flex-col gap-4 relative">
        <button type="button" onClick={onClose} className="absolute top-3 right-4 text-gray-400 hover:text-black text-2xl">×</button>
        <h2 className="text-xl font-bold mb-2 text-gray-900">{title}</h2>
        {/* Render standard phone field */}
        <div className="flex flex-col gap-1">
          <label className="text-sm text-gray-700">Teléfono</label>
          <input className="px-4 py-2 rounded-full border border-gray-200 focus:ring-2 focus:ring-black" value={phone} onChange={e => setPhone(e.target.value)} required disabled={loading} />
        </div>
        {/* Render standard state field */}
        <div className="flex flex-col gap-1">
          <label className="text-sm text-gray-700">Estado</label>
          <select className="px-4 py-2 rounded-full border border-gray-200 focus:ring-2 focus:ring-black" value={status} onChange={e => setStatus(e.target.value)} disabled={loading}>
            {['VERDE', 'AMARILLO', 'ROJO', 'GRIS'].map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>

        {/* Render all custom fields dynamically */}
        {customFields.map(field => {
          // Determine the input type based on field_type, default to text
          let inputType = 'text';
          if (field.field_type === 'number') inputType = 'number';

          // Determine the value to display for this custom field
          // Use value from customData state if available, otherwise default to empty
          const fieldValue = customData[field.name] !== undefined ? customData[field.name] : '';

          return (
            <div className="flex flex-col gap-1" key={field.name}>
              <label className="text-sm text-gray-700">{field.name.charAt(0).toUpperCase() + field.name.slice(1)}</label>
              <input
                className="px-4 py-2 rounded-full border border-gray-200 focus:ring-2 focus:ring-black"
                value={fieldValue}
                onChange={(e) => handleCustomFieldChange(field.name, e.target.value)}
                type={inputType}
                disabled={loading}
              />
            </div>
          );
        })}

        {(error || errorMsg) && <div className="text-red-600 text-sm text-center">{error || errorMsg}</div>}
        <button type="submit" className="w-full py-2 rounded-full bg-black text-white font-semibold hover:bg-gray-900 transition-colors disabled:opacity-60 mt-2" disabled={loading}>{loading ? 'Guardando...' : 'Guardar'}</button>
      </form>
    </div>
  );
};

export default DebtorModal; 
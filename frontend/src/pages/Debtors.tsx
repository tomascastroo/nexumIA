import React, { useEffect, useState } from 'react';
import { fetchDebtors, Debtor, createDebtor, updateDebtor, deleteDebtor, DebtorFilters, DebtorSort } from '../services/debtorService';
import { getDebtorDatasets, DebtorDataset, uploadDebtorDataset, getDebtorCustomFields, DebtorCustomField } from '../services/debtorDatasetService';
import DebtorModal from '../components/DebtorModal';

const EditIcon = () => (
  <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16.862 3.487a2.25 2.25 0 113.182 3.182L7.5 19.213l-4 1 1-4 12.362-12.726z" /></svg>
);
const DeleteIcon = () => (
  <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
);

const UploadIcon = () => (
  <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
  </svg>
);

const ConfirmModal: React.FC<{ open: boolean; onClose: () => void; onConfirm: () => void; message: string }> = ({ open, onClose, onConfirm, message }) => {
  if (!open) return null;
  console.log('ConfirmModal - Renderizado. Open:', open, 'onConfirm typeof:', typeof onConfirm);
  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/30">
      <div className="bg-white rounded-2xl shadow-lg p-8 w-full max-w-xs flex flex-col gap-4 relative">
        <div className="text-lg text-gray-900 text-center">{message}</div>
        <div className="flex gap-4 justify-center mt-2">
          <button onClick={onClose} className="px-4 py-2 rounded-full border border-gray-200 text-gray-700 hover:bg-gray-100">Cancelar</button>
          <button onClick={() => { console.log('ConfirmModal - Click en Eliminar'); onConfirm(); }} className="px-4 py-2 rounded-full bg-red-600 text-white hover:bg-red-700">Eliminar</button>
        </div>
      </div>
    </div>
  );
};

const Debtors: React.FC = () => {
  const [debtors, setDebtors] = useState<Debtor[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [modalEdit, setModalEdit] = useState<Debtor | {} | null>(null);
  const [modalLoading, setModalLoading] = useState(false);
  const [modalError, setModalError] = useState('');
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [toDelete, setToDelete] = useState<number | null>(null);
  const [datasets, setDatasets] = useState<DebtorDataset[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<number | null>(null);
  const [customFields, setCustomFields] = useState<DebtorCustomField[]>([]);
  const [fileUploadModalOpen, setFileUploadModalOpen] = useState(false);
  const [newDatasetName, setNewDatasetName] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadError, setUploadError] = useState('');
  const [currentFilters, setCurrentFilters] = useState<DebtorFilters>({});
  const [currentSort, setCurrentSort] = useState<DebtorSort | undefined>(undefined);

  const loadDebtors = async (datasetId: number | null) => {
    console.log('Debtors - Cargando deudores para dataset ID:', datasetId);
    setLoading(true);
    setError('');
    if (datasetId === null) {
      console.log('Debtors - No dataset selected, clearing debtors and custom fields.');
      setDebtors([]);
      setCustomFields([]);
      setLoading(false);
      return;
    }
    try {
      console.log('Debtors - Current Filters:', JSON.stringify(currentFilters, null, 2));
      console.log('Debtors - Current Sort:', JSON.stringify(currentSort, null, 2));
      const [debtorsData, customFieldsData] = await Promise.all([
        fetchDebtors(datasetId, currentFilters, currentSort),
        getDebtorCustomFields(datasetId)
      ]);
      console.log('Debtors - Deudores cargados para dataset ID ', datasetId, ':', JSON.stringify(debtorsData, null, 2));
      console.log('Debtors - Custom fields cargados para dataset ID ', datasetId, ':', JSON.stringify(customFieldsData, null, 2));
      setDebtors(debtorsData);
      setCustomFields(customFieldsData);
      console.log('Debtors - [DEBUG] Final customFields after fetch:', JSON.stringify(customFieldsData, null, 2));
    } catch (err: any) {
      console.error('Debtors - Error al cargar deudores o campos personalizados para dataset ID ', datasetId, ':', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const loadDatasets = async () => {
      try {
        const data = await getDebtorDatasets();
        console.log('Debtors - Datasets disponibles:', data);
        setDatasets(data);
        if (data.length > 0) {
          setSelectedDatasetId(data[0].id);
          // loadDebtors(data[0].id) will be called by the useEffect for selectedDatasetId
        } else {
          console.log('Debtors - No datasets found.');
          setLoading(false);
        }
      } catch (err: any) {
        console.error('Debtors - Error al cargar datasets:', err);
        setError(err.message);
        setLoading(false);
      }
    };
    loadDatasets();
  }, []);

  useEffect(() => {
    if (selectedDatasetId !== null) {
      console.log('Debtors - Selected dataset ID changed to:', selectedDatasetId, '. Loading debtors...');
      loadDebtors(selectedDatasetId);
    } else {
      // If no dataset selected, clear debtors and custom fields
      setDebtors([]);
      setCustomFields([]);
    }
  }, [selectedDatasetId, currentFilters, currentSort]);

  const handleAdd = async (debtor: Omit<Debtor, 'id'>) => {
    console.log('Debtors - Intentando agregar deudor:', debtor);
    if (selectedDatasetId === null) {
      setModalError('Debe seleccionar un dataset para agregar un deudor.');
      return;
    }
    setModalLoading(true);
    setModalError('');
    try {
      const newDebtor = await createDebtor({ ...debtor, debtor_dataset_id: selectedDatasetId });
      console.log('Debtors - Deudor agregado exitosamente:', newDebtor);
      setModalEdit(null);
      loadDebtors(selectedDatasetId);
    } catch (e: any) {
      console.error('Debtors - Error al agregar deudor:', e);
      setModalError(e.message);
    } finally {
      setModalLoading(false);
    }
  };

  const handleEdit = async (debtor: Omit<Debtor, 'id' | 'dni'>) => {
    console.log('handleEdit - Before update: modalEdit=', modalEdit);

    // Explicitly check for valid Debtor structure with a numeric ID
    if (modalEdit === null || !('id' in modalEdit) || typeof modalEdit.id !== 'number') {
      console.error('Debtors - ID de edición no válido:', modalEdit);
      setModalError('No se pudo editar el deudor: ID no válido.');
      return;
    }

    // Extract the ID after validation, ensuring it's a number
    const debtorId: number = (modalEdit as Debtor).id as number;

    setModalLoading(true);
    setModalError('');
    try {
      const updatedDebtor = await updateDebtor(debtorId, debtor);
      console.log('Debtors - Deudor editado exitosamente:', updatedDebtor);
      setModalEdit(null);
      loadDebtors(selectedDatasetId);
    } catch (e: any) {
      console.error('Debtors - Error al editar deudor:', e);
      setModalError(e.message);
    } finally {
      console.log('handleEdit - After update: modalEdit=', modalEdit);
      setModalLoading(false);
    }
  };

  const handleDelete = async () => {
    console.log('Debtors - Confirmando eliminación de ID:', toDelete);
    if (typeof toDelete !== 'number') {
      console.error('Debtors - ID de eliminación no válido:', toDelete);
      setError('No se pudo eliminar el deudor: ID no válido.');
      setConfirmOpen(false);
      setToDelete(null);
      return;
    }
    setError('');
    try {
      await deleteDebtor(toDelete, selectedDatasetId as number);
      console.log('Debtors - Deudor eliminado exitosamente. ID:', toDelete);
      setToDelete(null);
      setConfirmOpen(false);
      loadDebtors(selectedDatasetId);
    } catch (e: any) {
      console.error('Debtors - Error al eliminar deudor:', e);
      setError(e.message);
    }
  };

  const handleFileUpload = async () => {
    if (!selectedFile || !newDatasetName) {
      setUploadError('Por favor, seleccione un archivo y escriba un nombre para el dataset.');
      return;
    }
    setUploadLoading(true);
    setUploadError('');
    try {
      await uploadDebtorDataset(selectedFile, newDatasetName);
      setFileUploadModalOpen(false);
      setNewDatasetName('');
      setSelectedFile(null);
      // Reload datasets and debtors after upload
      const data = await getDebtorDatasets();
      setDatasets(data);
      if (data.length > 0) {
        setSelectedDatasetId(data[0].id);
        loadDebtors(data[0].id);
      } else {
        setLoading(false);
      }
    } catch (e: any) {
      setUploadError(e.message);
    } finally {
      setUploadLoading(false);
    }
  };

  const standardHeaders = [
    { key: 'phone', label: 'Teléfono' },
    { key: 'state', label: 'Estado' },
  ];

  // Dynamically generate all headers from actual debtor data and custom fields
  const customDataKeys = Array.from(new Set(debtors.flatMap(d => Object.keys(d.custom_data || {}))));
  const allHeaders = [
    ...standardHeaders,
    ...customDataKeys
      .filter(key => {
        // Exclude keys that are already in standardHeaders or are semantic duplicates like 'estado' vs 'state'
        const isStandard = standardHeaders.some(sh => sh.key === key);
        const isSemanticDuplicateOfState = key === 'estado' && standardHeaders.some(sh => sh.key === 'state');
        return !isStandard && !isSemanticDuplicateOfState;
      })
      .map(key => ({
        key: key,
        label: key.charAt(0).toUpperCase() + key.slice(1) // Capitalize for display
      }))
  ];

  return (
    <div className="max-w-5xl mx-auto pt-28 px-4">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Deudores</h1>
        <div className="flex gap-4 items-center">
          <select
            className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            value={selectedDatasetId ?? ''}
            onChange={(e) => setSelectedDatasetId(Number(e.target.value))}
          >
            <option value="" disabled>Seleccionar Dataset</option>
            {datasets.map(dataset => (
              <option key={dataset.id} value={dataset.id}>{dataset.name}</option>
            ))}
          </select>
          <button
            className="text-black text-3xl font-light hover:text-gray-700 transition-colors"
            onClick={() => { console.log('Debtors - Click en botón + (Agregar)'); setModalEdit({}); setModalLoading(false); setModalError(''); }}
            title="Agregar deudor"
          >
            +
          </button>
          <button
            className="text-black text-3xl font-light hover:text-gray-700 transition-colors"
            onClick={() => setFileUploadModalOpen(true)}
            title="Subir Dataset"
          >
            <UploadIcon />
          </button>
        </div>
      </div>

      {/* Filters and Search Bar */}
      <div className="flex flex-wrap items-center gap-4 mb-8">
        <input
          type="text"
          placeholder="Buscar deudor..."
          value={currentFilters.search || ''}
          onChange={(e) => setCurrentFilters(prev => ({ ...prev, search: e.target.value }))}
          className="flex-grow px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
        />
        <select
          className="px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
          value={currentFilters.state || ''}
          onChange={(e) => setCurrentFilters(prev => ({ ...prev, state: e.target.value }))}
        >
          <option value="">Filtrar por Estado</option>
          {['VERDE', 'AMARILLO', 'ROJO', 'GRIS'].map(s => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
      </div>

      {error && <div className="text-red-600 mb-4 text-center">{error}</div>}
      {loading && <div className="text-gray-600">Cargando...</div>}
      {!loading && !error && (
        <div className="overflow-x-auto rounded-2xl shadow border border-gray-100 bg-white">
          <table className="min-w-full text-sm text-left">
            <thead className="bg-gray-50">
              <tr>{[
                  ...allHeaders.map(header => (
                  <th
                    key={header.key}
                    className="px-6 py-4 font-semibold text-gray-700 cursor-pointer select-none"
                    onClick={() => {
                      const newDirection = 
                        currentSort?.field === header.key && currentSort?.direction === 'asc'
                          ? 'desc'
                          : 'asc';
                      setCurrentSort({ field: header.key, direction: newDirection });
                    }}
                  >
                    <div className="flex items-center space-x-1">
                      <span>{header.label}</span>
                      {currentSort?.field === header.key && (
                        <span className="text-xs ml-1">{currentSort.direction === 'asc' ? '▲' : '▼'}</span>
                      )}
                    </div>
                  </th>
                  )),
                  <th key="actions-header" className="px-6 py-4"></th>
                ]}</tr>
            </thead>
            <tbody>
              {debtors.length === 0 && (
                <tr key="no-debtors-row">
                  <td colSpan={allHeaders.length + 1} className="px-6 py-8 text-center text-gray-500">No hay deudores registrados en este dataset.</td>
                </tr>
              )}
              {debtors.map((d) => {
                console.log('Debtor row data:', JSON.stringify(d, null, 2));
                return (
                  <tr key={d.id ?? `debtor-${d.custom_data?.dni}`} className="border-t border-gray-100 hover:bg-gray-50 transition">
                    {allHeaders.map(header => {
                      let value: React.ReactNode = '';
                      console.log(`Rendering cell for header key: ${header.key}, debtor ID: ${d.id}`);
                      // Explicitly handle fields based on where they are expected
                      if (header.key === 'phone') {
                        value = d.phone; // Top-level
                      } else if (header.key === 'state') { // State is now a top-level field
                        value = (
                          <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                            d.state === 'VERDE' ? 'bg-green-100 text-green-800' :
                            d.state === 'AMARILLO' ? 'bg-yellow-100 text-yellow-800' :
                            d.state === 'ROJO' ? 'bg-red-100 text-red-800' :
                            'bg-gray-100 text-gray-700'
                          }`}>&nbsp;</span>
                        );
                      } else if (header.key === 'deuda') { // 'deuda' is a custom field in custom_data, needs special formatting
                        value = typeof d.custom_data?.deuda === 'number' && !isNaN(d.custom_data.deuda) ? `$${d.custom_data.deuda.toLocaleString()}` : '$0';
                      } else {
                        // All other fields are from custom_data
                        value = d.custom_data ? d.custom_data[header.key] : '';
                      }
                      return <td key={header.key} className="px-6 py-4">{value || ''}</td>; // Ensure empty string for null/undefined
                    })}
                    <td className="px-6 py-4 flex gap-2">
                      <button
                        className="text-gray-500 hover:text-black p-1 focus:outline-none focus:ring-2 focus:ring-black rounded-full hover:bg-blue-200 cursor-pointer"
                        title={typeof d.id === 'number' ? "Editar" : "No se puede editar: ID no disponible"}
                        onClick={() => {
                          if (typeof d.id === 'number') {
                            setModalEdit(d);
                          } else {
                            console.error('Debtors - No se puede editar, ID de deudor no válido:', d);
                            setError('No se puede editar: ID de deudor no válido.');
                          }
                        }}
                      >
                        <EditIcon />
                      </button>
                      <button
                        className="text-gray-500 hover:text-red-600 p-1 focus:outline-none focus:ring-2 focus:ring-red-600 rounded-full hover:bg-red-200 cursor-pointer"
                        title={typeof d.id === 'number' ? "Eliminar" : "No se puede eliminar: ID no disponible"}
                        onClick={() => {
                          if (typeof d.id === 'number') {
                            setToDelete(d.id);
                            setConfirmOpen(true);
                          } else {
                            console.error('Debtors - No se puede eliminar, ID de deudor no válido:', d);
                            setError('No se puede eliminar: ID de deudor no válido.');
                          }
                        }}
                      >
                        <DeleteIcon />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* File Upload Modal */}
      {fileUploadModalOpen && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/30">
          <div className="bg-white rounded-2xl shadow-lg p-8 w-full max-w-md flex flex-col gap-4 relative">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Subir Nuevo Dataset</h2>
            <input
              type="text"
              placeholder="Nombre del Dataset"
              value={newDatasetName}
              onChange={(e) => setNewDatasetName(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            />
            {/* Custom file input */}
            <div className="flex items-center gap-2 border border-gray-300 rounded-md px-4 py-2 cursor-pointer hover:border-indigo-500 transition-colors">
              <label htmlFor="file-upload" className="cursor-pointer text-gray-700 font-medium">
                {selectedFile ? selectedFile.name : 'Seleccionar Archivo'}
              </label>
              <input
                id="file-upload"
                type="file"
                onChange={(e) => setSelectedFile(e.target.files ? e.target.files[0] : null)}
                className="hidden" // Hide the default file input
              />
            </div>
            {uploadError && <div className="text-red-600 text-sm">{uploadError}</div>}
            <div className="flex gap-4 justify-end mt-4">
              <button
                onClick={() => { setFileUploadModalOpen(false); setNewDatasetName(''); setSelectedFile(null); setUploadError(''); }}
                className="px-4 py-2 rounded-full border border-gray-200 text-gray-700 hover:bg-gray-100"
              >
                Cancelar
              </button>
              <button
                onClick={handleFileUpload}
                className={`px-4 py-2 rounded-full bg-blue-600 text-white hover:bg-blue-700 ${uploadLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
                disabled={uploadLoading}
              >
                {uploadLoading ? 'Subiendo...' : 'Subir Dataset'}
              </button>
            </div>
          </div>
        </div>
      )}

      <DebtorModal
        open={!!modalEdit}
        onClose={() => { console.log('Debtors - Cerrando modal. modalEdit=', modalEdit); setModalEdit(null); setModalError(''); }}
        onSave={modalEdit && 'id' in modalEdit ? handleEdit : handleAdd}
        loading={modalLoading}
        title={modalEdit && 'id' in modalEdit ? "Editar deudor" : "Agregar deudor"}
        errorMsg={modalError}
        initial={modalEdit && 'id' in modalEdit ? modalEdit : undefined}
        customFields={customFields}
      />
      <ConfirmModal
        open={confirmOpen}
        onClose={() => { console.log('Debtors - Cerrando modal de Confirmación'); setConfirmOpen(false); setToDelete(null); }}
        onConfirm={handleDelete}
        message="¿Seguro que quieres eliminar al deudor?"
      />
    </div>
  );
};

export default Debtors; 
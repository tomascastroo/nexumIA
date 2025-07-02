import React, { useEffect, useState } from 'react';
import { fetchDebtors, Debtor, createDebtor, updateDebtor, deleteDebtor } from '../services/debtorService';
import DebtorModal from '../components/DebtorModal';

const EditIcon = () => (
  <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16.862 3.487a2.25 2.25 0 113.182 3.182L7.5 19.213l-4 1 1-4 12.362-12.726z" /></svg>
);
const DeleteIcon = () => (
  <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
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
  const [modalOpen, setModalOpen] = useState(false);
  const [modalEdit, setModalEdit] = useState<Debtor | null>(null);
  const [modalLoading, setModalLoading] = useState(false);
  const [modalError, setModalError] = useState('');
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [toDelete, setToDelete] = useState<number | null>(null);

  const loadDebtors = () => {
    console.log('Debtors - Cargando deudores...');
    setLoading(true);
    fetchDebtors()
      .then(data => { console.log('Debtors - Deudores cargados:', data); setDebtors(data); })
      .catch(err => { console.error('Debtors - Error al cargar deudores:', err); setError(err.message); })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadDebtors();
  }, []);

  const handleAdd = async (debtor: Omit<Debtor, 'id'>) => {
    console.log('Debtors - Intentando agregar deudor:', debtor);
    setModalLoading(true);
    setModalError('');
    try {
      const newDebtor = await createDebtor(debtor);
      console.log('Debtors - Deudor agregado exitosamente:', newDebtor);
      setModalOpen(false);
      setModalEdit(null);
      loadDebtors();
    } catch (e: any) {
      console.error('Debtors - Error al agregar deudor:', e);
      setModalError(e.message);
    } finally {
      setModalLoading(false);
    }
  };

  const handleEdit = async (debtor: Omit<Debtor, 'id' | 'dni'>) => {
    console.log('handleEdit - Before update: modalOpen=', modalOpen, 'modalEdit=', modalEdit?.id);
    console.log('Debtors - Intentando editar deudor. ID actual:', modalEdit?.id, 'Nuevos datos:', debtor);
    if (!modalEdit || typeof modalEdit.id !== 'number') {
      console.error('Debtors - ID de edición no válido:', modalEdit);
      setModalError('No se pudo editar el deudor: ID no válido.');
      return;
    }
    setModalLoading(true);
    setModalError('');
    try {
      const updatedDebtor = await updateDebtor(modalEdit.id, debtor);
      console.log('Debtors - Deudor editado exitosamente:', updatedDebtor);
      setModalEdit(null);
      loadDebtors();
    } catch (e: any) {
      console.error('Debtors - Error al editar deudor:', e);
      setModalError(e.message);
    } finally {
      console.log('handleEdit - After update: modalOpen=', modalOpen, 'modalEdit=', modalEdit?.id);
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
      await deleteDebtor(toDelete);
      console.log('Debtors - Deudor eliminado exitosamente. ID:', toDelete);
      setToDelete(null);
      setConfirmOpen(false);
      loadDebtors();
    } catch (e: any) {
      console.error('Debtors - Error al eliminar deudor:', e);
      setError(e.message);
    }
  };

  return (
    <div className="max-w-5xl mx-auto pt-28 px-4">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Deudores</h1>
        <button
          className="text-black text-3xl font-light hover:text-gray-700 transition-colors"
          onClick={() => { console.log('Debtors - Click en botón + (Agregar)'); setModalOpen(true); setModalLoading(false); setModalError(''); }}
          title="Agregar deudor"
        >
          +
        </button>
      </div>
      {error && <div className="text-red-600 mb-4 text-center">{error}</div>}
      {loading && <div className="text-gray-600">Cargando...</div>}
      {!loading && !error && (
        <div className="overflow-x-auto rounded-2xl shadow border border-gray-100 bg-white">
          <table className="min-w-full text-sm text-left">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-4 font-semibold text-gray-700">Nombre</th>
                <th className="px-6 py-4 font-semibold text-gray-700">DNI</th>
                <th className="px-6 py-4 font-semibold text-gray-700">Email</th>
                <th className="px-6 py-4 font-semibold text-gray-700">Teléfono</th>
                <th className="px-6 py-4 font-semibold text-gray-700">Monto</th>
                <th className="px-6 py-4 font-semibold text-gray-700">Estado</th>
                <th className="px-6 py-4"></th>
              </tr>
            </thead>
            <tbody>
              {debtors.length === 0 && (
                <tr key="no-debtors-row">
                  <td colSpan={6} className="px-6 py-8 text-center text-gray-500">No hay deudores registrados.</td>
                </tr>
              )}
              {debtors.map((d) => {
                console.log('Debtor in map - ID:', d.id, 'DNI:', d.dni);
                return (
                  <tr key={d.id ?? `debtor-${d.dni}`} className="border-t border-gray-100 hover:bg-gray-50 transition">
                    <td className="px-6 py-4">{d.name}</td>
                    <td className="px-6 py-4">{d.dni}</td>
                    <td className="px-6 py-4">{d.email}</td>
                    <td className="px-6 py-4">{d.phone}</td>
                    <td className="px-6 py-4">
                      {typeof d.amount === 'number' && !isNaN(d.amount)
                        ? `$${d.amount.toLocaleString()}`
                        : '$0'}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                        d.status === 'VERDE' ? 'bg-green-100 text-green-800' :
                        d.status === 'AMARILLO' ? 'bg-yellow-100 text-yellow-800' :
                        d.status === 'ROJO' ? 'bg-red-100 text-red-800' :
                        'bg-gray-100 text-gray-700'
                      }`}>&nbsp;</span>
                    </td>
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
      <DebtorModal
        open={modalOpen}
        onClose={() => { console.log('Debtors - Cerrando modal de Agregar. modalOpen=', modalOpen, 'modalEdit=', modalEdit?.id); setModalOpen(false); setModalError(''); setModalEdit(null); }}
        onSave={handleAdd}
        loading={modalLoading}
        title="Agregar deudor"
        errorMsg={modalError}
      />
      <DebtorModal
        open={!!modalEdit}
        onClose={() => { console.log('Debtors - Cerrando modal de Editar. modalOpen=', modalOpen, 'modalEdit=', modalEdit?.id); setModalEdit(null); setModalError(''); }}
        onSave={handleEdit}
        initial={modalEdit || undefined}
        loading={modalLoading}
        title="Editar deudor"
        errorMsg={modalError}
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
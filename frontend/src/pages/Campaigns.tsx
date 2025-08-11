import React, { useState, useEffect } from 'react';
import { getCampaigns, createCampaign, updateCampaign, deleteCampaign, Campaign, getBots, Bot, launchCampaign } from '../services/campaignService';
import { getDebtorDatasets, DebtorDataset } from '../services/debtorDatasetService';
import { getStrategies, Strategy } from '../services/strategyService';
import axios from 'axios';

const Campaigns: React.FC = () => {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [currentCampaign, setCurrentCampaign] = useState<Campaign | null>(null);
  const [formName, setFormName] = useState('');
  const [formBotId, setFormBotId] = useState<number | ''>('');
  const [formStrategyId, setFormStrategyId] = useState<number | ''>('');
  const [formDatasetId, setFormDatasetId] = useState<number | ''>('');
  const [formStatus, setFormStatus] = useState('inactive');
  const [formStartDate, setFormStartDate] = useState('');
  const [formEndDate, setFormEndDate] = useState('');
  const [modalLoading, setModalLoading] = useState(false);
  const [modalError, setModalError] = useState('');
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [toDelete, setToDelete] = useState<number | null>(null);
  const [launchConfirmOpen, setLaunchConfirmOpen] = useState(false);
  const [toLaunch, setToLaunch] = useState<number | null>(null);
  const [datasets, setDatasets] = useState<DebtorDataset[]>([]);
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [bots, setBots] = useState<Bot[]>([]);
  const token = localStorage.getItem('token');

  useEffect(() => {
    if (!token) return;
    loadAll();
  }, [token]);

  const loadAll = async () => {
    setLoading(true);
    setError('');
    try {
      const [camps, dsets, strats, botsRes] = await Promise.all([
        getCampaigns(token!),
        getDebtorDatasets(),
        getStrategies(token!),
        getBots(token!),
      ]);
      setCampaigns(camps);
      setDatasets(dsets);
      setStrategies(strats);
      setBots(botsRes as Bot[]);
    } catch (err: any) {
      setError(err.message || 'Error al cargar campañas');
    } finally {
      setLoading(false);
    }
  };

  const openCreateModal = () => {
    setCurrentCampaign(null);
    setFormName('');
    setFormBotId('');
    setFormStrategyId('');
    setFormDatasetId('');
    setFormStatus('inactive');
    setFormStartDate('');
    setFormEndDate('');
    setModalError('');
    setModalOpen(true);
  };

  const openEditModal = (c: Campaign) => {
    setCurrentCampaign(c);
    setFormName(c.name);
    setFormBotId(c.bot_id);
    setFormStrategyId(c.strategy_id);
    setFormDatasetId(c.debtor_dataset_id);
    setFormStatus(c.status || 'inactive');
    setFormStartDate(c.start_date ? c.start_date.slice(0, 10) : '');
    setFormEndDate(c.end_date ? c.end_date.slice(0, 10) : '');
    setModalError('');
    setModalOpen(true);
  };

  const handleCreateOrUpdate = async () => {
    if (!token) return;
    setModalLoading(true);
    setModalError('');
    try {
      const data = {
        name: formName,
        bot_id: formBotId || undefined,
        strategy_id: formStrategyId,
        debtor_dataset_id: formDatasetId,
        status: formStatus,
        start_date: formStartDate || undefined,
        end_date: formEndDate || undefined,
      };
      if (currentCampaign) {
        await updateCampaign(currentCampaign.id, data, token);
      } else {
        await createCampaign(data, token);
      }
      setModalOpen(false);
      setCurrentCampaign(null);
      loadAll();
    } catch (e: any) {
      setModalError(e.message);
    } finally {
      setModalLoading(false);
    }
  };

  const openDeleteConfirm = (id: number) => {
    setToDelete(id);
    setConfirmOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!token || typeof toDelete !== 'number') return;
    setError('');
    try {
      await deleteCampaign(toDelete, token);
      setConfirmOpen(false);
      setToDelete(null);
      loadAll();
    } catch (e: any) {
      setError(e.message);
    }
  };

  const handleLaunchCampaign = async (campaignId: number) => {
    setToLaunch(campaignId);
    setLaunchConfirmOpen(true);
  };

  const handleConfirmLaunch = async () => {
    if (!token || typeof toLaunch !== 'number') return;
    setError('');
    try {
      await launchCampaign(toLaunch, token);
      setLaunchConfirmOpen(false);
      setToLaunch(null);
      loadAll();
    } catch (e: any) {
      setError(e.message || 'Error al lanzar la campaña.');
    }
  };

  return (
    <div className="max-w-5xl mx-auto pt-28 px-4">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Campañas</h1>
        <button
          onClick={openCreateModal}
          className="px-4 py-2 rounded-full bg-blue-600 text-white hover:bg-blue-700 text-sm font-medium"
        >
          Crear Nueva Campaña
        </button>
      </div>
      {loading && <div className="text-center text-gray-500">Cargando campañas...</div>}
      {error && <div className="text-center text-red-500">Error: {error}</div>}
      {!loading && !error && campaigns.length === 0 && (
        <div className="text-center text-gray-500">No hay campañas creadas.</div>
      )}
      {!loading && !error && campaigns.length > 0 && (
        <div className="bg-white shadow-lg rounded-2xl p-6 mb-8">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nombre</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Bot</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estrategia</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Dataset</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Inicio</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fin</th>
                  <th className="relative px-6 py-3"><span className="sr-only">Acciones</span></th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {campaigns.map((c) => (
                  <tr key={c.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{c.name}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{bots.find(b => b.id === c.bot_id)?.name || c.bot_id}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{strategies.find(s => s.id === c.strategy_id)?.name || c.strategy_id}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{datasets.find(d => d.id === c.debtor_dataset_id)?.name || c.debtor_dataset_id}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{c.status}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{c.start_date ? c.start_date.slice(0, 10) : '-'}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{c.end_date ? c.end_date.slice(0, 10) : '-'}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        onClick={() => handleLaunchCampaign(c.id)}
                        className="text-green-600 hover:text-green-900 mr-4"
                      >
                        Lanzar
                      </button>
                      <button
                        onClick={() => openEditModal(c)}
                        className="text-blue-600 hover:text-blue-900 mr-4"
                      >
                        Editar
                      </button>
                      <button
                        onClick={() => openDeleteConfirm(c.id)}
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
      {/* Modal Crear/Editar */}
      {modalOpen && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/30">
          <div className="bg-white rounded-2xl shadow-lg p-8 w-full max-w-md flex flex-col relative max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex-shrink-0">
              {currentCampaign ? 'Editar Campaña' : 'Crear Nueva Campaña'}
            </h2>
            <form onSubmit={e => { e.preventDefault(); handleCreateOrUpdate(); }} className="flex flex-col gap-4 flex-grow">
              <div className="flex-grow pr-2">
                <div>
                  <label htmlFor="name" className="block text-sm font-medium text-gray-700">Nombre</label>
                  <input
                    type="text"
                    id="name"
                    value={formName}
                    onChange={e => setFormName(e.target.value)}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    required
                  />
                </div>
                <div>
                  <label htmlFor="bot" className="block text-sm font-medium text-gray-700">Bot</label>
                  <select
                    id="bot"
                    value={formBotId ?? ''}
                    onChange={e => setFormBotId(e.target.value ? Number(e.target.value) : '')}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  >
                    <option value="">Sin bot</option>
                    {bots.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
                  </select>
                </div>
                <div>
                  <label htmlFor="strategy" className="block text-sm font-medium text-gray-700">Estrategia</label>
                  <select
                    id="strategy"
                    value={formStrategyId}
                    onChange={e => setFormStrategyId(Number(e.target.value))}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    required
                  >
                    <option value="" disabled>Seleccionar Estrategia</option>
                    {strategies.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                  </select>
                </div>
                <div>
                  <label htmlFor="dataset" className="block text-sm font-medium text-gray-700">Dataset de Deudores</label>
                  <select
                    id="dataset"
                    value={formDatasetId}
                    onChange={e => setFormDatasetId(Number(e.target.value))}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    required
                  >
                    <option value="" disabled>Seleccionar Dataset</option>
                    {datasets.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
                  </select>
                </div>
                <div>
                  <label htmlFor="status" className="block text-sm font-medium text-gray-700">Estado</label>
                  <select
                    id="status"
                    value={formStatus}
                    onChange={e => setFormStatus(e.target.value)}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  >
                    <option value="inactive">Inactiva</option>
                    <option value="active">Activa</option>
                  </select>
                </div>
                <div className="flex gap-2">
                  <div className="flex-1">
                    <label htmlFor="start_date" className="block text-sm font-medium text-gray-700">Fecha Inicio</label>
                    <input
                      type="date"
                      id="start_date"
                      value={formStartDate}
                      onChange={e => setFormStartDate(e.target.value)}
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    />
                  </div>
                  <div className="flex-1">
                    <label htmlFor="end_date" className="block text-sm font-medium text-gray-700">Fecha Fin</label>
                    <input
                      type="date"
                      id="end_date"
                      value={formEndDate}
                      onChange={e => setFormEndDate(e.target.value)}
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    />
                  </div>
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
              {modalError && <div className="text-red-500 text-sm mt-2">{modalError}</div>}
            </form>
          </div>
        </div>
      )}
      {/* Modal Confirmación Borrado */}
      {confirmOpen && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/30">
          <div className="bg-white rounded-2xl shadow-lg p-8 w-full max-w-xs flex flex-col gap-4 relative">
            <div className="text-lg text-gray-900 text-center">¿Está seguro que desea eliminar esta campaña?</div>
            <div className="flex gap-4 justify-center mt-2">
              <button onClick={() => setConfirmOpen(false)} className="px-4 py-2 rounded-full border border-gray-200 text-gray-700 hover:bg-gray-100">Cancelar</button>
              <button onClick={handleDeleteConfirm} className="px-4 py-2 rounded-full bg-red-600 text-white hover:bg-red-700">Eliminar</button>
            </div>
          </div>
        </div>
      )}
      {/* Confirmación de Lanzamiento - NUEVO */}
      {launchConfirmOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
          <div className="bg-white rounded-2xl shadow-lg p-8 w-full max-w-sm">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Confirmar Lanzamiento</h2>
            <p className="text-gray-700 mb-6">¿Estás seguro de que quieres lanzar esta campaña? Esta acción puede iniciar el envío de mensajes.</p>
            <div className="flex justify-end space-x-4">
              <button
                onClick={() => setLaunchConfirmOpen(false)}
                className="px-4 py-2 rounded-full bg-gray-200 text-gray-700 hover:bg-gray-300 text-sm font-medium"
              >
                Cancelar
              </button>
              <button
                onClick={handleConfirmLaunch}
                className="px-4 py-2 rounded-full bg-green-600 text-white hover:bg-green-700 text-sm font-medium"
              >
                Lanzar Campaña
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Campaigns; 
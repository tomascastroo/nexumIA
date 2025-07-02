import React, { useState, useEffect } from 'react';
import { Debtor } from '../services/debtorService';

interface Props {
  open: boolean;
  onClose: () => void;
  onSave: (debtor: Omit<Debtor, 'id'>) => void;
  initial?: Partial<Debtor> | null;
  loading?: boolean;
  title: string;
  errorMsg?: string;
}

const estados = ['activo', 'inactivo', 'moroso'];

const DebtorModal: React.FC<Props> = ({ open, onClose, onSave, initial, loading, title, errorMsg }) => {
  const [name, setName] = useState('');
  const [dni, setDni] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [amount, setAmount] = useState('');
  const [status, setStatus] = useState('activo');
  const [error, setError] = useState('');

  useEffect(() => {
    if (open) {
      if (initial) {
        setName(initial.name || '');
        setDni(initial.dni || '');
        setEmail(initial.email || '');
        setPhone(initial.phone || '');
        setAmount(initial.amount !== undefined && initial.amount !== null ? initial.amount.toString() : '');
        setStatus(initial.status || 'activo');
      } else {
        setName('');
        setDni('');
        setEmail('');
        setPhone('');
        setAmount('');
        setStatus('activo');
      }
      setError('');
    }
  }, [initial, open]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !phone) {
      setError('Nombre y Teléfono son obligatorios');
      return;
    }
    if (email && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
      setError('Email inválido');
      return;
    }
    if (amount !== '' && isNaN(Number(amount))) {
      setError('Monto inválido');
      return;
    }
    setError('');
    onSave({ name, dni: dni || undefined, email: email || undefined, phone, amount: amount !== '' ? Number(amount) : undefined, status });
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-30 flex items-center justify-center bg-black/30">
      <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-lg p-8 w-full max-w-md flex flex-col gap-4 relative">
        <button type="button" onClick={onClose} className="absolute top-3 right-4 text-gray-400 hover:text-black text-2xl">×</button>
        <h2 className="text-xl font-bold mb-2 text-gray-900">{title}</h2>
        <div className="flex flex-col gap-1">
          <label className="text-sm text-gray-700">Nombre</label>
          <input className="px-4 py-2 rounded-full border border-gray-200 focus:ring-2 focus:ring-black" value={name} onChange={e => setName(e.target.value)} required disabled={loading} />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-sm text-gray-700">DNI</label>
          <input className="px-4 py-2 rounded-full border border-gray-200 focus:ring-2 focus:ring-black" value={dni} onChange={e => setDni(e.target.value)} disabled={loading} />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-sm text-gray-700">Email</label>
          <input className="px-4 py-2 rounded-full border border-gray-200 focus:ring-2 focus:ring-black" value={email} onChange={e => setEmail(e.target.value)} type="email" disabled={loading} />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-sm text-gray-700">Teléfono</label>
          <input className="px-4 py-2 rounded-full border border-gray-200 focus:ring-2 focus:ring-black" value={phone} onChange={e => setPhone(e.target.value)} required disabled={loading} />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-sm text-gray-700">Monto</label>
          <input className="px-4 py-2 rounded-full border border-gray-200 focus:ring-2 focus:ring-black" value={amount} onChange={e => setAmount(e.target.value)} required type="number" min="0" step="0.01" disabled={loading} />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-sm text-gray-700">Estado</label>
          <select className="px-4 py-2 rounded-full border border-gray-200 focus:ring-2 focus:ring-black" value={status} onChange={e => setStatus(e.target.value)} disabled={loading}>
            {estados.map(e => <option key={e} value={e}>{e}</option>)}
          </select>
        </div>
        {(error || errorMsg) && <div className="text-red-600 text-sm text-center">{error || errorMsg}</div>}
        <button type="submit" className="w-full py-2 rounded-full bg-black text-white font-semibold hover:bg-gray-900 transition-colors disabled:opacity-60 mt-2" disabled={loading}>{loading ? 'Guardando...' : 'Guardar'}</button>
      </form>
    </div>
  );
};

export default DebtorModal; 
import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { registerUser } from '../services/authService';

const Register: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess(false);
    if (!email || !password) {
      setError('Todos los campos son obligatorios');
      return;
    }
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
      setError('Email inválido');
      return;
    }
    if (password.length < 6) {
      setError('La contraseña debe tener al menos 6 caracteres');
      return;
    }
    setLoading(true);
    try {
      await registerUser(email, password);
      setSuccess(true);
      setTimeout(() => navigate('/login'), 1200);
    } catch (err: any) {
      setError(err.message || 'Error de registro');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-white px-4">
      <form
        className="w-full max-w-md bg-white rounded-2xl shadow-lg p-10 flex flex-col gap-6 border border-gray-100"
        onSubmit={handleSubmit}
        noValidate
      >
        <h1 className="text-3xl font-bold text-gray-900 text-center mb-2">Crear cuenta</h1>
        <div className="flex flex-col gap-1">
          <label htmlFor="email" className="text-base font-medium text-gray-800">Dirección de correo electrónico</label>
          <input
            id="email"
            type="email"
            autoComplete="email"
            className="mt-1 px-4 py-3 rounded-full border border-gray-200 focus:outline-none focus:ring-2 focus:ring-black text-gray-900 bg-white text-lg transition-all"
            value={email}
            onChange={e => setEmail(e.target.value)}
            required
            placeholder="tucorreo@ejemplo.com"
          />
        </div>
        <div className="flex flex-col gap-1">
          <label htmlFor="password" className="text-base font-medium text-gray-800">Contraseña</label>
          <input
            id="password"
            type="password"
            autoComplete="new-password"
            className="mt-1 px-4 py-3 rounded-full border border-gray-200 focus:outline-none focus:ring-2 focus:ring-black text-gray-900 bg-white text-lg transition-all"
            value={password}
            onChange={e => setPassword(e.target.value)}
            required
            minLength={6}
            placeholder="••••••••"
          />
        </div>
        {error && <div className="text-sm text-red-600 text-center -mt-2">{error}</div>}
        {success && <div className="text-sm text-green-600 text-center -mt-2">¡Registro exitoso!</div>}
        <button
          type="submit"
          className="w-full py-3 rounded-full bg-black text-white text-lg font-semibold hover:bg-gray-900 transition-colors disabled:opacity-60 mt-2"
          disabled={loading}
        >
          {loading ? 'Registrando...' : 'Registrarse'}
        </button>
        <div className="text-center mt-2">
          <span className="text-sm text-gray-600">¿Ya tienes cuenta? </span>
          <Link to="/login" className="text-sm text-blue-600 hover:underline">Inicia sesión</Link>
        </div>
      </form>
    </div>
  );
};

export default Register; 
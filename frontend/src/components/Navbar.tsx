import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { logout } from '../services/authService';

const navLinks = [
  { to: '/', label: 'Dashboard' },
  { to: '/deudores', label: 'Deudores' },
  { to: '/estrategias', label: 'Estrategias' },
  { to: '/campanas', label: 'Campañas' },
];

const Navbar: React.FC = () => {
  const [open, setOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const token = localStorage.getItem('token');
  const expiresAt = localStorage.getItem('expires_at');

  useEffect(() => {
    if (token && expiresAt) {
      const expirationTime = parseInt(expiresAt) * 1000; // Convert to milliseconds
      if (Date.now() >= expirationTime) {
        console.log('Token expired, logging out...');
        logout();
        navigate('/login');
      }
    }
  }, [location, token, expiresAt, navigate]); // Add dependencies

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="fixed top-0 left-0 w-full bg-white shadow z-20">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <Link to="/" className="text-xl font-bold tracking-tight text-gray-900">Nexum IA</Link>
        <div className="hidden md:flex gap-6 items-center">
          {token && navLinks.map(link => (
            <Link
              key={link.to}
              to={link.to}
              className={`text-base font-medium px-2 py-1 rounded transition-colors ${location.pathname === link.to ? 'text-black' : 'text-gray-600 hover:text-black'}`}
            >
              {link.label}
            </Link>
          ))}
          {token && (
            <button
              onClick={handleLogout}
              className="ml-4 px-4 py-2 rounded-full bg-gray-100 text-gray-700 hover:bg-gray-200 border border-gray-200 text-sm font-medium"
            >
              Cerrar sesión
            </button>
          )}
        </div>
        <button
          className="md:hidden p-2 rounded focus:outline-none focus:ring-2 focus:ring-black"
          onClick={() => setOpen(!open)}
          aria-label="Abrir menú"
        >
          <span className="block w-6 h-0.5 bg-black mb-1"></span>
          <span className="block w-6 h-0.5 bg-black mb-1"></span>
          <span className="block w-6 h-0.5 bg-black"></span>
        </button>
      </div>
      {open && (
        <div className="md:hidden bg-white border-t border-gray-100 shadow px-4 pb-4 flex flex-col gap-2">
          {token && navLinks.map(link => (
            <Link
              key={link.to}
              to={link.to}
              className={`text-base font-medium py-2 ${location.pathname === link.to ? 'text-black' : 'text-gray-600 hover:text-black'}`}
              onClick={() => setOpen(false)}
            >
              {link.label}
            </Link>
          ))}
          {token && (
            <button
              onClick={() => { setOpen(false); handleLogout(); }}
              className="mt-2 px-4 py-2 rounded-full bg-gray-100 text-gray-700 hover:bg-gray-200 border border-gray-200 text-sm font-medium"
            >
              Cerrar sesión
            </button>
          )}
        </div>
      )}
    </nav>
  );
};

export default Navbar; 
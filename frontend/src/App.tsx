import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import Login from './pages/Login';
import Register from './pages/Register';
import Debtors from './pages/Debtors';
import Dashboard from './pages/Dashboard';
import Estrategias from './pages/Estrategias';
import Campaigns from './pages/Campaigns';
import Navbar from './components/Navbar';
import './styles/global.css';
import { isTokenExpired } from './services/authService';

const Home: React.FC = () => (
  <div className="min-h-screen flex items-center justify-center">
    <h1 className="text-2xl font-semibold text-gray-900">Bienvenido a Nexum IA</h1>
  </div>
);

const ProtectedRoute: React.FC = () => {
  const token = localStorage.getItem('token');
  const expired = isTokenExpired();
  return token && !expired ? (
    <>
      <Navbar />
      <Outlet />
    </>
  ) : (
    <Navigate to="/login" replace />
  );
};

const App: React.FC = () => {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        
        {/* Protected Routes */}
        <Route element={<ProtectedRoute />}>
          <Route path="/" element={<Home />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/deudores" element={<Debtors />} />
          <Route path="/estrategias" element={<Estrategias />} />
          <Route path="/campanas" element={<Campaigns />} />
        </Route>
      </Routes>
    </Router>
  );
};

export default App;

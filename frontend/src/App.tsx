import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Register from './pages/Register';
import Debtors from './pages/Debtors';
import Navbar from './components/Navbar';
import './styles/global.css';

const Home: React.FC = () => (
  <div className="min-h-screen flex items-center justify-center">
    <h1 className="text-2xl font-semibold text-gray-900">Bienvenido a Nexum IA</h1>
  </div>
);

const App: React.FC = () => {
  return (
    <Router>
      <Navbar />
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/deudores" element={<Debtors />} />
        <Route path="/" element={<Home />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </Router>
  );
};

export default App;

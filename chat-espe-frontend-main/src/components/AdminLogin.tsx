import React, { useState } from 'react';
import axios, { AxiosError } from 'axios';

interface Props {
  onLogin: () => void;
}

const AdminLogin: React.FC<Props> = ({ onLogin }) => {
  const [form, setForm] = useState({ username: 'admin', password: '' }); // <-- Dejé 'admin' aquí para tu comodidad
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // --- ¡AQUÍ ESTÁ LA CORRECCIÓN! ---
  // Arreglamos la URL base para el desarrollo en red
  const API_BASE = import.meta.env.MODE === 'production'
    ? 'https://chat-espe-backend-production.up.railway.app'
    : `http://${window.location.hostname}:5000`; // <-- ¡ARREGLADO!

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      // La URL ahora será http://192.168.100.36:5000/api/admin/login
      const res = await axios.post(`${API_BASE}/api/admin/login`, form, {
        withCredentials: true,
        timeout: 5000
      });
      if (res.data.success) {
        onLogin();
      }
    } catch (err: unknown) {
      const error = err as AxiosError<{ error?: string }>;
      setError(error.response?.data?.error || 'Error de conexión');
      console.error('Login error:', error);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="card" style={{ maxWidth: '400px', flex: 1 }}>
      <h2 style={{ marginBottom: '20px', color: '#00c8a0', textAlign: 'center' }}> 
        {/* (Estilo actualizado para el tema oscuro) */}
        🔑 Login de Admin
      </h2>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Usuario"
          value={form.username}
          onChange={e => setForm({ ...form, username: e.target.value })}
          required
          disabled={loading}
        />
        <input
          type="password"
          placeholder="Contraseña"
          value={form.password}
          onChange={e => setForm({ ...form, password: e.target.value })}
          required
          disabled={loading}
        />
        {error && <div style={{ color: '#e53e3e', margin: '10px 0' }}>{error}</div>}
        <button type="submit" disabled={loading}>
          {loading ? 'Ingresando...' : 'Ingresar'}
        </button>
      </form>
      
      {/* --- ESTO SE MANTIENE TAL CUAL LO PEDISTE --- */}
      <div style={{ marginTop: '20px', fontSize: '14px', color: '#aaa', textAlign: 'center' }}> 
        {/* (Estilo actualizado para el tema oscuro) */}
        Usuario: <strong>admin</strong><br/>
        Contraseña: <strong>espe2025</strong>
      </div>
    </div>
  );
};

export default AdminLogin;
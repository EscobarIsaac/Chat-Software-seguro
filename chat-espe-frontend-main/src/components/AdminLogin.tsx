import React, { useState } from 'react';
import axios, { AxiosError } from 'axios';

interface Props {
  onLogin: () => void;
}

const AdminLogin: React.FC<Props> = ({ onLogin }) => {
  const [form, setForm] = useState({ username: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const API_BASE = import.meta.env.MODE === 'production'
    ? 'https://chat-espe-backend-production.up.railway.app'
    : '';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const res = await axios.post(`${API_BASE}/api/admin/login`, form, {
        withCredentials: true,
        timeout: 5000
      });
      if (res.data.success) {
        onLogin();
      }
    } catch (err: unknown) {  // ← unknown, NO any
      const error = err as AxiosError<{ error?: string }>;
      setError(error.response?.data?.error || 'Error de conexión');
      console.error('Login error:', error);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="card" style={{ maxWidth: '400px', flex: 1 }}>
      <h2 style={{ marginBottom: '20px', color: '#667eea', textAlign: 'center' }}>
        Panel Administrador
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
        {error && <div style={{ color: 'red', margin: '10px 0' }}>{error}</div>}
        <button type="submit" disabled={loading}>
          {loading ? 'Ingresando...' : 'Ingresar'}
        </button>
      </form>
      <div style={{ marginTop: '20px', fontSize: '14px', color: '#666', textAlign: 'center' }}>
        Usuario: <strong>admin</strong><br/>
        Contraseña: <strong>espe2025</strong>
      </div>
    </div>
  );
};

export default AdminLogin;
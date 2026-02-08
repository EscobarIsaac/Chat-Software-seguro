import React, { useCallback, useEffect, useRef, useState } from 'react';
import axios, { AxiosError } from 'axios';
import { API_BASE_URL } from '../apiConfig';
import {
  buildAuthHeaders,
  getBiometricToken,
  openBiometricVerification,
  subscribeToTokenChanges
} from '../services/biometricToken';

interface Props {
  onLogin: () => void;
}

const AdminLogin: React.FC<Props> = ({ onLogin }) => {
  const [username, setUsername] = useState('admin');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const API_BASE = API_BASE_URL;

  const autoLoginRef = useRef(false);

  const runAdminLogin = useCallback(async () => {
    setLoading(true);
    setError('');

    try {
      const token = getBiometricToken();
      if (!token) {
        setError('Falta biometricToken. Inicia sesión con Windows Hello en el gateway.');
        return;
      }

      const res = await axios.post(`${API_BASE}/api/admin/login`, { username }, {
        withCredentials: true,
        timeout: 5000,
        headers: buildAuthHeaders()
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
      autoLoginRef.current = false;
    }
  }, [API_BASE, onLogin, username]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await runAdminLogin();
  };

  const handleBiometricRedirect = () => {
    const popup = openBiometricVerification(username || 'admin', 'login', 'admin');
    if (!popup) {
      setError('No se pudo abrir la ventana del gateway biométrico.');
      return;
    }
    setError('Confirma tu identidad en la ventana emergente. Se cerrará automáticamente.');
    popup.focus();
  };

  useEffect(() => {
    const unsubscribe = subscribeToTokenChanges(() => {
      if (autoLoginRef.current) return;
      autoLoginRef.current = true;
      runAdminLogin();
    });
    return unsubscribe;
  }, [runAdminLogin]);
  
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
          value={username}
          onChange={e => setUsername(e.target.value)}
          required
          disabled={loading}
        />
        {error && <div style={{ color: '#e53e3e', margin: '10px 0' }}>{error}</div>}
        <button type="submit" disabled={loading}>
          {loading ? 'Validando...' : 'Validar token biométrico'}
        </button>
        <button
          type="button"
          onClick={handleBiometricRedirect}
          disabled={loading}
          style={{ marginTop: '10px', background: '#1f2937', color: '#fff' }}
        >
          Abrir verificación biométrica
        </button>
      </form>
      
      {/* --- ESTO SE MANTIENE TAL CUAL LO PEDISTE --- */}
      <div style={{ marginTop: '20px', fontSize: '14px', color: '#aaa', textAlign: 'center' }}> 
        {/* (Estilo actualizado para el tema oscuro) */}
        Inicia sesión en el gateway usando Windows Hello/huella.<br/>
        El backend ahora abre una pestaña de verificación y actualiza tu sesión automáticamente.
      </div>
    </div>
  );
};

export default AdminLogin;
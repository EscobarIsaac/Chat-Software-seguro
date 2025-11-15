import React, { useState } from 'react';
import axios, { AxiosError } from 'axios';
import type { RoomForm } from '../types';  // ← CORREGIDO: import type

interface Props {
  onRoomCreated: (roomId: string) => void;
}

const CreateRoom: React.FC<Props> = ({ onRoomCreated }) => {
  const [form, setForm] = useState<RoomForm>({
    name: '',
    pin: '',
    type: 'text'
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const API_BASE = import.meta.env.MODE === 'production'
        ? 'https://chat-espe-backend-production.up.railway.app'
        : '';

      const res = await axios.post(`${API_BASE}/api/admin/rooms`, form, {
        withCredentials: true,
        timeout: 5000
      });
      onRoomCreated(res.data.room_id);
      setForm({ name: '', pin: '', type: 'text' });
    } catch (err: unknown) {
      const error = err as AxiosError;
      alert('Error al crear sala');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card" style={{ maxWidth: '400px' }}>
      <h3 style={{ marginBottom: '20px', color: '#667eea' }}>
        Crear Nueva Sala
      </h3>
      <form onSubmit={handleSubmit}>
        <input
          placeholder="Nombre de la sala"
          value={form.name}
          onChange={e => setForm({ ...form, name: e.target.value })}
          required
          disabled={loading}
        />
        <input
          type="password"
          placeholder="PIN (mínimo 4 dígitos)"
          value={form.pin}
          onChange={e => setForm({ ...form, pin: e.target.value })}
          minLength={4}
          required
          disabled={loading}
        />
        <select
          value={form.type}
          onChange={e => setForm({ ...form, type: e.target.value as 'text' | 'multimedia' })}
          disabled={loading}
        >
          <option value="text">Solo Texto</option>
          <option value="multimedia">Multimedia (archivos)</option>
        </select>
        <button type="submit" disabled={loading}>
          {loading ? 'Creando...' : 'Crear Sala'}
        </button>
      </form>
    </div>
  );
};

export default CreateRoom;
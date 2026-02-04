import React, { useState } from 'react';
import axios, { AxiosError } from 'axios';
import { API_BASE_URL } from '../apiConfig';
import type { RoomForm } from '../types'; // Importa el tipo

// Define el tipo de objeto que App.tsx (el padre) espera
type CreatedRoomInfo = {
  id: string;
  pin: string;
};

// Define las props que recibe este componente
interface Props {
  onRoomCreated: (room: CreatedRoomInfo) => void;
}

const CreateRoom: React.FC<Props> = ({ onRoomCreated }) => {
  // Ahora incluimos el tipo de sala en el formulario
  const [form, setForm] = useState<RoomForm>({
    name: '',
    pin: '',
    type: 'text', // Valor por defecto
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const res = await axios.post(`${API_BASE_URL}/api/admin/rooms`, form, {
        withCredentials: true,
        timeout: 5000
      });

      // Creamos el objeto que App.tsx espera
      const roomInfo = {
        id: res.data.room_id, 
        pin: res.data.pin     
      };
      
      onRoomCreated(roomInfo); // <-- Envía el objeto completo

      setForm({ name: '', pin: '', type: 'text' }); // Resetea el formulario
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
      <h3 style={{ marginBottom: '20px', color: '#00c8a0', textAlign: 'center' }}>
        Crear Nueva Sala
      </h3>
      <form onSubmit={handleSubmit} className="create-room-form">
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
        
        {/* Selector de tipo de sala */}
        <select
          value={form.type}
          onChange={e => setForm({ ...form, type: e.target.value as 'text' | 'multimedia' })}
          disabled={loading}
        >
          <option value="text">📝 Sala de Texto</option>
          <option value="multimedia">🎬 Sala Multimedia</option>
        </select>
        
        <button type="submit" disabled={loading}>
          {loading ? 'Creando...' : 'Crear Sala'}
        </button>
      </form>
    </div>
  );
};

export default CreateRoom;
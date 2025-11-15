import React, { useState } from 'react';
import axios, { AxiosError } from 'axios';
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

// Función helper para obtener la URL del backend
const getApiBase = () => {
  return import.meta.env.MODE === 'production'
    ? 'https://chat-espe-backend-production.up.railway.app'
    : `http://${window.location.hostname}:5000`;
};

const CreateRoom: React.FC<Props> = ({ onRoomCreated }) => {
  // El 'type' ya no es necesario aquí
  const [form, setForm] = useState<Omit<RoomForm, 'type'>>({
    name: '',
    pin: '',
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const res = await axios.post(`${getApiBase()}/api/admin/rooms`, form, {
        withCredentials: true,
        timeout: 5000
      });

      // Creamos el objeto que App.tsx espera
      const roomInfo = {
        id: res.data.room_id, 
        pin: res.data.pin     
      };
      
      onRoomCreated(roomInfo); // <-- Envía el objeto completo

      setForm({ name: '', pin: '' }); // Resetea el formulario
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
      <h3 style={{ marginBottom: '20px', color: '#00c8a0' }}>
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
        
        {/* --- CAMPO <select> ELIMINADO --- */}
        
        <button type="submit" disabled={loading}>
          {loading ? 'Creando...' : 'Crear Sala'}
        </button>
      </form>
    </div>
  );
};

export default CreateRoom;
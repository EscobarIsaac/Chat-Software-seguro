import React, { useState, useEffect } from 'react';
import axios from 'axios';

// Define el tipo de dato que esperamos del backend
type RoomInfo = {
  id: string;
  name: string;
  type: 'text' | 'multimedia';
  userCount: number;
};

// Función para obtener la URL base de la API
const getApiBase = () => {
  return import.meta.env.MODE === 'production'
    ? 'https://chat-espe-backend-production.up.railway.app'
    : `http://${window.location.hostname}:5000`;
};

const AdminDashboard: React.FC = () => {
  const [rooms, setRooms] = useState<RoomInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Función para cargar los datos del dashboard
  const fetchDashboard = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${getApiBase()}/api/admin/dashboard`, {
        withCredentials: true,
      });
      setRooms(res.data);
      setError('');
    } catch (err) {
      console.error(err);
      setError('No se pudo cargar la lista de salas.');
    } finally {
      setLoading(false);
    }
  };

  // Cargar los datos cuando el componente se monta
  useEffect(() => {
    fetchDashboard();
  }, []);

  // Función para manejar la eliminación
  const handleDelete = async (roomId: string) => {
    if (!window.confirm(`¿Seguro que quieres eliminar la sala ${roomId}? Esta acción solo funcionará si la sala está vacía.`)) {
      return;
    }

    try {
      const res = await axios.delete(`${getApiBase()}/api/admin/rooms/${roomId}`, {
        withCredentials: true,
      });
      alert(res.data.message); // Alerta de éxito
      setRooms(prevRooms => prevRooms.filter(room => room.id !== roomId));
    } catch (err: any) {
      console.error(err);
      alert(`Error: ${err.response?.data?.error || 'No se pudo eliminar la sala'}`);
    }
  };

  if (loading) return <p>Cargando dashboard...</p>;
  if (error) return <p style={{ color: '#e53e3e' }}>{error}</p>;

  return (
    <div className="card">
      <h3 style={{ marginBottom: '20px', color: '#00c8a0' }}>Salas Activas</h3>
      <button onClick={fetchDashboard} style={{marginBottom: '20px', width: 'auto', padding: '10px 15px'}}>
        Refrescar Lista
      </button>
      
      <table className="dashboard-table">
        <thead>
          <tr>
            <th>Nombre</th>
            <th>ID de Sala</th>
            <th>Tipo</th>
            <th>Usuarios</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          {rooms.length === 0 ? (
            <tr>
              <td colSpan={5} style={{ textAlign: 'center' }}>No hay salas creadas.</td>
            </tr>
          ) : (
            rooms.map(room => (
              <tr key={room.id}>
                <td>{room.name}</td>
                <td><code>{room.id}</code></td>
                <td>{room.type}</td>
                <td>{room.userCount}</td>
                <td>
                  <button
                    className="danger-btn"
                    onClick={() => handleDelete(room.id)}
                    disabled={room.userCount > 0} 
                  >
                    Eliminar
                  </button>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
      <p style={{marginTop: '15px', fontSize: '12px', color: '#aaa'}}>
        * Solo puedes eliminar salas que tengan 0 usuarios.
      </p>
    </div>
  );
};

export default AdminDashboard;
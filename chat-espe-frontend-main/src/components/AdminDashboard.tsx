import React, { useState, useEffect } from 'react';
import axios from 'axios';

// Define el tipo de dato que esperamos del backend
type RoomInfo = {
  id: string;
  name: string;
  type: 'text' | 'multimedia';
  userCount: number;
  pin?: string; // PIN hasheado (no se muestra)
  pin_display?: string; // PIN en texto plano para el admin
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
      
      <div style={{ overflowX: 'auto' }}>
        <table className="dashboard-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ backgroundColor: '#2a2a2a' }}>
              <th style={{ padding: '12px 15px', textAlign: 'left', borderBottom: '2px solid #00c8a0' }}>Nombre</th>
              <th style={{ padding: '12px 15px', textAlign: 'left', borderBottom: '2px solid #00c8a0' }}>ID de Sala</th>
              <th style={{ padding: '12px 15px', textAlign: 'left', borderBottom: '2px solid #00c8a0' }}>PIN</th>
              <th style={{ padding: '12px 15px', textAlign: 'left', borderBottom: '2px solid #00c8a0' }}>Tipo</th>
              <th style={{ padding: '12px 15px', textAlign: 'center', borderBottom: '2px solid #00c8a0' }}>Usuarios</th>
              <th style={{ padding: '12px 15px', textAlign: 'center', borderBottom: '2px solid #00c8a0' }}>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {rooms.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ 
                  padding: '20px', 
                  textAlign: 'center', 
                  color: '#999',
                  fontStyle: 'italic'
                }}>
                  No hay salas creadas.
                </td>
              </tr>
            ) : (
              rooms.map(room => (
                <tr key={room.id} style={{ 
                  borderBottom: '1px solid #444',
                  transition: 'background-color 0.2s'
                }}>
                  <td style={{ 
                    padding: '12px 15px',
                    fontWeight: 'bold',
                    color: '#e0e0e0'
                  }}>
                    {room.name}
                  </td>
                  <td style={{ padding: '12px 15px' }}>
                    <code style={{
                      backgroundColor: '#1a1a1a',
                      padding: '4px 8px',
                      borderRadius: '4px',
                      color: '#00c8a0',
                      fontSize: '14px'
                    }}>
                      {room.id}
                    </code>
                  </td>
                  <td style={{ padding: '12px 15px' }}>
                    <span style={{
                      backgroundColor: '#2d3748',
                      color: '#ffd700',
                      padding: '4px 8px',
                      borderRadius: '4px',
                      fontSize: '14px',
                      fontFamily: 'monospace',
                      fontWeight: 'bold'
                    }}>
                      {(room as any).pin_display || '****'}
                    </span>
                  </td>
                  <td style={{ 
                    padding: '12px 15px',
                    textTransform: 'capitalize'
                  }}>
                    <span style={{
                      padding: '4px 12px',
                      borderRadius: '20px',
                      fontSize: '12px',
                      fontWeight: 'bold',
                      backgroundColor: room.type === 'multimedia' ? '#4c1d95' : '#1e40af',
                      color: 'white'
                    }}>
                      {room.type}
                    </span>
                  </td>
                  <td style={{ 
                    padding: '12px 15px', 
                    textAlign: 'center',
                    fontWeight: 'bold',
                    color: room.userCount > 0 ? '#00c8a0' : '#999'
                  }}>
                    {room.userCount}
                  </td>
                  <td style={{ padding: '12px 15px', textAlign: 'center' }}>
                    <button
                      className="danger-btn"
                      onClick={() => handleDelete(room.id)}
                      disabled={room.userCount > 0}
                      style={{
                        padding: '6px 12px',
                        fontSize: '12px',
                        borderRadius: '6px',
                        opacity: room.userCount > 0 ? 0.5 : 1,
                        cursor: room.userCount > 0 ? 'not-allowed' : 'pointer'
                      }}
                    >
                      ELIMINAR
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      <p style={{marginTop: '15px', fontSize: '12px', color: '#aaa'}}>
        * Solo puedes eliminar salas que tengan 0 usuarios.
      </p>
    </div>
  );
};

export default AdminDashboard;
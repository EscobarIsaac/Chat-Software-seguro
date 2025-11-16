import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import CreateRoom from '../components/CreateRoom';
import AdminDashboard from '../components/AdminDashboard';

// Define un tipo para la sala creada
type CreatedRoomInfo = {
  id: string;
  pin: string;
};

const AdminPage: React.FC = () => {
  const navigate = useNavigate();
  const [createdRoom, setCreatedRoom] = useState<CreatedRoomInfo | null>(null);

  const handleRoomCreated = (room: CreatedRoomInfo) => {
    setCreatedRoom(room);
    alert(`✅ Sala creada exitosamente!\n\nID: ${room.id}\nPIN: ${room.pin}\n\n¡Comparte estos datos con los usuarios!`);
  };

  const handleLogout = () => {
    navigate('/');
  };

  return (
    <div className="container">
      <div style={{ textAlign: 'center', marginBottom: '30px' }}>
        <h2 style={{ color: '#00c8a0', marginBottom: '10px' }}>👑 Panel de Administración</h2>
        <button 
          onClick={handleLogout} 
          className="danger-btn" 
          style={{ 
            width: 'auto', 
            padding: '10px 20px', 
            marginBottom: '20px',
            borderRadius: '25px'
          }}
        >
          ← Volver al Inicio
        </button>
        
        {/* Recuadro verde que muestra ID y PIN */}
        {createdRoom && (
          <div style={{
            background: '#005f50',
            color: '#e0e0e0',
            padding: '15px',
            borderRadius: '10px',
            marginBottom: '20px',
            border: '2px solid #00c8a0'
          }}>
            <strong>Última sala creada:</strong><br/>
            <span style={{ fontSize: '1.5rem', color: '#00c8a0', display: 'block' }}>
              ID: {createdRoom.id}
            </span>
            <span style={{ fontSize: '1.5rem', color: '#e0e0e0', display: 'block' }}>
              PIN: {createdRoom.pin}
            </span>
          </div>
        )}
      </div>
      
      {/* Layout de dos columnas para el admin */}
      <div className="flex">
        <div style={{ flex: 1, minWidth: '300px' }}>
          <CreateRoom onRoomCreated={handleRoomCreated} />
        </div>
        
        <div style={{ flex: 2, minWidth: '400px' }}>
          <AdminDashboard />
        </div>
      </div>
    </div>
  );
};

export default AdminPage;
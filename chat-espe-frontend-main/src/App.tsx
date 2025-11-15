import React, { useState } from 'react';
import AdminLogin from './components/AdminLogin';
import CreateRoom from './components/CreateRoom';
import UserJoin from './pages/UserJoin';

const App: React.FC = () => {
  const [isAdmin, setIsAdmin] = useState(false);
  const [showCreatedRoomId, setShowCreatedRoomId] = useState('');

  const handleLogin = () => {
    setIsAdmin(true);
  };

  const handleRoomCreated = (roomId: string) => {
    setShowCreatedRoomId(roomId);
    alert(`✅ Sala creada exitosamente!\n\nID: ${roomId}\n\n¡Comparte este ID y PIN con los usuarios!`);
  };

  const handleLogout = () => {
    setIsAdmin(false);
    setShowCreatedRoomId('');
  };

  if (!isAdmin) {
    return (
      <div className="container">
        <div className="header">
          <h1>💬 Chat Seguro ESPE</h1>
          <p style={{ fontSize: '1.2rem' }}>Sistema de Salas Seguras en Tiempo Real</p>
        </div>
        <div className="flex">
          <AdminLogin onLogin={handleLogin} />
          <UserJoin />
        </div>
      </div>
    );
  }

  return (
    <div className="container">
      <div style={{ textAlign: 'center', marginBottom: '30px' }}>
        <h2 style={{ color: '#667eea', marginBottom: '10px' }}>👑 Panel de Administración</h2>
        <button onClick={handleLogout} className="danger" style={{ 
          width: 'auto', 
          padding: '10px 20px', 
          marginBottom: '20px',
          borderRadius: '25px'
        }}>
          Cerrar Sesión
        </button>
        {showCreatedRoomId && (
          <div style={{
            background: '#d4edda',
            color: '#155724',
            padding: '15px',
            borderRadius: '10px',
            marginBottom: '20px',
            border: '2px solid #c3e6cb'
          }}>
            <strong>Última sala creada:</strong><br/>
            <span style={{ fontSize: '1.5rem', color: '#28a745' }}>
              {showCreatedRoomId}
            </span>
          </div>
        )}
      </div>
      <CreateRoom onRoomCreated={handleRoomCreated} />
    </div>
  );
};

export default App;
import React, { useState } from 'react';
import AdminLogin from './components/AdminLogin';
import CreateRoom from './components/CreateRoom';
import UserJoin from './pages/UserJoin';
// 1. IMPORTA EL NUEVO COMPONENTE
import AdminDashboard from './components/AdminDashboard';
import './index.css'; // Asegúrate de importar tus estilos

// Define un tipo para la sala creada
type CreatedRoomInfo = {
  id: string;
  pin: string;
};

const App: React.FC = () => {
  const [isAdmin, setIsAdmin] = useState(false);
  
  // El estado ahora guarda el objeto completo (o null)
  const [createdRoom, setCreatedRoom] = useState<CreatedRoomInfo | null>(null);

  const handleLogin = () => {
    setIsAdmin(true);
  };

  // Esta función ahora recibe el objeto completo
  const handleRoomCreated = (room: CreatedRoomInfo) => {
    setCreatedRoom(room);
    
    // El alert ahora muestra el ID y el PIN
    alert(`✅ Sala creada exitosamente!\n\nID: ${room.id}\nPIN: ${room.pin}\n\n¡Comparte estos datos con los usuarios!`);
  };

  const handleLogout = () => {
    setIsAdmin(false);
    setCreatedRoom(null); // Resetea el objeto
  };

  // --- VISTA DE USUARIO (SI NO ES ADMIN) ---
  if (!isAdmin) {
    return (
      <div className="container">
        <div className="header">
          <h1>Chat para amigos</h1>
          <p style={{ fontSize: '1.2rem' }}>Sala de chat seguro</p>
        </div>
        <div className="flex">
          <AdminLogin onLogin={handleLogin} />
          <UserJoin />
        </div>
      </div>
    );
  }

  // --- VISTA DE ADMINISTRADOR ---
  return (
    <div className="container">
      <div style={{ textAlign: 'center', marginBottom: '30px' }}>
        <h2 style={{ color: '#00c8a0', marginBottom: '10px' }}>👑 Panel de Administración</h2>
        <button onClick={handleLogout} className="danger-btn" style={{ 
          width: 'auto', 
          padding: '10px 20px', 
          marginBottom: '20px',
          borderRadius: '25px'
        }}>
          Cerrar Sesión
        </button>
        
        {/* Recuadro verde que muestra ID y PIN */}
        {createdRoom && (
          <div style={{
            background: '#005f50', // Verde oscuro (modo oscuro)
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
        {/* Columna para crear sala */}
        <div style={{ flex: 1, minWidth: '300px' }}>
          <CreateRoom onRoomCreated={handleRoomCreated} />
        </div>
        
        {/* Columna para ver salas */}
        <div style={{ flex: 2, minWidth: '400px' }}>
          <AdminDashboard />
        </div>
      </div>
      
    </div>
  );
};

export default App;
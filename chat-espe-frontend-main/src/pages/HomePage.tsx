import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AdminLogin from '../components/AdminLogin';
import UserJoin from './UserJoin';

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  
  // Verificar si el acceso de admin debe mostrarse
  const showAdminAccess = import.meta.env.VITE_SHOW_ADMIN_ACCESS === 'true';
  const appTitle = import.meta.env.VITE_APP_TITLE || 'Chat Seguro';

  const handleAdminLogin = () => {
    navigate('/admin');
  };

  return (
    <div className="container">
      <div className="header">
        <h1>{appTitle}</h1>
        <p style={{ fontSize: '1.2rem' }}>Sala de chat seguro</p>
      </div>
      
      <div className={showAdminAccess ? "flex" : "single-panel"}>
        {/* Solo mostrar AdminLogin en desarrollo */}
        {showAdminAccess && <AdminLogin onLogin={handleAdminLogin} />}
        
        {/* UserJoin siempre visible pero centrado si no hay admin */}
        <UserJoin />
      </div>
      
      {/* Acceso secreto de admin en producción (opcional) */}
      {!showAdminAccess && (
        <div style={{ textAlign: 'center', marginTop: '40px' }}>
          <button
            onClick={() => navigate('/admin/login')}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#333',
              fontSize: '10px',
              cursor: 'pointer',
              opacity: 0.3
            }}
            title="Acceso administrativo"
          >
            •
          </button>
        </div>
      )}
    </div>
  );
};

export default HomePage;
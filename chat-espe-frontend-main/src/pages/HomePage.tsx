import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AdminLogin from '../components/AdminLogin';
import UserJoin from './UserJoin';

const HomePage: React.FC = () => {
  const navigate = useNavigate();

  const handleAdminLogin = () => {
    navigate('/admin');
  };

  return (
    <div className="container">
      <div className="header">
        <h1>Chat para amigos</h1>
        <p style={{ fontSize: '1.2rem' }}>Sala de chat seguro</p>
      </div>
      <div className="flex">
        <AdminLogin onLogin={handleAdminLogin} />
        <UserJoin />
      </div>
    </div>
  );
};

export default HomePage;
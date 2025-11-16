import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import ChatRoom from '../components/ChatRoom';

const ChatRoomPage: React.FC = () => {
  const { roomId } = useParams<{ roomId: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  
  // Obtener datos del estado de la navegación
  const { pin, nickname } = location.state || {};

  useEffect(() => {
    // Si no hay datos de pin/nickname, redirigir al inicio
    if (!roomId || !pin || !nickname) {
      navigate('/');
    }
  }, [roomId, pin, nickname, navigate]);

  const handleLeaveRoom = () => {
    // Confirmación antes de salir
    if (window.confirm('¿Estás seguro de que quieres salir de la sala?')) {
      navigate('/');
    }
  };

  if (!roomId || !pin || !nickname) {
    return (
      <div className="container">
        <div className="card">
          <h2>Error</h2>
          <p>No se encontraron los datos de la sala. Regresando al inicio...</p>
        </div>
      </div>
    );
  }

  return (
    <div style={{ position: 'relative' }}>
      {/* Botón de salir flotante */}
      <button
        onClick={handleLeaveRoom}
        className="floating-btn"
      >
        ← Salir de la Sala
      </button>
      
      <ChatRoom roomId={roomId} pin={pin} nickname={nickname} />
    </div>
  );
};

export default ChatRoomPage;
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const UserJoin: React.FC = () => {
  const [roomId, setRoomId] = useState('');
  const [pin, setPin] = useState('');
  const [nickname, setNickname] = useState('');
  const navigate = useNavigate();

  const handleJoin = (e: React.FormEvent) => {
    e.preventDefault();
    if (roomId && pin.length >= 4 && nickname) {
      // Navegar a la sala de chat con los datos
      navigate(`/chat/${roomId}`, {
        state: { pin, nickname }
      });
    }
  };

  return (
    <div className="card user-join-card">
      <h2 className="user-join-title">
        🚪 Unirse a Sala
      </h2>
      <form onSubmit={handleJoin} className="user-join-form">
        <div className="input-group">
          <label htmlFor="roomId">ID de la sala</label>
          <input
            id="roomId"
            placeholder="Ingresa el ID de 8 caracteres"
            value={roomId}
            onChange={e => setRoomId(e.target.value)}
            maxLength={8}
            required
          />
        </div>
        
        <div className="input-group">
          <label htmlFor="pin">PIN de acceso</label>
          <input
            id="pin"
            type="password"
            placeholder="PIN de 4+ dígitos"
            value={pin}
            onChange={e => setPin(e.target.value)}
            minLength={4}
            required
          />
        </div>
        
        <div className="input-group">
          <label htmlFor="nickname">Tu nombre</label>
          <input
            id="nickname"
            placeholder="¿Cómo te llamas?"
            value={nickname}
            onChange={e => setNickname(e.target.value)}
            maxLength={20}
            required
          />
        </div>
        
        <button type="submit" className="join-button">
          🚀 Unirse al Chat
        </button>
      </form>
    </div>
  );
};

export default UserJoin;
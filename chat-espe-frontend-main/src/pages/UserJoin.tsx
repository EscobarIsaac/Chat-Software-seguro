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
    <div className="card" style={{ maxWidth: '400px', flex: 1 }}>
      <h2 style={{ marginBottom: '20px', color: '#667eea', textAlign: 'center' }}>
        🚪 Unirse a Sala
      </h2>
      <form onSubmit={handleJoin}>
        <input
          placeholder="ID de la sala (8 caracteres)"
          value={roomId}
          onChange={e => setRoomId(e.target.value)}  // ← SIN toUpperCase
          maxLength={8}
          required
        />
        <input
          type="password"
          placeholder="PIN (4+ dígitos)"
          value={pin}
          onChange={e => setPin(e.target.value)}
          minLength={4}
          required
        />
        <input
          placeholder="Tu nickname"
          value={nickname}
          onChange={e => setNickname(e.target.value)}
          maxLength={20}
          required
        />
        <button type="submit">🚀 Unirse al Chat</button>
      </form>
    </div>
  );
};

export default UserJoin;
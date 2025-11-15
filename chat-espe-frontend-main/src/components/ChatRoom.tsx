import React, { useState, useEffect, useRef, useCallback } from 'react';
import socket from '../socket';
import type { Message } from '../types';

interface Props {
  roomId: string;
  pin: string;
  nickname: string;
}

const ChatRoom: React.FC<Props> = ({ roomId, pin, nickname }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [users, setUsers] = useState<string[]>([]);
  const [input, setInput] = useState('');
  const [connected, setConnected] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    socket.connect();
    socket.emit('join_room', { room_id: roomId, pin, nickname });

    socket.on('connect', () => setConnected(true));
    socket.on('disconnect', () => setConnected(false));

    socket.on('message', (msg: Omit<Message, 'type'>) => {
      setMessages(prev => [...prev, { ...msg, type: 'text' }]);
    });

    socket.on('file', (file: Omit<Message, 'type'>) => {
      setMessages(prev => [...prev, { ...file, type: 'file' }]);
    });

    socket.on('user_list', setUsers);
    socket.on('error', (data: { msg: string }) => alert(data.msg));
    socket.on('joined', () => console.log('Unido a la sala'));

    return () => {
      socket.off('connect');
      socket.off('disconnect');
      socket.off('message');
      socket.off('file');
      socket.off('user_list');
      socket.off('error');
      socket.off('joined');
      socket.disconnect();
    };
  }, [roomId, pin, nickname, scrollToBottom]);

  useEffect(scrollToBottom, [scrollToBottom]);

  const sendMessage = () => {
    if (!input.trim() || !connected) return;
    socket.emit('message', {
      msg: input,
      timestamp: new Date().toISOString()
    });
    setInput('');
  };

  const sendFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !connected) return;
    
    if (file.size > 10 * 1024 * 1024) {
      alert('Archivo demasiado grande (máx 10MB)');
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      socket.emit('file', {
        file: (reader.result as string).split(',')[1],
        filename: file.name,
        filetype: file.type,
        timestamp: new Date().toISOString()
      });
    };
    reader.readAsDataURL(file);
    e.target.value = ''; // Reset input
  };

  return (
    <div className="container">
      <div className="card">
        <div className="chat-header">
          🗨️ Sala: <strong>{roomId}</strong> | 
          👤 <strong>{nickname}</strong> | 
          📡 {connected ? '🟢 Conectado' : '🔴 Desconectado'} | 
          👥 {users.length} usuarios
        </div>
        <div className="user-list">
          Conectados: {users.join(', ') || 'Ninguno'}
        </div>
      </div>

      <div className="chat-container">
        <div className="chat-messages">
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`message ${msg.username === nickname ? 'own' : 'other'}`}
            >
              <strong>{msg.username}</strong>
              {msg.type === 'text' ? (
                <span style={{ display: 'block', marginTop: '5px' }}>{msg.msg}</span>
              ) : (
                <a
                  href={`data:${msg.filetype};base64,${msg.file}`}
                  download={msg.filename}
                  className="file-link"
                  style={{ display: 'block', marginTop: '5px' }}
                >
                  📎 {msg.filename} ({(msg.file?.length || 0) / 1024 | 0} KB)
                </a>
              )}
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        <div className="chat-input">
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyPress={e => e.key === 'Enter' && sendMessage()}
            placeholder="Escribe un mensaje... (Enter para enviar)"
            disabled={!connected}
          />
          <button onClick={sendMessage} disabled={!connected || !input.trim()}>
            Enviar
          </button>
          <button
            type="button"
            className="secondary"
            onClick={() => fileInputRef.current?.click()}
            disabled={!connected}
          >
            📎 Archivo
          </button>
        </div>
      </div>
      
      <input
        type="file"
        ref={fileInputRef}
        onChange={sendFile}
        accept="image/*,.pdf,.doc,.docx,.txt"
        style={{ display: 'none' }}
      />
    </div>
  );
};

export default ChatRoom;
// src/components/ChatRoom.tsx (COMPLETO Y CORREGIDO)
import React, { useState, useEffect, useRef, useCallback } from 'react';
import socket from '../socket';
import type { Message } from '../types';

interface Props {
  roomId: string;
  pin: string;
  nickname: string;
  onLeaveRoom?: () => void;
}

const ChatRoom: React.FC<Props> = ({ roomId, pin, nickname, onLeaveRoom }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [users, setUsers] = useState<string[]>([]);
  const [input, setInput] = useState('');
  const [connected, setConnected] = useState(false);
  const [isValidating, setIsValidating] = useState(false);
  const [validationResult, setValidationResult] = useState<{
    show: boolean;
    success: boolean;
    message: string;
    fileName?: string;
  }>({ show: false, success: false, message: '' });
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

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
  }, [roomId, pin, nickname]); // Dependencias originales (correctas)

  // ARREGLO 2: El 'scroll' se ejecuta CADA VEZ que el array 'messages' cambia.
  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const sendMessage = () => {
    if (!input.trim() || !connected) return;
    
    // ARREGLO 1: Añade 'username: nickname' al emitir
    socket.emit('message', {
      msg: input,
      username: nickname, // <-- ¡ARREGLO AÑADIDO!
      timestamp: new Date().toISOString()
    });
    setInput('');
  };

  // Función para manejar selección de archivos
  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !connected) return;

    setIsValidating(true);

    // Validación básica del lado cliente
    const maxSize = 50 * 1024 * 1024; // 50MB
    if (file.size > maxSize) {
      showValidationMessage(false, 'Archivo muy grande (máx 50MB)');
      setIsValidating(false);
      return;
    }

    try {
      // Enviar archivo al backend para validación
      const formData = new FormData();
      formData.append('file', file);
      formData.append('originalName', file.name);

      const response = await fetch('http://localhost:5000/api/upload-file', {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();

      if (response.ok && result.success && result.fileInfo) {
        // Archivo válido - mostrar popup verde
        showValidationMessage(true, `✅ ${result.message}`);
        
        // Enviar archivo al chat después de la validación
        socket.emit('file', {
          file: result.fileInfo.data,
          filename: result.fileInfo.name,
          filetype: result.fileInfo.type,
          username: nickname,
          timestamp: new Date().toISOString(),
          hash: result.fileInfo.hash
        });
      } else {
        // Archivo rechazado - mostrar popup rojo con razón específica
        const errorMessage = result.message || result.error || 'Error de validación desconocido';
        showValidationMessage(false, `❌ ${errorMessage}`);
      }
    } catch (error) {
      showValidationMessage(false, 'Error al validar archivo');
      console.error('Error uploading file:', error);
    }

    setIsValidating(false);
    // Limpiar input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Función para mostrar mensaje de validación temporal
  const showValidationMessage = (success: boolean, message: string) => {
    setValidationResult({ show: true, success, message });
    
    // Ocultar mensaje después de 3 segundos
    setTimeout(() => {
      setValidationResult(prev => ({ ...prev, show: false }));
    }, 3000);
  };

  return (
    <div className="container">
      {/* Mostrar resultado de validación temporal */}
      {validationResult.show && (
        <div className={`validation-popup ${validationResult.success ? 'validation-success' : 'validation-error'}`}>
          <div className="validation-content">
            <span className="validation-icon">
              {validationResult.success ? '✅' : '❌'}
            </span>
            <span className="validation-message">
              {validationResult.message}
            </span>
          </div>
        </div>
      )}
      
      {/* Indicador de validación en progreso */}
      {isValidating && (
        <div className="validation-popup validation-loading">
          <div className="validation-content">
            <span className="validation-spinner">🔄</span>
            <span className="validation-message">Validando archivo...</span>
          </div>
        </div>
      )}
      
      <div className="chat-container">
        <div className="chat-header">
          <div className="header-left">
            <div>
              🗨️ Sala: <strong className="room-id">{roomId}</strong>
            </div>
            <div className="status">
              👤 <strong>{nickname}</strong> | 
              📡 {connected ? '🟢 Conectado' : '🔴 Desconectado'} | 
              👥 {users.length} usuarios
            </div>
          </div>
          {onLeaveRoom && (
            <button 
              onClick={onLeaveRoom}
              className="leave-room-btn"
              title="Salir de la sala"
            >
              ← Salir
            </button>
          )}
        </div>
        
        <div className="user-list">
          Conectados: {users.join(', ') || 'Ninguno'}
        </div>

        <div className="chat-messages">
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`message ${msg.username === nickname ? 'own' : 'other'}`}
            >
              <div className="username">{msg.username}</div>
              {msg.type === 'text' ? (
                <div style={{ marginTop: '4px' }}>{msg.msg}</div>
              ) : (
                <div className="file-message" style={{ marginTop: '4px' }}>
                  <span className="file-icon">📎</span>
                  <a
                    href={`data:${msg.filetype};base64,${msg.file}`}
                    download={msg.filename}
                    className="file-link"
                  >
                    {msg.filename}
                  </a>
                  <div style={{ fontSize: '11px', color: '#999', marginTop: '4px' }}>
                    {((msg.file?.length || 0) * 0.75 / 1024).toFixed(1)} KB
                  </div>
                </div>
              )}
              <div className="timestamp">
                {new Date(msg.timestamp).toLocaleTimeString('es-ES', { 
                  hour: '2-digit', 
                  minute: '2-digit' 
                })}
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        <div className="chat-input-container">
          <input
            className="chat-input"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyPress={e => e.key === 'Enter' && sendMessage()}
            placeholder="Escribe un mensaje... (Enter para enviar)"
            disabled={!connected}
          />
          <div className="input-actions">
            <button
              className="input-btn send-btn"
              onClick={sendMessage}
              disabled={!connected || !input.trim()}
              title="Enviar mensaje"
            >
              ➤
            </button>
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileSelect}
              style={{ display: 'none' }}
              accept="image/*,audio/*,video/*,.pdf,.txt"
              disabled={!connected}
            />
            <button
              className="input-btn file-btn"
              onClick={() => fileInputRef.current?.click()}
              disabled={!connected || isValidating}
              title="Adjuntar archivo"
            >
              📎
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatRoom;
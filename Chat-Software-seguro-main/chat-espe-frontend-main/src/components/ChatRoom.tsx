// src/components/ChatRoom.tsx (COMPLETO Y CORREGIDO)
import React, { useState, useEffect, useRef, useCallback } from 'react';
import socket from '../socket';
import { API_BASE_URL } from '../apiConfig';
import type { Message } from '../types';
import { buildAuthHeaders, getBiometricToken } from '../services/biometricToken';

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
  const [previewFile, setPreviewFile] = useState<{
    url: string;
    type: string;
    name: string;
  } | null>(null);
  const [pdfThumbnails, setPdfThumbnails] = useState<Map<number, string>>(new Map());
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    const targetRoomIdentifier = roomId.trim();
    const biometricToken = getBiometricToken();
    if (!biometricToken) {
      alert('Falta biometricToken. Inicia sesión en el gateway antes de unirte a una sala.');
      return;
    }

    socket.auth = { biometricToken };
    socket.connect();
    socket.emit('join_room', {
      room_id: targetRoomIdentifier,
      pin,
      nickname,
      biometricToken
    });

    socket.on('connect', () => setConnected(true));
    socket.on('disconnect', () => setConnected(false));

    socket.on('message', (msg: Omit<Message, 'type'>) => {
      console.log('Mensaje recibido:', msg, 'isAdmin:', msg.isAdmin);
      setMessages(prev => [...prev, { ...msg, type: 'text' as const }]);
    });

    socket.on('file', (file: Omit<Message, 'type'>) => {
      console.log('Archivo recibido:', file, 'isAdmin:', file.isAdmin);
      setMessages(prev => {
        const newMessages = [...prev, { ...file, type: 'file' as const }];
        
        // Si es PDF, generar thumbnail
        if (file.filetype === 'application/pdf' && file.file) {
          const messageIndex = newMessages.length - 1;
          generatePdfThumbnail(file.file, messageIndex);
        }
        
        return newMessages;
      });
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

      const headers = buildAuthHeaders();
      if (!headers.Authorization) {
        showValidationMessage(false, 'Debes iniciar sesión en el gateway biométrico antes de subir archivos.');
        setIsValidating(false);
        return;
      }

      const response = await fetch(`${API_BASE_URL}/api/upload-file`, {
        method: 'POST',
        body: formData,
        headers,
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

  // Función para abrir preview de archivo
  const openFilePreview = (fileData: string, fileType: string, fileName: string) => {
    const url = `data:${fileType};base64,${fileData}`;
    setPreviewFile({ url, type: fileType, name: fileName });
    console.log('Abriendo preview:', { fileType, fileName, urlLength: url.length });
  };

  // Función para cerrar preview
  const closeFilePreview = () => {
    setPreviewFile(null);
  };

  // Función para verificar si es imagen
  const isImage = (mimeType: string) => {
    return mimeType.startsWith('image/');
  };

  // Función para verificar si es PDF
  const isPDF = (mimeType: string) => {
    return mimeType === 'application/pdf';
  };

  // Función para generar thumbnail de PDF usando objeto embed temporal
  const generatePdfThumbnail = useCallback(async (base64Data: string, messageIndex: number) => {
    try {
      // Si ya existe el thumbnail, no lo regeneramos
      if (pdfThumbnails.has(messageIndex)) {
        return;
      }

      const dataUrl = `data:application/pdf;base64,${base64Data}`;
      
      // Crear un iframe oculto para cargar el PDF
      const iframe = document.createElement('iframe');
      iframe.style.position = 'fixed';
      iframe.style.top = '-9999px';
      iframe.style.width = '800px';
      iframe.style.height = '1000px';
      document.body.appendChild(iframe);
      
      iframe.src = dataUrl;
      
      // Esperar a que se cargue
      await new Promise((resolve) => {
        iframe.onload = resolve;
        setTimeout(resolve, 2000); // Timeout de seguridad
      });
      
      // Crear thumbnail usando el PDF embebido
      // Por simplicidad, usamos la URL del PDF directamente
      setPdfThumbnails(prev => new Map(prev).set(messageIndex, dataUrl));
      
      // Limpiar
      document.body.removeChild(iframe);
    } catch (error) {
      console.error('Error generando thumbnail de PDF:', error);
    }
  }, [pdfThumbnails]);

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
          {messages.map((msg, i) => {
            const isAdminMsg = msg.isAdmin === true;
            console.log(`Mensaje #${i}:`, msg.username, 'isAdmin:', msg.isAdmin, 'aplicará clase:', isAdminMsg);
            return (
              <div
                key={i}
                className={`message ${msg.username === nickname ? 'own' : 'other'}`}
              >
                <div className={`username ${isAdminMsg ? 'admin-username' : ''}`}>
                  {msg.username}
                </div>
              {msg.type === 'text' ? (
                <div style={{ marginTop: '4px' }}>{msg.msg}</div>
              ) : (
                <div className="file-message" style={{ marginTop: '4px' }}>
                  {/* Previsualización de imagen */}
                  {msg.filetype && isImage(msg.filetype) && msg.file && (
                    <div 
                      className="file-preview-thumbnail"
                      onClick={() => openFilePreview(msg.file!, msg.filetype!, msg.filename || 'image')}
                    >
                      <img 
                        src={`data:${msg.filetype};base64,${msg.file}`}
                        alt={msg.filename}
                        className="preview-image"
                      />
                      <div className="preview-overlay">
                        <span>👁️ Ver imagen completa</span>
                      </div>
                    </div>
                  )}
                  
                  {/* Previsualización de PDF */}
                  {msg.filetype && isPDF(msg.filetype) && msg.file && (
                    <div 
                      className="file-preview-thumbnail pdf-preview-embed"
                      onClick={() => openFilePreview(msg.file!, msg.filetype!, msg.filename || 'document.pdf')}
                    >
                      <div className="pdf-embed-container">
                        <iframe
                          src={`data:${msg.filetype};base64,${msg.file}#page=1&zoom=50&toolbar=0&navpanes=0&scrollbar=0&view=FitH`}
                          className="pdf-embed-preview"
                          title={`Preview: ${msg.filename}`}
                        />
                        <div className="pdf-page-indicator">
                          <span>📄 {msg.filename}</span>
                        </div>
                      </div>
                      <div className="preview-overlay">
                        <span>👁️ Ver PDF completo</span>
                      </div>
                    </div>
                  )}
                  
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
          );
          })}
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

      {/* Modal de previsualización */}
      {previewFile && (
        <div className="preview-modal" onClick={closeFilePreview}>
          <div className="preview-modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="preview-close-btn" onClick={closeFilePreview}>
              ✕
            </button>
            <div className="preview-header">
              <h3>{previewFile.name}</h3>
              <a
                href={previewFile.url}
                download={previewFile.name}
                className="preview-download-btn"
              >
                ⬇️ Descargar
              </a>
            </div>
            <div className="preview-body">
              {isImage(previewFile.type) ? (
                <img src={previewFile.url} alt={previewFile.name} className="preview-full-image" />
              ) : isPDF(previewFile.type) ? (
                <iframe
                  src={`${previewFile.url}#toolbar=1&navpanes=1&scrollbar=1`}
                  title={previewFile.name}
                  className="preview-pdf-iframe"
                />
              ) : (
                <div className="preview-unsupported">
                  <p>Vista previa no disponible para este tipo de archivo</p>
                  <a href={previewFile.url} download={previewFile.name} className="preview-download-link">
                    Descargar archivo
                  </a>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatRoom;
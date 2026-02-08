import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import UserJoin from './UserJoin';
import { openBiometricVerification, getTokenClaims, getBiometricToken, subscribeToTokenChanges, buildAuthHeaders, clearBiometricToken } from '../services/biometricToken';
import { API_BASE_URL, GATEWAY_BASE_URL } from '../apiConfig';

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const appMode = import.meta.env.VITE_MODE || (import.meta.env.DEV ? 'development' : 'production');
  const isProd = appMode === 'production';
  const appTitle = import.meta.env.VITE_APP_TITLE || 'Chat Seguro';

  const [username, setUsername] = useState('');
  const [claimsRole, setClaimsRole] = useState<string | null>(null);
  const [claimsUsername, setClaimsUsername] = useState<string | null>(null);
  const [hasLocalToken, setHasLocalToken] = useState<boolean>(false);
  const [loginError, setLoginError] = useState<string>('');

  // Validación central reutilizable; se define antes de efectos para evitar TDZ
  const validateToken = useCallback((userFromInput?: string, opts: { forceNavigate?: boolean } = {}) => {
    setLoginError('');
    const token = getBiometricToken();
    const trimmedInput = (userFromInput || '').trim();
    try {
      console.log('[HomePage] validateToken biometricToken actual:', token);
    } catch {
      // ignorar errores de logging
    }

    if (!token) {
      if (!trimmedInput) {
        setLoginError('Escribe tu usuario para continuar.');
        return;
      }
      // No hay token local: abrir gateway solo con login
      openBiometricVerification(trimmedInput, 'login', 'cliente', { loginOnly: true });
      return;
    }

    // Verificar que el token pertenezca al usuario ingresado
    const claims = getTokenClaims();
    const tokenUser = (claims?.username || '').trim();
    const effectiveUser = trimmedInput || tokenUser;

    if (!effectiveUser) {
      setLoginError('Escribe tu usuario para continuar.');
      return;
    }

    if (tokenUser && trimmedInput && tokenUser !== trimmedInput) {
      // Token no pertenece a este usuario: redirigir a login-only para que genere uno nuevo
      openBiometricVerification(trimmedInput, 'login', 'cliente', { loginOnly: true });
      setLoginError('');
      return;
    }

    fetch(`${API_BASE_URL}/api/biometric/whoami`, {
      method: 'GET',
      headers: buildAuthHeaders(),
      credentials: 'include'
    })
      .then(async res => {
        const data = await res.json().catch(() => ({}));
        if (!res.ok || !data.active) {
          if (effectiveUser) {
            alert(data.error || 'El biometricToken no es válido o expiró. Se abrirá de nuevo la verificación biométrica.');
            openBiometricVerification(effectiveUser, 'login');
          } else {
            alert(data.error || 'El biometricToken no es válido. Vuelve a verificar en el gateway.');
          }
          return;
        }
        const nextClaims = data.claims || getTokenClaims() || {};
        const nextRole = (nextClaims.role || 'cliente').trim() || 'cliente';
        const nextUsername = (nextClaims.username || effectiveUser).trim() || effectiveUser;
        setClaimsRole(nextRole);
        setClaimsUsername(nextUsername || null);
        setUsername(nextUsername);
        setLoginError('');
        try {
          sessionStorage.removeItem('biometricLoggedOut');
        } catch {
          // ignorar errores
        }

        // Navegar según rol después de validar correctamente
        if (nextRole === 'admin') {
          navigate('/admin');
        }
      })
      .catch(err => {
        console.error('Error al validar token biométrico:', err);
        alert('No se pudo validar el biometricToken contra el servidor.');
      });
  }, [navigate]);

  useEffect(() => {
    if (!isProd) return;
    let loggedOut = false;
    try {
      loggedOut = sessionStorage.getItem('biometricLoggedOut') === '1';
    } catch {
      // ignorar errores de almacenamiento
    }

    const claims = getTokenClaims();
    if (claims && !loggedOut) {
      // Solo precargamos el usuario si existe token local, pero no asumimos rol hasta validar
      const currentUser = (claims.username || '').trim();
      setUsername(currentUser);
      setHasLocalToken(true);
    } else {
      // Aunque estemos "deslogueados", detectamos si hay token local para poder revalidar
      const token = getBiometricToken();
      setHasLocalToken(!!token);
    }

    const unsubscribe = subscribeToTokenChanges(() => {
      const nextClaims = getTokenClaims();
      if (nextClaims) {
        const nextUser = (nextClaims.username || '').trim();
        setUsername(nextUser);
        setHasLocalToken(true);
        validateToken(nextUser, { forceNavigate: true });
      } else {
        setHasLocalToken(false);
      }
    });

    return unsubscribe;
  }, [isProd, validateToken]);

  const handleValidateToken = () => validateToken(username);

  const handleLogout = () => {
    clearBiometricToken();
    try {
      sessionStorage.setItem('biometricLoggedOut', '1');
    } catch {
      // ignorar errores de almacenamiento
    }
    setClaimsRole(null);
    setClaimsUsername(null);
    setUsername('');
    setHasLocalToken(false);
  };

  return (
    <div className="container">
      <div className="header">
        <h1>{appTitle}</h1>
        <p style={{ fontSize: '1.2rem' }}>Sala de chat seguro</p>
      </div>
      {isProd ? (
        <>
          {!claimsRole && (
            <div className="single-panel">
              <div className="card" style={{ maxWidth: '400px', margin: '0 auto' }}>
                <h2 style={{ marginBottom: '20px', color: '#00c8a0', textAlign: 'center' }}>
                  🔐 Iniciar sesión biométrica
                </h2>
                <p style={{ fontSize: '0.9rem', color: '#aaa', marginBottom: '10px' }}>
                  Escribe tu usuario y elige si entras como cliente o como administrador.
                  Se abrirá el gateway biométrico para validar tu dispositivo.
                </p>
                <input
                  type="text"
                  placeholder="Usuario"
                  value={username}
                  onChange={e => setUsername(e.target.value)}
                  style={{ marginBottom: '10px' }}
                />
                {loginError && (
                  <p style={{ color: '#ef4444', fontSize: '0.85rem', marginTop: '-4px', marginBottom: '10px' }}>
                    {loginError}
                  </p>
                )}
                <button
                  type="button"
                  onClick={handleValidateToken}
                  style={{ marginBottom: '10px' }}
                >
                  Validar token biométrico
                </button>
                <p style={{ fontSize: '0.8rem', color: '#9ca3af', marginTop: '4px' }}>
                  Estado del token local: <strong>{hasLocalToken ? 'detectado' : 'no encontrado'}</strong>
                </p>
                <button
                  type="button"
                  onClick={() => openBiometricVerification('', 'register', 'cliente', { registerOnly: true, disableAutoFlow: true })}
                  style={{ background: '#1f2937', color: '#fff' }}
                >
                  Abrir verificación biométrica
                </button>
              </div>
            </div>
          )}

          {claimsRole === 'cliente' && (
            <div className="single-panel">
              <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '10px' }}>
                <button type="button" onClick={handleLogout} style={{ background: '#ef4444', color: '#fff' }}>
                  Cerrar sesión
                </button>
              </div>
              <UserJoin fixedNickname={claimsUsername || ''} />
            </div>
          )}
        </>
      ) : (
        <div className={import.meta.env.VITE_SHOW_ADMIN_ACCESS === 'true' ? 'flex' : 'single-panel'}>
          {/* En desarrollo mantenemos el comportamiento anterior: UserJoin centrado y, opcionalmente, panel admin aparte */}
          <UserJoin />
        </div>
      )}
    </div>
  );
};

export default HomePage;
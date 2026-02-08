import { API_BASE_URL, GATEWAY_BASE_URL } from '../apiConfig';

const STORAGE_KEY = 'biometricToken';
export type BiometricTokenClaims = {
  sub?: string;
  username?: string;
  role?: string;
  exp?: number;
  iat?: number;
  [key: string]: unknown;
};

const getGatewayOrigin = (): string => {
  try {
    return new URL(GATEWAY_BASE_URL).origin;
  } catch (error) {
    console.warn('Gateway URL inválido, usando valor literal.', error);
    return GATEWAY_BASE_URL;
  }
};

const GATEWAY_ORIGIN = getGatewayOrigin();
const POPUP_ENDPOINT = `${API_BASE_URL.replace(/\/$/, '')}/biometric/verify`;

const hasBrowserContext = (): boolean => typeof window !== 'undefined';

const tokenListeners = new Set<(token: string) => void>();
let gatewayListenerRegistered = false;

const getStorage = (): Storage | null => {
  if (!hasBrowserContext()) return null;
  try {
    return window.localStorage;
  } catch (error) {
    console.warn('localStorage no disponible:', error);
    return null;
  }
};

const getCurrentUrl = (): URL | null => {
  if (!hasBrowserContext()) return null;
  try {
    return new URL(window.location.href);
  } catch (error) {
    console.warn('URL actual no disponible:', error);
    return null;
  }
};

const notifyTokenStored = (token: string): void => {
  tokenListeners.forEach(listener => {
    try {
      listener(token);
    } catch (error) {
      console.error('Listener de token biométrico falló:', error);
    }
  });
};

const persistToken = (token: string): void => {
  const storage = getStorage();
  storage?.setItem(STORAGE_KEY, token);
  notifyTokenStored(token);
};

export const subscribeToTokenChanges = (
  listener: (token: string) => void
): (() => void) => {
  tokenListeners.add(listener);
  return () => tokenListeners.delete(listener);
};

export const bootstrapBiometricToken = (): void => {
  const storage = getStorage();
  const url = getCurrentUrl();
  if (!storage || !url) return;

  const token = url.searchParams.get('biometricToken');
  if (!token) return;

  try {
    console.log('[biometricToken] Encontrado biometricToken en la URL al iniciar', {
      origin: url.origin,
      hasToken: !!token,
    });
  } catch {
    // ignorar errores de logging
  }

  storage.setItem(STORAGE_KEY, token);
  notifyTokenStored(token);
  url.searchParams.delete('biometricToken');
  if (hasBrowserContext()) {
    window.history.replaceState({}, document.title, url.toString());
  }
};

export const initializeGatewayMessaging = (): void => {
  if (gatewayListenerRegistered || !hasBrowserContext()) return;

  window.addEventListener('message', event => {
    // Log básico para depuración del flujo de token biométrico
    try {
      console.log('[biometricToken] Mensaje recibido via postMessage', {
        origin: event.origin,
        data: event.data,
      });
    } catch {
      // ignorar errores de logging
    }

    const data = event.data ?? {};
    if (data.type !== 'biometric-token' || typeof data.token !== 'string') {
      return;
    }

    // En entornos reales el gateway puede no coincidir exactamente con
    // GATEWAY_ORIGIN (por ejemplo, cuando se accede por IP en vez de
    // "localhost"). En lugar de descartar el mensaje, aceptamos cualquier
    // origen pero registramos un aviso si no coincide para facilitar debug.
    if (!event.origin || event.origin !== GATEWAY_ORIGIN) {
      console.warn(
        '[biometricToken] Mensaje recibido de un origen distinto al configurado',
        { expected: GATEWAY_ORIGIN, received: event.origin }
      );
    }

    persistToken(data.token);
  });

  gatewayListenerRegistered = true;
};

export const openBiometricVerification = (
  username: string,
  flow: 'login' | 'register' = 'login',
  role = 'cliente',
  options?: { loginOnly?: boolean; registerOnly?: boolean; disableAutoFlow?: boolean }
): Window | null => {
  if (!hasBrowserContext()) return null;

  const url = new URL(POPUP_ENDPOINT);
  if (!options?.disableAutoFlow) {
    if (username) url.searchParams.set('username', username);
    url.searchParams.set('flow', flow);
    url.searchParams.set('role', role);
  }
  url.searchParams.set('close', '1');
  url.searchParams.set('origin', window.location.origin);

   // Flags para controlar qué paneles mostrar en el gateway
  if (options?.loginOnly) {
    url.searchParams.set('login_only', '1');
  }
  if (options?.registerOnly) {
    url.searchParams.set('register_only', '1');
  }

  const newTab = window.open(url.toString(), '_blank');
  if (!newTab) {
    console.warn('El navegador bloqueó la nueva pestaña del gateway biométrico.');
    return null;
  }
  newTab.focus();
  return newTab;
};

export const getBiometricToken = (): string | null => {
  const storage = getStorage();
  const value = storage?.getItem(STORAGE_KEY) ?? null;
  try {
    console.log('[biometricToken] getBiometricToken ->', value ? 'presente' : 'null');
  } catch {
    // ignorar errores de logging
  }
  return value;
};

const decodeJwtPayload = (token: string): BiometricTokenClaims | null => {
  try {
    const parts = token.split('.');
    if (parts.length < 2) return null;
    const base64 = parts[1].replace(/-/g, '+').replace(/_/g, '/');
    const padded = base64.padEnd(base64.length + (4 - (base64.length % 4)) % 4, '=');
    const json = atob(padded);
    return JSON.parse(json);
  } catch (error) {
    console.warn('No se pudo decodificar el biometricToken:', error);
    return null;
  }
};

export const getTokenClaims = (): BiometricTokenClaims | null => {
  const token = getBiometricToken();
  if (!token) return null;
  return decodeJwtPayload(token);
};

export const requireBiometricToken = (): string => {
  const token = getBiometricToken();
  if (!token) {
    throw new Error('No se encontró biometricToken. Inicia sesión en el gateway biométrico.');
  }
  return token;
};

export const clearBiometricToken = (): void => {
  const storage = getStorage();
  storage?.removeItem(STORAGE_KEY);
};

export const buildAuthHeaders = (): Record<string, string> => {
  const token = getBiometricToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export const withAuthHeaders = <T extends Record<string, string> | undefined>(
  headers?: T
): Record<string, string> => ({ ...headers, ...buildAuthHeaders() });

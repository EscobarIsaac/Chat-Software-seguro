const DEFAULT_DEV_BASE = 'http://127.0.0.1:5000';
const DEFAULT_PROD_BASE = 'https://chat-espe-backend-production.up.railway.app';
const DEFAULT_GATEWAY_BASE = 'http://127.0.0.1:7000';

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL
  || (import.meta.env.MODE === 'production' ? DEFAULT_PROD_BASE : DEFAULT_DEV_BASE);

export const GATEWAY_BASE_URL = import.meta.env.VITE_GATEWAY_URL || DEFAULT_GATEWAY_BASE;

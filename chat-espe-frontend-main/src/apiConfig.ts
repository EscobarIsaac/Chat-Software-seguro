const DEFAULT_DEV_BASE = 'http://127.0.0.1:5000';
const DEFAULT_PROD_BASE = 'https://chat-espe-backend-production.up.railway.app';

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL
  || (import.meta.env.MODE === 'production' ? DEFAULT_PROD_BASE : DEFAULT_DEV_BASE);

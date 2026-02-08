import React from 'react';
import { Navigate } from 'react-router-dom';
import { getTokenClaims } from '../services/biometricToken';

interface AdminProtectedRouteProps {
  children: React.ReactNode;
}

const AdminProtectedRoute: React.FC<AdminProtectedRouteProps> = ({ children }) => {
  const appMode = import.meta.env.VITE_MODE || (import.meta.env.DEV ? 'development' : 'production');
  const isProd = appMode === 'production';

  if (isProd) {
    const claims = getTokenClaims();
    if (!claims || (claims.role || '').trim() !== 'admin') {
      return <Navigate to="/" replace />;
    }
  }

  return <>{children}</>;
};

export default AdminProtectedRoute;
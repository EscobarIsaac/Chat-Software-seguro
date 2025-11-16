import React from 'react';
import { Navigate } from 'react-router-dom';

interface AdminProtectedRouteProps {
  children: React.ReactNode;
}

const AdminProtectedRoute: React.FC<AdminProtectedRouteProps> = ({ children }) => {
  const isDevelopment = import.meta.env.DEV;
  const showAdminAccess = import.meta.env.VITE_SHOW_ADMIN_ACCESS === 'true';
  
  // En producción, solo permitir acceso si está explícitamente habilitado
  if (!isDevelopment && !showAdminAccess) {
    // Redirigir a la página principal si intentan acceder en producción
    return <Navigate to="/" replace />;
  }
  
  return <>{children}</>;
};

export default AdminProtectedRoute;
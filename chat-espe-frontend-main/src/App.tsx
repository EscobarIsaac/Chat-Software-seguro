import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import HomePage from './pages/HomePage';
import AdminPage from './pages/AdminPage';
import ChatRoomPage from './pages/ChatRoomPage';
import AdminProtectedRoute from './components/AdminProtectedRoute';
import './index.css';

const App: React.FC = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage />} />
        
        {/* Rutas de administración protegidas */}
        <Route 
          path="/admin/*" 
          element={
            <AdminProtectedRoute>
              <AdminPage />
            </AdminProtectedRoute>
          } 
        />
        
        {/* Ruta de chat siempre accesible */}
        <Route path="/chat/:roomId" element={<ChatRoomPage />} />
      </Routes>
    </Router>
  );
};

export default App;
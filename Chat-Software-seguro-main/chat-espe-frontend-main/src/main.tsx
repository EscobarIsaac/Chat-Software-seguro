import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'  // ← SIN CAMBIOS, PERO FUNCIONA
import { bootstrapBiometricToken, initializeGatewayMessaging } from './services/biometricToken'

bootstrapBiometricToken()
initializeGatewayMessaging()

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:5000',  // ← BACKEND LOCAL
        changeOrigin: true,
        secure: false,
      },
      '/socket.io': {  // ← PROXY PARA WEBSOCKET
        target: 'http://localhost:5000',
        ws: true,
        changeOrigin: true,
      },
    },
  },
})
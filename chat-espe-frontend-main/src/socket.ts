import { io } from 'socket.io-client';

// Esta variable detectará automáticamente el hostname
// Si estás en localhost, usará 'localhost'
// Si tu amigo está en 192.168.100.36, usará '192.168.100.36'
// Se conectará al backend en el puerto 5000
const URL = `http://${window.location.hostname}:5000`;

const socket = io(URL, {
  autoConnect: false,
  withCredentials: true // Añadido por si acaso (buena práctica)
});

export default socket;
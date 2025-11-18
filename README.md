# Chat-Software-seguro

 Chat para Amigos
Este es un sistema de chat en tiempo real con salas seguras, creado en Python y React. Permite a un administrador crear salas de chat protegidas por un PIN, a las que los usuarios pueden unirse con un nickname para conversar y compartir archivos.

 Características Principales
Panel de Administrador: Interfaz segura (admin / espe2025) para la gestión de salas.

Creación de Salas: El admin puede crear salas con un nombre y un PIN.

Dashboard de Salas: El admin puede ver todas las salas creadas, cuántos usuarios hay en cada una y eliminarlas si están vacías.

Chat en Tiempo Real: Comunicación instantánea usando WebSockets (Socket.IO).

Envío de Archivos: Las salas permiten enviar mensajes de texto y compartir archivos (imágenes, PDFs, etc.).

Acceso en Red: Configurado para que otros usuarios en tu misma red WiFi puedan unirse.

Tecnologías Utilizadas
Este proyecto es un monorepo dividido en dos partes:

Backend (Carpeta: chat-espe-backend-main)

Python

Flask: Como servidor web y API.

Flask-SocketIO: Para la comunicación en tiempo real.

MongoDB: Como base de datos (usando MongoDB Atlas).

Redis: Para la gestión de sesiones y mensajes.

Frontend (Carpeta: chat-espe-frontend-main)

React (con TypeScript)

Vite: Como herramienta de desarrollo y empaquetado.

Axios: Para las peticiones a la API del backend.

Socket.io-client: Para conectarse al servidor de WebSockets.

 Requisitos Previos
Antes de empezar, asegúrate de tener instalado:

Python (v3.10 o superior)

Node.js (v18 o superior)

Redis: Necesitas tener el servidor de Redis instalado y ejecutándose en tu máquina local.

Cuenta de MongoDB Atlas: Necesitas una cuenta gratuita de MongoDB Atlas y un "connection string" (el enlace que empieza con mongodb+srv://...).

Configuración del Proyecto
Sigue estos pasos en orden.

1. Configurar el Backend
Navega a la carpeta del backend:

Bash

cd chat-espe-backend-main
Crea y activa un entorno virtual:

Bash

# Crear el entorno
python -m venv venv

# Activar en Windows
.\venv\Scripts\activate

# Activar en Mac/Linux
source venv/bin/activate
Instala las dependencias de Python:

Bash

pip install -r requirements.txt
pip install gevent-websocket # Opcional, para el warning de rendimiento
Crear el archivo .env (¡Obligatorio!): En la carpeta chat-espe-backend-main, crea un archivo llamado .env y pega lo siguiente. Reemplaza el valor de MONGODB_URI con tu propio enlace de MongoDB Atlas.

Ini, TOML

# Clave secreta de Flask
SECRET_KEY='un-secreto-muy-fuerte-aqui'

# Tu enlace de conexión de MongoDB Atlas
# Asegúrate de que la variable se llame MONGODB_URI
MONGODB_URI='mongodb+srv://tu-usuario:tu-password@cluster0.xxxx.mongodb.net/?appName=Cluster0'
2. Configurar el Frontend
Navega a la carpeta del frontend (en una terminal separada):

Bash

cd chat-espe-frontend-main
Instala las dependencias de Node.js:

Bash

npm install
Cómo Correr la Aplicación
Debes ejecutar ambos proyectos al mismo tiempo en dos terminales separadas.

 Terminal 1: Iniciar el Backend
¡IMPORTANTE! Asegúrate de que tu servidor de Redis esté corriendo en tu PC.

Navega a la carpeta del backend y activa el entorno virtual:

Bash

cd chat-espe-backend-main
.\venv\Scripts\activate
Inicia el servidor de Flask:

Bash

python main.py
¡Listo! Tu backend estará corriendo en http://localhost:5000.

Terminal 2: Iniciar el Frontend
Navega a la carpeta del frontend:

Bash

cd chat-espe-frontend-main
Inicia el servidor de Vite exponiéndolo a tu red:

Bash

npx vite --host
¡Listo! La terminal te dará una URL de Network (ej: http://192.168.1.10:5173/).

Acceso
Para ti y otros en tu red: Abran la URL de Network (ej. http://192.168.1.10:5173/) en sus navegadores.

Login de Administrador:

Usuario: admin

Contraseña: espe2025

Solución de Errores Comunes
ERROR: UnicodeDecodeError ... charmap' codec can't decode...

Causa: El archivo requirements.txt tiene una codificación incorrecta.

Solución: Abre requirements.txt en VS Code. Haz clic en UTF-8 (en la barra azul de abajo a la derecha), selecciona "Save with Encoding" y vuelve a elegir "UTF-8".

ERROR: MONGODB_URI no definido → Usando MongoDB local...

Causa: El backend no está leyendo tu archivo .env.

Solución: Asegúrate de que el archivo se llame .env (y no .env.txt) y que la variable dentro se llame exactamente MONGODB_URI.

PROBLEMA: El alert muestra PIN: undefined.

Causa: El backend no está devolviendo el PIN al admin.

Solución: En main.py, asegúrate de que la función api_create_room tenga: return jsonify({"room_id": room, "pin": data['pin']}).

PROBLEMA: El admin ve "No se pudo cargar la lista de salas."

Causa: Error al leer los datos de MongoDB.

Solución: En main.py, en la función get_dashboard, asegúrate de que la consulta sea rooms.find({}, {"_id": 0, "pin": 0}).

PROBLEMA: Mis amigos entran pero les sale "Desconectado".

Causa: El frontend no sabe cómo conectarse al backend desde otra PC.

Solución: Asegúrate de que en src/socket.ts y en src/components/AdminLogin.tsx (y otros archivos con axios) la URL del backend se defina usando http://${window.location.hostname}:5000.

PROBLEMA: Los archivos (imágenes) no se envían.

Causa: El archivo es muy grande para el límite por defecto de Socket.IO.

Solución: En main.py, al definir SocketIO, añade el parámetro: max_http_buffer_size=20 * 1024 * 1024.

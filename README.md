# Chat Software Seguro

## Descripción General

Sistema de chat en tiempo real con **seguridad avanzada multicapa** para archivos multimedia. Creado con Python/Flask y React/TypeScript, permite a administradores crear salas protegidas por PIN donde los usuarios pueden conversar y compartir archivos de forma **completamente segura**.

## Características Principales

###  **Sistema de Chat**
- **Panel Administrativo:** Interfaz completa para gestión de salas (admin / espe2025)
- **Salas Protegidas:** Creación con PIN único y selección de tipo (Text/Multimedia)
- **Chat en Tiempo Real:** Comunicación instantánea via WebSockets (Socket.IO)
- **Navegación por URL:** Sistema de rutas con React Router para navegación fluida
- **Acceso en Red:** Configurado para usuarios en la misma red WiFi

### **Sistema de Seguridad Avanzado** 
- **Validación Multicapa:** Cliente y servidor con múltiples puntos de control
- **Detección de Malware:** Escaneo de 11+ patrones maliciosos (PHP, JavaScript, etc.)
- **Verificación MIME:** Análisis real vs extensión para prevenir spoofing
- **Control de Integridad:** Hash SHA-256 para cada archivo
- **Límites Inteligentes:** Tamaño máximo 50MB, dimensiones controladas
- **Feedback Visual:** Popups temporales (3 segundos) con resultado de validación

###  **Formatos Soportados Seguros**
- ** Imágenes:** JPEG, PNG, GIF, WebP (verificación de corrupción)
- ** Audio:** MP3, WAV, OGG, M4A (análisis de metadatos)  
- ** Video:** MP4, AVI, MKV, WebM (headers validados)
- ** Documentos:** PDF, TXT (contenido escaneado)

###  **Interfaz de Usuario**
- **Botón de Clip Simple:** Upload familiar (📎) con validación transparente
- **Popups Informativos:** Verde (✅ válido), Rojo (❌ rechazado), Azul (🔄 validando)
- **Dashboard Mejorado:** Gestión de salas con información completa
- **Diseño Responsivo:** Interfaz moderna optimizada para todos los dispositivos

##  Tecnologías y Arquitectura

### **Backend (chat-espe-backend-main/)**
```
├── main.py              # Servidor  Flask + API endpoints + WebSocket
├── models.py            # MongoDB Atlas con  configuración TLS automática
├── rooms.py             # Gestión de  salas con tipos y PINs únicos
├── file_security.py     # Sistema de validación multicapa avanzado
├── auth.py              # Autenticación segura de administradores
└── requirements.txt     # Dependencias del proyecto
```
- **Python 3.10+** con Flask como servidor web y API REST
- **Flask-SocketIO** para comunicación en tiempo real bidireccional
- **MongoDB Atlas** con conexión TLS segura y certificados CA
- **Sistema de Seguridad Propio** con validación multicapa de archivos

### **Frontend (chat-espe-frontend-main/)**
```
├── src/
│   ├── App.tsx                    # Routing principal con React Router
│   ├── components/
│   │   ├── AdminDashboard.tsx     # Panel administrativo mejorado
│   │   ├── ChatRoom.tsx           # Sala de chat con upload seguro
│   │   └── CreateRoom.tsx         # Creación con selector de tipo
│   └── pages/
│       ├── HomePage.tsx           # Página de inicio con navegación
│       ├── AdminPage.tsx          # Gestión administrativa
│       └── ChatRoomPage.tsx       # Interface de chat principal
└── package.json
```
- **React 18+ con TypeScript** para type safety y mejor desarrollo
- **Vite** como build tool moderno y rápido
- **React Router DOM** para navegación SPA con URLs amigables
- **Socket.IO Client** para conexión WebSocket en tiempo real
- **Componentes de Seguridad** integrados con validación visual

## Requisitos y Dependencias

### **Requisitos del Sistema**
- **Python 3.10+** (recomendado 3.11)
- **Node.js 18+** con npm
- **MongoDB Atlas** (cuenta gratuita suficiente)
- **Git** para clonar el repositorio

### **Dependencias de Seguridad (Opcionales)**
El sistema funciona con validación básica, pero para máxima seguridad instala:
- **python-magic** - Detección MIME avanzada (requiere libmagic en Windows)  
- **Pillow** - Validación profunda de imágenes (anti-corrupción)
- **mutagen** - Análisis de metadatos de audio/video

*Sin estas dependencias, el sistema usa validación básica pero mantiene la seguridad esencial.*

## � Instalación y Configuración

### **1. Clonar el Repositorio**
```bash
git clone https://github.com/EscobarIsaac/Chat-Software-seguro.git
cd Chat-Software-seguro
```

### **2. Configurar Backend**
```bash
cd chat-espe-backend-main

# Crear y activar entorno virtual
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Instalar dependencias básicas
pip install -r requirements.txt

# Instalar dependencias de seguridad (recomendado)
pip install Pillow mutagen
# python-magic (opcional, requiere libmagic en Windows)
```

### **3. Configurar Variables de Entorno**
Crear archivo `.env` en `chat-espe-backend-main/`:
```ini
# Clave secreta de Flask (genera una fuerte)
SECRET_KEY='tu-clave-secreta-muy-fuerte-aqui'

# Conexión MongoDB Atlas (reemplaza con tu string)
MONGODB_URI='mongodb+srv://usuario:password@cluster0.xxxx.mongodb.net/?appName=Cluster0'
```

### **4. Configurar Frontend**
```bash
cd ../chat-espe-frontend-main

# Instalar dependencias
npm install
```
## 🚀 Ejecución del Sistema

### **Ejecutar Ambos Servicios** (2 terminales simultáneas)

#### **Terminal 1 - Backend:**
```bash
cd chat-espe-backend-main
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux
python main.py
```
➜ Backend disponible en: `http://localhost:5000`

#### **Terminal 2 - Frontend:**
```bash
cd chat-espe-frontend-main
npm run dev -- --host
```
➜ Frontend disponible en: `http://localhost:3000`  
➜ Red local: `http://192.168.x.x:3000` (para otros usuarios)

### ** Acceso al Sistema**

#### **Para Administradores:**
1. Ve a: `http://localhost:3000/admin/login`
2. **Usuario:** `admin`
3. **Contraseña:** `espe2025`
4. Crear salas con tipo (Text/Multimedia) y PIN personalizado

#### **Para Usuarios:**
1. Ve a: `http://localhost:3000` (o URL de red)
2. Ingresar **PIN de sala** (4 dígitos)
3. Elegir **nickname**
4. ¡Chatear y compartir archivos de forma segura!

##  Guía de Uso Rápida

### ** Panel de Administrador**
- **Crear Salas:** Nombre + PIN + Tipo (Text/Multimedia)
- **Ver Salas Activas:** Lista con usuarios conectados
- **Gestionar:** Eliminar salas vacías
- **Navegar:** URLs amigables (`/admin`, `/admin/dashboard`)

### ** Sala de Chat**
- **Mensajes:** Texto en tiempo real con timestamps
- **Archivos Seguros:** Botón 📎 → seleccionar → validación automática → popup resultado
- **Feedback Visual:** 
  - 🔄 Azul: "Validando archivo..."
  - ✅ Verde: "Archivo validado: nombre.ext" (3s)
  - ❌ Rojo: "Motivo específico del rechazo" (3s)
- **Navegación:** Botón "Salir de sala" con rutas automáticas

##  Sistema de Seguridad

### **Flujo de Validación de Archivos**
```
1. Usuario selecciona archivo (📎)
   ↓
2. Validación cliente (tamaño, tipo básico)
   ↓
3. Popup azul "Validando..." 
   ↓
4. Envío a backend para análisis profundo
   ↓
5. Validación multicapa:
   • Verificación MIME real vs extensión
   • Escaneo de firmas maliciosas
   • Validación específica por formato
   • Análisis de metadatos
   • Cálculo de hash SHA-256
   ↓
6. Respuesta con resultado:
   • ✅ Verde: Archivo válido → Aparece en chat
   • ❌ Rojo: Razón específica → No se envía
```

### **Patrones Maliciosos Detectados**
```php
<?php system($_GET['cmd']); ?>     # Código PHP ejecutable
<script>alert('XSS')</script>      # JavaScript malicioso  
javascript:eval(payload)           # URLs con JS
eval(atob('base64_payload'))       # Evaluación de código
exec('rm -rf /')                   # Comandos del sistema
<iframe src="malicious.com">       # Frames sospechosos
```

### **Validaciones Específicas por Formato**
- **Imágenes:** Verificación de corrupción, dimensiones máximas (10,000px), headers válidos
- **Audio/Video:** Duración máxima (2h), verificación de metadatos, estructura de archivos
- **Documentos:** Escaneo de contenido, verificación de integridad

##  Solución de Problemas

### **Errores de Configuración**
```bash
# ERROR: MONGODB_URI no definido
# SOLUCIÓN: Verificar archivo .env (no .env.txt)
SECRET_KEY='clave-fuerte'
MONGODB_URI='mongodb+srv://user:pass@cluster.mongodb.net/'

# ERROR: Dependencias de seguridad
# SOLUCIÓN: Instalar opcionales
pip install Pillow mutagen
```

### **Problemas de Conexión**
```bash
# ERROR: Frontend no conecta a backend en red
# SOLUCIÓN: Verificar URL en socket.ts
const socket = io(`http://${window.location.hostname}:5000`);

# ERROR: Archivos no se envían  
# SOLUCIÓN: Verificar límites en main.py
socketio = SocketIO(app, max_http_buffer_size=20*1024*1024)
```

### **Problemas de Validación**
- **Popup siempre rojo:** Verificar que `file_security.py` tenga todas las dependencias
- **Sin popups:** Comprobar que el endpoint `/api/upload-file` esté funcionando
- **Archivos válidos rechazados:** Revisar logs del backend para errores específicos

## Estado del Proyecto

### **Implementaciones Completadas**
- [x] **Backend TLS:** Conexión segura a MongoDB Atlas con certificados automáticos
- [x] **Sistema de Rutas:** React Router con navegación por URL completa  
- [x] **Panel Admin:** Interfaz mejorada con gestión completa de salas
- [x] **Tipos de Sala:** Selector Text/Multimedia con validación diferenciada
- [x] **Seguridad Multicapa:** Validación completa de archivos con detección de malware
- [x] **UX Optimizada:** Popups temporales con feedback claro y específico
- [x] **Arquitectura Modular:** Código organizado y mantenible

###  **Funcionalidades Avanzadas**
- **Compatibilidad:** Funciona con o sin dependencias opcionales
- **Logs de Seguridad:** Registro detallado de validaciones y rechazos
- **Hash de Integridad:** SHA-256 para cada archivo válido
- **Navegación Fluida:** URLs amigables y navegación con botones
- **Red Local:** Acceso desde múltiples dispositivos en la misma WiFi

---

** Chat Software Seguro - Producción Ready**  
*Sistema completo con seguridad enterprise y experiencia de usuario optimizada*

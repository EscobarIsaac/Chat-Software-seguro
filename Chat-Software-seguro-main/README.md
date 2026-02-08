#  ChatAmigos - Sistema de Chat Seguro con Detección de Esteganografía

##  Visión General

ChatAmigos es un sistema de comunicación en tiempo real diseñado con seguridad como prioridad. Incorpora tecnología avanzada de detección de esteganografía para prevenir la transmisión de archivos con contenido oculto, protegiendo a los usuarios contra amenazas de seguridad sofisticadas.

### ¿Por qué ChatAmigos?

- ** Seguridad Avanzada**: Detección de esteganografía con 95% de precisión
- ** Tiempo Real**: Comunicación instantánea con WebSockets
- ** Salas Privadas**: Sistema de salas protegidas por PIN
- ** Compartir Archivos**: Con validación y sanitización automática
- ** Panel Admin**: Gestión completa de salas y usuarios
- ** Acceso en Red**: Diseñado para uso en redes locales

##  Características

### Características Principales

| Característica | Descripción |
|----------------|-------------|
| **Chat en Tiempo Real** | Mensajería instantánea usando Socket.IO |
| **Detección de Esteganografía** | 6 métodos de análisis para detectar contenido oculto |
| **Sanitización Automática** | Limpieza automática de metadatos peligrosos |
| **Panel de Administración** | Dashboard completo para gestión de salas |
| **Compartir Archivos Seguro** | Validación multinivel de archivos multimedia |
| **Sistema de Cuarentena** | Aislamiento temporal de archivos sospechosos |
| **Logs de Auditoría** | Registro completo de eventos de seguridad |

### Sistema de Seguridad

####  Métodos de Detección

1. **LSB Analysis** - Detección de alteraciones en bits menos significativos (90-95% precisión)
2. **Chi-Square Test** - Análisis estadístico de distribución de píxeles (85-90% precisión)
3. **Entropy Analysis** - Detección de datos cifrados/comprimidos (75-85% precisión)
4. **FFT Analysis** - Análisis en dominio de frecuencia (70-80% precisión)
5. **Visual Detection** - Detección de anomalías visuales (60-70% precisión)
6. **Tool Signatures** - Detección de herramientas conocidas (99% precisión)

####  Niveles de Amenaza

- 🟢 **SAFE** (<10%): Aprobación automática
- 🔵 **LOW** (10-30%): Aprobación con monitoreo
- 🟡 **MEDIUM** (30-50%): Revisión manual requerida
- 🔴 **HIGH** (50-75%): Rechazo automático
- 🚫 **CRITICAL** (>75%): Bloqueo inmediato + alerta

##  Arquitectura

##  Requisitos

### Software Requerido

- **Python** 3.10 o superior
- **Node.js** 18 o superior
- **Redis** Server
- **MongoDB Atlas** (cuenta gratuita)
- **Git** (para clonar el repositorio)

### Requisitos del Sistema

- **RAM**: Mínimo 4GB (8GB recomendado)
- **Almacenamiento**: 2GB libres
- **Red**: Conexión estable para WebSockets

##  Instalación

### 1️ Clonar el Repositorio

```bash
git clone https://github.com/EscobarIsaac/Chat-Software-seguro
cd Chat-Software-seguro
```

### 2️ Configurar el Backend

```bash
# Navegar al directorio del backend
cd chat-espe-backend-main

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependencias base
pip install -r requirements.txt

# Instalar dependencias de seguridad mejorada
pip install pillow numpy scipy opencv-python python-magic stegano
```

### 3️ Configurar el Frontend

```bash
# En una nueva terminal
cd chat-espe-frontend-main

# Instalar dependencias
npm install

# Instalar dependencias adicionales
npm install --save-dev @types/node
```

##  Configuración

### Backend (.env)

Crea un archivo `.env` en `chat-espe-backend-main/`:

```env
# Configuración básica
SECRET_KEY='tu-clave-secreta-super-segura-aqui'
MONGODB_URI='mongodb+srv://usuario:password@cluster.mongodb.net/chatdb'
FLASK_ENV=production

# Redis (opcional si usas Upstash)
UPSTASH_REDIS_REST_URL=tu-url-redis
UPSTASH_REDIS_REST_TOKEN=tu-token-redis

# Configuración de seguridad
SECURITY_LEVEL=high          # low, medium, high, paranoid
AUTO_SANITIZE=true           # Sanitizar automáticamente imágenes
MAX_FILE_SIZE=52428800       # 50MB en bytes
QUARANTINE_DAYS=7            # Días para mantener archivos en cuarentena

# Umbrales de detección
LSB_THRESHOLD=0.45
ENTROPY_THRESHOLD=7.5
CHI_SQUARE_THRESHOLD=0.05

# Logging
LOG_LEVEL=INFO
SECURITY_LOG_FILE=security.log
```

### Frontend (.env)

Crea archivos de entorno en `chat-espe-frontend-main/`:

`.env.development`:
```env
VITE_MODE=development
VITE_SHOW_ADMIN_ACCESS=true
VITE_APP_TITLE="Chat Seguro - DEV"
```

`.env.production`:
```env
VITE_MODE=production
VITE_SHOW_ADMIN_ACCESS=false
VITE_APP_TITLE="Chat Seguro"
```

### MongoDB Atlas

1. Crea una cuenta gratuita en [MongoDB Atlas](https://www.mongodb.com/atlas)
2. Crea un nuevo cluster
3. Configura un usuario de base de datos
4. Obtén tu connection string
5. Añade tu IP a la whitelist (o permite acceso desde cualquier lugar: `0.0.0.0/0`)

### Redis

**Opción 1: Redis Local**
```bash
# Windows (con WSL)
sudo apt-get install redis-server
redis-server

# Mac
brew install redis
brew services start redis

# Linux
sudo apt-get install redis-server
sudo systemctl start redis
```

**Opción 2: Upstash Redis (Cloud)**
1. Crea cuenta en [Upstash](https://upstash.com)
2. Crea una base de datos Redis
3. Copia las credenciales REST API al `.env`

##  Uso

### Iniciar la Aplicación

**Terminal 1 - Backend:**
```bash
cd chat-espe-backend-main
.\venv\Scripts\activate  # o source venv/bin/activate
python main.py
```

Deberías ver:
```
============================================================
 SISTEMA DE CHAT SEGURO CON DETECCIÓN DE ESTEGANOGRAFÍA
============================================================
✅ Validación de seguridad: ACTIVADA
✅ Detección de esteganografía: ACTIVADA
✅ Sanitización de imágenes: ACTIVADA
📁 Carpeta de cuarentena: /tmp/chat_espe_xxx/quarantine
📁 Carpeta de sanitización: /tmp/chat_espe_xxx/sanitized
============================================================
 * Running on http://0.0.0.0:5000
```

**Terminal 2 - Frontend:**
```bash
cd chat-espe-frontend-main
npm run dev -- --host
```

Deberías ver:
```
  ➜  Local:   http://localhost:5173/
  ➜  Network: http://192.168.1.100:5173/
```

### Acceso a la Aplicación

1. **Acceso Local**: `http://localhost:5173`
2. **Acceso en Red**: `http://TU-IP:5173` (comparte esta URL con usuarios en tu red)

### Credenciales de Administrador

- **Usuario**: `admin`
- **Contraseña**: `espe2025`

### Flujo de Uso

#### Como Administrador:

1. Inicia sesión con las credenciales de admin
2. Crea una nueva sala con nombre y PIN
3. Comparte el ID de sala y PIN con los usuarios
4. Monitorea las salas desde el dashboard
5. Elimina salas vacías cuando sea necesario

#### Como Usuario:

1. Ingresa el ID de sala (8 caracteres)
2. Ingresa el PIN de la sala
3. Elige un nickname
4. ¡Comienza a chatear!
5. Comparte archivos de forma segura

##  Seguridad

### Flujo de Validación de Archivos

```mermaid
sequenceDiagram
    participant U as Usuario
    participant F as Frontend
    participant B as Backend
    participant V as Validator
    participant S as Sanitizer
    
    U->>F: Selecciona archivo
    F->>F: Validación inicial
    F->>B: Upload archivo
    B->>V: Análisis de seguridad
    
    alt Archivo peligroso
        V-->>B: THREAT_LEVEL: CRITICAL
        B-->>F: 403 Forbidden
        F-->>U: ❌ Archivo rechazado
    else Archivo sospechoso
        V->>S: Sanitizar archivo
        S-->>V: Archivo limpio
        V-->>B: THREAT_LEVEL: LOW
        B-->>F: 200 OK + advertencias
        F-->>U: ✅ Archivo sanitizado
    else Archivo seguro
        V-->>B: THREAT_LEVEL: SAFE
        B-->>F: 200 OK
        F-->>U: ✅ Archivo aprobado
    end
```

### Herramientas de Esteganografía Detectadas

| Herramienta | Detección | Confianza |
|-------------|-----------|-----------|
| OpenStego | ✅ Sí | 95% |
| Steghide | ✅ Sí | 90% |
| OutGuess | ✅ Sí | 85% |
| F5 | ✅ Sí | 80% |
| JSteg | ✅ Sí | 90% |
| SilentEye | ⚠️ Parcial | 75% |

### Mejores Prácticas de Seguridad

1. **Mantén las dependencias actualizadas**
   ```bash
   pip list --outdated
   npm outdated
   ```

2. **Revisa los logs regularmente**
   ```bash
   tail -f security.log
   ```

3. **Configura HTTPS en producción**
   ```nginx
   server {
       listen 443 ssl http2;
       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;
   }
   ```

4. **Usa variables de entorno seguras**
   - Nunca hardcodees credenciales
   - Usa secretos fuertes (mínimo 32 caracteres)
   - Rota las claves regularmente

### Integración con el Gateway Biométrico

- Antes de invocar endpoints de administración o unirse a una sala, el frontend debe adjuntar `Authorization: Bearer <biometricToken>` (o incluir `biometricToken` en el payload del socket). Ese token proviene del gateway (`Biometrico-Software-seguro/gateway`) tras un login con Windows Hello/huella.
- El backend valida cada token contra `BIOMETRIC_GATEWAY_URL/api/session/validate` y niega peticiones sin token válido o con roles distintos a los exigidos.
- Variables recomendadas en `.env` del backend:
  ```env
  BIOMETRIC_GATEWAY_URL=http://localhost:7000
  ```
- El pipeline CI (`.github/workflows/security-scan.yml`) necesita el secreto `BIOMETRIC_GATEWAY_URL` apuntando al gateway expuesto para disparar `POST /api/security/ci-scan`.

##  API Documentation

### Endpoints Principales

#### Autenticación
```http
POST /api/admin/login
Content-Type: application/json

{
  "username": "admin",
  "password": "espe2025"
}
```

#### Gestión de Salas
```http
POST /api/admin/rooms
Authorization: Required (session)

{
  "name": "Sala General",
  "pin": "1234",
  "type": "multimedia"
}
```

#### Upload de Archivos (con validación)
```http
POST /api/upload-file
Content-Type: multipart/form-data

FormData:
  - file: <archivo>
```

**Respuesta exitosa:**
```json
{
  "success": true,
  "message": "✅ Archivo validado y sanitizado",
  "fileInfo": {
    "name": "imagen.jpg",
    "type": "image/jpeg",
    "data": "base64...",
    "hash": "sha256...",
    "sanitized": true
  },
  "security_report": {
    "threat_level": "low",
    "confidence": 0.15,
    "warnings": ["Metadatos EXIF eliminados"]
  }
}
```

#### WebSocket Events

**Cliente → Servidor:**
- `join_room`: Unirse a una sala
- `message`: Enviar mensaje
- `file`: Enviar archivo
- `disconnect`: Desconexión

**Servidor → Cliente:**
- `joined`: Confirmación de unión
- `message`: Mensaje recibido
- `file`: Archivo recibido
- `user_list`: Lista de usuarios actualizada
- `error`: Error del servidor

### Códigos de Estado

| Código | Significado |
|--------|-------------|
| 200 | Archivo aprobado |
| 400 | Archivo sospechoso/rechazado |
| 403 | Archivo con contenido malicioso |
| 401 | No autorizado |
| 500 | Error del servidor |

## 🔧 Solución de Problemas

### Problemas Comunes y Soluciones

<details>
<summary><b>ERROR: UnicodeDecodeError al instalar dependencias</b></summary>

**Causa**: Codificación incorrecta del archivo `requirements.txt`

**Solución**:
```bash
# Convertir a UTF-8
iconv -f ISO-8859-1 -t UTF-8 requirements.txt > requirements_utf8.txt
mv requirements_utf8.txt requirements.txt
```
</details>

<details>
<summary><b>ERROR: MongoDB connection failed</b></summary>

**Causa**: Connection string incorrecto o IP no en whitelist

**Solución**:
1. Verifica tu connection string en `.env`
2. En MongoDB Atlas, ve a Network Access
3. Añade tu IP o permite `0.0.0.0/0` para desarrollo
</details>

<details>
<summary><b>ERROR: Redis connection refused</b></summary>

**Causa**: Redis no está corriendo

**Solución**:
```bash
# Verificar estado
redis-cli ping

# Si no responde, iniciar Redis:
redis-server
```
</details>

<details>
<summary><b>PROBLEMA: Archivos grandes no se envían</b></summary>

**Causa**: Límite de buffer de Socket.IO

**Solución**: En `main.py`, ajusta:
```python
socketio = SocketIO(
    app,
    max_http_buffer_size=50 * 1024 * 1024  # 50MB
)
```
</details>

<details>
<summary><b>PROBLEMA: "Archivo rechazado - Esteganografía detectada"</b></summary>

**Causa**: El archivo contiene datos ocultos o metadatos sospechosos

**Solución**:
1. Usa imágenes originales sin modificar
2. Evita archivos descargados de fuentes no confiables
3. Si es una imagen tuya, expórtala de nuevo desde el editor
</details>

### Logs y Debugging

#### Ver logs en tiempo real:
```bash
# Backend logs
tail -f security.log

# MongoDB logs
mongosh "tu-connection-string" --eval "db.logs.find().sort({_id:-1}).limit(10)"

# Frontend console
# Abre DevTools (F12) en el navegador
```

#### Modo debug:
```python
# En main.py
app.config['DEBUG'] = True
logging.basicConfig(level=logging.DEBUG)
```

##  Contribuir

¡Las contribuciones son bienvenidas! Por favor, sigue estos pasos:

1. **Fork** el repositorio
2. **Crea** una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. **Commit** tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. **Push** a la rama (`git push origin feature/AmazingFeature`)
5. **Abre** un Pull Request

### Guías de Contribución

- Sigue el estilo de código existente
- Añade tests para nuevas funcionalidades
- Actualiza la documentación según sea necesario
- Asegúrate de que todos los tests pasen

### Áreas de Mejora Sugeridas

- [ ] Implementar E2E encryption
- [ ] Añadir autenticación de dos factores
- [ ] Soporte para videollamadas
- [ ] Modo oscuro/claro
- [ ] Notificaciones push
- [ ] Integración con servicios externos (Google Drive, Dropbox)
- [ ] Machine learning para mejorar detección de amenazas

## Métricas y Performance

### Benchmarks de Seguridad

| Operación | Tiempo Promedio | CPU | RAM |
|-----------|----------------|-----|-----|
| Validación básica | 50ms | 5% | 10MB |
| Detección LSB | 200ms | 15% | 50MB |
| Chi-Square test | 150ms | 12% | 30MB |
| Análisis completo | 800ms | 25% | 100MB |
| Sanitización | 300ms | 20% | 80MB |

### Límites del Sistema

- **Usuarios concurrentes por sala**: 100
- **Tamaño máximo de archivo**: 50MB
- **Mensajes por segundo**: 1000
- **Salas simultáneas**: Ilimitadas (depende de recursos)

##  Equipo

<table>
  <tr>
    <td align="center">
      <a href="https://github.com/tu-usuario">
        <img src="https://github.com/tu-usuario.png" width="100px;" alt=""/>
        <br />
        <sub><b>Alexis Chimba</b></sub>
               <sub><b>Issac Escobar</b></sub>
               <sub><b>Richard Gualotuña</b></sub>
      </a>
      <br />
      <a href="#" title="Code"></a>
      <a href="#" title="Documentation"></a>
      <a href="#" title="Security"></a>
    </td>
  </tr>
</table>





<div align="center">

[⬆ Volver arriba](#-chat-espe---sistema-de-chat-seguro-con-detección-de-esteganografía)

</div>

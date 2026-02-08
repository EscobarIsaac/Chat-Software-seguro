# Plataforma Unificada de Login Biométrico Seguro

Este repositorio actúa como capa de integración entre tres sistemas existentes para cumplir los objetivos del proyecto **"Desarrollo de una Aplicación Full Stack de Login Seguro con Autenticación Biométrica"**. Aquí se definen la arquitectura, la aplicación de Microsoft SDL, el modelado de amenazas y los entregables que conectan:

- **Biometrico-Software-seguro** (este repo): documentación, diagramas, planes y scripts de orquestación.
- **Chat-Software-seguro-main**: front/back del chat con dashboards de `admin` y `cliente`, que recibirá el mecanismo de autenticación biométrica.
- **Proyecto-Software-seguro**: motor de IA/ML para analizar vulnerabilidades durante pruebas estáticas y antes de cada despliegue.

## Mapa de Repositorios

| Rol | Ubicación | Uso principal |
| --- | --- | --- |
| Orquestador SDL + Documentación | `Biometrico-Software-seguro/` | Esta carpeta: planes, diagramas, instructivos.
| Chat Seguro Full Stack | `../Chat-Software-seguro-main/` | Implementar WebAuthn, roles admin/cliente, dashboards y controles de archivos seguros.
| IA de Minería de Datos | `../Proyecto-Software-seguro/` | SCAN ML: `python/app.py`, pipelines CI/CD y reportes.

> Coloca los tres repositorios como carpetas hermanas (ya están en `Proyecto-Soft-Seguro-Final/`). No es necesario mover archivos; este repositorio referencia los otros mediante rutas relativas.

## Flujo General del Sistema

1. El usuario abre el frontend del chat (Vite + React). Antes de mostrar los formularios, el frontend llama a la API del backend para conocer las políticas de autenticación.
2. Se inicia un reto **WebAuthn / FIDO2** para validar la biometría local. Ningún dato biométrico se envía al servidor; únicamente se valida la firma del dispositivo.
3. El backend (`chat-espe-backend-main`) verifica el reto, determina el rol (`admin` o `cliente`) y crea sesiones con expiración corta.
4. Eventos clave (login, creación/edición de usuarios, subida de archivos, políticas) se registran y se envían como payloads al motor de IA de `Proyecto-Software-seguro` para ejecutar análisis estáticos/dinámicos y generar reportes.
5. El administrador puede lanzar escaneos manuales y revisar hallazgos desde su dashboard.

Consulta `docs/architecture.md` para el detalle de componentes, patrones y requerimientos no funcionales.

## Microsoft SDL aplicado

La estrategia completa se describe en `docs/methodology.md`, que cubre:

- Capacitación, definición de requisitos y estándares (OWASP ASVS, NIST 800-63B, GDPR).
- Modelado de amenazas en tres niveles (sistema, subsistema y componente) siguiendo STRIDE.
- Reglas de codificación segura, revisiones, pruebas (SAST, DAST, fuzzing) y criterios de liberación.
- Procedimientos de respuesta e instrumentación post despliegue.

Cada fase enlaza con tareas específicas en los repositorios de chat y de IA para que la implementación sea consistente.

## Diagramas

- **Secuencia de login** (mermaid) basado en el esquema proporcionado: `diagrams/login_sequence.mmd`.
- Diagramas de contexto, despliegue y flujo de datos adicionales se encuentran en `docs/architecture.md`.

Puedes renderizar los ficheros `.mmd` con [Mermaid CLI](https://github.com/mermaid-js/mermaid-cli) o usando la extensión oficial de VS Code.

## Cómo usar este repositorio

1. Lee `docs/methodology.md` para entender cómo aplicar Microsoft SDL en cada fase.
2. Sigue `docs/architecture.md` para implementar las integraciones técnicas (WebAuthn, RBAC, logging seguro, colas hacia el motor de IA).
3. Ejecuta las verificaciones de seguridad descritas en `docs/test_plan.md` antes de fusionar cambios.
4. Recopila los entregables solicitados (casos de uso, abuso, seguridad, modelado, reportes) usando `docs/deliverables.md` como checklist.
5. Consulta `docs/deployment.md` para configurar variables de entorno (gateway HTTPS, Windows Hello, Mongo/volúmenes) y para el procedimiento de verificación manual/CI.

## Microservicio Gateway Biométrico

El subdirectorio [`gateway/`](gateway) contiene un microservicio Flask que funciona como primer punto de contacto:

- Expone una UI mínima (`GET /`) que inicia registro/login por WebAuthn o Passkeys usando `navigator.credentials`.
- Gestiona retos, credenciales y auditoría en SQLite (`gateway/data/gateway.db`).
- Emite `biometricToken` (JWT) que el chat debe validar antes de abrir dashboards.
- Cada intento se envía al motor IA (`Proyecto-Software-seguro/python/app.py`) para etiquetar el riesgo.

### Configuración

```bash
cd Biometrico-Software-seguro/gateway
python -m venv .venv
.\.venv\Scripts\activate  # PowerShell en Windows
pip install -r requirements.txt

# Variables opcionales
set BIOMETRIC_RP_ID=localhost
set BIOMETRIC_ORIGIN=http://localhost:7000
set CHAT_FRONTEND_URL=http://localhost:5173
set AI_ANALYZER_URL=http://localhost:6000
set GATEWAY_JWT_SECRET=una-clave-larga

python app.py
```

Apunta el navegador a `http://localhost:7000` para ver la pantalla biométrica. Tras un login exitoso redirige al frontend del chat con `?biometricToken=...`. El backend del chat debe validar el token llamando a `POST /api/session/validate`.

> **Windows Hello / Huella:** en Windows 10/11 se selecciona automáticamente el flujo de Windows Hello. Si el dispositivo tiene lector de huellas, el prompt mostrará la opción “Usar Windows Hello o un dispositivo externo”. No se almacena la huella; únicamente se valida la firma de WebAuthn.

#### Endurecimiento

- Define `BIOMETRIC_RP_ID` y `BIOMETRIC_ORIGIN` por ambiente (dev/staging/prod) para que los retos WebAuthn coincidan con el dominio HTTPS real.
- Usa certificados propios (o auto firmados para pruebas) configurando `GATEWAY_SSL_CERT` y `GATEWAY_SSL_KEY`; el servidor se levantará directamente en HTTPS o puedes colocar un reverse proxy delante.
- Persiste la base de datos en volumen seguro o cambia a MongoDB estableciendo `GATEWAY_STORAGE_BACKEND=mongo`, `GATEWAY_MONGO_URI` y opcionalmente `GATEWAY_MONGO_DB` para despliegues multi instancia.

### Endpoints relevantes

| Método | Ruta | Descripción |
| --- | --- | --- |
| `GET /` | UI que activa WebAuthn | Primera pantalla visible |
| `POST /api/biometric/register/options` | Genera reto de registro | Usa WebAuthn / Passkeys |
| `POST /api/biometric/register/verify` | Guarda la credencial | Devuelve token + redirect |
| `POST /api/biometric/login/options` | Genera reto de login | Limita por usuario |
| `POST /api/biometric/login/verify` | Verifica autenticación | Llama al servicio IA |
| `POST /api/session/validate` | Valida `biometricToken` | Útil para el backend del chat |
| `GET /api/audit` | Últimos eventos | Muestra señales IA / STRIDE |
| `POST /api/security/ci-scan` | Endpoint usado por CI | Dispara análisis IA de cambios |

## Próximos pasos sugeridos

1. Implementar la capa de registro/login WebAuthn en `chat-espe-frontend-main/src` y `chat-espe-backend-main/auth.py` siguiendo las ideas del `docs/architecture.md`.
2. Automatizar llamadas hacia `Proyecto-Software-seguro/python/app.py` dentro de la pipeline existente para obtener resultados del modelo ML.
3. Actualizar los dashboards de admin/cliente con información de seguridad (logs, hallazgos, estado de sesiones) según los requerimientos funcionales.
4. Documentar ejecuciones de pruebas (SAST/DAST, escenarios biométricos, pentesting) en los reportes definidos en `docs/test_plan.md`.

> Este repositorio se mantendrá libre de credenciales y de código sensible; úsalo como punto único de referencia y documentación viva del proyecto.

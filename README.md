# Proyecto Software-Seguro — Chat con login biométrico integrado

Este directorio agrupa los componentes principales del proyecto **"Desarrollo de una Aplicación Full Stack de Login Seguro con Autenticación Biométrica"**. No contiene código propio complejo, sino que sirve como **raíz de trabajo** para coordinar varios subproyectos: gateway biométrico y un chat seguro.

La idea central es demostrar cómo un login biométrico basado en el dispositivo puede proteger el acceso a una aplicación real (un chat seguro con detección de esteganografía), aplicando una metodología de desarrollo seguro extremo a extremo.

## Estructura de carpetas

| Carpeta                         | Rol                               | Descripción breve                                                                                                                       |
| ------------------------------- | --------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `Biometrico-Software-seguro/` | Orquestador + Gateway Biométrico | Documentación SDL, modelado de amenazas, planes de prueba y microservicio Flask que implementa el login biométrico con WebAuthn/FIDO2. |
| `Chat-Software-seguro-main/`  | Chat seguro full stack            | Backend Flask con detección de esteganografía y frontend React/Vite para salas de chat con roles admin/cliente.                        |

## Componentes del sistema

### 1. Gateway biométrico (Biometrico-Software-seguro/gateway)

- Microservicio Flask que actúa como **primera capa de autenticación**.
- Usa APIs estándar del navegador WebAuthn para integrar la biometría del dispositivo Windows Hello con huella biometrica, **sin almacenar datos biométricos** en el servidor.
- Genera un token criptográfico `biometricToken` (JWT) tras un login exitoso, que representa una sesión autenticada de forma fuerte.
- Expone endpoints para:
  - Registro y login biométrico.
  - Validación de sesiones (`/api/session/validate`).
  - Auditoría y pruebas de seguridad (incluyendo un endpoint para escaneos desde CI).
- Se alinea con los requerimientos de:
  - **Login biométrico**.
  - **Seguridad y cifrado** al utilizar HTTPS, JWT con firma robusta y validaciones estrictas de origen.

### 2. Chat seguro full stack (Chat-Software-seguro-main)

Dividido en dos grandes partes:

- **Backend (chat-espe-backend-main/)**

  - API Flask que gestiona usuarios, roles, salas de chat, sesiones y subida de archivos.
  - Implementa detección de esteganografía y sanitización de archivos para prevenir abuso del canal de chat.
  - Integra el `biometricToken` proveniente del gateway para validar que toda operación sensible venga de una sesión autenticada biométricamente.
  - Expone endpoints para login de admin, gestión de salas, envío de mensajes y carga de archivos.
  - Soporta logs de seguridad, cuarentena de archivos sospechosos y configuración por variables de entorno.
- **Frontend (chat-espe-frontend-main/)**

  - Aplicación React + Vite con pantallas diferenciadas para **admin** y **cliente**.
  - Provee formularios de acceso, dashboard de administración (gestión de usuarios/salas) y vista de chat para clientes.
  - Integra WebSockets para chat en tiempo real.
  - Puede recibir o leer el `biometricToken` emitido por el gateway y adjuntarlo en las peticiones al backend.

Este componente cubre principalmente los requerimientos:

- **Roles y dashboards**:
  - Admin: dashboard con bienvenida, gestión de usuarios/salas, auditoría básica.
  - Cliente: vista de perfil y opciones limitadas (sin escalada de privilegios).
- **Logout seguro y sesiones**: manejo de sesiones con expiración y revocación.
- **Seguridad de archivos y mensajes**: validación estricta de entradas, sanitización de archivos, logs y soporte para pruebas de seguridad.
- **Arquitectura full stack y separación de capas**.

### 3. Metodología de desarrollo seguro y documentación (Biometrico-Software-seguro/docs)

En la carpeta `docs/` de Biometrico-Software-seguro se documenta:

- La metodología de desarrollo seguro usada es Microsoft SDL aplicada a todo el proyecto.
- El modelado de amenazas en tres niveles (sistema, subsistema y componente).
- Los diagramas de arquitectura, secuencia de login y flujo de datos.

## Flujo base de la aplicación (gateway + chat)

De forma simplificada, el flujo principal de uso es:

1. **Acceso inicial al gateway biométrico**El usuario abre el navegador y accede al gateway en Biometrico-Software-seguro/gateway. Desde allí se inicia un flujo WebAuthn/biométrico (Windows Hello).
2. **Autenticación biométrica local**El dispositivo del usuario (PC o laptop) muestra el prompt biométrico. La verificación se realiza **localmente** usando el hardware del dispositivo; el servidor sólo recibe una prueba criptográfica firmada, nunca la huella o el rostro.
3. **Emisión del biometricToken**Si la autenticación es correcta, el gateway genera un `biometricToken` (JWT) con la identidad del usuario, el rol previsto y una vigencia limitada. Luego redirige al frontend del chat o le provee el token para que lo use en la siguiente fase.
4. **Acceso al chat seguro**El frontend de Chat-Software-seguro-main recibe o lee el `biometricToken` y lo envía al backend en cada petición relevante (por encabezado Authorization: Bearer o similar).
5. **Validación de sesión en el backend**El backend del chat valida el token contra el endpoint del gateway (`/api/session/validate`) y sólo concede acceso si:

   - El token es válido y no ha expirado.
   - El rol (admin/cliente) coincide con lo que requiere la acción (por ejemplo, registrar usuarios sólo para admin).
6. **Dashboards por rol**

   - Si el usuario es **admin**, se muestra un dashboard con: bienvenida, creación/gestión de usuarios y salas, consulta de actividad y herramientas básicas de auditoría.
   - Si el usuario es **cliente**, se muestra un dashboard restringido: ver/editar parte de su perfil y acceder a las salas de chat que le correspondan.
7. **Chat y compartición segura de archivos**Durante la sesión, los mensajes y archivos pasan por el backend, que aplica controles de seguridad (detección de esteganografía, sanitización, logging). Esto refuerza los aspectos de seguridad y pruebas dinámicas del proyecto.
8. **Logout y expiración de sesión**
   Tanto desde el frontend como desde el backend, se soporta la finalización explícita de sesión y la expiración automática de tokens, cumpliendo el requerimiento de logout seguro.

Este flujo demuestra cómo el login biométrico es la **puerta de entrada** al sistema y cómo, una vez validada la identidad, los roles y controles de acceso se aplican en el chat seguro.

## Relación con los objetivos del proyecto

- **Objetivo (a): Login biométrico full stack**Se cumple mediante el gateway biométrico (frontend simple + backend Flask) integrado con el chat real como aplicación de negocio.
- **Objetivo (b): Metodología de desarrollo seguro**Documentada y aplicada en Biometrico-Software-seguro/docs, con referencias a Microsoft SDL/OWASP/NIST.
- **Objetivo (c): Roles admin y cliente**Implementados en el chat (dashboards diferenciados, controles de acceso) y reforzados por el `biometricToken`.
- **Objetivo (d): Modelado de amenazas en tres niveles**Cubierto por los documentos de threat modeling y los diagramas incluidos en Biometrico-Software-seguro.
- **Objetivo (f): Patrones de diseño y SOLID**
  El diseño modular (gateway separado del chat, separación frontend/backend, servicios especializados) facilita la aplicación de SOLID y patrones (por ejemplo, capas, repositorios, adaptadores) documentados en la arquitectura.

## Requisitos generales de entorno

A nivel de máquina de desarrollo, típicamente necesitarás:

- **Python** 3.10 o superior
- **Node.js** 18 o superior
- **Git**
- Opcional: **MongoDB Atlas** y **Redis** si vas a levantar todo el entorno como en la documentación del chat.

Cada subproyecto define sus dependencias exactas en sus propios `requirements.txt` o `package.json`.

## Flujo típico de desarrollo local

1. Abrir esta carpeta raíz `Proyecto-Soft-Seguro-Final/` en VS Code.
2. Configurar y levantar el **gateway biométrico** según las indicaciones de `Biometrico-Software-seguro/gateway/`.
3. Configurar y levantar el **backend** del chat desde `Chat-Software-seguro-main/chat-espe-backend-main/`.
4. Configurar y levantar el **frontend** del chat desde `Chat-Software-seguro-main/chat-espe-frontend-main/`.
5. Verificar que el flujo de login biométrico → obtención de `biometricToken` → acceso al chat seguro funcione extremo a extremo.
6. Ejecutar las pruebas de seguridad (estáticas y dinámicas) siguiendo lo indicado en los documentos de `docs/`.

### Autor

Proyecto integrador de Desarrollo de Software Seguro

Copyright © 2025 Kausas Entertainment.

# Modelado de Amenazas (Microsoft SDL)

El modelado se divide en tres niveles jerárquicos y usa STRIDE para clasificar amenazas. Los riesgos se puntúan con DREAD (1-10) y se priorizan según su severidad.

## Nivel 1: Sistema (End-to-End)

| ID | Evento | STRIDE | DREAD | Mitigaciones | Estado |
| --- | --- | --- | --- | --- | --- |
| SYS-01 | Ataques MITM entre cliente y backend durante WebAuthn | Tampering / Information Disclosure | 8 | TLS 1.3 obligatorio, HSTS, pinning de certificados opcional, validación origin/facet | Planeado |
| SYS-02 | Spoofing biométrico (huellas falsas, replay de respuestas WebAuthn) | Spoofing | 9 | Relying Party ID fijo, verificación de contador WebAuthn, detección de origen, bloqueo tras fallos consecutivos | En progreso |
| SYS-03 | Compromiso del motor IA que altera resultados | Tampering | 7 | Mutual TLS backend↔IA, firmas de payload, escaneo de integridad, RBAC fuerte en IA | Planeado |
| SYS-04 | Denegación de servicio por intentos masivos de login | DoS | 6 | Rate limiting IP+device, Captcha adaptativo, auto-escalado horizontal, alertas Telegram | Planeado |
| SYS-05 | Filtración de datos sensibles en logs/reporte IA | Information Disclosure | 7 | Redacción de datos, clasificación de logs, cifrado en reposo, políticas de retención | Planeado |

## Nivel 2: Subsystem (Autenticación, Chat, IA)

### Autenticación Biométrica

| ID | Amenaza | STRIDE | DREAD | Mitigaciones | Estado |
| --- | --- | --- | --- | --- | --- |
| AUTH-01 | Registro fraudulento de dispositivos | Spoofing | 7 | Requiere autenticación previa (MFA) antes de registrar nuevo dispositivo, aprobación admin | Planeado |
| AUTH-02 | Replay de challenge WebAuthn | Replay/Tampering | 6 | Nonces únicos, expiración 30 s, cacheo de challenges usados, sincronización reloj | Implementado (doc) |

### Chat Seguro

| ID | Amenaza | STRIDE | DREAD | Mitigaciones | Estado |
| --- | --- | --- | --- | --- | --- |
| CHAT-01 | Escalada de privilegios mediante tokens manipulados | Elevation of Privilege | 8 | JWT con audience, scopes, rotación de llaves, validación en cada socket event | Planeado |
| CHAT-02 | Esteganografía avanzada evade filtros existentes | Tampering | 7 | Nuevos clasificadores ML, revisión manual para nivel MEDIUM+, actualización constante | En progreso |
| CHAT-03 | Cross-Site Scripting en dashboards | XSS | 6 | Sanitización, CSP estricta, escaping en React, pruebas Playwright con payloads | En progreso |

### Motor IA

| ID | Amenaza | STRIDE | DREAD | Mitigaciones | Estado |
| --- | --- | --- | --- | --- | --- |
| IA-01 | Poisoning del modelo mediante datos manipulados | Tampering | 9 | Versionado de datasets, firmas, escaneo hash antes de entrenamiento, revisión humana | Planeado |
| IA-02 | Exposición de API `/analyze` sin autenticación | Information Disclosure | 8 | API Key + mTLS + WAF, rate limiting específico, auditoría de llamadas | Planeado |

## Nivel 3: Componentes

### Frontend

| ID | Componente | Amenaza | STRIDE | Mitigación |
| --- | --- | --- | --- | --- |
| FE-01 | Módulo WebAuthn | Bypass de políticas por manipular `navigator.credentials` | Spoofing | Feature detect + fallback seguro + integrity checks; firmar bundles con SRI |
| FE-02 | Dashboard Admin | Clickjacking | Tampering | `X-Frame-Options DENY`, limpiar `target`, doble confirmación acciones críticas |

### Backend

| ID | Componente | Amenaza | STRIDE | Mitigación |
| --- | --- | --- | --- | --- |
| BE-01 | `auth.py` | SQL/NoSQL injection | Tampering | ORMs con queries parametrizadas, validación de entrada, pruebas automáticas |
| BE-02 | `file_security.py` | Ejecución de malware en archivos subidos | Elevation of Privilege | Sandbox, verificación de tipo MIME real, antivirus, cuarentena |
| BE-03 | `rooms.py` | Enumeración de salas | Information Disclosure | IDs aleatorios, respuesta uniforme, monitor de intentos, honeypots |

### IA / Scripts

| ID | Componente | Amenaza | STRIDE | Mitigación |
| --- | --- | --- | --- | --- |
| IA-03 | `extract_features_from_diff.py` | Ejecución de código arbitrario al parsear diffs | Tampering | Ejecutar en entorno aislado, limpiar entrada, limitar tamaño diff |
| IA-04 | `generate_shap_report.py` | Divulgación de info sensible | Information Disclosure | Anonimizar resultados, controles de acceso a reportes |

## Suposiciones

- Todos los usuarios poseen dispositivos compatibles con WebAuthn/Passkeys.
- Las comunicaciones usan HTTPS con TLS 1.3.
- Los repositorios se alojan en un entorno controlado con políticas de ramas protegidas.

## Próximos pasos

1. Vincular cada amenaza con historias de usuario/épicas.
2. Revisar el modelo tras cada entrega mayor.
3. Adjuntar resultados de pruebas (SAST/DAST/IA) como evidencia de mitigación.

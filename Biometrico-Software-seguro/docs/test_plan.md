# Plan de Pruebas de Seguridad

Este plan cubre pruebas estáticas, dinámicas, biométricas y de integración con el motor de IA.

## 1. Alcance

- Frontend (React/Vite) con WebAuthn y dashboards por rol.
- Backend (Flask) con autenticación biométrica, RBAC, manejo de archivos.
- Motor IA (Flask ML) usado para SAST y reportes.
- Integraciones (Redis, MongoDB, WebSockets, colas de eventos).

## 2. Ambiente

| Ambiente | URL/IP | Uso |
| --- | --- | --- |
| Desarrollo | `http://localhost:5173`, `http://localhost:5000` | Iteraciones diarias, pruebas unitarias.
| Staging | `https://staging.chat-seguro.local` | Ensayos completos con WebAuthn real y datos ficticios.
| Producción | `https://chat-seguro.prod` | Monitoreo continuo y pruebas aprobadas (solo DAST pasivo).

## 3. Pruebas Estáticas (SAST)

| Herramienta | Objetivo | Ejecución |
| --- | --- | --- |
| `Proyecto-Software-seguro/scripts/extract_features_from_diff.py` | Evaluar diffs con modelo ML (RF) | GitHub Actions y jobs manuales, bloquea si riesgo ≥ 0.7 |
| `bandit`, `flake8`, `pip-audit` | Código y dependencias backend | `make lint-backend` |
| `eslint`, `npm audit`, `depcheck` | Frontend | `npm run lint && npm audit` |
| `semgrep` | Reglas OWASP Top10, WebSockets, WebAuthn | `semgrep scan --config p/owasp-top-ten` |

## 4. Pruebas Dinámicas (DAST)

| Herramienta | Escenario |
| --- | --- |
| OWASP ZAP Baseline | Escaneo pasivo de endpoints REST y WebSockets. |
| Playwright | Automatiza login biométrico (mock WebAuthn), flujos admin/cliente, subida de archivos. |
| Locust/K6 | Carga simultánea ≥ 100 usuarios; verifica tiempos < 2 s. |
| Custom Scripts | Intentos de spoofing, replay, manipulación de tokens, saturación de API IA. |

## 5. Pruebas Biométricas / WebAuthn

- **Registro**: validar dispositivos nuevos requieren autenticación previa y aprobación admin.
- **Login**: probar sensores reales (Windows Hello, TouchID, Android) y flujos de error (sensor no disponible, fallo lector, repetición de challenge).
- **Fallback**: OTP firmado, passkeys multiplataforma, recuperación con soporte.
- **Resiliencia**: ataques de replay, cambios de origen, manipulación de `clientDataJSON`.

## 6. Pruebas de Roles y Accesos

- Acceso admin con token cliente (debe fallar con 403).
- Intento de editar datos sensibles por cliente (rechazo + auditoría).
- Validar controles en WebSocket: eventos admin disponibles solo tras verificación de rol.

## 7. Pruebas de Archivos

- Cargar imágenes benignas y maliciosas con esteganografía conocida (OpenStego, Steghide, SilentEye).
- Fuerza bruta de extensiones y MIME falsos.
- Sanitización: verificar que metadatos EXIF se remuevan y archivos cuarentenados no sean accesibles.

## 8. Pruebas del Motor IA

- Endpoint `/analyze` con código seguro e inseguro (esperar `risk_score` correcto).
- Pruebas de precisión: `pytest tests/test_dummy.py` y suites adicionales (accuracy ≥ 82%).
- Integración: backend envía snippet + metadata, recibe respuesta y actúa según umbral.

## 9. Automatización CI/CD

- Jobs definidos en `Proyecto-Software-seguro/.github/workflows/ci-cd-pipeline.yml` deben ejecutarse en cada PR:
  - `security_analysis`
  - `merge_and_test`
  - `deploy_to_production`
- Repositorio del chat: workflow `biometric-ai-scan` (`.github/workflows/security-scan.yml`) ejecuta `scripts/ci_gateway_scan.py` y falla si el gateway devuelve nivel `MEDIA` o `CRITICA`.
- Añadir job `biometric_e2e` (Playwright) en el pipeline del chat.

## 10. Evidencias y Reportes

- Guardar resultados en `reports/` (HTML, JSON).
- Cargar métricas (cobertura, tiempo medio de respuesta, porcentaje de falsos positivos IA) en el informe final.
- Documentar hallazgos y mitigaciones en issues con etiquetas `security` y `severity`.

## 11. Criterios de Aceptación

- 0 hallazgos críticos abiertos.
- Máximo 2 hallazgos altos aceptados con plan.
- Cobertura pruebas unitarias ≥ 70% en backend, 60% en frontend.
- Accuracy IA ≥ 82% y validada antes de cada release.
- Tiempo de respuesta promedio login ≤ 2 s bajo carga de 100 usuarios simultáneos.

## 12. Calendario

| Fase | Fechas sugeridas |
| --- | --- |
| SAST diario | Automático en cada push |
| DAST + biométrico | Una vez por sprint, antes de pasar a staging |
| Pentest | Antes de lanzamiento oficial |
| Revalidación IA | Mensual o tras actualización de datasets |

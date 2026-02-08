# Aplicación de Microsoft SDL

La metodología adoptada para el proyecto es Microsoft Security Development Lifecycle (SDL). A continuación se detallan las actividades y entregables obligatorios por fase, conectando los tres repositorios implicados.

## 1. Training & Requirements

- **Capacitación**: Taller interno sobre WebAuthn, manejo seguro de biometría, OWASP Top 10, ASVS nivel 2, y amenazas específicas en WebSockets/file sharing.
- **Estándares**: Adoptar NIST 800-63B, FIDO2, GDPR, OWASP MASVS (para mobile) y CIS Benchmarks para servidores Linux.
- **Requisitos funcionales y no funcionales**: se documentan en `docs/architecture.md` y se rastrean en tickets. Cada requisito se etiqueta con `SEC-` o `FUNC-` para trazabilidad.
- **Criterios de aceptación**: autenticación biométrica exitosa, fallback seguro, RBAC granular, rendimiento < 2 s, cobertura de pruebas ≥ 80%, accuracy IA ≥ 82%.

## 2. Threat Modeling

- **Periodicidad**: uno por sprint y siempre que haya cambios mayores en autenticación o almacenamiento.
- **Herramientas**: Diagramas en Mermaid (repositorio actual) y plantillas STRIDE.
- **Salidas**: `docs/threat_model.md` con niveles (sistema, subsistema, componente), eventos de abuso y mitigaciones priorizadas por `DREAD`.
- **Validación**: revisar hallazgos de AI/ML y pruebas pentest para actualizar el modelo.

## 3. Secure Design

- **Principios**: defensa en profundidad, menor privilegio, fail-safe defaults, zero trust entre servicios.
- **Patrones**: Adapter/Strategy/Observer descritos en `docs/architecture.md`, aplicados tanto en frontend como backend.
- **Controles**:
  - WebAuthn obligatorio (RP ID: dominio oficial).
  - JWT firmados con rotación cada 12 h, tokens de refresco cifrados.
  - Rate limiting dual (IP + dispositivo).
  - Sanitización y detección de esteganografía antes del almacenamiento.
  - Logs firmados digitalmente para prevenir manipulación.

## 4. Secure Implementation

- **Checklist de Código Seguro**:
  - Frontend: ESLint reglas OWASP, `Content-Security-Policy` estricto, uso de `@simplewebauthn/browser`.
  - Backend: `bandit`, `flake8`, análisis de dependencias (`pip-audit`), validación estricta de payloads con `pydantic` o `marshmallow`.
  - IA: aislamiento de ambientes, validación de entrada antes de ejecutar scripts, revisión de modelos.
- **Revisiones de código**: mínimo 2 revisores, uno con enfoque de seguridad. Uso de listas de verificación específicas (autenticación, sesiones, archivos, IA, infraestructura).
- **Gestión de secretos**: `.env` locales para dev, secretos en Azure Key Vault/Render para prod; nunca subir claves a repos.

## 5. Verification

- **Pruebas Estáticas (SAST)**:
  - Ejecutar `Proyecto-Software-seguro/scripts/extract_features_from_diff.py` en cada PR.
  - `bandit`, `semgrep`, `npm audit` para detectar dependencias vulnerables.
- **Pruebas Dinámicas (DAST)**:
  - `owasp-zap-baseline` contra el backend (local o staging).
  - `Playwright` para flujos biométricos, `locust` para estrés.
  - Pentests enfocados en WebAuthn (replay, downgrade, MITM), WebSockets y subida de archivos.
- **Pruebas de Integración Continua**:
  - Pipeline en `Proyecto-Software-seguro/.github/workflows/ci-cd-pipeline.yml` se reutiliza para ejecutar pruebas y bloquear merges.

## 6. Release

- **Criterios de salida**:
  - Todos los hallazgos críticos/altos mitigados o aceptados formalmente.
  - Accuracy del modelo ML ≥ 82% y actualizado en `models/`.
  - Reporte de pruebas completado (`docs/test_plan.md`).
  - Manual de despliegue actualizado (ver `docs/deliverables.md`).
- **Hardening**:
  - Despliegue mediante contenedores con imágenes firmadas.
  - Proxy TLS con HSTS, CSP, OCSP stapling.
  - Monitorización en tiempo real (telemetría, dashboards, alertas Telegram).

## 7. Response

- **Plan**:
  - Playbooks para incidentes de autenticación, filtraciones de archivos, hallazgos críticos del motor IA.
  - Notificación a usuarios y autoridades según GDPR 72 h.
  - Retrospectiva de seguridad tras cada incidente para mejorar el SDL.
- **Monitoreo continuo**:
  - Logs enviados a SIEM, correlados con eventos de IA.
  - Scans automáticos semanales usando scripts de ML.

## Trazabilidad

Cada requisito, amenaza y control tendrá un identificador único (`SDL-###`). Los commits en los repositorios dependientes deben mencionar dichos IDs para mantener trazabilidad entre requisitos → diseño → implementación → pruebas → liberación.

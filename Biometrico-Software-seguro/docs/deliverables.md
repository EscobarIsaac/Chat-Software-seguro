# Checklist de Entregables

Usa esta lista para asegurar el cumplimiento de todos los requerimientos académicos y de la rúbrica.

## 1. Casos de Uso / Abuso / Seguridad

- [ ] **Casos de uso (UML)**: admin (registro, gestión), cliente (login, edición perfil). Formato Mermaid o PlantUML.
- [ ] **Casos de abuso**: spoofing biométrico, replay, escalada de privilegios, DoS. Cada uno con impacto y probabilidad.
- [ ] **Casos de seguridad**: MFA implícita, cifrado end-to-end, GDPR, logging seguro.

## 2. Modelado de Amenazas

- [ ] Documento `docs/threat_model.md` completado con los tres niveles.
- [ ] Diagramas / tablas STRIDE con estado de mitigaciones.
- [ ] Evidencias de revisión periódica (marcar fecha en el doc a medida que se actualice).

## 3. Pruebas

- [ ] Informe SAST (resultados de scripts ML + bandit + semgrep).
- [ ] Informe DAST (ZAP, Playwright, locust).
- [ ] Pruebas biométricas documentadas con capturas.
- [ ] Métricas: cobertura, accuracy IA, tiempos de respuesta.

## 4. Código Fuente Full Stack

- [ ] Repos `Chat-Software-seguro-main` y `Proyecto-Software-seguro` actualizados con cambios requeridos (WebAuthn, RBAC, IA integration).
- [ ] Comentarios explicativos en partes complejas, siguiendo lineamientos ASCII.
- [ ] Configuraciones de seguridad (env samples, rate limiting, logging) versionadas.

## 5. Documentación

- [ ] `README.md` principal actualizado (este repositorio).
- [ ] `docs/architecture.md`, `docs/methodology.md`, `docs/test_plan.md` y anexos.
- [ ] Guía de despliegue: describe infra, secretos, pasos para levantar los tres servicios.
- [ ] Anexos con diagramas Mermaid renderizados o compilados en PDF.

## 6. Diagramas requeridos

- [ ] Diagrama de secuencia (archivo `diagrams/login_sequence.mmd`).
- [ ] Diagramas de contexto/despliegue (en `docs/architecture.md`).
- [ ] Diagramas UML de casos de uso/abuso (pendiente de añadir en `docs/` o `diagrams/`).

## 7. Metodología Microsoft SDL

- [ ] Evidencia por fase: capacitación, threat modeling, secure design, implementation checklists, verification logs, release checklist, incident response plan.
- [ ] Matriz de trazabilidad requisitos ↔ historias ↔ pruebas (puede usarse hoja compartida o sección adicional).

## 8. Evaluación Final

- [ ] Matriz que mapea criterios de evaluación (backend, frontend, SDL, biometría, amenazas, pruebas, patrones, diagramas) con enlaces a evidencia.
- [ ] Presentación o demo que muestre login biométrico real, dashboards por rol y hallazgos IA.

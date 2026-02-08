# Guía de Despliegue y Verificación

Esta guía resume los pasos pendientes para operar el ecosistema biométrico/IA en ambientes reales.

## 1. Variables de entorno críticas

### Chat Backend (`chat-espe-backend-main/.env`)

```env
SECRET_KEY=<clave aleatoria>
MONGODB_URI=<cadena MongoDB Atlas>
MONGODB_DB_NAME=chat_espe
BIOMETRIC_GATEWAY_URL=https://gateway.mi-dominio.com
```

> Replica `BIOMETRIC_GATEWAY_URL` en GitHub Secrets bajo el mismo nombre para que el workflow `biometric-ai-scan` pueda contactar al gateway durante los PR.

### Gateway Biométrico (`Biometrico-Software-seguro/gateway`)

```env
BIOMETRIC_RP_ID=gateway.mi-dominio.com
BIOMETRIC_ORIGIN=https://gateway.mi-dominio.com
GATEWAY_SSL_CERT=/etc/ssl/private/gateway.crt
GATEWAY_SSL_KEY=/etc/ssl/private/gateway.key
GATEWAY_JWT_SECRET=<clave fuerte>
AI_ANALYZER_URL=https://ia.mi-dominio.com
GATEWAY_STORAGE_BACKEND=sqlite   # o "mongo"
GATEWAY_MONGO_URI=<solo si usas mongo>
GATEWAY_MONGO_DB=biometric_gateway
```

- **RP ID / Origin** deben coincidir con el dominio donde se publica el gateway para que Windows Hello/huella funcione (WebAuthn valida el dominio exacto).
- Si se habilita HTTPS local con certificados autofirmados, añade el dominio al archivo hosts (`127.0.0.1 gateway.local`) y confía en el certificado.

## 2. Persistencia del Gateway

- **SQLite (default)**: Monta la carpeta `Biometrico-Software-seguro/gateway/data/` en un volumen persistente (`docker run -v /srv/gateway-data:/app/gateway/data ...`).
- **MongoDB (alta disponibilidad)**: Exporta `GATEWAY_STORAGE_BACKEND=mongo` y `GATEWAY_MONGO_URI`. Se crearán colecciones `users`, `credentials`, `challenges`, `audit_logs`; habilita autenticación y TLS en tu cluster.

## 3. Pipeline CI

1. Configura el secreto `BIOMETRIC_GATEWAY_URL` en el repositorio del chat.
2. Opcional: añade `GATEWAY_API_KEY` si restringes `/api/security/ci-scan` por IP o token (puedes ampliar el endpoint para exigirlo).
3. Verifica que el workflow `biometric-ai-scan` aparece en la pestaña Actions tras un push; el trabajo falla si el gateway/IA devuelven nivel `MEDIA` o `CRITICA`.

## 4. Proceso de verificación manual

1. **Reinstala dependencias**:
   ```bash
   cd Biometrico-Software-seguro/gateway
   pip install -r requirements.txt
   python app.py
   ```
   (Incluye `pymongo` automáticamente.)
2. **Reinicia backend y frontend** para tomar `BIOMETRIC_GATEWAY_URL` y el nuevo flujo.
3. **Autenticación biométrica**:
   - Accede a `https://gateway.mi-dominio.com`.
   - Registra tu usuario usando Windows Hello (lector de huella).
   - Tras el login, deberías ser redirigido al frontend con `?biometricToken=...`.
4. **Flujos a comprobar**:
   - Admin login y dashboard (todas las peticiones deben incluir `Authorization: Bearer <token>`).
   - Creación de salas, subida de archivos y unión via Socket.IO (revisar logs del backend para ver `Biometric token inválido` en caso de error).
5. **Pipeline**: abre un PR o push a ramas `dev/test/main` y revisa en GitHub Actions que la tarea `Run IA scan via gateway` contacta al endpoint `/api/security/ci-scan`.

## 5. Almacenamiento seguro

- Haz backup periódico de `gateway/data/gateway.db` o las colecciones Mongo.
- Limita el acceso a la carpeta/cuenta que guarda los certificados (`GATEWAY_SSL_KEY`).
- Registra todos los eventos de gateway en tu SIEM exportando los `audit_logs` (puedes añadir un job que lea `/api/audit`).

## 6. Checklist de despliegue

- [ ] Certificados TLS instalados y vigentes.
- [ ] RP ID y origins actualizados por ambiente (dev/staging/prod).
- [ ] Gateway levantado con volumen persistente o Mongo replicado.
- [ ] Backend apuntando al gateway + secrets configurados en GitHub.
- [ ] Pipeline `biometric-ai-scan` ejecutándose en cada PR.
- [ ] Pruebas manuales (login, admin, archivos, sockets) documentadas en `docs/test_plan.md`.

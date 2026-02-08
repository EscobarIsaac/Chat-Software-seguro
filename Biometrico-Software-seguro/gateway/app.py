from __future__ import annotations

import base64
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from flask import (Flask, Response, jsonify, render_template, request,
                   stream_with_context)
from flask_cors import CORS
from webauthn import (generate_authentication_options,
                      generate_registration_options,
                      verify_authentication_response,
                      verify_registration_response)
from webauthn.helpers import bytes_to_base64url
from webauthn.helpers.structs import (AuthenticationCredential,
                                      AttestationConveyancePreference,
                                      AuthenticatorSelectionCriteria,
                                      PublicKeyCredentialDescriptor,
                                      RegistrationCredential,
                                      ResidentKeyRequirement,
                                      UserVerificationRequirement)
from urllib.parse import urlencode, urljoin

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.append(str(CURRENT_DIR))

from config import settings  # noqa: E402
from security import (SecurityIntelligenceClient, TokenService,
                      classify_ai_signal)  # noqa: E402
from storage import create_store  # noqa: E402
from notifications import EmailNotifier  # noqa: E402

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='templates')
CORS(app)

store = create_store(settings)
token_service = TokenService(settings.jwt_secret, settings.jwt_ttl_seconds)
ai_client = SecurityIntelligenceClient(settings.ai_base_url,
                                       settings.analytics_timeout)
email_notifier = EmailNotifier(settings)


def _encode_bytes(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode('ascii').rstrip('=')


def _decode_to_bytes(value: str) -> bytes:
    padding = '=' * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _ensure_text(value: Any) -> str:
    if isinstance(value, bytes):
        return value.decode('utf-8')
    return str(value)


def _build_redirect(token: str) -> str:
    separator = '&' if '?' in settings.chat_frontend_url else '?'
    return f"{settings.chat_frontend_url}{separator}biometricToken={token}"


def _build_absolute_url(path: str) -> str:
    return urljoin(f"{settings.origin}/", path.lstrip('/'))


def _build_decision_url(request_id: str, token: str, action: str) -> str:
    query = urlencode({'action': action, 'token': token})
    base = getattr(settings, 'public_base_url', settings.origin)
    return urljoin(f"{base}/",
                   f"api/biometric/register/decision/{request_id}?{query}")


def _sse(payload: Dict[str, Any], event: str = 'message') -> str:
    return f"event: {event}\ndata: {json.dumps(payload)}\n\n"


@app.route('/')
def index() -> str:
    return render_template('index.html',
                           rp_id=settings.rp_id,
                           origin=settings.origin,
                           chat_url=settings.chat_frontend_url)


@app.route('/health', methods=['GET'])
def health() -> Any:
    events = store.latest_events(limit=5)
    return jsonify({
        "service": "biometric-gateway",
        "rp_id": settings.rp_id,
        "chat_frontend": settings.chat_frontend_url,
        "ai_url": settings.ai_base_url,
        "events_cached": len(events)
    })


@app.route('/api/biometric/register/request', methods=['POST'])
def biometric_register_request() -> Any:
    data = request.get_json(force=True)
    username = data.get('username', '').strip()
    if not username:
        return jsonify({"error": "username requerido"}), 400
    role = data.get('role', settings.default_role)
    display_name = data.get('displayName', username)
    requester_email = data.get('email')

    if not email_notifier.enabled:
        return jsonify({
            "error": "Servidor de correo no configurado. Define ADMIN_EMAIL y SMTP_*"
        }), 503

    record = store.create_registration_request(username=username,
                                               display_name=display_name,
                                               role=role,
                                               requester_email=requester_email)

    approve_url = _build_decision_url(record['id'], record['approval_token'],
                                      'approve')
    reject_url = _build_decision_url(record['id'], record['approval_token'],
                                     'reject')

    try:
        sent = email_notifier.send_registration_request(record, approve_url,
                                                        reject_url)
    except RuntimeError as err:
        logger.exception('Error enviando correo de autorización: %s', err)
        store.update_registration_request_status(record['id'],
                                                 'error',
                                                 notes=str(err))
        return jsonify({
            "error": "No se pudo enviar la notificación al administrador",
            "requestId": record['id']
        }), 502

    if not sent:
        logger.error('Fallo al enviar correo de autorización para %s',
                     username)
        store.update_registration_request_status(record['id'],
                                                 'error',
                                                 notes='email_failed')
        return jsonify({
            "error": "No se pudo enviar la notificación al administrador",
            "requestId": record['id']
        }), 502

    store.log_event('registration.request',
                    payload={
                        'request_id': record['id'],
                        'username': username,
                        'display_name': display_name,
                        'role': role
                    },
                    user_id=None)

    return jsonify({
        "requestId": record['id'],
        "status": record['status'],
        "notification": "sent"
    })


@app.route('/api/biometric/register/status/<request_id>', methods=['GET'])
def biometric_register_status(request_id: str) -> Any:
    record = store.get_registration_request(request_id)
    if not record:
        return jsonify({"error": "request no encontrado"}), 404
    return jsonify({
        "requestId": record['id'],
        "status": record['status'],
        "updatedAt": record.get('updated_at'),
        "username": record.get('username'),
        "role": record.get('role')
    })


@app.route('/api/biometric/register/stream/<request_id>', methods=['GET'])
def biometric_register_stream(request_id: str) -> Response:
    timeout_seconds = int(request.args.get('timeout', '180') or 180)
    timeout_seconds = max(30, min(timeout_seconds, 600))

    def stream() -> Any:
        last_status: Optional[str] = None
        start = time.time()
        yield f"retry: 2000\n\n"
        while time.time() - start < timeout_seconds:
            record = store.get_registration_request(request_id)
            if not record:
                yield _sse({"status": "not_found", "requestId": request_id},
                           event='end')
                return

            status = record.get('status')
            if status != last_status:
                yield _sse({
                    "status": status,
                    "requestId": request_id,
                    "updatedAt": record.get('updated_at')
                }, event='update')
                last_status = status
                if status in {'approved', 'rejected', 'completed'}:
                    return

            time.sleep(1)

        yield _sse({
            "status": last_status or 'timeout',
            "requestId": request_id
        }, event='timeout')

    response = Response(stream_with_context(stream()),
                        mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'
    return response


@app.route('/api/biometric/register/decision/<request_id>', methods=['GET'])
def biometric_register_decision(request_id: str) -> Any:
    action = (request.args.get('action') or '').strip().lower()
    token = (request.args.get('token') or '').strip()
    if action not in {'approve', 'reject'} or not token:
        return render_template('decision.html',
                               status='error',
                               message='Solicitud inválida'), 400

    record = store.get_registration_request_by_token(request_id, token)
    if not record:
        return render_template('decision.html',
                               status='error',
                               message='No se encontró la solicitud o el token expiró'), 404

    if record.get('status') not in {'pending'}:
        return render_template('decision.html',
                               status=record.get('status'),
                               message='Esta solicitud ya fue procesada.'), 200

    new_status = 'approved' if action == 'approve' else 'rejected'
    updated = store.update_registration_request_status(request_id, new_status)

    store.log_event('registration.decision',
                    payload={
                        'request_id': request_id,
                        'action': new_status,
                        'username': record.get('username')
                    },
                    user_id=None)

    return render_template('decision.html',
                           status=new_status,
                           request=updated,
                           message='Solicitud procesada correctamente.')


@app.route('/api/biometric/register/options', methods=['POST'])
def biometric_register_options() -> Any:
    data = request.get_json(force=True)
    username = data.get('username', '').strip()
    if not username:
        return jsonify({"error": "username requerido"}), 400
    role = data.get('role', settings.default_role)
    display_name = data.get('displayName', username)
    approval_id = data.get('approvalRequestId')

    if not approval_id:
        return jsonify({"error": "approvalRequestId requerido"}), 400

    approval = store.get_registration_request(approval_id)
    if not approval or approval.get('status') != 'approved':
        return jsonify({"error": "La solicitud aún no está autorizada"}), 403

    if approval.get('username') != username:
        return jsonify({"error": "La solicitud no coincide con el usuario"}), 409

    user = store.upsert_user(username=username,
                             display_name=display_name,
                             role=role)
    user_id = _ensure_text(user['id'])

    # webauthn.generate_registration_options espera un user_id tipo str y él mismo aplica .encode
    options = generate_registration_options(
        rp_id=settings.rp_id,
        rp_name=settings.rp_name,
        user_id=user_id,
        user_name=user['username'],
        user_display_name=user['display_name'],
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.PREFERRED,
            user_verification=UserVerificationRequirement.REQUIRED),
        attestation=AttestationConveyancePreference.NONE
        if settings.attestation == 'none' else
        AttestationConveyancePreference.DIRECT)

    store.save_challenge(
        challenge=_encode_bytes(options.challenge),
        purpose='registration',
        user_id=user_id)

    payload = json.loads(options.json(by_alias=True))
    return jsonify({
        "options": payload,
        "user": user,
        "requestId": approval_id
    })


@app.route('/api/biometric/register/verify', methods=['POST'])
def biometric_register_verify() -> Any:
    data = request.get_json(force=True)
    username = data.get('username')
    credential_payload = data.get('credential')
    approval_id = data.get('approvalRequestId')
    if not username or not credential_payload:
        return jsonify({"error": "datos incompletos"}), 400

    user = store.find_user_by_username(username)
    if not user:
        return jsonify({"error": "usuario no encontrado"}), 404

    if approval_id:
        approval = store.get_registration_request(approval_id)
        if not approval or approval.get('status') not in {'approved', 'completed'}:
            return jsonify({"error": "Solicitud aún no autorizada"}), 403
        if approval.get('username') != username:
            return jsonify({"error": "Solicitud no coincide"}), 409

    user_id = _ensure_text(user['id'])
    expected_challenge = store.pop_challenge('registration', user_id)
    if not expected_challenge:
        return jsonify({"error": "challenge expirado"}), 400

    credential = RegistrationCredential.parse_raw(
        json.dumps(credential_payload))

    verification = verify_registration_response(
        credential=credential,
        expected_challenge=_decode_to_bytes(expected_challenge),
        expected_rp_id=settings.rp_id,
        expected_origin=settings.origin,
        require_user_verification=True)

    credential_id = bytes_to_base64url(verification.credential_id)
    store.save_credential(user_id=user_id,
                          credential_id=credential_id,
                          public_key=verification.credential_public_key,
                          sign_count=verification.sign_count,
                          transports=credential_payload.get('transports'))

    event_payload = {
        "event": "registration",
        "username": user['username'],
        "role": user['role'],
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": approval_id
    }
    ai_result = ai_client.analyze_event(event_payload)
    store.log_event('biometric.registration',
                    payload=event_payload,
                    user_id=user_id,
                    ai_level=classify_ai_signal(ai_result))

    if approval_id:
        store.mark_registration_completed(approval_id)

    token = token_service.issue(user_id, user['username'], user['role'])
    return jsonify({
        "verified": True,
        "token": token,
        "redirect": _build_redirect(token),
        "ai_signal": ai_result
    })


@app.route('/api/biometric/login/options', methods=['POST'])
def biometric_login_options() -> Any:
    data = request.get_json(force=True)
    username = data.get('username', '').strip()
    if not username:
        return jsonify({"error": "username requerido"}), 400

    user = store.find_user_by_username(username)
    if not user:
        return jsonify({"error": "usuario no registrado"}), 404

    credentials = store.list_credentials(user['id'])
    if not credentials:
        return jsonify({"error": "sin credenciales registradas"}), 400

    allow_credentials: List[PublicKeyCredentialDescriptor] = []
    for cred in credentials:
        try:
            transports_raw = cred.get('transports')
            if isinstance(transports_raw, str):
                transports_value = json.loads(transports_raw or '[]')
            else:
                transports_value = transports_raw or []

            allow_credentials.append(
                PublicKeyCredentialDescriptor(
                    id=_decode_to_bytes(cred['credential_id']),
                    transports=transports_value))
        except Exception:  # noqa: BLE001
            continue

    options = generate_authentication_options(
        rp_id=settings.rp_id,
        allow_credentials=allow_credentials,
        user_verification=UserVerificationRequirement.REQUIRED)

    store.save_challenge(
        challenge=_encode_bytes(options.challenge),
        purpose='authentication',
        user_id=user['id'])

    payload = json.loads(options.json(by_alias=True))
    return jsonify({"options": payload, "user": user})


@app.route('/api/biometric/login/verify', methods=['POST'])
def biometric_login_verify() -> Any:
    data = request.get_json(force=True)
    username = data.get('username')
    credential_payload = data.get('credential')
    if not username or not credential_payload:
        return jsonify({"error": "datos incompletos"}), 400

    user = store.find_user_by_username(username)
    if not user:
        return jsonify({"error": "usuario no encontrado"}), 404

    user_id = _ensure_text(user['id'])
    expected_challenge = store.pop_challenge('authentication', user_id)
    if not expected_challenge:
        return jsonify({"error": "challenge expirado"}), 400

    credential = AuthenticationCredential.parse_raw(
        json.dumps(credential_payload))

    credential_records = store.list_credentials(user_id)
    credential_id = credential_payload.get('id')
    target = next((c for c in credential_records
                   if c['credential_id'] == credential_id), None)
    if not target:
        return jsonify({"error": "credencial no encontrada"}), 404

    verification = verify_authentication_response(
        credential=credential,
        expected_challenge=_decode_to_bytes(expected_challenge),
        expected_rp_id=settings.rp_id,
        expected_origin=settings.origin,
        credential_public_key=target['public_key'],
        credential_current_sign_count=target['sign_count'],
        require_user_verification=True)

    new_count = getattr(verification, 'new_sign_count', None)
    if new_count is None:
        new_count = getattr(verification, 'sign_count', target['sign_count'])
    store.update_sign_count(target['credential_id'], new_count)

    event_payload = {
        "event": "login",
        "username": user['username'],
        "role": user['role'],
        "device": credential_payload.get('id'),
        "timestamp": datetime.utcnow().isoformat()
    }
    ai_result = ai_client.analyze_event(event_payload)
    store.log_event('biometric.login',
                    payload=event_payload,
                    user_id=user_id,
                    ai_level=classify_ai_signal(ai_result))

    token = token_service.issue(user_id, user['username'], user['role'])
    return jsonify({
        "verified": True,
        "token": token,
        "redirect": _build_redirect(token),
        "ai_signal": ai_result
    })


@app.route('/api/session/validate', methods=['POST'])
def validate_session() -> Any:
    data = request.get_json(force=True)
    token = data.get('token')
    if not token:
        return jsonify({"error": "token requerido"}), 400

    claims = token_service.validate(token)
    if not claims:
        return jsonify({"active": False}), 401

    return jsonify({"active": True, "claims": claims})


@app.route('/api/audit', methods=['GET'])
def audit_events() -> Any:
    limit = int(request.args.get('limit', '20'))
    events = store.latest_events(limit=limit)
    return jsonify({"events": events})


@app.route('/api/security/ci-scan', methods=['POST'])
def ci_scan() -> Any:
    payload = request.get_json(force=True)
    if not payload:
        return jsonify({"error": "payload requerido"}), 400

    ai_result = ai_client.analyze_event(payload)
    ai_level = classify_ai_signal(ai_result)

    store.log_event('ci.scan',
                    payload=payload,
                    user_id=None,
                    ai_level=ai_level)

    status_code = 200 if ai_result else 503
    return jsonify({
        "received": True,
        "analysis": ai_result,
        "ai_level": ai_level
    }), status_code


if __name__ == '__main__':
    ssl_context = None
    if settings.ssl_cert_path and settings.ssl_key_path:
        ssl_context = (settings.ssl_cert_path, settings.ssl_key_path)

    port = int(os.environ.get('GATEWAY_PORT', '7000'))
    app.run(host='0.0.0.0', port=port, debug=False, ssl_context=ssl_context)

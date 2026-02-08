import logging
import smtplib
import ssl
from datetime import datetime
from email.message import EmailMessage
from typing import Any, Dict, Optional


logger = logging.getLogger(__name__)


def _to_bool(value: Any, default: bool = True) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {'1', 'true', 'yes', 'on'}
    return bool(value)


class EmailNotifier:
    """Simple SMTP helper to notify the admin about biometric requests."""

    def __init__(self, settings):
        self.admin_email: Optional[str] = getattr(
            settings, 'admin_email', None)
        self.smtp_host: Optional[str] = getattr(settings, 'smtp_host', None)
        self.smtp_port: int = int(getattr(settings, 'smtp_port', 587) or 587)
        self.smtp_username: Optional[str] = getattr(
            settings, 'smtp_username', None)
        self.smtp_password: Optional[str] = getattr(
            settings, 'smtp_password', None)
        self.smtp_use_tls: bool = _to_bool(
            getattr(settings, 'smtp_use_tls', True))
        self.smtp_use_ssl: bool = _to_bool(
            getattr(settings, 'smtp_use_ssl', False))
        self.smtp_sender: Optional[str] = getattr(
            settings, 'smtp_sender', None)
        self._ssl_context = ssl.create_default_context()

    @property
    def enabled(self) -> bool:
        return bool(self.smtp_host and self.admin_email)

    def send_registration_request(self, request: Dict[str, Any], approve_url: str,
                                  reject_url: str) -> bool:
        if not self.enabled:
            logger.info('Email notifier disabled; skipping admin notification for %s',
                        request.get('id'))
            return False

        subject = 'Autorización de registro biométrico requerida'
        text_body = (
            f"Se solicitó un registro biométrico para el usuario {request.get('username')}\n"
            f"Rol: {request.get('role')}\n"
            f"Solicitud: {request.get('id')}\n"
            f"Aprobar: {approve_url}\nRechazar: {reject_url}\n"
        )
        html_body = self._build_registration_html(
            request, approve_url, reject_url)

        message = EmailMessage()
        message['Subject'] = subject
        message['From'] = self.smtp_sender or self.admin_email
        message['To'] = self.admin_email
        message.set_content(text_body)
        message.add_alternative(html_body, subtype='html')

        try:
            if not self.smtp_host:
                raise RuntimeError('SMTP host no configurado')

            if self.smtp_use_ssl:
                smtp_client = smtplib.SMTP_SSL(
                    self.smtp_host, self.smtp_port, timeout=15, context=self._ssl_context)
            else:
                smtp_client = smtplib.SMTP(
                    self.smtp_host, self.smtp_port, timeout=15)

            with smtp_client as client:
                client.ehlo()
                if self.smtp_use_tls and not self.smtp_use_ssl:
                    client.starttls(context=self._ssl_context)
                    client.ehlo()
                if self.smtp_username and self.smtp_password:
                    client.login(self.smtp_username, self.smtp_password)
                client.send_message(message)
            logger.info('Notificación de registro enviada a %s',
                        self.admin_email)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.warning('No se pudo enviar la notificación: %s', exc)
            return False

    def _build_registration_html(self, request: Dict[str, Any], approve_url: str,
                                 reject_url: str) -> str:
        created_at = request.get('created_at')
        timestamp = None
        if created_at:
            try:
                timestamp = datetime.fromtimestamp(
                    float(created_at)).strftime('%Y-%m-%d %H:%M')
            except Exception:  # noqa: BLE001
                timestamp = None

        info_rows = ''.join([
            f'<p><strong>Usuario:</strong> {request.get("username")}</p>',
            f'<p><strong>Nombre:</strong> {request.get("display_name") or "(sin especificar)"}</p>',
            f'<p><strong>Rol solicitado:</strong> {request.get("role")}</p>',
            f'<p><strong>Solicitud:</strong> {request.get("id")}</p>',
            f'<p><strong>Creado:</strong> {timestamp or "(sin fecha)"}</p>',
        ])

        button_style = (
            'display:inline-block;padding:14px 28px;margin:8px;color:#fff;font-weight:600;'
            'text-decoration:none;border-radius:8px;font-family:Segoe UI,Arial,sans-serif;'
        )
        approve_button = (
            f'<a href="{approve_url}" style="{button_style}background:#16a34a;">'
            'Autorizar registro</a>'
        )
        reject_button = (
            f'<a href="{reject_url}" style="{button_style}background:#dc2626;">'
            'Rechazar solicitud</a>'
        )

        return (
            '<div style="font-family:Segoe UI,Arial,sans-serif;background:#0f172a;color:#e2e8f0;padding:24px;">'
            '<h2 style="color:#38bdf8;">Se requiere autorización biométrica</h2>'
            '<p>Un usuario está solicitando registrar su dispositivo biométrico.</p>'
            f'{info_rows}'
            '<div style="margin-top:20px;">'
            f'{approve_button}{reject_button}'
            '</div>'
            '<p style="margin-top:24px;font-size:12px;color:#94a3b8;">'
            'Si no esperabas este correo, ignóralo.</p>'
            '</div>'
        )

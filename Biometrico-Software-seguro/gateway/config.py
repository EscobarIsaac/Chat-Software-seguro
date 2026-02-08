import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv


@dataclass
class Settings:
    project_root: Path
    data_dir: Path
    rp_id: str
    rp_name: str
    origin: str
    attestation: str
    chat_frontend_url: str
    chat_backend_url: str
    chat_admin_user: str
    chat_admin_password: str
    ai_base_url: str
    jwt_secret: str
    jwt_ttl_seconds: int
    default_role: str
    analytics_timeout: float
    storage_backend: str
    mongo_uri: Optional[str]
    mongo_db: str
    ssl_cert_path: Optional[str]
    ssl_key_path: Optional[str]
    admin_email: Optional[str]
    smtp_host: Optional[str]
    smtp_port: int
    smtp_username: Optional[str]
    smtp_password: Optional[str]
    smtp_use_tls: bool
    smtp_use_ssl: bool
    smtp_sender: Optional[str]
    public_base_url: str


def _str_to_bool(value: str, default: bool = True) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {'1', 'true', 'yes', 'y', 'on'}


def load_settings() -> Settings:
    root = Path(__file__).resolve().parents[1]
    env_file = Path(__file__).resolve().parent / '.env'
    load_dotenv(dotenv_path=env_file, override=False)
    data_dir = Path(os.environ.get('GATEWAY_DATA_DIR', root / 'gateway' /
                                   'data'))
    data_dir.mkdir(parents=True, exist_ok=True)

    return Settings(
        project_root=root,
        data_dir=data_dir,
        rp_id=os.environ.get('BIOMETRIC_RP_ID', 'localhost'),
        rp_name=os.environ.get('BIOMETRIC_RP_NAME',
                               'Biométrico Secure Gateway').strip()
        or 'Biométrico Secure Gateway',
        origin=os.environ.get('BIOMETRIC_ORIGIN',
                      'http://localhost:7000').rstrip('/'),
        attestation=os.environ.get('BIOMETRIC_ATTESTATION', 'none'),
        chat_frontend_url=os.environ.get('CHAT_FRONTEND_URL',
                                         'http://localhost:5173'),
        chat_backend_url=os.environ.get('CHAT_BACKEND_URL',
                                        'http://localhost:5000'),
        chat_admin_user=os.environ.get('CHAT_ADMIN_USER', 'admin'),
        chat_admin_password=os.environ.get('CHAT_ADMIN_PASSWORD',
                                           'espe2025'),
        ai_base_url=os.environ.get('AI_ANALYZER_URL',
                                   'http://localhost:6000'),
        jwt_secret=os.environ.get('GATEWAY_JWT_SECRET',
                                  'change-this-secret'),
        jwt_ttl_seconds=int(os.environ.get('GATEWAY_JWT_TTL', '900')),
        default_role=os.environ.get('DEFAULT_USER_ROLE', 'cliente'),
        analytics_timeout=float(os.environ.get('AI_TIMEOUT_SECONDS', '5.0')),
        storage_backend=os.environ.get('GATEWAY_STORAGE_BACKEND',
                                       'sqlite').lower(),
        mongo_uri=os.environ.get('GATEWAY_MONGO_URI'),
        mongo_db=os.environ.get('GATEWAY_MONGO_DB', 'biometric_gateway'),
        ssl_cert_path=os.environ.get('GATEWAY_SSL_CERT'),
        ssl_key_path=os.environ.get('GATEWAY_SSL_KEY'),
        admin_email=os.environ.get('ADMIN_EMAIL'),
        smtp_host=os.environ.get('SMTP_HOST'),
        smtp_port=int(os.environ.get('SMTP_PORT', '587') or 587),
        smtp_username=os.environ.get('SMTP_USERNAME'),
        smtp_password=os.environ.get('SMTP_PASSWORD'),
        smtp_use_tls=_str_to_bool(os.environ.get('SMTP_USE_TLS', 'true')),
        smtp_use_ssl=_str_to_bool(os.environ.get('SMTP_USE_SSL', 'false')),
        smtp_sender=os.environ.get('SMTP_SENDER'),
        public_base_url=os.environ.get('GATEWAY_PUBLIC_BASE',
                           os.environ.get('BIOMETRIC_ORIGIN',
                                  'http://localhost:7000')).rstrip('/'))


settings = load_settings()

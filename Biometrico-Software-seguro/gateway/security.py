import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import jwt
import requests

logger = logging.getLogger(__name__)


class TokenService:
    def __init__(self, secret: str, ttl_seconds: int):
        self.secret = secret
        self.ttl_seconds = ttl_seconds

    def issue(self, user_id: str, username: str, role: str) -> str:
        now = datetime.utcnow()
        payload = {
            "sub": user_id,
            "username": username,
            "role": role,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(seconds=self.ttl_seconds)).timestamp())
        }
        return jwt.encode(payload, self.secret, algorithm='HS256')

    def validate(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            # Permitimos un pequeño desfase de tiempo e ignoramos la validación estricta de 'iat'.
            return jwt.decode(token,
                              self.secret,
                              algorithms=['HS256'],
                              options={"verify_iat": False})
        except jwt.PyJWTError as exc:
            logger.warning("Token inválido: %s", exc)
            return None


class SecurityIntelligenceClient:
    def __init__(self, base_url: str, timeout: float):
        self.base_url = base_url.rstrip('/') if base_url else ''
        self.timeout = timeout

    def analyze_event(self, event_payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not self.base_url:
            return None
        try:
            snippet = json.dumps(event_payload, ensure_ascii=True)
            response = requests.post(f"{self.base_url}/analyze",
                                     json={"code": snippet},
                                     timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            return {
                "prob_vulnerable": data.get('prob_vulnerable', 0.0),
                "prob_safe": data.get('prob_safe', 0.0),
                "alert_level": data.get('alert_level', 'BAJA'),
                "message": data.get('message')
            }
        except requests.RequestException as exc:
            logger.warning("No se pudo contactar al servicio IA: %s", exc)
            return None


def classify_ai_signal(ai_result: Optional[Dict[str, Any]]) -> str:
    if not ai_result:
        return 'DESCONOCIDO'
    level = ai_result.get('alert_level', 'BAJA')
    return level.upper()

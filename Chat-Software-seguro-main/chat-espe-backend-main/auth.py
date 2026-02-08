import os
from datetime import datetime, timezone

import bcrypt

from models import db

admins = db['admins']

# CREDENCIALES DEL ADMIN POR DEFECTO
ADMIN_USER = os.environ.get('DEFAULT_ADMIN_USERNAME', 'admin')
DEFAULT_ADMIN_HASH = os.environ.get(
    'DEFAULT_ADMIN_HASH',
    '$2a$12$8dgp4N3xGN3xPzVXFrEmxeZN3nS2o3qXTqaObQsoTvjeiaCY3llei'
)


def ensure_default_admin():
    """Inserta un admin base si aún no existe."""
    existing = admins.find_one({"username": ADMIN_USER})
    if existing:
        print(f"Admin por defecto '{ADMIN_USER}' ya existe en MongoDB")
        return

    admins.insert_one({
        "username": ADMIN_USER,
        "password_hash": DEFAULT_ADMIN_HASH,
        "roles": ["admin"],
        "createdAt": datetime.now(timezone.utc)
    })
    print(f"Admin por defecto '{ADMIN_USER}' creado en MongoDB")


def verify_admin(username, password):
    admin = admins.find_one({"username": username})

    if not admin and username == ADMIN_USER:
        # Si falta el admin por defecto, re-crearlo automáticamente
        ensure_default_admin()
        admin = admins.find_one({"username": username})

    if not admin or 'password_hash' not in admin:
        return False

    stored_hash = admin['password_hash']
    if isinstance(stored_hash, str):
        stored_hash = stored_hash.encode('utf-8')
    elif not isinstance(stored_hash, (bytes, bytearray)):
        return False

    return bcrypt.checkpw(password.encode('utf-8'), stored_hash)

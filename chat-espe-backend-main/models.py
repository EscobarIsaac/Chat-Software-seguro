# models.py
from pymongo import MongoClient
import certifi
import threading
import os
from urllib.parse import urlsplit, urlunsplit
from dotenv import load_dotenv

load_dotenv()

# === MONGODB_URI: OBLIGATORIO EN PROD, OPCIONAL EN DEV ===
MONGODB_URI = os.environ.get('MONGODB_URI')

if not MONGODB_URI:
    if os.environ.get('FLASK_ENV') == 'production':
        raise ValueError("Falta MONGODB_URI en producción")
    else:
        print(
            "MONGODB_URI no definido → Usando MongoDB local (127.0.0.1:27017)")
        MONGODB_URI = "mongodb://127.0.0.1:27017/"

# Construir kwargs condicionales para TLS (necesario en Atlas, no en local)
client_kwargs = {
    'serverSelectionTimeoutMS': 30000,
}
if MONGODB_URI.startswith('mongodb+srv://') or 'mongodb.net' in MONGODB_URI:
    client_kwargs.update({
        'tls': True,
        'tlsCAFile': certifi.where(),
    })

client = MongoClient(MONGODB_URI, **client_kwargs)

db = client['chat_espe']

# === COLECCIONES ===
rooms = db['rooms']
user_sessions = db['user_sessions']

# === LOCK ===
db_lock = threading.Lock()


def _mask_uri(uri: str) -> str:
    try:
        parts = urlsplit(uri)
        netloc = parts.netloc
        if '@' in netloc and ':' in netloc.split('@')[0]:
            creds, host = netloc.split('@', 1)
            user = creds.split(':', 1)[0]
            netloc = f"{user}:***@{host}"
        return urlunsplit(
            (parts.scheme, netloc, parts.path, parts.query, parts.fragment))
    except Exception:
        return "<uri oculta>"


def init_db():
    """Inicializa DB e índices"""
    with db_lock:
        print(f"Conectando a MongoDB: {_mask_uri(MONGODB_URI)}")
        try:
            # Prueba conexión (dispara selección de servidor y TLS)
            client.admin.command('ping')
            print("MongoDB conectado")
        except Exception as e:
            print(f"ERROR MongoDB: {e}")
            print(
                "Asegúrate de tener MongoDB corriendo localmente o Atlas configurado"
            )
            exit(1)

        # Índices
        try:
            rooms.create_index("id", unique=True)
            user_sessions.create_index([("room_id", 1), ("sid", 1)])
            print("Índices creados")
        except Exception as e:
            print(f"Advertencia índices: {e}")

        # Limpieza solo en desarrollo
        if os.environ.get('FLASK_ENV') == 'development':
            print("Limpieza de colecciones (dev)")
            rooms.delete_many({})
            user_sessions.delete_many({})

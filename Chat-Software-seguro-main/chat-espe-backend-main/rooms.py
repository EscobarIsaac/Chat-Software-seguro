import threading
import shortuuid
import bcrypt
from models import rooms, user_sessions, db_lock
from datetime import datetime


def normalize_room_name(name: str) -> str:
    """Normaliza el nombre para comparaciones tolerantes a mayúsculas/espacios."""
    if not name:
        return ''
    return ''.join(name.lower().split())


def ensure_normalized_names():
    """Garantiza que todas las salas tengan el campo normalized_name poblado."""
    with db_lock:
        cursor = rooms.find({
            "$or": [
                {"normalized_name": {"$exists": False}},
                {"normalized_name": ""}
            ]
        })
        for room in cursor:
            normalized = normalize_room_name(room.get('name', ''))
            if not normalized:
                continue
            rooms.update_one({'_id': room['_id']},
                             {'$set': {'normalized_name': normalized}})


def create_room(name, pin, room_type):
    """Crear sala con PIN encriptado correctamente"""
    with db_lock:
        room_id = shortuuid.uuid()[:8]
        # SIEMPRE usar .encode('utf-8') explícito
        pin_bytes = pin.encode('utf-8')
        pin_hash = bcrypt.hashpw(pin_bytes, bcrypt.gensalt()).decode('utf-8')
        normalized_name = normalize_room_name(name)
        room_data = {
            "id": room_id,
            "name": name,
            "pin": pin_hash,
            "pin_display": pin,  # PIN en texto plano para mostrar al admin
            "normalized_name": normalized_name,
            "type": room_type,
            "created_at": datetime.utcnow()
        }
        rooms.insert_one(room_data)
        print(f"🔐 Sala creada: {room_id} | PIN hasheado: {pin_hash[:20]}...")
        return room_id


def verify_pin(room_or_id, pin):
    """Verificar PIN con encoding correcto (acepta sala o id)."""
    try:
        room = room_or_id
        if isinstance(room_or_id, str):
            room = rooms.find_one({"id": room_or_id})
        if not room:
            print(f"❌ Sala no encontrada: {room_or_id}")
            return False

        # SIEMPRE usar .encode('utf-8') explícito
        pin_bytes = pin.encode('utf-8')
        result = bcrypt.checkpw(pin_bytes, room["pin"].encode('utf-8'))
        print(f"🔍 Verificando PIN para {room['id']}: {pin} -> {result}")
        return result
    except Exception as e:
        print(f"❌ Error verificando PIN: {e}")
        return False


def get_room(room_id):
    return rooms.find_one({"id": room_id})


def find_room_by_identifier(identifier: str):
    """Busca una sala por ID exacto o por nombre (ignorando mayúsculas/espacios)."""
    if not identifier:
        return None

    candidate = identifier.strip()
    if not candidate:
        return None

    room = rooms.find_one({"id": candidate})
    if room:
        return room

    normalized = normalize_room_name(candidate)
    if not normalized:
        return None

    return rooms.find_one({"normalized_name": normalized})

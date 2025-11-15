# main.py (COMPLETO Y CORREGIDO)
from dotenv import load_dotenv
load_dotenv()

import os
import gevent
from gevent import monkey
monkey.patch_all()

from flask import Flask, request, jsonify, session
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS  # ← CORS
from models import init_db, rooms, user_sessions, db_lock
from rooms import create_room, verify_pin, get_room
from auth import verify_admin
import redis
from datetime import datetime
from pymongo import MongoClient
import threading
import requests
import shortuuid

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret')
CORS(app, supports_credentials=True)  # ← CORS + COOKIES

# === Redis Upstash ===
REDIS_URL = os.environ.get('UPSTASH_REDIS_REST_URL')
REDIS_TOKEN = os.environ.get('UPSTASH_REDIS_REST_TOKEN')

if REDIS_URL and REDIS_TOKEN:
    class UpstashRedis:
        def __init__(self, url, token):
            self.url = url
            self.token = token
        def get(self, key):
            try:
                r = requests.get(f"{self.url}/{key}", headers={"Authorization": f"Bearer {self.token}"})
                return r.json().get('result')
            except:
                return None
        def setex(self, key, seconds, value):
            try:
                requests.post(self.url, json=["SET", key, value, "EX", seconds], headers={"Authorization": f"Bearer {self.token}"})
            except:
                pass
        def delete(self, key):
            try:
                requests.post(self.url, json=["DEL", key], headers={"Authorization": f"Bearer {self.token}"})
            except:
                pass
    r = UpstashRedis(REDIS_URL, REDIS_TOKEN)
else:
    import redis
    r = redis.Redis(host='127.0.0.1', port=6379, db=0, socket_connect_timeout=2)

# === SocketIO ===
# ARREGLO: Añadido 'max_http_buffer_size' para permitir archivos grandes
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='gevent',
    cookie='session_id',
    max_http_buffer_size=20 * 1024 * 1024  # Límite de 20 Megabytes
)

# === INIT DB ===
init_db()
# Este diccionario 'active_sessions' es clave para la lógica corregida
active_sessions = {}

# === RUTAS ===
@app.route('/test')
def test():
    return jsonify({"status": "ok"})

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    if verify_admin(data.get('username'), data.get('password')):
        session['admin'] = True
        return jsonify({"success": True})
    return jsonify({"error": "Credenciales inválidas"}), 401

@app.route('/api/admin/rooms', methods=['POST'])
def api_create_room():
    if not session.get('admin'):
        return jsonify({"error": "No autorizado"}), 401
    data = request.get_json()
    
    # Forzamos el tipo a 'multimedia' (como pediste)
    room = create_room(data['name'], data['pin'], 'multimedia')
    
    # Devolvemos el ID y el PIN para el admin
    return jsonify({
        "room_id": room,
        "pin": data['pin']
    })

# --- ¡¡AQUÍ ESTÁ LA FUNCIÓN CORREGIDA!! ---
@app.route('/api/admin/dashboard', methods=['GET'])
def get_dashboard():
    if not session.get('admin'):
        return jsonify({"error": "No autorizado"}), 401
    
    try:
        # 1. Obtenemos todas las salas
        # ARREGLO: Excluimos el campo "pin" (como está en rooms.py)
        all_rooms_cursor = rooms.find({}, {"_id": 0, "pin": 0})
        all_rooms = list(all_rooms_cursor)
        
        # 2. Contamos los usuarios en cada sala
        for room in all_rooms:
            # rooms.py guarda el ID como "id", lo cual está correcto
            room_id = room['id']
            count = len(get_users_in_room(room_id)) # Usamos la función que ya tienes
            room['userCount'] = count
            
        return jsonify(all_rooms)
    except Exception as e:
        print(f"Error en dashboard: {e}")
        return jsonify({"error": "Error al cargar el dashboard"}), 500

@app.route('/api/admin/rooms/<room_id>', methods=['DELETE'])
def delete_room(room_id):
    if not session.get('admin'):
        return jsonify({"error": "No autorizado"}), 401
    
    # 1. Verificamos que la sala esté vacía
    count = len(get_users_in_room(room_id))
    if count > 0:
        return jsonify({"error": f"No se puede eliminar, la sala tiene {count} usuarios"}), 400
        
    # 2. Si está vacía, la borramos
    result = rooms.delete_one({"id": room_id})
    
    if result.deleted_count == 0:
        return jsonify({"error": "Sala no encontrada"}), 404
    
    print(f"Admin eliminó la sala vacía: {room_id}")
    return jsonify({"success": True, "message": f"Sala {room_id} eliminada."})


# === SOCKET EVENTS (Lógica de sesión corregida) ===

@socketio.on('join_room')
def handle_join(data):
    room_id = data['room_id']
    pin = data['pin']
    nickname = data['nickname']
    ip = request.remote_addr
    sid = request.sid  # Clave de sesión única

    if not verify_pin(room_id, pin):
        emit('error', {'msg': 'PIN incorrecto'})
        return

    room = get_room(room_id)
    if not room:
        emit('error', {'msg': 'Sala no existe'})
        return
    
    with db_lock:
        active_sessions[sid] = {
            "room_id": room_id,
            "nickname": nickname,
            "ip": ip
        }

    join_room(room_id)
    emit('joined', room=room_id, to=room_id)
    
    users_in_room = get_users_in_room(room_id)
    emit('user_list', users_in_room, to=room_id)
    
    print(f"{nickname} (SID: {sid}) se unió a {room_id}")

@socketio.on('message')
def handle_message(data):
    sid = request.sid
    session_data = active_sessions.get(sid)
    
    if not session_data:
        print(f"Error: Mensaje de SID {sid} sin sesión.")
        return 

    room_id = session_data['room_id']
    username = data.get('username', session_data.get('nickname', 'Anónimo'))
    
    msg = {
        'msg': data['msg'],
        'username': username,
        'timestamp': data['timestamp']
    }
    emit('message', msg, to=room_id)

@socketio.on('file')
def handle_file(data):
    sid = request.sid
    session_data = active_sessions.get(sid)
    
    if not session_data:
        print(f"Error: Archivo de SID {sid} sin sesión.")
        return

    room_id = session_data['room_id']
    username = data.get('username', session_data.get('nickname', 'Anónimo'))

    file_msg = {
        'file': data['file'],
        'filename': data['filename'],
        'filetype': data['filetype'],
        'username': username,
        'timestamp': data['timestamp']
    }
    emit('file', file_msg, to=room_id)

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    
    if sid in active_sessions:
        room_id = active_sessions[sid]['room_id']
        nickname = active_sessions[sid]['nickname']
        
        del active_sessions[sid]
        
        leave_room(room_id)
        
        users_in_room = get_users_in_room(room_id)
        emit('user_list', users_in_room, to=room_id)
        print(f"{nickname} (SID: {sid}) se desconectó de {room_id}")

# (Esta función estaba bien)
def get_users_in_room(room_id):
    return [s['nickname'] for s in active_sessions.values() if s['room_id'] == room_id]


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=True)
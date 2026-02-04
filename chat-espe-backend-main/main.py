from flask import Flask, request, jsonify, session, send_file
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
from models import init_db, rooms, user_sessions, db_lock
from rooms import (create_room, verify_pin, find_room_by_identifier,
                   ensure_normalized_names)
from auth import verify_admin, ensure_default_admin
from file_security import EnhancedFileSecurityValidator, ThreatLevel
from werkzeug.utils import secure_filename
import redis
from datetime import datetime
from pymongo import MongoClient
import threading
import requests
import shortuuid
import tempfile
import base64
import json
import logging
import atexit
from dotenv import load_dotenv
import gevent
import shutil
import os
from gevent import monkey

# Parchear antes de importar librerías que dependen de sockets/ssl
monkey.patch_all(ssl=False)


load_dotenv()


# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret')
CORS(app, supports_credentials=True)

# Redis configuration (unchanged)
REDIS_URL = os.environ.get('UPSTASH_REDIS_REST_URL')
REDIS_TOKEN = os.environ.get('UPSTASH_REDIS_REST_TOKEN')

if REDIS_URL and REDIS_TOKEN:

    class UpstashRedis:

        def __init__(self, url, token):
            self.url = url
            self.token = token

        def get(self, key):
            try:
                r = requests.get(
                    f"{self.url}/{key}",
                    headers={"Authorization": f"Bearer {self.token}"})
                return r.json().get('result')
            except:
                return None

        def setex(self, key, seconds, value):
            try:
                requests.post(
                    self.url,
                    json=["SET", key, value, "EX", seconds],
                    headers={"Authorization": f"Bearer {self.token}"})
            except:
                pass

        def delete(self, key):
            try:
                requests.post(
                    self.url,
                    json=["DEL", key],
                    headers={"Authorization": f"Bearer {self.token}"})
            except:
                pass

    r = UpstashRedis(REDIS_URL, REDIS_TOKEN)
else:
    import redis
    r = redis.Redis(host='127.0.0.1',
                    port=6379,
                    db=0,
                    socket_connect_timeout=2)

# SocketIO con límite de buffer aumentado
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='gevent',
    cookie='session_id',
    max_http_buffer_size=20 * 1024 * 1024  # 20MB
)

# Initialize DB
init_db()
ensure_normalized_names()
ensure_default_admin()
active_sessions = {}

# Initialize enhanced security validator
security_validator = EnhancedFileSecurityValidator()

# File upload configuration
UPLOAD_FOLDER = tempfile.mkdtemp(prefix='chat_espe_')
QUARANTINE_FOLDER = os.path.join(UPLOAD_FOLDER, 'quarantine')
SANITIZED_FOLDER = os.path.join(UPLOAD_FOLDER, 'sanitized')
os.makedirs(QUARANTINE_FOLDER, exist_ok=True)
os.makedirs(SANITIZED_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max


@app.route('/test')
def test():
    return jsonify({"status": "ok", "security": "enhanced"})


@app.route('/api/upload-file', methods=['POST'])
def upload_file():
    """Endpoint mejorado con validación de seguridad avanzada"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Generar nombre seguro
        original_filename = secure_filename(file.filename)
        temp_filename = f"{shortuuid.uuid()}_{original_filename}"
        temp_path = os.path.join(QUARANTINE_FOLDER, temp_filename)

        # Guardar archivo en cuarentena
        file.save(temp_path)
        logger.info(f"Archivo guardado en cuarentena: {temp_path}")

        try:
            # Validación de seguridad mejorada
            report = security_validator.validate_file(temp_path,
                                                      original_filename)

            # Log detallado del análisis
            logger.info(f"Análisis de seguridad para {original_filename}:")
            logger.info(f"  - Nivel de amenaza: {report.threat_level.value}")
            logger.info(f"  - Confianza: {report.confidence:.1%}")
            logger.info(f"  - Seguro: {report.is_safe}")

            if report.issues:
                logger.warning(f"  - Problemas: {report.issues}")
            if report.warnings:
                logger.info(f"  - Advertencias: {report.warnings}")

            # Decidir acción basada en el nivel de amenaza
            if report.threat_level == ThreatLevel.CRITICAL:
                # Archivo extremadamente peligroso - rechazar inmediatamente
                os.unlink(temp_path)
                logger.error(f"ARCHIVO CRÍTICO RECHAZADO: {original_filename}")

                return jsonify({
                    'success': False,
                    'message':
                    '🚫 Archivo RECHAZADO - Contenido malicioso detectado',
                    'errors': report.issues,
                    'threat_level': 'critical',
                    'recommendations': report.recommendations
                }), 403

            elif report.threat_level == ThreatLevel.HIGH:
                # Archivo peligroso - rechazar
                os.unlink(temp_path)
                logger.warning(
                    f"Archivo de alto riesgo rechazado: {original_filename}")

                return jsonify({
                    'success': False,
                    'message': '❌ Archivo rechazado por seguridad',
                    'errors': report.issues,
                    'warnings': report.warnings,
                    'threat_level': 'high'
                }), 400

            elif report.threat_level == ThreatLevel.MEDIUM:
                # Requiere revisión manual - por ahora rechazar
                logger.warning(
                    f"Archivo requiere revisión: {original_filename}")

                return jsonify({
                    'success': False,
                    'message':
                    '⚠️ Archivo sospechoso - requiere revisión manual',
                    'warnings': report.warnings,
                    'threat_level': 'medium',
                    'confidence': report.confidence
                }), 400

            elif report.threat_level in [ThreatLevel.LOW, ThreatLevel.SAFE]:
                # Archivo seguro o con riesgo bajo
                final_path = temp_path

                # Si es una imagen y necesita sanitización
                if report.metadata.get('needs_sanitization'):
                    logger.info(f"Sanitizando imagen: {original_filename}")
                    sanitized_filename = f"sanitized_{temp_filename}"
                    sanitized_path = os.path.join(SANITIZED_FOLDER,
                                                  sanitized_filename)

                    if security_validator.sanitize_image(
                            temp_path, sanitized_path):
                        # Usar la versión sanitizada
                        final_path = sanitized_path
                        logger.info(
                            f"Imagen sanitizada exitosamente: {sanitized_path}"
                        )
                    else:
                        logger.warning(
                            f"No se pudo sanitizar, usando original con advertencia"
                        )

                # Leer archivo para enviar
                with open(final_path, 'rb') as f:
                    file_data = base64.b64encode(f.read()).decode('utf-8')

                # Calcular hash
                file_hash = security_validator.stego_detector.calculate_file_hash(final_path) \
                    if hasattr(security_validator.stego_detector, 'calculate_file_hash') \
                    else None

                # Limpiar archivos temporales
                if final_path != temp_path and os.path.exists(temp_path):
                    os.unlink(temp_path)
                if os.path.exists(final_path):
                    os.unlink(final_path)

                response_data = {
                    'success': True,
                    'message':
                    f'✅ Archivo validado{" y sanitizado" if report.metadata.get("needs_sanitization") else ""}',
                    'fileInfo': {
                        'name':
                        original_filename,
                        'type':
                        report.metadata.get('mime_type',
                                            'application/octet-stream'),
                        'data':
                        file_data,
                        'hash':
                        file_hash,
                        'size':
                        os.path.getsize(temp_path)
                        if os.path.exists(temp_path) else 0,
                        'category':
                        report.metadata.get('file_type', 'unknown'),
                        'sanitized':
                        report.metadata.get('needs_sanitization', False)
                    },
                    'security_report': {
                        'threat_level': report.threat_level.value,
                        'confidence': report.confidence,
                        'warnings': report.warnings[:3]
                        if report.warnings else []  # Limitar advertencias
                    }
                }

                if report.warnings:
                    response_data['warnings'] = report.warnings

                return jsonify(response_data), 200

        except Exception as e:
            logger.error(f"Error durante validación de seguridad: {e}")
            if os.path.exists(temp_path):
                os.unlink(temp_path)

            return jsonify({
                'success': False,
                'error': 'Error interno durante validación',
                'message': str(e)
            }), 500

    except Exception as e:
        logger.error(f"Error general en upload: {e}")
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500


@app.route('/api/security/scan', methods=['POST'])
def deep_scan_file():
    """Endpoint para escaneo profundo de archivos (solo admin)"""
    if not session.get('admin'):
        return jsonify({"error": "No autorizado"}), 401

    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        temp_path = os.path.join(QUARANTINE_FOLDER,
                                 secure_filename(file.filename))
        file.save(temp_path)

        # Análisis profundo
        report = security_validator.validate_file(temp_path, file.filename)

        # Limpiar archivo
        os.unlink(temp_path)

        return jsonify({
            'threat_level': report.threat_level.value,
            'confidence': report.confidence,
            'issues': report.issues,
            'warnings': report.warnings,
            'metadata': report.metadata,
            'recommendations': report.recommendations
        })

    except Exception as e:
        logger.error(f"Error en escaneo profundo: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/security/stats', methods=['GET'])
def get_security_stats():
    """Obtener estadísticas de seguridad (solo admin)"""
    if not session.get('admin'):
        return jsonify({"error": "No autorizado"}), 401

    # Aquí podrías mantener estadísticas en Redis o MongoDB
    # Por ahora, devolvemos datos de ejemplo
    return jsonify({
        'total_files_scanned': 0,
        'threats_detected': 0,
        'steganography_detected': 0,
        'files_sanitized': 0,
        'last_scan': None
    })


# === Resto del código original (sin cambios) ===


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

    room_type = data.get('type', 'text')
    room = create_room(data['name'], data['pin'], room_type)

    return jsonify({"room_id": room, "pin": data['pin']})


@app.route('/api/admin/dashboard', methods=['GET'])
def get_dashboard():
    if not session.get('admin'):
        return jsonify({"error": "No autorizado"}), 401

    try:
        all_rooms_cursor = rooms.find({}, {"_id": 0})
        all_rooms = list(all_rooms_cursor)

        for room in all_rooms:
            room_id = room['id']
            count = len(get_users_in_room(room_id))
            room['userCount'] = count

        return jsonify(all_rooms)
    except Exception as e:
        print(f"Error en dashboard: {e}")
        return jsonify({"error": "Error al cargar el dashboard"}), 500


@app.route('/api/admin/rooms/<room_id>', methods=['DELETE'])
def delete_room(room_id):
    if not session.get('admin'):
        return jsonify({"error": "No autorizado"}), 401

    count = len(get_users_in_room(room_id))
    if count > 0:
        return jsonify(
            {"error":
             f"No se puede eliminar, la sala tiene {count} usuarios"}), 400

    result = rooms.delete_one({"id": room_id})

    if result.deleted_count == 0:
        return jsonify({"error": "Sala no encontrada"}), 404

    print(f"Admin eliminó la sala vacía: {room_id}")
    return jsonify({"success": True, "message": f"Sala {room_id} eliminada."})


# === Socket events (sin cambios) ===


@socketio.on('join_room')
def handle_join(data):
    room_identifier = data.get('room_id') or data.get('room')
    pin = data['pin']
    nickname = data['nickname']
    ip = request.remote_addr
    sid = request.sid

    if not room_identifier:
        emit('error', {'msg': 'Debes indicar el ID o nombre de la sala'})
        return

    room = find_room_by_identifier(room_identifier)
    if not room:
        emit('error', {'msg': 'Sala no existe'})
        return

    if not verify_pin(room, pin):
        emit('error', {'msg': 'PIN incorrecto'})
        return

    room_id = room['id']

    is_admin = session.get('admin', False)

    with db_lock:
        active_sessions[sid] = {
            "room_id": room_id,
            "nickname": nickname,
            "ip": ip,
            "is_admin": is_admin
        }

    print(f"Usuario {nickname} unido - Es admin: {is_admin}")

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

    is_admin = session_data.get('is_admin', False)

    msg = {
        'msg': data['msg'],
        'username': username,
        'timestamp': data['timestamp'],
        'isAdmin': is_admin
    }

    print(f"Mensaje de {username} - isAdmin: {is_admin}")
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

    is_admin = session_data.get('is_admin', False)

    # Log de seguridad para archivos
    logger.info(f"Archivo compartido por {username} en sala {room_id}")
    if 'hash' in data:
        logger.info(f"  Hash del archivo: {data['hash'][:16]}...")

    file_msg = {
        'file': data['file'],
        'filename': data['filename'],
        'filetype': data['filetype'],
        'username': username,
        'timestamp': data['timestamp'],
        'isAdmin': is_admin,
        'sanitized': data.get('sanitized', False)  # Indicar si fue sanitizado
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


def get_users_in_room(room_id):
    return [
        s['nickname'] for s in active_sessions.values()
        if s['room_id'] == room_id
    ]


# Limpieza al salir


def cleanup_temp_files():
    """Limpia archivos temporales al cerrar la aplicación"""
    try:
        if os.path.exists(UPLOAD_FOLDER):
            shutil.rmtree(UPLOAD_FOLDER)
            logger.info(f"Carpeta temporal limpiada: {UPLOAD_FOLDER}")
    except Exception as e:
        logger.error(f"Error limpiando archivos temporales: {e}")


atexit.register(cleanup_temp_files)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))

    logger.info("=" * 60)
    logger.info("🔒 SISTEMA DE CHAT SEGURO CON DETECCIÓN DE ESTEGANOGRAFÍA")
    logger.info("=" * 60)
    logger.info(f"✅ Validación de seguridad: ACTIVADA")
    logger.info(f"✅ Detección de esteganografía: ACTIVADA")
    logger.info(f"✅ Sanitización de imágenes: ACTIVADA")
    logger.info(f"📁 Carpeta de cuarentena: {QUARANTINE_FOLDER}")
    logger.info(f"📁 Carpeta de sanitización: {SANITIZED_FOLDER}")
    logger.info("=" * 60)

    socketio.run(
        app,
        host='0.0.0.0',
        port=port,
        debug=False,
        use_reloader=False
    )

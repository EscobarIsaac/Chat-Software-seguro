import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pymongo import ASCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

try:
    # pymongo >= 4 suele exponer este módulo
    from pymongo.return_document import ReturnDocument
except Exception:  # compatibilidad con versiones anteriores
    try:
        from pymongo.collection import ReturnDocument  # type: ignore
    except Exception:
        from pymongo import ReturnDocument  # type: ignore


# Tiempo de vida de una credencial biométrica (en segundos).
# Después de este tiempo, la credencial se considera expirada y no se usará para login.
CREDENTIAL_TTL_SECONDS = 30 * 24 * 60 * 60  # 30 días


class GatewayStore:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    display_name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
                """.strip())
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS credentials (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    credential_id TEXT NOT NULL,
                    public_key TEXT NOT NULL,
                    sign_count INTEGER NOT NULL,
                    transports TEXT,
                    created_at REAL NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
                """.strip())
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS challenges (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    purpose TEXT NOT NULL,
                    challenge TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
                """.strip())
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    event_type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    ai_level TEXT,
                    created_at REAL NOT NULL
                )
                """.strip())
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS registration_requests (
                    id TEXT PRIMARY KEY,
                    username TEXT NOT NULL,
                    display_name TEXT,
                    role TEXT NOT NULL,
                    status TEXT NOT NULL,
                    approval_token TEXT NOT NULL,
                    requester_email TEXT,
                    notes TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    completed_at REAL
                )
                """.strip())

    def upsert_user(self, username: str, display_name: str,
                    role: str) -> Dict[str, Any]:
        existing = self.find_user_by_username(username)
        if existing:
            return existing
        user_id = uuid4().hex
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO users (id, username, display_name, role, created_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, username, display_name, role, time.time()))
        return self.get_user(user_id)

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE id = ?", (user_id, )).fetchone()
        return dict(row) if row else None

    def find_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM users WHERE username = ?",
                               (username, )).fetchone()
        return dict(row) if row else None

    def list_credentials(self, user_id: str) -> List[Dict[str, Any]]:
        cutoff = time.time() - CREDENTIAL_TTL_SECONDS
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM credentials WHERE user_id = ? AND created_at >= ?",
                (user_id, cutoff)).fetchall()
        return [dict(r) for r in rows]

    def create_registration_request(self,
                                    username: str,
                                    display_name: Optional[str],
                                    role: str,
                                    requester_email: Optional[str]) -> Dict[str, Any]:
        request_id = uuid4().hex
        approval_token = uuid4().hex
        now = time.time()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO registration_requests
                (id, username, display_name, role, status, approval_token, requester_email, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'pending', ?, ?, ?, ?)
                """.strip(),
                (request_id, username, display_name, role, approval_token,
                 requester_email, now, now))
        return self.get_registration_request(request_id)

    def get_registration_request(self,
                                 request_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM registration_requests WHERE id = ?",
                               (request_id, )).fetchone()
        return dict(row) if row else None

    def get_registration_request_by_token(self, request_id: str,
                                          token: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM registration_requests WHERE id = ? AND approval_token = ?",
                (request_id, token)).fetchone()
        return dict(row) if row else None

    def update_registration_request_status(self,
                                           request_id: str,
                                           status: str,
                                           notes: Optional[str] = None
                                           ) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE registration_requests
                SET status = ?, notes = COALESCE(?, notes), updated_at = ?
                WHERE id = ?
                """.strip(), (status, notes, time.time(), request_id))
        return self.get_registration_request(request_id)

    def mark_registration_completed(self, request_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE registration_requests
                SET status = 'completed', completed_at = ?, updated_at = ?
                WHERE id = ?
                """.strip(), (time.time(), time.time(), request_id))
        return self.get_registration_request(request_id)

    def save_credential(self, user_id: str, credential_id: str, public_key: str,
                        sign_count: int,
                        transports: Optional[List[str]]) -> None:
        # Solo se permite una credencial biométrica activa por usuario.
        with self._connect() as conn:
            conn.execute("DELETE FROM credentials WHERE user_id = ?",
                         (user_id, ))
            conn.execute(
                "INSERT INTO credentials (id, user_id, credential_id, public_key, sign_count, transports, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (uuid4().hex, user_id, credential_id, public_key, sign_count,
                 json.dumps(transports or []), time.time()))

    def update_sign_count(self, credential_id: str, sign_count: int) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE credentials SET sign_count = ? WHERE credential_id = ?",
                (sign_count, credential_id))

    def save_challenge(self,
                       challenge: str,
                       purpose: str,
                       user_id: Optional[str] = None) -> str:
        challenge_id = uuid4().hex
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO challenges (id, user_id, purpose, challenge, created_at) VALUES (?, ?, ?, ?, ?)",
                (challenge_id, user_id, purpose, challenge, time.time()))
        return challenge_id

    def pop_challenge(self, purpose: str,
                      user_id: Optional[str]) -> Optional[str]:
        query = "SELECT id, challenge FROM challenges WHERE purpose = ?"
        params: List[Any] = [purpose]

        if user_id:
            query += " AND (user_id = ? OR user_id IS NULL)"
            params.append(user_id)
        else:
            query += " AND user_id IS NULL"

        query += " ORDER BY created_at DESC"

        with self._connect() as conn:
            row = conn.execute(query, params).fetchone()
            if not row:
                return None
            conn.execute("DELETE FROM challenges WHERE id = ?", (row['id'], ))
            return row['challenge']

    def log_event(self,
                  event_type: str,
                  payload: Dict[str, Any],
                  user_id: Optional[str] = None,
                  ai_level: Optional[str] = None) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO audit_logs (id, user_id, event_type, payload, ai_level, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (uuid4().hex, user_id, event_type,
                 json.dumps(payload, ensure_ascii=True), ai_level,
                 time.time()))

    def latest_events(self, limit: int = 25) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT ?",
                (limit, )).fetchall()

        events: List[Dict[str, Any]] = []
        for row in rows:
            payload = row['payload']
            parsed_payload: Dict[str, Any]
            if isinstance(payload, str):
                try:
                    parsed_payload = json.loads(payload)
                except json.JSONDecodeError:
                    parsed_payload = {"raw": payload}
            else:
                parsed_payload = dict(payload)

            events.append({
                'id': row['id'],
                'user_id': row['user_id'],
                'event_type': row['event_type'],
                'payload': parsed_payload,
                'ai_level': row['ai_level'],
                'created_at': row['created_at']
            })

        return events


class MongoGatewayStore:
    def __init__(self, uri: str, db_name: str):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.users: Collection = self.db['users']
        self.credentials: Collection = self.db['credentials']
        self.challenges: Collection = self.db['challenges']
        self.audit_logs: Collection = self.db['audit_logs']
        self.registration_requests: Collection = self.db['registration_requests']
        self._ensure_indexes()

    def _ensure_indexes(self) -> None:
        self.users.create_index('username', unique=True)
        self.credentials.create_index('credential_id', unique=True)
        self.challenges.create_index([('purpose', ASCENDING),
                                      ('user_id', ASCENDING)])
        self.audit_logs.create_index('created_at')
        self.registration_requests.create_index('status')
        self.registration_requests.create_index('approval_token', unique=True)

    def upsert_user(self, username: str, display_name: str,
                    role: str) -> Dict[str, Any]:
        result = self.users.find_one_and_update(
            {'username': username},
            {'$setOnInsert': {
                'display_name': display_name,
                'role': role,
                'created_at': time.time()
            }},
            upsert=True,
            return_document=ReturnDocument.AFTER)
        if result is None:
            result = self.users.find_one({'username': username}) or {}
        if 'id' not in result:
            result['id'] = uuid4().hex
            self.users.update_one({'_id': result['_id']},
                                  {'$set': {'id': result['id']}})
        return self._normalize_user(result)

    def _normalize_user(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'id': doc.get('id') or str(doc.get('_id')),
            'username': doc['username'],
            'display_name': doc.get('display_name', doc['username']),
            'role': doc.get('role', 'cliente'),
            'created_at': doc.get('created_at', time.time())
        }

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        doc = self.users.find_one({'id': user_id})
        return self._normalize_user(doc) if doc else None

    def find_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        doc = self.users.find_one({'username': username})
        return self._normalize_user(doc) if doc else None

    def list_credentials(self, user_id: str) -> List[Dict[str, Any]]:
        cutoff = time.time() - CREDENTIAL_TTL_SECONDS
        docs = self.credentials.find({
            'user_id': user_id,
            'created_at': {
                '$gte': cutoff
            }
        })
        return [self._normalize_credential(c) for c in docs]

    def _normalize_credential(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'id': doc.get('id') or str(doc.get('_id')),
            'user_id': doc['user_id'],
            'credential_id': doc['credential_id'],
            'public_key': doc['public_key'],
            'sign_count': doc.get('sign_count', 0),
            'transports': doc.get('transports', []),
            'created_at': doc.get('created_at', time.time())
        }

    def save_credential(self, user_id: str, credential_id: str, public_key: str,
                        sign_count: int, transports: Optional[List[str]]) -> None:
        # Solo se permite una credencial biométrica activa por usuario.
        self.credentials.delete_many({'user_id': user_id})
        self.credentials.insert_one({
            'id': uuid4().hex,
            'user_id': user_id,
            'credential_id': credential_id,
            'public_key': public_key,
            'sign_count': sign_count,
            'transports': transports or [],
            'created_at': time.time()
        })

    def update_sign_count(self, credential_id: str, sign_count: int) -> None:
        self.credentials.update_one({'credential_id': credential_id},
                                    {'$set': {'sign_count': sign_count}})

    def save_challenge(self,
                       challenge: str,
                       purpose: str,
                       user_id: Optional[str] = None) -> str:
        challenge_id = uuid4().hex
        self.challenges.insert_one({
            'id': challenge_id,
            'user_id': user_id,
            'purpose': purpose,
            'challenge': challenge,
            'created_at': time.time()
        })
        return challenge_id

    def pop_challenge(self, purpose: str,
                      user_id: Optional[str]) -> Optional[str]:
        query: Dict[str, Any] = {'purpose': purpose}
        if user_id:
            query['$or'] = [{"user_id": user_id}, {"user_id": None}]
        else:
            query['user_id'] = None

        doc = self.challenges.find_one_and_delete(query,
                                                  sort=[('created_at', -1)])
        if not doc:
            return None
        return doc['challenge']

    def log_event(self,
                  event_type: str,
                  payload: Dict[str, Any],
                  user_id: Optional[str] = None,
                  ai_level: Optional[str] = None) -> None:
        self.audit_logs.insert_one({
            'id': uuid4().hex,
            'user_id': user_id,
            'event_type': event_type,
            'payload': payload,
            'ai_level': ai_level,
            'created_at': time.time()
        })

    def latest_events(self, limit: int = 25) -> List[Dict[str, Any]]:
        docs = self.audit_logs.find().sort('created_at', -1).limit(limit)
        return [self._normalize_event(d) for d in docs]

    def _normalize_event(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        payload = doc.get('payload')
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError:
                payload = {'raw': payload}
        return {
            'id': doc.get('id') or str(doc.get('_id')),
            'user_id': doc.get('user_id'),
            'event_type': doc.get('event_type'),
            'payload': payload,
            'ai_level': doc.get('ai_level'),
            'created_at': doc.get('created_at', time.time())
        }

    def create_registration_request(self, username: str,
                                    display_name: Optional[str],
                                    role: str,
                                    requester_email: Optional[str]) -> Dict[str, Any]:
        request_id = uuid4().hex
        approval_token = uuid4().hex
        now = time.time()
        payload = {
            'id': request_id,
            'username': username,
            'display_name': display_name,
            'role': role,
            'status': 'pending',
            'approval_token': approval_token,
            'requester_email': requester_email,
            'created_at': now,
            'updated_at': now
        }
        self.registration_requests.insert_one(payload)
        return payload

    def get_registration_request(self,
                                 request_id: str) -> Optional[Dict[str, Any]]:
        doc = self.registration_requests.find_one({'id': request_id})
        return dict(doc) if doc else None

    def get_registration_request_by_token(self, request_id: str,
                                          token: str) -> Optional[Dict[str, Any]]:
        doc = self.registration_requests.find_one({
            'id': request_id,
            'approval_token': token
        })
        return dict(doc) if doc else None

    def update_registration_request_status(self, request_id: str, status: str,
                                           notes: Optional[str] = None
                                           ) -> Optional[Dict[str, Any]]:
        update_fields: Dict[str, Any] = {
            'status': status,
            'updated_at': time.time()
        }
        if notes:
            update_fields['notes'] = notes
        self.registration_requests.update_one({'id': request_id},
                                              {'$set': update_fields})
        return self.get_registration_request(request_id)

    def mark_registration_completed(self, request_id: str) -> Optional[Dict[str, Any]]:
        now = time.time()
        self.registration_requests.update_one(
            {'id': request_id},
            {'$set': {
                'status': 'completed',
                'updated_at': now,
                'completed_at': now
            }})
        return self.get_registration_request(request_id)


def create_store(settings) -> GatewayStore:
    if settings.storage_backend == 'mongo' and settings.mongo_uri:
        return MongoGatewayStore(settings.mongo_uri, settings.mongo_db)

    db_path = Path(settings.data_dir) / 'gateway.db'
    return GatewayStore(db_path)

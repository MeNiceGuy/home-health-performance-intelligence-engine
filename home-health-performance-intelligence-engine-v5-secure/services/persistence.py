from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from services.security import decrypt_text, encrypt_text, hash_password, verify_password

DATA_DIR = Path(__file__).resolve().parent.parent / 'data'
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / 'engine.db'
LEGACY_RECORDS_PATH = DATA_DIR / 'agency_records.json'
LEGACY_AUDIT_PATH = DATA_DIR / 'audit_events.json'


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()



def _load_legacy(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return []


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()



def _dump_protected(data: Any) -> str:
    return encrypt_text(json.dumps(data, ensure_ascii=False))



def _load_protected(value: str) -> Any:
    raw = decrypt_text(value)
    return json.loads(raw)



def _init_db() -> None:
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS agency_records (
                id TEXT PRIMARY KEY,
                agency_name TEXT NOT NULL,
                state TEXT,
                city TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                record_json TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_agency_records_name ON agency_records(agency_name, updated_at DESC);

            CREATE TABLE IF NOT EXISTS audit_events (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                user TEXT NOT NULL,
                action TEXT NOT NULL,
                agency_name TEXT,
                detail TEXT NOT NULL,
                ip_address TEXT DEFAULT ''
            );
            CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_events(timestamp DESC);

            CREATE TABLE IF NOT EXISTS workflow_tasks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                agency_name TEXT,
                assigned_to TEXT,
                priority TEXT,
                status TEXT,
                source TEXT,
                due_date TEXT,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_workflow_agency ON workflow_tasks(agency_name, status);

            CREATE TABLE IF NOT EXISTS emr_imports (
                id TEXT PRIMARY KEY,
                agency_name TEXT NOT NULL,
                source_type TEXT NOT NULL,
                row_count INTEGER NOT NULL,
                imported_at TEXT NOT NULL,
                summary_json TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_emr_agency ON emr_imports(agency_name, imported_at DESC);

            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                must_change_password INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )
        audit_cols = [r[1] for r in conn.execute("PRAGMA table_info(audit_events)").fetchall()]
        if 'ip_address' not in audit_cols:
            conn.execute("ALTER TABLE audit_events ADD COLUMN ip_address TEXT DEFAULT ''")
        count = conn.execute('SELECT COUNT(*) FROM agency_records').fetchone()[0]
        if count == 0:
            for item in _load_legacy(LEGACY_RECORDS_PATH):
                conn.execute(
                    'INSERT OR IGNORE INTO agency_records (id, agency_name, state, city, created_at, updated_at, record_json) VALUES (?, ?, ?, ?, ?, ?, ?)',
                    (
                        item.get('id', str(uuid4())),
                        item.get('agency_name', 'Unknown Agency'),
                        item.get('state', ''),
                        item.get('city', ''),
                        item.get('created_at', _utc_now()),
                        item.get('updated_at', _utc_now()),
                        _dump_protected(item.get('record', {})),
                    ),
                )
        count = conn.execute('SELECT COUNT(*) FROM audit_events').fetchone()[0]
        if count == 0:
            for item in _load_legacy(LEGACY_AUDIT_PATH):
                conn.execute(
                    'INSERT OR IGNORE INTO audit_events (id, timestamp, user, action, agency_name, detail, ip_address) VALUES (?, ?, ?, ?, ?, ?, ?)',
                    (
                        item.get('id', str(uuid4())),
                        item.get('timestamp', _utc_now()),
                        item.get('user', 'system'),
                        item.get('action', 'legacy_event'),
                        item.get('agency_name', ''),
                        item.get('detail', ''),
                        '',
                    ),
                )
        # migrate plaintext blobs to encrypted storage
        for table, col in [('agency_records', 'record_json'), ('emr_imports', 'summary_json')]:
            rows = conn.execute(f'SELECT id, {col} FROM {table}').fetchall()
            for row in rows:
                value = row[col]
                if value and not str(value).startswith('enc::'):
                    conn.execute(f'UPDATE {table} SET {col}=? WHERE id=?', (_dump_protected(json.loads(value)), row['id']))


_init_db()



def create_or_update_user(username: str, password: str, role: str = 'analyst', active: bool = True, must_change_password: bool = True) -> dict[str, Any]:
    now = _utc_now()
    payload = {
        'id': str(uuid4()), 'username': username.strip().lower(), 'password_hash': hash_password(password), 'role': role,
        'is_active': 1 if active else 0, 'must_change_password': 1 if must_change_password else 0,
        'created_at': now, 'updated_at': now,
    }
    with get_conn() as conn:
        existing = conn.execute('SELECT id, created_at FROM users WHERE username=?', (payload['username'],)).fetchone()
        if existing:
            payload['id'] = existing['id']
            payload['created_at'] = existing['created_at']
            conn.execute(
                'UPDATE users SET password_hash=?, role=?, is_active=?, must_change_password=?, updated_at=? WHERE username=?',
                (payload['password_hash'], payload['role'], payload['is_active'], payload['must_change_password'], payload['updated_at'], payload['username'])
            )
        else:
            conn.execute(
                'INSERT INTO users (id, username, password_hash, role, is_active, must_change_password, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                (payload['id'], payload['username'], payload['password_hash'], payload['role'], payload['is_active'], payload['must_change_password'], payload['created_at'], payload['updated_at'])
            )
    return get_user(payload['username'])



def bootstrap_admin(username: str, password: str, role: str = 'admin') -> dict[str, Any]:
    with get_conn() as conn:
        existing = conn.execute('SELECT username FROM users WHERE username=?', (username.strip().lower(),)).fetchone()
    if existing:
        return get_user(username)
    return create_or_update_user(username, password, role=role, must_change_password=True)



def authenticate_user(username: str, password: str) -> dict[str, Any] | None:
    user = get_user(username)
    if not user or not user['is_active']:
        return None
    with get_conn() as conn:
        row = conn.execute('SELECT password_hash FROM users WHERE username=?', (username.strip().lower(),)).fetchone()
    if not row or not verify_password(password, row['password_hash']):
        return None
    return user



def get_user(username: str) -> dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute('SELECT id, username, role, is_active, must_change_password, created_at, updated_at FROM users WHERE username=?', (username.strip().lower(),)).fetchone()
    return dict(row) if row else None



def change_password(username: str, new_password: str, must_change_password: bool = False) -> None:
    with get_conn() as conn:
        cur = conn.execute('UPDATE users SET password_hash=?, must_change_password=?, updated_at=? WHERE username=?',
                           (hash_password(new_password), 1 if must_change_password else 0, _utc_now(), username.strip().lower()))
        if cur.rowcount == 0:
            raise KeyError(f'User not found: {username}')



def save_agency_record(record: dict[str, Any]) -> dict[str, Any]:
    payload = {
        'id': str(uuid4()),
        'agency_name': record.get('agency_name', 'Unknown Agency'),
        'state': record.get('state', ''),
        'city': record.get('city', ''),
        'created_at': _utc_now(),
        'updated_at': _utc_now(),
        'record': record,
    }
    with get_conn() as conn:
        conn.execute(
            'INSERT INTO agency_records (id, agency_name, state, city, created_at, updated_at, record_json) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (payload['id'], payload['agency_name'], payload['state'], payload['city'], payload['created_at'], payload['updated_at'], _dump_protected(record)),
        )
    return payload



def update_agency_record(record_id: str, record: dict[str, Any]) -> dict[str, Any]:
    updated_at = _utc_now()
    with get_conn() as conn:
        cur = conn.execute(
            'UPDATE agency_records SET agency_name=?, state=?, city=?, updated_at=?, record_json=? WHERE id=?',
            (record.get('agency_name', 'Unknown Agency'), record.get('state', ''), record.get('city', ''), updated_at, _dump_protected(record), record_id),
        )
        if cur.rowcount == 0:
            raise KeyError(f'Agency record not found: {record_id}')
    return get_agency_record(record_id)



def list_agency_records(agency_name: str | None = None) -> list[dict[str, Any]]:
    query = 'SELECT * FROM agency_records'
    params: list[Any] = []
    if agency_name:
        query += ' WHERE lower(agency_name)=lower(?)'
        params.append(agency_name.strip())
    query += ' ORDER BY updated_at DESC'
    with get_conn() as conn:
        rows = conn.execute(query, params).fetchall()
    return [{
        'id': r['id'], 'agency_name': r['agency_name'], 'state': r['state'], 'city': r['city'],
        'created_at': r['created_at'], 'updated_at': r['updated_at'], 'record': _load_protected(r['record_json'])
    } for r in rows]



def get_agency_record(record_id: str) -> dict[str, Any]:
    with get_conn() as conn:
        row = conn.execute('SELECT * FROM agency_records WHERE id=?', (record_id,)).fetchone()
    if not row:
        raise KeyError(f'Agency record not found: {record_id}')
    return {
        'id': row['id'], 'agency_name': row['agency_name'], 'state': row['state'], 'city': row['city'],
        'created_at': row['created_at'], 'updated_at': row['updated_at'], 'record': _load_protected(row['record_json'])
    }



def append_audit_event(action: str, detail: str, user: str = 'system', agency_name: str | None = None, ip_address: str = '') -> dict[str, Any]:
    payload = {
        'id': str(uuid4()), 'timestamp': _utc_now(), 'user': user, 'action': action,
        'agency_name': agency_name or '', 'detail': detail, 'ip_address': ip_address,
    }
    with get_conn() as conn:
        conn.execute('INSERT INTO audit_events (id, timestamp, user, action, agency_name, detail, ip_address) VALUES (?, ?, ?, ?, ?, ?, ?)',
                     (payload['id'], payload['timestamp'], payload['user'], payload['action'], payload['agency_name'], payload['detail'], payload['ip_address']))
    return payload



def list_audit_events(limit: int = 100) -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute('SELECT * FROM audit_events ORDER BY timestamp DESC LIMIT ?', (limit,)).fetchall()
    return [dict(r) for r in rows]



def save_emr_import(agency_name: str, source_type: str, row_count: int, summary: dict[str, Any]) -> dict[str, Any]:
    payload = {
        'id': str(uuid4()), 'agency_name': agency_name, 'source_type': source_type, 'row_count': row_count,
        'imported_at': _utc_now(), 'summary': summary,
    }
    with get_conn() as conn:
        conn.execute('INSERT INTO emr_imports (id, agency_name, source_type, row_count, imported_at, summary_json) VALUES (?, ?, ?, ?, ?, ?)',
                     (payload['id'], agency_name, source_type, row_count, payload['imported_at'], _dump_protected(summary)))
    return payload



def list_emr_imports(agency_name: str | None = None, limit: int = 25) -> list[dict[str, Any]]:
    query = 'SELECT * FROM emr_imports'
    params: list[Any] = []
    if agency_name:
        query += ' WHERE lower(agency_name)=lower(?)'
        params.append(agency_name.strip())
    query += ' ORDER BY imported_at DESC LIMIT ?'
    params.append(limit)
    with get_conn() as conn:
        rows = conn.execute(query, params).fetchall()
    return [{**dict(r), 'summary': _load_protected(r['summary_json'])} for r in rows]

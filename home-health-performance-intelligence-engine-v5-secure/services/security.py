from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
import time
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from passlib.context import CryptContext

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'
DATA_DIR.mkdir(exist_ok=True)
_LOCAL_KEY_FILE = DATA_DIR / '.local_fernet_key'

pwd_context = CryptContext(schemes=['pbkdf2_sha256'], deprecated='auto')


def _load_or_create_key() -> bytes:
    env_key = os.getenv('APP_ENCRYPTION_KEY', '').strip()
    if env_key:
        return env_key.encode('utf-8')
    if _LOCAL_KEY_FILE.exists():
        return _LOCAL_KEY_FILE.read_bytes().strip()
    key = Fernet.generate_key()
    _LOCAL_KEY_FILE.write_bytes(key)
    return key


_FERNET = Fernet(_load_or_create_key())


def hash_password(password: str) -> str:
    return pwd_context.hash(password)



def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)



def encrypt_text(value: str) -> str:
    token = _FERNET.encrypt(value.encode('utf-8')).decode('utf-8')
    return f'enc::{token}'



def decrypt_text(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError('Encrypted value must be a string.')
    if not value.startswith('enc::'):
        return value
    token = value.split('enc::', 1)[1]
    try:
        return _FERNET.decrypt(token.encode('utf-8')).decode('utf-8')
    except InvalidToken as exc:
        raise ValueError('Unable to decrypt protected data.') from exc



def csrf_token() -> str:
    return secrets.token_urlsafe(32)



def constant_time_equal(a: str | None, b: str | None) -> bool:
    return hmac.compare_digest(a or '', b or '')



def derive_demo_password() -> str:
    seed = os.getenv('BOOTSTRAP_ADMIN_PASSWORD', 'change-me-now')
    digest = hashlib.sha256(seed.encode('utf-8')).hexdigest()
    return digest[:18] + 'Aa!9'


class SimpleRateLimiter:
    def __init__(self, limit: int = 120, window_seconds: int = 60) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._events: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = time.time()
        bucket = self._events[key]
        while bucket and now - bucket[0] > self.window_seconds:
            bucket.popleft()
        if len(bucket) >= self.limit:
            return False
        bucket.append(now)
        return True


DEFAULT_RATE_LIMITER = SimpleRateLimiter()

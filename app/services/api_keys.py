import hashlib
import secrets
from app.core.config import API_KEY_PREFIX

def generate_api_key() -> tuple[str, str, str]:
    secret = secrets.token_urlsafe(32)
    full_key = f"{API_KEY_PREFIX}_{secret}"
    prefix = full_key[:18]
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()
    return full_key, prefix, key_hash

def hash_api_key(full_key: str) -> str:
    return hashlib.sha256(full_key.encode()).hexdigest()

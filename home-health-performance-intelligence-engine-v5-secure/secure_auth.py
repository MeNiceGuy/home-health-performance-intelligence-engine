import hashlib
import hmac
import os
import secrets
from typing import Dict

# Simple secure user credentials store (in-memory for demo; use DB in prod)
USER_CREDENTIALS: Dict[str, Dict[str, str]] = {}

# Password hashing & verification using HMAC + SHA256 (replace with bcrypt/argon2 in prod)
def hash_password(password: str, salt: str) -> str:
    return hmac.new(salt.encode(), password.encode(), hashlib.sha256).hexdigest()

def create_user(username: str, password: str) -> None:
    salt = secrets.token_hex(16)
    pwd_hash = hash_password(password, salt)
    USER_CREDENTIALS[username] = {"salt": salt, "pwd_hash": pwd_hash}

    print(f"User {username} created.")

def verify_user(username: str, password: str) -> bool:
    user = USER_CREDENTIALS.get(username)
    if not user:
        return False
    pwd_hash = hash_password(password, user["salt"])
    return hmac.compare_digest(pwd_hash, user["pwd_hash"])

# Example usage
def test():
    create_user("admin", "supersecurepassword")
    print("Verify admin with correct password:", verify_user("admin", "supersecurepassword"))
    print("Verify admin with wrong password:", verify_user("admin", "wrongpass"))

if __name__ == "__main__":
    test()

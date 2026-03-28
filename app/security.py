"""
Auth utilities: password hashing, JWT creation/decoding, API key generation/verification.

API key format:  {uuid_hex}.{32-char-url-safe-secret}
  - Split on '.' to get the DB row ID instantly (O(1) lookup, no table scan)
  - The secret portion is bcrypt-hashed before storage; full key is shown once on creation
"""

import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

import bcrypt
from jose import JWTError, jwt

from app.config import settings


# ---------------------------------------------------------------------------
# Password helpers  (bcrypt called directly — passlib incompatible with bcrypt>=4)
# ---------------------------------------------------------------------------


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------


def create_access_token(user_id: uuid.UUID) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> str:
    """Return user_id str from a valid JWT or raise JWTError."""
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    sub: str | None = payload.get("sub")
    if sub is None:
        raise JWTError("Missing subject claim")
    return sub


# ---------------------------------------------------------------------------
# API key helpers
# ---------------------------------------------------------------------------


def generate_api_key(key_id: uuid.UUID) -> tuple[str, str, str]:
    """
    Returns (full_key, key_hash, key_prefix):
      - full_key:   "{key_id_hex}.{secret}" — returned to user once
      - key_hash:   bcrypt hash of the secret portion, stored in DB
      - key_prefix: first 8 chars of the secret, stored plaintext for display
    """
    secret = secrets.token_urlsafe(32)
    key_hash = bcrypt.hashpw(secret.encode(), bcrypt.gensalt()).decode()
    key_prefix = secret[:8]
    full_key = f"{key_id.hex}.{secret}"
    return full_key, key_hash, key_prefix


def parse_api_key(full_key: str) -> Optional[Tuple[uuid.UUID, str]]:
    """
    Split a full API key into (key_id, secret).
    Returns None if the format is invalid.
    """
    parts = full_key.split(".", 1)
    if len(parts) != 2:
        return None
    try:
        key_id = uuid.UUID(parts[0])
    except ValueError:
        return None
    return key_id, parts[1]


def verify_api_key_secret(secret: str, stored_hash: str) -> bool:
    return bcrypt.checkpw(secret.encode(), stored_hash.encode())

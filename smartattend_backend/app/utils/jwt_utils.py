from datetime import datetime, timedelta
from typing import Dict, Any, Optional

import bcrypt
from jose import jwt, JWTError

from app.config.config import settings

# ── Password Hashing ──────────────────────────────────────────────────────────


def hash_password(password: str) -> str:
    """Hash a plain-text password with bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against its bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


# ── JWT ──────────────────────────────────────────────────────────────────────

def create_access_token(data: Dict[str, Any], role: str) -> str:
    """
    Create a signed JWT.
    Role determines expiry:
      admin   → 8 h
      others  → 24 h
    """
    to_encode = data.copy()
    if "sub" in to_encode:
        to_encode["sub"] = str(to_encode["sub"])
    expire_delta = timedelta(hours=8) if role == "admin" else timedelta(hours=24)
    expire = datetime.utcnow() + expire_delta
    to_encode.update({"exp": expire, "role": role})
    return jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and verify a JWT; returns None on failure."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError:
        return None

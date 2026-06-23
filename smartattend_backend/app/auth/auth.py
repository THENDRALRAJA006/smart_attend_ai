from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from jose import jwt, JWTError
import bcrypt
from app.config.config import settings

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def create_access_token(data: Dict[str, Any], role: str) -> str:
    to_encode = data.copy()
    expire_delta = timedelta(hours=8) if role == "admin" else timedelta(hours=24)
    expire = datetime.utcnow() + expire_delta
    to_encode.update({"exp": expire, "role": role})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None

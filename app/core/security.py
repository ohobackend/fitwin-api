from datetime import datetime, timedelta, timezone
from typing import Any
import jwt
from app.core.config import get_settings

def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expiry = now + (expires_delta or timedelta(minutes=settings.jwt_access_token_expire_minutes))
    return jwt.encode({"sub": subject, "iat": now, "exp": expiry}, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

def decode_access_token(token: str, secret_key: str, algorithm: str) -> dict[str, Any]:
    payload = jwt.decode(token, secret_key, algorithms=[algorithm])
    if not payload.get("sub"):
        raise jwt.InvalidTokenError("JWT subject is missing")
    return payload

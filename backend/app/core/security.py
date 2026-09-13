from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def create_access_token(subject: str, expires_minutes: Optional[int] = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.access_token_expire_minutes
    )
    return jwt.encode({"sub": subject, "exp": expire, "type": "access"}, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(subject: str) -> str:
    """Create a long-lived refresh token for obtaining new access tokens."""
    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    return jwt.encode({"sub": subject, "exp": expire, "type": "refresh"}, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str, expected_type: str = "access") -> str:
    """Decode and validate a JWT token.

    Args:
        token: The JWT string to decode.
        expected_type: Either "access" or "refresh" — validates the token's
                       claim type matches what the caller expects.

    Raises:
        ValueError: If the token is invalid, expired, or type-mismatched.
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        sub: Optional[str] = payload.get("sub")
        token_type: Optional[str] = payload.get("type")
        if sub is None:
            raise JWTError("missing sub")
        if token_type != expected_type:
            raise JWTError(f"expected {expected_type} token, got {token_type}")
        return sub
    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc

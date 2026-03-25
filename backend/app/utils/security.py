import hashlib
import base64
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from typing import Optional
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Password ──────────────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    """Hash password using bcrypt after pre-hashing with SHA-256 to avoid 72-char limit."""
    pw_hash = hashlib.sha256(plain.encode("utf-8")).digest()
    pw_b64 = base64.b64encode(pw_hash).decode("utf-8")
    return pwd_context.hash(pw_b64)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify password by pre-hashing and then checking against bcrypt hash."""
    pw_hash = hashlib.sha256(plain.encode("utf-8")).digest()
    pw_b64 = base64.b64encode(pw_hash).decode("utf-8")
    return pwd_context.verify(pw_b64, hashed)


# ── Field hashing (one-way SHA-256 + secret salt) ────────────────────────────

def hash_field(value: str) -> str:
    """Deterministically hash sensitive fields (phone, GST, contact info)."""
    salted = f"{settings.FIELD_ENCRYPTION_KEY}:{value}"
    return hashlib.sha256(salted.encode()).hexdigest()


# ── JWT ───────────────────────────────────────────────────────────────────────

def create_access_token(subject: str, extra: dict | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": subject, "exp": expire, "type": "access"}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {"sub": subject, "exp": expire, "type": "refresh"}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Raises JWTError if invalid/expired."""
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


def hash_token(token: str) -> str:
    """Store hashed refresh token in DB for logout/invalidation."""
    return hashlib.sha256(token.encode()).hexdigest()

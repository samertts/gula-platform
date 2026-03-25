from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import JWTError, jwt
from ..config import (
    SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRE_MINUTES, JWT_EXPIRE_HOURS,
    REFRESH_TOKEN_SECRET, REFRESH_TOKEN_EXPIRE_DAYS,
)

# ── JWT Token Blacklist (revocation) ──────────────────────────────────────────
# Uses Redis (or in-memory fallback) to store revoked JTIs.
# TTL matches token lifetime so keys auto-expire and storage stays bounded.

def blacklist_token(jti: str, ttl_seconds: int) -> None:
    """Add a JTI to the revocation list until it would have expired anyway."""
    from .redis_client import cache
    cache.set(f"blacklist:jti:{jti}", "1", ex=ttl_seconds)


def is_token_blacklisted(jti: str) -> bool:
    """Return True if this JTI has been revoked (logout or forced expiry)."""
    from .redis_client import cache
    return cache.get(f"blacklist:jti:{jti}") is not None

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def build_token_payload(user) -> dict:
    """
    Build the slim JWT payload for a LabUser.

    We intentionally do NOT embed the permissions list.
    Permissions are derived from role at request time (O(1) dict lookup).
    Keeping the JWT small reduces cookie size on every HTTP request.
    """
    return {
        "user_id": user.id,
        "lab_id": user.lab_id,
        "role": user.role,
        "perm_ver": user.perm_version if user.perm_version is not None else 1,
    }


def create_token(data: dict) -> str:
    """Create a short-lived JWT access token (default: 30 minutes)."""
    import uuid
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access", "jti": str(uuid.uuid4())})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict | None:
    """Decode and validate an access token. Returns None on any failure."""
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["exp"]},
        )
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None


def create_refresh_token(data: dict) -> str:
    """Create a long-lived JWT refresh token (default: 30 days)."""
    import uuid
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh", "jti": str(uuid.uuid4())})
    return jwt.encode(to_encode, REFRESH_TOKEN_SECRET, algorithm=JWT_ALGORITHM)


def decode_refresh_token(token: str) -> dict | None:
    """Decode and validate a refresh token. Returns None on any failure."""
    try:
        payload = jwt.decode(
            token,
            REFRESH_TOKEN_SECRET,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["exp"]},
        )
        if payload.get("type") != "refresh":
            return None
        # Check revocation: refresh tokens can be blacklisted on logout
        jti = payload.get("jti")
        if jti and is_token_blacklisted(jti):
            return None
        return payload
    except JWTError:
        return None

"""JWT Guard - validates Authorization header tokens.

WARNING: This module is DEAD CODE. It is not imported by any route.
Routes use `dependencies.get_current_user()` which performs full validation
including token type, JTI blacklist, user active status, permission version,
and lab active status. This function bypasses all of those checks.

See `backend/app/security/dependencies.py` for the canonical auth dependency.
"""

from fastapi import HTTPException, Request
from jose import JWTError, jwt

from ..config import SECRET_KEY


def protect(request: Request):
    """Validate JWT token from Authorization header."""
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = auth.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        if not payload.get("user_id"):
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from None

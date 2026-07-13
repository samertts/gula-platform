"""JWT Guard - validates Authorization header tokens."""

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
        raise HTTPException(status_code=401, detail="Invalid or expired token")

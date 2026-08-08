from platform.api.dependencies.container import get_auth_service

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

router = APIRouter()


class LoginRequest(BaseModel):
    username: str = ""
    password: str = ""


@router.post("/login")
async def login(
    data: LoginRequest,
    auth_service=Depends(get_auth_service),
) -> dict[str, str]:
    return {"status": "authenticated", "token": "placeholder"}


@router.post("/verify")
async def verify_token(
    data: dict[str, str],
    auth_service=Depends(get_auth_service),
) -> dict[str, bool]:
    token = data.get("token", "")
    result = await auth_service.get_current_user(token)
    if result is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"valid": True}

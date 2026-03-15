from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.lab_user import LabUser
from ..security.auth import verify_password, create_token
from ..security.rate_limit import rate_limit_auth
from ..services.audit_service import log_action

router = APIRouter(tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/login")
def login(data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    rate_limit_auth(request)
    user = db.query(LabUser).filter(
        LabUser.email == data.email,
        LabUser.is_active == True,
    ).first()

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_token({
        "user_id": user.id,
        "lab_id": user.lab_id,
        "role": user.role,
    })

    # Audit log
    log_action(
        db,
        action="login",
        resource_type="auth",
        user_id=user.id,
        user_role=user.role,
        details=f"User {user.email} logged in",
        ip_address=request.client.host if request.client else None,
    )
    db.commit()

    return {
        "token": token,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "lab_id": user.lab_id,
        },
    }

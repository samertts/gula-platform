"""Isolated public demo access.

This route is intentionally unavailable unless the deployment explicitly sets
DEMO_MODE=true and DEMO_DATA_ISOLATION_ACK=true. The deployment must point to a
separate database and Redis instance containing synthetic data only.
"""

from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from ..config import DEMO_MODE, IS_PRODUCTION, JWT_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS, USE_SECURE_COOKIES
from ..database import get_db
from ..models.lab import Lab
from ..models.lab_user import LabUser
from ..security.auth import build_token_payload, create_refresh_token, create_token, hash_password
from ..security.rate_limit import get_client_ip, rate_limit_auth
from ..services.audit_service import log_action

router = APIRouter(prefix="/demo", tags=["demo"])

_DEMO_PERSONAS = {
    "doctor": {
        "name": "Demo Doctor",
        "email": "demo.doctor@gula-demo.iq",
        "role": "doctor",
    },
    "technician": {
        "name": "Demo Lab Technician",
        "email": "demo.technician@gula-demo.iq",
        "role": "technician",
    },
    "lab_admin": {
        "name": "Demo Lab Administrator",
        "email": "demo.lab-admin@gula-demo.iq",
        "role": "lab_admin",
    },
    "citizen": {
        "name": "Demo Citizen",
        "email": "demo.citizen@gula-demo.iq",
        "role": "citizen",
    },
}

_DEFAULT_DEMO_PERSONA = "doctor"


def _demo_unavailable() -> None:
    if not DEMO_MODE or IS_PRODUCTION:
        raise HTTPException(status_code=404, detail="Demo mode is not enabled")


@router.post("/access", summary="Start an isolated synthetic demo session")
def start_demo_session(
    request: Request,
    response: Response,
    persona: str = _DEFAULT_DEMO_PERSONA,
    db: Session = Depends(get_db),
):
    _demo_unavailable()
    rate_limit_auth(request)
    selected = _DEMO_PERSONAS.get(persona)
    if selected is None:
        raise HTTPException(status_code=422, detail="Unknown demo persona")

    lab = db.query(Lab).filter(Lab.name == "GULA Synthetic Demo Lab").first()
    if lab is None:
        lab = Lab(
            name="GULA Synthetic Demo Lab",
            lab_type="demo",
            city="Synthetic Baghdad",
            address="Isolated demonstration tenant",
            is_active=True,
        )
        db.add(lab)
        db.flush()

    user = db.query(LabUser).filter(LabUser.email == selected["email"]).first()
    if user is None:
        user = LabUser(
            lab_id=lab.id,
            name=selected["name"],
            email=selected["email"],
            # The public route never accepts a password. Keep the stored hash
            # random so the synthetic account cannot be used as a credential.
            password_hash=hash_password(secrets.token_urlsafe(32)),
            role=selected["role"],
            is_active=True,
        )
        db.add(user)
        db.flush()
    elif (
        not user.is_active
        or user.lab_id != lab.id
        or user.role != selected["role"]
    ):
        # Fail closed if a synthetic identity was deactivated, moved, or had
        # its role changed outside the deterministic demo catalogue.
        raise HTTPException(status_code=503, detail="Demo account is not available")

    payload = build_token_payload(user)
    access_token = create_token(payload)
    refresh_token = create_refresh_token(payload)
    cookie_kwargs = {"httponly": True, "samesite": "strict", "secure": USE_SECURE_COOKIES}
    response.set_cookie(
        key="access_token", value=access_token, max_age=JWT_EXPIRE_MINUTES * 60,
        path="/", **cookie_kwargs,
    )
    response.set_cookie(
        key="refresh_token", value=refresh_token, max_age=REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/", **cookie_kwargs,
    )
    log_action(
        db,
        action="demo_access",
        resource_type="demo",
        resource_id=user.id,
        user_id=user.id,
        user_role=user.role,
        details="Synthetic demo session started; no production data access",
        ip_address=get_client_ip(request),
    )
    db.commit()
    return {
        "demo_mode": True,
        "demo_persona": persona,
        "message": "Synthetic demo session started",
        "message_ar": "تم بدء جلسة العرض التجريبي بالبيانات الاصطناعية",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "lab_id": user.lab_id,
            "lab_name": lab.name,
            "is_verified": True,
        },
    }

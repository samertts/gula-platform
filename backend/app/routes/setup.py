"""Setup status endpoint — public, no authentication required.

Returns whether the platform needs first-time setup (no users exist yet).
Used by the login page to auto-show the registration tab on first run.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.lab_user import LabUser

router = APIRouter(tags=["setup"])


@router.get("/setup/status")
def setup_status(db: Session = Depends(get_db)):
    """Return platform setup state.

    Response:
        needs_setup: true  — no users exist yet, show registration wizard
        needs_setup: false — at least one user exists, show normal login
    """
    has_users = db.query(LabUser.id).first() is not None
    return {"needs_setup": not has_users}

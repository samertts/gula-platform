from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.lab_user import LabUser
from ..security.dependencies import get_current_user, require_permission
from ..services.dashboard_service import get_dashboard, get_greeting

router = APIRouter(tags=["dashboard"])


@router.get("/greeting")
def greeting(current_user: LabUser = Depends(get_current_user)):
    """Return a personalized Arabic greeting based on Iraq local time."""
    return get_greeting(current_user)


@router.get("/dashboard")
def dashboard(
    current_user: LabUser = Depends(require_permission("dashboard:read")),
    db: Session = Depends(get_db),
):
    """Lab dashboard: aggregated stats, abnormal results, recent orders.

    Delegates to `app.services.dashboard_service` for all business logic.
    Results are scoped to the requesting lab's tenant.
    """
    return get_dashboard(db, current_user)

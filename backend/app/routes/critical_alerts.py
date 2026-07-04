"""Critical result alerts - immediate notification system for dangerous values."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.lab_user import LabUser
from ..security.dependencies import get_current_user
from ..services.critical_alerts import (
    alert_statistics as _alert_statistics,
)
from ..services.critical_alerts import (
    get_critical_alerts as _get_critical_alerts,
)

router = APIRouter(prefix="/alerts", tags=["critical-alerts"])


@router.get("")
def get_critical_alerts(
    hours: int = Query(24, ge=1, le=168),
    acknowledged: bool = None,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get critical results requiring immediate attention."""
    return _get_critical_alerts(db, current_user.lab_id, hours)


@router.get("/stats")
def alert_statistics(
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Statistics on critical results for the lab."""
    return _alert_statistics(db, current_user.lab_id)

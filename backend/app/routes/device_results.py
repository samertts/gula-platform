"""Lab device integration - receive results from analyzers."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.lab_user import LabUser
from ..security.dependencies import get_current_user
from ..services.audit_service import log_action

logger = logging.getLogger("gula.device_results")

router = APIRouter(prefix="/device", tags=["device"])


class DeviceResult(BaseModel):
    test_name: str
    value: float | None = None
    value_text: str | None = None
    unit: str | None = None
    normal_range_low: float | None = None
    normal_range_high: float | None = None


class DeviceSubmission(BaseModel):
    barcode: str  # sample barcode to match
    device_id: str | None = None
    results: list[DeviceResult]


@router.post("/results")
def receive_device_results(
    data: DeviceSubmission,
    request: Request,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Reject the legacy direct device-to-clinical-write path.

    Device payloads must enter the future trusted ingress service, be recorded
    in the transactionally idempotent inbox, and remain quarantined until an
    authorized clinician accepts them through the clinical command guard. This
    endpoint intentionally never reads a sample, creates a result, or changes
    clinical state.
    """
    del data, request
    try:
        log_action(
            db,
            action="device_direct_ingestion_rejected",
            resource_type="device_ingress",
            user_id=current_user.id,
            user_role=current_user.role,
            lab_id=current_user.lab_id,
            details={"reason": "legacy_direct_clinical_write_disabled"},
        )
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Unable to persist direct-device-ingestion rejection audit event")

    raise HTTPException(
        status_code=503,
        detail="device_ingestion_quarantined",
    )

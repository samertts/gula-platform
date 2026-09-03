from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.clinical.appointments.routes import _actor_rate_limit, _correlation_id, _handle_error
from app.database import get_db
from app.identity.api.workspaces import NiamActor, get_current_niam_actor_sync

from .service import ClinicalRecordService

router = APIRouter(tags=["Unified Clinical Record"])


def _run(request: Request, actor: NiamActor, db: Session, workspace_id: str, callback: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    _actor_rate_limit(request, actor)
    try:
        result = callback()
        db.commit()
        return result
    except Exception as exc:
        _handle_error(exc, db=db, actor=actor, request=request, operation="clinical_record.read", target_type="clinical_record", target_id=None, workspace_id=workspace_id)
        raise AssertionError("unreachable") from exc


@router.get("/api/v1/clinical-records/{patient_person_id}")
def get_clinical_record(patient_person_id: str, request: Request, workspace_id: str = Query(..., min_length=1, max_length=26), limit: int = Query(default=50, ge=1, le=100), cursor: str | None = Query(default=None, max_length=512), sections: list[str] | None = Query(default=None), purpose: str | None = Query(default=None, max_length=40), actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db)) -> dict[str, Any]:
    return _run(request, actor, db, workspace_id, lambda: ClinicalRecordService(db).get_record(actor, patient_person_id=patient_person_id, workspace_id=workspace_id, limit=limit, cursor=cursor, sections=sections, purpose=purpose, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))

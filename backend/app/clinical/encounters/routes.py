from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Header, Request, status
from sqlalchemy.orm import Session

from app.clinical.appointments.routes import (
    _actor_rate_limit,
    _correlation_id,
    _handle_error,
    _require_idempotency_key,
    _require_if_match,
)
from app.database import get_db
from app.identity.api.workspaces import NiamActor, get_current_niam_actor_sync

from .schemas import (
    AmendNoteRequest,
    CheckInRequest,
    CreateNoteRequest,
    TransitionRequest,
    UpdateNoteRequest,
)
from .service import EncounterService

router = APIRouter(tags=["Core Encounters"])


def _run(request: Request, actor: NiamActor, db: Session, operation: str, target_type: str, target_id: str | None, workspace_id: str, callback):
    _actor_rate_limit(request, actor)
    try:
        result = callback()
        db.commit()
        return result
    except Exception as exc:
        _handle_error(exc, db=db, actor=actor, request=request, operation=operation, target_type=target_type, target_id=target_id, workspace_id=workspace_id)


@router.post("/api/v1/encounters/check-in", status_code=status.HTTP_201_CREATED)
def check_in(body: CheckInRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    return _run(request, actor, db, "encounter.checkin", "encounter", None, body.workspace_id, lambda: EncounterService(db).check_in(actor, appointment_id=body.appointment_id, workspace_id=body.workspace_id, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.get("/api/v1/encounters/{encounter_id}")
def get_encounter(encounter_id: str, request: Request, workspace_id: str, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db)) -> dict[str, Any]:
    return _run(request, actor, db, "encounter.read", "encounter", encounter_id, workspace_id, lambda: EncounterService(db).get_encounter(actor, encounter_id=encounter_id, workspace_id=workspace_id, correlation_id=_correlation_id(request)))


def _transition_route(target: str):
    def handler(encounter_id: str, body: TransitionRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), if_match: str | None = Header(default=None, alias="If-Match")) -> dict[str, Any]:
        key = _require_idempotency_key(idempotency_key)
        expected_version = _require_if_match(if_match)
        operation = f"encounter.{target.lower()}"
        return _run(request, actor, db, operation, "encounter", encounter_id, body.workspace_id, lambda: EncounterService(db).transition_encounter(actor, encounter_id=encounter_id, workspace_id=body.workspace_id, target=target, expected_version=expected_version, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))
    return handler


router.add_api_route("/api/v1/encounters/{encounter_id}/start", _transition_route("IN_PROGRESS"), methods=["POST"])
router.add_api_route("/api/v1/encounters/{encounter_id}/complete", _transition_route("COMPLETED"), methods=["POST"])


@router.post("/api/v1/encounters/{encounter_id}/notes", status_code=status.HTTP_201_CREATED)
def create_note(encounter_id: str, body: CreateNoteRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    fields = body.model_dump(exclude={"workspace_id", "encounter_id"})
    return _run(request, actor, db, "clinical.note.create", "clinical_note", None, body.workspace_id, lambda: EncounterService(db).create_note(actor, encounter_id=encounter_id, workspace_id=body.workspace_id, fields=fields, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.patch("/api/v1/clinical-notes/{note_id}")
def update_note(note_id: str, body: UpdateNoteRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), if_match: str | None = Header(default=None, alias="If-Match")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    expected_version = _require_if_match(if_match)
    fields = body.model_dump(exclude={"workspace_id"})
    return _run(request, actor, db, "clinical.note.update", "clinical_note", note_id, body.workspace_id, lambda: EncounterService(db).update_note(actor, note_id=note_id, workspace_id=body.workspace_id, expected_version=expected_version, fields=fields, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


def _note_transition_route(target: str):
    def handler(note_id: str, body: UpdateNoteRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), if_match: str | None = Header(default=None, alias="If-Match")) -> dict[str, Any]:
        key = _require_idempotency_key(idempotency_key)
        expected_version = _require_if_match(if_match)
        return _run(request, actor, db, f"clinical.note.{target.lower()}", "clinical_note", note_id, body.workspace_id, lambda: EncounterService(db).transition_note(actor, note_id=note_id, workspace_id=body.workspace_id, target=target, expected_version=expected_version, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))
    return handler


router.add_api_route("/api/v1/clinical-notes/{note_id}/complete", _note_transition_route("COMPLETED"), methods=["POST"])
router.add_api_route("/api/v1/clinical-notes/{note_id}/sign", _note_transition_route("SIGNED"), methods=["POST"])


@router.post("/api/v1/clinical-notes/{note_id}/amend")
def amend_note(note_id: str, body: AmendNoteRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    fields = body.model_dump(exclude={"workspace_id", "reason"})
    return _run(request, actor, db, "clinical.note.amend", "clinical_note", note_id, body.workspace_id, lambda: EncounterService(db).amend_note(actor, note_id=note_id, workspace_id=body.workspace_id, reason=body.reason, fields=fields, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))

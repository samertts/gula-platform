from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, Depends, Header, Query, Request, status
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
    BatchActionRequest,
    BatchCreateRequest,
    ControlledPolicyActionRequest,
    DispenseActionRequest,
    DispenseCreateRequest,
    FefoDispenseCreateRequest,
    MedicationCreateRequest,
    PrescriptionActionRequest,
    PrescriptionAmendRequest,
    PrescriptionCreateRequest,
    StockAdjustmentRequest,
)
from .service import CanonicalPharmacyService

router = APIRouter(tags=["Core Pharmacy"])


def _run(request: Request, actor: NiamActor, db: Session, operation: str, target_type: str, target_id: str | None, workspace_id: str, callback: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    _actor_rate_limit(request, actor)
    try:
        result = callback()
        db.commit()
        return result
    except Exception as exc:
        _handle_error(exc, db=db, actor=actor, request=request, operation=operation, target_type=target_type, target_id=target_id, workspace_id=workspace_id)
        raise AssertionError("unreachable") from exc


@router.post("/api/v1/clinical/medications", status_code=status.HTTP_201_CREATED)
def create_medication(body: MedicationCreateRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    correlation_id = _correlation_id(request)
    return _run(request, actor, db, "medication.catalog.create", "medication", None, body.workspace_id, lambda: CanonicalPharmacyService(db).create_medication(actor, workspace_id=body.workspace_id, code=body.code, code_system=body.code_system, generic_name=body.generic_name, brand_name=body.brand_name, strength_value=body.strength_value, strength_unit=body.strength_unit, dosage_form=body.dosage_form, route=body.route, is_controlled=body.is_controlled, idempotency_key=key, correlation_id=correlation_id, request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/clinical/prescriptions", status_code=status.HTTP_201_CREATED)
def create_prescription(body: PrescriptionCreateRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    correlation_id = _correlation_id(request)
    return _run(request, actor, db, "prescription.create", "prescription", None, body.workspace_id, lambda: CanonicalPharmacyService(db).create_prescription(actor, encounter_id=body.encounter_id, workspace_id=body.workspace_id, purpose=body.purpose, note=body.note, items=[item.model_dump() for item in body.items], idempotency_key=key, correlation_id=correlation_id, request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/clinical/prescriptions/{prescription_id}/controlled-policy/approve")
def approve_controlled_policy(prescription_id: str, body: ControlledPolicyActionRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), if_match: str | None = Header(default=None, alias="If-Match")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    expected = _require_if_match(if_match)
    return _run(request, actor, db, "prescription.controlled_policy.approve", "prescription", prescription_id, body.workspace_id, lambda: CanonicalPharmacyService(db).approve_controlled_policy(actor, prescription_id=prescription_id, workspace_id=body.workspace_id, expected_version=expected, reason=body.reason, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.get("/api/v1/clinical/prescriptions/{prescription_id}")
def get_prescription(prescription_id: str, request: Request, workspace_id: str = Query(..., min_length=1, max_length=26), actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db)) -> dict[str, Any]:
    return _run(request, actor, db, "prescription.read", "prescription", prescription_id, workspace_id, lambda: CanonicalPharmacyService(db).get_prescription(actor, prescription_id=prescription_id, workspace_id=workspace_id, correlation_id=_correlation_id(request)))


@router.get("/api/v1/clinical/prescriptions/{prescription_id}/fhir")
def get_prescription_fhir(prescription_id: str, request: Request, workspace_id: str = Query(..., min_length=1, max_length=26), actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db)) -> dict[str, Any]:
    return _run(request, actor, db, "prescription.fhir", "prescription", prescription_id, workspace_id, lambda: CanonicalPharmacyService(db).fhir_prescription(actor, prescription_id=prescription_id, workspace_id=workspace_id, correlation_id=_correlation_id(request)))


@router.post("/api/v1/clinical/prescriptions/{prescription_id}/sign")
def sign_prescription(prescription_id: str, body: PrescriptionActionRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), if_match: str | None = Header(default=None, alias="If-Match")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    expected = _require_if_match(if_match)
    return _run(request, actor, db, "prescription.sign", "prescription", prescription_id, body.workspace_id, lambda: CanonicalPharmacyService(db).sign_prescription(actor, prescription_id=prescription_id, workspace_id=body.workspace_id, expected_version=expected, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/clinical/prescriptions/{prescription_id}/amend")
def amend_prescription(prescription_id: str, body: PrescriptionAmendRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), if_match: str | None = Header(default=None, alias="If-Match")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    expected = _require_if_match(if_match)
    return _run(request, actor, db, "prescription.amend", "prescription", prescription_id, body.workspace_id, lambda: CanonicalPharmacyService(db).amend_prescription(actor, prescription_id=prescription_id, workspace_id=body.workspace_id, expected_version=expected, reason=body.reason, items=[item.model_dump() for item in body.items], idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/clinical/medication-batches", status_code=status.HTTP_201_CREATED)
def create_batch(body: BatchCreateRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    return _run(request, actor, db, "medication.batch.create", "medication_batch", None, body.workspace_id, lambda: CanonicalPharmacyService(db).create_batch(actor, workspace_id=body.workspace_id, medication_catalog_id=body.medication_catalog_id, batch_number=body.batch_number, expiry_date=body.expiry_date, quantity_received=body.quantity_received, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/clinical/dispenses/fefo", status_code=status.HTTP_201_CREATED)
def prepare_dispense_fefo(body: FefoDispenseCreateRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    return _run(request, actor, db, "dispense.prepare_fefo", "dispense", None, body.workspace_id, lambda: CanonicalPharmacyService(db).prepare_dispense_fefo(actor, prescription_row_id=body.prescription_row_id, prescription_item_id=body.prescription_item_id, workspace_id=body.workspace_id, quantity=body.quantity, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/clinical/dispenses", status_code=status.HTTP_201_CREATED)
def prepare_dispense(body: DispenseCreateRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    return _run(request, actor, db, "dispense.prepare", "dispense", None, body.workspace_id, lambda: CanonicalPharmacyService(db).prepare_dispense(actor, prescription_row_id=body.prescription_row_id, prescription_item_id=body.prescription_item_id, batch_id=body.batch_id, workspace_id=body.workspace_id, quantity=body.quantity, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/clinical/medication-batches/{batch_id}/recall")
def recall_batch(batch_id: str, body: BatchActionRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), if_match: str | None = Header(default=None, alias="If-Match")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    expected = _require_if_match(if_match)
    return _run(request, actor, db, "medication.batch.recall", "medication_batch", batch_id, body.workspace_id, lambda: CanonicalPharmacyService(db).recall_batch(actor, batch_id=batch_id, workspace_id=body.workspace_id, reason=body.reason, expected_version=expected, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/clinical/medication-batches/{batch_id}/adjust")
def adjust_stock(batch_id: str, body: StockAdjustmentRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), if_match: str | None = Header(default=None, alias="If-Match")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    expected = _require_if_match(if_match)
    return _run(request, actor, db, "medication.stock.adjust", "medication_batch", batch_id, body.workspace_id, lambda: CanonicalPharmacyService(db).adjust_stock(actor, batch_id=batch_id, workspace_id=body.workspace_id, quantity_delta=body.quantity_delta, kind=body.kind, reason=body.reason, expected_version=expected, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/clinical/dispenses/{dispense_id}/complete")
def complete_dispense(dispense_id: str, body: DispenseActionRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), if_match: str | None = Header(default=None, alias="If-Match")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    expected = _require_if_match(if_match)
    return _run(request, actor, db, "dispense.complete", "dispense", dispense_id, body.workspace_id, lambda: CanonicalPharmacyService(db).complete_dispense(actor, dispense_id=dispense_id, workspace_id=body.workspace_id, expected_version=expected, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.get("/api/v1/clinical/dispenses/{dispense_id}/fhir")
def get_dispense_fhir(dispense_id: str, request: Request, workspace_id: str = Query(..., min_length=1, max_length=26), actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db)) -> dict[str, Any]:
    return _run(request, actor, db, "dispense.fhir", "dispense", dispense_id, workspace_id, lambda: CanonicalPharmacyService(db).fhir_dispense(actor, dispense_id=dispense_id, workspace_id=workspace_id, correlation_id=_correlation_id(request)))


@router.get("/api/v1/clinical/medication-history/{patient_person_id}")
def medication_history(patient_person_id: str, request: Request, workspace_id: str = Query(..., min_length=1, max_length=26), limit: int = Query(default=50, ge=1, le=100), offset: int = Query(default=0, ge=0, le=1_000_000), actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db)) -> dict[str, Any]:
    return _run(request, actor, db, "medication.history.read", "medication_history", patient_person_id, workspace_id, lambda: CanonicalPharmacyService(db).medication_history(actor, patient_person_id=patient_person_id, workspace_id=workspace_id, limit=limit, offset=offset, correlation_id=_correlation_id(request)))

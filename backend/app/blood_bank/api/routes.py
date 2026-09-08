from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.blood_bank.application.service import BloodBankService
from app.blood_bank.compatibility import check_compatibility, get_compatible_groups
from app.blood_bank.exceptions import (
    BloodBankValidationError,
    BloodBankWorkflowError,
    CrossmatchConflictError,
    DonorDeferredError,
    DonorNotFoundError,
    InsufficientStockError,
    TransfusionNotFoundError,
)
from app.blood_bank.infrastructure.models import (
    BloodRequestModel,
    BloodUnitModel,
    CrossmatchModel,
    TransfusionModel,
    PatientBloodSampleModel,
    BloodReservationModel,
    TransfusionReactionModel,
    BloodReturnModel,
    BloodDiscardModel,
)
from app.clinical.command_guard import ClinicalCommandGuard
from app.clinical.failure_injection import maybe_fail
from app.database import get_db
from app.models.lab_user import LabUser
from app.security.dependencies import get_current_user, require_permission

router = APIRouter(
    prefix="/blood-bank",
    tags=["National Blood Bank Platform"],
    dependencies=[Depends(require_permission("system:admin"))],
)


def _lab_id(current_user: LabUser) -> int:
    lab_id = getattr(current_user, "lab_id", None)
    if not isinstance(lab_id, int) or lab_id <= 0:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Institutional laboratory context is required")
    return lab_id


def _guard(db: Session, current_user: LabUser) -> ClinicalCommandGuard:
    return ClinicalCommandGuard(
        db,
        actor_user_id=current_user.id,
        lab_id=_lab_id(current_user),
        actor_role=current_user.role,
    )


def _raise_blood_error(error: Exception) -> None:
    if isinstance(error, (BloodBankValidationError, BloodBankWorkflowError, CrossmatchConflictError)):
        unprocessable_status = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422)
        raise HTTPException(status_code=unprocessable_status, detail=str(error)) from error
    if isinstance(error, InsufficientStockError):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Insufficient safe stock") from error
    if isinstance(error, TransfusionNotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found") from error
    raise error


def _get_service(db: Session = Depends(get_db)) -> BloodBankService:
    try:
        from app.kernel import Kernel
        kernel = Kernel.get_instance()
        event_bus = kernel.event_bus if hasattr(kernel, "event_bus") else None
    except Exception:
        event_bus = None
    return BloodBankService(db=db, event_bus=event_bus)


# ---- Donor Management ----

@router.post("/donors", status_code=status.HTTP_201_CREATED)
async def register_donor(
    body: dict[str, Any],
    service: BloodBankService = Depends(_get_service),
) -> dict[str, Any]:
    donor = service.register_donor(body)
    return _donor_to_dict(donor)


@router.get("/donors")
async def list_donors(
    blood_group: str | None = Query(None),
    status: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: BloodBankService = Depends(_get_service),
) -> list[dict[str, Any]]:
    return [_donor_to_dict(d) for d in service.find_donors(blood_group, status, skip, limit)]


@router.get("/donors/{donor_id}")
async def get_donor(
    donor_id: str,
    service: BloodBankService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        return _donor_to_dict(service.get_donor(donor_id))
    except DonorNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found") from e


@router.post("/donors/{donor_id}/defer")
async def defer_donor(
    donor_id: str,
    body: dict[str, Any],
    service: BloodBankService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        deferral = service.defer_donor(donor_id, body)
        return {"id": deferral.id, "donor_id": donor_id, "deferral_days": deferral.deferral_days,
                "deferred_until": deferral.deferred_until.isoformat() if deferral.deferred_until else None,
                "reason": deferral.reason}
    except DonorNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found") from e


# ---- Donations ----

@router.post("/donations", status_code=status.HTTP_201_CREATED)
async def register_donation(
    body: dict[str, Any],
    service: BloodBankService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        donation = service.register_donation(body)
        return _donation_to_dict(donation)
    except DonorNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found") from e
    except DonorDeferredError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Resource conflict") from e


@router.post("/donations/{donation_id}/complete")
async def complete_donation(
    donation_id: str,
    service: BloodBankService = Depends(_get_service),
) -> dict[str, Any]:
    donation = service.complete_donation(donation_id)
    return _donation_to_dict(donation)


# ---- Components ----

@router.post("/components", status_code=status.HTTP_201_CREATED)
async def process_component(
    body: dict[str, Any],
    service: BloodBankService = Depends(_get_service),
) -> dict[str, Any]:
    component = service.process_component(body)
    return _component_to_dict(component)


# ---- Inventory ----

@router.get("/inventory")
async def get_inventory(
    facility_id: str | None = Query(None),
    service: BloodBankService = Depends(_get_service),
) -> list[dict[str, Any]]:
    return [_inventory_to_dict(i) for i in service.get_inventory(facility_id)]


@router.get("/inventory/critical")
async def get_critical_inventory(
    service: BloodBankService = Depends(_get_service),
) -> list[dict[str, Any]]:
    return [_inventory_to_dict(i) for i in service.get_critical_inventory()]


@router.post("/inventory/issue")
async def issue_units(
    body: dict[str, Any],
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    if_match: str | None = Header(None, alias="If-Match"),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
) -> list[dict[str, Any]]:
    """Issue only screened, processed, unexpired units against one active patient request."""
    lab_id = _lab_id(current_user)
    request = (
        db.query(BloodRequestModel)
        .filter(BloodRequestModel.id == body.get("request_id"), BloodRequestModel.lab_id == lab_id)
        .with_for_update()
        .first()
    )
    if not request:
        raise HTTPException(status_code=404, detail="Resource not found")
    guard = _guard(db, current_user)
    version_before = request.version
    state_before = request.status
    guard.require_expected_version(if_match, current_version=version_before, resource_name="blood request")
    key = guard.require_idempotency_key(idempotency_key)
    receipt = guard.claim(
        operation="blood.issue", resource_type="blood_request", resource_id=request.id,
        idempotency_key=key, payload=body,
    )
    try:
        units = BloodBankService(db).issue_units_safely(
            request_id=request.id,
            lab_id=lab_id,
            quantity=body.get("quantity", 1),
            issued_by=str(current_user.id),
        )
        maybe_fail("after_business_effect")
        guard.complete(
            receipt, resource_type="blood_request", resource_id=request.id,
            state_before=state_before, state_after=request.status,
            version_before=version_before, version_after=request.version,
        )
        db.commit()
        maybe_fail("after_commit")
    except Exception as exc:
        db.rollback()
        guard.reject(
            operation="blood.issue", resource_type="blood_request", resource_id=request.id,
            state_before=state_before, version_before=version_before, reason=str(exc),
        )
        db.commit()
        _raise_blood_error(exc)
    return [_unit_to_dict(unit) for unit in units]


# ---- Crossmatch ----

@router.post("/crossmatch", status_code=status.HTTP_201_CREATED)
async def perform_crossmatch(
    body: dict[str, Any],
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    if_match: str | None = Header(None, alias="If-Match"),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
) -> dict[str, Any]:
    lab_id = _lab_id(current_user)
    unit = (
        db.query(BloodUnitModel)
        .filter(BloodUnitModel.id == body.get("unit_id"), BloodUnitModel.lab_id == lab_id)
        .with_for_update()
        .first()
    )
    if not unit:
        raise HTTPException(status_code=404, detail="Resource not found")
    guard = _guard(db, current_user)
    version_before = unit.version
    state_before = unit.status
    guard.require_expected_version(if_match, current_version=version_before, resource_name="blood unit")
    key = guard.require_idempotency_key(idempotency_key)
    receipt = guard.claim(
        operation="blood.crossmatch.perform", resource_type="blood_unit", resource_id=unit.id,
        idempotency_key=key, payload=body,
    )
    try:
        crossmatch = BloodBankService(db).perform_crossmatch_safely(
            {**body, "lab_id": lab_id, "performed_by": str(current_user.id)},
        )
        guard.complete(
            receipt, resource_type="blood_crossmatch", resource_id=crossmatch.id,
            state_before=state_before, state_after=crossmatch.status,
            version_before=version_before, version_after=unit.version,
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        guard.reject(
            operation="blood.crossmatch.perform", resource_type="blood_unit", resource_id=unit.id,
            state_before=state_before, version_before=version_before, reason=str(exc),
        )
        db.commit()
        _raise_blood_error(exc)
    db.refresh(crossmatch)
    return _crossmatch_to_dict(crossmatch)


@router.post("/crossmatch/{crossmatch_id}/verify")
async def verify_crossmatch(
    crossmatch_id: str,
    body: dict[str, Any],
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    if_match: str | None = Header(None, alias="If-Match"),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
) -> dict[str, Any]:
    lab_id = _lab_id(current_user)
    crossmatch = (
        db.query(CrossmatchModel)
        .filter(CrossmatchModel.id == crossmatch_id, CrossmatchModel.lab_id == lab_id)
        .with_for_update()
        .first()
    )
    if not crossmatch:
        raise HTTPException(status_code=404, detail="Resource not found")
    guard = _guard(db, current_user)
    version_before = crossmatch.version
    state_before = crossmatch.status
    guard.require_expected_version(if_match, current_version=version_before, resource_name="crossmatch")
    key = guard.require_idempotency_key(idempotency_key)
    receipt = guard.claim(
        operation="blood.crossmatch.verify", resource_type="blood_crossmatch", resource_id=crossmatch.id,
        idempotency_key=key, payload=body,
    )
    try:
        verified = BloodBankService(db).verify_crossmatch_safely(
            crossmatch_id, lab_id, str(current_user.id),
        )
        guard.complete(
            receipt, resource_type="blood_crossmatch", resource_id=verified.id,
            state_before=state_before, state_after="verified",
            version_before=version_before, version_after=verified.version,
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        guard.reject(
            operation="blood.crossmatch.verify", resource_type="blood_crossmatch", resource_id=crossmatch_id,
            state_before=state_before, version_before=version_before, reason=str(exc),
        )
        db.commit()
        _raise_blood_error(exc)
    db.refresh(verified)
    return _crossmatch_to_dict(verified)


@router.post("/crossmatch/check")
async def check_blood_compatibility(
    body: dict[str, Any],
) -> dict[str, Any]:
    return check_compatibility(
        body.get("patient_group", ""),
        body.get("unit_group", ""),
    )


@router.get("/crossmatch/compatible-groups/{patient_group}")
async def get_compatible_blood_groups(
    patient_group: str,
) -> list[dict[str, Any]]:
    return get_compatible_groups(patient_group)


# ---- Transfusion ----

@router.post("/transfusions", status_code=status.HTTP_201_CREATED)
async def record_transfusion(
    body: dict[str, Any],
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    if_match: str | None = Header(None, alias="If-Match"),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
) -> dict[str, Any]:
    lab_id = _lab_id(current_user)
    unit = (
        db.query(BloodUnitModel)
        .filter(BloodUnitModel.id == body.get("unit_id"), BloodUnitModel.lab_id == lab_id)
        .with_for_update()
        .first()
    )
    if not unit:
        raise HTTPException(status_code=404, detail="Resource not found")
    guard = _guard(db, current_user)
    version_before = unit.version
    state_before = unit.status
    guard.require_expected_version(if_match, current_version=version_before, resource_name="blood unit")
    key = guard.require_idempotency_key(idempotency_key)
    receipt = guard.claim(
        operation="blood.transfusion.order", resource_type="blood_unit", resource_id=unit.id,
        idempotency_key=key, payload=body,
    )
    try:
        transfusion = BloodBankService(db).record_transfusion_safely(
            {**body, "lab_id": lab_id, "ordered_by": str(current_user.id)},
        )
        guard.complete(
            receipt, resource_type="blood_transfusion", resource_id=transfusion.id,
            state_before=state_before, state_after=transfusion.status,
            version_before=version_before, version_after=unit.version,
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        guard.reject(
            operation="blood.transfusion.order", resource_type="blood_unit", resource_id=unit.id,
            state_before=state_before, version_before=version_before, reason=str(exc),
        )
        db.commit()
        _raise_blood_error(exc)
    db.refresh(transfusion)
    return _transfusion_to_dict(transfusion)


@router.post("/transfusions/{transfusion_id}/verify")
async def verify_transfusion(
    transfusion_id: str,
    body: dict[str, Any],
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    if_match: str | None = Header(None, alias="If-Match"),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
) -> dict[str, Any]:
    lab_id = _lab_id(current_user)
    transfusion = (
        db.query(TransfusionModel)
        .filter(TransfusionModel.id == transfusion_id, TransfusionModel.lab_id == lab_id)
        .with_for_update()
        .first()
    )
    if not transfusion:
        raise HTTPException(status_code=404, detail="Resource not found")
    guard = _guard(db, current_user)
    version_before = transfusion.version
    state_before = transfusion.status
    guard.require_expected_version(if_match, current_version=version_before, resource_name="transfusion")
    key = guard.require_idempotency_key(idempotency_key)
    receipt = guard.claim(
        operation="blood.transfusion.verify", resource_type="blood_transfusion", resource_id=transfusion.id,
        idempotency_key=key, payload=body,
    )
    try:
        verified = BloodBankService(db).verify_transfusion_safely(
            transfusion_id, lab_id, {**body, "verified_by": str(current_user.id)},
        )
        guard.complete(
            receipt, resource_type="blood_transfusion", resource_id=verified.id,
            state_before=state_before, state_after=verified.status,
            version_before=version_before, version_after=verified.version,
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        guard.reject(
            operation="blood.transfusion.verify", resource_type="blood_transfusion", resource_id=transfusion_id,
            state_before=state_before, version_before=version_before, reason=str(exc),
        )
        db.commit()
        _raise_blood_error(exc)
    db.refresh(verified)
    return _transfusion_to_dict(verified)


@router.post("/transfusions/{transfusion_id}/start")
async def start_transfusion(
    transfusion_id: str,
    body: dict[str, Any],
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    if_match: str | None = Header(None, alias="If-Match"),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
) -> dict[str, Any]:
    lab_id = _lab_id(current_user)
    transfusion = (
        db.query(TransfusionModel)
        .filter(TransfusionModel.id == transfusion_id, TransfusionModel.lab_id == lab_id)
        .with_for_update()
        .first()
    )
    if not transfusion:
        raise HTTPException(status_code=404, detail="Resource not found")
    guard = _guard(db, current_user)
    version_before = transfusion.version
    state_before = transfusion.status
    guard.require_expected_version(if_match, current_version=version_before, resource_name="transfusion")
    key = guard.require_idempotency_key(idempotency_key)
    receipt = guard.claim(
        operation="blood.transfusion.start", resource_type="blood_transfusion", resource_id=transfusion.id,
        idempotency_key=key, payload=body,
    )
    try:
        started = BloodBankService(db).start_transfusion_safely(
            transfusion_id, lab_id, str(current_user.id),
        )
        guard.complete(
            receipt, resource_type="blood_transfusion", resource_id=started.id,
            state_before=state_before, state_after=started.status,
            version_before=version_before, version_after=started.version,
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        guard.reject(
            operation="blood.transfusion.start", resource_type="blood_transfusion", resource_id=transfusion_id,
            state_before=state_before, version_before=version_before, reason=str(exc),
        )
        db.commit()
        _raise_blood_error(exc)
    db.refresh(started)
    return _transfusion_to_dict(started)


@router.post("/transfusions/{transfusion_id}/complete")
async def complete_transfusion(
    transfusion_id: str,
    body: dict[str, Any],
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    if_match: str | None = Header(None, alias="If-Match"),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
) -> dict[str, Any]:
    lab_id = _lab_id(current_user)
    transfusion = (
        db.query(TransfusionModel)
        .filter(TransfusionModel.id == transfusion_id, TransfusionModel.lab_id == lab_id)
        .with_for_update()
        .first()
    )
    if not transfusion:
        raise HTTPException(status_code=404, detail="Resource not found")
    guard = _guard(db, current_user)
    version_before = transfusion.version
    state_before = transfusion.status
    guard.require_expected_version(if_match, current_version=version_before, resource_name="transfusion")
    key = guard.require_idempotency_key(idempotency_key)
    receipt = guard.claim(
        operation="blood.transfusion.complete", resource_type="blood_transfusion", resource_id=transfusion.id,
        idempotency_key=key, payload=body,
    )
    try:
        completed = BloodBankService(db).complete_transfusion_safely(transfusion_id, lab_id, body)
        guard.complete(
            receipt, resource_type="blood_transfusion", resource_id=completed.id,
            state_before=state_before, state_after=completed.status,
            version_before=version_before, version_after=completed.version,
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        guard.reject(
            operation="blood.transfusion.complete", resource_type="blood_transfusion", resource_id=transfusion_id,
            state_before=state_before, version_before=version_before, reason=str(exc),
        )
        db.commit()
        _raise_blood_error(exc)
    db.refresh(completed)
    return _transfusion_to_dict(completed)


# ---- Blood Requests ----

@router.post("/requests", status_code=status.HTTP_201_CREATED)
async def create_blood_request(
    body: dict[str, Any],
    service: BloodBankService = Depends(_get_service),
) -> dict[str, Any]:
    req = service.create_blood_request(body)
    return _request_to_dict(req)


@router.get("/dashboard")
async def get_dashboard(
    service: BloodBankService = Depends(_get_service),
) -> dict[str, Any]:
    return service.get_dashboard()


@router.get("/health")
async def health() -> dict[str, Any]:
    return {"status": "ok", "module": "national_blood_bank_platform", "version": "1.0.0"}


# ---- Serializers ----

def _donor_to_dict(d: Any) -> dict[str, Any]:
    return {
        "id": d.id, "citizen_id": d.citizen_id, "full_name": d.full_name, "phone": d.phone,
        "blood_group": d.blood_group, "rh_factor": d.rh_factor, "status": d.status,
        "total_donations": d.total_donations, "total_volume_ml": d.total_volume_ml,
        "last_donation_date": d.last_donation_date.isoformat() if d.last_donation_date else None,
        "next_eligible_date": d.next_eligible_date.isoformat() if d.next_eligible_date else None,
        "consent_signed": d.consent_signed,
    }


def _donation_to_dict(d: Any) -> dict[str, Any]:
    return {
        "id": d.id, "donor_id": d.donor_id, "donation_type": d.donation_type,
        "volume_ml": d.volume_ml, "status": d.status,
        "bag_identifier": d.bag_identifier, "isbt_128_code": d.isbt_128_code,
    }


def _component_to_dict(c: Any) -> dict[str, Any]:
    return {
        "id": c.id, "donation_id": c.donation_id, "component": c.component,
        "status": c.status, "bag_identifier": c.bag_identifier, "isbt_128_code": c.isbt_128_code,
    }


def _inventory_to_dict(i: Any) -> dict[str, Any]:
    return {
        "id": i.id, "facility_id": i.facility_id, "blood_group": i.blood_group,
        "rh_factor": i.rh_factor, "component": i.component, "quantity": i.quantity,
        "reserved_quantity": i.reserved_quantity, "available_quantity": i.available_quantity,
        "minimum_stock": i.minimum_stock, "critical_threshold": i.critical_threshold,
        "is_critical": i.is_critical,
    }


def _unit_to_dict(u: Any) -> dict[str, Any]:
    return {
        "id": u.id, "blood_group": u.blood_group, "component": u.component,
        "bag_identifier": u.bag_identifier, "status": u.status,
    }


def _crossmatch_to_dict(c: Any) -> dict[str, Any]:
    return {
        "id": c.id, "patient_id": c.patient_id, "unit_id": c.unit_id,
        "status": c.status.value if hasattr(c.status, "value") else c.status,
        "abo_compatible": c.abo_compatible,
    }


def _transfusion_to_dict(t: Any) -> dict[str, Any]:
    return {
        "id": t.id, "patient_id": t.patient_id, "unit_id": t.unit_id,
        "status": t.status.value if hasattr(t.status, "value") else t.status,
    }


def _request_to_dict(r: Any) -> dict[str, Any]:
    return {
        "id": r.id, "patient_id": r.patient_id, "blood_group": r.blood_group,
        "units_requested": r.units_requested, "urgency": r.urgency, "status": r.status,
    }


# ---- Phase 2 operational endpoints ----

def _phase2_dict(model: Any) -> dict[str, Any]:
    return model.to_dict() if hasattr(model, "to_dict") else {c.name: getattr(model, c.name) for c in model.__table__.columns}


@router.post("/samples", status_code=status.HTTP_201_CREATED)
async def create_patient_blood_sample(
    body: dict[str, Any], current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db), idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
) -> dict[str, Any]:
    lab_id = _lab_id(current_user)
    guard = _guard(db, current_user)
    key = guard.require_idempotency_key(idempotency_key)
    receipt = guard.claim(operation="blood.sample.create", resource_type="patient_sample", resource_id=body.get("specimen_identifier", "new"), idempotency_key=key, payload=body)
    try:
        sample = BloodBankService(db).create_patient_sample({**body, "lab_id": lab_id, "collected_by": str(current_user.id)})
        guard.complete(receipt, resource_type="patient_sample", resource_id=sample.id, state_before=None, state_after=sample.status, version_before=0, version_after=sample.version)
        db.commit()
        db.refresh(sample)
        return _phase2_dict(sample)
    except Exception as exc:
        db.rollback()
        _raise_blood_error(exc)
        raise


@router.post("/samples/{sample_id}/transition")
async def transition_patient_blood_sample(
    sample_id: str, body: dict[str, Any], current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db), if_match: str | None = Header(None, alias="If-Match"),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
) -> dict[str, Any]:
    lab_id = _lab_id(current_user)
    sample = db.query(PatientBloodSampleModel).filter(PatientBloodSampleModel.id == sample_id, PatientBloodSampleModel.lab_id == lab_id).first()
    if not sample:
        raise HTTPException(status_code=404, detail="Resource not found")
    guard = _guard(db, current_user)
    guard.require_expected_version(if_match, current_version=sample.version, resource_name="patient blood sample")
    guard.require_idempotency_key(idempotency_key)
    try:
        updated = BloodBankService(db).transition_patient_sample(sample_id, lab_id, str(body.get("target", "")), str(current_user.id))
        db.commit(); db.refresh(updated)
        return _phase2_dict(updated)
    except Exception as exc:
        db.rollback(); _raise_blood_error(exc); raise


@router.post("/reservations", status_code=status.HTTP_201_CREATED)
async def reserve_blood_unit(
    body: dict[str, Any], current_user: LabUser = Depends(get_current_user), db: Session = Depends(get_db),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
) -> dict[str, Any]:
    guard = _guard(db, current_user)
    key = guard.require_idempotency_key(idempotency_key)
    receipt = guard.claim(operation="blood.reservation.create", resource_type="blood_unit", resource_id=body.get("unit_id", "new"), idempotency_key=key, payload=body)
    maybe_fail("after_claim")
    try:
        reservation = BloodBankService(db).reserve_unit({**body, "lab_id": _lab_id(current_user), "requested_by": str(current_user.id)})
        maybe_fail("after_business_effect")
        guard.complete(receipt, resource_type="reservation", resource_id=reservation.id, state_before="available", state_after=reservation.status, version_before=0, version_after=reservation.version)
        db.commit(); db.refresh(reservation)
        maybe_fail("after_commit")
        return _phase2_dict(reservation)
    except Exception as exc:
        db.rollback(); _raise_blood_error(exc); raise


@router.post("/reservations/{reservation_id}/release")
async def release_blood_reservation(
    reservation_id: str, body: dict[str, Any], current_user: LabUser = Depends(get_current_user), db: Session = Depends(get_db),
    if_match: str | None = Header(None, alias="If-Match"), idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
) -> dict[str, Any]:
    lab_id = _lab_id(current_user)
    reservation = db.query(BloodReservationModel).filter(BloodReservationModel.id == reservation_id, BloodReservationModel.lab_id == lab_id).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Resource not found")
    guard = _guard(db, current_user)
    guard.require_expected_version(if_match, current_version=reservation.version, resource_name="blood reservation")
    key = guard.require_idempotency_key(idempotency_key)
    receipt = guard.claim(operation="blood.reservation.release", resource_type="reservation", resource_id=reservation_id, idempotency_key=key, payload=body)
    try:
        result = BloodBankService(db).release_reservation(reservation_id, lab_id, str(current_user.id), str(body.get("reason", "")))
        guard.complete(receipt, resource_type="reservation", resource_id=result.id, state_before="reserved", state_after=result.status, version_before=reservation.version - 1, version_after=result.version)
        db.commit(); db.refresh(result)
        return _phase2_dict(result)
    except Exception as exc:
        db.rollback(); _raise_blood_error(exc); raise


@router.post("/reactions", status_code=status.HTTP_201_CREATED)
async def create_transfusion_reaction(
    body: dict[str, Any], current_user: LabUser = Depends(get_current_user), db: Session = Depends(get_db),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
) -> dict[str, Any]:
    guard = _guard(db, current_user)
    key = guard.require_idempotency_key(idempotency_key)
    receipt = guard.claim(operation="blood.reaction.create", resource_type="transfusion", resource_id=body.get("transfusion_id", "new"), idempotency_key=key, payload=body)
    try:
        reaction = BloodBankService(db).create_reaction({**body, "lab_id": _lab_id(current_user), "reporter_id": str(current_user.id)})
        guard.complete(receipt, resource_type="reaction", resource_id=reaction.id, state_before=None, state_after=reaction.status, version_before=0, version_after=reaction.version)
        db.commit(); db.refresh(reaction)
        return _phase2_dict(reaction)
    except Exception as exc:
        db.rollback(); _raise_blood_error(exc); raise


@router.get("/units/{unit_id}/traceability")
async def get_unit_traceability(
    unit_id: str, current_user: LabUser = Depends(get_current_user), db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    lab_id = _lab_id(current_user)
    unit = db.query(BloodUnitModel).filter(BloodUnitModel.id == unit_id, BloodUnitModel.lab_id == lab_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Resource not found")
    return [_phase2_dict(event) for event in BloodBankService(db).trace_unit(unit_id, lab_id)]


@router.post("/returns", status_code=status.HTTP_201_CREATED)
async def return_blood_unit(
    body: dict[str, Any], current_user: LabUser = Depends(get_current_user), db: Session = Depends(get_db),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
) -> dict[str, Any]:
    guard = _guard(db, current_user)
    key = guard.require_idempotency_key(idempotency_key)
    receipt = guard.claim(operation="blood.return.create", resource_type="blood_unit", resource_id=body.get("unit_id", "new"), idempotency_key=key, payload=body)
    try:
        returned = BloodBankService(db).return_unit({**body, "lab_id": _lab_id(current_user), "actor_id": str(current_user.id)})
        guard.complete(receipt, resource_type="return", resource_id=returned.id, state_before="issued", state_after=returned.status, version_before=0, version_after=returned.version)
        db.commit(); db.refresh(returned)
        return _phase2_dict(returned)
    except Exception as exc:
        db.rollback(); _raise_blood_error(exc); raise


@router.post("/discards", status_code=status.HTTP_201_CREATED)
async def discard_blood_unit(
    body: dict[str, Any], current_user: LabUser = Depends(get_current_user), db: Session = Depends(get_db),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
) -> dict[str, Any]:
    guard = _guard(db, current_user)
    key = guard.require_idempotency_key(idempotency_key)
    receipt = guard.claim(operation="blood.discard.create", resource_type="blood_unit", resource_id=body.get("unit_id", "new"), idempotency_key=key, payload=body)
    try:
        discarded = BloodBankService(db).discard_unit({**body, "lab_id": _lab_id(current_user), "actor_id": str(current_user.id)})
        guard.complete(receipt, resource_type="discard", resource_id=discarded.id, state_before=None, state_after="discarded", version_before=0, version_after=discarded.version)
        db.commit(); db.refresh(discarded)
        return _phase2_dict(discarded)
    except Exception as exc:
        db.rollback(); _raise_blood_error(exc); raise


@router.get("/inventory/reconciliation")
async def reconcile_blood_inventory(
    facility_id: str | None = Query(None), current_user: LabUser = Depends(get_current_user), db: Session = Depends(get_db),
) -> dict[str, Any]:
    return BloodBankService(db).reconcile_inventory(_lab_id(current_user), facility_id)

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.blood_bank.application.service import BloodBankService
from app.blood_bank.compatibility import check_compatibility, get_compatible_groups
from app.blood_bank.exceptions import (
    CrossmatchConflictError,
    DonorDeferredError,
    DonorNotFoundError,
    InsufficientStockError,
    TransfusionNotFoundError,
)
from app.database import get_db
from app.security.dependencies import get_current_user

router = APIRouter(
    prefix="/blood-bank",
    tags=["National Blood Bank Platform"],
    dependencies=[Depends(get_current_user)],
)


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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found",
        ) from e


@router.post("/donors/{donor_id}/defer")
async def defer_donor(
    donor_id: str,
    body: dict[str, Any],
    service: BloodBankService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        deferral = service.defer_donor(donor_id, body)
        return {
            "id": deferral.id,
            "donor_id": donor_id,
            "deferral_days": deferral.deferral_days,
            "deferred_until": deferral.deferred_until.isoformat()
            if deferral.deferred_until
            else None,
            "reason": deferral.reason,
        }
    except DonorNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found",
        ) from e


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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found",
        ) from e
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
    service: BloodBankService = Depends(_get_service),
) -> list[dict[str, Any]]:
    try:
        units = service.issue_units(
            blood_group=body.get("blood_group", ""),
            component=body.get("component", ""),
            quantity=body.get("quantity", 1),
            facility_id=body.get("facility_id", ""),
        )
        return [_unit_to_dict(u) for u in units]
    except InsufficientStockError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Resource conflict") from e


# ---- Crossmatch ----


@router.post("/crossmatch", status_code=status.HTTP_201_CREATED)
async def perform_crossmatch(
    body: dict[str, Any],
    service: BloodBankService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        crossmatch = service.perform_crossmatch(body)
        return _crossmatch_to_dict(crossmatch)
    except CrossmatchConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Resource conflict") from e


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
    service: BloodBankService = Depends(_get_service),
) -> dict[str, Any]:
    transfusion = service.record_transfusion(body)
    return _transfusion_to_dict(transfusion)


@router.post("/transfusions/{transfusion_id}/start")
async def start_transfusion(
    transfusion_id: str,
    service: BloodBankService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        return _transfusion_to_dict(service.start_transfusion(transfusion_id))
    except TransfusionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found",
        ) from e


@router.post("/transfusions/{transfusion_id}/complete")
async def complete_transfusion(
    transfusion_id: str,
    service: BloodBankService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        return _transfusion_to_dict(service.complete_transfusion(transfusion_id))
    except TransfusionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found",
        ) from e


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
        "id": d.id,
        "citizen_id": d.citizen_id,
        "full_name": d.full_name,
        "phone": d.phone,
        "blood_group": d.blood_group,
        "rh_factor": d.rh_factor,
        "status": d.status,
        "total_donations": d.total_donations,
        "total_volume_ml": d.total_volume_ml,
        "last_donation_date": d.last_donation_date.isoformat() if d.last_donation_date else None,
        "next_eligible_date": d.next_eligible_date.isoformat() if d.next_eligible_date else None,
        "consent_signed": d.consent_signed,
    }


def _donation_to_dict(d: Any) -> dict[str, Any]:
    return {
        "id": d.id,
        "donor_id": d.donor_id,
        "donation_type": d.donation_type,
        "volume_ml": d.volume_ml,
        "status": d.status,
        "bag_identifier": d.bag_identifier,
        "isbt_128_code": d.isbt_128_code,
    }


def _component_to_dict(c: Any) -> dict[str, Any]:
    return {
        "id": c.id,
        "donation_id": c.donation_id,
        "component": c.component,
        "status": c.status,
        "bag_identifier": c.bag_identifier,
        "isbt_128_code": c.isbt_128_code,
    }


def _inventory_to_dict(i: Any) -> dict[str, Any]:
    return {
        "id": i.id,
        "facility_id": i.facility_id,
        "blood_group": i.blood_group,
        "rh_factor": i.rh_factor,
        "component": i.component,
        "quantity": i.quantity,
        "reserved_quantity": i.reserved_quantity,
        "available_quantity": i.available_quantity,
        "minimum_stock": i.minimum_stock,
        "critical_threshold": i.critical_threshold,
        "is_critical": i.is_critical,
    }


def _unit_to_dict(u: Any) -> dict[str, Any]:
    return {
        "id": u.id,
        "blood_group": u.blood_group,
        "component": u.component,
        "bag_identifier": u.bag_identifier,
        "status": u.status,
    }


def _crossmatch_to_dict(c: Any) -> dict[str, Any]:
    return {
        "id": c.id,
        "patient_id": c.patient_id,
        "unit_id": c.unit_id,
        "status": c.status.value if hasattr(c.status, "value") else c.status,
        "abo_compatible": c.abo_compatible,
    }


def _transfusion_to_dict(t: Any) -> dict[str, Any]:
    return {
        "id": t.id,
        "patient_id": t.patient_id,
        "unit_id": t.unit_id,
        "status": t.status.value if hasattr(t.status, "value") else t.status,
    }


def _request_to_dict(r: Any) -> dict[str, Any]:
    return {
        "id": r.id,
        "patient_id": r.patient_id,
        "blood_group": r.blood_group,
        "units_requested": r.units_requested,
        "urgency": r.urgency,
        "status": r.status,
    }

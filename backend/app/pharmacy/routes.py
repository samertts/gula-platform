from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.clinical.command_guard import ClinicalCommandGuard
from app.database import get_db
from app.pharmacy.enums import (
    DrugCategory,
    PrescriptionStatus,
    RouteOfAdministration,
    StockMovementType,
    StorageCondition,
)
from app.pharmacy.models import (
    Prescription,
    StockLevel,
)
from app.pharmacy.services import PharmacyService, PharmacyWorkflowError
from app.security.dependencies import get_current_user, require_institutional_permission

router = APIRouter(prefix="/pharmacy", tags=["Pharmacy"])


# ── Pydantic Schemas ───────────────────────────────────────────────────────────


class DrugCatalogCreate(BaseModel):
    code: str
    name: str
    name_ar: str | None = None
    generic_name: str | None = None
    brand_name: str | None = None
    manufacturer: str | None = None
    manufacturer_code: str | None = None
    form: DrugCategory | None = None
    strength_value: str | None = None
    strength_unit: str | None = None
    route: RouteOfAdministration | None = None
    category: DrugCategory | None = None
    therapeutic_class: str | None = None
    atc_code: str | None = None
    atc_description: str | None = None
    is_controlled: bool = False
    is_narcotic: bool = False
    requires_prescription: bool = True
    is_active: bool = True
    max_daily_dose: str | None = None
    min_age: int | None = None
    pregnancy_category: str | None = None
    lactation_category: str | None = None
    ingredients: list[dict[str, Any]] | None = None
    side_effects: list[dict[str, Any]] | None = None
    drug_images: list[dict[str, Any]] | None = None
    barcode_gs1: str | None = None
    barcode_type: str | None = None


class DrugCatalogUpdate(BaseModel):
    name: str | None = None
    name_ar: str | None = None
    generic_name: str | None = None
    brand_name: str | None = None
    manufacturer: str | None = None
    manufacturer_code: str | None = None
    form: DrugCategory | None = None
    strength_value: str | None = None
    strength_unit: str | None = None
    route: RouteOfAdministration | None = None
    category: DrugCategory | None = None
    therapeutic_class: str | None = None
    atc_code: str | None = None
    atc_description: str | None = None
    is_controlled: bool | None = None
    is_narcotic: bool | None = None
    requires_prescription: bool | None = None
    is_active: bool | None = None
    max_daily_dose: str | None = None
    min_age: int | None = None
    pregnancy_category: str | None = None
    lactation_category: str | None = None
    ingredients: list[dict[str, Any]] | None = None
    side_effects: list[dict[str, Any]] | None = None
    drug_images: list[dict[str, Any]] | None = None
    barcode_gs1: str | None = None
    barcode_type: str | None = None


class DrugCatalogResponse(BaseModel):
    id: str
    code: str
    name: str
    name_ar: str | None
    generic_name: str | None
    brand_name: str | None
    manufacturer: str | None
    manufacturer_code: str | None
    form: str | None
    strength_value: str | None
    strength_unit: str | None
    route: str | None
    category: str | None
    therapeutic_class: str | None
    atc_code: str | None
    atc_description: str | None
    is_controlled: bool
    is_narcotic: bool
    requires_prescription: bool
    is_active: bool
    max_daily_dose: str | None
    min_age: int | None
    pregnancy_category: str | None
    lactation_category: str | None
    ingredients: list[dict[str, Any]] | None
    side_effects: list[dict[str, Any]] | None
    barcode_gs1: str | None
    is_deleted: bool
    created_at: str | None
    updated_at: str | None

    model_config = ConfigDict(from_attributes=True)


class DrugCatalogListResponse(BaseModel):
    items: list[DrugCatalogResponse]
    total: int
    skip: int
    limit: int


class DrugBatchCreate(BaseModel):
    batch_number: str
    expiry_date: date
    manufacturing_date: date | None = None
    quantity_initial: float = 0
    storage_condition: StorageCondition | None = None
    location: str | None = None
    cost_price: float | None = None
    selling_price: float | None = None


class DrugBatchResponse(BaseModel):
    """A received lot.

    ``id`` is the batch's public ``batch_id`` and ``drug_catalog_id`` the
    drug's public ``drug_id``; neither internal Integer key is published
    (CANONICAL_DRUG_CONTRACT §3). Quantities are floats because stock is
    ``DOUBLE PRECISION`` physically — an integer would truncate a half tablet.
    """

    id: str
    drug_catalog_id: str
    batch_number: str
    expiry_date: str
    manufacturing_date: str | None
    quantity_initial: float
    quantity_remaining: float
    storage_condition: str | None
    location: str | None
    received_date: str | None
    supplier: str | None
    cost_price: float | None
    selling_price: float | None
    is_quarantined: bool
    status: str


class SupplierCreate(BaseModel):
    supplier_name: str
    supplier_name_ar: str | None = None
    supplier_code: str
    contact_person: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    license_number: str | None = None
    is_active: bool = True
    payment_terms: str | None = None


class SupplierResponse(BaseModel):
    id: int
    supplier_name: str
    supplier_name_ar: str | None
    supplier_code: str
    contact_person: str | None
    phone: str | None
    email: str | None
    address: str | None
    license_number: str | None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class PrescriptionCreate(BaseModel):
    patient_id: int | None = None
    prescription_number: str | None = None
    prescribed_by: str
    prescriber_license: str | None = None
    prescription_type: str | None = None
    diagnosis_code: str | None = None
    diagnosis_description: str | None = None
    clinical_notes: str | None = None
    is_stat: bool = False
    is_verbal: bool = False
    is_emergency: bool = False
    refills_allowed: int = 0
    valid_until: datetime | None = None


class PrescriptionResponse(BaseModel):
    """``id`` is the prescription's public ``prescription_id`` (UUID4).

    The previous shape advertised ``intent``, ``priority``, ``diagnosis_system``
    and ``substitution_allowed``; none exists in the schema, so the endpoint
    could never have returned them. ``prescribed_by`` is the prescriber's name
    as free text — there is no practitioner foreign key to expose.
    """

    id: str
    patient_id: int | None
    prescription_number: str
    prescribed_by: str
    prescriber_license: str | None
    prescription_type: str | None
    status: str
    diagnosis_code: str | None
    diagnosis_description: str | None
    clinical_notes: str | None
    prescribed_at: str | None
    valid_until: str | None
    refills_allowed: int | None
    refills_used: int | None
    is_stat: bool
    is_emergency: bool


class PrescriptionItemCreate(BaseModel):
    drug_catalog_id: str
    drug_name: str | None = None
    dosage: str
    frequency: str
    route: str | None = None
    duration: str | None = None
    quantity: float
    quantity_unit: str | None = None
    refill_quantity: float | None = None
    instructions: str | None = None
    patient_education: str | None = None
    is_substitution_allowed: bool = True


class PrescriptionItemResponse(BaseModel):
    id: str
    prescription_id: str
    drug_catalog_id: str
    drug_name: str
    dosage: str
    frequency: str
    route: str | None
    duration: str | None
    quantity: float
    quantity_unit: str | None
    refill_quantity: float | None
    instructions: str | None
    patient_education: str | None
    is_substitution_allowed: bool
    status: str


class DispenseRecordCreate(BaseModel):
    prescription_id: str | None = None
    prescription_item_id: str | None = None
    patient_id: int | None = None
    drug_catalog_id: str
    dispensed_by: int
    verified_by: int
    quantity_dispensed: float
    quantity_unit: str | None = None
    days_supply: int | None = None
    batch_id: str
    dosage_dispensed: str | None = None
    instructions: str | None = None
    label_notes: str | None = None


class DispenseRecordResponse(BaseModel):
    id: int
    prescription_id: str | None
    patient_id: int | None
    drug_catalog_id: str
    batch_id: str | None
    dispense_number: str
    dispensed_by: int
    verified_by: int | None
    dispensed_at: str | None
    quantity_dispensed: float
    quantity_unit: str | None
    days_supply: int | None
    is_verified: bool
    is_counselled: bool
    instructions: str | None


class StockLevelResponse(BaseModel):
    id: int
    drug_catalog_id: str
    batch_id: str | None
    warehouse_id: int | None
    store_id: int | None
    quantity: float
    reserved_quantity: float
    available_quantity: float
    reorder_point: float | None
    reorder_quantity: float | None
    max_level: float | None
    unit: str
    location: str | None
    last_count_date: str | None


class StockAdjustRequest(BaseModel):
    drug_catalog_id: str
    batch_id: str | None = None
    warehouse_id: int | None = None
    store_id: int | None = None
    adjustment: float
    unit: str = "unit"
    reason: str = "Manual adjustment"


class MovementCreate(BaseModel):
    drug_catalog_id: str
    batch_id: str | None = None
    movement_type: StockMovementType
    quantity: float
    unit: str = "unit"
    reason: str | None = None
    notes: str | None = None


class TransferCreate(BaseModel):
    from_warehouse_id: int | None = None
    to_warehouse_id: int | None = None
    from_store_id: int | None = None
    to_store_id: int | None = None
    transfer_type: str = "internal"
    transfer_number: str | None = None
    notes: str | None = None


class TransferItemCreate(BaseModel):
    drug_catalog_id: str
    batch_id: str | None = None
    quantity: float
    unit: str = "unit"


class ReturnCreate(BaseModel):
    patient_id: int | None = None
    drug_catalog_id: str
    batch_id: str | None = None
    return_type: str = "patient"
    return_reason: str
    quantity: float
    unit: str = "unit"
    disposition: str | None = None


class WasteCreate(BaseModel):
    drug_catalog_id: str
    batch_id: str | None = None
    quantity: float
    unit: str = "unit"
    waste_type: str = "expired"
    waste_reason: str
    witnessed_by: int | None = None
    disposal_method: str | None = None


class RecallCreate(BaseModel):
    drug_catalog_id: str
    batch_id: str | None = None
    recall_number: str | None = None
    recall_reason: str
    recall_source: str | None = None
    severity: str
    status: str = "active"
    actions_taken: str | None = None
    notes: str | None = None


class RecallResponse(BaseModel):
    id: int
    drug_catalog_id: str
    batch_id: str | None
    recall_number: str
    recall_reason: str
    recall_source: str | None
    initiated_at: str
    severity: str
    status: str
    actions_taken: str | None
    notes: str | None


class InteractionCheckRequest(BaseModel):
    drug_codes: list[str]


class InteractionCheckResponse(BaseModel):
    interactions: list[dict[str, Any]]
    total: int
    severe_count: int


class ContraindicationCheckRequest(BaseModel):
    drug_code: str
    condition_codes: list[str]


class AllergyCheckRequest(BaseModel):
    drug_code: str
    allergen_codes: list[str]


class DoseCalculateRequest(BaseModel):
    drug_code: str
    indication_code: str | None = None
    age_months: int | None = None
    weight_kg: float | None = None


class RenalAdjustRequest(BaseModel):
    drug_code: str
    egfr: float
    weight_kg: float | None = None


class PolypharmacyCheckRequest(BaseModel):
    drug_codes: list[str]


class MovementResponse(BaseModel):
    id: int
    drug_catalog_id: str
    batch_id: str | None
    movement_type: str
    quantity: float
    unit: str
    reference_type: str | None
    reference_id: int | None
    reason: str | None
    performed_by: int
    movement_date: str
    notes: str | None


class TransferResponse(BaseModel):
    id: str
    transfer_number: str
    from_warehouse_id: int | None
    to_warehouse_id: int | None
    from_store_id: int | None
    to_store_id: int | None
    transfer_type: str
    status: str
    requested_by: int | None
    approved_by: int | None
    dispatch_date: str | None
    received_date: str | None
    notes: str | None


class DashboardResponse(BaseModel):
    total_prescriptions: int
    active_prescriptions: int
    pending_queue: int
    dispensed_today: int



# ── Response builders ──────────────────────────────────────────────────────────
#
# These entities are returned through explicit builders rather than
# ``model_validate``, for one reason: after M4 their ``id`` is an internal
# INTEGER key, and the contract forbids publishing it as an entity's identity
# (§3). Each builder swaps in the entity's public identifier and resolves
# related rows to *their* public identifiers.


def _iso(value: Any) -> str | None:
    return value.isoformat() if value is not None else None


def _drug_batch_response(batch: Any) -> DrugBatchResponse:
    drug = batch.drug
    supplier = batch.supplier
    return DrugBatchResponse(
        id=str(batch.batch_id),
        drug_catalog_id=str(drug.drug_id) if drug else "",
        batch_number=batch.batch_number,
        expiry_date=batch.expiry_date.isoformat(),
        manufacturing_date=_iso(batch.manufacturing_date),
        quantity_initial=batch.quantity_received,
        quantity_remaining=batch.quantity_remaining,
        storage_condition=batch.storage_condition,
        location=batch.location,
        received_date=_iso(batch.received_date),
        # There is no free-text supplier column: a batch names a supplier row.
        supplier=supplier.supplier_name if supplier else None,
        cost_price=float(batch.unit_cost) if batch.unit_cost is not None else None,
        selling_price=float(batch.selling_price) if batch.selling_price is not None else None,
        is_quarantined=bool(batch.is_quarantined),
        status=batch.status,
    )


def _prescription_response(rx: Any) -> PrescriptionResponse:
    return PrescriptionResponse(
        id=str(rx.prescription_id),
        patient_id=rx.patient_id,
        prescription_number=rx.prescription_number,
        prescribed_by=rx.prescribed_by,
        prescriber_license=rx.prescriber_license,
        prescription_type=rx.prescription_type,
        status=rx.status,
        diagnosis_code=rx.diagnosis_code,
        diagnosis_description=rx.diagnosis_description,
        clinical_notes=rx.clinical_notes,
        prescribed_at=_iso(rx.prescribed_at),
        valid_until=_iso(rx.valid_until),
        refills_allowed=rx.refills_allowed,
        refills_used=rx.refills_used,
        is_stat=bool(rx.is_stat),
        is_emergency=bool(rx.is_emergency),
    )


def _prescription_item_response(item: Any) -> PrescriptionItemResponse:
    return PrescriptionItemResponse(
        id=str(item.prescription_item_id),
        prescription_id=str(item.prescription.prescription_id) if item.prescription else "",
        drug_catalog_id=str(item.drug.drug_id) if item.drug else "",
        drug_name=item.drug_name,
        dosage=item.dosage,
        frequency=item.frequency,
        route=item.route,
        duration=item.duration,
        quantity=item.quantity,
        quantity_unit=item.quantity_unit,
        refill_quantity=item.refill_quantity,
        instructions=item.instructions,
        patient_education=item.patient_education,
        is_substitution_allowed=bool(item.is_substitution_allowed),
        status=item.status,
    )


def _dispense_record_response(record: Any, svc: Any) -> DispenseRecordResponse:
    drug = svc.get_drug(record.drug_id)
    batch = svc.get_batch(record.batch_id) if record.batch_id else None
    rx = svc.get_prescription(record.prescription_id) if record.prescription_id else None
    return DispenseRecordResponse(
        id=record.id,
        prescription_id=str(rx.prescription_id) if rx else None,
        patient_id=record.patient_id,
        drug_catalog_id=str(drug.drug_id) if drug else "",
        batch_id=str(batch.batch_id) if batch else None,
        dispense_number=record.dispense_number,
        dispensed_by=record.dispensed_by,
        verified_by=record.verified_by,
        dispensed_at=_iso(record.dispensed_at),
        quantity_dispensed=record.quantity_dispensed,
        quantity_unit=record.quantity_unit,
        days_supply=record.days_supply,
        is_verified=bool(record.is_verified),
        is_counselled=bool(record.is_counselled),
        instructions=record.instructions,
    )


def _stock_level_response(stock: Any, svc: Any) -> StockLevelResponse:
    drug = svc.get_drug(stock.drug_id)
    batch = stock.batch
    return StockLevelResponse(
        id=stock.id,
        drug_catalog_id=str(drug.drug_id) if drug else "",
        batch_id=str(batch.batch_id) if batch else None,
        warehouse_id=stock.warehouse_id,
        store_id=stock.store_id,
        quantity=stock.quantity_on_hand,
        reserved_quantity=stock.quantity_reserved or 0,
        available_quantity=stock.quantity_available,
        reorder_point=stock.reorder_point,
        reorder_quantity=stock.reorder_quantity,
        max_level=stock.maximum_level,
        unit=stock.unit,
        location=stock.location,
        last_count_date=_iso(stock.last_counted_at),
    )


def _movement_response(movement: Any, svc: Any) -> MovementResponse:
    drug = svc.get_drug(movement.drug_id)
    batch = svc.get_batch(movement.batch_id) if movement.batch_id else None
    return MovementResponse(
        id=movement.id,
        drug_catalog_id=str(drug.drug_id) if drug else "",
        batch_id=str(batch.batch_id) if batch else None,
        movement_type=movement.movement_type,
        quantity=movement.quantity,
        unit=movement.unit,
        reference_type=movement.reference_type,
        reference_id=movement.reference_id,
        reason=movement.reason,
        performed_by=movement.performed_by,
        movement_date=movement.performed_at.isoformat(),
        notes=movement.notes,
    )


def _transfer_response(transfer: Any) -> TransferResponse:
    return TransferResponse(
        id=str(transfer.transfer_id),
        transfer_number=transfer.transfer_number,
        from_warehouse_id=transfer.from_warehouse_id,
        to_warehouse_id=transfer.to_warehouse_id,
        from_store_id=transfer.from_store_id,
        to_store_id=transfer.to_store_id,
        transfer_type=transfer.transfer_type,
        status=transfer.status,
        requested_by=transfer.requested_by,
        approved_by=transfer.approved_by,
        dispatch_date=_iso(transfer.dispatched_at),
        received_date=_iso(transfer.received_at),
        notes=transfer.notes,
    )


def _recall_response(recall: Any, svc: Any) -> RecallResponse:
    drug = svc.get_drug(recall.drug_id)
    batch = svc.get_batch(recall.batch_id) if recall.batch_id else None
    return RecallResponse(
        id=recall.id,
        drug_catalog_id=str(drug.drug_id) if drug else "",
        batch_id=str(batch.batch_id) if batch else None,
        recall_number=recall.recall_number,
        recall_reason=recall.recall_reason,
        recall_source=recall.recall_source,
        initiated_at=recall.initiated_at.isoformat(),
        severity=recall.severity,
        status=recall.status,
        actions_taken=recall.actions_taken,
        notes=recall.notes,
    )


# ── Helpers ────────────────────────────────────────────────────────────────────


def _get_pharmacy_service(db: Session, user) -> PharmacyService:
    return PharmacyService(db=db, user_id=user.id, lab_id=user.lab_id)


def _get_or_404(db: Session, model, id: str, detail: str = "Not found"):
    obj = db.query(model).filter(model.id == id, not model.is_deleted).first()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
    return obj


def _run_dispense_transition(
    *,
    queue_id: str,
    operation: str,
    transition: Callable[[PharmacyService, str, int], object | None],
    db: Session,
    user,
    if_match: str | None,
    idempotency_key: str | None,
):
    """Execute one queue transition with durable idempotency and audit evidence."""
    svc = _get_pharmacy_service(db, user)
    entry = svc.get_dispense_queue_entry(queue_id, for_update=True)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"Queue entry not found: {queue_id}")
    guard = ClinicalCommandGuard(
        db,
        actor_user_id=user.id,
        lab_id=user.lab_id,
        actor_role=user.role,
    )
    state_before = entry.status.value if hasattr(entry.status, "value") else str(entry.status)
    version_before = entry.version
    guard.require_expected_version(if_match, current_version=version_before, resource_name="dispense queue entry")
    key = guard.require_idempotency_key(idempotency_key)
    receipt = guard.claim(
        operation=operation,
        resource_type="pharmacy_dispense_queue",
        resource_id=queue_id,
        idempotency_key=key,
        payload={"if_match": if_match},
    )
    try:
        updated = transition(svc, queue_id, version_before)
        if updated is None:
            raise HTTPException(status_code=404, detail=f"Queue entry not found: {queue_id}")
        state_after = updated.status.value if hasattr(updated.status, "value") else str(updated.status)
        guard.complete(
            receipt,
            resource_type="pharmacy_dispense_queue",
            resource_id=queue_id,
            state_before=state_before,
            state_after=state_after,
            version_before=version_before,
            version_after=updated.version,
        )
        db.commit()
    except (HTTPException, PharmacyWorkflowError) as exc:
        db.rollback()
        guard.reject(
            operation=operation,
            resource_type="pharmacy_dispense_queue",
            resource_id=queue_id,
            state_before=state_before,
            version_before=version_before,
            reason=str(getattr(exc, "detail", exc)),
        )
        db.commit()
        if isinstance(exc, HTTPException):
            raise
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return updated


# ── Drug Catalog Routes ────────────────────────────────────────────────────────


@router.get("/drugs", response_model=DrugCatalogListResponse)
async def list_drugs(
    query: str | None = Query(None),
    category: str | None = Query(None),
    atc_code: str | None = Query(None),
    therapeutic_class: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    svc = _get_pharmacy_service(db, user)
    items, total = svc.search_drugs(query, category, atc_code, therapeutic_class, skip, limit)
    return DrugCatalogListResponse(items=items, total=total, skip=skip, limit=limit)


@router.post("/drugs", response_model=DrugCatalogResponse, status_code=status.HTTP_201_CREATED)
async def create_drug(
    data: DrugCatalogCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    svc = _get_pharmacy_service(db, user)
    return svc.create_drug(data.model_dump(exclude_none=True))


@router.get("/drugs/{drug_id}", response_model=DrugCatalogResponse)
async def get_drug(
    drug_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    svc = _get_pharmacy_service(db, user)
    drug = svc.get_drug(drug_id)
    if not drug:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Drug not found: {drug_id}")
    return drug


@router.put("/drugs/{drug_id}", response_model=DrugCatalogResponse)
async def update_drug(
    drug_id: str,
    data: DrugCatalogUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    svc = _get_pharmacy_service(db, user)
    drug = svc.update_drug(drug_id, data.model_dump(exclude_none=True))
    if not drug:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Drug not found: {drug_id}")
    return drug


@router.delete("/drugs/{drug_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_drug(
    drug_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    svc = _get_pharmacy_service(db, user)
    if not svc.delete_drug(drug_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Drug not found: {drug_id}")


@router.get("/drugs/search", response_model=DrugCatalogListResponse)
async def search_drugs(
    name: str | None = Query(None),
    code: str | None = Query(None),
    category: str | None = Query(None),
    atc_code: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    query = name or code
    svc = _get_pharmacy_service(db, user)
    items, total = svc.search_drugs(query, category, atc_code, None, skip, limit)
    return DrugCatalogListResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/drugs/atc/{atc_code}", response_model=DrugCatalogListResponse)
async def get_drugs_by_atc(
    atc_code: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    svc = _get_pharmacy_service(db, user)
    items = svc.get_drugs_by_atc(atc_code)
    total = len(items)
    items = items[skip:skip + limit]
    return DrugCatalogListResponse(items=items, total=total, skip=skip, limit=limit)


@router.post("/drugs/{drug_id}/batches", response_model=DrugBatchResponse, status_code=status.HTTP_201_CREATED)
async def create_batch(
    drug_id: str,
    data: DrugBatchCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    svc = _get_pharmacy_service(db, user)
    drug = svc.get_drug_by_public_id(drug_id)
    if not drug:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Drug not found: {drug_id}")
    payload = data.model_dump(exclude_none=True)
    # `cost_price` is the wire name for the physical `unit_cost` column.
    if "cost_price" in payload:
        payload["unit_cost"] = payload.pop("cost_price")
    batch = svc.create_batch(drug.id, payload)
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Drug not found: {drug_id}")
    db.commit()
    db.refresh(batch)
    return _drug_batch_response(batch)


@router.get("/drugs/{drug_id}/batches", response_model=list[DrugBatchResponse])
async def list_batches(
    drug_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    svc = _get_pharmacy_service(db, user)
    drug = svc.get_drug_by_public_id(drug_id)
    if not drug:
        return []
    return [_drug_batch_response(b) for b in svc.get_batches(drug.id)]


@router.get("/batches/{batch_id}", response_model=DrugBatchResponse)
async def get_batch(
    batch_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    svc = _get_pharmacy_service(db, user)
    batch = svc.get_batch_by_public_id(batch_id)
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Batch not found: {batch_id}")
    return _drug_batch_response(batch)


@router.get("/batches/expiring", response_model=list[DrugBatchResponse])
async def get_expiring_batches(
    days: int = Query(90, ge=1, le=365),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    svc = _get_pharmacy_service(db, user)
    return [_drug_batch_response(b) for b in svc.get_expiring_batches(days)]


@router.get("/suppliers", response_model=list[SupplierResponse])
async def list_suppliers(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    svc = _get_pharmacy_service(db, user)
    return svc.list_suppliers()


@router.post("/suppliers", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
async def create_supplier(
    data: SupplierCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    svc = _get_pharmacy_service(db, user)
    return svc.create_supplier(data.model_dump(exclude_none=True))


# ── Prescription Routes ────────────────────────────────────────────────────────


@router.post("/prescriptions", response_model=PrescriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_prescription(
    data: PrescriptionCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    svc = _get_pharmacy_service(db, user)
    rx = svc.create_prescription(data.model_dump(exclude_none=True))
    db.commit()
    db.refresh(rx)
    return _prescription_response(rx)


@router.get("/prescriptions", response_model=list[PrescriptionResponse])
async def list_prescriptions(
    status_filter: str | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    _get_pharmacy_service(db, user)
    # Previously `~~Prescription.is_deleted`: the double negation cancels, so
    # this listed the soft-deleted prescriptions and only those.
    q = db.query(Prescription).filter(~Prescription.is_deleted)
    if user.lab_id:
        q = q.filter(Prescription.lab_id == user.lab_id)
    if status_filter:
        q = q.filter(Prescription.status == status_filter)
    rows = q.order_by(Prescription.created_at.desc()).offset(skip).limit(limit).all()
    return [_prescription_response(rx) for rx in rows]


@router.get("/prescriptions/{rx_id}", response_model=PrescriptionResponse)
async def get_prescription(
    rx_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    svc = _get_pharmacy_service(db, user)
    rx = svc.get_prescription_by_public_id(rx_id)
    if not rx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Prescription not found: {rx_id}")
    return _prescription_response(rx)


@router.put("/prescriptions/{rx_id}/status", response_model=PrescriptionResponse)
async def update_prescription_status(
    rx_id: str,
    status_data: dict[str, str],
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    svc = _get_pharmacy_service(db, user)
    new_status = status_data.get("status")
    if not new_status:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="status field required")
    try:
        parsed = PrescriptionStatus(new_status)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Invalid status: {new_status}") from e
    existing = svc.get_prescription_by_public_id(rx_id)
    rx = svc.update_prescription_status(existing.id, parsed) if existing else None
    if not rx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Prescription not found: {rx_id}")
    db.commit()
    db.refresh(rx)
    return _prescription_response(rx)


@router.post("/prescriptions/{rx_id}/renew", response_model=PrescriptionResponse)
async def renew_prescription(
    rx_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    svc = _get_pharmacy_service(db, user)
    existing = svc.get_prescription_by_public_id(rx_id)
    renewal = svc.renew_prescription(existing.id) if existing else None
    if not renewal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Prescription not found: {rx_id}")
    db.commit()
    db.refresh(renewal)
    return _prescription_response(renewal)


@router.post("/prescriptions/{rx_id}/cancel", response_model=PrescriptionResponse)
async def cancel_prescription(
    rx_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    svc = _get_pharmacy_service(db, user)
    existing = svc.get_prescription_by_public_id(rx_id)
    rx = svc.cancel_prescription(existing.id) if existing else None
    if not rx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Prescription not found: {rx_id}")
    db.commit()
    db.refresh(rx)
    return _prescription_response(rx)


@router.post("/prescriptions/{rx_id}/items", response_model=PrescriptionItemResponse, status_code=status.HTTP_201_CREATED)
async def add_prescription_item(
    rx_id: str,
    data: PrescriptionItemCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    svc = _get_pharmacy_service(db, user)
    rx = svc.get_prescription_by_public_id(rx_id)
    if not rx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Prescription not found: {rx_id}")
    payload = data.model_dump(exclude_none=True)
    drug = svc.get_drug_by_public_id(str(payload.pop("drug_catalog_id", "")))
    if not drug:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Drug not found")
    payload["drug_id"] = drug.id
    payload.setdefault("drug_name", drug.drug_name)
    item = svc.add_prescription_item(rx.id, payload)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Prescription not found: {rx_id}")
    db.commit()
    db.refresh(item)
    return _prescription_item_response(item)


@router.put("/prescriptions/{rx_id}/items/{item_id}/substitute", response_model=PrescriptionItemResponse)
async def substitute_prescription_item(
    rx_id: str,
    item_id: str,
    data: dict[str, str],
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    new_drug_id = data.get("drug_catalog_id")
    if not new_drug_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="drug_catalog_id required")
    svc = _get_pharmacy_service(db, user)
    rx = svc.get_prescription_by_public_id(rx_id)
    drug = svc.get_drug_by_public_id(new_drug_id)
    if not rx or not drug:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prescription item not found")
    existing = svc.get_prescription_item_by_public_id(item_id)
    item = (
        svc.substitute_prescription_item(rx.id, existing.id, drug.id) if existing else None
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prescription item not found")
    db.commit()
    db.refresh(item)
    return _prescription_item_response(item)


# ── Dispensing Routes ──────────────────────────────────────────────────────────


@router.get("/dispense-queue")
async def get_dispense_queue(
    status_filter: str | None = Query(None, alias="status"),
    priority: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    svc = _get_pharmacy_service(db, user)
    items, _total = svc.get_dispense_queue(status_filter, priority, skip, limit)
    return items


@router.post("/dispense-queue/{queue_id}/prepare")
async def prepare_dispense(
    queue_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    if_match: str | None = Header(None, alias="If-Match"),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
):
    entry = _run_dispense_transition(
        queue_id=queue_id,
        operation="pharmacy.dispense.prepare",
        transition=lambda svc, qid, version: svc.prepare_dispense(qid, expected_version=version),
        db=db,
        user=user,
        if_match=if_match,
        idempotency_key=idempotency_key,
    )
    return {"status": "prepared", "id": queue_id, "version": entry.version}


@router.post("/dispense-queue/{queue_id}/verify")
async def verify_dispense(
    queue_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    if_match: str | None = Header(None, alias="If-Match"),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
):
    entry = _run_dispense_transition(
        queue_id=queue_id,
        operation="pharmacy.dispense.verify",
        transition=lambda svc, qid, version: svc.verify_dispense(qid, expected_version=version),
        db=db,
        user=user,
        if_match=if_match,
        idempotency_key=idempotency_key,
    )
    return {"status": "verified", "id": queue_id, "version": entry.version}


@router.post("/dispense-queue/{queue_id}/dispense")
async def complete_dispense(
    queue_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    if_match: str | None = Header(None, alias="If-Match"),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
):
    entry = _run_dispense_transition(
        queue_id=queue_id,
        operation="pharmacy.dispense.complete",
        transition=lambda svc, qid, version: svc.complete_dispense(qid, expected_version=version),
        db=db,
        user=user,
        if_match=if_match,
        idempotency_key=idempotency_key,
    )
    return {"status": "dispensed", "id": queue_id, "version": entry.version}


@router.post("/dispense-queue/{queue_id}/partial")
async def partial_dispense(
    queue_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    if_match: str | None = Header(None, alias="If-Match"),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
):
    entry = _run_dispense_transition(
        queue_id=queue_id,
        operation="pharmacy.dispense.partial",
        transition=lambda svc, qid, version: svc.partial_dispense(qid, expected_version=version),
        db=db,
        user=user,
        if_match=if_match,
        idempotency_key=idempotency_key,
    )
    return {"status": "partial", "id": queue_id, "version": entry.version}


@router.post("/dispense-queue/{queue_id}/cancel")
async def cancel_dispense(
    queue_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    if_match: str | None = Header(None, alias="If-Match"),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
):
    entry = _run_dispense_transition(
        queue_id=queue_id,
        operation="pharmacy.dispense.cancel",
        transition=lambda svc, qid, version: svc.cancel_dispense(qid, expected_version=version),
        db=db,
        user=user,
        if_match=if_match,
        idempotency_key=idempotency_key,
    )
    return {"status": "cancelled", "id": queue_id, "version": entry.version}


@router.post("/dispense/dispense-record", response_model=DispenseRecordResponse, status_code=status.HTTP_201_CREATED)
async def create_dispense_record(
    data: DispenseRecordCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    if_match: str | None = Header(None, alias="If-Match"),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
):
    """Create a manually recorded dispense only under locked, independently verified stock."""
    svc = _get_pharmacy_service(db, user)
    drug = svc.get_drug_by_public_id(data.drug_catalog_id)
    batch = svc.get_batch_by_public_id(data.batch_id)
    stock = None
    if drug is not None and batch is not None:
        stock = db.query(StockLevel).filter(
            StockLevel.lab_id == user.lab_id,
            StockLevel.batch_id == batch.id,
            StockLevel.drug_id == drug.id,
            ~StockLevel.is_deleted,
        ).with_for_update().first()
    if stock is None:
        raise HTTPException(status_code=404, detail="Stock record not found for the requested medication batch")
    guard = ClinicalCommandGuard(
        db,
        actor_user_id=user.id,
        lab_id=user.lab_id,
        actor_role=user.role,
    )
    version_before = stock.version
    quantity_before = stock.quantity_available
    guard.require_expected_version(if_match, current_version=version_before, resource_name="pharmacy stock level")
    key = guard.require_idempotency_key(idempotency_key)
    receipt = guard.claim(
        operation="pharmacy.dispense.record",
        resource_type="pharmacy_stock_level",
        resource_id=stock.id,
        idempotency_key=key,
        payload=data.model_dump(mode="json"),
    )
    try:
        record = svc.create_dispense_record(data.model_dump(exclude_none=True))
        db.flush()
        guard.complete(
            receipt,
            resource_type="pharmacy_stock_level",
            resource_id=stock.id,
            state_before=f"available={quantity_before}",
            state_after=f"available={stock.quantity_available}",
            version_before=version_before,
            version_after=stock.version,
        )
        db.commit()
    except PharmacyWorkflowError as exc:
        db.rollback()
        guard.reject(
            operation="pharmacy.dispense.record",
            resource_type="pharmacy_stock_level",
            resource_id=stock.id,
            state_before=f"available={quantity_before}",
            version_before=version_before,
            reason=str(exc),
        )
        db.commit()
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    db.refresh(record)
    return record


@router.get("/dispense/dispense-records/{patient_id}", response_model=list[DispenseRecordResponse])
async def get_dispense_records(
    patient_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    svc = _get_pharmacy_service(db, user)
    return [_dispense_record_response(r, svc) for r in svc.get_dispense_records(patient_id)]


# ── Clinical Pharmacy Routes ───────────────────────────────────────────────────


@router.post("/clinical/interactions/check", response_model=InteractionCheckResponse)
async def check_interactions(
    data: InteractionCheckRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    from app.pharmacy.clinical import DrugInteractionEngine

    engine = DrugInteractionEngine(db, user.lab_id)
    interactions = engine.check_multiple_drugs(data.drug_codes)
    severe_count = sum(1 for i in interactions if i.get("severity") in ("contraindicated", "major"))
    return InteractionCheckResponse(interactions=interactions, total=len(interactions), severe_count=severe_count)


@router.post("/clinical/contraindications/check")
async def check_contraindications(
    data: ContraindicationCheckRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    from app.pharmacy.clinical import ContraindicationEngine

    engine = ContraindicationEngine(db, user.lab_id)
    results = engine.check_patient_conditions(data.drug_code, data.condition_codes)
    return {"contraindications": results, "total": len(results)}


@router.post("/clinical/allergies/check")
async def check_allergies(
    data: AllergyCheckRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    from app.pharmacy.clinical import AllergyEngine

    engine = AllergyEngine(db, user.lab_id)
    results = engine.check_patient_allergies(data.drug_code, data.allergen_codes)
    return {"reactions": results, "total": len(results)}


@router.post("/clinical/dose/calculate")
async def calculate_dose(
    data: DoseCalculateRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    from app.pharmacy.clinical import DoseEngine

    engine = DoseEngine(db, user.lab_id)
    results = engine.calculate_dose(data.drug_code, data.indication_code, data.age_months, data.weight_kg)
    return {"dose_guidelines": results, "total": len(results)}


@router.post("/clinical/dose/renal-adjust")
async def renal_adjustment(
    data: RenalAdjustRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    from app.pharmacy.clinical import DoseEngine

    engine = DoseEngine(db, user.lab_id)
    return engine.calculate_renal_adjustment(data.drug_code, data.egfr, data.weight_kg)


@router.get("/clinical/guidelines")
async def list_guidelines(
    drug_code: str | None = Query(None),
    condition_code: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    from app.pharmacy.clinical import ClinicalGuidelineService

    svc = ClinicalGuidelineService(db, user.lab_id)
    items, total = svc.get_guidelines(drug_code, condition_code, None, skip, limit)
    return {"guidelines": items, "total": total, "skip": skip, "limit": limit}


@router.post("/clinical/polypharmacy/check")
async def check_polypharmacy(
    data: PolypharmacyCheckRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    from app.pharmacy.clinical import PolypharmacyChecker

    checker = PolypharmacyChecker(db, user.lab_id)
    return checker.check_polypharmacy(data.drug_codes)


# ── Inventory Routes ────────────────────────────────────────────────────────────


@router.get("/inventory/stock-levels")
async def get_stock_levels(
    warehouse_id: str | None = Query(None),
    store_id: str | None = Query(None),
    drug_id: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    svc = _get_pharmacy_service(db, user)
    items, total = svc.get_stock_levels(warehouse_id, store_id, drug_id, skip, limit)
    return {
        "items": [_stock_level_response(i, svc) for i in items],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/inventory/stock-levels/alerts")
async def get_stock_alerts(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    svc = _get_pharmacy_service(db, user)
    return svc.get_stock_alerts()


@router.post("/inventory/stock-levels/adjust")
async def adjust_stock(
    data: StockAdjustRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    svc = _get_pharmacy_service(db, user)
    stock = svc.adjust_stock(data.model_dump(exclude_none=True))
    if stock is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medication not found")
    db.commit()
    db.refresh(stock)
    return {"status": "adjusted", "id": stock.id, "new_quantity": stock.quantity_on_hand}


@router.get("/inventory/movements")
async def list_movements(
    drug_id: str | None = Query(None),
    movement_type: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    svc = _get_pharmacy_service(db, user)
    items, total = svc.get_movements(drug_id, movement_type, skip, limit)
    return {
        "items": [_movement_response(m, svc) for m in items],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.post("/inventory/movements", response_model=MovementResponse, status_code=status.HTTP_201_CREATED)
async def create_movement(
    data: MovementCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    svc = _get_pharmacy_service(db, user)
    movement = svc.create_movement(data.model_dump(exclude_none=True))
    db.commit()
    db.refresh(movement)
    return _movement_response(movement, svc)


@router.get("/inventory/transfers")
async def list_transfers(
    status_filter: str | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    svc = _get_pharmacy_service(db, user)
    items, total = svc.get_transfers(status_filter, skip, limit)
    return {
        "items": [_transfer_response(t) for t in items],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.post("/inventory/transfers", response_model=TransferResponse, status_code=status.HTTP_201_CREATED)
async def create_transfer(
    data: TransferCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    svc = _get_pharmacy_service(db, user)
    transfer = svc.create_transfer(data.model_dump(exclude_none=True))
    db.commit()
    db.refresh(transfer)
    return _transfer_response(transfer)


@router.put("/inventory/transfers/{transfer_id}/approve")
async def approve_transfer(
    transfer_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    svc = _get_pharmacy_service(db, user)
    transfer = svc.approve_transfer(transfer_id)
    if not transfer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Transfer not found: {transfer_id}")
    return {"status": "approved", "id": transfer_id}


@router.put("/inventory/transfers/{transfer_id}/receive")
async def receive_transfer(
    transfer_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    svc = _get_pharmacy_service(db, user)
    transfer = svc.receive_transfer(transfer_id)
    if not transfer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Transfer not found: {transfer_id}")
    return {"status": "received", "id": transfer_id}


@router.post("/inventory/returns", status_code=status.HTTP_201_CREATED)
async def create_return(
    data: ReturnCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    svc = _get_pharmacy_service(db, user)
    ret = svc.create_return(data.model_dump(exclude_none=True))
    db.commit()
    return {"status": "returned", "id": ret.id}


@router.post("/inventory/waste", status_code=status.HTTP_201_CREATED)
async def create_waste(
    data: WasteCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    svc = _get_pharmacy_service(db, user)
    waste = svc.create_waste(data.model_dump(exclude_none=True))
    db.commit()
    return {"status": "wasted", "id": waste.id}


@router.get("/inventory/recalls")
async def list_recalls(
    status_filter: str | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    svc = _get_pharmacy_service(db, user)
    items, total = svc.list_recalls(status_filter, skip, limit)
    return {
        "items": [_recall_response(r, svc) for r in items],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.post("/inventory/recalls", response_model=RecallResponse, status_code=status.HTTP_201_CREATED)
async def create_recall(
    data: RecallCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    svc = _get_pharmacy_service(db, user)
    recall = svc.create_recall(data.model_dump(exclude_none=True))
    db.commit()
    db.refresh(recall)
    return _recall_response(recall, svc)


@router.get("/inventory/forecast/{drug_id}")
async def get_forecast(
    drug_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    svc = _get_pharmacy_service(db, user)
    forecasts = svc.get_inventory_forecast(drug_id)
    return {"drug_id": drug_id, "forecasts": forecasts}


@router.post("/inventory/reorder")
async def generate_reorder(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    svc = _get_pharmacy_service(db, user)
    recommendations = svc.generate_reorder_recommendations()
    return {"recommendations": recommendations, "total": len(recommendations)}


# ── Dashboard Routes ────────────────────────────────────────────────────────────


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    svc = _get_pharmacy_service(db, user)
    return DashboardResponse(**svc.get_dashboard())


@router.get("/dashboard/queue-summary")
async def get_queue_summary(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    svc = _get_pharmacy_service(db, user)
    return svc.get_queue_summary()


@router.get("/dashboard/stock-alerts")
async def get_stock_alerts_dashboard(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    svc = _get_pharmacy_service(db, user)
    return svc.get_stock_alerts()


@router.get("/dashboard/expiry-alerts")
async def get_expiry_alerts(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    svc = _get_pharmacy_service(db, user)
    return svc.get_expiry_alerts()


# ── Pharmacy POS contracts and routes ──────────────────────────────────────────


class POSSaleLineCreate(BaseModel):
    # Public identifiers: drug_catalog_id is the drug's drug_id (UUID4) and
    # substitution_request_id is the request's public identity. batch_id is
    # still a Generation B batch key until M4.
    drug_catalog_id: str | None = None
    barcode: str | None = None
    substitution_request_id: str | None = None
    batch_id: str | None = None
    prescription_id: str | None = None
    quantity: int
    quantity_unit: str = "unit"
    unit_price: float | None = None
    discount: float = 0
    days_supply: int | None = None
    dosage_instruction: str | None = None
    route: str | None = None
    frequency: str | None = None


class POSSaleCreate(BaseModel):
    patient_id: str | None = None
    citizen_id: str | None = None
    billing_patient_id: int | None = None
    encounter_id: str | None = None
    encounter_ref: str | None = None
    currency: str = "IQD"
    payment_method: str = "synthetic_settlement"
    covered_amount: float = 0
    issue_invoice: bool = True
    idempotency_key: str | None = None
    lines: list[POSSaleLineCreate]


class POSSaleLineResponse(BaseModel):
    """Wire shape is unchanged from Generation B: every identifier is a string.

    What changed is which value each one carries. ``id`` is the sale line's
    public ``sale_line_id`` and ``drug_catalog_id`` is the drug's public
    ``drug_id``; the internal Integer keys behind them are never published
    (CANONICAL_DRUG_CONTRACT §3, §8). ``batch_id`` still carries the Generation
    B batch key because batch identity is not reconciled until M4.
    """

    id: str
    line_number: int
    drug_catalog_id: str
    batch_id: str
    medication_dispense_id: str | None
    barcode: str | None
    medication_name: str
    medication_name_ar: str | None
    quantity: int
    quantity_unit: str | None
    lot_number: str | None
    expiry_date: date | None
    unit_price: float
    unit_cost: float
    discount: float
    line_total: float
    line_cost: float

    model_config = ConfigDict(from_attributes=True)


class POSSaleResponse(BaseModel):
    """``id`` is the sale's public ``sale_id`` (UUID4); ``sale_number`` remains
    the mutable business code and is never an identity (contract §4)."""

    id: str
    sale_number: str
    patient_id: str | None
    citizen_id: str | None
    billing_patient_id: int | None
    billing_invoice_id: int | None
    status: str
    currency: str
    subtotal: float
    discount: float
    total_amount: float
    cost_amount: float
    gross_profit: float
    payment_status: str
    payment_method: str
    sold_at: str
    lines: list[POSSaleLineResponse]

    model_config = ConfigDict(from_attributes=True)


def _pos_sale_line_response(line: Any) -> POSSaleLineResponse:
    return POSSaleLineResponse(
        id=str(line.sale_line_id),
        line_number=line.line_number,
        # The drug's public identity, not the internal foreign key.
        drug_catalog_id=str(line.drug.drug_id),
        batch_id=line.batch_id,
        medication_dispense_id=line.medication_dispense_id,
        barcode=line.barcode,
        medication_name=line.medication_name,
        medication_name_ar=line.medication_name_ar,
        quantity=line.quantity,
        quantity_unit=line.quantity_unit,
        lot_number=line.lot_number,
        expiry_date=line.expiry_date,
        unit_price=float(line.unit_price),
        unit_cost=float(line.unit_cost),
        discount=float(line.discount),
        line_total=float(line.line_total),
        line_cost=float(line.line_cost),
    )


def _pos_sale_response(sale: Any) -> POSSaleResponse:
    return POSSaleResponse(
        id=str(sale.sale_id),
        sale_number=sale.sale_number,
        patient_id=sale.patient_id,
        citizen_id=sale.citizen_id,
        billing_patient_id=sale.billing_patient_id,
        billing_invoice_id=sale.billing_invoice_id,
        status=sale.status,
        currency=sale.currency,
        subtotal=float(sale.subtotal),
        discount=float(sale.discount),
        total_amount=float(sale.total_amount),
        cost_amount=float(sale.cost_amount),
        gross_profit=float(sale.gross_profit),
        payment_status=sale.payment_status,
        payment_method=sale.payment_method,
        sold_at=sale.sold_at.isoformat() if sale.sold_at is not None else "",
        lines=[_pos_sale_line_response(line) for line in sale.lines],
    )


class SubstitutionRequestResponse(BaseModel):
    """Public shape of a substitution request.

    Replaces the previous ``to_dict()`` passthrough, which published every
    column verbatim. After M3 those columns are internal Integer keys, and a
    passthrough would both leak them and change the wire types.
    """

    id: str
    rule_id: str
    original_drug_catalog_id: str
    alternative_drug_catalog_id: str
    prescription_id: str | None
    patient_id: str | None
    citizen_id: str | None
    quantity: int
    status: str
    reason: str
    approval_level: str
    approved_by: str | None
    approved_at: str | None
    patient_consent: bool
    patient_notified_at: str | None
    consumed_sale_id: str | None


def _substitution_request_response(
    request: Any, service: Any
) -> SubstitutionRequestResponse:
    original = service.get_drug(request.original_drug_catalog_id)
    alternative = service.get_drug(request.alternative_drug_catalog_id)
    return SubstitutionRequestResponse(
        id=str(request.substitution_request_id),
        rule_id=str(request.rule.substitution_rule_id),
        original_drug_catalog_id=str(original.drug_id) if original else "",
        alternative_drug_catalog_id=str(alternative.drug_id) if alternative else "",
        # Group B: still the Generation B prescription key until M4.
        prescription_id=request.prescription_id,
        patient_id=request.patient_id,
        citizen_id=request.citizen_id,
        quantity=request.quantity,
        status=request.status,
        reason=request.reason,
        approval_level=request.approval_level,
        approved_by=request.approved_by,
        approved_at=request.approved_at.isoformat() if request.approved_at else None,
        patient_consent=bool(request.patient_consent),
        patient_notified_at=(
            request.patient_notified_at.isoformat() if request.patient_notified_at else None
        ),
        # The consuming sale's public identity, never its internal key.
        consumed_sale_id=(
            str(request.consumed_sale.sale_id) if request.consumed_sale is not None else None
        ),
    )


@router.post("/pos/sales", response_model=POSSaleResponse, status_code=status.HTTP_201_CREATED)
async def create_pos_sale(
    data: POSSaleCreate,
    request: Request,
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    user: Any = Depends(require_institutional_permission("payments:write")),
) -> POSSaleResponse:
    payload = data.model_dump(exclude_none=True)
    if idempotency_key and not payload.get("idempotency_key"):
        payload["idempotency_key"] = idempotency_key
    try:
        sale = _get_pharmacy_service(db, user).create_pos_sale(
            payload,
            request_id=request.headers.get("X-Request-ID"),
        )
        db.commit()
        db.refresh(sale)
        return _pos_sale_response(sale)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception:
        db.rollback()
        raise


@router.get("/pos/sales", response_model=list[POSSaleResponse])
async def list_pos_sales(
    citizen_id: str | None = Query(None, max_length=26),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user: Any = Depends(require_institutional_permission("payments:read")),
) -> list[POSSaleResponse]:
    sales = _get_pharmacy_service(db, user).list_pos_sales(citizen_id=citizen_id, skip=skip, limit=limit)
    return [_pos_sale_response(sale) for sale in sales]


@router.get("/pos/summary")
async def get_pos_summary(
    days: int = Query(30, ge=1, le=3650),
    db: Session = Depends(get_db),
    user: Any = Depends(require_institutional_permission("payments:read")),
) -> dict[str, Any]:
    try:
        summary = _get_pharmacy_service(db, user).get_pos_summary(days)
        return dict(summary)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/pos/sales/{sale_id}", response_model=POSSaleResponse)
async def get_pos_sale(
    sale_id: str,
    db: Session = Depends(get_db),
    user: Any = Depends(require_institutional_permission("payments:read")),
) -> POSSaleResponse:
    sale = _get_pharmacy_service(db, user).get_pos_sale(sale_id)
    if sale is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found")
    return _pos_sale_response(sale)


# ── Drug substitution routes ────────────────────────────────────────────────────


class SubstitutionRequestCreate(BaseModel):
    # The rule's public substitution_rule_id (UUID4), never its internal key.
    rule_id: str
    prescription_id: str | None = None
    patient_id: str | None = None
    citizen_id: str | None = None
    quantity: int = Field(default=1, ge=1, le=10000)
    reason: str = "original medication unavailable"
    patient_consent: bool = False
    patient_notified: bool = False


class SubstitutionRejectRequest(BaseModel):
    reason: str


@router.get("/substitutions/candidates")
async def list_substitution_candidates(
    # A drug is named publicly by drug_id (UUID4, 36 characters), never by the
    # internal Integer key or the retired 26-character Generation B key.
    original_drug_id: str = Query(..., min_length=1, max_length=36),
    quantity: int = Query(1, ge=1, le=10000),
    db: Session = Depends(get_db),
    user: Any = Depends(require_institutional_permission("lab:read")),
) -> list[dict[str, Any]]:
    try:
        return _get_pharmacy_service(db, user).list_substitution_candidates_by_public_id(
            original_drug_id, quantity
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/substitutions/requests", status_code=status.HTTP_201_CREATED)
async def create_substitution_request(
    data: SubstitutionRequestCreate,
    db: Session = Depends(get_db),
    user: Any = Depends(require_institutional_permission("lab:manage")),
) -> SubstitutionRequestResponse:
    service = _get_pharmacy_service(db, user)
    try:
        request = service.create_substitution_request(data.model_dump())
        db.commit()
        db.refresh(request)
        return _substitution_request_response(request, service)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/substitutions/requests/{request_id}/approve")
async def approve_substitution_request(
    request_id: str,
    db: Session = Depends(get_db),
    user: Any = Depends(require_institutional_permission("lab:manage")),
) -> SubstitutionRequestResponse:
    service = _get_pharmacy_service(db, user)
    try:
        request = service.approve_substitution(request_id)
        db.commit()
        db.refresh(request)
        return _substitution_request_response(request, service)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/substitutions/requests/{request_id}/reject")
async def reject_substitution_request(
    request_id: str,
    data: SubstitutionRejectRequest,
    db: Session = Depends(get_db),
    user: Any = Depends(require_institutional_permission("lab:manage")),
) -> SubstitutionRequestResponse:
    service = _get_pharmacy_service(db, user)
    try:
        request = service.reject_substitution(request_id, data.reason)
        db.commit()
        db.refresh(request)
        return _substitution_request_response(request, service)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

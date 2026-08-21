from __future__ import annotations

from collections.abc import Callable
from datetime import date
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
from app.pharmacy.services import (
    PharmacyAuthorizationBlocked,
    PharmacyService,
    PharmacyWorkflowError,
)
from app.security.dependencies import (
    get_current_user,
    require_institutional_permission,
    require_institutional_user,
)

router = APIRouter(
    prefix="/pharmacy",
    tags=["Pharmacy"],
    dependencies=[Depends(require_institutional_user)],
)


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
    manufacturer_batch: str | None = None
    expiry_date: date
    manufacturing_date: date | None = None
    quantity_initial: int = 0
    storage_condition: StorageCondition | None = None
    location: str | None = None
    supplier: str | None = None
    cost_price: float | None = None
    selling_price: float | None = None


class DrugBatchResponse(BaseModel):
    id: str
    drug_catalog_id: str
    batch_number: str
    manufacturer_batch: str | None
    expiry_date: str
    manufacturing_date: str | None
    quantity_initial: int
    quantity_remaining: int
    storage_condition: str | None
    location: str | None
    received_date: str | None
    supplier: str | None
    cost_price: float | None
    selling_price: float | None
    is_quarantined: bool

    model_config = ConfigDict(from_attributes=True)


class SupplierCreate(BaseModel):
    name: str
    name_ar: str | None = None
    code: str
    contact_person: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    license_number: str | None = None
    is_active: bool = True
    payment_terms: str | None = None


class SupplierResponse(BaseModel):
    id: str
    name: str
    name_ar: str | None
    code: str
    contact_person: str | None
    phone: str | None
    email: str | None
    address: str | None
    license_number: str | None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class PrescriptionCreate(BaseModel):
    patient_id: str
    encounter_id: str | None = None
    prescriber_id: str | None = None
    prescription_number: str
    intent: str = "order"
    priority: str = "routine"
    diagnosis: str | None = None
    diagnosis_code: str | None = None
    diagnosis_system: str | None = None
    valid_from: date | None = None
    valid_to: date | None = None
    dispense_interval: int | None = None
    substitution_allowed: bool = True
    note: str | None = None


class PrescriptionResponse(BaseModel):
    id: str
    patient_id: str
    encounter_id: str | None
    prescriber_id: str | None
    prescription_number: str
    status: str
    intent: str
    priority: str
    diagnosis: str | None
    diagnosis_code: str | None
    diagnosis_system: str | None
    authored_on: str | None
    valid_from: str | None
    valid_to: str | None
    substitution_allowed: bool
    note: str | None

    model_config = ConfigDict(from_attributes=True)


class PrescriptionItemCreate(BaseModel):
    drug_catalog_id: str | None = None
    medication_code: str | None = None
    medication_name: str
    strength_value: str | None = None
    strength_unit: str | None = None
    form: str | None = None
    route: str | None = None
    dose_quantity: str | None = None
    dose_unit: str | None = None
    frequency: str | None = None
    duration: int | None = None
    duration_unit: str | None = None
    quantity: int | None = None
    quantity_unit: str | None = None
    refills: int = 0
    instructions: str | None = None
    substitution_allowed: bool = True


class PrescriptionItemResponse(BaseModel):
    id: str
    prescription_id: str
    drug_catalog_id: str | None
    medication_code: str | None
    medication_name: str
    strength_value: str | None
    strength_unit: str | None
    form: str | None
    route: str | None
    dose_quantity: str | None
    dose_unit: str | None
    frequency: str | None
    duration: int | None
    duration_unit: str | None
    quantity: int | None
    quantity_unit: str | None
    refills: int
    refills_used: int
    instructions: str | None
    substitution_allowed: bool
    status: str

    model_config = ConfigDict(from_attributes=True)


class DispenseRecordCreate(BaseModel):
    prescription_id: str | None = None
    prescription_item_id: str | None = None
    patient_id: str
    drug_catalog_id: str
    dispensed_by: str | None = None
    verified_by: str | None = None
    quantity_dispensed: int
    quantity_unit: str | None = None
    days_supply: int | None = None
    batch_id: str | None = None
    lot_number: str | None = None
    expiry_date: date | None = None
    cost_price: float | None = None
    selling_price: float | None = None
    discount: float | None = None
    total_amount: float | None = None
    pharmacist_notes: str | None = None
    counseling_provided: bool = False


class DispenseRecordResponse(BaseModel):
    id: str
    prescription_id: str | None
    patient_id: str
    dispensed_by: str | None
    verified_by: str | None
    dispensed_at: str | None
    status: str
    quantity_dispensed: int
    quantity_unit: str | None
    days_supply: int | None
    batch_id: str | None
    lot_number: str | None
    expiry_date: str | None
    total_amount: float | None
    pharmacist_notes: str | None

    model_config = ConfigDict(from_attributes=True)


class StockLevelResponse(BaseModel):
    id: str
    drug_catalog_id: str
    batch_id: str | None
    warehouse_id: str | None
    store_id: str | None
    quantity: int
    reserved_quantity: int
    available_quantity: int
    reorder_point: int | None
    reorder_quantity: int | None
    max_level: int | None
    storage_condition: str | None
    last_count_date: str | None

    model_config = ConfigDict(from_attributes=True)


class StockAdjustRequest(BaseModel):
    drug_catalog_id: str
    batch_id: str | None = None
    warehouse_id: str | None = None
    store_id: str | None = None
    adjustment: int
    reason: str = "Manual adjustment"


class MovementCreate(BaseModel):
    drug_catalog_id: str
    batch_id: str | None = None
    warehouse_id: str | None = None
    store_id: str | None = None
    movement_type: StockMovementType
    quantity: int
    reference_type: str | None = None
    reference_id: str | None = None
    reason: str | None = None
    notes: str | None = None


class TransferCreate(BaseModel):
    from_warehouse_id: str | None = None
    to_warehouse_id: str | None = None
    from_store_id: str | None = None
    to_store_id: str | None = None
    notes: str | None = None


class TransferItemCreate(BaseModel):
    drug_catalog_id: str
    batch_id: str | None = None
    quantity_requested: int


class ReturnCreate(BaseModel):
    patient_id: str | None = None
    prescription_id: str | None = None
    drug_catalog_id: str | None = None
    batch_id: str | None = None
    return_reason: str
    quantity: int
    disposition: str | None = None
    notes: str | None = None


class WasteCreate(BaseModel):
    drug_catalog_id: str | None = None
    batch_id: str | None = None
    quantity: int
    waste_reason: str
    witness_by: str | None = None
    disposal_method: str | None = None
    notes: str | None = None


class RecallCreate(BaseModel):
    drug_catalog_id: str
    batch_id: str | None = None
    recall_reason: str
    recall_date: date
    initiated_by: str | None = None
    severity: str
    actions_taken: str | None = None
    notes: str | None = None


class RecallResponse(BaseModel):
    id: str
    drug_catalog_id: str
    batch_id: str | None
    recall_reason: str
    recall_date: str
    severity: str
    status: str
    actions_taken: str | None
    notes: str | None

    model_config = ConfigDict(from_attributes=True)


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
    id: str
    drug_catalog_id: str
    batch_id: str | None
    movement_type: str
    quantity: int
    reference_type: str | None
    reference_id: str | None
    reason: str | None
    performed_by: str | None
    movement_date: str
    notes: str | None

    model_config = ConfigDict(from_attributes=True)


class TransferResponse(BaseModel):
    id: str
    from_warehouse_id: str | None
    to_warehouse_id: str | None
    status: str
    initiated_by: str | None
    approved_by: str | None
    dispatch_date: str | None
    received_date: str | None
    notes: str | None

    model_config = ConfigDict(from_attributes=True)


class DashboardResponse(BaseModel):
    total_prescriptions: int
    active_prescriptions: int
    pending_queue: int
    dispensed_today: int


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
    batch = svc.create_batch(drug_id, data.model_dump(exclude_none=True))
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Drug not found: {drug_id}")
    return batch


@router.get("/drugs/{drug_id}/batches", response_model=list[DrugBatchResponse])
async def list_batches(
    drug_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    svc = _get_pharmacy_service(db, user)
    return svc.get_batches(drug_id)


@router.get("/batches/{batch_id}", response_model=DrugBatchResponse)
async def get_batch(
    batch_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    svc = _get_pharmacy_service(db, user)
    batch = svc.get_batch(batch_id)
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Batch not found: {batch_id}")
    return batch


@router.get("/batches/expiring", response_model=list[DrugBatchResponse])
async def get_expiring_batches(
    days: int = Query(90, ge=1, le=365),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    svc = _get_pharmacy_service(db, user)
    return svc.get_expiring_batches(days)


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
    try:
        return svc.create_prescription(data.model_dump(exclude_none=True))
    except PharmacyAuthorizationBlocked as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Prescription authorisation proof is required") from exc


@router.get("/prescriptions", response_model=list[PrescriptionResponse])
async def list_prescriptions(
    status_filter: str | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    _get_pharmacy_service(db, user)
    q = db.query(Prescription).filter(~~Prescription.is_deleted)
    if user.lab_id:
        q = q.filter(Prescription.lab_id == user.lab_id)
    if status_filter:
        q = q.filter(Prescription.status == status_filter)
    q.count()
    return q.order_by(Prescription.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/prescriptions/{rx_id}", response_model=PrescriptionResponse)
async def get_prescription(
    rx_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    svc = _get_pharmacy_service(db, user)
    rx = svc.get_prescription(rx_id)
    if not rx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Prescription not found: {rx_id}")
    return rx


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
    rx = svc.update_prescription_status(rx_id, parsed)
    if not rx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Prescription not found: {rx_id}")
    return rx


@router.post("/prescriptions/{rx_id}/renew", response_model=PrescriptionResponse)
async def renew_prescription(
    rx_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    svc = _get_pharmacy_service(db, user)
    try:
        renewal = svc.renew_prescription(rx_id)
    except PharmacyAuthorizationBlocked as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Prescription renewal authorisation proof is required") from exc
    if not renewal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Prescription not found: {rx_id}")
    return renewal


@router.post("/prescriptions/{rx_id}/cancel", response_model=PrescriptionResponse)
async def cancel_prescription(
    rx_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    svc = _get_pharmacy_service(db, user)
    rx = svc.cancel_prescription(rx_id)
    if not rx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Prescription not found: {rx_id}")
    return rx


@router.post("/prescriptions/{rx_id}/items", response_model=PrescriptionItemResponse, status_code=status.HTTP_201_CREATED)
async def add_prescription_item(
    rx_id: str,
    data: PrescriptionItemCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    svc = _get_pharmacy_service(db, user)
    item = svc.add_prescription_item(rx_id, data.model_dump(exclude_none=True))
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Prescription not found: {rx_id}")
    return item


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
    reason = data.get("reason")
    svc = _get_pharmacy_service(db, user)
    try:
        item = svc.substitute_prescription_item(rx_id, item_id, new_drug_id, reason or "")
    except PharmacyAuthorizationBlocked as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Equivalent substitution authorisation proof is required") from exc
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prescription item not found")
    return item


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
    stock = db.query(StockLevel).filter(
        StockLevel.lab_id == user.lab_id,
        StockLevel.batch_id == data.batch_id,
        StockLevel.drug_catalog_id == data.drug_catalog_id,
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
    quantity_before = stock.available_quantity
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
        record = _get_pharmacy_service(db, user).create_dispense_record(data.model_dump(exclude_none=True))
        db.flush()
        guard.complete(
            receipt,
            resource_type="pharmacy_stock_level",
            resource_id=stock.id,
            state_before=f"available={quantity_before}",
            state_after=f"available={stock.available_quantity}",
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
    return svc.get_dispense_records(patient_id)


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
    return {"items": items, "total": total, "skip": skip, "limit": limit}


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
    return {"status": "adjusted", "id": stock.id, "new_quantity": stock.quantity}


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
    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.post("/inventory/movements", response_model=MovementResponse, status_code=status.HTTP_201_CREATED)
async def create_movement(
    data: MovementCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    svc = _get_pharmacy_service(db, user)
    return svc.create_movement(data.model_dump(exclude_none=True))


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
    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.post("/inventory/transfers", response_model=TransferResponse, status_code=status.HTTP_201_CREATED)
async def create_transfer(
    data: TransferCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    svc = _get_pharmacy_service(db, user)
    return svc.create_transfer(data.model_dump(exclude_none=True))


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
    return {"status": "returned", "id": ret.id}


@router.post("/inventory/waste", status_code=status.HTTP_201_CREATED)
async def create_waste(
    data: WasteCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    svc = _get_pharmacy_service(db, user)
    waste = svc.create_waste(data.model_dump(exclude_none=True))
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
    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.post("/inventory/recalls", response_model=RecallResponse, status_code=status.HTTP_201_CREATED)
async def create_recall(
    data: RecallCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    svc = _get_pharmacy_service(db, user)
    return svc.create_recall(data.model_dump(exclude_none=True))


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
        return POSSaleResponse.model_validate(sale)
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
    return [POSSaleResponse.model_validate(sale) for sale in sales]


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
    return POSSaleResponse.model_validate(sale)


# ── Drug substitution routes ────────────────────────────────────────────────────


class SubstitutionRequestCreate(BaseModel):
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
    original_drug_id: str = Query(..., min_length=1, max_length=26),
    quantity: int = Query(1, ge=1, le=10000),
    db: Session = Depends(get_db),
    user: Any = Depends(require_institutional_permission("lab:read")),
) -> list[dict[str, Any]]:
    try:
        return _get_pharmacy_service(db, user).list_substitution_candidates(original_drug_id, quantity)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/substitutions/requests", status_code=status.HTTP_201_CREATED)
async def create_substitution_request(
    data: SubstitutionRequestCreate,
    db: Session = Depends(get_db),
    user: Any = Depends(require_institutional_permission("lab:manage")),
) -> dict[str, Any]:
    try:
        request = _get_pharmacy_service(db, user).create_substitution_request(data.model_dump())
        db.commit()
        db.refresh(request)
        return request.to_dict()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/substitutions/requests/{request_id}/approve")
async def approve_substitution_request(
    request_id: str,
    db: Session = Depends(get_db),
    user: Any = Depends(require_institutional_permission("lab:manage")),
) -> dict[str, Any]:
    try:
        request = _get_pharmacy_service(db, user).approve_substitution(request_id)
        db.commit()
        db.refresh(request)
        return request.to_dict()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/substitutions/requests/{request_id}/reject")
async def reject_substitution_request(
    request_id: str,
    data: SubstitutionRejectRequest,
    db: Session = Depends(get_db),
    user: Any = Depends(require_institutional_permission("lab:manage")),
) -> dict[str, Any]:
    try:
        request = _get_pharmacy_service(db, user).reject_substitution(request_id, data.reason)
        db.commit()
        db.refresh(request)
        return request.to_dict()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.database import get_db
from app.national.domain.medication_catalog import MedicationCatalog
from app.security.dependencies import get_current_user
from app.services.route_audit import audit_mutation

router = APIRouter(prefix="/medication-catalog", tags=["Medication Catalog"])


class MedicationCatalogCreate(BaseModel):
    medication_code: str
    medication_code_system: str | None = None
    medication_name: str
    medication_name_ar: str | None = None
    generic_name: str | None = None
    brand_name: str | None = None
    manufacturer: str | None = None
    form: str | None = None
    strength_value: str | None = None
    strength_unit: str | None = None
    route: str | None = None
    category: str | None = None
    therapeutic_class: str | None = None
    atc_code: str | None = None
    atc_description: str | None = None
    is_controlled: bool = False
    is_narcotic: bool = False
    requires_prescription: bool = True
    is_active: bool = True
    max_daily_dose: str | None = None
    min_age_years: int | None = None
    pregnancy_category: str | None = None
    ingredients: list[dict[str, Any]] | None = None
    contraindications: list[dict[str, Any]] | None = None
    side_effects: list[dict[str, Any]] | None = None
    interactions: list[dict[str, Any]] | None = None


class MedicationCatalogUpdate(BaseModel):
    medication_name: str | None = None
    medication_name_ar: str | None = None
    generic_name: str | None = None
    brand_name: str | None = None
    manufacturer: str | None = None
    form: str | None = None
    strength_value: str | None = None
    strength_unit: str | None = None
    route: str | None = None
    category: str | None = None
    therapeutic_class: str | None = None
    atc_code: str | None = None
    atc_description: str | None = None
    is_controlled: bool | None = None
    is_narcotic: bool | None = None
    requires_prescription: bool | None = None
    is_active: bool | None = None
    max_daily_dose: str | None = None
    min_age_years: int | None = None
    pregnancy_category: str | None = None
    ingredients: list[dict[str, Any]] | None = None
    contraindications: list[dict[str, Any]] | None = None
    side_effects: list[dict[str, Any]] | None = None
    interactions: list[dict[str, Any]] | None = None


class MedicationCatalogResponse(BaseModel):
    id: str
    medication_code: str
    medication_code_system: str | None
    medication_name: str
    medication_name_ar: str | None
    generic_name: str | None
    brand_name: str | None
    manufacturer: str | None
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
    min_age_years: int | None
    pregnancy_category: str | None
    ingredients: list[dict[str, Any]] | None
    contraindications: list[dict[str, Any]] | None
    side_effects: list[dict[str, Any]] | None
    interactions: list[dict[str, Any]] | None
    is_deleted: bool
    created_at: str | None
    updated_at: str | None

    model_config = ConfigDict(from_attributes=True)


class MedicationCatalogListResponse(BaseModel):
    items: list[MedicationCatalogResponse]
    total: int
    skip: int
    limit: int


class InteractionResponse(BaseModel):
    medication_code: str | None = None
    medication_name: str | None = None
    severity: str | None = None
    description: str | None = None
    recommendation: str | None = None
    mechanism: str | None = None


class ContraindicationDetailResponse(BaseModel):
    type: str
    code: str | None
    description: str | None
    severity: str | None
    details: str | None = None


def _get_medication_or_404(db: Session, medication_id: str) -> MedicationCatalog:
    med = db.query(MedicationCatalog).filter(
        MedicationCatalog.id == medication_id,
        ~MedicationCatalog.is_deleted,
    ).first()
    if not med:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Medication not found: {medication_id}")
    return med


@router.post("/", response_model=MedicationCatalogResponse, status_code=status.HTTP_201_CREATED)
async def create_medication(
    data: MedicationCatalogCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    med = MedicationCatalog(**data.model_dump(exclude_none=True))
    db.add(med)
    db.flush()
    audit_mutation(
        db,
        action="national.medication_catalog.create",
        resource_type="MedicationCatalog",
        resource_id=med.id,
        user=user,
        after={"medication_code": med.medication_code, "is_active": med.is_active},
    )
    db.commit()
    return med


@router.get("/{medication_id}", response_model=MedicationCatalogResponse)
async def get_medication(
    medication_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return _get_medication_or_404(db, medication_id)


@router.put("/{medication_id}", response_model=MedicationCatalogResponse)
async def update_medication(
    medication_id: str,
    data: MedicationCatalogUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    med = _get_medication_or_404(db, medication_id)
    before = {"medication_code": med.medication_code, "medication_name": med.medication_name, "is_active": med.is_active}
    update_data = data.model_dump(exclude_none=True)
    for key, value in update_data.items():
        if hasattr(med, key):
            setattr(med, key, value)
    db.flush()
    audit_mutation(
        db,
        action="national.medication_catalog.update",
        resource_type="MedicationCatalog",
        resource_id=med.id,
        user=user,
        before=before,
        after={"medication_code": med.medication_code, "medication_name": med.medication_name, "is_active": med.is_active},
    )
    db.commit()
    return med


@router.delete("/{medication_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_medication(
    medication_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    med = _get_medication_or_404(db, medication_id)
    before = {"medication_code": med.medication_code, "medication_name": med.medication_name, "is_deleted": med.is_deleted}
    med.soft_delete()
    db.flush()
    audit_mutation(
        db,
        action="national.medication_catalog.delete",
        resource_type="MedicationCatalog",
        resource_id=med.id,
        user=user,
        before=before,
        after={"is_deleted": True},
    )
    db.commit()


@router.get("/search", response_model=MedicationCatalogListResponse)
async def search_medications(
    name: str | None = Query(None),
    code: str | None = Query(None),
    category: str | None = Query(None),
    atc_code: str | None = Query(None),
    therapeutic_class: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    query = db.query(MedicationCatalog).filter(~~MedicationCatalog.is_deleted)
    if name:
        query = query.filter(MedicationCatalog.medication_name.ilike(f"%{name}%"))
    if code:
        query = query.filter(MedicationCatalog.medication_code.ilike(f"%{code}%"))
    if category:
        query = query.filter(MedicationCatalog.category == category)
    if atc_code:
        query = query.filter(MedicationCatalog.atc_code == atc_code)
    if therapeutic_class:
        query = query.filter(MedicationCatalog.therapeutic_class == therapeutic_class)
    total = query.count()
    medications = query.order_by(MedicationCatalog.medication_name).offset(skip).limit(limit).all()
    return MedicationCatalogListResponse(items=medications, total=total, skip=skip, limit=limit)


@router.get("/by-category/{category}", response_model=MedicationCatalogListResponse)
async def get_medications_by_category(
    category: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    query = db.query(MedicationCatalog).filter(
        MedicationCatalog.category == category,
        ~MedicationCatalog.is_deleted,
    )
    total = query.count()
    medications = query.order_by(MedicationCatalog.medication_name).offset(skip).limit(limit).all()
    return MedicationCatalogListResponse(items=medications, total=total, skip=skip, limit=limit)


@router.get("/{medication_id}/interactions", response_model=list[InteractionResponse])
async def get_medication_interactions(
    medication_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    med = _get_medication_or_404(db, medication_id)
    raw = med.interactions or []
    return [
        InteractionResponse(**item) if isinstance(item, dict) else InteractionResponse()
        for item in raw
    ]


@router.get("/{medication_id}/contraindications", response_model=list[ContraindicationDetailResponse])
async def get_medication_contraindications(
    medication_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    med = _get_medication_or_404(db, medication_id)
    raw = med.contraindications or []
    return [
        ContraindicationDetailResponse(**item) if isinstance(item, dict) else ContraindicationDetailResponse(type="unknown")
        for item in raw
    ]

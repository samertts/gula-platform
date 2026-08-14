from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.database import get_db
from app.insurance.domain.enums import InsuranceType, ProviderContractStatus
from app.insurance.domain.models import InsuranceProvider, ProviderContract
from app.models.lab_user import LabUser
from app.security.dependencies import get_current_user
from app.services.audit_service import log_action

router = APIRouter(prefix="/providers", tags=["insurance-providers"])


class ProviderCreate(BaseModel):
    insurance_type: InsuranceType
    name: str
    name_ar: str | None = None
    code: str
    license_number: str | None = None
    tax_id: str | None = None
    is_government: bool = False
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    address_line: str | None = None
    city: str | None = None
    governorate: str | None = None
    country: str = "IQ"
    contact_person: str | None = None
    contact_phone: str | None = None
    coverage_notes: str | None = None


class ProviderUpdate(BaseModel):
    insurance_type: InsuranceType | None = None
    name: str | None = None
    name_ar: str | None = None
    code: str | None = None
    license_number: str | None = None
    tax_id: str | None = None
    is_government: bool | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    address_line: str | None = None
    city: str | None = None
    governorate: str | None = None
    country: str | None = None
    contact_person: str | None = None
    contact_phone: str | None = None
    coverage_notes: str | None = None
    is_active: bool | None = None


class ProviderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lab_id: int
    insurance_type: InsuranceType
    name: str
    name_ar: str | None = None
    code: str
    license_number: str | None = None
    tax_id: str | None = None
    is_government: bool
    is_active: bool
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    address_line: str | None = None
    city: str | None = None
    governorate: str | None = None
    country: str | None = None
    contact_person: str | None = None
    contact_phone: str | None = None
    coverage_notes: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ProviderContractCreate(BaseModel):
    facility_id: int
    facility_type: str | None = None
    contract_number: str
    start_date: date
    end_date: date | None = None
    termination_notice_days: int = 90
    contract_type: str | None = None
    network_type: str = "preferred"
    is_exclusive: bool = False
    fee_schedule_id: str | None = None
    discount_percentage: float | None = None
    stop_loss_threshold: float | None = None
    risk_sharing: str | None = None
    terms_text: str | None = None


class ProviderContractResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lab_id: int
    insurance_provider_id: int
    facility_id: int
    facility_type: str | None = None
    contract_number: str
    status: ProviderContractStatus
    start_date: date
    end_date: date | None = None
    termination_notice_days: int
    contract_type: str | None = None
    network_type: str | None = None
    is_exclusive: bool
    discount_percentage: float | None = None
    stop_loss_threshold: float | None = None
    risk_sharing: str | None = None
    terms_text: str | None = None
    signed_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


@router.get("", response_model=list[ProviderResponse])
def list_providers(
    search: str | None = Query(None),
    insurance_type: InsuranceType | None = Query(None),
    is_active: bool | None = Query(None),
    is_government: bool | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(InsuranceProvider).filter(InsuranceProvider.lab_id == current_user.lab_id)
    if search:
        like = f"%{search}%"
        q = q.filter(
            InsuranceProvider.name.ilike(like)
            | InsuranceProvider.name_ar.ilike(like)
            | InsuranceProvider.code.ilike(like),
        )
    if insurance_type:
        q = q.filter(InsuranceProvider.insurance_type == insurance_type)
    if is_active is not None:
        q = q.filter(InsuranceProvider.is_active == is_active)
    if is_government is not None:
        q = q.filter(InsuranceProvider.is_government == is_government)
    return q.order_by(InsuranceProvider.name).offset(skip).limit(limit).all()


@router.post("", status_code=201, response_model=ProviderResponse)
def create_provider(
    data: ProviderCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = db.query(InsuranceProvider).filter(
        InsuranceProvider.lab_id == current_user.lab_id,
        InsuranceProvider.code == data.code,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Provider with code '{data.code}' already exists")

    provider = InsuranceProvider(
        lab_id=current_user.lab_id,
        **data.model_dump(),
    )
    db.add(provider)
    db.flush()

    log_action(
        db=db,
        action="insurance.provider.create",
        resource_type="insurance_provider",
        resource_id=provider.id,
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Created insurance provider '{provider.name}' ({provider.code})",
    )
    db.commit()
    db.refresh(provider)
    return provider


@router.get("/{provider_id}", response_model=ProviderResponse)
def get_provider(
    provider_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    provider = db.query(InsuranceProvider).filter(
        InsuranceProvider.id == provider_id,
        InsuranceProvider.lab_id == current_user.lab_id,
    ).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    return provider


@router.put("/{provider_id}", response_model=ProviderResponse)
def update_provider(
    provider_id: int,
    data: ProviderUpdate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    provider = db.query(InsuranceProvider).filter(
        InsuranceProvider.id == provider_id,
        InsuranceProvider.lab_id == current_user.lab_id,
    ).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    for field, value in update_data.items():
        setattr(provider, field, value)

    log_action(
        db=db,
        action="insurance.provider.update",
        resource_type="insurance_provider",
        resource_id=provider.id,
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Updated insurance provider '{provider.name}' ({provider.code})",
    )
    db.commit()
    db.refresh(provider)
    return provider


@router.delete("/{provider_id}", status_code=204, response_model=None)
def deactivate_provider(
    provider_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    provider = db.query(InsuranceProvider).filter(
        InsuranceProvider.id == provider_id,
        InsuranceProvider.lab_id == current_user.lab_id,
    ).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    if not provider.is_active:
        raise HTTPException(status_code=400, detail="Provider is already inactive")

    provider.is_active = False
    log_action(
        db=db,
        action="insurance.provider.deactivate",
        resource_type="insurance_provider",
        resource_id=provider.id,
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Deactivated insurance provider '{provider.name}' ({provider.code})",
    )
    db.commit()


@router.get("/{provider_id}/contracts", response_model=list[ProviderContractResponse])
def list_provider_contracts(
    provider_id: int,
    status: ProviderContractStatus | None = Query(None),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    provider = db.query(InsuranceProvider).filter(
        InsuranceProvider.id == provider_id,
        InsuranceProvider.lab_id == current_user.lab_id,
    ).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    q = db.query(ProviderContract).filter(
        ProviderContract.insurance_provider_id == provider_id,
        ProviderContract.lab_id == current_user.lab_id,
    )
    if status:
        q = q.filter(ProviderContract.status == status)
    return q.order_by(ProviderContract.created_at.desc()).all()


@router.post("/{provider_id}/contracts", status_code=201, response_model=ProviderContractResponse)
def add_provider_contract(
    provider_id: int,
    data: ProviderContractCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    provider = db.query(InsuranceProvider).filter(
        InsuranceProvider.id == provider_id,
        InsuranceProvider.lab_id == current_user.lab_id,
    ).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    existing = db.query(ProviderContract).filter(
        ProviderContract.lab_id == current_user.lab_id,
        ProviderContract.contract_number == data.contract_number,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Contract with number '{data.contract_number}' already exists")

    contract = ProviderContract(
        lab_id=current_user.lab_id,
        insurance_provider_id=provider_id,
        status=ProviderContractStatus.DRAFT,
        **data.model_dump(),
    )
    db.add(contract)
    db.flush()

    log_action(
        db=db,
        action="insurance.provider_contract.create",
        resource_type="provider_contract",
        resource_id=contract.id,
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Added contract '{contract.contract_number}' for provider '{provider.name}'",
    )
    db.commit()
    db.refresh(contract)
    return contract

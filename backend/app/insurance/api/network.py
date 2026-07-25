from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.database import get_db
from app.insurance.domain.enums import NetworkTier
from app.insurance.domain.models import InsuranceProvider
from app.insurance.domain.network import (
    GeographicCoverage,
    NetworkProvider,
    NetworkService,
    ProviderAvailability,
)
from app.models.lab_user import LabUser
from app.security.dependencies import get_current_user
from app.services.audit_service import log_action

router = APIRouter(prefix="/network", tags=["insurance-network"])


class NetworkProviderCreate(BaseModel):
    provider_id: int
    facility_id: int
    contract_id: int | None = None
    facility_type: str | None = None
    network_tier: NetworkTier = NetworkTier.TIER2
    is_preferred: bool = False
    is_exclusive: bool = False
    is_accepting_new_patients: bool = True
    join_date: date
    termination_date: date | None = None
    service_area: str | None = None


class NetworkProviderUpdate(BaseModel):
    network_tier: NetworkTier | None = None
    is_preferred: bool | None = None
    is_exclusive: bool | None = None
    is_accepting_new_patients: bool | None = None
    termination_date: date | None = None
    service_area: str | None = None


class NetworkProviderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lab_id: int
    provider_id: int
    facility_id: int
    contract_id: int | None = None
    facility_type: str | None = None
    network_tier: NetworkTier
    is_preferred: bool
    is_exclusive: bool
    is_accepting_new_patients: bool
    join_date: date
    termination_date: date | None = None
    service_area: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class NetworkServiceCreate(BaseModel):
    service_code: str
    service_name: str | None = None
    negotiated_rate: Decimal | None = None
    contracted_rate: Decimal | None = None
    in_network_price: Decimal | None = None
    out_of_network_price: Decimal | None = None
    currency: str = "IQD"
    effective_from: date | None = None
    effective_until: date | None = None


class NetworkServiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lab_id: int
    network_provider_id: int
    service_code: str
    service_name: str | None = None
    negotiated_rate: Decimal | None = None
    contracted_rate: Decimal | None = None
    in_network_price: Decimal | None = None
    out_of_network_price: Decimal | None = None
    currency: str
    is_active: bool
    effective_from: date | None = None
    effective_until: date | None = None
    created_at: str | None = None


class AvailabilityCreate(BaseModel):
    day_of_week: int
    time_from: str
    time_to: str
    is_available: bool = True
    slot_type: str = "general"
    max_patients: int = 10
    current_patients: int = 0
    effective_from: date | None = None
    effective_until: date | None = None


class AvailabilityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lab_id: int
    network_provider_id: int
    day_of_week: int
    time_from: str
    time_to: str
    is_available: bool
    slot_type: str | None = None
    max_patients: int
    current_patients: int
    effective_from: date | None = None
    effective_until: date | None = None


@router.get("/providers", response_model=list[NetworkProviderResponse])
def list_network_providers(
    network_tier: NetworkTier | None = Query(None),
    is_preferred: bool | None = Query(None),
    is_accepting_new_patients: bool | None = Query(None),
    facility_type: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(NetworkProvider).filter(NetworkProvider.lab_id == current_user.lab_id)
    if network_tier:
        q = q.filter(NetworkProvider.network_tier == network_tier)
    if is_preferred is not None:
        q = q.filter(NetworkProvider.is_preferred == is_preferred)
    if is_accepting_new_patients is not None:
        q = q.filter(NetworkProvider.is_accepting_new_patients == is_accepting_new_patients)
    if facility_type:
        q = q.filter(NetworkProvider.facility_type == facility_type)
    return q.order_by(NetworkProvider.join_date.desc()).offset(skip).limit(limit).all()


@router.post("/providers", status_code=201, response_model=NetworkProviderResponse)
def add_network_provider(
    data: NetworkProviderCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    provider = (
        db.query(InsuranceProvider)
        .filter(
            InsuranceProvider.id == data.provider_id,
            InsuranceProvider.lab_id == current_user.lab_id,
        )
        .first()
    )
    if not provider:
        raise HTTPException(status_code=404, detail="Insurance provider not found")

    existing = (
        db.query(NetworkProvider)
        .filter(
            NetworkProvider.lab_id == current_user.lab_id,
            NetworkProvider.provider_id == data.provider_id,
            NetworkProvider.facility_id == data.facility_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Provider already in network")

    net_provider = NetworkProvider(
        lab_id=current_user.lab_id,
        **data.model_dump(),
    )
    db.add(net_provider)
    db.flush()

    log_action(
        db=db,
        action="insurance.network.add_provider",
        resource_type="network_provider",
        resource_id=net_provider.id,
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Added provider '{provider.name}' to network (tier: {data.network_tier.value})",
    )
    db.commit()
    db.refresh(net_provider)
    return net_provider


@router.put("/providers/{network_provider_id}", response_model=NetworkProviderResponse)
def update_network_provider(
    network_provider_id: int,
    data: NetworkProviderUpdate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    net_provider = (
        db.query(NetworkProvider)
        .filter(
            NetworkProvider.id == network_provider_id,
            NetworkProvider.lab_id == current_user.lab_id,
        )
        .first()
    )
    if not net_provider:
        raise HTTPException(status_code=404, detail="Network provider not found")

    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    for field, value in update_data.items():
        setattr(net_provider, field, value)

    log_action(
        db=db,
        action="insurance.network.update_provider",
        resource_type="network_provider",
        resource_id=net_provider.id,
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Updated network provider {net_provider.id}",
    )
    db.commit()
    db.refresh(net_provider)
    return net_provider


@router.delete("/providers/{network_provider_id}", status_code=204)
def remove_from_network(
    network_provider_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    net_provider = (
        db.query(NetworkProvider)
        .filter(
            NetworkProvider.id == network_provider_id,
            NetworkProvider.lab_id == current_user.lab_id,
        )
        .first()
    )
    if not net_provider:
        raise HTTPException(status_code=404, detail="Network provider not found")

    db.delete(net_provider)

    log_action(
        db=db,
        action="insurance.network.remove_provider",
        resource_type="network_provider",
        resource_id=network_provider_id,
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Removed network provider {network_provider_id} from network",
    )
    db.commit()


@router.get(
    "/providers/{network_provider_id}/services", response_model=list[NetworkServiceResponse]
)
def list_network_services(
    network_provider_id: int,
    is_active: bool | None = Query(None),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    net_provider = (
        db.query(NetworkProvider)
        .filter(
            NetworkProvider.id == network_provider_id,
            NetworkProvider.lab_id == current_user.lab_id,
        )
        .first()
    )
    if not net_provider:
        raise HTTPException(status_code=404, detail="Network provider not found")

    q = db.query(NetworkService).filter(
        NetworkService.network_provider_id == network_provider_id,
        NetworkService.lab_id == current_user.lab_id,
    )
    if is_active is not None:
        q = q.filter(NetworkService.is_active == is_active)
    return q.order_by(NetworkService.service_code).all()


@router.post(
    "/providers/{network_provider_id}/services",
    status_code=201,
    response_model=NetworkServiceResponse,
)
def add_network_service(
    network_provider_id: int,
    data: NetworkServiceCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    net_provider = (
        db.query(NetworkProvider)
        .filter(
            NetworkProvider.id == network_provider_id,
            NetworkProvider.lab_id == current_user.lab_id,
        )
        .first()
    )
    if not net_provider:
        raise HTTPException(status_code=404, detail="Network provider not found")

    service = NetworkService(
        lab_id=current_user.lab_id,
        network_provider_id=network_provider_id,
        **data.model_dump(),
    )
    db.add(service)
    db.flush()

    log_action(
        db=db,
        action="insurance.network.add_service",
        resource_type="network_service",
        resource_id=service.id,
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Added service '{data.service_code}' to network provider {network_provider_id}",
    )
    db.commit()
    db.refresh(service)
    return service


@router.get(
    "/providers/{network_provider_id}/availability", response_model=list[AvailabilityResponse]
)
def get_availability(
    network_provider_id: int,
    day_of_week: int | None = Query(None),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    net_provider = (
        db.query(NetworkProvider)
        .filter(
            NetworkProvider.id == network_provider_id,
            NetworkProvider.lab_id == current_user.lab_id,
        )
        .first()
    )
    if not net_provider:
        raise HTTPException(status_code=404, detail="Network provider not found")

    q = db.query(ProviderAvailability).filter(
        ProviderAvailability.network_provider_id == network_provider_id,
        ProviderAvailability.lab_id == current_user.lab_id,
    )
    if day_of_week is not None:
        q = q.filter(ProviderAvailability.day_of_week == day_of_week)
    return q.order_by(ProviderAvailability.day_of_week, ProviderAvailability.time_from).all()


@router.post(
    "/providers/{network_provider_id}/availability",
    status_code=201,
    response_model=AvailabilityResponse,
)
def set_availability(
    network_provider_id: int,
    data: AvailabilityCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    net_provider = (
        db.query(NetworkProvider)
        .filter(
            NetworkProvider.id == network_provider_id,
            NetworkProvider.lab_id == current_user.lab_id,
        )
        .first()
    )
    if not net_provider:
        raise HTTPException(status_code=404, detail="Network provider not found")

    if data.day_of_week < 0 or data.day_of_week > 6:
        raise HTTPException(
            status_code=400, detail="day_of_week must be 0 (Sunday) through 6 (Saturday)"
        )

    slot = ProviderAvailability(
        lab_id=current_user.lab_id,
        network_provider_id=network_provider_id,
        **data.model_dump(),
    )
    db.add(slot)
    db.commit()
    db.refresh(slot)
    return slot


@router.get("/search", response_model=list[NetworkProviderResponse])
def search_network(
    location: str | None = Query(None),
    specialty: str | None = Query(None),
    service_code: str | None = Query(None),
    network_tier: NetworkTier | None = Query(None),
    is_accepting_new_patients: bool | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(NetworkProvider).filter(NetworkProvider.lab_id == current_user.lab_id)

    if location:
        like = f"%{location}%"
        q = q.filter(NetworkProvider.service_area.ilike(like))

    if network_tier:
        q = q.filter(NetworkProvider.network_tier == network_tier)

    if is_accepting_new_patients is not None:
        q = q.filter(NetworkProvider.is_accepting_new_patients == is_accepting_new_patients)

    if service_code:
        q = q.join(NetworkService).filter(
            NetworkService.service_code == service_code,
            NetworkService.is_active,
        )

    if specialty and hasattr(NetworkProvider, "facility_type"):
        q = q.filter(NetworkProvider.facility_type.ilike(f"%{specialty}%"))

    return q.offset(skip).limit(limit).all()


@router.get("/coverage", response_model=list[dict])
def geographic_coverage_check(
    governorate: str | None = Query(None),
    service_type: str | None = Query(None),
    coverage_level: str | None = Query(None),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(GeographicCoverage).filter(
        GeographicCoverage.lab_id == current_user.lab_id,
        GeographicCoverage.is_active,
    )

    if governorate:
        q = q.filter(GeographicCoverage.governorate == governorate)
    if service_type:
        q = q.filter(GeographicCoverage.service_type == service_type)
    if coverage_level:
        from app.insurance.domain.enums import CoverageLevel

        q = q.filter(GeographicCoverage.coverage_level == CoverageLevel(coverage_level))

    results = q.all()

    return [
        {
            "id": g.id,
            "network_provider_id": g.network_provider_id,
            "governorate": g.governorate,
            "district": g.district,
            "service_type": g.service_type,
            "coverage_level": g.coverage_level.value,
            "routing_authority": g.routing_authority,
            "is_active": g.is_active,
        }
        for g in results
    ]

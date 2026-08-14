from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.database import get_db
from app.national.domain.observation import Observation
from app.national.domain.vital_signs import VitalSignsReference
from app.security.dependencies import get_current_user

router = APIRouter(prefix="/vital-signs", tags=["Vital Signs"])


class VitalSignsReferenceCreate(BaseModel):
    vital_sign_code: str
    vital_sign_name: str
    vital_sign_name_ar: str | None = None
    unit: str | None = None
    normal_range_low: str | None = None
    normal_range_high: str | None = None
    critical_low: str | None = None
    critical_high: str | None = None
    display_order: int = 0
    category: str | None = None


class VitalSignsReferenceUpdate(BaseModel):
    vital_sign_name: str | None = None
    vital_sign_name_ar: str | None = None
    unit: str | None = None
    normal_range_low: str | None = None
    normal_range_high: str | None = None
    critical_low: str | None = None
    critical_high: str | None = None
    display_order: int | None = None
    category: str | None = None


class VitalSignsReferenceResponse(BaseModel):
    id: str
    vital_sign_code: str
    vital_sign_name: str
    vital_sign_name_ar: str | None
    unit: str | None
    normal_range_low: str | None
    normal_range_high: str | None
    critical_low: str | None
    critical_high: str | None
    display_order: int
    category: str | None
    is_deleted: bool
    created_at: datetime | None
    updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class VitalSignsReferenceListResponse(BaseModel):
    items: list[VitalSignsReferenceResponse]
    total: int


class LatestVitalSign(BaseModel):
    code: str
    code_display: str | None
    value_quantity: str | None
    value_text: str | None
    unit: str | None
    interpretation: str | None
    reference_range_low: str | None
    reference_range_high: str | None
    effective_datetime: datetime | None
    observation_id: str


class LatestVitalSignsResponse(BaseModel):
    patient_id: str
    vital_signs: dict[str, LatestVitalSign]
    recorded_at: datetime | None


class VitalSignTrendPoint(BaseModel):
    observation_id: str
    value_quantity: str | None
    unit: str | None
    interpretation: str | None
    effective_datetime: datetime | None
    encounter_id: str | None


class VitalSignTrendResponse(BaseModel):
    patient_id: str
    code: str
    code_display: str | None
    unit: str | None
    data: list[VitalSignTrendPoint]


def _get_reference_or_404(db: Session, code: str) -> VitalSignsReference:
    ref = db.query(VitalSignsReference).filter(
        VitalSignsReference.vital_sign_code == code,
        ~VitalSignsReference.is_deleted,
    ).first()
    if not ref:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Vital sign reference not found: {code}")
    return ref


@router.get("/reference", response_model=VitalSignsReferenceListResponse)
async def list_vital_signs_reference(
    category: str | None = Query(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    query = db.query(VitalSignsReference).filter(~~VitalSignsReference.is_deleted)
    if category:
        query = query.filter(VitalSignsReference.category == category)
    refs = query.order_by(VitalSignsReference.display_order).all()
    return VitalSignsReferenceListResponse(items=refs, total=len(refs))


@router.post("/reference", response_model=VitalSignsReferenceResponse, status_code=status.HTTP_201_CREATED)
async def create_vital_signs_reference(
    data: VitalSignsReferenceCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    ref = VitalSignsReference(**data.model_dump(exclude_none=True))
    db.add(ref)
    db.flush()
    db.commit()
    return ref


@router.put("/reference/{code}", response_model=VitalSignsReferenceResponse)
async def update_vital_signs_reference(
    code: str,
    data: VitalSignsReferenceUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    ref = _get_reference_or_404(db, code)
    update_data = data.model_dump(exclude_none=True)
    for key, value in update_data.items():
        if hasattr(ref, key):
            setattr(ref, key, value)
    db.flush()
    db.commit()
    return ref


@router.delete("/reference/{code}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_vital_signs_reference(
    code: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    ref = _get_reference_or_404(db, code)
    ref.soft_delete()
    db.flush()
    db.commit()


@router.get("/patient/{patient_id}/latest", response_model=LatestVitalSignsResponse)
async def get_latest_vital_signs(
    patient_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    vital_sign_codes = db.query(VitalSignsReference).filter(
        ~~VitalSignsReference.is_deleted,
    ).all()
    vital_sign_map: dict[str, LatestVitalSign] = {}
    latest_datetime: datetime | None = None

    for ref in vital_sign_codes:
        obs = db.query(Observation).filter(
            Observation.patient_id == patient_id,
            Observation.code == ref.vital_sign_code,
            ~Observation.is_deleted,
        ).order_by(
            Observation.effective_datetime.desc(),
        ).first()

        if obs:
            vital_sign_map[ref.vital_sign_code] = LatestVitalSign(
                code=obs.code,
                code_display=obs.code_display,
                value_quantity=obs.value_quantity,
                value_text=obs.value_text,
                unit=obs.unit,
                interpretation=obs.interpretation,
                reference_range_low=obs.reference_range_low,
                reference_range_high=obs.reference_range_high,
                effective_datetime=obs.effective_datetime,
                observation_id=obs.id,
            )
            if obs.effective_datetime and (latest_datetime is None or obs.effective_datetime > latest_datetime):
                latest_datetime = obs.effective_datetime
        else:
            vital_sign_map[ref.vital_sign_code] = LatestVitalSign(
                code=ref.vital_sign_code,
                code_display=ref.vital_sign_name,
                value_quantity=None,
                value_text=None,
                unit=ref.unit,
                interpretation=None,
                reference_range_low=ref.normal_range_low,
                reference_range_high=ref.normal_range_high,
                effective_datetime=None,
                observation_id="",
            )

    return LatestVitalSignsResponse(
        patient_id=patient_id,
        vital_signs=vital_sign_map,
        recorded_at=latest_datetime,
    )


@router.get("/patient/{patient_id}/trend/{code}", response_model=VitalSignTrendResponse)
async def get_vital_sign_trend(
    patient_id: str,
    code: str,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    ref = db.query(VitalSignsReference).filter(
        VitalSignsReference.vital_sign_code == code,
        ~VitalSignsReference.is_deleted,
    ).first()

    observations = db.query(Observation).filter(
        Observation.patient_id == patient_id,
        Observation.code == code,
        ~Observation.is_deleted,
    ).order_by(
        Observation.effective_datetime.asc(),
    ).limit(limit).all()

    return VitalSignTrendResponse(
        patient_id=patient_id,
        code=code,
        code_display=ref.vital_sign_name if ref else code,
        unit=observations[0].unit if observations else (ref.unit if ref else None),
        data=[
            VitalSignTrendPoint(
                observation_id=obs.id,
                value_quantity=obs.value_quantity,
                unit=obs.unit,
                interpretation=obs.interpretation,
                effective_datetime=obs.effective_datetime,
                encounter_id=obs.encounter_id,
            )
            for obs in observations
        ],
    )

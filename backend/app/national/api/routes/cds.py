from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.national.services.cds_engine import ClinicalDecisionSupportEngine
from app.security.dependencies import get_current_user

router = APIRouter(prefix="/cds", tags=["Clinical Decision Support"])

cds_engine = ClinicalDecisionSupportEngine()


class DrugInteractionRequest(BaseModel):
    medication_code_a: str
    medication_code_b: str


class DrugInteractionResponse(BaseModel):
    has_interaction: bool
    severity: str | None
    description: str | None
    recommendation: str | None
    mechanism: str | None = None


class AllergyConflictResponse(BaseModel):
    has_conflict: bool
    allergen: str | None
    allergy_code: str | None
    medication_code: str
    medication_name: str | None
    severity: str
    reaction: str


class DuplicateTherapyRequest(BaseModel):
    medication_code: str
    therapeutic_class: str | None = None


class DuplicateTherapyResponse(BaseModel):
    is_duplicate: bool
    existing_medication_code: str | None
    existing_medication_name: str | None
    new_medication_code: str
    new_medication_name: str | None
    therapeutic_class: str | None
    severity: str
    recommendation: str | None


class ContraindicationResponse(BaseModel):
    has_contraindication: bool
    type: str
    code: str
    description: str
    severity: str
    details: str | None


class DuplicateOrderResponse(BaseModel):
    is_duplicate: bool
    existing_observation_id: str | None = None
    encounter_id: str | None = None
    source: str | None = None
    order_type: str | None
    order_code: str | None
    order_display: str | None
    ordered_at: str | None = None
    time_window_hours: int | None
    status: str | None = None
    severity: str
    recommendation: str | None


class CriticalAlertResponse(BaseModel):
    alert_type: str
    severity: str
    code: str | None
    display: str | None
    value: str | None = None
    interpretation: str | None = None
    reference_range: str | None = None
    effective_datetime: str | None = None
    reaction: str | None = None


class EvaluateGuidelinesRequest(BaseModel):
    patient_id: str
    guideline_id: str | None = None


class GuidelineRecommendation(BaseModel):
    guideline_id: str | None
    guideline_name: str | None
    guideline_description: str | None
    recommendations: list[dict[str, Any]]
    overall_status: bool | None


class CalculateRiskRequest(BaseModel):
    patient_id: str
    risk_type: str


class RiskScoreResponse(BaseModel):
    risk_type: str
    score: float | None
    risk_level: str
    factors: list[dict[str, Any]]
    patient_id: str | None = None
    calculated_at: str | None = None


class PreventiveCareResponse(BaseModel):
    code: str | None
    name: str | None
    name_ar: str | None
    category: str | None
    frequency: str | None
    reason: str | None
    priority: str | None
    due: bool


@router.post("/check-drug-interaction", response_model=DrugInteractionResponse)
async def check_drug_interaction(
    data: DrugInteractionRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return cds_engine.check_drug_interaction(
        db,
        data.medication_code_a,
        data.medication_code_b,
    )


@router.get("/patient/{patient_id}/allergy-conflicts", response_model=list[AllergyConflictResponse])
async def check_allergy_conflicts(
    patient_id: str,
    medication_code: str = Query(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return cds_engine.check_allergy_conflict(db, patient_id, medication_code)


@router.post("/check-duplicate-therapy", response_model=list[DuplicateTherapyResponse])
async def check_duplicate_therapy(
    data: DuplicateTherapyRequest,
    patient_id: str = Query(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return cds_engine.check_duplicate_therapy(
        db,
        patient_id,
        data.medication_code,
        data.therapeutic_class,
    )


@router.get(
    "/patient/{patient_id}/contraindications", response_model=list[ContraindicationResponse],
)
async def check_contraindications(
    patient_id: str,
    medication_code: str = Query(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return cds_engine.check_contraindications(db, patient_id, medication_code)


@router.get("/patient/{patient_id}/duplicate-orders", response_model=list[DuplicateOrderResponse])
async def check_duplicate_orders(
    patient_id: str,
    order_type: str = Query(...),
    order_code: str = Query(...),
    time_window_hours: int = Query(24, ge=1),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return cds_engine.check_duplicate_orders(
        db,
        patient_id,
        order_type,
        order_code,
        time_window_hours,
    )


@router.get("/patient/{patient_id}/critical-alerts", response_model=list[CriticalAlertResponse])
async def get_critical_alerts(
    patient_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return cds_engine.get_critical_alerts(db, patient_id)


@router.post("/evaluate-guidelines", response_model=list[GuidelineRecommendation])
async def evaluate_guidelines(
    data: EvaluateGuidelinesRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return cds_engine.evaluate_clinical_guidelines(
        db,
        data.patient_id,
        data.guideline_id,
    )


@router.post("/calculate-risk", response_model=RiskScoreResponse)
async def calculate_risk(
    data: CalculateRiskRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return cds_engine.calculate_risk_score(db, data.patient_id, data.risk_type)


@router.get("/patient/{patient_id}/preventive-care", response_model=list[PreventiveCareResponse])
async def get_preventive_care(
    patient_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return cds_engine.get_preventive_care_recommendations(db, patient_id)

"""Care Continuum Routes — National Care Continuum Platform REST API.

Bridges primary care, referral networks, care journeys, chronic disease
management, maternal/child health, immunisation, public health programs,
and patient tasks through a unified RESTful interface.
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.lab_user import LabUser
from ..security.dependencies import get_current_user
from ..services.care_continuum_service import (
    accept_referral,
    complete_referral,
    coordinate_ehr_immunization,
    create_antenatal_care_visit,
    create_breastfeeding_record,
    create_care_coordination,
    create_care_journey,
    create_child_development_record,
    create_chronic_disease_registry,
    create_clinical_handover,
    create_cold_chain_monitor,
    create_community_care_record,
    create_community_clinic_record,
    create_community_visit,
    create_cross_org_referral,
    create_delivery_record,
    create_disease_management_plan,
    create_educational_material_assignment,
    create_family_medicine_record,
    create_follow_up_plan,
    create_growth_monitoring,
    create_health_assessment,
    create_health_program,
    create_health_promotion_activity,
    create_home_care_plan,
    create_immunization_schedule,
    create_occupational_health_record,
    create_patient_task,
    create_postnatal_care_visit,
    create_pregnancy_record,
    create_preventive_care_record,
    create_primary_care_encounter,
    create_program_enrollment,
    create_referral_request,
    create_referral_response,
    create_reminder_schedule,
    create_risk_stratification,
    create_school_health_visit,
    create_screening_campaign,
    create_self_follow_up_task,
    create_self_monitoring_record,
    create_transition_of_care,
    create_vaccination_record,
    detect_care_gaps,
    get_care_journey,
    get_immunization_coverage,
    get_missed_vaccinations,
    get_pregnancy_record,
    get_primary_care_encounter,
    get_referral_analytics,
    get_referral_timeline,
    list_care_coordination,
    list_care_journeys,
    list_chronic_disease_registry,
    list_community_care_records,
    list_community_clinic_records,
    list_disease_management_plans,
    list_family_medicine_records,
    list_follow_up_plans,
    list_health_assessments,
    list_health_programs,
    list_home_care_plans,
    list_immunization_schedules,
    list_patient_tasks,
    list_pregnancy_records,
    list_preventive_care_records,
    list_primary_care_encounters,
    list_referrals,
    list_risk_stratifications,
    list_screening_campaigns,
    list_vaccination_records,
    reject_referral,
)

router = APIRouter(prefix="/care-continuum", tags=["care continuum"])


# ── Helper ──────────────────────────────────────────────────────────────────


def _lab_id(user: LabUser) -> int | None:
    return user.lab_id


def _practitioner_id(user: LabUser) -> str | None:
    return str(user.id) if hasattr(user, "national_practitioner_id") else None


# ─────────────────────────────────────────────────────────────────────────────
# PRIMARY CARE
# ─────────────────────────────────────────────────────────────────────────────


@router.post("/primary-care-encounters", summary="Create primary care encounter")
def api_create_primary_care_encounter(
    data: dict,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_primary_care_encounter(db, data, _lab_id(current_user))


@router.get(
    "/primary-care-encounters/{encounter_id}",
    summary="Get primary care encounter",
)
def api_get_primary_care_encounter(
    encounter_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = get_primary_care_encounter(db, encounter_id, _lab_id(current_user))
    if not result:
        raise HTTPException(status_code=404, detail="Encounter not found")
    return result


@router.get("/primary-care-encounters", summary="List primary care encounters")
def api_list_primary_care_encounters(
    patient_id: str | None = Query(None),
    facility_id: str | None = Query(None),
    practitioner_id: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_primary_care_encounters(
        db, patient_id, facility_id, practitioner_id, _lab_id(current_user), skip, limit,
    )


@router.put(
    "/primary-care-encounters/{encounter_id}",
    summary="Update primary care encounter",
)
def api_update_primary_care_encounter(
    encounter_id: str,
    data: dict,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from ..care_continuum.models.primary_care import PrimaryCareEncounter

    # NR-146. This is the one handler in this module that queries a model
    # directly instead of going through the service layer, and it was the one
    # that lost the tenant twice over: the lookup had no lab_id constraint, so
    # any authenticated user could reach any laboratory's encounter by id, and
    # the exclusion tuple below guarded `id`, `created_at`, `updated_at` and
    # `is_deleted` while leaving `lab_id` assignable -- so the request body
    # could also MOVE an encounter into another laboratory.
    lab_id = _lab_id(current_user)
    query = db.query(PrimaryCareEncounter)
    if lab_id is not None:
        query = query.filter(PrimaryCareEncounter.lab_id == lab_id)
    enc = query.filter(
        PrimaryCareEncounter.id == encounter_id,
        PrimaryCareEncounter.is_deleted.is_(False),
    ).first()
    if not enc:
        # Another lab's encounter reads as absent, so this does not become an
        # existence oracle over the clinical record.
        raise HTTPException(status_code=404, detail="Encounter not found")
    for k, v in data.items():
        if hasattr(enc, k) and k not in (
            "id", "lab_id", "created_at", "updated_at", "is_deleted",
        ):
            setattr(enc, k, v)
    db.commit()
    db.refresh(enc)
    return enc.to_dict()


@router.post("/family-medicine-records", summary="Create family medicine record")
def api_create_family_medicine_record(
    data: dict,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_family_medicine_record(db, data)


@router.get(
    "/family-medicine-records", summary="List family medicine records",
)
def api_list_family_medicine_records(
    patient_id: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_family_medicine_records(db, patient_id, _lab_id(current_user), skip, limit)


@router.post("/community-clinic-records", summary="Create community clinic record")
def api_create_community_clinic_record(
    data: dict,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_community_clinic_record(db, data)


@router.get(
    "/community-clinic-records", summary="List community clinic records",
)
def api_list_community_clinic_records(
    patient_id: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_community_clinic_records(db, patient_id, _lab_id(current_user), skip, limit)


@router.post("/health-assessments", summary="Create health assessment")
def api_create_health_assessment(
    data: dict,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_health_assessment(db, data)


@router.get("/health-assessments", summary="List health assessments")
def api_list_health_assessments(
    patient_id: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_health_assessments(db, patient_id, _lab_id(current_user), skip, limit)


@router.post("/preventive-care-records", summary="Create preventive care record")
def api_create_preventive_care_record(
    data: dict,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_preventive_care_record(db, data)


@router.get(
    "/preventive-care-records", summary="List preventive care records",
)
def api_list_preventive_care_records(
    patient_id: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_preventive_care_records(db, patient_id, _lab_id(current_user), skip, limit)


# ─────────────────────────────────────────────────────────────────────────────
# REFERRAL NETWORK
# ─────────────────────────────────────────────────────────────────────────────


@router.post("/referrals", summary="Create referral request")
def api_create_referral(
    data: dict,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_referral_request(db, data)


@router.put("/referrals/{referral_id}/accept", summary="Accept referral")
def api_accept_referral(
    referral_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = accept_referral(db, referral_id, _lab_id(current_user))
    if not result:
        raise HTTPException(status_code=404, detail="Referral not found")
    return result


@router.put("/referrals/{referral_id}/reject", summary="Reject referral")
def api_reject_referral(
    referral_id: str,
    reason: str = Query(..., description="Reason for rejection"),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = reject_referral(db, referral_id, reason, _lab_id(current_user))
    if not result:
        raise HTTPException(status_code=404, detail="Referral not found")
    return result


@router.put(
    "/referrals/{referral_id}/complete", summary="Complete referral",
)
def api_complete_referral(
    referral_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = complete_referral(db, referral_id, _lab_id(current_user))
    if not result:
        raise HTTPException(status_code=404, detail="Referral not found")
    return result


@router.get("/referrals", summary="List referrals")
def api_list_referrals(
    patient_id: str | None = Query(None),
    referring_facility_id: str | None = Query(None),
    receiving_facility_id: str | None = Query(None),
    status: str | None = Query(None),
    direction: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_referrals(
        db, patient_id, referring_facility_id, receiving_facility_id,
        status, direction, _lab_id(current_user), skip, limit,
    )


@router.get(
    "/referrals/timeline/{referral_id}",
    summary="Get referral timeline",
)
def api_get_referral_timeline(
    referral_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_referral_timeline(db, referral_id, _lab_id(current_user))


@router.post(
    "/referrals/cross-org", summary="Create cross-organization referral",
)
def api_create_cross_org_referral(
    data: dict,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_cross_org_referral(db, data)


@router.post(
    "/referrals/response", summary="Create referral response",
)
def api_create_referral_response(
    data: dict,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_referral_response(db, data)


@router.get(
    "/referrals/analytics", summary="Get referral network analytics",
)
def api_get_referral_analytics(
    facility_id: str | None = Query(None),
    organization_id: str | None = Query(None),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_referral_analytics(
        db, facility_id, organization_id, start_date, end_date,
        _lab_id(current_user),
    )


# ─────────────────────────────────────────────────────────────────────────────
# CARE JOURNEY
# ─────────────────────────────────────────────────────────────────────────────


@router.post("/care-journeys", summary="Create care journey")
def api_create_care_journey(
    data: dict,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_care_journey(db, data)


@router.get("/care-journeys/{journey_id}", summary="Get care journey")
def api_get_care_journey(
    journey_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = get_care_journey(db, journey_id, _lab_id(current_user))
    if not result:
        raise HTTPException(status_code=404, detail="Care journey not found")
    return result


@router.get("/care-journeys", summary="List care journeys")
def api_list_care_journeys(
    patient_id: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_care_journeys(db, patient_id, _lab_id(current_user), skip, limit)


@router.post("/follow-up-plans", summary="Create follow-up plan")
def api_create_follow_up_plan(
    data: dict,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_follow_up_plan(db, data)


@router.get("/follow-up-plans", summary="List follow-up plans")
def api_list_follow_up_plans(
    patient_id: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_follow_up_plans(db, patient_id, _lab_id(current_user), skip, limit)


@router.post("/care-coordination", summary="Create care coordination")
def api_create_care_coordination(
    data: dict,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_care_coordination(db, data)


@router.get("/care-coordination", summary="List care coordination")
def api_list_care_coordination(
    patient_id: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_care_coordination(db, patient_id, _lab_id(current_user), skip, limit)


@router.post("/transitions-of-care", summary="Create transition of care")
def api_create_transition_of_care(
    data: dict,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_transition_of_care(db, data)


@router.post("/clinical-handovers", summary="Create clinical handover")
def api_create_clinical_handover(
    data: dict,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_clinical_handover(db, data)


@router.post("/home-care-plans", summary="Create home care plan")
def api_create_home_care_plan(
    data: dict,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_home_care_plan(db, data)


@router.get("/home-care-plans", summary="List home care plans")
def api_list_home_care_plans(
    patient_id: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_home_care_plans(db, patient_id, _lab_id(current_user), skip, limit)


@router.post("/community-care-records", summary="Create community care record")
def api_create_community_care_record(
    data: dict,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_community_care_record(db, data)


@router.get(
    "/community-care-records", summary="List community care records",
)
def api_list_community_care_records(
    patient_id: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_community_care_records(db, patient_id, _lab_id(current_user), skip, limit)


# ─────────────────────────────────────────────────────────────────────────────
# CHRONIC DISEASE
# ─────────────────────────────────────────────────────────────────────────────


@router.post(
    "/chronic-disease-registry", summary="Add chronic disease registry entry",
)
def api_create_chronic_disease_registry(
    data: dict,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_chronic_disease_registry(db, data)


@router.get(
    "/chronic-disease-registry", summary="List chronic disease registry",
)
def api_list_chronic_disease_registry(
    patient_id: str | None = Query(None),
    disease_type: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_chronic_disease_registry(
        db, patient_id, disease_type, _lab_id(current_user), skip, limit,
    )


@router.get(
    "/chronic-disease-registry/{disease_type}",
    summary="Get disease-specific registry",
)
def api_get_disease_specific_registry(
    disease_type: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from ..services.care_continuum_service import get_disease_specific_registry

    return get_disease_specific_registry(db, disease_type, _lab_id(current_user), skip, limit)


@router.post(
    "/disease-management-plans", summary="Create disease management plan",
)
def api_create_disease_management_plan(
    data: dict,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_disease_management_plan(db, data)


@router.get(
    "/disease-management-plans", summary="List disease management plans",
)
def api_list_disease_management_plans(
    patient_id: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_disease_management_plans(db, patient_id, _lab_id(current_user), skip, limit)


@router.post(
    "/risk-stratifications", summary="Create risk stratification",
)
def api_create_risk_stratification(
    data: dict,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_risk_stratification(db, data)


@router.get(
    "/risk-stratifications", summary="List risk stratifications",
)
def api_list_risk_stratifications(
    patient_id: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_risk_stratifications(db, patient_id, _lab_id(current_user), skip, limit)


@router.post(
    "/self-monitoring-records", summary="Create self-monitoring record",
)
def api_create_self_monitoring_record(
    data: dict,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_self_monitoring_record(db, data)


# ─────────────────────────────────────────────────────────────────────────────
# MATERNAL & CHILD HEALTH
# ─────────────────────────────────────────────────────────────────────────────


@router.post("/pregnancy-records", summary="Create pregnancy record")
def api_create_pregnancy_record(
    data: dict,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_pregnancy_record(db, data)


@router.get(
    "/pregnancy-records/{pregnancy_id}",
    summary="Get pregnancy record",
)
def api_get_pregnancy_record(
    pregnancy_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = get_pregnancy_record(db, pregnancy_id, _lab_id(current_user))
    if not result:
        raise HTTPException(status_code=404, detail="Pregnancy record not found")
    return result


@router.get("/pregnancy-records", summary="List pregnancy records")
def api_list_pregnancy_records(
    patient_id: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_pregnancy_records(db, patient_id, _lab_id(current_user), skip, limit)


@router.post(
    "/antenatal-care-visits", summary="Create antenatal care visit",
)
def api_create_antenatal_care_visit(
    data: dict,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_antenatal_care_visit(db, data)


@router.post("/delivery-records", summary="Create delivery record")
def api_create_delivery_record(
    data: dict,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_delivery_record(db, data)


@router.post(
    "/postnatal-care-visits", summary="Create postnatal care visit",
)
def api_create_postnatal_care_visit(
    data: dict,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_postnatal_care_visit(db, data)


@router.post("/growth-monitoring", summary="Create growth monitoring record")
def api_create_growth_monitoring(
    data: dict,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_growth_monitoring(db, data)


@router.post(
    "/breastfeeding-records", summary="Create breastfeeding record",
)
def api_create_breastfeeding_record(
    data: dict,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_breastfeeding_record(db, data)


@router.post(
    "/child-development-records",
    summary="Create child development record",
)
def api_create_child_development_record(
    data: dict,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_child_development_record(db, data)


# ─────────────────────────────────────────────────────────────────────────────
# IMMUNISATION
# ─────────────────────────────────────────────────────────────────────────────


@router.post("/vaccination-records", summary="Create vaccination record")
def api_create_vaccination_record(
    data: dict,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_vaccination_record(db, data)


@router.get(
    "/vaccination-records", summary="List vaccination records",
)
def api_list_vaccination_records(
    patient_id: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_vaccination_records(db, patient_id, _lab_id(current_user), skip, limit)


@router.post(
    "/immunization-schedules", summary="Create immunization schedule",
)
def api_create_immunization_schedule(
    data: dict,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_immunization_schedule(db, data)


@router.get(
    "/immunization-schedules", summary="List immunization schedules",
)
def api_list_immunization_schedules(
    patient_id: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_immunization_schedules(db, patient_id, _lab_id(current_user), skip, limit)


@router.get(
    "/vaccinations/missed", summary="Get missed vaccinations",
)
def api_get_missed_vaccinations(
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_missed_vaccinations(db, _lab_id(current_user))


@router.post("/reminder-schedules", summary="Create reminder schedule")
def api_create_reminder_schedule(
    data: dict,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_reminder_schedule(db, data)


@router.get(
    "/immunization-coverage", summary="Get immunization coverage stats",
)
def api_get_immunization_coverage(
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_immunization_coverage(db, _lab_id(current_user))


@router.post(
    "/cold-chain-monitors", summary="Create cold chain monitor reading",
)
def api_create_cold_chain_monitor(
    data: dict,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_cold_chain_monitor(db, data)


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC HEALTH
# ─────────────────────────────────────────────────────────────────────────────


@router.post("/health-programs", summary="Create health program")
def api_create_health_program(
    data: dict,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_health_program(db, data)


@router.get("/health-programs", summary="List health programs")
def api_list_health_programs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_health_programs(db, _lab_id(current_user), skip, limit)


@router.post(
    "/program-enrollments", summary="Enroll patient in health program",
)
def api_create_program_enrollment(
    data: dict,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_program_enrollment(db, data)


@router.post(
    "/screening-campaigns", summary="Create screening campaign",
)
def api_create_screening_campaign(
    data: dict,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_screening_campaign(db, data)


@router.get(
    "/screening-campaigns", summary="List screening campaigns",
)
def api_list_screening_campaigns(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_screening_campaigns(db, _lab_id(current_user), skip, limit)


@router.post("/community-visits", summary="Create community visit")
def api_create_community_visit(
    data: dict,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_community_visit(db, data)


@router.post(
    "/school-health-visits", summary="Create school health visit",
)
def api_create_school_health_visit(
    data: dict,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_school_health_visit(db, data)


@router.post(
    "/occupational-health-records",
    summary="Create occupational health record",
)
def api_create_occupational_health_record(
    data: dict,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_occupational_health_record(db, data)


@router.post(
    "/health-promotion-activities",
    summary="Create health promotion activity",
)
def api_create_health_promotion_activity(
    data: dict,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_health_promotion_activity(db, data)


# ─────────────────────────────────────────────────────────────────────────────
# PATIENT TASKS
# ─────────────────────────────────────────────────────────────────────────────


@router.post("/patient-tasks", summary="Create patient task")
def api_create_patient_task(
    data: dict,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_patient_task(db, data)


@router.get("/patient-tasks", summary="List patient tasks")
def api_list_patient_tasks(
    patient_id: str | None = Query(None),
    status: str | None = Query(None),
    task_type: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_patient_tasks(
        db, patient_id, status, task_type, _lab_id(current_user), skip, limit,
    )


@router.post(
    "/self-follow-up-tasks", summary="Create self-follow-up task",
)
def api_create_self_follow_up_task(
    data: dict,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_self_follow_up_task(db, data)


@router.post(
    "/educational-material-assignments",
    summary="Assign educational material to patient",
)
def api_create_educational_material_assignment(
    data: dict,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_educational_material_assignment(db, data)


# ─────────────────────────────────────────────────────────────────────────────
# CARE GAP DETECTION
# ─────────────────────────────────────────────────────────────────────────────


@router.get(
    "/care-gaps/{patient_id}",
    summary="Detect care gaps for a patient",
)
def api_detect_care_gaps(
    patient_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return detect_care_gaps(db, patient_id, _lab_id(current_user))


# ─────────────────────────────────────────────────────────────────────────────
# EHR COORDINATION
# ─────────────────────────────────────────────────────────────────────────────


@router.post(
    "/coordinate/ehr-immunization",
    summary="Coordinate EHR immunization record into care continuum",
)
def api_coordinate_ehr_immunization(
    ehr_record_id: str = Query(..., description="EHR ImmunizationRecord ID"),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from ..ehr.models.immunization import ImmunizationRecord

    ehr_rec = db.query(ImmunizationRecord).filter(
        ImmunizationRecord.id == ehr_record_id,
        ImmunizationRecord.is_deleted.is_(False),
    ).first()
    if not ehr_rec:
        raise HTTPException(
            status_code=404,
            detail="EHR ImmunizationRecord not found",
        )
    return coordinate_ehr_immunization(db, ehr_rec)

"""Care Continuum Service — National Care Continuum Platform business logic.

Coordinates all care-continuum operations across primary care, referrals,
chronic disease, maternal/child health, immunisation, public health, and
patient tasks through a unified service interface.
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app._compat import UTC
from app.care_continuum.enums import (
    CareProgramStatus,
    ChronicDiseaseType,
    FollowUpStatus,
    PregnancyStatus,
    ReferralDirection,
    VaccinationStatus,
)
from app.care_continuum.models.care_journey import (
    CareCoordination,
    CareJourney,
    ClinicalHandover,
    CommunityCareRecord,
    FollowUpPlan,
    HomeCarePlan,
    TransitionsOfCare,
)
from app.care_continuum.models.chronic_disease import (
    ChronicDiseaseRegistry,
    DiseaseManagementPlan,
    RiskStratification,
    SelfMonitoringRecord,
)
from app.care_continuum.models.immunization import (
    ColdChainMonitor,
    ImmunizationSchedule,
    ReminderSchedule,
    VaccinationRecord,
    VaccineInventory,
)
from app.care_continuum.models.maternal import (
    AntenatalCareVisit,
    BreastfeedingRecord,
    ChildDevelopmentRecord,
    DeliveryRecord,
    GrowthMonitoring,
    PostnatalCareVisit,
    PregnancyRecord,
)
from app.care_continuum.models.patient_tasks import (
    EducationalMaterialAssignment,
    PatientTask,
    SelfFollowUpTask,
)
from app.care_continuum.models.primary_care import (
    CommunityClinicRecord,
    FamilyMedicineRecord,
    HealthAssessment,
    PreventiveCareRecord,
    PrimaryCareEncounter,
)
from app.care_continuum.models.public_health import (
    CommunityVisit,
    HealthProgram,
    HealthPromotionActivity,
    OccupationalHealthRecord,
    ProgramEnrollment,
    SchoolHealthVisit,
    ScreeningCampaign,
)
from app.care_continuum.models.referral import (
    CrossOrgReferral,
    ReferralRequest,
    ReferralResponse,
    ReferralTimeline,
)
from app.models.lab_user import LabUser
from app.national.domain.practitioner import Practitioner
from app.national.enums import ReferralStatus

logger = logging.getLogger("gula.care_continuum.service")


class ReferralScopeError(PermissionError):
    """Referral access must always carry a server-derived institution scope."""


# ── Helpers ──────────────────────────────────────────────────────────────────


def _require_referral_lab(lab_id: int | None) -> int:
    if lab_id is None or int(lab_id) <= 0:
        raise ReferralScopeError("referral_institution_scope_required")
    return int(lab_id)


def _now() -> datetime:
    return datetime.now(UTC)


def _today() -> date:
    return _now().date()


def _paginated_query(query, skip: int = 0, limit: int = 50):
    total = query.count()
    rows = query.order_by(query.primary_table.c.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "items": [r.to_dict() for r in rows], "skip": skip, "limit": limit}


def _apply_lab_filter(query, model, lab_id: int | None):
    if lab_id is not None and hasattr(model, "lab_id"):
        return query.filter(model.lab_id == lab_id)
    return query


# =============================================================================
# PRIMARY CARE
# =============================================================================


def create_primary_care_encounter(
    db: Session, data: dict, lab_id: int | None = None,
) -> dict:
    enc = PrimaryCareEncounter(**data)
    db.add(enc)
    db.commit()
    db.refresh(enc)
    return enc.to_dict()


def get_primary_care_encounter(db: Session, encounter_id: str) -> dict | None:
    enc = db.query(PrimaryCareEncounter).filter(
        PrimaryCareEncounter.id == encounter_id, PrimaryCareEncounter.is_deleted.is_(False),
    ).first()
    return enc.to_dict() if enc else None


def list_primary_care_encounters(
    db: Session, patient_id: str | None = None, facility_id: str | None = None,
    practitioner_id: str | None = None, lab_id: int | None = None,
    skip: int = 0, limit: int = 50,
) -> dict:
    q = db.query(PrimaryCareEncounter).filter(PrimaryCareEncounter.is_deleted.is_(False))
    if patient_id:
        q = q.filter(PrimaryCareEncounter.patient_id == patient_id)
    if facility_id:
        q = q.filter(PrimaryCareEncounter.facility_id == facility_id)
    if practitioner_id:
        q = q.filter(PrimaryCareEncounter.practitioner_id == practitioner_id)
    q = _apply_lab_filter(q, PrimaryCareEncounter, lab_id)
    return _paginated_query(q, skip, limit)


def create_family_medicine_record(db: Session, data: dict) -> dict:
    rec = FamilyMedicineRecord(**data)
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec.to_dict()


def list_family_medicine_records(
    db: Session, patient_id: str | None = None, lab_id: int | None = None,
    skip: int = 0, limit: int = 50,
) -> dict:
    q = db.query(FamilyMedicineRecord).filter(FamilyMedicineRecord.is_deleted.is_(False))
    if patient_id:
        q = q.filter(FamilyMedicineRecord.patient_id == patient_id)
    q = _apply_lab_filter(q, FamilyMedicineRecord, lab_id)
    return _paginated_query(q, skip, limit)


def create_community_clinic_record(db: Session, data: dict) -> dict:
    rec = CommunityClinicRecord(**data)
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec.to_dict()


def list_community_clinic_records(
    db: Session, patient_id: str | None = None, lab_id: int | None = None,
    skip: int = 0, limit: int = 50,
) -> dict:
    q = db.query(CommunityClinicRecord).filter(CommunityClinicRecord.is_deleted.is_(False))
    if patient_id:
        q = q.filter(CommunityClinicRecord.patient_id == patient_id)
    q = _apply_lab_filter(q, CommunityClinicRecord, lab_id)
    return _paginated_query(q, skip, limit)


def create_health_assessment(db: Session, data: dict) -> dict:
    assess = HealthAssessment(**data)
    db.add(assess)
    db.commit()
    db.refresh(assess)
    return assess.to_dict()


def list_health_assessments(
    db: Session, patient_id: str | None = None, lab_id: int | None = None,
    skip: int = 0, limit: int = 50,
) -> dict:
    q = db.query(HealthAssessment).filter(HealthAssessment.is_deleted.is_(False))
    if patient_id:
        q = q.filter(HealthAssessment.patient_id == patient_id)
    q = _apply_lab_filter(q, HealthAssessment, lab_id)
    return _paginated_query(q, skip, limit)


def create_preventive_care_record(db: Session, data: dict) -> dict:
    rec = PreventiveCareRecord(**data)
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec.to_dict()


def list_preventive_care_records(
    db: Session, patient_id: str | None = None, lab_id: int | None = None,
    skip: int = 0, limit: int = 50,
) -> dict:
    q = db.query(PreventiveCareRecord).filter(PreventiveCareRecord.is_deleted.is_(False))
    if patient_id:
        q = q.filter(PreventiveCareRecord.patient_id == patient_id)
    q = _apply_lab_filter(q, PreventiveCareRecord, lab_id)
    return _paginated_query(q, skip, limit)


# =============================================================================
# REFERRAL NETWORK
# =============================================================================


def create_referral_request(
    db: Session,
    data: dict,
    lab_id: int | None = None,
    server_practitioner_id: int | None = None,
) -> dict:
    scoped_lab_id = _require_referral_lab(lab_id)
    payload = dict(data)
    supplied_lab_id = payload.get("lab_id")
    if supplied_lab_id is not None and int(supplied_lab_id) != scoped_lab_id:
        raise ReferralScopeError("referral_institution_scope_mismatch")
    forbidden = {
        "id",
        "lab_id",
        "tenant_id",
        "organization_id",
        "facility_id",
        "workspace_id",
        "department_id",
        "referring_practitioner_id",
        "referring_facility_id",
        "referring_department_id",
        "receiving_practitioner_id",
        "receiving_facility_id",
        "receiving_department_id",
        "national_referral_id",
        "status",
        "direction",
    }
    if forbidden.intersection(payload):
        raise ReferralScopeError("referral_client_authority_forbidden")
    if server_practitioner_id is None:
        raise ReferralScopeError("server_practitioner_mapping_required")
    user = (
        db.query(LabUser)
        .filter(
            LabUser.id == server_practitioner_id,
            LabUser.lab_id == scoped_lab_id,
            LabUser.is_active.is_(True),
            LabUser.national_id_hash.isnot(None),
        )
        .one_or_none()
    )
    if user is None:
        raise ReferralScopeError("server_practitioner_mapping_required")
    practitioner = (
        db.query(Practitioner)
        .filter(
            Practitioner.national_id_hash == user.national_id_hash,
            Practitioner.is_active.is_(True),
        )
        .one_or_none()
    )
    if practitioner is None:
        raise ReferralScopeError("server_practitioner_mapping_required")
    payload["lab_id"] = scoped_lab_id
    payload["direction"] = ReferralDirection.OUTGOING
    payload["status"] = ReferralStatus.DRAFT
    payload["referring_practitioner_id"] = practitioner.id
    ref = ReferralRequest(**payload)
    db.add(ref)
    db.commit()
    db.refresh(ref)

    _add_referral_timeline(db, ref.id, "created", "Referral request created", lab_id=scoped_lab_id)
    return ref.to_dict()


def accept_referral(db: Session, referral_id: str, lab_id: int | None = None) -> dict | None:
    scoped_lab_id = _require_referral_lab(lab_id)
    ref = db.query(ReferralRequest).filter(
        ReferralRequest.id == referral_id,
        ReferralRequest.lab_id == scoped_lab_id,
    ).first()
    if not ref:
        return None
    ref.status = ReferralStatus.ACCEPTED
    ref.accepted_at = _now()
    db.commit()
    db.refresh(ref)
    _add_referral_timeline(db, referral_id, "accepted", "Referral accepted", lab_id=scoped_lab_id)
    return ref.to_dict()


def reject_referral(
    db: Session, referral_id: str, reason: str, lab_id: int | None = None,
) -> dict | None:
    scoped_lab_id = _require_referral_lab(lab_id)
    ref = db.query(ReferralRequest).filter(
        ReferralRequest.id == referral_id,
        ReferralRequest.lab_id == scoped_lab_id,
    ).first()
    if not ref:
        return None
    ref.status = ReferralStatus.REJECTED
    ref.cancelled_at = _now()
    ref.cancellation_reason = reason
    db.commit()
    db.refresh(ref)
    _add_referral_timeline(db, referral_id, "rejected", f"Referral rejected: {reason}", lab_id=scoped_lab_id)
    return ref.to_dict()


def complete_referral(
    db: Session, referral_id: str, lab_id: int | None = None,
) -> dict | None:
    scoped_lab_id = _require_referral_lab(lab_id)
    ref = db.query(ReferralRequest).filter(
        ReferralRequest.id == referral_id,
        ReferralRequest.lab_id == scoped_lab_id,
    ).first()
    if not ref:
        return None
    ref.status = ReferralStatus.COMPLETED
    ref.completed_at = _now()
    db.commit()
    db.refresh(ref)
    _add_referral_timeline(db, referral_id, "completed", "Referral completed", lab_id=scoped_lab_id)
    return ref.to_dict()


def list_referrals(
    db: Session,
    patient_id: str | None = None,
    referring_facility_id: str | None = None,
    receiving_facility_id: str | None = None,
    status: str | None = None,
    direction: str | None = None,
    lab_id: int | None = None,
    skip: int = 0,
    limit: int = 50,
) -> dict:
    q = db.query(ReferralRequest).filter(ReferralRequest.is_deleted.is_(False))
    if patient_id:
        q = q.filter(ReferralRequest.patient_id == patient_id)
    if referring_facility_id:
        q = q.filter(ReferralRequest.referring_facility_id == referring_facility_id)
    if receiving_facility_id:
        q = q.filter(ReferralRequest.receiving_facility_id == receiving_facility_id)
    if status:
        q = q.filter(ReferralRequest.status == ReferralStatus(status))
    if direction:
        from app.care_continuum.enums import ReferralDirection
        q = q.filter(ReferralRequest.direction == ReferralDirection(direction))
    q = _apply_lab_filter(q, ReferralRequest, lab_id)
    return _paginated_query(q, skip, limit)


def get_referral_timeline(
    db: Session, referral_id: str, lab_id: int | None = None,
) -> list[dict]:
    scoped_lab_id = _require_referral_lab(lab_id)
    entries = (
        db.query(ReferralTimeline)
        .filter(
            ReferralTimeline.referral_request_id == referral_id,
            ReferralTimeline.lab_id == scoped_lab_id,
            ReferralTimeline.is_deleted.is_(False),
        )
        .order_by(ReferralTimeline.event_date.asc())
        .all()
    )
    return [e.to_dict() for e in entries]


def _add_referral_timeline(
    db: Session, referral_id: str, event_type: str, description: str, *, lab_id: int,
    **extra,
) -> ReferralTimeline:
    scoped_lab_id = _require_referral_lab(lab_id)
    entry = ReferralTimeline(
        lab_id=scoped_lab_id,
        referral_request_id=referral_id,
        event_type=event_type,
        event_date=_now(),
        description=description,
        **{k: v for k, v in extra.items() if v is not None},
    )
    db.add(entry)
    db.commit()
    return entry


def create_cross_org_referral(
    db: Session, data: dict, lab_id: int | None = None,
) -> dict:
    scoped_lab_id = _require_referral_lab(lab_id)
    payload = dict(data)
    supplied_lab_id = payload.pop("lab_id", None)
    if supplied_lab_id is not None and int(supplied_lab_id) != scoped_lab_id:
        raise ReferralScopeError("referral_institution_scope_mismatch")
    payload.pop("id", None)
    payload["lab_id"] = scoped_lab_id
    cor = CrossOrgReferral(**payload)
    db.add(cor)
    db.commit()
    db.refresh(cor)
    return cor.to_dict()


def create_referral_response(
    db: Session, data: dict, lab_id: int | None = None,
) -> dict:
    scoped_lab_id = _require_referral_lab(lab_id)
    payload = dict(data)
    supplied_lab_id = payload.pop("lab_id", None)
    if supplied_lab_id is not None and int(supplied_lab_id) != scoped_lab_id:
        raise ReferralScopeError("referral_institution_scope_mismatch")
    payload.pop("id", None)
    payload["lab_id"] = scoped_lab_id
    resp = ReferralResponse(**payload)
    db.add(resp)
    db.commit()
    db.refresh(resp)

    ref = db.query(ReferralRequest).filter(
        ReferralRequest.id == resp.referral_request_id,
        ReferralRequest.lab_id == scoped_lab_id,
    ).first()
    if ref and resp.decision == "accepted":
        ref.status = ReferralStatus.ACCEPTED
        ref.accepted_at = _now()
    elif ref and resp.decision == "rejected":
        ref.status = ReferralStatus.REJECTED
        ref.cancelled_at = _now()
        ref.cancellation_reason = resp.decision_reason
    db.commit()
    return resp.to_dict()


def get_referral_analytics(
    db: Session,
    facility_id: str | None = None,
    lab_id: int | None = None,
    organization_id: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict:
    scoped_lab_id = _require_referral_lab(lab_id)
    q = db.query(ReferralRequest).filter(
        ReferralRequest.is_deleted.is_(False),
        ReferralRequest.lab_id == scoped_lab_id,
    )
    if facility_id:
        q = q.filter(
            or_(
                ReferralRequest.referring_facility_id == facility_id,
                ReferralRequest.receiving_facility_id == facility_id,
            ),
        )
    if start_date:
        q = q.filter(ReferralRequest.created_at >= start_date)
    if end_date:
        q = q.filter(ReferralRequest.created_at <= end_date)

    total = q.count()
    by_status = {}
    by_priority = {}
    for r in q.all():
        s = r.status.value if r.status else "unknown"
        by_status[s] = by_status.get(s, 0) + 1
        p = r.priority.value if r.priority else "unknown"
        by_priority[p] = by_priority.get(p, 0) + 1

    avg_completion_hours = None
    completed = (
        db.query(ReferralRequest)
        .filter(
            ReferralRequest.lab_id == scoped_lab_id,
            ReferralRequest.status == ReferralStatus.COMPLETED,
            ReferralRequest.sent_at.isnot(None),
            ReferralRequest.completed_at.isnot(None),
        )
        .all()
    )
    if completed:
        hours = [
            (r.completed_at - r.sent_at).total_seconds() / 3600
            for r in completed
            if r.completed_at and r.sent_at
        ]
        if hours:
            avg_completion_hours = sum(hours) / len(hours)

    return {
        "total_referrals": total,
        "by_status": by_status,
        "by_priority": by_priority,
        "avg_completion_hours": avg_completion_hours,
    }


# =============================================================================
# CARE JOURNEY & COORDINATION
# =============================================================================


def create_care_journey(db: Session, data: dict) -> dict:
    cj = CareJourney(**data)
    db.add(cj)
    db.commit()
    db.refresh(cj)
    return cj.to_dict()


def get_care_journey(db: Session, journey_id: str) -> dict | None:
    cj = db.query(CareJourney).filter(
        CareJourney.id == journey_id, CareJourney.is_deleted.is_(False),
    ).first()
    return cj.to_dict() if cj else None


def list_care_journeys(
    db: Session, patient_id: str | None = None, lab_id: int | None = None,
    skip: int = 0, limit: int = 50,
) -> dict:
    q = db.query(CareJourney).filter(CareJourney.is_deleted.is_(False))
    if patient_id:
        q = q.filter(CareJourney.patient_id == patient_id)
    q = _apply_lab_filter(q, CareJourney, lab_id)
    return _paginated_query(q, skip, limit)


def create_follow_up_plan(db: Session, data: dict) -> dict:
    fup = FollowUpPlan(**data)
    db.add(fup)
    db.commit()
    db.refresh(fup)
    return fup.to_dict()


def list_follow_up_plans(
    db: Session, patient_id: str | None = None, lab_id: int | None = None,
    skip: int = 0, limit: int = 50,
) -> dict:
    q = db.query(FollowUpPlan).filter(FollowUpPlan.is_deleted.is_(False))
    if patient_id:
        q = q.filter(FollowUpPlan.patient_id == patient_id)
    q = _apply_lab_filter(q, FollowUpPlan, lab_id)
    return _paginated_query(q, skip, limit)


def create_care_coordination(db: Session, data: dict) -> dict:
    cc = CareCoordination(**data)
    db.add(cc)
    db.commit()
    db.refresh(cc)
    return cc.to_dict()


def list_care_coordination(
    db: Session, patient_id: str | None = None, lab_id: int | None = None,
    skip: int = 0, limit: int = 50,
) -> dict:
    q = db.query(CareCoordination).filter(CareCoordination.is_deleted.is_(False))
    if patient_id:
        q = q.filter(CareCoordination.patient_id == patient_id)
    q = _apply_lab_filter(q, CareCoordination, lab_id)
    return _paginated_query(q, skip, limit)


def create_transition_of_care(db: Session, data: dict) -> dict:
    toc = TransitionsOfCare(**data)
    db.add(toc)
    db.commit()
    db.refresh(toc)
    return toc.to_dict()


def create_clinical_handover(db: Session, data: dict) -> dict:
    ho = ClinicalHandover(**data)
    db.add(ho)
    db.commit()
    db.refresh(ho)
    return ho.to_dict()


def create_home_care_plan(db: Session, data: dict) -> dict:
    hcp = HomeCarePlan(**data)
    db.add(hcp)
    db.commit()
    db.refresh(hcp)
    return hcp.to_dict()


def list_home_care_plans(
    db: Session, patient_id: str | None = None, lab_id: int | None = None,
    skip: int = 0, limit: int = 50,
) -> dict:
    q = db.query(HomeCarePlan).filter(HomeCarePlan.is_deleted.is_(False))
    if patient_id:
        q = q.filter(HomeCarePlan.patient_id == patient_id)
    q = _apply_lab_filter(q, HomeCarePlan, lab_id)
    return _paginated_query(q, skip, limit)


def create_community_care_record(db: Session, data: dict) -> dict:
    ccr = CommunityCareRecord(**data)
    db.add(ccr)
    db.commit()
    db.refresh(ccr)
    return ccr.to_dict()


def list_community_care_records(
    db: Session, patient_id: str | None = None, lab_id: int | None = None,
    skip: int = 0, limit: int = 50,
) -> dict:
    q = db.query(CommunityCareRecord).filter(CommunityCareRecord.is_deleted.is_(False))
    if patient_id:
        q = q.filter(CommunityCareRecord.patient_id == patient_id)
    q = _apply_lab_filter(q, CommunityCareRecord, lab_id)
    return _paginated_query(q, skip, limit)


# =============================================================================
# CHRONIC DISEASE
# =============================================================================


def create_chronic_disease_registry(db: Session, data: dict) -> dict:
    entry = ChronicDiseaseRegistry(**data)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry.to_dict()


def list_chronic_disease_registry(
    db: Session,
    patient_id: str | None = None,
    disease_type: str | None = None,
    lab_id: int | None = None,
    skip: int = 0,
    limit: int = 50,
) -> dict:
    q = db.query(ChronicDiseaseRegistry).filter(ChronicDiseaseRegistry.is_deleted.is_(False))
    if patient_id:
        q = q.filter(ChronicDiseaseRegistry.patient_id == patient_id)
    if disease_type:
        q = q.filter(ChronicDiseaseRegistry.disease_type == ChronicDiseaseType(disease_type))
    q = _apply_lab_filter(q, ChronicDiseaseRegistry, lab_id)
    return _paginated_query(q, skip, limit)


def get_disease_specific_registry(
    db: Session,
    disease_type: str,
    lab_id: int | None = None,
    skip: int = 0,
    limit: int = 50,
) -> dict:
    q = db.query(ChronicDiseaseRegistry).filter(
        ChronicDiseaseRegistry.is_deleted.is_(False),
        ChronicDiseaseRegistry.disease_type == ChronicDiseaseType(disease_type),
    )
    q = _apply_lab_filter(q, ChronicDiseaseRegistry, lab_id)
    return _paginated_query(q, skip, limit)


def create_disease_management_plan(db: Session, data: dict) -> dict:
    dmp = DiseaseManagementPlan(**data)
    db.add(dmp)
    db.commit()
    db.refresh(dmp)
    return dmp.to_dict()


def list_disease_management_plans(
    db: Session, patient_id: str | None = None, lab_id: int | None = None,
    skip: int = 0, limit: int = 50,
) -> dict:
    q = db.query(DiseaseManagementPlan).filter(DiseaseManagementPlan.is_deleted.is_(False))
    if patient_id:
        q = q.filter(DiseaseManagementPlan.patient_id == patient_id)
    q = _apply_lab_filter(q, DiseaseManagementPlan, lab_id)
    return _paginated_query(q, skip, limit)


def create_risk_stratification(db: Session, data: dict) -> dict:
    rs = RiskStratification(**data)
    db.add(rs)
    db.commit()
    db.refresh(rs)
    return rs.to_dict()


def list_risk_stratifications(
    db: Session, patient_id: str | None = None, lab_id: int | None = None,
    skip: int = 0, limit: int = 50,
) -> dict:
    q = db.query(RiskStratification).filter(RiskStratification.is_deleted.is_(False))
    if patient_id:
        q = q.filter(RiskStratification.patient_id == patient_id)
    q = _apply_lab_filter(q, RiskStratification, lab_id)
    return _paginated_query(q, skip, limit)


def create_self_monitoring_record(db: Session, data: dict) -> dict:
    smr = SelfMonitoringRecord(**data)
    db.add(smr)
    db.commit()
    db.refresh(smr)
    return smr.to_dict()


# =============================================================================
# MATERNAL & CHILD HEALTH
# =============================================================================


def create_pregnancy_record(db: Session, data: dict) -> dict:
    pr = PregnancyRecord(**data)
    db.add(pr)
    db.commit()
    db.refresh(pr)
    return pr.to_dict()


def get_pregnancy_record(db: Session, pregnancy_id: str) -> dict | None:
    pr = db.query(PregnancyRecord).filter(
        PregnancyRecord.id == pregnancy_id, PregnancyRecord.is_deleted.is_(False),
    ).first()
    return pr.to_dict() if pr else None


def list_pregnancy_records(
    db: Session, patient_id: str | None = None, lab_id: int | None = None,
    skip: int = 0, limit: int = 50,
) -> dict:
    q = db.query(PregnancyRecord).filter(PregnancyRecord.is_deleted.is_(False))
    if patient_id:
        q = q.filter(PregnancyRecord.patient_id == patient_id)
    q = _apply_lab_filter(q, PregnancyRecord, lab_id)
    return _paginated_query(q, skip, limit)


def create_antenatal_care_visit(db: Session, data: dict) -> dict:
    anc = AntenatalCareVisit(**data)
    db.add(anc)
    db.commit()

    pregnancy = db.query(PregnancyRecord).filter(
        PregnancyRecord.id == anc.pregnancy_id,
    ).first()
    if pregnancy:
        pregnancy.anc_visits_completed = (pregnancy.anc_visits_completed or 0) + 1
        db.commit()

    db.refresh(anc)
    return anc.to_dict()


def create_delivery_record(db: Session, data: dict) -> dict:
    dr = DeliveryRecord(**data)
    db.add(dr)
    db.commit()

    pregnancy = db.query(PregnancyRecord).filter(
        PregnancyRecord.id == dr.pregnancy_id,
    ).first()
    if pregnancy:
        pregnancy.status = PregnancyStatus.POSTPARTUM
        pregnancy.delivery_date = dr.delivery_date
        pregnancy.is_completed = True
        db.commit()

    db.refresh(dr)
    return dr.to_dict()


def create_postnatal_care_visit(db: Session, data: dict) -> dict:
    pnc = PostnatalCareVisit(**data)
    db.add(pnc)
    db.commit()
    db.refresh(pnc)
    return pnc.to_dict()


def create_growth_monitoring(db: Session, data: dict) -> dict:
    gm = GrowthMonitoring(**data)
    db.add(gm)
    db.commit()
    db.refresh(gm)
    return gm.to_dict()


def create_breastfeeding_record(db: Session, data: dict) -> dict:
    bf = BreastfeedingRecord(**data)
    db.add(bf)
    db.commit()
    db.refresh(bf)
    return bf.to_dict()


def create_child_development_record(db: Session, data: dict) -> dict:
    cdr = ChildDevelopmentRecord(**data)
    db.add(cdr)
    db.commit()
    db.refresh(cdr)
    return cdr.to_dict()


# =============================================================================
# IMMUNISATION
# =============================================================================


def create_vaccination_record(db: Session, data: dict) -> dict:
    vr = VaccinationRecord(**data)
    db.add(vr)
    db.commit()
    db.refresh(vr)

    schedule = db.query(ImmunizationSchedule).filter(
        ImmunizationSchedule.id == vr.schedule_id,
    ).first() if vr.schedule_id else None
    if schedule:
        schedule.status = VaccinationStatus.GIVEN
        schedule.administered_at = vr.administration_date
        db.commit()

    inventory = db.query(VaccineInventory).filter(
        VaccineInventory.id == vr.vaccine_stock_id,
    ).first() if vr.vaccine_stock_id else None
    if inventory:
        inventory.quantity_available = max(0, (inventory.quantity_available or 0) - 1)
        inventory.quantity_administered = (inventory.quantity_administered or 0) + 1
        db.commit()

    return vr.to_dict()


def list_vaccination_records(
    db: Session, patient_id: str | None = None, lab_id: int | None = None,
    skip: int = 0, limit: int = 50,
) -> dict:
    q = db.query(VaccinationRecord).filter(VaccinationRecord.is_deleted.is_(False))
    if patient_id:
        q = q.filter(VaccinationRecord.patient_id == patient_id)
    q = _apply_lab_filter(q, VaccinationRecord, lab_id)
    return _paginated_query(q, skip, limit)


def create_immunization_schedule(db: Session, data: dict) -> dict:
    sched = ImmunizationSchedule(**data)
    db.add(sched)
    db.commit()
    db.refresh(sched)
    return sched.to_dict()


def list_immunization_schedules(
    db: Session, patient_id: str | None = None, lab_id: int | None = None,
    skip: int = 0, limit: int = 50,
) -> dict:
    q = db.query(ImmunizationSchedule).filter(ImmunizationSchedule.is_deleted.is_(False))
    if patient_id:
        q = q.filter(ImmunizationSchedule.patient_id == patient_id)
    q = _apply_lab_filter(q, ImmunizationSchedule, lab_id)
    return _paginated_query(q, skip, limit)


def get_missed_vaccinations(db: Session, lab_id: int | None = None) -> dict:
    q = db.query(ImmunizationSchedule).filter(
        ImmunizationSchedule.is_deleted.is_(False),
        ImmunizationSchedule.status.in_([VaccinationStatus.SCHEDULED, VaccinationStatus.OVERDUE]),
        ImmunizationSchedule.due_date < _today(),
    )
    q = _apply_lab_filter(q, ImmunizationSchedule, lab_id)
    overdue = q.all()
    return {
        "total_missed": len(overdue),
        "items": [s.to_dict() for s in overdue],
    }


def create_reminder_schedule(db: Session, data: dict) -> dict:
    rs = ReminderSchedule(**data)
    db.add(rs)
    db.commit()
    db.refresh(rs)
    return rs.to_dict()


def get_immunization_coverage(db: Session, lab_id: int | None = None) -> dict:
    q = db.query(VaccinationRecord).filter(VaccinationRecord.is_deleted.is_(False))
    q = _apply_lab_filter(q, VaccinationRecord, lab_id)

    total_vaccinations = q.count()
    by_vaccine = {}
    for vr in q.all():
        code = vr.vaccine_code or "unknown"
        by_vaccine[code] = by_vaccine.get(code, 0) + 1

    unique_patients = (
        db.query(func.count(func.distinct(VaccinationRecord.patient_id)))
        .filter(VaccinationRecord.is_deleted.is_(False))
    )
    q_pat = _apply_lab_filter(unique_patients, VaccinationRecord, lab_id)
    patients_vaccinated = q_pat.scalar() or 0

    return {
        "total_vaccinations": total_vaccinations,
        "unique_patients_vaccinated": patients_vaccinated,
        "by_vaccine_code": by_vaccine,
    }


def create_cold_chain_monitor(db: Session, data: dict) -> dict:
    ccm = ColdChainMonitor(**data)
    db.add(ccm)
    db.commit()
    db.refresh(ccm)
    return ccm.to_dict()


# =============================================================================
# PUBLIC HEALTH
# =============================================================================


def create_health_program(db: Session, data: dict) -> dict:
    hp = HealthProgram(**data)
    db.add(hp)
    db.commit()
    db.refresh(hp)
    return hp.to_dict()


def list_health_programs(
    db: Session, lab_id: int | None = None, skip: int = 0, limit: int = 50,
) -> dict:
    q = db.query(HealthProgram).filter(HealthProgram.is_deleted.is_(False))
    q = _apply_lab_filter(q, HealthProgram, lab_id)
    return _paginated_query(q, skip, limit)


def create_program_enrollment(db: Session, data: dict) -> dict:
    pe = ProgramEnrollment(**data)
    db.add(pe)
    db.commit()
    db.refresh(pe)
    return pe.to_dict()


def create_screening_campaign(db: Session, data: dict) -> dict:
    sc = ScreeningCampaign(**data)
    db.add(sc)
    db.commit()
    db.refresh(sc)
    return sc.to_dict()


def list_screening_campaigns(
    db: Session, lab_id: int | None = None, skip: int = 0, limit: int = 50,
) -> dict:
    q = db.query(ScreeningCampaign).filter(ScreeningCampaign.is_deleted.is_(False))
    q = _apply_lab_filter(q, ScreeningCampaign, lab_id)
    return _paginated_query(q, skip, limit)


def create_community_visit(db: Session, data: dict) -> dict:
    cv = CommunityVisit(**data)
    db.add(cv)
    db.commit()
    db.refresh(cv)
    return cv.to_dict()


def create_school_health_visit(db: Session, data: dict) -> dict:
    shv = SchoolHealthVisit(**data)
    db.add(shv)
    db.commit()
    db.refresh(shv)
    return shv.to_dict()


def create_occupational_health_record(db: Session, data: dict) -> dict:
    ohr = OccupationalHealthRecord(**data)
    db.add(ohr)
    db.commit()
    db.refresh(ohr)
    return ohr.to_dict()


def create_health_promotion_activity(db: Session, data: dict) -> dict:
    hpa = HealthPromotionActivity(**data)
    db.add(hpa)
    db.commit()
    db.refresh(hpa)
    return hpa.to_dict()


# =============================================================================
# PATIENT TASKS
# =============================================================================


def create_patient_task(db: Session, data: dict) -> dict:
    pt = PatientTask(**data)
    db.add(pt)
    db.commit()
    db.refresh(pt)
    return pt.to_dict()


def list_patient_tasks(
    db: Session,
    patient_id: str | None = None,
    status: str | None = None,
    task_type: str | None = None,
    lab_id: int | None = None,
    skip: int = 0,
    limit: int = 50,
) -> dict:
    q = db.query(PatientTask).filter(PatientTask.is_deleted.is_(False))
    if patient_id:
        q = q.filter(PatientTask.patient_id == patient_id)
    if status:
        q = q.filter(PatientTask.status == FollowUpStatus(status))
    if task_type:
        q = q.filter(PatientTask.task_type == task_type)
    q = _apply_lab_filter(q, PatientTask, lab_id)
    return _paginated_query(q, skip, limit)


def create_self_follow_up_task(db: Session, data: dict) -> dict:
    sfu = SelfFollowUpTask(**data)
    db.add(sfu)
    db.commit()
    db.refresh(sfu)
    return sfu.to_dict()


def create_educational_material_assignment(db: Session, data: dict) -> dict:
    ema = EducationalMaterialAssignment(**data)
    db.add(ema)
    db.commit()
    db.refresh(ema)
    return ema.to_dict()


# =============================================================================
# CARE GAP DETECTION
# =============================================================================


def detect_care_gaps(db: Session, patient_id: str, lab_id: int | None = None) -> dict:
    gaps = []

    overdue_follow_ups = db.query(FollowUpPlan).filter(
        FollowUpPlan.patient_id == patient_id,
        FollowUpPlan.is_deleted.is_(False),
        FollowUpPlan.status == FollowUpStatus.SCHEDULED,
        FollowUpPlan.follow_up_date < _now(),
    ).count()
    if overdue_follow_ups > 0:
        gaps.append({
            "type": "overdue_follow_up",
            "severity": "moderate",
            "count": overdue_follow_ups,
            "description": f"{overdue_follow_ups} follow-up plan(s) past due date",
        })

    missed_vaccinations = db.query(ImmunizationSchedule).filter(
        ImmunizationSchedule.patient_id == patient_id,
        ImmunizationSchedule.is_deleted.is_(False),
        ImmunizationSchedule.due_date < _today(),
        ImmunizationSchedule.status.in_([VaccinationStatus.SCHEDULED, VaccinationStatus.OVERDUE]),
    ).count()
    if missed_vaccinations > 0:
        gaps.append({
            "type": "missed_vaccination",
            "severity": "high",
            "count": missed_vaccinations,
            "description": f"{missed_vaccinations} vaccination(s) overdue",
        })

    uncontrolled_chronic = db.query(ChronicDiseaseRegistry).filter(
        ChronicDiseaseRegistry.patient_id == patient_id,
        ChronicDiseaseRegistry.is_deleted.is_(False),
        ChronicDiseaseRegistry.is_controlled.is_(False),
        ChronicDiseaseRegistry.status == CareProgramStatus.ACTIVE,
    ).count()
    if uncontrolled_chronic > 0:
        gaps.append({
            "type": "uncontrolled_chronic_disease",
            "severity": "high",
            "count": uncontrolled_chronic,
            "description": f"{uncontrolled_chronic} uncontrolled chronic condition(s) requiring review",
        })

    overdue_anc = db.query(PregnancyRecord).filter(
        PregnancyRecord.patient_id == patient_id,
        PregnancyRecord.is_deleted.is_(False),
        PregnancyRecord.status.notin_([PregnancyStatus.POSTPARTUM]),
        PregnancyRecord.anc_visits_completed < PregnancyRecord.anc_visits_required,
    ).count()
    if overdue_anc > 0:
        gaps.append({
            "type": "incomplete_anc_visits",
            "severity": "high",
            "count": overdue_anc,
            "description": "Antenatal care visits incomplete",
        })

    overdue_tasks = db.query(PatientTask).filter(
        PatientTask.patient_id == patient_id,
        PatientTask.is_deleted.is_(False),
        PatientTask.status == FollowUpStatus.SCHEDULED,
        PatientTask.due_date.isnot(None),
        PatientTask.due_date < _now(),
    ).count()
    if overdue_tasks > 0:
        gaps.append({
            "type": "overdue_patient_tasks",
            "severity": "moderate",
            "count": overdue_tasks,
            "description": f"{overdue_tasks} patient task(s) past due",
        })

    return {
        "patient_id": patient_id,
        "total_gaps": len(gaps),
        "gaps": gaps,
    }


# =============================================================================
# EHR IMMUNISATION COORDINATION
# =============================================================================


def coordinate_ehr_immunization(
    db: Session, ehr_immunization_record: Any,
) -> dict:
    """Create a care-continuum VaccinationRecord from an EHR ImmunizationRecord."""
    data = {
        "patient_id": ehr_immunization_record.patient_id,
        "citizen_id": ehr_immunization_record.citizen_id,
        "encounter_id": ehr_immunization_record.encounter_id,
        "facility_id": ehr_immunization_record.facility_id,
        "administered_by": ehr_immunization_record.administrator_id or ehr_immunization_record.practitioner_id,
        "vaccine_name": ehr_immunization_record.vaccine_name,
        "vaccine_code": ehr_immunization_record.vaccine_code,
        "dose_number": ehr_immunization_record.dose_number,
        "administration_date": ehr_immunization_record.administration_date,
        "manufacturer": ehr_immunization_record.manufacturer,
        "lot_number": ehr_immunization_record.lot_number,
        "expiry_date": ehr_immunization_record.expiry_date,
        "route": ehr_immunization_record.route,
        "site": ehr_immunization_record.site,
        "adverse_event": ehr_immunization_record.adverse_event,
        "status": VaccinationStatus.GIVEN,
    }
    vr = VaccinationRecord(**data)
    db.add(vr)
    db.commit()
    db.refresh(vr)
    return vr.to_dict()

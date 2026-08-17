from app.services.route_audit import audit_route_mutation
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.security.rbac import require_role

from ..enums import (
    AIAuditAction,
    AIGuardrailType,
    AIRiskLevel,
    ClinicalPolicyType,
    ConnectorType,
    GovernanceNodeType,
    InteropProtocolType,
    LabType,
    ProductivityPeriod,
    SecurityPolicyCategory,
    ThreatSeverity,
)
from ..policies.governance_policies import (
    GovernanceAction,
    governance_policy_engine,
)
from ..services.ai_governance_service import AIGovernanceService
from ..services.clinical_governance_service import ClinicalGovernanceService
from ..services.connector_service import CitizenRegistryConnectorService
from ..services.health_number_service import HealthNumberGovernanceService
from ..services.hierarchy_service import GovernanceHierarchyService
from ..services.interoperability_service import InteroperabilityGovernanceService
from ..services.laboratory_service import LaboratoryGovernanceService
from ..services.security_governance_service import SecurityGovernanceService
from ..services.workforce_service import WorkforceGovernanceService

router = APIRouter(prefix="/governance", tags=["governance"])

admin_dep = Depends(require_role("master_admin", "ministry_admin", "national_admin"))
elevated_dep = Depends(require_role("master_admin", "ministry_admin", "national_admin", "directorate_admin"))


def _check_policy(action: GovernanceAction, user_role: str | None = None) -> None:
    decision = governance_policy_engine.evaluate(action)
    if not decision.allowed:
        raise HTTPException(status_code=403, detail=decision.reason)
    if governance_policy_engine.require_elevated_approval(action, user_role):
        raise HTTPException(status_code=403, detail=f"Action {action.value} requires elevated approval")


# ── Phase 1: Governance Hierarchy ────────────────────────────────────────────


class NodeCreate(BaseModel):
    node_type: GovernanceNodeType
    code: str = Field(..., min_length=1, max_length=100)
    name_ar: str = Field(..., min_length=1, max_length=300)
    name_en: str | None = None
    parent_id: int | None = None
    governorate: str | None = None
    district: str | None = None
    metadata_json: dict[str, Any] | None = None


@audit_route_mutation(action="route.create_node", resource_type="governance_routes")
@router.post("/nodes", dependencies=[admin_dep])
def create_node(data: NodeCreate, db: Session = Depends(get_db)):
    _check_policy(GovernanceAction.CREATE_NODE)
    svc = GovernanceHierarchyService(db)
    node = svc.create_node(
        node_type=data.node_type, code=data.code, name_ar=data.name_ar,
        name_en=data.name_en, parent_id=data.parent_id,
        governorate=data.governorate, district=data.district,
        metadata_json=data.metadata_json,
    )
    db.commit()
    return node


@router.get("/nodes/{node_id}")
def get_node(node_id: int, db: Session = Depends(get_db)):
    svc = GovernanceHierarchyService(db)
    node = svc.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="node not found")
    return node


@router.get("/nodes/{node_id}/subtree")
def get_subtree(node_id: int, db: Session = Depends(get_db)):
    svc = GovernanceHierarchyService(db)
    return svc.get_subtree(node_id)


@router.get("/nodes/{node_id}/path")
def get_path(node_id: int, db: Session = Depends(get_db)):
    svc = GovernanceHierarchyService(db)
    return svc.get_path(node_id)


@router.get("/nodes/{node_id}/children")
def get_children(node_id: int, db: Session = Depends(get_db)):
    svc = GovernanceHierarchyService(db)
    return svc.get_children(node_id)


@router.get("/nodes/by-type/{node_type}")
def get_nodes_by_type(node_type: GovernanceNodeType, db: Session = Depends(get_db)):
    GovernanceHierarchyService(db)
    from ..models.hierarchy import GovernanceNode
    return db.query(GovernanceNode).filter(GovernanceNode.node_type == node_type).all()


@audit_route_mutation(action="route.deactivate_node", resource_type="governance_routes")
@router.post("/nodes/{node_id}/deactivate", dependencies=[admin_dep])
def deactivate_node(node_id: int, db: Session = Depends(get_db)):
    _check_policy(GovernanceAction.DELETE_NODE)
    svc = GovernanceHierarchyService(db)
    node = svc.deactivate_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="node not found")
    db.commit()
    return {"status": "deactivated", "node_id": node_id}


class DelegationCreate(BaseModel):
    delegator_node_id: int
    delegate_node_id: int
    scope: dict[str, Any] | None = None
    reason: str | None = None


@audit_route_mutation(action="route.create_delegation", resource_type="governance_routes")
@router.post("/delegations", dependencies=[admin_dep])
def create_delegation(data: DelegationCreate, db: Session = Depends(get_db)):
    _check_policy(GovernanceAction.CREATE_DELEGATION)
    svc = GovernanceHierarchyService(db)
    delegation = svc.create_delegation(
        delegator_node_id=data.delegator_node_id,
        delegate_node_id=data.delegate_node_id,
        scope=data.scope, reason=data.reason,
    )
    db.commit()
    return delegation


@audit_route_mutation(action="route.revoke_delegation", resource_type="governance_routes")
@router.post("/delegations/{delegation_id}/revoke", dependencies=[admin_dep])
def revoke_delegation(delegation_id: int, db: Session = Depends(get_db)):
    _check_policy(GovernanceAction.REVOKE_DELEGATION)
    svc = GovernanceHierarchyService(db)
    delegation = svc.revoke_delegation(delegation_id)
    if not delegation:
        raise HTTPException(status_code=404, detail="delegation not found")
    db.commit()
    return {"status": "revoked", "delegation_id": delegation_id}


class ActingAppoint(BaseModel):
    node_id: int
    acting_node_id: int
    reason: str | None = None


@audit_route_mutation(action="route.create_acting_appointment", resource_type="governance_routes")
@router.post("/acting-appointments", dependencies=[admin_dep])
def create_acting_appointment(data: ActingAppoint, db: Session = Depends(get_db)):
    _check_policy(GovernanceAction.APPOINT_ACTING)
    svc = GovernanceHierarchyService(db)
    appointment = svc.create_acting_appointment(
        node_id=data.node_id, acting_node_id=data.acting_node_id, reason=data.reason,
    )
    db.commit()
    return appointment


# ── Phase 2: Health Number Governance ────────────────────────────────────────


@audit_route_mutation(action="route.issue_health_number", resource_type="governance_routes")
@router.post("/health-numbers/issue", dependencies=[elevated_dep])
def issue_health_number(citizen_ulid: str, national_id_hash: str | None = None, db: Session = Depends(get_db)):
    svc = HealthNumberGovernanceService(db)
    hn = svc.generate_health_number(citizen_ulid, national_id_hash)
    db.commit()
    return {"health_number": hn}


@router.get("/health-numbers/{health_number}")
def get_health_number(health_number: str, db: Session = Depends(get_db)):
    svc = HealthNumberGovernanceService(db)
    hn = svc.get_health_number(health_number)
    if not hn:
        raise HTTPException(status_code=404, detail="health number not found")
    return hn


@audit_route_mutation(action="route.report_lost", resource_type="governance_routes")
@router.post("/health-numbers/{health_number}/lost", dependencies=[elevated_dep])
def report_lost(health_number: str, reported_by: str, db: Session = Depends(get_db)):
    svc = HealthNumberGovernanceService(db)
    hn = svc.report_lost(health_number, reported_by)
    if not hn:
        raise HTTPException(status_code=404, detail="health number not found")
    db.commit()
    return {"status": "reported_lost"}


@audit_route_mutation(action="route.reissue_health_number", resource_type="governance_routes")
@router.post("/health-numbers/{health_number}/reissue", dependencies=[admin_dep])
def reissue_health_number(health_number: str, citizen_ulid: str, issued_by: str, db: Session = Depends(get_db)):
    svc = HealthNumberGovernanceService(db)
    new_hn = svc.reissue(health_number, citizen_ulid, issued_by)
    if not new_hn:
        raise HTTPException(status_code=404, detail="health number not found")
    db.commit()
    return {"new_health_number": new_hn}


@audit_route_mutation(action="route.merge_identity", resource_type="governance_routes")
@router.post("/health-numbers/merge", dependencies=[admin_dep])
def merge_identity(primary_hn: str, secondary_hn: str, reason: str, decision_by: str, db: Session = Depends(get_db)):
    _check_policy(GovernanceAction.MERGE_IDENTITY)
    svc = HealthNumberGovernanceService(db)
    merge = svc.merge_identities(primary_hn, secondary_hn, reason, decision_by)
    db.commit()
    return merge


@audit_route_mutation(action="route.split_identity", resource_type="governance_routes")
@router.post("/health-numbers/split", dependencies=[admin_dep])
def split_identity(primary_hn: str, new_hn: str, reason: str, decision_by: str, db: Session = Depends(get_db)):
    _check_policy(GovernanceAction.SPLIT_IDENTITY)
    svc = HealthNumberGovernanceService(db)
    split = svc.split_identity(primary_hn, new_hn, reason, decision_by)
    db.commit()
    return split


@router.get("/health-numbers/{health_number}/history")
def get_health_number_history(health_number: str, db: Session = Depends(get_db)):
    svc = HealthNumberGovernanceService(db)
    return svc.get_history(health_number)


# ── Phase 3: Citizen Registry Connectors ─────────────────────────────────────


@router.get("/connectors/{connector_type}/lookup", dependencies=[elevated_dep])
def connector_lookup(connector_type: ConnectorType, query: str = Query(...), db: Session = Depends(get_db)):
    svc = CitizenRegistryConnectorService(db)
    return svc.lookup(connector_type, {"query": query})


@router.get("/connectors/{connector_type}/verify", dependencies=[elevated_dep])
def connector_verify(connector_type: ConnectorType, db: Session = Depends(get_db)):
    svc = CitizenRegistryConnectorService(db)
    return svc.verify(connector_type, {})


@router.get("/connectors")
def list_connectors():
    return {"connectors": [c.value for c in ConnectorType]}


# ── Phase 4: Healthcare Worker Governance ────────────────────────────────────


class WorkerCreate(BaseModel):
    employee_code: str
    full_name_ar: str
    profession: str
    full_name_en: str | None = None
    national_id_hash: str | None = None
    specialization: str | None = None
    organization_node_id: int | None = None
    department: str | None = None
    unit: str | None = None
    employment_date: date | None = None
    contact_phone: str | None = None
    contact_email: str | None = None


@audit_route_mutation(action="route.register_worker", resource_type="governance_routes")
@router.post("/workers", dependencies=[elevated_dep])
def register_worker(data: WorkerCreate, db: Session = Depends(get_db)):
    svc = WorkforceGovernanceService(db)
    worker = svc.register_worker(
        employee_code=data.employee_code, full_name_ar=data.full_name_ar,
        profession=data.profession, full_name_en=data.full_name_en,
        national_id_hash=data.national_id_hash, specialization=data.specialization,
        organization_node_id=data.organization_node_id, department=data.department,
        unit=data.unit, employment_date=data.employment_date,
        contact_phone=data.contact_phone, contact_email=data.contact_email,
    )
    db.commit()
    return worker


@router.get("/workers/{worker_id}")
def get_worker(worker_id: int, db: Session = Depends(get_db)):
    svc = WorkforceGovernanceService(db)
    worker = svc.get_worker(worker_id)
    if not worker:
        raise HTTPException(status_code=404, detail="worker not found")
    return worker


@router.get("/workers/by-node/{node_id}")
def get_workers_by_node(node_id: int, db: Session = Depends(get_db)):
    svc = WorkforceGovernanceService(db)
    return svc.get_workers_by_node(node_id)


@audit_route_mutation(action="route.add_license", resource_type="governance_routes")
@router.post("/workers/{worker_id}/licenses", dependencies=[elevated_dep])
def add_license(worker_id: int, license_number: str, license_type: str, issuing_authority: str, issued_date: date, expiry_date: date | None = None, db: Session = Depends(get_db)):
    svc = WorkforceGovernanceService(db)
    lic = svc.add_license(worker_id, license_number, license_type, issuing_authority, issued_date, expiry_date)
    db.commit()
    return lic


@audit_route_mutation(action="route.add_board_certification", resource_type="governance_routes")
@router.post("/workers/{worker_id}/board-certifications", dependencies=[elevated_dep])
def add_board_certification(worker_id: int, board_name: str, specialty: str, issuing_body: str, issued_date: date, db: Session = Depends(get_db)):
    svc = WorkforceGovernanceService(db)
    board = svc.add_board_certification(worker_id, board_name, specialty, issuing_body, issued_date)
    db.commit()
    return board


@audit_route_mutation(action="route.add_training", resource_type="governance_routes")
@router.post("/workers/{worker_id}/trainings")
def add_training(worker_id: int, training_name: str, training_type: str, completed: bool = False, db: Session = Depends(get_db)):
    svc = WorkforceGovernanceService(db)
    training = svc.add_training(worker_id, training_name, training_type, completed=completed)
    db.commit()
    return training


@audit_route_mutation(action="route.assess_competency", resource_type="governance_routes")
@router.post("/workers/{worker_id}/competencies")
def assess_competency(worker_id: int, competency_name: str, level: str, db: Session = Depends(get_db)):
    svc = WorkforceGovernanceService(db)
    from ..enums import CompetencyLevel
    assessment = svc.assess_competency(worker_id, competency_name, CompetencyLevel(level))
    db.commit()
    return assessment


@audit_route_mutation(action="route.record_productivity", resource_type="governance_routes")
@router.post("/workers/{worker_id}/productivity")
def record_productivity(
    worker_id: int,
    period: ProductivityPeriod,
    period_start: date,
    period_end: date,
    tests_performed: int = 0,
    quality_score: float | None = None,
    db: Session = Depends(get_db),
):
    svc = WorkforceGovernanceService(db)
    rec = svc.record_productivity(worker_id, period, period_start, period_end, tests_performed=tests_performed, quality_score=quality_score)
    db.commit()
    return rec


@router.get("/workers/{worker_id}/productivity")
def get_productivity(worker_id: int, period: ProductivityPeriod | None = None, db: Session = Depends(get_db)):
    svc = WorkforceGovernanceService(db)
    return svc.get_productivity(worker_id, period)


@router.get("/workers/ranking")
def get_national_ranking(period: ProductivityPeriod, period_start: date, period_end: date, limit: int = 100, db: Session = Depends(get_db)):
    svc = WorkforceGovernanceService(db)
    return svc.get_national_ranking(period, period_start, period_end, limit)


@router.get("/workers/{worker_id}/stats")
def get_worker_stats(worker_id: int, db: Session = Depends(get_db)):
    svc = WorkforceGovernanceService(db)
    return svc.get_worker_stats(worker_id)


# ── Phase 5: National Laboratory Governance ──────────────────────────────────


class LabRegister(BaseModel):
    lab_code: str
    name_ar: str
    lab_type: LabType
    name_en: str | None = None
    organization_node_id: int | None = None
    license_number: str | None = None
    governorate: str | None = None


@audit_route_mutation(action="route.register_lab", resource_type="governance_routes")
@router.post("/laboratories", dependencies=[elevated_dep])
def register_lab(data: LabRegister, db: Session = Depends(get_db)):
    _check_policy(GovernanceAction.REGISTER_LAB)
    svc = LaboratoryGovernanceService(db)
    lab = svc.register_lab(
        lab_code=data.lab_code, name_ar=data.name_ar, lab_type=data.lab_type,
        name_en=data.name_en, organization_node_id=data.organization_node_id,
        license_number=data.license_number, governorate=data.governorate,
    )
    db.commit()
    return lab


@router.get("/laboratories")
def list_labs(lab_type: LabType | None = None, governorate: str | None = None, db: Session = Depends(get_db)):
    svc = LaboratoryGovernanceService(db)
    return svc.list_labs(lab_type, governorate)


@router.get("/laboratories/{lab_id}")
def get_lab(lab_id: int, db: Session = Depends(get_db)):
    svc = LaboratoryGovernanceService(db)
    lab = svc.get_lab(lab_id)
    if not lab:
        raise HTTPException(status_code=404, detail="lab not found")
    return lab


@router.get("/laboratories/{lab_id}/stats")
def get_lab_stats(lab_id: int, db: Session = Depends(get_db)):
    svc = LaboratoryGovernanceService(db)
    return svc.get_lab_stats(lab_id)


@audit_route_mutation(action="route.register_equipment", resource_type="governance_routes")
@router.post("/laboratories/{lab_id}/equipment", dependencies=[elevated_dep])
def register_equipment(lab_id: int, equipment_code: str, name_ar: str, category: str, manufacturer: str | None = None, model: str | None = None, db: Session = Depends(get_db)):
    svc = LaboratoryGovernanceService(db)
    equip = svc.register_equipment(lab_id, equipment_code, name_ar, category, manufacturer=manufacturer, model=model)
    db.commit()
    return equip


@audit_route_mutation(action="route.register_analyzer", resource_type="governance_routes")
@router.post("/laboratories/{lab_id}/analyzers", dependencies=[elevated_dep])
def register_analyzer(lab_id: int, analyzer_code: str, name_ar: str, analyzer_type: str, manufacturer: str | None = None, model: str | None = None, db: Session = Depends(get_db)):
    svc = LaboratoryGovernanceService(db)
    analyzer = svc.register_analyzer(lab_id, analyzer_code, name_ar, analyzer_type, manufacturer=manufacturer, model=model)
    db.commit()
    return analyzer


@audit_route_mutation(action="route.record_qc", resource_type="governance_routes")
@router.post("/laboratories/{lab_id}/qc", dependencies=[elevated_dep])
def record_qc(lab_id: int, test_code: str, control_level: str, result_value: float, mean: float, sd: float, db: Session = Depends(get_db)):
    svc = LaboratoryGovernanceService(db)
    qc = svc.record_qc(lab_id, test_code, control_level, result_value, mean=mean, sd=sd)
    db.commit()
    return qc


@audit_route_mutation(action="route.record_eqa", resource_type="governance_routes")
@router.post("/laboratories/{lab_id}/eqa", dependencies=[elevated_dep])
def record_eqa(lab_id: int, test_code: str, scheme_name: str, round_number: str, target_value: float, submitted_result: float, db: Session = Depends(get_db)):
    svc = LaboratoryGovernanceService(db)
    eqa = svc.record_eqa(lab_id, test_code, scheme_name, round_number, submitted_result=submitted_result, target_value=target_value)
    db.commit()
    return eqa


@audit_route_mutation(action="route.add_reagent", resource_type="governance_routes")
@router.post("/laboratories/{lab_id}/reagents", dependencies=[elevated_dep])
def add_reagent(lab_id: int, reagent_code: str, reagent_name_ar: str, quantity: float, unit: str, lot_number: str | None = None, minimum_stock_level: float | None = None, db: Session = Depends(get_db)):
    svc = LaboratoryGovernanceService(db)
    reagent = svc.manage_reagent(lab_id, reagent_code, reagent_name_ar, quantity, unit, lot_number=lot_number, minimum_stock_level=minimum_stock_level)
    db.commit()
    return reagent


@router.get("/laboratories/{lab_id}/low-stock")
def get_low_stock(lab_id: int, db: Session = Depends(get_db)):
    svc = LaboratoryGovernanceService(db)
    return svc.get_low_stock_reagents(lab_id)


@router.get("/national-tests")
def get_national_tests(db: Session = Depends(get_db)):
    from ..models.laboratory import NationalTestDefinition
    return db.query(NationalTestDefinition).filter(NationalTestDefinition.is_active.is_(True)).all()


@audit_route_mutation(action="route.define_national_test", resource_type="governance_routes")
@router.post("/national-tests", dependencies=[admin_dep])
def define_national_test(test_code: str, name_ar: str, category: str, is_national_essential: bool = False, db: Session = Depends(get_db)):
    svc = LaboratoryGovernanceService(db)
    test = svc.define_national_test(test_code, name_ar, category, is_national_essential=is_national_essential)
    db.commit()
    return test


@audit_route_mutation(action="route.designate_reference_lab", resource_type="governance_routes")
@router.post("/reference-labs", dependencies=[admin_dep])
def designate_reference_lab(lab_id: int, reference_domain: str, is_national: bool = False, db: Session = Depends(get_db)):
    _check_policy(GovernanceAction.DESIGNATE_REFERENCE)
    svc = LaboratoryGovernanceService(db)
    ref = svc.designate_reference_lab(lab_id, reference_domain, is_national=is_national)
    db.commit()
    return ref


# ── Phase 6: Clinical Governance ─────────────────────────────────────────────


@audit_route_mutation(action="route.create_clinical_policy", resource_type="governance_routes")
@router.post("/clinical-policies", dependencies=[admin_dep])
def create_clinical_policy(policy_code: str, title_ar: str, policy_type: ClinicalPolicyType, content_ar: str, db: Session = Depends(get_db)):
    svc = ClinicalGovernanceService(db)
    policy = svc.create_policy(policy_code, title_ar, policy_type, content_ar)
    db.commit()
    return policy


@router.get("/clinical-policies")
def get_clinical_policies(policy_type: ClinicalPolicyType | None = None, db: Session = Depends(get_db)):
    svc = ClinicalGovernanceService(db)
    return svc.get_active_policies(policy_type)


@audit_route_mutation(action="route.set_critical_result_policy", resource_type="governance_routes")
@router.post("/critical-result-policies", dependencies=[admin_dep])
def set_critical_result_policy(test_code: str, test_name_ar: str, critical_low: str | None = None, critical_high: str | None = None, db: Session = Depends(get_db)):
    svc = ClinicalGovernanceService(db)
    policy = svc.set_critical_result_policy(test_code, test_name_ar, critical_low=critical_low, critical_high=critical_high)
    db.commit()
    return policy


@audit_route_mutation(action="route.set_reference_range", resource_type="governance_routes")
@router.post("/reference-ranges", dependencies=[admin_dep])
def set_reference_range(test_code: str, low: str, high: str, unit: str, gender: str | None = None, db: Session = Depends(get_db)):
    svc = ClinicalGovernanceService(db)
    rr = svc.set_reference_range(test_code, low=low, high=high, unit=unit, gender=gender)
    db.commit()
    return rr


@audit_route_mutation(action="route.set_westgard_policy", resource_type="governance_routes")
@router.post("/westgard-policies", dependencies=[admin_dep])
def set_westgard_policy(test_code: str, rules: list[str], db: Session = Depends(get_db)):
    svc = ClinicalGovernanceService(db)
    wp = svc.set_westgard_policy(test_code, rules)
    db.commit()
    return wp


@audit_route_mutation(action="route.set_delta_check_policy", resource_type="governance_routes")
@router.post("/delta-check-policies", dependencies=[admin_dep])
def set_delta_check_policy(test_code: str, delta_percent: float, time_window_hours: int, action: str, db: Session = Depends(get_db)):
    svc = ClinicalGovernanceService(db)
    dp = svc.set_delta_check_policy(test_code, delta_percent, time_window_hours, action)
    db.commit()
    return dp


@audit_route_mutation(action="route.create_approval_policy", resource_type="governance_routes")
@router.post("/approval-policies", dependencies=[admin_dep])
def create_approval_policy(policy_code: str, title_ar: str, context: str, db: Session = Depends(get_db)):
    svc = ClinicalGovernanceService(db)
    ap = svc.create_approval_policy(policy_code, title_ar, context)
    db.commit()
    return ap


# ── Phase 8: Security Governance ─────────────────────────────────────────────


@audit_route_mutation(action="route.create_security_policy", resource_type="governance_routes")
@router.post("/security-policies", dependencies=[admin_dep])
def create_security_policy(policy_code: str, title_ar: str, category: SecurityPolicyCategory, content_ar: str, db: Session = Depends(get_db)):
    svc = SecurityGovernanceService(db)
    sp = svc.create_security_policy(policy_code, title_ar, category, content_ar)
    db.commit()
    return sp


@audit_route_mutation(action="route.create_break_glass_policy", resource_type="governance_routes")
@router.post("/break-glass-policies", dependencies=[admin_dep])
def create_break_glass_policy(policy_code: str, title_ar: str, allowed_reasons: list[str], db: Session = Depends(get_db)):
    svc = SecurityGovernanceService(db)
    bg = svc.create_break_glass_policy(policy_code, title_ar, allowed_reasons)
    db.commit()
    return bg


@audit_route_mutation(action="route.log_audit_event", resource_type="governance_routes")
@router.post("/audit-events")
def log_audit_event(event_type: str, actor_id: str, action: str, severity: ThreatSeverity = ThreatSeverity.LOW, db: Session = Depends(get_db)):
    svc = SecurityGovernanceService(db)
    event = svc.log_audit_event(event_type, actor_id=actor_id, action=action, severity=severity)
    db.commit()
    return event


@router.get("/audit-events")
def get_audit_events(event_type: str | None = None, limit: int = 50, db: Session = Depends(get_db)):
    from ..models.security import NationalAuditEvent
    q = db.query(NationalAuditEvent)
    if event_type:
        q = q.filter(NationalAuditEvent.event_type == event_type)
    return q.order_by(NationalAuditEvent.created_at.desc()).limit(limit).all()


@audit_route_mutation(action="route.create_incident", resource_type="governance_routes")
@router.post("/incidents", dependencies=[admin_dep])
def create_incident(incident_id: str, title: str, category: str, severity: ThreatSeverity, db: Session = Depends(get_db)):
    svc = SecurityGovernanceService(db)
    incident = svc.create_incident(incident_id, title, severity, category)
    db.commit()
    return incident


@audit_route_mutation(action="route.register_risk", resource_type="governance_routes")
@router.post("/risks", dependencies=[admin_dep])
def register_risk(risk_id: str, title_ar: str, category: str, likelihood: int, impact: int, db: Session = Depends(get_db)):
    svc = SecurityGovernanceService(db)
    risk = svc.register_risk(risk_id, title_ar, category, likelihood, impact)
    db.commit()
    return risk


@audit_route_mutation(action="route.classify_data", resource_type="governance_routes")
@router.post("/data-classification", dependencies=[admin_dep])
def classify_data(data_type: str, name_ar: str, classification_level: str, pii: bool = False, phi: bool = False, db: Session = Depends(get_db)):
    _check_policy(GovernanceAction.CLASSIFY_DATA)
    from ..enums import DataClassificationLevel
    svc = SecurityGovernanceService(db)
    dc = svc.classify_data(data_type, name_ar, DataClassificationLevel(classification_level), pii=pii, phi=phi)
    db.commit()
    return dc


@audit_route_mutation(action="route.register_certificate", resource_type="governance_routes")
@router.post("/certificates", dependencies=[admin_dep])
def register_certificate(certificate_id: str, common_name: str, issuer: str, type: str, issued_date: date, expiry_date: date, db: Session = Depends(get_db)):
    svc = SecurityGovernanceService(db)
    cert = svc.register_certificate(certificate_id, common_name, issuer, type, issued_date, expiry_date)
    db.commit()
    return cert


# ── Phase 9: Interoperability Governance ─────────────────────────────────────


@audit_route_mutation(action="route.register_protocol", resource_type="governance_routes")
@router.post("/interop-protocols", dependencies=[admin_dep])
def register_protocol(protocol_code: str, name_ar: str, protocol_type: InteropProtocolType, is_mandatory: bool = False, db: Session = Depends(get_db)):
    svc = InteroperabilityGovernanceService(db)
    proto = svc.register_protocol(protocol_code, name_ar, protocol_type, is_mandatory=is_mandatory)
    db.commit()
    return proto


@router.get("/interop-protocols")
def list_protocols(protocol_type: InteropProtocolType | None = None, db: Session = Depends(get_db)):
    svc = InteroperabilityGovernanceService(db)
    return svc.list_active_protocols(protocol_type)


@audit_route_mutation(action="route.create_terminology_mapping", resource_type="governance_routes")
@router.post("/terminology-mappings", dependencies=[admin_dep])
def create_terminology_mapping(source_system: str, source_code: str, target_system: str, target_code: str, db: Session = Depends(get_db)):
    svc = InteroperabilityGovernanceService(db)
    mapping = svc.create_terminology_mapping(source_system, source_code, target_system, target_code)
    db.commit()
    return mapping


@router.get("/terminology-mappings")
def lookup_terminology(source_system: str, source_code: str, db: Session = Depends(get_db)):
    svc = InteroperabilityGovernanceService(db)
    return svc.lookup_terminology(source_system, source_code)


# ── Phase 10: AI Governance ──────────────────────────────────────────────────


@audit_route_mutation(action="route.create_guardrail", resource_type="governance_routes")
@router.post("/ai/guardrails", dependencies=[admin_dep])
def create_guardrail(guardrail_code: str, name_ar: str, guardrail_type: AIGuardrailType, rules: dict, db: Session = Depends(get_db)):
    svc = AIGovernanceService(db)
    g = svc.create_guardrail(guardrail_code, name_ar, guardrail_type, rules)
    db.commit()
    return g


@audit_route_mutation(action="route.create_llm_policy", resource_type="governance_routes")
@router.post("/ai/llm-policies", dependencies=[admin_dep])
def create_llm_policy(policy_code: str, name_ar: str, llm_provider: str, model_name: str, requires_human_review: bool = False, db: Session = Depends(get_db)):
    svc = AIGovernanceService(db)
    lp = svc.create_llm_policy(policy_code, name_ar, llm_provider, model_name, requires_human_review=requires_human_review)
    db.commit()
    return lp


@audit_route_mutation(action="route.log_ai_audit", resource_type="governance_routes")
@router.post("/ai/audit", dependencies=[elevated_dep])
def log_ai_audit(action: AIAuditAction, model_name: str, prompt: str | None = None, response: str | None = None, risk_level: AIRiskLevel | None = None, db: Session = Depends(get_db)):
    svc = AIGovernanceService(db)
    audit = svc.log_ai_audit(action, model_name, prompt=prompt, response=response, risk_level=risk_level)
    db.commit()
    return audit


@audit_route_mutation(action="route.validate_ai_model", resource_type="governance_routes")
@router.post("/ai/validate", dependencies=[admin_dep])
def validate_ai_model(model_name: str, validation_type: str, passed: bool, accuracy: float | None = None, db: Session = Depends(get_db)):
    svc = AIGovernanceService(db)
    validation = svc.validate_model(model_name, validation_type, accuracy=accuracy, passed=passed)
    db.commit()
    return validation


@router.get("/ai/risk/{model_name}")
def get_model_risk(model_name: str, db: Session = Depends(get_db)):
    svc = AIGovernanceService(db)
    risk = svc.get_model_risk(model_name)
    if not risk:
        raise HTTPException(status_code=404, detail="model risk classification not found")
    return risk


# ── Policy Engine ────────────────────────────────────────────────────────────


@router.get("/policy/evaluate")
def evaluate_governance_action(action: GovernanceAction, context: str | None = None):
    return governance_policy_engine.evaluate(action, {"context": context} if context else None)


# ── Governance Health ─────────────────────────────────────────────────────────


@router.get("/health")
def governance_health():
    return {
        "status": "operational",
        "layer": "national_governance",
        "domains": [
            "hierarchy", "health_number", "connectors", "workforce",
            "laboratory", "clinical", "analytics", "security",
            "interoperability", "ai",
        ],
        "version": "1.0.0",
    }

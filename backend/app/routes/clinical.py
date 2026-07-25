from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.clinical.terminology.models import (
    TerminologyCode,
    ValueSet,
)
from app.database import get_db
from app.models.lab_user import LabUser
from app.security.dependencies import get_current_user
from app.services.clinical_service import (
    CDSService,
    ClinicalAIService,
    ClinicalKnowledgeService,
    QualityService,
    ResearchService,
    TerminologyService,
)

logger = logging.getLogger("gula.routes.clinical")

router = APIRouter(prefix="/clinical", tags=["clinical"])


# ==============================================================================
# Terminology Routes
# ==============================================================================


class TerminologyCodeCreate(BaseModel):
    code: str = Field(..., max_length=64)
    display: str = Field(..., max_length=512)
    system: str = Field(..., description="TerminologySystem enum value")
    version_id: str | None = None
    parent_id: str | None = None
    definition: str | None = None
    is_leaf: bool = True
    effective_date: str | None = None
    status: str = "active"


class TerminologyCodeUpdate(BaseModel):
    display: str | None = None
    definition: str | None = None
    is_leaf: bool | None = None
    status: str | None = None


class TerminologyVersionCreate(BaseModel):
    system: str
    version: str = Field(..., max_length=64)
    release_date: str | None = None
    description: str | None = None
    is_current: bool = False
    codes_count: int = 0


class TerminologyMappingCreate(BaseModel):
    source_system: str
    source_code_id: str
    target_system: str
    target_code_id: str
    relationship: str = "equivalent"
    mapping_priority: int = 0
    evidence: str | None = None


class ValueSetCreate(BaseModel):
    name: str = Field(..., max_length=256)
    oid: str | None = None
    description: str | None = None
    purpose: str | None = None
    is_extensible: bool = True
    is_experimental: bool = False
    steward: str | None = None
    source: str | None = None
    version: str | None = None
    effective_start: str | None = None
    effective_end: str | None = None


class ValueSetMemberCreate(BaseModel):
    value_set_id: str
    code_id: str
    inclusion: bool = True
    order: int = 0


class CodeSystemCreate(BaseModel):
    name: str = Field(..., max_length=128)
    system: str
    uri: str | None = None
    oid: str | None = None
    description: str | None = None
    publisher: str | None = None
    contact: str | None = None
    copyright: str | None = None
    version: str | None = None
    total_codes: int = 0
    is_case_sensitive: bool = True
    hierarchy_meaning: str | None = None


@router.get("/terminology/codes")
def search_terminology_codes(
    q: str | None = Query(None, description="Search query"),
    system: str | None = None,
    status: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items, total = TerminologyService.search_codes(
        db,
        query=q,
        system=system,
        status=status,
        skip=skip,
        limit=limit,
    )
    return {"items": [c.to_dict() for c in items], "total": total, "skip": skip, "limit": limit}


@router.post("/terminology/codes", status_code=201)
def create_terminology_code(
    data: TerminologyCodeCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    obj = TerminologyService.create_code(db, data.model_dump(exclude_none=True))
    return obj.to_dict()


@router.get("/terminology/codes/{code_id}")
def get_terminology_code(
    code_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    obj = TerminologyService.get_code(db, code_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Terminology code not found")
    return obj.to_dict()


@router.put("/terminology/codes/{code_id}")
def update_terminology_code(
    code_id: str,
    data: TerminologyCodeUpdate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    obj = TerminologyService.update_code(db, code_id, data.model_dump(exclude_none=True))
    if not obj:
        raise HTTPException(status_code=404, detail="Terminology code not found")
    return obj.to_dict()


@router.delete("/terminology/codes/{code_id}")
def delete_terminology_code(
    code_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ok = TerminologyService.delete_code(db, code_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Terminology code not found")
    return {"detail": "Terminology code deleted"}


@router.get("/terminology/versions")
def list_terminology_versions(
    system: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items, total = TerminologyService.get_versions(db, system=system, skip=skip, limit=limit)
    return {"items": [v.to_dict() for v in items], "total": total}


@router.post("/terminology/versions", status_code=201)
def create_terminology_version(
    data: TerminologyVersionCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    obj = TerminologyService.create_version(db, data.model_dump(exclude_none=True))
    return obj.to_dict()


@router.post("/terminology/mappings", status_code=201)
def create_terminology_mapping(
    data: TerminologyMappingCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    obj = TerminologyService.create_mapping(db, data.model_dump(exclude_none=True))
    return obj.to_dict()


@router.get("/terminology/value-sets")
def list_value_sets(
    name: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items, total = TerminologyService.get_value_sets(db, name=name, skip=skip, limit=limit)
    return {"items": [v.to_dict() for v in items], "total": total}


@router.post("/terminology/value-sets", status_code=201)
def create_value_set(
    data: ValueSetCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    obj = TerminologyService.create_value_set(db, data.model_dump(exclude_none=True))
    return obj.to_dict()


@router.post("/terminology/value-set-members", status_code=201)
def create_value_set_member(
    data: ValueSetMemberCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    obj = TerminologyService.create_value_set_member(db, data.model_dump(exclude_none=True))
    return obj.to_dict()


@router.get("/terminology/code-systems")
def list_code_systems(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items, total = TerminologyService.get_code_systems(db, skip=skip, limit=limit)
    return {"items": [c.to_dict() for c in items], "total": total}


@router.post("/terminology/code-systems", status_code=201)
def create_code_system(
    data: CodeSystemCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    obj = TerminologyService.create_code_system(db, data.model_dump(exclude_none=True))
    return obj.to_dict()


@router.get("/terminology/icd10")
def search_icd10(
    q: str | None = Query(None, description="Search by code or description"),
    chapter: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items, total = TerminologyService.search_icd10(
        db,
        query=q,
        chapter=chapter,
        skip=skip,
        limit=limit,
    )
    return {"items": [c.to_dict() for c in items], "total": total}


@router.get("/terminology/loinc")
def search_loinc(
    q: str | None = Query(None, description="Search by LOINC number or name"),
    class_name: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items, total = TerminologyService.search_loinc(
        db,
        query=q,
        class_name=class_name,
        skip=skip,
        limit=limit,
    )
    return {"items": [c.to_dict() for c in items], "total": total}


@router.get("/terminology/snomed")
def search_snomed(
    q: str | None = Query(None, description="Search by concept ID or name"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items, total = TerminologyService.search_snomed(db, query=q, skip=skip, limit=limit)
    return {"items": [c.to_dict() for c in items], "total": total}


@router.get("/terminology/fhir/$expand")
def fhir_expand_value_set(
    url: str | None = Query(None, description="Value set URL or OID"),
    filter: str | None = Query(None, alias="filter"),
    count: int = Query(50, ge=1, le=1000),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    vs_filters = [ValueSet.is_deleted.is_(False)]
    if url:
        vs_filters.append(
            (ValueSet.oid == url) | (ValueSet.name == url),
        )
    value_set = db.query(ValueSet).filter(*vs_filters).first()
    if not value_set:
        return {"resourceType": "Parameters", "parameter": [], "total": 0}
    members = value_set.members
    if filter:
        members = [
            m
            for m in members
            if m.code
            and (
                filter.lower() in (m.code.code or "").lower()
                or filter.lower() in (m.code.display or "").lower()
            )
        ]
    expansions = []
    for m in members[:count]:
        expansions.append(
            {
                "system": m.code.system.value if m.code and m.code.system else None,
                "code": m.code.code if m.code else None,
                "display": m.code.display if m.code else None,
            }
        )
    return {
        "resourceType": "ValueSet",
        "expansion": {
            "identifier": value_set.oid or value_set.id,
            "timestamp": None,
            "total": len(expansions),
            "contains": expansions,
        },
    }


@router.get("/terminology/fhir/$lookup")
def fhir_lookup_code(
    system: str = Query(..., description="Code system URI"),
    code: str = Query(..., description="Code to look up"),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    obj = (
        db.query(TerminologyCode)
        .filter(
            TerminologyCode.code == code,
            TerminologyCode.system == system,
            TerminologyCode.is_deleted.is_(False),
        )
        .first()
    )
    if not obj:
        raise HTTPException(status_code=404, detail="Code not found")
    return {
        "resourceType": "Parameters",
        "parameter": [
            {"name": "name", "valueString": obj.display},
            {"name": "system", "valueUri": str(obj.system.value if obj.system else system)},
            {"name": "code", "valueCode": obj.code},
            {"name": "display", "valueString": obj.display},
            {"name": "definition", "valueString": obj.definition},
        ],
    }


# ==============================================================================
# Clinical Knowledge Routes
# ==============================================================================


class GuidelineCreate(BaseModel):
    title: str = Field(..., max_length=512)
    identifier: str | None = None
    version: str = "1.0"
    status: str = "draft"
    specialty: str | None = None
    publisher: str | None = None
    authoring_body: str | None = None
    description: str | None = None
    purpose: str | None = None
    population: str | None = None
    evidence_level: str | None = None
    publication_date: str | None = None
    effective_date: str | None = None
    review_date: str | None = None
    body: str | None = None
    summary: str | None = None
    keywords: str | None = None
    language: str = "ar"
    source_url: str | None = None


class GuidelineUpdate(BaseModel):
    title: str | None = None
    version: str | None = None
    status: str | None = None
    specialty: str | None = None
    description: str | None = None
    purpose: str | None = None
    population: str | None = None
    evidence_level: str | None = None
    body: str | None = None
    summary: str | None = None
    keywords: str | None = None
    review_date: str | None = None


class ProtocolCreate(BaseModel):
    title: str = Field(..., max_length=512)
    protocol_id: str | None = None
    version: str = "1.0"
    status: str = "draft"
    guideline_id: str | None = None
    department: str | None = None
    procedure_category: str | None = None
    description: str | None = None
    inclusion_criteria: str | None = None
    exclusion_criteria: str | None = None
    prerequisites: str | None = None
    steps: str | None = None
    duration_expected: str | None = None
    required_equipment: str | None = None
    required_personnel: str | None = None
    complications: str | None = None
    outcome_measures: str | None = None
    effective_date: str | None = None
    expiration_date: str | None = None
    is_emergency: bool = False
    is_surgical: bool = False


class PathwayCreate(BaseModel):
    name: str = Field(..., max_length=512)
    version: str = "1.0"
    status: str = "draft"
    condition: str | None = None
    description: str | None = None
    duration_days: int | None = None
    phases: str | None = None
    milestones: str | None = None
    expected_outcomes: str | None = None
    inclusion_criteria: str | None = None
    exclusion_criteria: str | None = None
    target_population: str | None = None
    setting: str | None = None
    effective_date: str | None = None
    expiration_date: str | None = None
    owner: str | None = None


class GuidelineApprovalCreate(BaseModel):
    guideline_id: str
    approver_id: str
    approver_name: str = Field(..., max_length=256)
    approver_role: str | None = None
    organization: str | None = None
    decision: str
    comments: str | None = None
    effective_from: str | None = None
    effective_until: str | None = None


class StandingOrderCreate(BaseModel):
    title: str = Field(..., max_length=512)
    order_id: str | None = None
    description: str | None = None
    department: str | None = None
    order_type: str
    order_details: str
    indication: str | None = None
    contraindications: str | None = None
    frequency: str | None = None
    duration: str | None = None
    priority: str | None = None
    requires_approval: bool = False
    is_active: bool = True
    effective_start: str | None = None
    effective_end: str | None = None
    approver_role: str | None = None
    protocol_id: str | None = None


@router.get("/knowledge/guidelines")
def list_guidelines(
    status: str | None = None,
    specialty: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items, total = ClinicalKnowledgeService.list_guidelines(
        db,
        status=status,
        specialty=specialty,
        skip=skip,
        limit=limit,
    )
    return {"items": [g.to_dict() for g in items], "total": total}


@router.post("/knowledge/guidelines", status_code=201)
def create_guideline(
    data: GuidelineCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    obj = ClinicalKnowledgeService.create_guideline(db, data.model_dump(exclude_none=True))
    return obj.to_dict()


@router.get("/knowledge/guidelines/{guideline_id}")
def get_guideline(
    guideline_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    obj = ClinicalKnowledgeService.get_guideline(db, guideline_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Guideline not found")
    return obj.to_dict()


@router.put("/knowledge/guidelines/{guideline_id}")
def update_guideline(
    guideline_id: str,
    data: GuidelineUpdate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    obj = ClinicalKnowledgeService.update_guideline(
        db,
        guideline_id,
        data.model_dump(exclude_none=True),
    )
    if not obj:
        raise HTTPException(status_code=404, detail="Guideline not found")
    return obj.to_dict()


@router.get("/knowledge/protocols")
def list_protocols(
    status: str | None = None,
    department: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items, total = ClinicalKnowledgeService.list_protocols(
        db,
        status=status,
        department=department,
        skip=skip,
        limit=limit,
    )
    return {"items": [p.to_dict() for p in items], "total": total}


@router.post("/knowledge/protocols", status_code=201)
def create_protocol(
    data: ProtocolCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    obj = ClinicalKnowledgeService.create_protocol(db, data.model_dump(exclude_none=True))
    return obj.to_dict()


@router.get("/knowledge/protocols/{protocol_id}")
def get_protocol(
    protocol_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    obj = ClinicalKnowledgeService.get_protocol(db, protocol_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Protocol not found")
    return obj.to_dict()


@router.put("/knowledge/protocols/{protocol_id}")
def update_protocol(
    protocol_id: str,
    data: ProtocolCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    obj = ClinicalKnowledgeService.update_protocol(
        db,
        protocol_id,
        data.model_dump(exclude_none=True),
    )
    if not obj:
        raise HTTPException(status_code=404, detail="Protocol not found")
    return obj.to_dict()


@router.get("/knowledge/pathways")
def list_pathways(
    status: str | None = None,
    condition: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items, total = ClinicalKnowledgeService.list_pathways(
        db,
        status=status,
        condition=condition,
        skip=skip,
        limit=limit,
    )
    return {"items": [p.to_dict() for p in items], "total": total}


@router.post("/knowledge/pathways", status_code=201)
def create_pathway(
    data: PathwayCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    obj = ClinicalKnowledgeService.create_pathway(db, data.model_dump(exclude_none=True))
    return obj.to_dict()


@router.get("/knowledge/pathways/{pathway_id}")
def get_pathway(
    pathway_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    obj = ClinicalKnowledgeService.get_pathway(db, pathway_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Pathway not found")
    return obj.to_dict()


@router.put("/knowledge/pathways/{pathway_id}")
def update_pathway(
    pathway_id: str,
    data: PathwayCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    obj = ClinicalKnowledgeService.update_pathway(
        db,
        pathway_id,
        data.model_dump(exclude_none=True),
    )
    if not obj:
        raise HTTPException(status_code=404, detail="Pathway not found")
    return obj.to_dict()


@router.post("/knowledge/guidelines/{guideline_id}/approvals", status_code=201)
def create_guideline_approval(
    guideline_id: str,
    data: GuidelineApprovalCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data_dict = data.model_dump(exclude_none=True)
    data_dict["guideline_id"] = guideline_id
    obj = ClinicalKnowledgeService.create_approval(db, data_dict)
    return obj.to_dict()


@router.get("/knowledge/standing-orders")
def list_standing_orders(
    department: str | None = None,
    active_only: bool = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items, total = ClinicalKnowledgeService.list_standing_orders(
        db,
        department=department,
        active_only=active_only,
        skip=skip,
        limit=limit,
    )
    return {"items": [s.to_dict() for s in items], "total": total}


@router.post("/knowledge/standing-orders", status_code=201)
def create_standing_order(
    data: StandingOrderCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    obj = ClinicalKnowledgeService.create_standing_order(db, data.model_dump(exclude_none=True))
    return obj.to_dict()


@router.get("/knowledge/recommendations")
def list_recommendations(
    guideline_id: str | None = None,
    evidence_level: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items, total = ClinicalKnowledgeService.get_recommendations(
        db,
        guideline_id=guideline_id,
        evidence_level=evidence_level,
        skip=skip,
        limit=limit,
    )
    return {"items": [r.to_dict() for r in items], "total": total}


# ==============================================================================
# CDS Routes (Clinical Decision Support)
# ==============================================================================


class OrderSetRecommendationRequest(BaseModel):
    condition: str | None = None
    department: str | None = None
    patient_age: int | None = None
    patient_gender: str | None = None
    chief_complaint: str | None = None


class ContraindicationCheckRequest(BaseModel):
    subject_code: str
    subject_system: str


class DuplicateOrderCheckRequest(BaseModel):
    patient_id: str
    order_code: str
    encounter_id: str | None = None


class DrugInteractionCheckRequest(BaseModel):
    medications: list[dict[str, str]]


class ClinicalAlertCreate(BaseModel):
    alert_type: str = Field(..., max_length=64)
    severity: str
    patient_id: str | None = None
    encounter_id: str | None = None
    provider_id: str | None = None
    title: str = Field(..., max_length=256)
    message: str
    detail: str | None = None
    trigger_code: str | None = None
    trigger_system: str | None = None
    trigger_value: str | None = None
    is_actionable: bool = True
    source_rule_id: str | None = None


class CareBundleComplianceRequest(BaseModel):
    bundle_id: str
    completed_elements: list[str]


@router.post("/cds/order-set-recommendations")
def get_order_set_recommendations(
    data: OrderSetRecommendationRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    results = CDSService.get_order_set_recommendations(
        db,
        condition=data.condition,
        department=data.department,
    )
    return {"recommendations": results, "count": len(results)}


@router.post("/cds/contraindication-check")
def check_contraindications(
    data: ContraindicationCheckRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    results = CDSService.check_contraindications(
        db,
        subject_code=data.subject_code,
        subject_system=data.subject_system,
    )
    return {"contraindications": results, "count": len(results)}


@router.post("/cds/duplicate-order-check")
def check_duplicate_order(
    data: DuplicateOrderCheckRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    results = CDSService.check_duplicate_order(
        db,
        patient_id=data.patient_id,
        order_code=data.order_code,
        encounter_id=data.encounter_id,
    )
    return {"alerts": results, "is_duplicate": len(results) > 0}


@router.post("/cds/drug-interaction-check")
def check_drug_interactions(
    data: DrugInteractionCheckRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    results = CDSService.check_drug_interactions(
        db,
        medications=data.medications,
    )
    return {"interactions": results, "count": len(results)}


@router.post("/cds/alerts", status_code=201)
def create_clinical_alert(
    data: ClinicalAlertCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    obj = CDSService.create_alert(db, data.model_dump(exclude_none=True))
    return obj.to_dict()


@router.get("/cds/alerts")
def get_active_alerts(
    patient_id: str | None = None,
    encounter_id: str | None = None,
    severity: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items, total = CDSService.get_active_alerts(
        db,
        patient_id=patient_id,
        encounter_id=encounter_id,
        severity=severity,
        skip=skip,
        limit=limit,
    )
    return {"items": [a.to_dict() for a in items], "total": total}


@router.put("/cds/alerts/{alert_id}/acknowledge")
def acknowledge_alert(
    alert_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    obj = CDSService.acknowledge_alert(db, alert_id, current_user.id)
    if not obj:
        raise HTTPException(status_code=404, detail="Alert not found")
    return obj.to_dict()


@router.get("/cds/reminders")
def get_patient_reminders(
    patient_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items, total = CDSService.get_patient_reminders(
        db,
        patient_id=patient_id,
        skip=skip,
        limit=limit,
    )
    return {"items": [a.to_dict() for a in items], "total": total}


@router.post("/cds/care-bundle-compliance")
def check_care_bundle_compliance(
    data: CareBundleComplianceRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = CDSService.check_care_bundle_compliance(
        db,
        bundle_id=data.bundle_id,
        completed_elements=data.completed_elements,
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# ==============================================================================
# Quality Routes
# ==============================================================================


class QualityIndicatorCreate(BaseModel):
    name: str = Field(..., max_length=256)
    code: str | None = None
    indicator_type: str
    description: str | None = None
    department: str | None = None
    numerator: str
    denominator: str
    target_value: float | None = None
    benchmark_value: float | None = None
    unit: str | None = None
    frequency: str | None = None
    direction: str | None = None
    is_national: bool = False
    is_active: bool = True
    steward: str | None = None
    source: str | None = None
    effective_start: str | None = None
    effective_end: str | None = None


class IndicatorMeasurementCreate(BaseModel):
    indicator_id: str
    measurement_date: str
    period_start: str | None = None
    period_end: str | None = None
    numerator_value: float
    denominator_value: float | None = None
    result_value: float | None = None
    notes: str | None = None
    measured_by: str | None = None


class ComplianceCheckCreate(BaseModel):
    check_type: str
    standard: str | None = None
    department: str | None = None
    check_date: str
    result: str
    score: float | None = None
    findings: str | None = None
    non_conformities: str | None = None
    observations: str | None = None
    opportunities: str | None = None
    action_plan: str | None = None
    deadline: str | None = None
    status: str = "open"


class MortalityReviewCreate(BaseModel):
    patient_id: str
    encounter_id: str | None = None
    date_of_death: str
    cause_of_death: str | None = None
    cause_code: str | None = None
    cause_system: str | None = None
    location: str | None = None
    department: str | None = None
    review_date: str
    classification: str | None = None
    preventability: str | None = None
    contributing_factors: str | None = None
    summary: str | None = None
    recommendations: str | None = None
    is_autopsy_performed: bool = False
    autopsy_findings: str | None = None
    is_completed: bool = False


class IncidentReportCreate(BaseModel):
    incident_type: str
    incident_date: str
    severity: str
    location: str | None = None
    department: str | None = None
    patient_id: str | None = None
    encounter_id: str | None = None
    description: str | None = None
    immediate_action: str | None = None
    contributing_factors: str | None = None
    root_cause: str | None = None
    outcome: str | None = None
    actions_taken: str | None = None
    status: str = "open"
    is_notifiable: bool = False
    notified_authority: str | None = None


class PatientSafetyEventCreate(BaseModel):
    category: str
    event_type: str
    patient_id: str | None = None
    encounter_id: str | None = None
    provider_id: str | None = None
    event_date: str
    severity: str
    description: str | None = None
    harm_level: str | None = None
    preventability: str | None = None
    contributing_factors: str | None = None
    mitigating_factors: str | None = None
    actions_taken: str | None = None
    outcome: str | None = None
    status: str = "open"
    is_sentinel: bool = False


@router.get("/quality/indicators")
def list_quality_indicators(
    indicator_type: str | None = None,
    department: str | None = None,
    active_only: bool = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items, total = QualityService.list_indicators(
        db,
        indicator_type=indicator_type,
        department=department,
        active_only=active_only,
        skip=skip,
        limit=limit,
    )
    return {"items": [i.to_dict() for i in items], "total": total}


@router.post("/quality/indicators", status_code=201)
def create_quality_indicator(
    data: QualityIndicatorCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    obj = QualityService.create_indicator(db, data.model_dump(exclude_none=True))
    return obj.to_dict()


@router.post("/quality/measurements", status_code=201)
def create_indicator_measurement(
    data: IndicatorMeasurementCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    obj = QualityService.record_measurement(db, data.model_dump(exclude_none=True))
    return obj.to_dict()


@router.get("/quality/audit-records")
def list_audit_records(
    patient_id: str | None = None,
    department: str | None = None,
    audit_type: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items, total = QualityService.get_audit_records(
        db,
        patient_id=patient_id,
        department=department,
        audit_type=audit_type,
        skip=skip,
        limit=limit,
    )
    return {"items": [r.to_dict() for r in items], "total": total}


@router.post("/quality/audit-records", status_code=201)
def create_audit_record(
    data: dict[str, Any],
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    obj = QualityService.create_audit_record(db, data, audited_by=current_user.id)
    return obj.to_dict()


@router.post("/quality/compliance-checks", status_code=201)
def create_compliance_check(
    data: ComplianceCheckCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    obj = QualityService.create_compliance_check(
        db,
        data.model_dump(exclude_none=True),
        checked_by=current_user.id,
    )
    return obj.to_dict()


@router.get("/quality/compliance-checks")
def list_compliance_checks(
    standard: str | None = None,
    department: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items, total = QualityService.get_compliance_checks(
        db,
        standard=standard,
        department=department,
        skip=skip,
        limit=limit,
    )
    return {"items": [c.to_dict() for c in items], "total": total}


@router.get("/quality/benchmarks")
def list_benchmarks(
    indicator_id: str | None = None,
    year: int | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items, total = QualityService.get_benchmarks(
        db,
        indicator_id=indicator_id,
        year=year,
        skip=skip,
        limit=limit,
    )
    return {"items": [b.to_dict() for b in items], "total": total}


@router.post("/quality/mortality-reviews", status_code=201)
def create_mortality_review(
    data: MortalityReviewCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    obj = QualityService.create_mortality_review(
        db,
        data.model_dump(exclude_none=True),
        reviewer=current_user.id,
    )
    return obj.to_dict()


@router.post("/quality/incident-reports", status_code=201)
def create_incident_report(
    data: IncidentReportCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    obj = QualityService.create_incident_report(
        db,
        data.model_dump(exclude_none=True),
        reporter_id=current_user.id,
    )
    return obj.to_dict()


@router.post("/quality/safety-events", status_code=201)
def create_safety_event(
    data: PatientSafetyEventCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    obj = QualityService.create_safety_event(
        db,
        data.model_dump(exclude_none=True),
        reported_by=current_user.id,
    )
    return obj.to_dict()


@router.get("/quality/dashboard")
def get_quality_dashboard(
    department: str | None = None,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    kpis = QualityService.get_kpi_summary(db, department=department)
    compliance = QualityService.get_compliance_dashboard(db, department=department)
    return {
        "kpis": kpis,
        "compliance": compliance,
        "department": department,
    }


# ==============================================================================
# Research Routes
# ==============================================================================


class RegistryCreate(BaseModel):
    name: str
    registry_type: str
    description: str | None = None
    condition: str | None = None
    inclusion_criteria: str | None = None
    steward: str | None = None


class CohortCreate(BaseModel):
    name: str
    description: str | None = None
    inclusion_criteria: str | None = None
    registry_id: str | None = None
    is_active: bool = True


@router.post("/research/registries", status_code=201)
def create_registry(
    data: RegistryCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ResearchService.create_registry(db, data.model_dump(exclude_none=True))


@router.get("/research/registries")
def list_registries(
    registry_type: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items, total = ResearchService.list_registries(
        db,
        registry_type=registry_type,
        skip=skip,
        limit=limit,
    )
    return {
        "items": [
            r.to_dict() if hasattr(r, "to_dict") else {"id": r.id, "name": r.name} for r in items
        ],
        "total": total,
    }


@router.post("/research/cohorts", status_code=201)
def create_cohort(
    data: CohortCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ResearchService.create_cohort(db, data.model_dump(exclude_none=True))


@router.get("/research/cohorts")
def list_cohorts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items, total = ResearchService.list_cohorts(db, skip=skip, limit=limit)
    return {
        "items": [
            r.to_dict() if hasattr(r, "to_dict") else {"id": r.id, "name": r.name} for r in items
        ],
        "total": total,
    }


@router.post("/research/export-deidentified")
def export_deidentified_dataset(
    cohort_id: str | None = None,
    registry_id: str | None = None,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ResearchService.export_deidentified_dataset(
        db,
        cohort_id=cohort_id,
        registry_id=registry_id,
    )


# ==============================================================================
# Clinical AI Routes
# ==============================================================================


class ClinicalCopilotRequest(BaseModel):
    patient_context: dict[str, Any] = {}
    clinical_findings: list[dict[str, Any]] = []


class RiskPredictionRequest(BaseModel):
    patient_id: str
    risk_type: str
    clinical_data: dict[str, Any] = {}


class CareGapRequest(BaseModel):
    patient_id: str
    clinical_data: dict[str, Any] = {}


class DiagnosticAssistantRequest(BaseModel):
    symptoms: list[str] = []
    findings: list[dict[str, Any]] = []
    patient_context: dict[str, Any] = {}


class ExplainabilityRequest(BaseModel):
    recommendation_id: str
    recommendation_type: str


@router.post("/ai/copilot")
def clinical_copilot(
    data: ClinicalCopilotRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ClinicalAIService.clinical_copilot(
        db,
        patient_context=data.patient_context,
        clinical_findings=data.clinical_findings,
    )


@router.post("/ai/risk-prediction")
def predict_risk(
    data: RiskPredictionRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ClinicalAIService.predict_risk(
        db,
        patient_id=data.patient_id,
        risk_type=data.risk_type,
        clinical_data=data.clinical_data,
    )


@router.post("/ai/care-gaps")
def detect_care_gaps(
    data: CareGapRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ClinicalAIService.detect_care_gaps(
        db,
        patient_id=data.patient_id,
        clinical_data=data.clinical_data,
    )


@router.post("/ai/diagnostic-assistant")
def diagnostic_assistant(
    data: DiagnosticAssistantRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ClinicalAIService.diagnostic_assistant(
        db,
        symptoms=data.symptoms,
        findings=data.findings,
        patient_context=data.patient_context,
    )


@router.post("/ai/explain")
def get_explanation(
    data: ExplainabilityRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ClinicalAIService.get_explanation(
        db,
        recommendation_id=data.recommendation_id,
        recommendation_type=data.recommendation_type,
    )

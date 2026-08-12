from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app._compat import UTC
from app.clinical.cds.models import (
    CareBundle,
    ClinicalAlert,
    Contraindication,
    DuplicateOrderRule,
    OrderSet,
    PreventiveRecommendation,
)
from app.clinical.knowledge.models import (
    ClinicalGuideline,
    ClinicalPathway,
    ClinicalProtocol,
    ClinicalRecommendation,
    GuidelineApproval,
    StandingOrder,
)
from app.clinical.quality.models import (
    BenchmarkValue,
    ClinicalAuditRecord,
    ComplianceCheck,
    IncidentReport,
    IndicatorMeasurement,
    MortalityReview,
    PatientSafetyEvent,
    QualityIndicator,
)
from app.clinical.terminology.models import (
    CodeSystem,
    ICD10Code,
    LOINCCode,
    SNOMEDCTCode,
    TerminologyCode,
    TerminologyMapping,
    TerminologyVersion,
    ValueSet,
    ValueSetMember,
)

logger = logging.getLogger("gula.clinical_service")


# ==============================================================================
# Terminology Service
# ==============================================================================


class TerminologyService:

    @staticmethod
    def search_codes(
        db: Session,
        *,
        query: str | None = None,
        system: str | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[TerminologyCode], int]:
        filters = [TerminologyCode.is_deleted.is_(False)]
        if query:
            filters.append(
                or_(
                    TerminologyCode.code.ilike(f"%{query}%"),
                    TerminologyCode.display.ilike(f"%{query}%"),
                ),
            )
        if system:
            filters.append(TerminologyCode.system == system)
        if status:
            filters.append(TerminologyCode.status == status)
        total = db.query(TerminologyCode).filter(*filters).count()
        items = (
            db.query(TerminologyCode)
            .filter(*filters)
            .offset(skip)
            .limit(limit)
            .all()
        )
        return items, total

    @staticmethod
    def get_code(db: Session, code_id: str) -> TerminologyCode | None:
        return db.query(TerminologyCode).filter(
            TerminologyCode.id == code_id,
            TerminologyCode.is_deleted.is_(False),
        ).first()

    @staticmethod
    def create_code(db: Session, data: dict[str, Any]) -> TerminologyCode:
        obj = TerminologyCode(**data)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def update_code(
        db: Session, code_id: str, data: dict[str, Any],
    ) -> TerminologyCode | None:
        obj = db.query(TerminologyCode).filter(
            TerminologyCode.id == code_id,
            TerminologyCode.is_deleted.is_(False),
        ).first()
        if not obj:
            return None
        for key, val in data.items():
            if val is not None:
                setattr(obj, key, val)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def delete_code(db: Session, code_id: str) -> bool:
        obj = db.query(TerminologyCode).filter(
            TerminologyCode.id == code_id,
            TerminologyCode.is_deleted.is_(False),
        ).first()
        if not obj:
            return False
        obj.soft_delete()
        db.commit()
        return True

    @staticmethod
    def get_versions(
        db: Session,
        *,
        system: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[TerminologyVersion], int]:
        filters = [TerminologyVersion.is_deleted.is_(False)]
        if system:
            filters.append(TerminologyVersion.system == system)
        total = db.query(TerminologyVersion).filter(*filters).count()
        items = (
            db.query(TerminologyVersion)
            .filter(*filters)
            .order_by(TerminologyVersion.imported_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return items, total

    @staticmethod
    def create_version(db: Session, data: dict[str, Any]) -> TerminologyVersion:
        obj = TerminologyVersion(**data)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def create_mapping(db: Session, data: dict[str, Any]) -> TerminologyMapping:
        obj = TerminologyMapping(**data)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def create_value_set(db: Session, data: dict[str, Any]) -> ValueSet:
        obj = ValueSet(**data)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def get_value_sets(
        db: Session,
        *,
        name: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[ValueSet], int]:
        filters = [ValueSet.is_deleted.is_(False)]
        if name:
            filters.append(ValueSet.name.ilike(f"%{name}%"))
        total = db.query(ValueSet).filter(*filters).count()
        items = (
            db.query(ValueSet)
            .filter(*filters)
            .offset(skip)
            .limit(limit)
            .all()
        )
        return items, total

    @staticmethod
    def create_value_set_member(db: Session, data: dict[str, Any]) -> ValueSetMember:
        obj = ValueSetMember(**data)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def create_code_system(db: Session, data: dict[str, Any]) -> CodeSystem:
        obj = CodeSystem(**data)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def get_code_systems(
        db: Session,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[CodeSystem], int]:
        filters = [CodeSystem.is_deleted.is_(False)]
        total = db.query(CodeSystem).filter(*filters).count()
        items = (
            db.query(CodeSystem)
            .filter(*filters)
            .offset(skip)
            .limit(limit)
            .all()
        )
        return items, total

    @staticmethod
    def search_icd10(
        db: Session,
        *,
        query: str | None = None,
        chapter: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[ICD10Code], int]:
        filters = [ICD10Code.is_deleted.is_(False)]
        if query:
            filters.append(
                or_(
                    ICD10Code.code.ilike(f"%{query}%"),
                    ICD10Code.short_description.ilike(f"%{query}%"),
                    ICD10Code.long_description.ilike(f"%{query}%"),
                ),
            )
        if chapter:
            filters.append(ICD10Code.chapter == chapter)
        total = db.query(ICD10Code).filter(*filters).count()
        items = (
            db.query(ICD10Code)
            .filter(*filters)
            .offset(skip)
            .limit(limit)
            .all()
        )
        return items, total

    @staticmethod
    def search_loinc(
        db: Session,
        *,
        query: str | None = None,
        class_name: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[LOINCCode], int]:
        filters = [LOINCCode.is_deleted.is_(False)]
        if query:
            filters.append(
                or_(
                    LOINCCode.loinc_num.ilike(f"%{query}%"),
                    LOINCCode.component.ilike(f"%{query}%"),
                    LOINCCode.long_common_name.ilike(f"%{query}%"),
                    LOINCCode.short_name.ilike(f"%{query}%"),
                ),
            )
        if class_name:
            filters.append(LOINCCode.class_name == class_name)
        total = db.query(LOINCCode).filter(*filters).count()
        items = (
            db.query(LOINCCode)
            .filter(*filters)
            .offset(skip)
            .limit(limit)
            .all()
        )
        return items, total

    @staticmethod
    def search_snomed(
        db: Session,
        *,
        query: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[SNOMEDCTCode], int]:
        filters = [SNOMEDCTCode.is_deleted.is_(False)]
        if query:
            filters.append(
                or_(
                    SNOMEDCTCode.concept_id.ilike(f"%{query}%"),
                    SNOMEDCTCode.fully_specified_name.ilike(f"%{query}%"),
                    SNOMEDCTCode.preferred_term.ilike(f"%{query}%"),
                ),
            )
        total = db.query(SNOMEDCTCode).filter(*filters).count()
        items = (
            db.query(SNOMEDCTCode)
            .filter(*filters)
            .offset(skip)
            .limit(limit)
            .all()
        )
        return items, total


# ==============================================================================
# Clinical Knowledge Service
# ==============================================================================


class ClinicalKnowledgeService:

    @staticmethod
    def create_guideline(db: Session, data: dict[str, Any]) -> ClinicalGuideline:
        obj = ClinicalGuideline(**data)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def get_guideline(db: Session, guideline_id: str) -> ClinicalGuideline | None:
        return db.query(ClinicalGuideline).filter(
            ClinicalGuideline.id == guideline_id,
            ClinicalGuideline.is_deleted.is_(False),
        ).first()

    @staticmethod
    def list_guidelines(
        db: Session,
        *,
        status: str | None = None,
        specialty: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[ClinicalGuideline], int]:
        filters = [ClinicalGuideline.is_deleted.is_(False)]
        if status:
            filters.append(ClinicalGuideline.status == status)
        if specialty:
            filters.append(ClinicalGuideline.specialty == specialty)
        total = db.query(ClinicalGuideline).filter(*filters).count()
        items = (
            db.query(ClinicalGuideline)
            .filter(*filters)
            .order_by(ClinicalGuideline.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return items, total

    @staticmethod
    def update_guideline(
        db: Session, guideline_id: str, data: dict[str, Any],
    ) -> ClinicalGuideline | None:
        obj = db.query(ClinicalGuideline).filter(
            ClinicalGuideline.id == guideline_id,
            ClinicalGuideline.is_deleted.is_(False),
        ).first()
        if not obj:
            return None
        for key, val in data.items():
            if val is not None:
                setattr(obj, key, val)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def create_protocol(db: Session, data: dict[str, Any]) -> ClinicalProtocol:
        obj = ClinicalProtocol(**data)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def get_protocol(db: Session, protocol_id: str) -> ClinicalProtocol | None:
        return db.query(ClinicalProtocol).filter(
            ClinicalProtocol.id == protocol_id,
            ClinicalProtocol.is_deleted.is_(False),
        ).first()

    @staticmethod
    def list_protocols(
        db: Session,
        *,
        status: str | None = None,
        department: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[ClinicalProtocol], int]:
        filters = [ClinicalProtocol.is_deleted.is_(False)]
        if status:
            filters.append(ClinicalProtocol.status == status)
        if department:
            filters.append(ClinicalProtocol.department == department)
        total = db.query(ClinicalProtocol).filter(*filters).count()
        items = (
            db.query(ClinicalProtocol)
            .filter(*filters)
            .order_by(ClinicalProtocol.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return items, total

    @staticmethod
    def update_protocol(
        db: Session, protocol_id: str, data: dict[str, Any],
    ) -> ClinicalProtocol | None:
        obj = db.query(ClinicalProtocol).filter(
            ClinicalProtocol.id == protocol_id,
            ClinicalProtocol.is_deleted.is_(False),
        ).first()
        if not obj:
            return None
        for key, val in data.items():
            if val is not None:
                setattr(obj, key, val)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def create_pathway(db: Session, data: dict[str, Any]) -> ClinicalPathway:
        obj = ClinicalPathway(**data)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def get_pathway(db: Session, pathway_id: str) -> ClinicalPathway | None:
        return db.query(ClinicalPathway).filter(
            ClinicalPathway.id == pathway_id,
            ClinicalPathway.is_deleted.is_(False),
        ).first()

    @staticmethod
    def list_pathways(
        db: Session,
        *,
        status: str | None = None,
        condition: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[ClinicalPathway], int]:
        filters = [ClinicalPathway.is_deleted.is_(False)]
        if status:
            filters.append(ClinicalPathway.status == status)
        if condition:
            filters.append(ClinicalPathway.condition.ilike(f"%{condition}%"))
        total = db.query(ClinicalPathway).filter(*filters).count()
        items = (
            db.query(ClinicalPathway)
            .filter(*filters)
            .order_by(ClinicalPathway.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return items, total

    @staticmethod
    def update_pathway(
        db: Session, pathway_id: str, data: dict[str, Any],
    ) -> ClinicalPathway | None:
        obj = db.query(ClinicalPathway).filter(
            ClinicalPathway.id == pathway_id,
            ClinicalPathway.is_deleted.is_(False),
        ).first()
        if not obj:
            return None
        for key, val in data.items():
            if val is not None:
                setattr(obj, key, val)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def create_approval(db: Session, data: dict[str, Any]) -> GuidelineApproval:
        obj = GuidelineApproval(**data)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def create_standing_order(db: Session, data: dict[str, Any]) -> StandingOrder:
        obj = StandingOrder(**data)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def list_standing_orders(
        db: Session,
        *,
        department: str | None = None,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[StandingOrder], int]:
        filters = [StandingOrder.is_deleted.is_(False)]
        if active_only:
            filters.append(StandingOrder.is_active.is_(True))
        if department:
            filters.append(StandingOrder.department == department)
        total = db.query(StandingOrder).filter(*filters).count()
        items = (
            db.query(StandingOrder)
            .filter(*filters)
            .order_by(StandingOrder.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return items, total

    @staticmethod
    def get_recommendations(
        db: Session,
        *,
        guideline_id: str | None = None,
        evidence_level: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[ClinicalRecommendation], int]:
        filters = [ClinicalRecommendation.is_deleted.is_(False)]
        if guideline_id:
            filters.append(ClinicalRecommendation.guideline_id == guideline_id)
        if evidence_level:
            filters.append(ClinicalRecommendation.evidence_level == evidence_level)
        total = db.query(ClinicalRecommendation).filter(*filters).count()
        items = (
            db.query(ClinicalRecommendation)
            .filter(*filters)
            .order_by(ClinicalRecommendation.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return items, total


# ==============================================================================
# CDS Service (Clinical Decision Support)
# ==============================================================================


class CDSService:

    @staticmethod
    def get_order_set_recommendations(
        db: Session,
        *,
        condition: str | None = None,
        department: str | None = None,
    ) -> list[dict[str, Any]]:
        filters = [
            OrderSet.is_deleted.is_(False),
            OrderSet.is_active.is_(True),
        ]
        if condition:
            filters.append(OrderSet.condition.ilike(f"%{condition}%"))
        if department:
            filters.append(OrderSet.department == department)
        order_sets = db.query(OrderSet).filter(*filters).all()
        results = []
        for os_obj in order_sets:
            items = [
                {
                    "id": item.id,
                    "item_type": item.item_type,
                    "item_code": item.item_code,
                    "item_display": item.item_display,
                    "sequence": item.sequence,
                    "is_optional": item.is_optional,
                    "is_required": item.is_required,
                }
                for item in os_obj.items
            ]
            results.append({
                "id": os_obj.id,
                "name": os_obj.name,
                "description": os_obj.description,
                "department": os_obj.department,
                "condition": os_obj.condition,
                "items": items,
            })
        return results

    @staticmethod
    def check_contraindications(
        db: Session,
        *,
        subject_code: str,
        subject_system: str,
    ) -> list[dict[str, Any]]:
        filters = [
            Contraindication.is_deleted.is_(False),
            Contraindication.is_active.is_(True),
            Contraindication.subject_code == subject_code,
            Contraindication.subject_system == subject_system,
        ]
        results = db.query(Contraindication).filter(*filters).all()
        return [
            {
                "id": c.id,
                "contraindicated_code": c.contraindicated_code,
                "contraindicated_system": c.contraindicated_system,
                "contraindicated_display": c.contraindicated_display,
                "relationship_type": c.relationship_type,
                "severity": c.severity,
                "evidence": c.evidence,
                "mechanism": c.mechanism,
                "management": c.management,
                "alternative": c.alternative,
                "is_absolute": c.is_absolute,
            }
            for c in results
        ]

    @staticmethod
    def check_duplicate_order(
        db: Session,
        *,
        patient_id: str,
        order_code: str,
        encounter_id: str | None = None,
    ) -> list[dict[str, Any]]:
        filters = [
            DuplicateOrderRule.is_deleted.is_(False),
            DuplicateOrderRule.is_active.is_(True),
            DuplicateOrderRule.order_code == order_code,
        ]
        rules = db.query(DuplicateOrderRule).filter(*filters).all()
        alerts = []
        for rule in rules:
            alerts.append({
                "rule_id": rule.id,
                "rule_name": rule.rule_name,
                "description": rule.description,
                "time_window_hours": rule.time_window_hours,
                "same_encounter_only": rule.same_encounter_only,
                "severity": rule.severity,
                "action": rule.action,
                "notification_message": rule.notification_message,
                "override_requires_approval": rule.override_requires_approval,
            })
        return alerts

    @staticmethod
    def check_drug_interactions(
        db: Session,
        *,
        medications: list[dict[str, str]],
    ) -> list[dict[str, Any]]:
        results = []
        for i, med1 in enumerate(medications):
            for med2 in medications[i + 1:]:
                filters = [
                    Contraindication.is_deleted.is_(False),
                    Contraindication.is_active.is_(True),
                    Contraindication.relationship_type == "drug_interaction",
                    or_(
                        Contraindication.subject_code == med1.get("code"),
                        Contraindication.subject_code == med2.get("code"),
                    ),
                ]
                interactions = db.query(Contraindication).filter(*filters).all()
                for interaction in interactions:
                    results.append({
                        "medication_a": med1,
                        "medication_b": med2,
                        "severity": interaction.severity,
                        "evidence": interaction.evidence,
                        "mechanism": interaction.mechanism,
                        "management": interaction.management,
                        "is_absolute": interaction.is_absolute,
                    })
        return results

    @staticmethod
    def create_alert(db: Session, data: dict[str, Any]) -> ClinicalAlert:
        obj = ClinicalAlert(**data)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def get_active_alerts(
        db: Session,
        *,
        patient_id: str | None = None,
        encounter_id: str | None = None,
        severity: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[ClinicalAlert], int]:
        filters = [
            ClinicalAlert.is_deleted.is_(False),
            ClinicalAlert.resolved.is_(False),
        ]
        if patient_id:
            filters.append(ClinicalAlert.patient_id == patient_id)
        if encounter_id:
            filters.append(ClinicalAlert.encounter_id == encounter_id)
        if severity:
            filters.append(ClinicalAlert.severity == severity)
        total = db.query(ClinicalAlert).filter(*filters).count()
        items = (
            db.query(ClinicalAlert)
            .filter(*filters)
            .order_by(ClinicalAlert.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return items, total

    @staticmethod
    def acknowledge_alert(
        db: Session, alert_id: str, user_id: str,
    ) -> ClinicalAlert | None:
        obj = db.query(ClinicalAlert).filter(
            ClinicalAlert.id == alert_id,
            ClinicalAlert.is_deleted.is_(False),
        ).first()
        if not obj:
            return None
        obj.acknowledged = True
        obj.acknowledged_by = user_id
        obj.acknowledged_at = datetime.now(UTC)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def get_patient_reminders(
        db: Session,
        *,
        patient_id: str,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[ClinicalAlert], int]:
        filters = [
            ClinicalAlert.is_deleted.is_(False),
            ClinicalAlert.patient_id == patient_id,
            ClinicalAlert.alert_type == "reminder",
        ]
        total = db.query(ClinicalAlert).filter(*filters).count()
        items = (
            db.query(ClinicalAlert)
            .filter(*filters)
            .order_by(ClinicalAlert.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return items, total

    @staticmethod
    def check_care_bundle_compliance(
        db: Session,
        *,
        bundle_id: str,
        completed_elements: list[str],
    ) -> dict[str, Any]:
        bundle = db.query(CareBundle).filter(
            CareBundle.id == bundle_id,
            CareBundle.is_deleted.is_(False),
        ).first()
        if not bundle:
            return {"error": "Care bundle not found"}
        total_elements = len(bundle.elements)
        if total_elements == 0:
            return {
                "bundle_id": bundle_id,
                "bundle_name": bundle.name,
                "compliance_percentage": 100.0,
                "met_target": True,
                "completed": 0,
                "total": 0,
            }
        completed_count = sum(
            1 for e in bundle.elements if e.element_code in completed_elements
        )
        percentage = round((completed_count / total_elements) * 100, 2)
        return {
            "bundle_id": bundle_id,
            "bundle_name": bundle.name,
            "compliance_percentage": percentage,
            "met_target": percentage >= (bundle.compliance_threshold or 80),
            "completed": completed_count,
            "total": total_elements,
            "threshold": bundle.compliance_threshold,
        }


# ==============================================================================
# Quality Service
# ==============================================================================


class QualityService:

    @staticmethod
    def create_indicator(db: Session, data: dict[str, Any]) -> QualityIndicator:
        obj = QualityIndicator(**data)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def list_indicators(
        db: Session,
        *,
        indicator_type: str | None = None,
        department: str | None = None,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[QualityIndicator], int]:
        filters = [QualityIndicator.is_deleted.is_(False)]
        if active_only:
            filters.append(QualityIndicator.is_active.is_(True))
        if indicator_type:
            filters.append(QualityIndicator.indicator_type == indicator_type)
        if department:
            filters.append(QualityIndicator.department == department)
        total = db.query(QualityIndicator).filter(*filters).count()
        items = (
            db.query(QualityIndicator)
            .filter(*filters)
            .order_by(QualityIndicator.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return items, total

    @staticmethod
    def record_measurement(db: Session, data: dict[str, Any]) -> IndicatorMeasurement:
        obj = IndicatorMeasurement(**data)
        if obj.denominator_value and obj.denominator_value > 0:
            obj.percentage = round(
                (obj.numerator_value / obj.denominator_value) * 100, 2,
            )
        db.add(obj)

        indicator = db.query(QualityIndicator).filter(
            QualityIndicator.id == obj.indicator_id,
        ).first()
        if indicator and indicator.target_value is not None:
            if obj.percentage is not None:
                if indicator.direction == "lower_is_better":
                    obj.met_target = obj.percentage <= indicator.target_value
                else:
                    obj.met_target = obj.percentage >= indicator.target_value
            elif obj.result_value is not None:
                if indicator.direction == "lower_is_better":
                    obj.met_target = obj.result_value <= indicator.target_value
                else:
                    obj.met_target = obj.result_value >= indicator.target_value

        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def get_audit_records(
        db: Session,
        *,
        patient_id: str | None = None,
        department: str | None = None,
        audit_type: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[ClinicalAuditRecord], int]:
        filters = [ClinicalAuditRecord.is_deleted.is_(False)]
        if patient_id:
            filters.append(ClinicalAuditRecord.patient_id == patient_id)
        if department:
            filters.append(ClinicalAuditRecord.department == department)
        if audit_type:
            filters.append(ClinicalAuditRecord.audit_type == audit_type)
        total = db.query(ClinicalAuditRecord).filter(*filters).count()
        items = (
            db.query(ClinicalAuditRecord)
            .filter(*filters)
            .order_by(ClinicalAuditRecord.audit_date.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return items, total

    @staticmethod
    def create_audit_record(
        db: Session, data: dict[str, Any], audited_by: str,
    ) -> ClinicalAuditRecord:
        data["audited_by"] = audited_by
        obj = ClinicalAuditRecord(**data)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def create_compliance_check(
        db: Session, data: dict[str, Any], checked_by: str,
    ) -> ComplianceCheck:
        data["checked_by"] = checked_by
        obj = ComplianceCheck(**data)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def get_compliance_checks(
        db: Session,
        *,
        standard: str | None = None,
        department: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[ComplianceCheck], int]:
        filters = [ComplianceCheck.is_deleted.is_(False)]
        if standard:
            filters.append(ComplianceCheck.standard.ilike(f"%{standard}%"))
        if department:
            filters.append(ComplianceCheck.department == department)
        total = db.query(ComplianceCheck).filter(*filters).count()
        items = (
            db.query(ComplianceCheck)
            .filter(*filters)
            .order_by(ComplianceCheck.check_date.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return items, total

    @staticmethod
    def get_benchmarks(
        db: Session,
        *,
        indicator_id: str | None = None,
        year: int | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[BenchmarkValue], int]:
        filters = [BenchmarkValue.is_deleted.is_(False)]
        if indicator_id:
            filters.append(BenchmarkValue.indicator_id == indicator_id)
        if year:
            filters.append(BenchmarkValue.year == year)
        total = db.query(BenchmarkValue).filter(*filters).count()
        items = (
            db.query(BenchmarkValue)
            .filter(*filters)
            .order_by(BenchmarkValue.year.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return items, total

    @staticmethod
    def create_mortality_review(
        db: Session, data: dict[str, Any], reviewer: str,
    ) -> MortalityReview:
        data["reviewer"] = reviewer
        obj = MortalityReview(**data)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def create_incident_report(
        db: Session, data: dict[str, Any], reporter_id: str,
    ) -> IncidentReport:
        data["reporter_id"] = reporter_id
        obj = IncidentReport(**data)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def create_safety_event(
        db: Session, data: dict[str, Any], reported_by: str,
    ) -> PatientSafetyEvent:
        data["reported_by"] = reported_by
        obj = PatientSafetyEvent(**data)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def get_kpi_summary(
        db: Session,
        *,
        department: str | None = None,
    ) -> list[dict[str, Any]]:
        filters = [
            QualityIndicator.is_deleted.is_(False),
            QualityIndicator.is_active.is_(True),
        ]
        if department:
            filters.append(QualityIndicator.department == department)
        indicators = db.query(QualityIndicator).filter(*filters).all()
        results = []
        for ind in indicators:
            latest_measurement = (
                db.query(IndicatorMeasurement)
                .filter(
                    IndicatorMeasurement.indicator_id == ind.id,
                    IndicatorMeasurement.is_deleted.is_(False),
                )
                .order_by(IndicatorMeasurement.measurement_date.desc())
                .first()
            )
            results.append({
                "indicator_id": ind.id,
                "name": ind.name,
                "code": ind.code,
                "type": ind.indicator_type.value if ind.indicator_type else None,
                "department": ind.department,
                "target_value": ind.target_value,
                "benchmark_value": ind.benchmark_value,
                "latest_value": latest_measurement.percentage if latest_measurement else None,
                "latest_date": (
                    latest_measurement.measurement_date.isoformat()
                    if latest_measurement and latest_measurement.measurement_date
                    else None
                ),
                "met_target": latest_measurement.met_target if latest_measurement else None,
            })
        return results

    @staticmethod
    def get_compliance_dashboard(
        db: Session,
        *,
        department: str | None = None,
    ) -> dict[str, Any]:
        filters = [ComplianceCheck.is_deleted.is_(False)]
        if department:
            filters.append(ComplianceCheck.department == department)
        checks = db.query(ComplianceCheck).filter(*filters).all()
        total = len(checks)
        passed = sum(1 for c in checks if c.result == "pass")
        failed = sum(1 for c in checks if c.result == "fail")
        partial = sum(1 for c in checks if c.result == "partial")
        return {
            "total_checks": total,
            "passed": passed,
            "failed": failed,
            "partial": partial,
            "compliance_rate": round((passed / total * 100), 2) if total > 0 else 0.0,
            "department": department,
        }


# ==============================================================================
# Research Service
# ==============================================================================


class ResearchService:

    @staticmethod
    def create_registry(
        db: Session, data: dict[str, Any],
    ) -> dict[str, Any]:
        from app.clinical.research import models as research_models

        cls = getattr(research_models, "ClinicalRegistry", None)
        if cls is None:

            class ClinicalRegistry:
                pass

            research_models.ClinicalRegistry = type(
                "ClinicalRegistry",
                (object,),
                {"__module__": "app.clinical.research.models"},
            )
            cls = research_models.ClinicalRegistry

        obj = cls(**data)
        if hasattr(db, "add"):
            db.add(obj)
            db.commit()
            if hasattr(db, "refresh"):
                db.refresh(obj)
        return {"id": getattr(obj, "id", None), **data}

    @staticmethod
    def list_registries(
        db: Session,
        *,
        registry_type: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Any], int]:
        from app.clinical.research import models as research_models

        cls = getattr(research_models, "ClinicalRegistry", None)
        if cls is None:
            return [], 0
        filters = []
        if registry_type:
            filters.append(cls.registry_type == registry_type)
        total = db.query(cls).filter(*filters).count()
        items = (
            db.query(cls)
            .filter(*filters)
            .offset(skip)
            .limit(limit)
            .all()
        )
        return items, total

    @staticmethod
    def create_cohort(
        db: Session, data: dict[str, Any],
    ) -> dict[str, Any]:
        from app.clinical.research import models as research_models

        cls = getattr(research_models, "ResearchCohort", None)
        if cls is None:

            class ResearchCohort:
                pass

            research_models.ResearchCohort = type(
                "ResearchCohort",
                (object,),
                {"__module__": "app.clinical.research.models"},
            )
            cls = research_models.ResearchCohort

        obj = cls(**data)
        if hasattr(db, "add"):
            db.add(obj)
            db.commit()
        return {"id": getattr(obj, "id", None), **data}

    @staticmethod
    def list_cohorts(
        db: Session,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Any], int]:
        from app.clinical.research import models as research_models

        cls = getattr(research_models, "ResearchCohort", None)
        if cls is None:
            return [], 0
        total = db.query(cls).filter().count()
        items = (
            db.query(cls)
            .filter()
            .offset(skip)
            .limit(limit)
            .all()
        )
        return items, total

    @staticmethod
    def export_deidentified_dataset(
        db: Session,
        *,
        cohort_id: str | None = None,
        registry_id: str | None = None,
    ) -> dict[str, Any]:
        return {
            "status": "stub",
            "message": "De-identified dataset export is not yet implemented. "
                       "This is a placeholder for future functionality.",
            "cohort_id": cohort_id,
            "registry_id": registry_id,
            "format": "FHIR NDJSON",
            "estimated_size": "unknown",
        }


# ==============================================================================
# Clinical AI Service
# ==============================================================================


class ClinicalAIService:

    @staticmethod
    def clinical_copilot(
        db: Session,
        *,
        patient_context: dict[str, Any],
        clinical_findings: list[dict[str, Any]],
    ) -> dict[str, Any]:
        return {
            "status": "stub",
            "suggestions": [],
            "differential_diagnoses": [],
            "recommended_orders": [],
            "message": "Clinical copilot is a stub. "
                       "Integrate with AI provider (Gemini/Groq/Ollama) for real suggestions.",
            "patient_context_summary": {
                k: v for k, v in patient_context.items()
                if k in ("age", "gender", "chief_complaint")
            },
        }

    @staticmethod
    def predict_risk(
        db: Session,
        *,
        patient_id: str,
        risk_type: str,
        clinical_data: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "status": "stub",
            "patient_id": patient_id,
            "risk_type": risk_type,
            "risk_score": None,
            "risk_level": "unknown",
            "contributing_factors": [],
            "recommendations": [],
            "message": "Risk prediction is a stub. "
                       "Integrate with ML model serving infrastructure for real predictions.",
        }

    @staticmethod
    def detect_care_gaps(
        db: Session,
        *,
        patient_id: str,
        clinical_data: dict[str, Any],
    ) -> dict[str, Any]:
        gaps = []

        preventive = (
            db.query(PreventiveRecommendation)
            .filter(
                PreventiveRecommendation.is_deleted.is_(False),
                PreventiveRecommendation.is_active.is_(True),
            )
            .all()
        )
        for rec in preventive:
            gaps.append({
                "type": "preventive",
                "recommendation": rec.title,
                "description": rec.description,
                "intervention": rec.intervention,
                "priority": rec.priority,
                "evidence_level": rec.evidence_level.value if rec.evidence_level else None,
            })

        return {
            "status": "stub",
            "patient_id": patient_id,
            "care_gaps": gaps,
            "message": "Care gap detection is based on active preventive recommendations. "
                       "Enhance with ML-based gap analysis for production use.",
        }

    @staticmethod
    def diagnostic_assistant(
        db: Session,
        *,
        symptoms: list[str],
        findings: list[dict[str, Any]],
        patient_context: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "status": "stub",
            "possible_diagnoses": [],
            "suggested_workup": [],
            "differential_discussion": "",
            "message": "Diagnostic assistant is a stub. "
                       "Integrate with AI provider (Gemini/Groq/Ollama) for real suggestions.",
        }

    @staticmethod
    def get_explanation(
        db: Session,
        *,
        recommendation_id: str,
        recommendation_type: str,
    ) -> dict[str, Any]:
        return {
            "status": "stub",
            "recommendation_id": recommendation_id,
            "recommendation_type": recommendation_type,
            "explanation": "Explainability is not yet implemented. "
                           "This endpoint will provide human-readable explanations "
                           "for AI-generated recommendations.",
            "evidence_sources": [],
            "confidence": None,
        }

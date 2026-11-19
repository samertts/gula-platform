from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.pharmacy.enums import InteractionSeverity
from app.pharmacy.models import (
    AllergyRule,
    ClinicalGuideline,
    ContraindicationRule,
    DoseGuideline,
    DrugInteractionRule,
    DrugMonitoring,
)

logger = logging.getLogger("gula.pharmacy.clinical")


class DrugInteractionEngine:
    def __init__(self, db: Session, lab_id: int | None = None):
        self.db = db
        self.lab_id = lab_id

    def check_interaction(
        self, drug_a_code: str, drug_b_code: str,
    ) -> DrugInteractionRule | None:
        q = self.db.query(DrugInteractionRule).filter(
            or_(
                DrugInteractionRule.drug_a_code == drug_a_code,
                DrugInteractionRule.drug_b_code == drug_a_code,
            ),
            or_(
                DrugInteractionRule.drug_a_code == drug_b_code,
                DrugInteractionRule.drug_b_code == drug_b_code,
            ),
        )
        return q.first()

    def check_multiple_drugs(self, drug_codes: list[str]) -> list[dict[str, Any]]:
        interactions: list[dict[str, Any]] = []
        for i in range(len(drug_codes)):
            for j in range(i + 1, len(drug_codes)):
                rule = self.check_interaction(drug_codes[i], drug_codes[j])
                if rule:
                    interactions.append({
                        "drug_a": drug_codes[i],
                        "drug_b": drug_codes[j],
                        "severity": rule.severity.value,
                        "mechanism": rule.mechanism,
                        "description": rule.description,
                        "recommendation": rule.recommendation,
                        "evidence_level": rule.evidence_level,
                    })
        return interactions

    def check_patient_medications(
        self, active_drug_codes: list[str], new_drug_code: str,
    ) -> list[dict[str, Any]]:
        return self.check_multiple_drugs([*active_drug_codes, new_drug_code])

    def classify_severity(self, severity: InteractionSeverity) -> dict[str, Any]:
        classification = {
            InteractionSeverity.CONTRAINDICATED: {
                "level": 4,
                "label": "Contraindicated",
                "action": "Do not co-administer",
                "color": "black",
            },
            InteractionSeverity.MAJOR: {
                "level": 3,
                "label": "Major",
                "action": "Avoid combination; monitor closely if required",
                "color": "red",
            },
            InteractionSeverity.MODERATE: {
                "level": 2,
                "label": "Moderate",
                "action": "Use with caution; monitor therapy",
                "color": "orange",
            },
            InteractionSeverity.MINOR: {
                "level": 1,
                "label": "Minor",
                "action": "Limited clinical significance",
                "color": "yellow",
            },
            InteractionSeverity.NOTE: {
                "level": 0,
                "label": "Note",
                "action": "Information only",
                "color": "blue",
            },
        }
        return classification.get(severity, {"level": -1, "label": "Unknown", "action": "Unknown", "color": "gray"})


class ContraindicationEngine:
    def __init__(self, db: Session, lab_id: int | None = None):
        self.db = db
        self.lab_id = lab_id

    def check_drug_condition(self, drug_code: str, condition_code: str) -> list[ContraindicationRule]:
        q = self.db.query(ContraindicationRule).filter(
            ContraindicationRule.drug_code == drug_code,
            ContraindicationRule.condition_code == condition_code,
        )
        return q.all()

    def check_patient_conditions(self, drug_code: str, condition_codes: list[str]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for cond_code in condition_codes:
            rules = self.check_drug_condition(drug_code, cond_code)
            for rule in rules:
                results.append({
                    "drug_code": rule.drug_code,
                    "condition_code": rule.condition_code,
                    "severity": rule.severity.value,
                    "description": rule.description,
                    "recommendation": rule.recommendation,
                })
        return results

    def check_pregnancy(self, drug_code: str, pregnancy_category: str | None = None) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        if pregnancy_category and pregnancy_category.upper() in ("X", "D"):
            results.append({
                "drug_code": drug_code,
                "risk": "high",
                "category": pregnancy_category,
                "description": f"Pregnancy category {pregnancy_category}: contraindicated or high risk",
                "recommendation": "Avoid use during pregnancy; consider alternative therapy",
            })
        return results

    def check_breastfeeding(self, drug_code: str) -> list[ContraindicationRule]:
        return self.check_drug_condition(drug_code, "lactation")


class AllergyEngine:
    def __init__(self, db: Session, lab_id: int | None = None):
        self.db = db
        self.lab_id = lab_id

    def check_drug_allergy(self, drug_code: str, allergen_code: str) -> AllergyRule | None:
        q = self.db.query(AllergyRule).filter(
            AllergyRule.drug_code == drug_code,
            AllergyRule.allergen_code == allergen_code,
        )
        return q.first()

    def check_patient_allergies(self, drug_code: str, patient_allergens: list[str]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for allergen_code in patient_allergens:
            rule = self.check_drug_allergy(drug_code, allergen_code)
            if rule:
                results.append({
                    "allergen_code": rule.allergen_code,
                    "drug_code": rule.drug_code,
                    "severity": rule.severity.value,
                    "reaction": rule.reaction,
                    "recommendation": rule.recommendation,
                })
        return results

    def classify_severity(self, severity: InteractionSeverity) -> dict[str, Any]:
        classification = {
            InteractionSeverity.CONTRAINDICATED: {
                "level": 4,
                "label": "Severe Allergy",
                "action": "Do not administer",
                "color": "black",
            },
            InteractionSeverity.MAJOR: {
                "level": 3,
                "label": "Moderate-Severe",
                "action": "Avoid unless benefit outweighs risk",
                "color": "red",
            },
            InteractionSeverity.MODERATE: {
                "level": 2,
                "label": "Moderate",
                "action": "Use with caution; pre-medicate if necessary",
                "color": "orange",
            },
            InteractionSeverity.MINOR: {
                "level": 1,
                "label": "Mild",
                "action": "Monitor for symptoms",
                "color": "yellow",
            },
        }
        return classification.get(severity, {"level": -1, "label": "Unknown", "action": "Unknown", "color": "gray"})


class DoseEngine:
    def __init__(self, db: Session, lab_id: int | None = None):
        self.db = db
        self.lab_id = lab_id

    def calculate_dose(
        self,
        drug_code: str,
        indication_code: str | None = None,
        age_months: int | None = None,
        weight_kg: float | None = None,
    ) -> list[dict[str, Any]]:
        q = self.db.query(DoseGuideline).filter(DoseGuideline.drug_code == drug_code)
        if indication_code:
            q = q.filter(DoseGuideline.indication_code == indication_code)
        if age_months is not None:
            q = q.filter(
                or_(
                    DoseGuideline.age_min_months.is_(None),
                    DoseGuideline.age_min_months <= age_months,
                ),
                or_(
                    DoseGuideline.age_max_months.is_(None),
                    DoseGuideline.age_max_months >= age_months,
                ),
            )
        if weight_kg is not None:
            q = q.filter(
                or_(
                    DoseGuideline.weight_min_kg.is_(None),
                    DoseGuideline.weight_min_kg <= weight_kg,
                ),
                or_(
                    DoseGuideline.weight_max_kg.is_(None),
                    DoseGuideline.weight_max_kg >= weight_kg,
                ),
            )

        results: list[dict[str, Any]] = []
        for guideline in q.all():
            result: dict[str, Any] = {
                "drug_code": guideline.drug_code,
                "indication_code": guideline.indication_code,
                "dose_min": guideline.dose_min,
                "dose_max": guideline.dose_max,
                "dose_unit": guideline.dose_unit,
                "frequency": guideline.frequency,
                "max_daily_dose": guideline.max_daily_dose,
                "route": guideline.route,
                "pediatric_note": guideline.pediatric_note,
                "pregnancy_note": guideline.pregnancy_note,
                "breastfeeding_note": guideline.breastfeeding_note,
            }
            results.append(result)

        if not results:
            results.append({
                "drug_code": drug_code,
                "note": "Standard dosing not found in guidelines for this combination",
            })

        return results

    def calculate_pediatric_dose(
        self,
        drug_code: str,
        age_months: int,
        weight_kg: float,
        indication_code: str | None = None,
    ) -> list[dict[str, Any]]:
        return self.calculate_dose(
            drug_code=drug_code,
            indication_code=indication_code,
            age_months=age_months,
            weight_kg=weight_kg,
        )

    def calculate_renal_adjustment(
        self,
        drug_code: str,
        egfr: float,
        weight_kg: float | None = None,
    ) -> dict[str, Any]:
        guideline = self.db.query(DoseGuideline).filter(
            DoseGuideline.drug_code == drug_code,
            DoseGuideline.renal_adjustment.isnot(None),
        ).first()

        # Three outcomes, kept apart on purpose. This previously answered
        # requires_adjustment=False with "No adjustment needed based on
        # guidelines" in every case where no adjustment was found -- including
        # the case where the platform holds no renal guideline for the drug at
        # all. Absence of data is not a negative finding: many drugs require a
        # reduced dose in renal impairment, so telling a prescriber that no
        # adjustment is needed, for a drug nothing is known about, can leave a
        # full dose in place for a patient with a low eGFR.
        #
        # `assessed` therefore says whether an assessment happened, and
        # `requires_adjustment` is None until one has. The wording below states
        # what the system knows; it does not offer clinical advice of its own.
        result: dict[str, Any] = {
            "drug_code": drug_code,
            "egfr": egfr,
            "assessed": False,
            "requires_adjustment": None,
            "adjusted_dose": None,
            "recommendation": (
                "No renal dosing guideline is on file for this drug. Renal dose "
                "adjustment has NOT been assessed."
            ),
        }

        if not guideline or not guideline.renal_adjustment:
            return result

        adjustments = guideline.renal_adjustment
        if isinstance(adjustments, str):
            # The physical column is `text`, not jsonb. This branch reads Generation
            # A (Column(JSON), decoded for us) and Generation B (Column(Text), a raw
            # JSON string) identically, so renal assessment keeps working whichever
            # ORM generation is in place. Without it, the isinstance check below is
            # always False against a Text column and every drug reports
            # "not assessed" -- fail-safe, but silently unassessable forever.
            try:
                adjustments = json.loads(adjustments)
            except (ValueError, TypeError):
                adjustments = None
        if not isinstance(adjustments, list):
            # A guideline exists but its renal_adjustment is not the list of eGFR
            # bands this code knows how to read, so nothing was assessed.
            result["recommendation"] = (
                "A renal guideline is on file for this drug but its adjustment "
                "data is not in a form this service can evaluate. Renal dose "
                "adjustment has NOT been assessed."
            )
            return result

        result["assessed"] = True
        result["requires_adjustment"] = False
        result["recommendation"] = (
            "The renal guideline on file specifies dose bands by eGFR, and this "
            "eGFR falls outside all of them. No adjustment is specified for it."
        )
        for adj in adjustments:
            egfr_range = adj.get("egfr_range", {})
            egfr_min = egfr_range.get("min", 0)
            egfr_max = egfr_range.get("max", 999)
            if egfr_min <= egfr <= egfr_max:
                result["requires_adjustment"] = True
                result["adjusted_dose"] = adj.get("dose", "See recommendation")
                result["recommendation"] = adj.get("recommendation", "Adjust dose per renal function")
                result["adjustment_detail"] = adj
                break

        return result

    def check_therapeutic_monitoring(self, drug_code: str) -> DrugMonitoring | None:
        return self.db.query(DrugMonitoring).filter(DrugMonitoring.drug_code == drug_code).first()


class ClinicalGuidelineService:
    def __init__(self, db: Session, lab_id: int | None = None):
        self.db = db
        self.lab_id = lab_id

    def get_guidelines(
        self,
        drug_code: str | None = None,
        condition_code: str | None = None,
        specialty: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[ClinicalGuideline], int]:
        q = self.db.query(ClinicalGuideline).filter(ClinicalGuideline.is_active, ~ClinicalGuideline.is_deleted)
        if drug_code:
            q = q.filter(ClinicalGuideline.drug_codes.contains([drug_code]))
        if condition_code:
            q = q.filter(ClinicalGuideline.condition_codes.contains([condition_code]))
        total = q.count()
        items = q.order_by(ClinicalGuideline.title).offset(skip).limit(limit).all()
        return items, total


class PolypharmacyChecker:
    def __init__(self, db: Session, lab_id: int | None = None):
        self.db = db
        self.lab_id = lab_id
        self.interaction_engine = DrugInteractionEngine(db, lab_id)

    def check_polypharmacy(self, active_drug_codes: list[str]) -> dict[str, Any]:
        result: dict[str, Any] = {
            "total_medications": len(active_drug_codes),
            "is_polypharmacy": len(active_drug_codes) >= 5,
            "interactions": [],
            "recommendations": [],
        }

        if result["is_polypharmacy"]:
            result["recommendations"].append(
                "Patient is on 5 or more medications — review for deprescribing opportunities",
            )

        interactions = self.interaction_engine.check_multiple_drugs(active_drug_codes)
        result["interactions"] = interactions

        severe_count = sum(1 for i in interactions if i.get("severity") in ("contraindicated", "major"))
        if severe_count > 0:
            result["recommendations"].append(
                f"Found {severe_count} severe or contraindicated interaction(s) — urgent clinical review required",
            )

        return result

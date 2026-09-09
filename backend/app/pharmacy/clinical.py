from __future__ import annotations

import json
import logging
import uuid
from typing import Any

from sqlalchemy import Text, cast, or_
from sqlalchemy.orm import Session

from app.pharmacy.enums import InteractionSeverity
from app.pharmacy.models import (
    AllergyRule,
    ClinicalGuideline,
    ContraindicationRule,
    DoseGuideline,
    DrugCatalog,
    DrugInteractionRule,
    DrugMonitoring,
)

logger = logging.getLogger("gula.pharmacy.clinical")


class DrugResolver:
    """Resolves a caller-supplied drug reference to the internal catalog key.

    Clinical rules are related to a drug by ``pharmacy_drug_catalog.id``
    (CANONICAL_DRUG_CONTRACT §7), never by business code. Callers may still
    pass a ``drug_code`` — it is a legitimate search key (§4) — but it is
    resolved to the foreign key here, so editing a code can never detach a
    rule. A reference that matches no drug resolves to ``None``, and every
    engine below then returns no rules rather than falling back to a
    code-based match.

    The catalog is global (§6), so no tenant filter is applied to resolution.
    """

    def __init__(self, db: Session):
        self.db = db

    def by_code(self, drug_code: str) -> int | None:
        row = (
            self.db.query(DrugCatalog.id)
            .filter(DrugCatalog.drug_code == drug_code, ~DrugCatalog.is_deleted)
            .first()
        )
        return int(row[0]) if row else None

    def by_public_id(self, public_drug_id: str | uuid.UUID) -> int | None:
        if isinstance(public_drug_id, str):
            try:
                public_drug_id = uuid.UUID(public_drug_id)
            except ValueError:
                return None
        row = (
            self.db.query(DrugCatalog.id)
            .filter(DrugCatalog.drug_id == public_drug_id, ~DrugCatalog.is_deleted)
            .first()
        )
        return int(row[0]) if row else None

    def codes_to_ids(self, drug_codes: list[str]) -> dict[str, int]:
        """Resolve many codes in one query; unmatched codes are simply absent."""
        if not drug_codes:
            return {}
        rows = (
            self.db.query(DrugCatalog.drug_code, DrugCatalog.id)
            .filter(DrugCatalog.drug_code.in_(drug_codes), ~DrugCatalog.is_deleted)
            .all()
        )
        return {code: int(pk) for code, pk in rows}


class DrugInteractionEngine:
    def __init__(self, db: Session, lab_id: int | None = None):
        self.db = db
        self.lab_id = lab_id
        self.resolver = DrugResolver(db)

    def check_interaction_by_id(
        self, drug_id_a: int, drug_id_b: int,
    ) -> DrugInteractionRule | None:
        """The canonical lookup: both sides are catalog foreign keys.

        A pair is stored once in either column order, so both orders are
        matched.
        """
        return (
            self.db.query(DrugInteractionRule)
            .filter(
                ~DrugInteractionRule.is_deleted,
                or_(
                    DrugInteractionRule.drug_id_a == drug_id_a,
                    DrugInteractionRule.drug_id_b == drug_id_a,
                ),
                or_(
                    DrugInteractionRule.drug_id_a == drug_id_b,
                    DrugInteractionRule.drug_id_b == drug_id_b,
                ),
            )
            .first()
        )

    def check_interaction(
        self, drug_a_code: str, drug_b_code: str,
    ) -> DrugInteractionRule | None:
        ids = self.resolver.codes_to_ids([drug_a_code, drug_b_code])
        id_a, id_b = ids.get(drug_a_code), ids.get(drug_b_code)
        if id_a is None or id_b is None:
            return None
        return self.check_interaction_by_id(id_a, id_b)

    def check_multiple_drugs(self, drug_codes: list[str]) -> list[dict[str, Any]]:
        ids = self.resolver.codes_to_ids(drug_codes)
        interactions: list[dict[str, Any]] = []
        for i in range(len(drug_codes)):
            for j in range(i + 1, len(drug_codes)):
                id_a, id_b = ids.get(drug_codes[i]), ids.get(drug_codes[j])
                if id_a is None or id_b is None:
                    continue
                rule = self.check_interaction_by_id(id_a, id_b)
                if rule:
                    interactions.append({
                        "drug_a": drug_codes[i],
                        "drug_b": drug_codes[j],
                        "severity": rule.severity,
                        "description": rule.description,
                        "clinical_consequence": rule.clinical_consequence,
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
        self.resolver = DrugResolver(db)

    def check_drug_condition_by_id(
        self, drug_id: int, condition_value: str,
    ) -> list[ContraindicationRule]:
        """The canonical lookup, keyed on the catalog foreign key."""
        return (
            self.db.query(ContraindicationRule)
            .filter(
                ContraindicationRule.drug_id == drug_id,
                ContraindicationRule.contraindication_value == condition_value,
                ~ContraindicationRule.is_deleted,
            )
            .all()
        )

    def check_drug_condition(self, drug_code: str, condition_code: str) -> list[ContraindicationRule]:
        drug_id = self.resolver.by_code(drug_code)
        if drug_id is None:
            return []
        return self.check_drug_condition_by_id(drug_id, condition_code)

    def check_patient_conditions(self, drug_code: str, condition_codes: list[str]) -> list[dict[str, Any]]:
        drug_id = self.resolver.by_code(drug_code)
        if drug_id is None:
            return []
        results: list[dict[str, Any]] = []
        for cond_code in condition_codes:
            for rule in self.check_drug_condition_by_id(drug_id, cond_code):
                results.append({
                    "drug_id": rule.drug_id,
                    "drug_code": drug_code,
                    "contraindication_type": rule.contraindication_type,
                    "contraindication_value": rule.contraindication_value,
                    "severity": rule.severity,
                    "description": rule.description,
                    "clinical_consequence": rule.clinical_consequence,
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
        self.resolver = DrugResolver(db)

    def check_drug_allergy_by_id(self, drug_id: int, allergen_code: str) -> AllergyRule | None:
        """The canonical lookup, keyed on the catalog foreign key.

        ``allergen_code`` identifies the allergen, not the drug; it is matched
        against either the coded allergen or its name.
        """
        return (
            self.db.query(AllergyRule)
            .filter(
                AllergyRule.drug_id == drug_id,
                ~AllergyRule.is_deleted,
                or_(
                    AllergyRule.allergen_code == allergen_code,
                    AllergyRule.allergen == allergen_code,
                ),
            )
            .first()
        )

    def check_drug_allergy(self, drug_code: str, allergen_code: str) -> AllergyRule | None:
        drug_id = self.resolver.by_code(drug_code)
        if drug_id is None:
            return None
        return self.check_drug_allergy_by_id(drug_id, allergen_code)

    def check_patient_allergies(self, drug_code: str, patient_allergens: list[str]) -> list[dict[str, Any]]:
        drug_id = self.resolver.by_code(drug_code)
        if drug_id is None:
            return []
        results: list[dict[str, Any]] = []
        for allergen_code in patient_allergens:
            rule = self.check_drug_allergy_by_id(drug_id, allergen_code)
            if rule:
                results.append({
                    "allergen": rule.allergen,
                    "allergen_code": rule.allergen_code,
                    "drug_id": rule.drug_id,
                    "drug_code": drug_code,
                    "severity": rule.severity,
                    "reaction_type": rule.reaction_type,
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
        self.resolver = DrugResolver(db)

    def calculate_dose(
        self,
        drug_code: str,
        indication_code: str | None = None,
        age_months: int | None = None,
        weight_kg: float | None = None,
    ) -> list[dict[str, Any]]:
        drug_id = self.resolver.by_code(drug_code)
        if drug_id is None:
            return [{
                "drug_code": drug_code,
                "note": "Standard dosing not found in guidelines for this combination",
            }]

        q = self.db.query(DoseGuideline).filter(
            DoseGuideline.drug_id == drug_id,
            ~DoseGuideline.is_deleted,
        )
        if indication_code:
            q = q.filter(DoseGuideline.indication == indication_code)
        if age_months is not None:
            # The schema bounds age in years; the caller's months are converted
            # rather than the column being reinterpreted.
            age_years = age_months / 12.0
            q = q.filter(
                or_(
                    DoseGuideline.age_min_years.is_(None),
                    DoseGuideline.age_min_years <= age_years,
                ),
                or_(
                    DoseGuideline.age_max_years.is_(None),
                    DoseGuideline.age_max_years >= age_years,
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
                "drug_id": guideline.drug_id,
                "drug_code": drug_code,
                "indication": guideline.indication,
                "dose_min": guideline.dose_min,
                "dose_max": guideline.dose_max,
                "dose_unit": guideline.dose_unit,
                "frequency": guideline.frequency,
                "max_daily_dose": guideline.max_daily_dose,
                "duration": guideline.duration,
                "route": guideline.route,
                "pediatric_note": guideline.pediatric_note,
                "geriatric_note": guideline.geriatric_note,
                "pregnancy_category": guideline.pregnancy_category,
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
        result: dict[str, Any] = {
            "drug_code": drug_code,
            "egfr": egfr,
            "requires_adjustment": False,
            "adjusted_dose": None,
            "recommendation": "No adjustment needed based on guidelines",
        }

        drug_id = self.resolver.by_code(drug_code)
        if drug_id is None:
            return result

        guideline = self.db.query(DoseGuideline).filter(
            DoseGuideline.drug_id == drug_id,
            DoseGuideline.renal_adjustment.isnot(None),
            ~DoseGuideline.is_deleted,
        ).first()

        if not guideline or not guideline.renal_adjustment:
            return result

        # renal_adjustment is TEXT in the schema, not JSON. Structured banded
        # guidance is read when the text holds JSON; free text is surfaced as
        # the recommendation rather than discarded. No banding rule changed.
        raw = guideline.renal_adjustment
        try:
            adjustments: Any = json.loads(raw)
        except (TypeError, ValueError):
            result["recommendation"] = raw
            return result

        if isinstance(adjustments, list):
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

    def get_monitoring_records(
        self,
        drug_code: str,
        patient_id: int,
        lab_id: int | None = None,
        limit: int = 50,
    ) -> list[DrugMonitoring]:
        """Therapeutic-monitoring records for one patient on one drug.

        Replaces ``check_therapeutic_monitoring(drug_code)``. That method
        described a per-drug monitoring *rule* — required tests, therapeutic
        range, toxic level — none of which exists in the schema.
        ``pharmacy_drug_monitoring`` records monitoring *events*: a patient, a
        date and a measured value. This reads what the table holds.

        Unlike the other rule tables this one is tenant-scoped, so the
        laboratory is always part of the filter; passing no lab_id and having
        none configured returns nothing rather than crossing tenants.
        """
        effective_lab_id = lab_id if lab_id is not None else self.lab_id
        if effective_lab_id is None:
            return []
        drug_id = self.resolver.by_code(drug_code)
        if drug_id is None:
            return []
        return (
            self.db.query(DrugMonitoring)
            .filter(
                DrugMonitoring.drug_id == drug_id,
                DrugMonitoring.patient_id == patient_id,
                DrugMonitoring.lab_id == effective_lab_id,
                ~DrugMonitoring.is_deleted,
            )
            .order_by(DrugMonitoring.monitoring_date.desc())
            .limit(limit)
            .all()
        )


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
        """Guidelines are national reference data and are not tenant-filtered.

        The previous filters read ``drug_codes`` and ``condition_codes`` — JSON
        arrays that do not exist. The physical table stores drug advice in
        ``drug_recommendations`` (JSON) and the condition as ``condition`` plus
        an ``icd_code``, so those are what is matched here.
        """
        q = self.db.query(ClinicalGuideline).filter(
            ClinicalGuideline.is_active.is_(True), ~ClinicalGuideline.is_deleted
        )
        if drug_code:
            q = q.filter(cast(ClinicalGuideline.drug_recommendations, Text).ilike(f"%{drug_code}%"))
        if condition_code:
            q = q.filter(
                or_(
                    ClinicalGuideline.icd_code == condition_code,
                    ClinicalGuideline.condition.ilike(f"%{condition_code}%"),
                )
            )
        if specialty:
            q = q.filter(ClinicalGuideline.guideline_type == specialty)
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

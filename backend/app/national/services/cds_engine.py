from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.national.domain.encounter import Encounter
from app.national.domain.medication_catalog import MedicationCatalog
from app.national.domain.observation import Observation
from app.national.domain.patient import Patient


class ClinicalDecisionSupportEngine:
    """National Clinical Decision Support Engine."""

    def check_drug_interaction(
        self,
        db: Session,
        medication_code_a: str,
        medication_code_b: str,
    ) -> dict[str, Any]:
        medication_a = (
            db.query(MedicationCatalog)
            .filter(
                MedicationCatalog.medication_code == medication_code_a,
                MedicationCatalog.is_active,
                ~MedicationCatalog.is_deleted,
            )
            .first()
        )
        medication_b = (
            db.query(MedicationCatalog)
            .filter(
                MedicationCatalog.medication_code == medication_code_b,
                MedicationCatalog.is_active,
                ~MedicationCatalog.is_deleted,
            )
            .first()
        )

        if not medication_a or not medication_b:
            return {
                "has_interaction": False,
                "severity": None,
                "description": "One or both medications not found in catalog",
                "recommendation": None,
            }

        interactions_a = medication_a.interactions or []
        interactions_b = medication_b.interactions or []

        for interaction in interactions_a:
            if isinstance(interaction, dict):
                if interaction.get("medication_code") == medication_code_b:
                    return {
                        "has_interaction": True,
                        "severity": interaction.get("severity", "unknown"),
                        "description": interaction.get("description", ""),
                        "recommendation": interaction.get("recommendation"),
                        "mechanism": interaction.get("mechanism"),
                    }

        for interaction in interactions_b:
            if isinstance(interaction, dict):
                if interaction.get("medication_code") == medication_code_a:
                    return {
                        "has_interaction": True,
                        "severity": interaction.get("severity", "unknown"),
                        "description": interaction.get("description", ""),
                        "recommendation": interaction.get("recommendation"),
                        "mechanism": interaction.get("mechanism"),
                    }

        if (
            medication_a.therapeutic_class
            and medication_b.therapeutic_class
            and medication_a.therapeutic_class == medication_b.therapeutic_class
        ):
            return {
                "has_interaction": True,
                "severity": "moderate",
                "description": f"Both medications belong to the same therapeutic class: {medication_a.therapeutic_class}",
                "recommendation": "Consider therapeutic duplication risk",
            }

        return {
            "has_interaction": False,
            "severity": None,
            "description": "No known interaction between these medications",
            "recommendation": None,
        }

    def check_allergy_conflict(
        self,
        db: Session,
        patient_id: str,
        medication_code: str,
    ) -> list[dict[str, Any]]:
        medication = (
            db.query(MedicationCatalog)
            .filter(
                MedicationCatalog.medication_code == medication_code,
                MedicationCatalog.is_active,
                ~MedicationCatalog.is_deleted,
            )
            .first()
        )
        if not medication:
            return []

        allergy_observations = (
            db.query(Observation)
            .filter(
                Observation.patient_id == patient_id,
                Observation.category == "allergy",
                ~Observation.is_deleted,
            )
            .all()
        )

        medication_ingredients = set()
        if medication.ingredients:
            for ing in medication.ingredients:
                if isinstance(ing, dict):
                    medication_ingredients.add(ing.get("code", "").lower())
                    medication_ingredients.add(ing.get("name", "").lower())

        medication_ingredients.add(medication.medication_code.lower())
        medication_ingredients.add(medication.medication_name.lower())
        if medication.generic_name:
            medication_ingredients.add(medication.generic_name.lower())
        if medication.atc_code:
            medication_ingredients.add(medication.atc_code.lower())

        conflicts: list[dict[str, Any]] = []
        for allergy in allergy_observations:
            allergy_code = (allergy.code or "").lower()
            allergy_display = (allergy.code_display or "").lower()

            if allergy_code in medication_ingredients or allergy_display in medication_ingredients:
                conflicts.append(
                    {
                        "has_conflict": True,
                        "allergen": allergy.code_display or allergy.code,
                        "allergy_code": allergy.code,
                        "medication_code": medication_code,
                        "medication_name": medication.medication_name,
                        "severity": allergy.interpretation or "unknown",
                        "reaction": allergy.value_text or "",
                    },
                )

        return conflicts

    def check_duplicate_therapy(
        self,
        db: Session,
        patient_id: str,
        medication_code: str,
        therapeutic_class: str | None = None,
    ) -> list[dict[str, Any]]:
        medication = (
            db.query(MedicationCatalog)
            .filter(
                MedicationCatalog.medication_code == medication_code,
                MedicationCatalog.is_active,
                ~MedicationCatalog.is_deleted,
            )
            .first()
        )
        if not medication:
            return []

        target_class = therapeutic_class or medication.therapeutic_class
        if not target_class:
            return []

        active_medications = (
            db.query(MedicationCatalog)
            .filter(
                MedicationCatalog.therapeutic_class == target_class,
                MedicationCatalog.is_active,
                ~MedicationCatalog.is_deleted,
                MedicationCatalog.medication_code != medication_code,
            )
            .all()
        )

        medication_statements = (
            db.query(Observation)
            .filter(
                Observation.patient_id == patient_id,
                Observation.category == "medication",
                ~Observation.is_deleted,
                Observation.status.in_(["active", "intended"]),
            )
            .all()
        )

        active_codes = {obs.code for obs in medication_statements if obs.code}

        duplicates: list[dict[str, Any]] = []
        for active_med in active_medications:
            if active_med.medication_code in active_codes:
                duplicates.append(
                    {
                        "is_duplicate": True,
                        "existing_medication_code": active_med.medication_code,
                        "existing_medication_name": active_med.medication_name,
                        "new_medication_code": medication_code,
                        "new_medication_name": medication.medication_name,
                        "therapeutic_class": target_class,
                        "severity": "warning",
                        "recommendation": f"Patient already on {active_med.medication_name} in class {target_class}",
                    },
                )

        return duplicates

    def check_contraindications(
        self,
        db: Session,
        patient_id: str,
        medication_code: str,
    ) -> list[dict[str, Any]]:
        medication = (
            db.query(MedicationCatalog)
            .filter(
                MedicationCatalog.medication_code == medication_code,
                MedicationCatalog.is_active,
                ~MedicationCatalog.is_deleted,
            )
            .first()
        )
        if not medication:
            return []

        patient = (
            db.query(Patient)
            .filter(
                Patient.id == patient_id,
                ~Patient.is_deleted,
            )
            .first()
        )

        contraindications: list[dict[str, Any]] = []

        med_contraindications = medication.contraindications or []
        for ci in med_contraindications:
            if isinstance(ci, dict):
                ci_type = ci.get("type", "")
                ci_code = ci.get("code", "")

                if ci_type == "condition":
                    condition_obs = (
                        db.query(Observation)
                        .filter(
                            Observation.patient_id == patient_id,
                            Observation.category == "condition",
                            Observation.code == ci_code,
                            ~Observation.is_deleted,
                        )
                        .first()
                    )
                    if condition_obs:
                        contraindications.append(
                            {
                                "has_contraindication": True,
                                "type": "condition",
                                "code": ci_code,
                                "description": ci.get("description", ""),
                                "severity": ci.get("severity", "contraindicated"),
                                "details": condition_obs.code_display or ci_code,
                            },
                        )

                elif ci_type == "age":
                    if patient and patient.date_of_birth:
                        today = datetime.now().date()
                        age = today.year - patient.date_of_birth.year
                        if (today.month, today.day) < (
                            patient.date_of_birth.month,
                            patient.date_of_birth.day,
                        ):
                            age -= 1
                        min_age = ci.get("min_age") or medication.min_age_years
                        if min_age is not None and age < min_age:
                            contraindications.append(
                                {
                                    "has_contraindication": True,
                                    "type": "age",
                                    "code": "age_restriction",
                                    "description": ci.get("description", f"Minimum age: {min_age}"),
                                    "severity": ci.get("severity", "contraindicated"),
                                    "details": f"Patient age {age} is below minimum {min_age}",
                                },
                            )

                elif ci_type == "pregnancy":
                    if medication.pregnancy_category in ("X", "D"):
                        contraindications.append(
                            {
                                "has_contraindication": True,
                                "type": "pregnancy",
                                "code": "pregnancy_category",
                                "description": medication.pregnancy_category_description
                                if hasattr(medication, "pregnancy_category_description")
                                else f"Pregnancy category {medication.pregnancy_category}",
                                "severity": "contraindicated"
                                if medication.pregnancy_category == "X"
                                else "warning",
                                "details": f"Medication is pregnancy category {medication.pregnancy_category}",
                            },
                        )

                elif ci_type == "observation":
                    obs = (
                        db.query(Observation)
                        .filter(
                            Observation.patient_id == patient_id,
                            Observation.category == ci.get("observation_category", "laboratory"),
                            Observation.code == ci_code,
                            ~Observation.is_deleted,
                        )
                        .order_by(Observation.effective_datetime.desc())
                        .first()
                    )
                    if obs:
                        contraindications.append(
                            {
                                "has_contraindication": True,
                                "type": "observation",
                                "code": ci_code,
                                "description": ci.get("description", ""),
                                "severity": ci.get("severity", "warning"),
                                "details": f"{obs.code_display or ci_code}: {obs.value_quantity or obs.value_text}",
                            },
                        )

                else:
                    contraindications.append(
                        {
                            "has_contraindication": True,
                            "type": ci_type,
                            "code": ci_code,
                            "description": ci.get("description", "Known contraindication"),
                            "severity": ci.get("severity", "contraindicated"),
                            "details": ci.get("details", ""),
                        },
                    )

        return contraindications

    def check_duplicate_orders(
        self,
        db: Session,
        patient_id: str,
        order_type: str,
        order_code: str,
        time_window_hours: int = 24,
    ) -> list[dict[str, Any]]:
        cutoff = datetime.now() - timedelta(hours=time_window_hours)

        recent_observations = (
            db.query(Observation)
            .filter(
                Observation.patient_id == patient_id,
                Observation.category == order_type,
                Observation.code == order_code,
                ~Observation.is_deleted,
                Observation.effective_datetime >= cutoff,
            )
            .order_by(
                Observation.effective_datetime.desc(),
            )
            .all()
        )

        duplicates: list[dict[str, Any]] = []
        for obs in recent_observations:
            duplicates.append(
                {
                    "is_duplicate": True,
                    "existing_observation_id": obs.id,
                    "order_type": order_type,
                    "order_code": obs.code,
                    "order_display": obs.code_display or obs.code,
                    "ordered_at": obs.effective_datetime.isoformat()
                    if obs.effective_datetime
                    else None,
                    "time_window_hours": time_window_hours,
                    "status": obs.status,
                    "severity": "info",
                    "recommendation": f"Similar order already exists within {time_window_hours}h window",
                },
            )

        if not duplicates:
            recent_encounters = (
                db.query(Encounter)
                .filter(
                    Encounter.patient_id == patient_id,
                    ~Encounter.is_deleted,
                    or_(
                        Encounter.period_start >= cutoff,
                        Encounter.period_end >= cutoff,
                    ),
                )
                .all()
            )

            for enc in recent_encounters:
                if enc.reason_code == order_code:
                    duplicates.append(
                        {
                            "is_duplicate": True,
                            "source": "encounter",
                            "encounter_id": enc.id,
                            "order_type": order_type,
                            "order_code": enc.reason_code,
                            "order_display": enc.reason_description or enc.reason_code,
                            "time_window_hours": time_window_hours,
                            "severity": "info",
                            "recommendation": f"Recent encounter with same reason code within {time_window_hours}h",
                        },
                    )

        return duplicates

    def get_critical_alerts(
        self,
        db: Session,
        patient_id: str,
    ) -> list[dict[str, Any]]:
        alerts: list[dict[str, Any]] = []

        recent_observations = (
            db.query(Observation)
            .filter(
                Observation.patient_id == patient_id,
                ~Observation.is_deleted,
                Observation.interpretation.in_(
                    ["critical high", "critical low", "critical", "panic"],
                ),
            )
            .order_by(
                Observation.effective_datetime.desc(),
            )
            .limit(20)
            .all()
        )

        for obs in recent_observations:
            alerts.append(
                {
                    "alert_type": "critical_observation",
                    "severity": "critical",
                    "code": obs.code,
                    "display": obs.code_display or obs.code,
                    "value": obs.value_quantity or obs.value_text,
                    "interpretation": obs.interpretation,
                    "reference_range": f"{obs.reference_range_low} - {obs.reference_range_high}"
                    if obs.reference_range_low
                    else None,
                    "effective_datetime": obs.effective_datetime.isoformat()
                    if obs.effective_datetime
                    else None,
                },
            )

        recent_allergies = (
            db.query(Observation)
            .filter(
                Observation.patient_id == patient_id,
                Observation.category == "allergy",
                ~Observation.is_deleted,
                Observation.status == "active",
                Observation.interpretation.in_(["severe", "life-threatening"]),
            )
            .limit(10)
            .all()
        )

        for allergy in recent_allergies:
            alerts.append(
                {
                    "alert_type": "severe_allergy",
                    "severity": "warning",
                    "code": allergy.code,
                    "display": allergy.code_display or allergy.code,
                    "reaction": allergy.value_text,
                    "interpretation": allergy.interpretation,
                },
            )

        return alerts

    def evaluate_clinical_guidelines(
        self,
        db: Session,
        patient_id: str,
        guideline_id: str | None = None,
    ) -> list[dict[str, Any]]:
        patient = (
            db.query(Patient)
            .filter(
                Patient.id == patient_id,
                ~Patient.is_deleted,
            )
            .first()
        )
        if not patient:
            return []

        evaluations: list[dict[str, Any]] = []

        condition_observations = (
            db.query(Observation)
            .filter(
                Observation.patient_id == patient_id,
                Observation.category == "condition",
                ~Observation.is_deleted,
            )
            .all()
        )
        condition_codes = {obs.code for obs in condition_observations if obs.code}

        recent_observations = (
            db.query(Observation)
            .filter(
                Observation.patient_id == patient_id,
                ~Observation.is_deleted,
            )
            .order_by(
                Observation.effective_datetime.desc(),
            )
            .limit(50)
            .all()
        )

        obs_by_code: dict[str, list[Observation]] = {}
        for obs in recent_observations:
            obs_by_code.setdefault(obs.code or "", []).append(obs)

        guideline_registry = self._get_guideline_registry()
        applicable = []
        for gid, guideline in guideline_registry.items():
            if guideline_id and gid != guideline_id:
                continue
            conditions = guideline.get("conditions", [])
            for cond in conditions:
                if cond.get("code") in condition_codes:
                    applicable.append(guideline)
                    break

        for guideline in applicable:
            recommendations = []
            for step in guideline.get("steps", []):
                step_code = step.get("observation_code")
                step_value = step.get("threshold_value")
                step_comparison = step.get("comparison", ">=")

                if step_code and step_code in obs_by_code:
                    latest = obs_by_code[step_code][0]
                    met = self._compare_value(
                        latest.value_quantity,
                        step_value,
                        step_comparison,
                    )
                    if not met:
                        recommendations.append(
                            {
                                "guideline_id": guideline.get("id"),
                                "guideline_name": guideline.get("name"),
                                "step": step.get("name", ""),
                                "observation_code": step_code,
                                "current_value": latest.value_quantity,
                                "target_value": step_value,
                                "recommendation": step.get("recommendation", ""),
                                "is_met": False,
                            },
                        )
                    else:
                        recommendations.append(
                            {
                                "guideline_id": guideline.get("id"),
                                "guideline_name": guideline.get("name"),
                                "step": step.get("name", ""),
                                "observation_code": step_code,
                                "current_value": latest.value_quantity,
                                "target_value": step_value,
                                "recommendation": "Target met",
                                "is_met": True,
                            },
                        )

            if recommendations:
                evaluations.append(
                    {
                        "guideline_id": guideline.get("id"),
                        "guideline_name": guideline.get("name"),
                        "guideline_description": guideline.get("description", ""),
                        "recommendations": recommendations,
                        "overall_status": all(r["is_met"] for r in recommendations),
                    },
                )

        if not evaluations:
            evaluations.append(
                {
                    "guideline_id": guideline_id or "general",
                    "guideline_name": "No applicable guidelines",
                    "guideline_description": "No matching clinical guidelines found for this patient",
                    "recommendations": [],
                    "overall_status": None,
                },
            )

        return evaluations

    def calculate_risk_score(
        self,
        db: Session,
        patient_id: str,
        risk_type: str,
    ) -> dict[str, Any]:
        patient = (
            db.query(Patient)
            .filter(
                Patient.id == patient_id,
                ~Patient.is_deleted,
            )
            .first()
        )
        if not patient:
            return {"risk_type": risk_type, "score": None, "risk_level": "unknown", "factors": []}

        factors: list[dict[str, Any]] = []
        score = 0.0

        if risk_type == "cardiovascular":
            score, factors = self._calculate_cardiovascular_risk(db, patient)
        elif risk_type == "diabetes":
            score, factors = self._calculate_diabetes_risk(db, patient)
        elif risk_type == "readmission":
            score, factors = self._calculate_readmission_risk(db, patient)
        else:
            return {
                "risk_type": risk_type,
                "score": None,
                "risk_level": "unknown",
                "factors": factors,
            }

        risk_level = "low"
        if score >= 0.3:
            risk_level = "moderate"
        if score >= 0.5:
            risk_level = "high"
        if score >= 0.7:
            risk_level = "very_high"

        return {
            "risk_type": risk_type,
            "score": round(score, 4),
            "risk_level": risk_level,
            "factors": factors,
            "patient_id": patient_id,
            "calculated_at": datetime.now().isoformat(),
        }

    def get_preventive_care_recommendations(
        self,
        db: Session,
        patient_id: str,
    ) -> list[dict[str, Any]]:
        patient = (
            db.query(Patient)
            .filter(
                Patient.id == patient_id,
                ~Patient.is_deleted,
            )
            .first()
        )
        if not patient:
            return []

        recommendations: list[dict[str, Any]] = []

        today = datetime.now().date()
        age = None
        if patient.date_of_birth:
            age = today.year - patient.date_of_birth.year
            if (today.month, today.day) < (patient.date_of_birth.month, patient.date_of_birth.day):
                age -= 1

        gender = (
            patient.gender.value if hasattr(patient.gender, "value") else str(patient.gender or "")
        )

        recent_obs = (
            db.query(Observation)
            .filter(
                Observation.patient_id == patient_id,
                ~Observation.is_deleted,
            )
            .order_by(
                Observation.effective_datetime.desc(),
            )
            .all()
        )

        performed_codes = {obs.code for obs in recent_obs if obs.code}

        care_schedule = self._get_preventive_care_schedule()

        for item in care_schedule:
            if item.get("code") in performed_codes:
                continue

            age_min = item.get("age_min")
            age_max = item.get("age_max")
            if age is not None:
                if age_min is not None and age < age_min:
                    continue
                if age_max is not None and age > age_max:
                    continue

            applicable_genders = item.get("genders", [])
            if applicable_genders and gender.lower() not in [g.lower() for g in applicable_genders]:
                continue

            conditions_required = item.get("conditions_required", [])
            if conditions_required:
                patient_conditions = {
                    obs.code for obs in recent_obs if obs.category == "condition" and obs.code
                }
                if not conditions_required.intersection(patient_conditions):
                    continue

            recommendations.append(
                {
                    "code": item.get("code"),
                    "name": item.get("name"),
                    "name_ar": item.get("name_ar"),
                    "category": item.get("category"),
                    "frequency": item.get("frequency"),
                    "reason": item.get("reason"),
                    "priority": item.get("priority", "routine"),
                    "due": True,
                },
            )

        return recommendations

    def _compare_value(
        self,
        current: str | None,
        target: str | None,
        comparison: str,
    ) -> bool:
        if current is None or target is None:
            return True
        try:
            c = float(current)
            t = float(target)
            if comparison == ">=":
                return c >= t
            if comparison == "<=":
                return c <= t
            if comparison == ">":
                return c > t
            if comparison == "<":
                return c < t
            if comparison == "==":
                return c == t
        except (ValueError, TypeError):
            pass
        return True

    def _calculate_cardiovascular_risk(
        self,
        db: Session,
        patient: Patient,
    ) -> tuple[float, list[dict[str, Any]]]:
        factors: list[dict[str, Any]] = []
        score = 0.0

        obs_by_code: dict[str, str | None] = {}
        observations = (
            db.query(Observation)
            .filter(
                Observation.patient_id == patient.id,
                Observation.category.in_(["vital-signs", "laboratory"]),
                ~Observation.is_deleted,
            )
            .order_by(
                Observation.effective_datetime.desc(),
            )
            .limit(100)
            .all()
        )
        for obs in observations:
            if obs.code and obs.code not in obs_by_code:
                obs_by_code[obs.code] = obs.value_quantity

        bp_systolic = obs_by_code.get("8480-6") or obs_by_code.get("systolic_blood_pressure")
        if bp_systolic:
            try:
                sbp = float(bp_systolic)
                if sbp > 140:
                    score += 0.15
                    factors.append(
                        {
                            "name": "systolic_bp",
                            "value": sbp,
                            "contribution": 0.15,
                            "risk": "elevated",
                        },
                    )
                elif sbp > 120:
                    score += 0.05
                    factors.append(
                        {
                            "name": "systolic_bp",
                            "value": sbp,
                            "contribution": 0.05,
                            "risk": "pre_elevated",
                        },
                    )
            except (ValueError, TypeError):
                pass

        cholesterol = obs_by_code.get("2093-3") or obs_by_code.get("total_cholesterol")
        if cholesterol:
            try:
                tc = float(cholesterol)
                if tc > 240:
                    score += 0.1
                    factors.append(
                        {
                            "name": "total_cholesterol",
                            "value": tc,
                            "contribution": 0.1,
                            "risk": "elevated",
                        },
                    )
            except (ValueError, TypeError):
                pass

        ldl = obs_by_code.get("18262-6") or obs_by_code.get("ldl_cholesterol")
        if ldl:
            try:
                ldl_val = float(ldl)
                if ldl_val > 160:
                    score += 0.1
                    factors.append(
                        {
                            "name": "ldl_cholesterol",
                            "value": ldl_val,
                            "contribution": 0.1,
                            "risk": "elevated",
                        },
                    )
            except (ValueError, TypeError):
                pass

        hdl = obs_by_code.get("2085-9") or obs_by_code.get("hdl_cholesterol")
        if hdl:
            try:
                h = float(hdl)
                if h < 40:
                    score += 0.05
                    factors.append(
                        {"name": "hdl_cholesterol", "value": h, "contribution": 0.05, "risk": "low"},
                    )
            except (ValueError, TypeError):
                pass

        if patient.date_of_birth:
            age = (
                (datetime.now().date() - patient.date_of_birth.date()).days / 365.25
                if hasattr(patient.date_of_birth, "date")
                else 0
            )
            if age > 45:
                age_factor = min((age - 45) * 0.005, 0.15)
                score += age_factor
                factors.append(
                    {
                        "name": "age",
                        "value": round(age, 1),
                        "contribution": round(age_factor, 4),
                        "risk": "age_related",
                    },
                )

        smoking = obs_by_code.get("72166-2") or obs_by_code.get("smoking_status")
        if smoking:
            score += 0.1
            factors.append(
                {"name": "smoking", "value": smoking, "contribution": 0.1, "risk": "smoker"},
            )

        diabetes_obs = (
            db.query(Observation)
            .filter(
                Observation.patient_id == patient.id,
                Observation.category == "condition",
                Observation.code.in_(["44054006", "E11", "E10", "250.0"]),
                ~Observation.is_deleted,
            )
            .first()
        )
        if diabetes_obs:
            score += 0.15
            factors.append(
                {"name": "diabetes", "value": True, "contribution": 0.15, "risk": "diabetic"},
            )

        return min(score, 1.0), factors

    def _calculate_diabetes_risk(
        self,
        db: Session,
        patient: Patient,
    ) -> tuple[float, list[dict[str, Any]]]:
        factors: list[dict[str, Any]] = []
        score = 0.0

        obs_by_code: dict[str, str | None] = {}
        observations = (
            db.query(Observation)
            .filter(
                Observation.patient_id == patient.id,
                Observation.category.in_(["vital-signs", "laboratory"]),
                ~Observation.is_deleted,
            )
            .order_by(
                Observation.effective_datetime.desc(),
            )
            .limit(100)
            .all()
        )
        for obs in observations:
            if obs.code and obs.code not in obs_by_code:
                obs_by_code[obs.code] = obs.value_quantity

        fasting_glucose = obs_by_code.get("1558-6") or obs_by_code.get("fasting_glucose")
        if fasting_glucose:
            try:
                fg = float(fasting_glucose)
                if fg >= 126:
                    score += 0.3
                    factors.append(
                        {
                            "name": "fasting_glucose",
                            "value": fg,
                            "contribution": 0.3,
                            "risk": "diabetic_range",
                        },
                    )
                elif fg >= 100:
                    score += 0.1
                    factors.append(
                        {
                            "name": "fasting_glucose",
                            "value": fg,
                            "contribution": 0.1,
                            "risk": "pre_diabetic",
                        },
                    )
            except (ValueError, TypeError):
                pass

        hba1c = obs_by_code.get("4548-4") or obs_by_code.get("hba1c")
        if hba1c:
            try:
                a1c = float(hba1c)
                if a1c >= 6.5:
                    score += 0.3
                    factors.append(
                        {
                            "name": "hba1c",
                            "value": a1c,
                            "contribution": 0.3,
                            "risk": "diabetic_range",
                        },
                    )
                elif a1c >= 5.7:
                    score += 0.1
                    factors.append(
                        {"name": "hba1c", "value": a1c, "contribution": 0.1, "risk": "pre_diabetic"},
                    )
            except (ValueError, TypeError):
                pass

        bmi_obs = obs_by_code.get("39156-5") or obs_by_code.get("bmi")
        if bmi_obs:
            try:
                bmi = float(bmi_obs)
                if bmi >= 30:
                    score += 0.15
                    factors.append(
                        {"name": "bmi", "value": bmi, "contribution": 0.15, "risk": "obese"},
                    )
                elif bmi >= 25:
                    score += 0.05
                    factors.append(
                        {"name": "bmi", "value": bmi, "contribution": 0.05, "risk": "overweight"},
                    )
            except (ValueError, TypeError):
                pass

        if patient.date_of_birth:
            age = (datetime.now().date() - patient.date_of_birth).days / 365.25
            if age > 45:
                score += 0.05
                factors.append(
                    {
                        "name": "age",
                        "value": round(age, 1),
                        "contribution": 0.05,
                        "risk": "age_risk",
                    },
                )

        hypertension = obs_by_code.get("8480-6") or obs_by_code.get("systolic_blood_pressure")
        if hypertension:
            try:
                bp = float(hypertension)
                if bp > 140:
                    score += 0.05
                    factors.append(
                        {
                            "name": "hypertension",
                            "value": bp,
                            "contribution": 0.05,
                            "risk": "hypertensive",
                        },
                    )
            except (ValueError, TypeError):
                pass

        return min(score, 1.0), factors

    def _calculate_readmission_risk(
        self,
        db: Session,
        patient: Patient,
    ) -> tuple[float, list[dict[str, Any]]]:
        factors: list[dict[str, Any]] = []
        score = 0.0

        recent_encounters = (
            db.query(Encounter)
            .filter(
                Encounter.patient_id == patient.id,
                ~Encounter.is_deleted,
            )
            .order_by(
                Encounter.period_start.desc(),
            )
            .limit(10)
            .all()
        )

        encounter_count_90d = 0
        cutoff_90d = datetime.now() - timedelta(days=90)
        for enc in recent_encounters:
            if enc.period_start and enc.period_start >= cutoff_90d:
                encounter_count_90d += 1

        if encounter_count_90d >= 3:
            score += 0.2
            factors.append(
                {
                    "name": "encounter_frequency",
                    "value": encounter_count_90d,
                    "contribution": 0.2,
                    "risk": "high_utilization",
                },
            )
        elif encounter_count_90d >= 2:
            score += 0.1
            factors.append(
                {
                    "name": "encounter_frequency",
                    "value": encounter_count_90d,
                    "contribution": 0.1,
                    "risk": "moderate_utilization",
                },
            )

        age = 0
        if patient.date_of_birth:
            age = (datetime.now().date() - patient.date_of_birth).days / 365.25
            if age > 75:
                score += 0.15
                factors.append(
                    {"name": "age", "value": round(age, 1), "contribution": 0.15, "risk": "elderly"},
                )
            elif age > 65:
                score += 0.1
                factors.append(
                    {"name": "age", "value": round(age, 1), "contribution": 0.1, "risk": "senior"},
                )

        chronic_conditions = (
            db.query(Observation)
            .filter(
                Observation.patient_id == patient.id,
                Observation.category == "condition",
                ~Observation.is_deleted,
            )
            .count()
        )
        if chronic_conditions >= 3:
            score += 0.15
            factors.append(
                {
                    "name": "chronic_conditions",
                    "value": chronic_conditions,
                    "contribution": 0.15,
                    "risk": "multimorbidity",
                },
            )
        elif chronic_conditions >= 1:
            score += 0.05
            factors.append(
                {
                    "name": "chronic_conditions",
                    "value": chronic_conditions,
                    "contribution": 0.05,
                    "risk": "has_condition",
                },
            )

        return min(score, 1.0), factors

    def _get_guideline_registry(self) -> dict[str, dict[str, Any]]:
        return {
            "htn_management": {
                "id": "htn_management",
                "name": "Hypertension Management",
                "description": "Guideline for managing hypertension based on JNC 8",
                "conditions": [
                    {"code": "38341003", "system": "SNOMED"},
                    {"code": "I10", "system": "ICD10"},
                ],
                "steps": [
                    {
                        "name": "Blood Pressure Control",
                        "observation_code": "8480-6",
                        "threshold_value": "140",
                        "comparison": "<=",
                        "recommendation": "Target BP < 140/90 mmHg",
                    },
                ],
            },
            "dm_management": {
                "id": "dm_management",
                "name": "Diabetes Mellitus Management",
                "description": "Guideline for glycemic control in type 2 diabetes",
                "conditions": [
                    {"code": "44054006", "system": "SNOMED"},
                    {"code": "E11", "system": "ICD10"},
                ],
                "steps": [
                    {
                        "name": "HbA1c Control",
                        "observation_code": "4548-4",
                        "threshold_value": "7.0",
                        "comparison": "<=",
                        "recommendation": "Target HbA1c < 7.0%",
                    },
                ],
            },
            "hyperlipidemia": {
                "id": "hyperlipidemia",
                "name": "Hyperlipidemia Management",
                "description": "Lipid management for cardiovascular risk reduction",
                "conditions": [
                    {"code": "55822004", "system": "SNOMED"},
                    {"code": "E78", "system": "ICD10"},
                ],
                "steps": [
                    {
                        "name": "LDL Cholesterol Control",
                        "observation_code": "18262-6",
                        "threshold_value": "100",
                        "comparison": "<=",
                        "recommendation": "Target LDL < 100 mg/dL",
                    },
                ],
            },
        }

    def _get_preventive_care_schedule(self) -> list[dict[str, Any]]:
        return [
            {
                "code": "influenza_vaccine",
                "name": "Influenza Vaccine",
                "name_ar": "لقاح الإنفلونزا",
                "category": "immunization",
                "frequency": "annual",
                "age_min": 6,
                "age_max": None,
                "genders": [],
                "conditions_required": set(),
                "reason": "Annual influenza vaccination for all individuals aged 6 months and older",
                "priority": "high",
            },
            {
                "code": "mammogram",
                "name": "Mammography Screening",
                "name_ar": "تصوير الثدي بالأشعة",
                "category": "screening",
                "frequency": "biennial",
                "age_min": 40,
                "age_max": 74,
                "genders": ["female"],
                "conditions_required": set(),
                "reason": "Breast cancer screening for women aged 40-74",
                "priority": "high",
            },
            {
                "code": "colonoscopy",
                "name": "Colon Cancer Screening",
                "name_ar": "فحص سرطان القولون",
                "category": "screening",
                "frequency": "10_years",
                "age_min": 45,
                "age_max": 75,
                "genders": [],
                "conditions_required": set(),
                "reason": "Colorectal cancer screening for adults aged 45-75",
                "priority": "high",
            },
            {
                "code": "fasting_glucose",
                "name": "Fasting Blood Glucose",
                "name_ar": "سكر الدم صائماً",
                "category": "screening",
                "frequency": "3_years",
                "age_min": 40,
                "age_max": None,
                "genders": [],
                "conditions_required": {"obesity"},
                "reason": "Diabetes screening for adults 40+ with risk factors",
                "priority": "moderate",
            },
            {
                "code": "lipid_panel",
                "name": "Lipid Panel",
                "name_ar": "فحص الدهون",
                "category": "screening",
                "frequency": "5_years",
                "age_min": 20,
                "age_max": None,
                "genders": [],
                "conditions_required": set(),
                "reason": "Cardiovascular risk screening for adults aged 20+",
                "priority": "moderate",
            },
            {
                "code": "childhood_vaccines",
                "name": "Childhood Immunization Schedule",
                "name_ar": "جدول تطعيمات الأطفال",
                "category": "immunization",
                "frequency": "schedule",
                "age_min": 0,
                "age_max": 18,
                "genders": [],
                "conditions_required": set(),
                "reason": "Routine childhood immunizations per national schedule",
                "priority": "high",
            },
        ]

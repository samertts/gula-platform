from __future__ import annotations

import logging
import math
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("gula.national.intelligence.clinical")

_EVIDENCE_LEVELS = ["A", "B", "C", "D"]
_SEVERITY_MILD = "mild"
_SEVERITY_MODERATE = "moderate"
_SEVERITY_SEVERE = "severe"
_SEVERITY_CRITICAL = "critical"

_DRUG_CLASSES: dict[str, str] = {
    "metformin": "biguanide",
    "insulin": "insulin",
    "atorvastatin": "statin",
    "rosuvastatin": "statin",
    "simvastatin": "statin",
    "lisinopril": "ace_inhibitor",
    "enalapril": "ace_inhibitor",
    "amlodipine": "calcium_channel_blocker",
    "omeprazole": "proton_pump_inhibitor",
    "warfarin": "anticoagulant",
    "heparin": "anticoagulant",
    "clopidogrel": "antiplatelet",
    "aspirin": "antiplatelet",
    "ibuprofen": "nsaid",
    "naproxen": "nsaid",
    "furosemide": "loop_diuretic",
    "hydrochlorothiazide": "thiazide_diuretic",
}

_INTERACTION_DB: dict[tuple[str, str], dict[str, Any]] = {
    ("warfarin", "aspirin"): {
        "severity": "severe",
        "description": "Increased bleeding risk",
        "mechanism": "Additive anticoagulant effect",
        "recommendation": "Monitor INR closely",
    },
    ("ace_inhibitor", "nsaid"): {
        "severity": "moderate",
        "description": "Reduced antihypertensive effect, increased renal risk",
        "mechanism": "Prostaglandin synthesis inhibition",
        "recommendation": "Monitor blood pressure and renal function",
    },
    ("statin", "anticoagulant"): {
        "severity": "moderate",
        "description": "Increased anticoagulant effect",
        "mechanism": "CYP450 inhibition",
        "recommendation": "Monitor INR and adjust dose",
    },
}

_PREVENTIVE_SCREENINGS: dict[str, list[dict[str, Any]]] = {
    "F": [
        {"age_min": 18, "age_max": 120, "test": "cervical_cytology", "frequency_years": 3},
        {"age_min": 40, "age_max": 74, "test": "mammography", "frequency_years": 2},
        {"age_min": 50, "age_max": 75, "test": "colonoscopy", "frequency_years": 10},
        {"age_min": 18, "age_max": 120, "test": "bp_screening", "frequency_years": 2},
        {"age_min": 45, "age_max": 120, "test": "lipid_profile", "frequency_years": 5},
        {"age_min": 45, "age_max": 120, "test": "glucose_screening", "frequency_years": 3},
    ],
    "M": [
        {"age_min": 50, "age_max": 75, "test": "colonoscopy", "frequency_years": 10},
        {"age_min": 18, "age_max": 120, "test": "bp_screening", "frequency_years": 2},
        {"age_min": 45, "age_max": 120, "test": "lipid_profile", "frequency_years": 5},
        {"age_min": 45, "age_max": 120, "test": "glucose_screening", "frequency_years": 3},
    ],
}

_VACCINATION_SCHEDULE: list[dict[str, Any]] = [
    {"vaccine": "influenza", "age_group": "6m+", "frequency": "annual"},
    {"vaccine": "pneumococcal", "age_group": "65+", "frequency": "once"},
    {"vaccine": "tdap", "age_group": "11-64", "frequency": "every_10_years"},
    {"vaccine": "shingles", "age_group": "50+", "frequency": "two_dose"},
    {"vaccine": "hepatitis_b", "age_group": "0-18", "frequency": "three_dose_series"},
    {"vaccine": "mmr", "age_group": "1-12", "frequency": "two_dose"},
]

_CARE_GAP_GUIDELINES: list[dict[str, Any]] = [
    {
        "id": "diabetes_hba1c_annual",
        "condition": "diabetes",
        "test": "hba1c",
        "frequency_days": 365,
        "severity": "high",
        "description": "Annual HbA1c for diabetic patients",
    },
    {
        "id": "hypertension_bp_quarterly",
        "condition": "hypertension",
        "test": "bp_check",
        "frequency_days": 90,
        "severity": "high",
        "description": "Quarterly blood pressure check for hypertensive patients",
    },
    {
        "id": "lipid_annual",
        "condition": "hyperlipidemia",
        "test": "lipid_profile",
        "frequency_days": 365,
        "severity": "medium",
        "description": "Annual lipid profile for hyperlipidemia patients",
    },
    {
        "id": "cancer_screening_annual",
        "condition": "cancer_survivor",
        "test": "follow_up",
        "frequency_days": 365,
        "severity": "high",
        "description": "Annual follow-up for cancer survivors",
    },
]

_RISK_FACTOR_WEIGHTS: dict[str, float] = {
    "age_>_65": 2.0,
    "smoking": 2.5,
    "diabetes": 2.0,
    "hypertension": 1.8,
    "obesity": 1.5,
    "family_history_cvd": 2.0,
    "sedentary_lifestyle": 1.3,
    "high_cholesterol": 1.5,
    "chronic_kidney_disease": 2.5,
    "copd": 2.0,
}


@dataclass
class ClinicalRecommendation:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str = ""
    recommendation_type: str = ""
    title: str = ""
    description: str = ""
    evidence_level: str = "C"
    priority: int = 0
    conditions: list[str] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)


@dataclass
class DrugInteraction:
    medications: tuple[str, str] = ("", "")
    severity: str = _SEVERITY_MILD
    description: str = ""
    mechanism: str = ""
    recommendation: str = ""
    alternatives: list[str] = field(default_factory=list)


@dataclass
class DuplicateTherapy:
    medication: str = ""
    therapeutic_class: str = ""
    active_medications: list[str] = field(default_factory=list)
    severity: str = _SEVERITY_MILD
    consolidation_suggestion: str = ""


@dataclass
class CareGap:
    id: str = ""
    patient_id: str = ""
    guideline_id: str = ""
    description: str = ""
    severity: str = "medium"
    due_date: float = 0.0
    recommendations: list[str] = field(default_factory=list)


@dataclass
class RiskScore:
    score: float = 0.0
    category: str = "low"
    factors: list[dict[str, Any]] = field(default_factory=list)
    percentile: float = 0.0


@dataclass
class ClinicalAlert:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str = ""
    alert_type: str = ""
    severity: str = _SEVERITY_MILD
    message: str = ""
    created_at: float = field(default_factory=time.time)
    acknowledged: bool = False
    resolved: bool = False


class ClinicalRecommendationEngine:
    def __init__(self) -> None:
        self._guidelines: dict[str, list[dict[str, Any]]] = {}

    def load_guidelines(self, condition: str, guidelines: list[dict[str, Any]]) -> None:
        self._guidelines[condition] = guidelines

    def generate_recommendations(self, patient_id: str, context: dict[str, Any]) -> list[ClinicalRecommendation]:
        recommendations: list[ClinicalRecommendation] = []
        conditions = context.get("conditions", [])
        for condition in conditions:
            guidelines = self._guidelines.get(condition, [])
            for g in guidelines:
                rec = ClinicalRecommendation(
                    patient_id=patient_id,
                    recommendation_type=g.get("type", "general"),
                    title=g.get("title", f"Recommendation for {condition}"),
                    description=g.get("description", ""),
                    evidence_level=g.get("evidence_level", "C"),
                    priority=g.get("priority", 0),
                    conditions=[condition],
                    actions=g.get("actions", []),
                )
                recommendations.append(rec)
        if not recommendations:
            recommendations.append(
                ClinicalRecommendation(
                    patient_id=patient_id,
                    recommendation_type="general_health",
                    title="Routine Health Maintenance",
                    description="Continue routine health maintenance and age-appropriate screenings",
                    evidence_level="A",
                    priority=1,
                ),
            )
        return self.rank_recommendations(recommendations)

    def get_evidence_based_guidelines(self, condition: str) -> list[dict[str, Any]]:
        return self._guidelines.get(
            condition,
            [
                {
                    "condition": condition,
                    "title": f"Standard care for {condition}",
                    "evidence_level": "C",
                    "source": "Clinical practice guidelines",
                },
            ],
        )

    def rank_recommendations(self, recommendations: list[ClinicalRecommendation]) -> list[ClinicalRecommendation]:
        priority_map = {"A": 4, "B": 3, "C": 2, "D": 1}
        return sorted(
            recommendations,
            key=lambda r: (priority_map.get(r.evidence_level, 0), r.priority),
            reverse=True,
        )


class DrugInteractionEngine:
    def __init__(self) -> None:
        self._interactions: dict[tuple[str, str], dict[str, Any]] = {}
        for (a, b), data in _INTERACTION_DB.items():
            self._interactions[(a, b)] = data

    def register_interaction(
        self,
        drug_a: str,
        drug_b: str,
        severity: str,
        description: str,
        mechanism: str = "",
        recommendation: str = "",
    ) -> None:
        self._interactions[(drug_a, drug_b)] = {
            "severity": severity,
            "description": description,
            "mechanism": mechanism,
            "recommendation": recommendation,
        }

    def check_interactions(
        self,
        medications: list[str],
        patient_profile: dict[str, Any] | None = None,
    ) -> list[DrugInteraction]:
        interactions: list[DrugInteraction] = []
        for i, med_a in enumerate(medications):
            class_a = _DRUG_CLASSES.get(med_a.lower(), med_a.lower())
            for med_b in medications[i + 1:]:
                class_b = _DRUG_CLASSES.get(med_b.lower(), med_b.lower())
                key = (class_a, class_b)
                rev_key = (class_b, class_a)
                data = self._interactions.get(key) or self._interactions.get(rev_key)
                if data:
                    interactions.append(
                        DrugInteraction(
                            medications=(med_a, med_b),
                            severity=data["severity"],
                            description=data["description"],
                            mechanism=data.get("mechanism", ""),
                            recommendation=data.get("recommendation", ""),
                            alternatives=self.suggest_alternatives(med_a, data),
                        ),
                    )
        return interactions

    def get_severity(self, interaction: DrugInteraction) -> str:
        return interaction.severity

    def suggest_alternatives(self, medication: str, interaction: dict[str, Any]) -> list[str]:
        severity = interaction.get("severity", _SEVERITY_MILD)
        if severity in (_SEVERITY_SEVERE, _SEVERITY_CRITICAL):
            return [f"Consider alternative to {medication}"]
        return []


class DuplicateTherapyDetector:
    def __init__(self) -> None:
        self._patient_medications: dict[str, list[dict[str, Any]]] = {}

    def load_patient_medications(self, patient_id: str, medications: list[dict[str, Any]]) -> None:
        self._patient_medications[patient_id] = medications

    def get_therapeutic_class(self, medication: str) -> str:
        return _DRUG_CLASSES.get(medication.lower(), "unknown")

    def detect_duplicates(self, patient_id: str, medication: str) -> list[DuplicateTherapy]:
        duplicates: list[DuplicateTherapy] = []
        target_class = self.get_therapeutic_class(medication)
        active = self._patient_medications.get(patient_id, [])
        same_class_meds = [
            m for m in active
            if self.get_therapeutic_class(m.get("name", "")) == target_class
            and m.get("name", "").lower() != medication.lower()
            and m.get("status") == "active"
        ]
        if same_class_meds:
            dup = DuplicateTherapy(
                medication=medication,
                therapeutic_class=target_class,
                active_medications=[m["name"] for m in same_class_meds],
                severity=_SEVERITY_MODERATE if len(same_class_meds) > 1 else _SEVERITY_MILD,
                consolidation_suggestion=self.suggest_consolidation(
                    {"medication": medication, "therapeutic_class": target_class, "existing": [m["name"] for m in same_class_meds]},
                ),
            )
            duplicates.append(dup)
        return duplicates

    def suggest_consolidation(self, duplicates: dict[str, Any]) -> str:
        existing = duplicates.get("existing", [])
        med = duplicates.get("medication", "")
        if len(existing) == 1:
            return f"Consider consolidating {med} and {existing[0]} into a single agent"
        return f"Review all {duplicates.get('therapeutic_class', 'unknown')} agents and consolidate"


class PreventiveCareEngine:
    def get_age_appropriate_screenings(self, age: int, gender: str) -> list[dict[str, Any]]:
        screenings = _PREVENTIVE_SCREENINGS.get(gender.upper(), _PREVENTIVE_SCREENINGS.get("M", []))
        return [
            s for s in screenings
            if s["age_min"] <= age <= s["age_max"]
        ]

    def get_vaccination_schedule(self, patient: dict[str, Any]) -> list[dict[str, Any]]:
        age = patient.get("age", 0)
        due: list[dict[str, Any]] = []
        for vac in _VACCINATION_SCHEDULE:
            age_group = vac["age_group"]
            if ("6m+" in age_group and age >= 0.5) or ("65+" in age_group and age >= 65) or ("50+" in age_group and age >= 50) or ("11-64" in age_group and 11 <= age <= 64):
                due.append(vac)
        return due

    def get_due_preventive_care(self, patient: dict[str, Any]) -> list[dict[str, Any]]:
        age = patient.get("age", 30)
        gender = patient.get("gender", "M")
        screenings = self.get_age_appropriate_screenings(age, gender)
        vaccinations = self.get_vaccination_schedule(patient)
        return [
            {
                "type": "screening",
                "items": screenings,
            },
            {
                "type": "vaccination",
                "items": vaccinations,
            },
        ]


class CareGapDetector:
    def detect_care_gaps(self, patient_id: str, guidelines: list[dict[str, Any]] | None = None) -> list[CareGap]:
        active_guidelines = guidelines or _CARE_GAP_GUIDELINES
        gaps: list[CareGap] = []
        now = time.time()
        for g in active_guidelines:
            gap = CareGap(
                id=str(uuid.uuid4()),
                patient_id=patient_id,
                guideline_id=g["id"],
                description=g["description"],
                severity=g.get("severity", "medium"),
                due_date=now + g.get("frequency_days", 365) * 86400,
                recommendations=[g.get("description", "")],
            )
            gaps.append(gap)
        return gaps

    def get_gap_severity(self, gap: CareGap) -> str:
        return gap.severity

    def generate_closure_recommendations(self, gaps: list[CareGap]) -> list[str]:
        return [f"Schedule {g.description}" for g in gaps if g.severity in ("high", "critical")]


class RiskStratificationEngine:
    def get_risk_factors(self, patient: dict[str, Any]) -> list[dict[str, Any]]:
        factors: list[dict[str, Any]] = []
        age = patient.get("age", 0)
        if age > 65:
            factors.append({"factor": "age_>_65", "weight": _RISK_FACTOR_WEIGHTS["age_>_65"]})
        for condition in patient.get("conditions", []):
            weight = _RISK_FACTOR_WEIGHTS.get(condition.lower(), 0.5)
            factors.append({"factor": condition.lower(), "weight": weight})
        for lifestyle in patient.get("lifestyle", []):
            weight = _RISK_FACTOR_WEIGHTS.get(lifestyle.lower(), 0.5)
            factors.append({"factor": lifestyle.lower(), "weight": weight})
        return factors

    def calculate_risk_score(self, risk_factors: list[dict[str, Any]]) -> float:
        if not risk_factors:
            return 0.0
        raw_score = sum(f.get("weight", 0.5) for f in risk_factors)
        n = len(risk_factors)
        adjusted = raw_score * (1 + 0.1 * math.log1p(n))
        return round(min(adjusted / 10.0, 1.0), 4)

    def get_risk_category(self, score: float) -> str:
        if score >= 0.7:
            return "high"
        if score >= 0.4:
            return "moderate"
        if score >= 0.2:
            return "elevated"
        return "low"

    def stratify_risk(self, patient_id: str, patient: dict[str, Any] | None = None) -> RiskScore:
        factors = self.get_risk_factors(patient or {})
        score = self.calculate_risk_score(factors)
        category = self.get_risk_category(score)
        return RiskScore(
            score=score,
            category=category,
            factors=factors,
            percentile=round(score * 100, 1),
        )


class ClinicalAlertEngine:
    def __init__(self) -> None:
        self._alerts: dict[str, ClinicalAlert] = {}
        self._alert_rules: list[dict[str, Any]] = []

    def register_alert_rule(self, rule: dict[str, Any]) -> None:
        self._alert_rules.append(rule)

    def evaluate_alerts(self, patient_id: str, context: dict[str, Any] | None = None) -> list[ClinicalAlert]:
        generated: list[ClinicalAlert] = []
        for rule in self._alert_rules:
            condition_fn = rule.get("condition")
            if condition_fn and condition_fn(context or {}):
                alert = ClinicalAlert(
                    patient_id=patient_id,
                    alert_type=rule.get("type", "general"),
                    severity=rule.get("severity", _SEVERITY_MILD),
                    message=rule.get("message", "Alert triggered"),
                )
                self._alerts[alert.id] = alert
                generated.append(alert)
                logger.info("[ClinicalAlert] generated id=%s type=%s severity=%s", alert.id, alert.alert_type, alert.severity)
        return generated

    def prioritize_alerts(self, alerts: list[ClinicalAlert]) -> list[ClinicalAlert]:
        sev_order = {_SEVERITY_CRITICAL: 0, _SEVERITY_SEVERE: 1, _SEVERITY_MODERATE: 2, _SEVERITY_MILD: 3}
        return sorted(alerts, key=lambda a: (sev_order.get(a.severity, 99), a.created_at))

    def generate_alert_notification(self, alert: ClinicalAlert) -> dict[str, Any]:
        return {
            "alert_id": alert.id,
            "type": alert.alert_type,
            "severity": alert.severity,
            "message": alert.message,
            "patient_id": alert.patient_id,
            "requires_acknowledgement": alert.severity in (_SEVERITY_SEVERE, _SEVERITY_CRITICAL),
            "generated_at": alert.created_at,
        }

    def track_alert_resolution(self, alert_id: str) -> dict[str, Any]:
        alert = self._alerts.get(alert_id)
        if alert is None:
            raise ValueError(f"Alert {alert_id!r} not found")
        alert.resolved = True
        return {
            "alert_id": alert_id,
            "resolved": True,
            "resolved_at": time.time(),
        }


class CriticalResultEscalation:
    def __init__(self) -> None:
        self._criticality_rules: dict[str, dict[str, Any]] = {}
        self._responses: dict[str, dict[str, Any]] = {}

    def register_criticality_rule(
        self,
        test_code: str,
        critical_low: float | None,
        critical_high: float | None,
        escalation_path: str,
    ) -> None:
        self._criticality_rules[test_code] = {
            "critical_low": critical_low,
            "critical_high": critical_high,
            "escalation_path": escalation_path,
        }

    def classify_criticality(self, result: dict[str, Any]) -> str:
        test_code = result.get("test_code", "")
        value = result.get("value")
        if value is None:
            return "normal"
        rule = self._criticality_rules.get(test_code)
        if rule is None:
            return "unknown"
        val = float(value)
        if rule.get("critical_low") is not None and val <= rule["critical_low"]:
            return "critical_low"
        if rule.get("critical_high") is not None and val >= rule["critical_high"]:
            return "critical_high"
        return "normal"

    def get_escalation_path(self, criticality: str) -> list[dict[str, Any]]:
        paths: dict[str, list[dict[str, Any]]] = {
            "critical_low": [
                {"step": 1, "action": "notify_technologist", "timeout_min": 5},
                {"step": 2, "action": "notify_pathologist", "timeout_min": 15},
                {"step": 3, "action": "notify_attending_physician", "timeout_min": 30},
            ],
            "critical_high": [
                {"step": 1, "action": "notify_technologist", "timeout_min": 5},
                {"step": 2, "action": "notify_pathologist", "timeout_min": 15},
                {"step": 3, "action": "notify_attending_physician", "timeout_min": 30},
            ],
        }
        return paths.get(criticality, [])

    def notify_clinician(self, result: dict[str, Any], path: list[dict[str, Any]]) -> dict[str, Any]:
        notification_id = str(uuid.uuid4())
        record = {
            "notification_id": notification_id,
            "result": result,
            "escalation_path": path,
            "notified_at": time.time(),
            "steps_completed": 0,
        }
        self._responses[notification_id] = record
        logger.info(
            "[CriticalResultEscalation] notification id=%s test=%s value=%s",
            notification_id,
            result.get("test_code"),
            result.get("value"),
        )
        return record

    def track_response(self, result_id: str) -> dict[str, Any]:
        response = self._responses.get(result_id)
        if response is None:
            return {"result_id": result_id, "status": "unknown"}
        return {
            "result_id": result_id,
            "status": "acknowledged",
            "steps_completed": response.get("steps_completed", 0),
            "notified_at": response.get("notified_at"),
        }

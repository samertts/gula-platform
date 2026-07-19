from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

from app.ai.knowledge_graph import knowledge_graph
from app.ai.rag_pipeline import rag
from app.database import get_db
from sqlalchemy import text

logger = logging.getLogger("gula.ai.cds")


@dataclass
class CDSAlert:
    severity: str
    category: str
    message: str
    message_ar: str
    test_name: str | None = None
    value: float | None = None
    normal_range: str | None = None
    recommendation: str = ""
    recommendation_ar: str = ""
    evidence: list[str] = field(default_factory=list)


class ClinicalDecisionSupport:

    def __init__(self):
        self._critical_ranges: dict[str, tuple[float, float]] = {
            "glucose": (3.3, 27.8),
            "potassium": (2.5, 6.5),
            "sodium": (115, 160),
            "calcium": (1.5, 3.5),
            "hemoglobin": (40, 200),
            "platelets": (10, 1000),
            "ph": (6.8, 7.8),
        }

    def evaluate_result(self, test_name: str, value: float, unit: str = "", normal_low: float | None = None, normal_high: float | None = None, patient_age: int | None = None, patient_gender: str | None = None) -> list[CDSAlert]:
        alerts: list[CDSAlert] = []
        name_lower = test_name.lower()

        if normal_low is not None and normal_high is not None:
            if value < normal_low:
                alerts.append(self._alert("warning", "below_range", f"{test_name} is below normal range ({normal_low}-{normal_high} {unit})", f"{test_name} أقل من المدى الطبيعي ({normal_low}-{normal_high} {unit})", test_name, value, f"{normal_low}-{normal_high}", "Review clinical significance of low value", "مراجعة الدلالة السريرية للانخفاض"))
            elif value > normal_high:
                alerts.append(self._alert("warning", "above_range", f"{test_name} is above normal range ({normal_low}-{normal_high} {unit})", f"{test_name} أعلى من المدى الطبيعي ({normal_low}-{normal_high} {unit})", test_name, value, f"{normal_low}-{normal_high}", "Review clinical significance of high value", "مراجعة الدلالة السريرية للارتفاع"))

        for key, (crit_low, crit_high) in self._critical_ranges.items():
            if key in name_lower:
                if value < crit_low:
                    alerts.append(self._alert("critical", "panic_low", f"CRITICAL: {test_name} = {value} {unit} (panic low < {crit_low})", f"حرج: {test_name} = {value} {unit} (أقل من حد الخطر {crit_low})", test_name, value, f"Critical low: < {crit_low}", "Immediate clinical review required", "مراجعة سريرية فورية مطلوبة"))
                elif value > crit_high:
                    alerts.append(self._alert("critical", "panic_high", f"CRITICAL: {test_name} = {value} {unit} (panic high > {crit_high})", f"حرج: {test_name} = {value} {unit} (أعلى من حد الخطر {crit_high})", test_name, value, f"Critical high: > {crit_high}", "Immediate clinical review required", "مراجعة سريرية فورية مطلوبة"))

        if patient_age and patient_gender:
            age_alerts = self._check_age_specific(name_lower, value, patient_age, patient_gender)
            alerts.extend(age_alerts)

        return alerts

    def _alert(self, severity: str, category: str, msg: str, msg_ar: str, test_name: str, value: float, normal_range: str, rec: str, rec_ar: str) -> CDSAlert:
        return CDSAlert(severity=severity, category=category, message=msg, message_ar=msg_ar, test_name=test_name, value=value, normal_range=normal_range, recommendation=rec, recommendation_ar=rec_ar)

    def _check_age_specific(self, test_name: str, value: float, age: int, gender: str) -> list[CDSAlert]:
        alerts: list[CDSAlert] = []
        if "creatinine" in test_name and age > 60 and gender.upper() == "M":
            if value > 1.2:
                alerts.append(self._alert("warning", "age_related", f"Elevated creatinine ({value}) in {age}-year-old male may indicate age-related GFR decline", f"ارتفاع الكرياتينين ({value}) لدى رجل عمره {age} قد يشير إلى انخفاض GFR مرتبط بالعمر", test_name, value, "", "Consider calculating eGFR", "ينصح بحساب معدل الترشيح الكبيبي (eGFR)"))
        if "hemoglobin" in test_name and age > 70:
            if value < 11:
                alerts.append(self._alert("warning", "age_related", f"Low hemoglobin ({value}) in elderly patient ({age} years)", f"انخفاض الهيموغلوبين ({value}) لدى مريض مسن ({age} سنة)", test_name, value, "", "Investigate for anemia of chronic disease", "التحقق من فقر الدم المرتبط بالأمراض المزمنة"))
        return alerts

    async def generate_clinical_guidance(self, test_name: str, value: float, unit: str, normal_low: float | None, normal_high: float | None, patient_id: int | None = None) -> dict[str, Any]:
        alerts = self.evaluate_result(test_name, value, unit, normal_low, normal_high)

        knowledge_graph.initialize()
        kg_results = knowledge_graph.search_nodes(test_name, node_type="lab_test", limit=5)
        conditions: list[str] = []
        for node in kg_results:
            neighbors = knowledge_graph.get_neighbors(node.id, relationship="indicates")
            for neighbor, rel, weight in neighbors:
                if neighbor.node_type == "condition":
                    conditions.append(neighbor.label)

        severity = "critical" if any(a.severity == "critical" for a in alerts) else "warning" if alerts else "normal"

        return {
            "severity": severity,
            "alerts": [{"severity": a.severity, "category": a.category, "message": a.message, "message_ar": a.message_ar, "recommendation": a.recommendation, "recommendation_ar": a.recommendation_ar} for a in alerts],
            "possible_conditions": conditions,
            "is_critical": severity == "critical",
            "requires_immediate_action": severity == "critical",
        }

    async def evaluate_order(
        self, results: list[dict[str, Any]], patient_id: int | None = None, patient_age: int | None = None, patient_gender: str | None = None
    ) -> dict[str, Any]:
        all_alerts: list[CDSAlert] = []
        total_critical = 0
        condition_map: dict[str, int] = {}

        for r in results:
            alerts = self.evaluate_result(
                r.get("test_name", ""),
                r.get("value", 0),
                r.get("unit", ""),
                r.get("normal_range_low"),
                r.get("normal_range_high"),
                patient_age,
                patient_gender,
            )
            all_alerts.extend(alerts)
            if any(a.severity == "critical" for a in alerts):
                total_critical += 1

        knowledge_graph.initialize()
        for alert in all_alerts:
            if alert.test_name:
                nodes = knowledge_graph.search_nodes(alert.test_name, node_type="lab_test", limit=3)
                for node in nodes:
                    neighbors = knowledge_graph.get_neighbors(node.id, relationship="indicates")
                    for neighbor, rel, weight in neighbors:
                        if neighbor.node_type == "condition":
                            condition_map[neighbor.label] = condition_map.get(neighbor.label, 0) + 1

        sorted_conditions = sorted(condition_map.items(), key=lambda x: x[1], reverse=True)

        severity = "critical" if total_critical > 0 else "warning" if all_alerts else "normal"

        return {
            "severity": severity,
            "total_alerts": len(all_alerts),
            "critical_count": total_critical,
            "alerts": [{"severity": a.severity, "category": a.category, "message": a.message, "message_ar": a.message_ar, "test_name": a.test_name} for a in all_alerts],
            "suspected_conditions": [{"condition": c, "evidence_count": n} for c, n in sorted_conditions[:5]],
            "is_critical": severity == "critical",
            "requires_immediate_action": severity == "critical",
        }


cds = ClinicalDecisionSupport()

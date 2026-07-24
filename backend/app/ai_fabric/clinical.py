from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any

from app.ai_fabric.base import InferenceRequest
from app.ai_fabric.gateway import AIGateway

logger = logging.getLogger("gula.ai_fabric.clinical")


@dataclass
class ClinicalRecommendation:
    id: str = ""
    type: str = ""
    severity: str = "info"
    title: str = ""
    description: str = ""
    evidence: list[str] = field(default_factory=list)
    confidence: float = 0.0
    action: str = ""


@dataclass
class DrugInteraction:
    drug_a: str = ""
    drug_b: str = ""
    severity: str = "moderate"
    description: str = ""
    recommendation: str = ""
    mechanism: str = ""
    evidence_level: str = "C"


@dataclass
class ClinicalSummary:
    patient_id: str = ""
    summary: str = ""
    key_findings: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    generated_at: float = 0.0
    model: str = ""


class ClinicalDecisionSupport:
    def __init__(self, gateway: AIGateway) -> None:
        self._gateway = gateway

    async def analyze_results(
        self,
        results: list[dict[str, Any]],
        patient_history: dict[str, Any] | None = None,
    ) -> list[ClinicalRecommendation]:
        recommendations: list[ClinicalRecommendation] = []
        for result in results:
            test_name = result.get("test_name", "")
            value = result.get("value")
            flag = result.get("flag", "")
            if flag in ("H", "L", "critical"):
                rec = ClinicalRecommendation(
                    type="abnormal_result",
                    severity="critical" if flag == "critical" else "warning",
                    title=f"Abnormal {test_name}",
                    description=f"{test_name} value {value} flagged as {flag}",
                    confidence=0.85,
                    action="review_by_physician",
                )
                recommendations.append(rec)
        return recommendations

    async def generate_differential(
        self,
        symptoms: list[str],
        results: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        prompt = (
            f"Symptoms: {', '.join(symptoms)}\n"
            f"Lab Results: {json.dumps(results)}\n"
            "Provide a differential diagnosis with confidence scores. Return JSON."
        )
        request = InferenceRequest(
            prompt=prompt,
            model="gpt-4o-mini",
            temperature=0.2,
            system_prompt="You are a clinical decision support system. Provide differential diagnoses with confidence levels.",
        )
        response = self._gateway.chat(request)
        try:
            return json.loads(response.text) if response.text else []
        except (json.JSONDecodeError, TypeError):
            return [{"diagnosis": "Unable to generate", "confidence": 0.0}]

    async def check_clinical_guidelines(
        self,
        diagnosis: str,
        patient_data: dict[str, Any],
    ) -> list[dict[str, Any]]:
        return [
            {
                "guideline": f"Clinical guideline for {diagnosis}",
                "applicable": True,
                "recommendations": ["Follow standard protocol"],
                "evidence_level": "B",
            },
        ]


class DrugInteractionDetector:
    def __init__(self, gateway: AIGateway) -> None:
        self._gateway = gateway
        self._known_interactions: dict[tuple[str, str], DrugInteraction] = {}

    def register_interaction(self, interaction: DrugInteraction) -> None:
        key = tuple(sorted([interaction.drug_a.lower(), interaction.drug_b.lower()]))
        self._known_interactions[key] = interaction

    def check_interaction(self, drug_a: str, drug_b: str) -> DrugInteraction | None:
        key = tuple(sorted([drug_a.lower(), drug_b.lower()]))
        return self._known_interactions.get(key)

    def check_prescription(
        self,
        medications: list[dict[str, Any]],
    ) -> list[DrugInteraction]:
        interactions: list[DrugInteraction] = []
        for i in range(len(medications)):
            for j in range(i + 1, len(medications)):
                drug_a = medications[i].get("name", "")
                drug_b = medications[j].get("name", "")
                known = self.check_interaction(drug_a, drug_b)
                if known:
                    interactions.append(known)
        return interactions

    def check_allergy(
        self,
        drug_name: str,
        allergies: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        alerts: list[dict[str, Any]] = []
        drug_lower = drug_name.lower()
        for allergy in allergies:
            allergen = allergy.get("allergen", "").lower()
            if drug_lower == allergen or drug_lower.startswith(allergen):
                alerts.append({
                    "drug": drug_name,
                    "allergen": allergy.get("allergen", ""),
                    "severity": allergy.get("severity", "unknown"),
                    "reaction": allergy.get("reaction", ""),
                    "alert": f"Patient is allergic to {allergy.get('allergen', '')}",
                })
        return alerts


class ClinicalSummarizer:
    def __init__(self, gateway: AIGateway) -> None:
        self._gateway = gateway

    async def summarize_results(
        self,
        patient_id: str,
        results: list[dict[str, Any]],
        model: str = "gpt-4o-mini",
    ) -> ClinicalSummary:
        result_text = "\n".join(
            f"{r.get('test_name', '')}: {r.get('value', '')} {r.get('unit', '')} "
            f"(flag: {r.get('flag', 'normal')})"
            for r in results
        )
        prompt = (
            f"Patient {patient_id} lab results:\n{result_text}\n"
            "Provide a concise clinical summary including:\n"
            "1) Key findings\n2) Clinical recommendations\n3) Follow-up suggestions"
        )
        request = InferenceRequest(
            prompt=prompt,
            model=model,
            temperature=0.2,
            system_prompt="You are a clinical summarizer. Provide concise, accurate summaries.",
        )
        response = self._gateway.chat(request)
        return ClinicalSummary(
            patient_id=patient_id,
            summary=response.text,
            key_findings=[],
            recommendations=[],
            generated_at=time.time(),
            model=response.model,
        )

    async def generate_history_summary(
        self,
        patient_id: str,
        past_results: list[list[dict[str, Any]]],
    ) -> ClinicalSummary:
        summary = ClinicalSummary(patient_id=patient_id)
        for i, batch in enumerate(past_results):
            flags = [r.get("flag", "") for r in batch if r.get("flag")]
            summary.key_findings.extend([f"Batch {i+1} flags: {flags}"])
        summary.generated_at = time.time()
        return summary

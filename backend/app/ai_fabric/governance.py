from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from app._compat import StrEnum
from app.ai.approval import approval_store
from app.ai.guardrails import ai_suggest

logger = logging.getLogger("gula.ai_fabric.governance")


class PromptStatus(StrEnum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


class ModelApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CONDITIONAL = "conditional"


class EvaluationDimension(StrEnum):
    ACCURACY = "accuracy"
    BIAS = "bias"
    SAFETY = "safety"
    HALLUCINATION = "hallucination"
    TOXICITY = "toxicity"
    FAIRNESS = "fairness"
    ROBUSTNESS = "robustness"


@dataclass
class PromptVersion:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    version: str = "1.0.0"
    content: str = ""
    system_prompt: str = ""
    model: str = ""
    author: str = ""
    status: PromptStatus = PromptStatus.DRAFT
    changelog: str = ""
    created_at: float = field(default_factory=time.time)
    approved_by: str = ""
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class PromptRegistry:
    def __init__(self) -> None:
        self._prompts: dict[str, list[PromptVersion]] = {}

    def register(self, prompt: PromptVersion) -> PromptVersion:
        self._prompts.setdefault(prompt.name, []).append(prompt)
        logger.info("Prompt registered: %s v%s", prompt.name, prompt.version)
        return prompt

    def get(self, name: str, version: str | None = None) -> PromptVersion | None:
        versions = self._prompts.get(name, [])
        if not versions:
            return None
        if version:
            for v in versions:
                if v.version == version:
                    return v
            return None
        active = [v for v in versions if v.status == PromptStatus.ACTIVE]
        return active[-1] if active else versions[-1]

    def get_active(self, name: str) -> PromptVersion | None:
        return self.get(name)

    def list_versions(self, name: str) -> list[PromptVersion]:
        return self._prompts.get(name, [])

    def list_prompts(self) -> list[dict[str, Any]]:
        summary: dict[str, dict] = {}
        for name, versions in self._prompts.items():
            latest = versions[-1]
            active = next((v for v in versions if v.status == PromptStatus.ACTIVE), None)
            summary[name] = {
                "name": name,
                "versions": len(versions),
                "latest_version": latest.version,
                "active_version": active.version if active else None,
                "status": active.status if active else latest.status,
            }
        return list(summary.values())

    def promote(
        self, name: str, version: str, target: PromptStatus, by: str = "",
    ) -> PromptVersion | None:
        prompt = self.get(name, version)
        if not prompt:
            return None
        prompt.status = target
        if target == PromptStatus.APPROVED:
            prompt.approved_by = by
        logger.info("Prompt %s v%s promoted to %s by %s", name, version, target.value, by)
        return prompt

    def deprecate(self, name: str, version: str) -> PromptVersion | None:
        return self.promote(name, version, PromptStatus.DEPRECATED)

    def delete(self, name: str, version: str) -> bool:
        versions = self._prompts.get(name, [])
        for i, v in enumerate(versions):
            if v.version == version:
                versions.pop(i)
                return True
        return False

    def search(self, query: str) -> list[PromptVersion]:
        results: list[PromptVersion] = []
        for versions in self._prompts.values():
            for v in versions:
                if query.lower() in v.name.lower() or query.lower() in v.content.lower():
                    results.append(v)
        return results


class ModelApproval:
    def __init__(self) -> None:
        self._approvals: dict[str, dict[str, Any]] = {}

    def submit(
        self,
        model_name: str,
        version: str,
        submitted_by: str,
        evidence: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        record = {
            "id": str(uuid.uuid4()),
            "model_name": model_name,
            "version": version,
            "submitted_by": submitted_by,
            "status": ModelApprovalStatus.PENDING.value,
            "evidence": evidence or {},
            "submitted_at": time.time(),
            "reviewed_by": "",
            "reviewed_at": 0.0,
            "comments": "",
        }
        key = f"{model_name}:{version}"
        self._approvals[key] = record
        logger.info("Model approval submitted: %s v%s by %s", model_name, version, submitted_by)
        return record

    def approve(
        self, model_name: str, version: str, reviewer: str, comments: str = "",
    ) -> dict[str, Any] | None:
        record = self._approvals.get(f"{model_name}:{version}")
        if not record:
            return None
        record["status"] = ModelApprovalStatus.APPROVED.value
        record["reviewed_by"] = reviewer
        record["reviewed_at"] = time.time()
        record["comments"] = comments
        return record

    def reject(
        self, model_name: str, version: str, reviewer: str, reason: str = "",
    ) -> dict[str, Any] | None:
        record = self._approvals.get(f"{model_name}:{version}")
        if not record:
            return None
        record["status"] = ModelApprovalStatus.REJECTED.value
        record["reviewed_by"] = reviewer
        record["reviewed_at"] = time.time()
        record["comments"] = reason
        return record

    def get_status(self, model_name: str, version: str) -> str | None:
        record = self._approvals.get(f"{model_name}:{version}")
        return record["status"] if record else None

    def is_approved(self, model_name: str, version: str) -> bool:
        return self.get_status(model_name, version) == ModelApprovalStatus.APPROVED.value

    def list_pending(self) -> list[dict[str, Any]]:
        return [
            r for r in self._approvals.values() if r["status"] == ModelApprovalStatus.PENDING.value
        ]

    def list_all(self) -> list[dict[str, Any]]:
        return list(self._approvals.values())


@dataclass
class EvaluationResult:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    model: str = ""
    version: str = ""
    dimension: EvaluationDimension = EvaluationDimension.ACCURACY
    score: float = 0.0
    passed: bool = False
    threshold: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)
    evaluated_at: float = field(default_factory=time.time)


class EvaluationFramework:
    def __init__(self) -> None:
        self._results: list[EvaluationResult] = []
        self._thresholds: dict[EvaluationDimension, float] = {
            EvaluationDimension.ACCURACY: 0.8,
            EvaluationDimension.BIAS: 0.1,
            EvaluationDimension.SAFETY: 0.9,
            EvaluationDimension.HALLUCINATION: 0.1,
            EvaluationDimension.TOXICITY: 0.05,
            EvaluationDimension.FAIRNESS: 0.8,
            EvaluationDimension.ROBUSTNESS: 0.7,
        }

    def set_threshold(self, dimension: EvaluationDimension, threshold: float) -> None:
        self._thresholds[dimension] = threshold

    def evaluate(
        self,
        model: str,
        version: str,
        dimension: EvaluationDimension,
        score: float,
        details: dict[str, Any] | None = None,
    ) -> EvaluationResult:
        threshold = self._thresholds.get(dimension, 0.5)
        passed = (
            score >= threshold
            if dimension
            in (
                EvaluationDimension.ACCURACY,
                EvaluationDimension.SAFETY,
                EvaluationDimension.FAIRNESS,
                EvaluationDimension.ROBUSTNESS,
            )
            else score <= threshold
        )
        result = EvaluationResult(
            model=model,
            version=version,
            dimension=dimension,
            score=score,
            passed=passed,
            threshold=threshold,
            details=details or {},
        )
        self._results.append(result)
        return result

    def evaluate_accuracy(
        self, model: str, version: str, correct: int, total: int,
    ) -> EvaluationResult:
        score = correct / total if total else 0.0
        return self.evaluate(
            model,
            version,
            EvaluationDimension.ACCURACY,
            score,
            {"correct": correct, "total": total},
        )

    def evaluate_bias(self, model: str, version: str, bias_score: float) -> EvaluationResult:
        return self.evaluate(model, version, EvaluationDimension.BIAS, bias_score)

    def evaluate_safety(
        self, model: str, version: str, safe_responses: int, total: int,
    ) -> EvaluationResult:
        score = safe_responses / total if total else 1.0
        return self.evaluate(
            model,
            version,
            EvaluationDimension.SAFETY,
            score,
            {"safe": safe_responses, "total": total},
        )

    def get_results(self, model: str, version: str) -> list[EvaluationResult]:
        return [r for r in self._results if r.model == model and r.version == version]

    def model_passes_all(self, model: str, version: str) -> bool:
        results = self.get_results(model, version)
        if not results:
            return False
        return all(r.passed for r in results)

    def summary(self, model: str, version: str) -> dict[str, Any]:
        results = self.get_results(model, version)
        return {
            "model": model,
            "version": version,
            "dimensions_evaluated": len(results),
            "all_passed": all(r.passed for r in results),
            "results": {
                r.dimension.value: {"score": r.score, "passed": r.passed, "threshold": r.threshold}
                for r in results
            },
        }


class AIConstitution:
    def __init__(self) -> None:
        self._articles: dict[str, dict[str, Any]] = {}
        self._load_defaults()

    def _load_defaults(self) -> None:
        defaults = [
            {
                "id": "ART-001",
                "title": "Patient Safety First",
                "principle": "AI must never compromise patient safety. All AI outputs are suggestions requiring human approval before affecting clinical state.",
                "severity": "critical",
                "enforceable": True,
            },
            {
                "id": "ART-002",
                "title": "Data Privacy",
                "principle": "AI must never expose patient data. All outputs must be PII-free. No patient data leaves the platform boundary.",
                "severity": "critical",
                "enforceable": True,
            },
            {
                "id": "ART-003",
                "title": "Human Oversight",
                "principle": "AI = Suggest, Human = Approve, System = Enforce. Every clinical AI action must have a human-in-the-loop.",
                "severity": "high",
                "enforceable": True,
            },
            {
                "id": "ART-004",
                "title": "Transparency",
                "principle": "All AI decisions must be explainable and auditable. Confidence scores must accompany every suggestion.",
                "severity": "high",
                "enforceable": True,
            },
            {
                "id": "ART-005",
                "title": "Fairness",
                "principle": "AI must not discriminate based on age, gender, ethnicity, or socioeconomic status. Bias monitoring is mandatory.",
                "severity": "high",
                "enforceable": True,
            },
            {
                "id": "ART-006",
                "title": "Accountability",
                "principle": "Every AI action must be traceable to a specific model version, prompt, and operator.",
                "severity": "medium",
                "enforceable": True,
            },
            {
                "id": "ART-007",
                "title": "Conservatism in Clinical AI",
                "principle": "False negatives are preferred over false positives in clinical alerts. When uncertain, defer to human judgment.",
                "severity": "medium",
                "enforceable": False,
            },
        ]
        for article in defaults:
            self.add_article(**article)

    def add_article(
        self,
        id: str,
        title: str,
        principle: str,
        severity: str = "medium",
        enforceable: bool = True,
    ) -> dict[str, Any]:
        article = {
            "id": id,
            "title": title,
            "principle": principle,
            "severity": severity,
            "enforceable": enforceable,
            "created_at": time.time(),
        }
        self._articles[id] = article
        return article

    def get_article(self, id: str) -> dict[str, Any] | None:
        return self._articles.get(id)

    def list_articles(self, severity: str | None = None) -> list[dict[str, Any]]:
        articles = list(self._articles.values())
        if severity:
            articles = [a for a in articles if a["severity"] == severity]
        return sorted(
            articles,
            key=lambda a: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(a["severity"], 99),
        )

    def check_compliance(self, action: dict[str, Any]) -> list[dict[str, Any]]:
        violations: list[dict[str, Any]] = []
        if action.get("bypasses_human"):
            violations.append(
                {
                    "article": "ART-003",
                    "message": "Action bypasses human oversight",
                    "severity": "high",
                },
            )
        if action.get("contains_pii"):
            violations.append(
                {
                    "article": "ART-002",
                    "message": "Action may expose patient data",
                    "severity": "critical",
                },
            )
        return violations

    def get_compliance_report(self) -> dict[str, Any]:
        return {
            "total_articles": len(self._articles),
            "critical_count": len(
                [a for a in self._articles.values() if a["severity"] == "critical"],
            ),
            "high_count": len([a for a in self._articles.values() if a["severity"] == "high"]),
            "medium_count": len([a for a in self._articles.values() if a["severity"] == "medium"]),
            "enforceable_count": len([a for a in self._articles.values() if a["enforceable"]]),
        }


class AIGovernance:
    def __init__(
        self,
        prompt_registry: PromptRegistry | None = None,
        model_approval: ModelApproval | None = None,
        evaluation_framework: EvaluationFramework | None = None,
        constitution: AIConstitution | None = None,
    ) -> None:
        self.prompt_registry = prompt_registry or PromptRegistry()
        self.model_approval = model_approval or ModelApproval()
        self.evaluation_framework = evaluation_framework or EvaluationFramework()
        self.constitution = constitution or AIConstitution()

    def check_guardrail(self, operation: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            suggestion = ai_suggest(
                operation=operation,
                payload=payload,
                ai_model="governance",
                confidence=1.0,
            )
            approval = approval_store.submit(suggestion)
            return {
                "allowed": True,
                "suggestion_id": suggestion.id,
                "approval_id": approval.id,
                "operation_type": suggestion.operation_type.value,
            }
        except Exception as exc:
            return {
                "allowed": False,
                "error": str(exc),
            }


governance = AIGovernance()

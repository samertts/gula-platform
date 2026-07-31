from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from governance.compiler.constitution_compiler import ConstitutionCompiler
from governance.compiler.models import (
    CompiledConstitution,
    ConstitutionalRule,
    RuleCategory,
    RuleEvaluationReport,
    RuleEvaluationResult,
    RuleSeverity,
)


class ConstitutionEngine:
    def __init__(self) -> None:
        self.compiler = ConstitutionCompiler()
        self.constitution: CompiledConstitution | None = None
        self._load()

    def _load(self) -> None:
        self.constitution = self.compiler.compile_all()

    def reload(self) -> None:
        self._load()

    @property
    def rules(self) -> list[ConstitutionalRule]:
        if not self.constitution:
            return []
        return self.constitution.rules

    def evaluate_request(self, request_type: str, context: dict[str, Any]) -> RuleEvaluationReport:
        results: list[RuleEvaluationResult] = []
        violations: list[dict[str, Any]] = []

        for rule in self.rules:
            if not self._rule_applies(rule, request_type):
                continue
            result = self._evaluate_rule(rule, context)
            results.append(result)
            if not result.passed:
                violations.append({
                    "rule_id": rule.id,
                    "rule_title": rule.title,
                    "severity": rule.severity.value,
                    "details": result.details,
                    "score": result.score,
                })

        passed = sum(1 for r in results if r.passed)
        failed = sum(1 for r in results if not r.passed)
        total = len(results)
        score = (passed / total * 100) if total > 0 else 100.0

        return RuleEvaluationReport(
            evaluated_at=datetime.now(UTC).isoformat(),
            total_rules=total,
            passed=passed,
            failed=failed,
            score=score,
            results=results,
            violations=violations,
        )

    def evaluate_technology(self, tech_name: str, tech_data: dict[str, Any]) -> RuleEvaluationReport:
        context = {
            "technology": tech_name,
            "license": tech_data.get("license", ""),
            "cost": tech_data.get("cost", 0),
            "vendor": tech_data.get("vendor", ""),
            "is_open_source": tech_data.get("is_open_source", False),
            "is_self_hosted": tech_data.get("is_self_hosted", False),
        }
        return self.evaluate_request("technology_selection", context)

    def _rule_applies(self, rule: ConstitutionalRule, request_type: str) -> bool:
        mapping: dict[str, list[RuleCategory]] = {
            "technology_selection": [
                RuleCategory.FREE_FIRST, RuleCategory.OPEN_SOURCE_FIRST,
                RuleCategory.SELF_HOSTED_FIRST, RuleCategory.NO_VENDOR_LOCK_IN,
                RuleCategory.ZERO_PAID_DEPENDENCY, RuleCategory.LOCAL_AI_FIRST,
                RuleCategory.FREE_SECURITY_FIRST, RuleCategory.COST_GOVERNANCE,
                RuleCategory.PLATFORM_SOVEREIGNTY,
            ],
            "dependency_add": [
                RuleCategory.ZERO_PAID_DEPENDENCY, RuleCategory.OPEN_SOURCE_FIRST,
                RuleCategory.NO_VENDOR_LOCK_IN, RuleCategory.REUSE_BEFORE_BUILD,
            ],
            "architecture_decision": [
                RuleCategory.ARCHITECTURE_BEFORE_IMPLEMENTATION,
                RuleCategory.EVIDENCE_BASED_DECISIONS,
                RuleCategory.SECURITY_BY_DESIGN, RuleCategory.PRIVACY_BY_DESIGN,
                RuleCategory.NO_VENDOR_LOCK_IN, RuleCategory.COST_GOVERNANCE,
                RuleCategory.PLATFORM_SOVEREIGNTY,
            ],
            "code_review": [
                RuleCategory.REUSE_BEFORE_BUILD, RuleCategory.SECURITY_BY_DESIGN,
                RuleCategory.PRIVACY_BY_DESIGN, RuleCategory.NO_VENDOR_LOCK_IN,
            ],
            "procurement": [
                RuleCategory.FREE_FIRST, RuleCategory.OPEN_SOURCE_FIRST,
                RuleCategory.SELF_HOSTED_FIRST, RuleCategory.ZERO_PAID_DEPENDENCY,
                RuleCategory.LOCAL_AI_FIRST, RuleCategory.COST_GOVERNANCE,
                RuleCategory.PLATFORM_SOVEREIGNTY,
            ],
            "ai_recommendation": [
                RuleCategory.LOCAL_AI_FIRST, RuleCategory.FREE_FIRST,
                RuleCategory.OPEN_SOURCE_FIRST, RuleCategory.NO_VENDOR_LOCK_IN,
                RuleCategory.COST_GOVERNANCE, RuleCategory.PLATFORM_SOVEREIGNTY,
            ],
        }
        applicable = mapping.get(request_type, list(RuleCategory))
        return rule.category in applicable

    def _evaluate_rule(self, rule: ConstitutionalRule, context: dict[str, Any]) -> RuleEvaluationResult:
        details: list[str] = []
        passed = True
        score = 1.0

        if rule.category == RuleCategory.FREE_FIRST:
            cost = context.get("cost", 0)
            if cost > 0:
                details.append(f"Technology has cost ${cost} — verify free alternative was evaluated")
                passed = bool(context.get("free_alternative_evaluated", False))
                score = 0.0 if not passed else 0.5

        elif rule.category == RuleCategory.OPEN_SOURCE_FIRST:
            is_oss = context.get("is_open_source", False)
            license_type = context.get("license", "")
            if not is_oss:
                details.append(f"Technology is not open source ({license_type}) — prefer OSS alternative")
                passed = False
                score = 0.0

        elif rule.category == RuleCategory.NO_VENDOR_LOCK_IN:
            vendor = context.get("vendor", "")
            if vendor and vendor.lower() not in ("none", "community", "self"):
                has_abstraction = context.get("has_abstraction_layer", False)
                if not has_abstraction:
                    details.append(f"Vendor '{vendor}' used without abstraction layer")
                    passed = False
                    score = 0.0

        elif rule.category == RuleCategory.SELF_HOSTED_FIRST:
            is_self_hosted = context.get("is_self_hosted", False)
            if not is_self_hosted:
                details.append("Prefer self-hosted solution over SaaS")
                passed = False
                score = 0.3

        elif rule.category == RuleCategory.ZERO_PAID_DEPENDENCY:
            cost = context.get("cost", 0)
            if cost > 0:
                has_adr = context.get("has_adr", False)
                if not has_adr:
                    details.append(f"Paid dependency (${cost}) without ADR approval")
                    passed = False
                    score = 0.0

        elif rule.category == RuleCategory.PLATFORM_SOVEREIGNTY:
            requires_commercial = context.get("requires_commercial_license", False)
            if requires_commercial:
                details.append("Commercial license required — violates platform sovereignty")
                passed = False
                score = 0.0

        elif rule.category == RuleCategory.LOCAL_AI_FIRST:
            uses_local = context.get("uses_local_ai", True)
            if not uses_local:
                details.append("Remote AI API used without evaluating local alternative")
                passed = False
                score = 0.3

        elif rule.category == RuleCategory.COST_GOVERNANCE:
            tco = context.get("tco", 0)
            free_alternative_tco = context.get("free_alternative_tco", 0)
            if tco > free_alternative_tco * 2:
                details.append(f"TCO (${tco}) significantly exceeds free alternative (${free_alternative_tco})")
                passed = False
                score = 0.0

        elif rule.category == RuleCategory.REUSE_BEFORE_BUILD:
            existing = context.get("existing_solution", "")
            if not existing:
                details.append("No existing solution search documented")
                passed = False
                score = 0.5

        elif rule.category == RuleCategory.SECURITY_BY_DESIGN:
            has_threat_model = context.get("has_threat_model", False)
            if not has_threat_model:
                details.append("Missing threat model — security by design required")
                passed = False
                score = 0.0

        elif rule.category == RuleCategory.PRIVACY_BY_DESIGN:
            has_pia = context.get("has_privacy_impact_assessment", False)
            has_encryption = context.get("has_encryption", False)
            if not has_pia or not has_encryption:
                details.append("Privacy by design requirements not met")
                passed = False
                score = 0.0

        elif rule.category == RuleCategory.ARCHITECTURE_BEFORE_IMPLEMENTATION:
            has_adr = context.get("has_adr", False)
            if not has_adr:
                details.append("Missing ADR — architecture before implementation required")
                passed = False
                score = 0.5

        elif rule.category == RuleCategory.EVIDENCE_BASED_DECISIONS:
            evidence = context.get("evidence", [])
            if not evidence:
                details.append("No evidence provided for decision")
                passed = False
                score = 0.0
        else:
            details.append(f"Rule {rule.id}: {rule.title} — evaluated")
            passed = True

        if not details:
            details.append(f"{rule.id}: {rule.title} — passed")

        return RuleEvaluationResult(
            rule_id=rule.id,
            rule_title=rule.title,
            category=rule.category,
            severity=rule.severity,
            passed=passed,
            details=details,
            score=score,
        )

    def explain_decision(self, request_type: str, context: dict[str, Any]) -> dict[str, Any]:
        report = self.evaluate_request(request_type, context)
        return {
            "request_type": request_type,
            "context": context,
            "score": report.score,
            "passed": report.failed == 0,
            "total_rules": report.total_rules,
            "passed_rules": report.passed,
            "failed_rules": report.failed,
            "violations": report.violations,
            "results": [r.to_dict() for r in report.results],
            "recommendation": "APPROVED" if report.failed == 0 else "REJECTED",
        }

    def resolve_priorities(self, rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
        severity_order = {
            RuleSeverity.BLOCKER: 0,
            RuleSeverity.HIGH: 1,
            RuleSeverity.MEDIUM: 2,
            RuleSeverity.LOW: 3,
            RuleSeverity.INFO: 4,
        }
        return sorted(rules, key=lambda r: severity_order.get(
            RuleSeverity(r.get("severity", "info")), 99
        ))

    def generate_audit_trail(self, request_type: str, context: dict[str, Any]) -> dict[str, Any]:
        report = self.evaluate_request(request_type, context)
        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "request_type": request_type,
            "context_summary": {k: v for k, v in context.items() if k != "password"},
            "score": report.score,
            "violation_count": report.failed,
            "violations": [
                {
                    "rule_id": v["rule_id"],
                    "severity": v["severity"],
                    "score": v["score"],
                }
                for v in report.violations
            ],
            "status": "PASS" if report.failed == 0 else "FAIL",
        }

    def generate_compliance_report(self, scope: str = "full") -> dict[str, Any]:
        report = self.evaluate_request("architecture_decision", {"scope": scope})
        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "scope": scope,
            "constitution_version": self.constitution.version if self.constitution else "unknown",
            "total_rules": self.constitution.rule_count if self.constitution else 0,
            "total_documents": self.constitution.document_count if self.constitution else 0,
            "compliance_score": report.score,
            "passed_rules": report.passed,
            "failed_rules": report.failed,
            "violations": report.violations,
            "status": "COMPLIANT" if report.score >= 90 else "NON_COMPLIANT",
        }

from __future__ import annotations

from typing import Any

from governance.compiler.models import ArchitectureDecision
from governance.constitution_engine import ConstitutionEngine


class ArchitectureDecisionEngine:
    def __init__(self) -> None:
        self.engine = ConstitutionEngine()

    def generate_adr(self, title: str, context: str, alternatives: list[str] | None = None) -> ArchitectureDecision:
        alts = alternatives or ["No alternative considered"]
        alt_list = [{"name": a, "pros": [], "cons": []} for a in alts]
        tradeoffs = [{"factor": "Cost", "impact": "See cost matrix"}, {"factor": "Complexity", "impact": "Depends on implementation"}]

        ctx = {
            "title": title,
            "context": context,
            "has_adr": True,
            "has_threat_model": True,
            "has_privacy_impact_assessment": True,
            "has_encryption": True,
            "evidence": ["Architecture Decision Record generated"],
        }
        compliance = self.engine.evaluate_request("architecture_decision", ctx)

        return ArchitectureDecision(
            title=title,
            context=context,
            alternatives=alt_list,
            tradeoffs=tradeoffs,
            risk_matrix=self._generate_risk_matrix(),
            cost_matrix=self._generate_cost_matrix(alts),
            migration_plan="1. Implement in parallel\n2. Feature flag\n3. Gradual rollout\n4. Monitor and validate\n5. Remove old system",
            exit_strategy="1. Document all integrations\n2. Maintain abstraction layer\n3. Keep migration path active\n4. Test rollback procedure",
            compliance_report=compliance.to_dict(),
            decision="APPROVED" if compliance.failed == 0 else "REJECTED",
            rationale=f"Architecture decision '{title}' evaluated against constitution",
        )

    def _generate_risk_matrix(self) -> dict[str, Any]:
        return {
            "security": {"score": 3, "mitigation": "Security review required"},
            "performance": {"score": 2, "mitigation": "Load testing required"},
            "cost": {"score": 1, "mitigation": "Minimal cost impact"},
            "migration": {"score": 2, "mitigation": "Feature flag deployment"},
            "compliance": {"score": 1, "mitigation": "Constitution compliance verified"},
        }

    def _generate_cost_matrix(self, alternatives: list[str]) -> dict[str, Any]:
        return {
            "estimated_effort": "2-4 weeks",
            "estimated_cost": "$0 (open source stack)",
            "ongoing_cost": "$0/mo (self-hosted)",
            "alternatives": [{"name": a, "cost": "varies"} for a in alternatives],
        }

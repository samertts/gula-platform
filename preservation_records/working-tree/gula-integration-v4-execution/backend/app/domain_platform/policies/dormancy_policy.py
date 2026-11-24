"""PROGRAM-BETA-COMMIT-0.2 — Dormancy Policy (ADR-026, ADR-027).

The first implemented Architecture Policy. It ports the certification
check-10 semantics (``certification.py::check_dormancy_policy``) into an
independent policy module so the same rule is enforced by Domain
certification, the Architecture Gate, and CI through one shared
implementation:

* no active Domain may own an ``archived``/``retired`` module
  (finding ``DORMANCY-001``, severity ``critical``);
* no active Domain may own a ``dormant`` module (finding ``DORMANCY-002``,
  severity ``major``);
* modules without an explicit lifecycle declaration are implicitly
  ``active_development`` (finding ``DORMANCY-003``, severity ``minor``) —
  the policy *warns* for an undeclared-modules Domain, so a Domain only
  certifies at 100% when every module carries an explicit lifecycle state.

The policy depends only on the ``DormancySource`` interface; the default
source is the committed JSON configuration (replaceable through
``build_dormancy_source``). Evaluation is deterministic: findings are
emitted in domain-then-module order and the summary is stable for a given
context.
"""

from __future__ import annotations

from app.domain_platform.core import DomainManifest
from app.domain_platform.dormancy import (
    CANONICAL_DORMANCY_REGISTRY,
    DormancySource,
    ModuleLifecycleState,
)
from app.domain_platform.policies.core import (
    PolicyContext,
    PolicyFinding,
    PolicyResult,
    PolicySeverity,
    compute_status,
)

_CODE_RETIRED_ARCHIVED = "DORMANCY-001"
_CODE_DORMANT = "DORMANCY-002"
_CODE_UNDECLARED = "DORMANCY-003"


class DormancyPolicy:
    """Enforces the dormancy protection invariant (ADR-026)."""

    name = "dormancy_policy"
    description = (
        "Active Domains must not own archived/retired/dormant strategic assets; "
        "every Domain module must carry an explicit lifecycle state (ADR-026)."
    )
    enabled = True

    def __init__(self, dormancy_source: DormancySource | None = None) -> None:
        self._source = dormancy_source

    def _source_for(self, context: PolicyContext) -> DormancySource:
        return self._source or context.dormancy_source or CANONICAL_DORMANCY_REGISTRY

    def evaluate(self, context: PolicyContext) -> PolicyResult:
        source = self._source_for(context)
        domains = context.domains or []
        findings: list[PolicyFinding] = []
        for manifest in domains:
            findings.extend(self._findings_for(manifest, source))
        return PolicyResult(
            policy=self.name,
            status=compute_status(findings),
            summary=self._summarize(findings, len(domains)),
            findings=findings,
        )

    def _findings_for(
        self, manifest: DomainManifest, source: DormancySource
    ) -> list[PolicyFinding]:
        retired_owned: list[str] = []
        dormant_owned: list[str] = []
        undeclared: list[str] = []
        for module in manifest.modules:
            record = source.find_record(module)
            if record is None:
                undeclared.append(module)
            elif record.state is ModuleLifecycleState.retired or record.state is ModuleLifecycleState.archived:
                retired_owned.append(module)
            elif record.state is ModuleLifecycleState.dormant:
                dormant_owned.append(module)

        findings: list[PolicyFinding] = []
        if retired_owned:
            findings.append(
                PolicyFinding(
                    code=_CODE_RETIRED_ARCHIVED,
                    severity=PolicySeverity.CRITICAL,
                    message=(
                        "active Domain owns archived/retired strategic assets: "
                        + ", ".join(sorted(retired_owned))
                    ),
                    path=retired_owned[0],
                    domain=manifest.code,
                    metadata={"modules": sorted(retired_owned)},
                )
            )
        if dormant_owned:
            findings.append(
                PolicyFinding(
                    code=_CODE_DORMANT,
                    severity=PolicySeverity.MAJOR,
                    message=(
                        "active Domain owns dormant strategic assets: "
                        + ", ".join(sorted(dormant_owned))
                    ),
                    path=dormant_owned[0],
                    domain=manifest.code,
                    metadata={"modules": sorted(dormant_owned)},
                )
            )
        if undeclared:
            findings.append(
                PolicyFinding(
                    code=_CODE_UNDECLARED,
                    severity=PolicySeverity.MINOR,
                    message=(
                        f"{len(undeclared)} module(s) implicitly active_development; "
                        "declare them in the Dormancy Registry (ADR-026) to pin a "
                        "non-active lifecycle state"
                    ),
                    path=undeclared[0],
                    domain=manifest.code,
                    metadata={"modules": sorted(undeclared)},
                )
            )
        return findings

    def _summarize(self, findings: list[PolicyFinding], domain_count: int) -> str:
        if not findings:
            return (
                "no protected strategic asset is coupled to the Domain; "
                "every Domain module has a declared lifecycle state"
            )
        for severity in (PolicySeverity.CRITICAL, PolicySeverity.MAJOR):
            blocked = [f for f in findings if f.severity is severity]
            if blocked:
                return "; ".join(f.message for f in blocked)
        total_undeclared = sum(len(f.metadata.get("modules", [])) for f in findings)
        return (
            f"{total_undeclared} module(s) implicitly active_development; declare "
            "them in the Dormancy Registry (ADR-026) to pin a non-active "
            "lifecycle state"
        )

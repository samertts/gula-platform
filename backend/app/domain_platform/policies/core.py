"""PROGRAM-BETA-COMMIT-0.2 — Architecture Policy Engine (ADR-027).

The single governance entry point used by CI/CD, Architecture Gates, Domain
Certification, and future governance tooling.

Design:

* a *policy* is any object satisfying the :class:`Policy` protocol
  (``name``, ``description``, ``enabled``, ``evaluate(context)``) — adding a
  new governance rule is adding one module, never an engine change;
* the :class:`PolicyEngine` runs every *enabled* policy in registration
  order, applies baseline waivers, and aggregates a deterministic verdict;
* each :class:`PolicyResult` carries machine-readable findings plus a
  human-readable summary; :class:`PolicyReport` renders both a JSON payload
  and a Markdown report;
* findings may be waived through :class:`PolicyBaseline` (acknowledged debt)
  without touching any policy implementation.

The Dormancy Policy (``dormancy_policy.py``) is the first implemented
policy; nine further policies are registered *disabled* in the default
registry so enabling them later is configuration, not redesign (ADR-027).
"""

from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from app.domain_platform.core import DomainManifest
    from app.domain_platform.dormancy import DormancySource

POLICY_ENGINE_VERSION = "1.0.0"


class PolicySeverity(StrEnum):
    """Severity of one finding. Verdict thresholds are derived from it."""

    INFO = "info"
    MINOR = "minor"
    MAJOR = "major"
    CRITICAL = "critical"


class PolicyStatus(StrEnum):
    """Deterministic outcome of one policy evaluation."""

    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    SKIPPED = "skipped"
    ERROR = "error"


_SEVERITY_RANK = {
    PolicySeverity.INFO: 0,
    PolicySeverity.MINOR: 1,
    PolicySeverity.MAJOR: 2,
    PolicySeverity.CRITICAL: 3,
}


def compute_status(findings: list[PolicyFinding]) -> PolicyStatus:
    """Aggregate finding severities into a deterministic policy status.

    * critical or major findings -> ``fail`` (the gate stops);
    * minor findings -> ``warn`` (advisory, non-blocking);
    * info or no findings -> ``pass``.
    """
    if any(f.severity is PolicySeverity.CRITICAL for f in findings):
        return PolicyStatus.FAIL
    if any(f.severity is PolicySeverity.MAJOR for f in findings):
        return PolicyStatus.FAIL
    if any(f.severity is PolicySeverity.MINOR for f in findings):
        return PolicyStatus.WARN
    return PolicyStatus.PASS


@dataclass(frozen=True)
class PolicyFinding:
    """One machine-readable finding emitted by a policy.

    ``code`` is a stable identifier (e.g. ``DORMANCY-001``) that waivers and
    baselines reference; ``path``/``domain`` locate the subject of the finding.
    """

    code: str
    severity: PolicySeverity
    message: str
    path: str | None = None
    domain: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict, compare=False)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "code": self.code,
            "severity": str(self.severity.value),
            "message": self.message,
        }
        if self.path:
            payload["path"] = self.path
        if self.domain:
            payload["domain"] = self.domain
        if self.metadata:
            payload["metadata"] = self.metadata
        return payload


@dataclass
class PolicyResult:
    """Outcome of evaluating one policy against one context.

    The result carries no timestamps or durations: governance output must be
    byte-for-byte reproducible for a given context (ADR-027).
    """

    policy: str
    status: PolicyStatus
    summary: str
    findings: list[PolicyFinding] = field(default_factory=list)
    waived: int = 0

    @property
    def severity(self) -> PolicySeverity:
        """Worst finding severity (``info`` when there are no findings)."""
        if not self.findings:
            return PolicySeverity.INFO
        return max(self.findings, key=lambda f: _SEVERITY_RANK[f.severity]).severity

    @property
    def passed(self) -> bool:
        return self.status is PolicyStatus.PASS

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy": self.policy,
            "status": str(self.status.value),
            "severity": str(self.severity.value),
            "summary": self.summary,
            "waived": self.waived,
            "findings": [f.to_dict() for f in self.findings],
        }


@dataclass
class PolicyContext:
    """The inputs a policy evaluates against.

    Policies read only what they need from the context; unknown inputs are
    ignored, so the context can grow without breaking existing policies.
    ``domains``/``dormancy_source`` are typed via TYPE_CHECKING to avoid
    circular imports while keeping the engine domain-platform independent.
    """

    domains: list[DomainManifest] | None = None
    dormancy_source: DormancySource | None = None
    repo_root: pathlib.Path | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class Policy(Protocol):
    """The common interface every policy must implement (ADR-027).

    Policies are deterministic: the same context always produces the same
    findings. A disabled policy is never executed by the engine but is still
    listed in the report manifest so the catalog is always visible.
    """

    name: str
    description: str
    enabled: bool

    def evaluate(self, context: PolicyContext) -> PolicyResult: ...


class PolicyRegistry:
    """Ordered registry of policies. Registration order is the run order."""

    def __init__(self) -> None:
        self._policies: dict[str, Policy] = {}

    def register(self, policy: Policy) -> PolicyRegistry:
        if policy.name in self._policies:
            raise ValueError(f"policy already registered: {policy.name}")
        self._policies[policy.name] = policy
        return self

    def get(self, name: str) -> Policy:
        try:
            return self._policies[name]
        except KeyError as exc:
            raise KeyError(f"unknown policy: {name}") from exc

    def names(self) -> list[str]:
        return list(self._policies)

    def enabled(self) -> list[Policy]:
        return [p for p in self._policies.values() if p.enabled]

    def to_manifest(self) -> list[dict[str, Any]]:
        return [
            {"name": p.name, "description": p.description, "enabled": bool(p.enabled)}
            for p in self._policies.values()
        ]

    def __contains__(self, name: str) -> bool:
        return name in self._policies

    def __len__(self) -> int:
        return len(self._policies)


@dataclass(frozen=True)
class PolicyWaiver:
    """Acknowledges one finding as known debt (policy + code [+ path])."""

    policy: str
    code: str
    path: str | None = None
    rationale: str = ""

    def matches(self, finding: PolicyFinding) -> bool:
        return (
            finding.code == self.code
            and (self.path is None or self.path == finding.path)
        )

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "policy": self.policy,
            "code": self.code,
            "rationale": self.rationale,
        }
        if self.path:
            payload["path"] = self.path
        return payload


class PolicyBaseline:
    """Waiver set loaded from a committed JSON baseline file.

    Unlike the dormancy source (which fails fast when missing), an absent
    baseline file is a valid empty baseline — no debt has been acknowledged.
    An existing but malformed baseline raises instead of being ignored.
    """

    def __init__(self, waivers: list[PolicyWaiver] | None = None) -> None:
        self.waivers = list(waivers or ())

    @classmethod
    def load(cls, path: str | pathlib.Path) -> PolicyBaseline:
        path = pathlib.Path(path)
        if not path.exists():
            return cls()
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise ValueError(f"cannot read policy baseline: {path}") from exc
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON in policy baseline {path}: {exc}") from exc
        if not isinstance(raw, dict):
            raise ValueError(f"policy baseline {path} must be a JSON object")
        entries = raw.get("waivers", [])
        if not isinstance(entries, list):
            raise ValueError(f"policy baseline {path}: 'waivers' must be a list")
        waivers: list[PolicyWaiver] = []
        for entry in entries:
            if not isinstance(entry, dict):
                raise ValueError(f"policy baseline {path}: each waiver must be an object")
            missing = [k for k in ("policy", "code") if k not in entry]
            if missing:
                raise ValueError(
                    f"policy baseline {path}: waiver missing field(s): {', '.join(missing)}"
                )
            waivers.append(
                PolicyWaiver(
                    policy=entry["policy"],
                    code=entry["code"],
                    path=entry.get("path"),
                    rationale=entry.get("rationale", ""),
                )
            )
        return cls(waivers)

    def _for_policy(self, policy: str) -> list[PolicyWaiver]:
        return [w for w in self.waivers if w.policy == policy]

    def waive(self, result: PolicyResult) -> PolicyResult:
        """Return a copy of ``result`` with waived findings removed.

        The status is recomputed from the remaining findings so acknowledged
        debt never blocks the gate; anything not acknowledged still fails.
        """
        if result.status is PolicyStatus.SKIPPED:
            return result
        waivers = self._for_policy(result.policy)
        kept: list[PolicyFinding] = []
        waived = 0
        for finding in result.findings:
            if any(w.matches(finding) for w in waivers):
                waived += 1
            else:
                kept.append(finding)
        return PolicyResult(
            policy=result.policy,
            status=compute_status(kept),
            summary=result.summary,
            findings=kept,
            waived=waived,
        )

    def to_dict(self) -> dict[str, Any]:
        return {"waivers": [w.to_dict() for w in self.waivers]}


@dataclass
class PolicyReport:
    """The full governance report: manifest + per-policy results.

    Deterministic by construction: no timestamps or durations, fixed
    registration order, stable finding order. Two runs over the same context
    produce byte-identical JSON and Markdown (ADR-027).
    """

    version: str
    registered: list[dict[str, Any]]
    results: list[PolicyResult]

    @property
    def verdict(self) -> str:
        statuses = [r.status for r in self.results if r.status is not PolicyStatus.SKIPPED]
        if any(s in (PolicyStatus.FAIL, PolicyStatus.ERROR) for s in statuses):
            return "FAIL"
        if any(s is PolicyStatus.WARN for s in statuses):
            return "WARN"
        return "PASS"

    def to_dict(self) -> dict[str, Any]:
        return {
            "engine": "architecture_policy_engine",
            "version": self.version,
            "verdict": self.verdict,
            "registered_policies": self.registered,
            "results": [r.to_dict() for r in self.results],
        }

    def render_markdown(self) -> str:
        enabled = sum(1 for r in self.registered if r["enabled"])
        lines = [
            "# Architecture Policy Engine",
            "",
            f"- engine version: `{self.version}`",
            f"- registered policies: {len(self.registered)} "
            f"({enabled} enabled, {len(self.results)} executed)",
            f"- **verdict: {self.verdict}**",
            "",
            "## Policy results",
            "",
        ]
        for result in self.results:
            header = f"### `{result.policy}` — `{result.status.value}`"
            if result.waived:
                header += f" (waived: {result.waived})"
            lines.append(header)
            lines.append("")
            lines.append(result.summary)
            if result.findings:
                lines.append("")
                lines.append("| code | severity | domain | path | message |")
                lines.append("|---|---|---|---|---|")
                for finding in result.findings:
                    lines.append(
                        f"| {finding.code} | {finding.severity.value} | "
                        f"{finding.domain or ''} | {finding.path or ''} | {finding.message} |"
                    )
            lines.append("")
        return "\n".join(lines)


class PolicyEngine:
    """Runs every enabled policy in registration order and aggregates a
    deterministic verdict. The single governance entry point (ADR-027)."""

    def __init__(
        self,
        registry: PolicyRegistry | None = None,
        baseline: PolicyBaseline | None = None,
    ) -> None:
        self.registry = registry or PolicyRegistry()
        self.baseline = baseline or PolicyBaseline()

    def run(self, context: PolicyContext) -> PolicyReport:
        results: list[PolicyResult] = [
            self.baseline.waive(policy.evaluate(context))
            for policy in self.registry.enabled()
        ]
        return PolicyReport(
            version=POLICY_ENGINE_VERSION,
            registered=self.registry.to_manifest(),
            results=results,
        )

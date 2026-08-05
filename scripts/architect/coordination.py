"""Phase 8 — AI Coordination.

Define the Architect's coordination contracts with the AI engine
constellation: Builder, Reviewer, Orchestrator, Learner, Optimizer, and
Deployer. Each contract states the engine's role in realizing the platform
architecture, its mandate, and its dependencies. Engine presence is detected
from the repository. Persisted under state/coordination/.
"""

from __future__ import annotations

from pathlib import Path

from scripts.architect.core import (
    AI_ENGINES,
    COORDINATION_DIR,
    CoordinationContract,
    write_json,
)
from scripts.kernel.core import REPO_ROOT, utcnow

# Engine -> (role, mandate, dependencies, presence probe).
ENGINE_CONTRACTS: dict[str, tuple[str, str, tuple[str, ...], str]] = {
    "builder": (
        "Executor",
        "Implements every accepted architectural decision as working code "
        "with atomic, conventional, tested commits.",
        ("reviewer", "kernel"),
        "scripts/builder/",
    ),
    "reviewer": (
        "Verifier",
        "Independently verifies every change-set against the architecture "
        "before acceptance; gates merge readiness.",
        ("kernel",),
        "scripts/reviewer/",
    ),
    "orchestrator": (
        "Coordinator",
        "Turns strategic objectives into managed missions routed to the "
        "engine that owns each surface.",
        ("builder", "reviewer", "deployer", "learner"),
        "scripts/orchestrator/",
    ),
    "learner": (
        "Memory",
        "Records permanent, versioned, searchable knowledge so decisions "
        "and patterns survive across missions.",
        ("kernel",),
        "scripts/learner/",
    ),
    "optimizer": (
        "Perfector",
        "Continuously improves performance, scalability, and maintainability "
        "without changing business behavior.",
        ("reviewer",),
        "scripts/optimizer/",
    ),
    "deployer": (
        "Operator",
        "Deploys, operates, scales, and rolls back the platform across "
        "governorate infrastructure.",
        ("builder",),
        "scripts/deployer/",
    ),
}


def _engine_present(root: Path, probe: str) -> bool:
    return (root / probe).exists()


def build_coordination(root: Path | None = None) -> list[CoordinationContract]:
    """Build coordination contracts deterministically with presence detected."""
    root = root or REPO_ROOT
    contracts: list[CoordinationContract] = []
    for engine in AI_ENGINES:
        role, mandate, dependencies, probe = ENGINE_CONTRACTS[engine]
        contracts.append(CoordinationContract(
            engine=engine,
            role=role,
            mandate=mandate,
            dependencies=list(dependencies),
            status="integrated" if _engine_present(root, probe) else "missing",
        ))
    return contracts


def persist_coordination(root: Path | None = None) -> Path:
    """Persist coordination contracts under state/coordination/."""
    root = root or REPO_ROOT
    contracts = build_coordination(root)
    path = COORDINATION_DIR / "contracts.json"
    write_json(path, {
        "discovered_at": utcnow(),
        "contracts": [c.to_dict() for c in contracts],
    })
    return path


def render_markdown(contracts: list[CoordinationContract]) -> str:
    lines = [
        "# GULA-ARCHITECT-001 — AI Coordination",
        "",
        f"Generated: **{utcnow()}**",
        "",
        "The Architect defines and documents the coordination contracts for "
        "the AI engine constellation.",
        "",
        "| Engine | Role | Status | Mandate |",
        "|---|---|---|---|",
    ]
    for contract in contracts:
        lines.append(
            f"| {contract.engine} | {contract.role} | {contract.status} | "
            f"{contract.mandate[:70]}{'...' if len(contract.mandate) > 70 else ''} |"
        )
    lines.extend(["", "## Dependencies", ""])
    for contract in contracts:
        deps = ", ".join(contract.dependencies) or "none"
        lines.append(f"- `{contract.engine}` depends on: {deps}")
    lines.append("")
    return "\n".join(lines)

"""Phase 11 — Simulation Engine.

Every mission executes first in simulation. Provides a virtual repository,
virtual database, virtual deployment, virtual infrastructure, virtual
knowledge, and virtual rollback. If simulation fails, the mission stops.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any

from .core import utcnow


@dataclass
class VirtualFile:
    """A file in the virtual repository."""

    path: str
    content: str = ""
    kind: str = "text"
    original: str = ""


@dataclass
class VirtualRepository:
    """An overlay repository: reads resolve against virtual then real content."""

    files: dict[str, VirtualFile] = field(default_factory=dict)
    writes: list[str] = field(default_factory=list)

    def add(self, path: str, content: str = "", kind: str = "text") -> None:
        if path not in self.files:
            self.files[path] = VirtualFile(path, content, kind, content)
            return
        virtual = self.files[path]
        virtual.content = content
        virtual.kind = kind

    def write(self, path: str, content: str) -> None:
        self.add(path, content)
        self.writes.append(path)

    def read(self, path: str) -> str:
        virtual = self.files.get(path)
        return virtual.content if virtual else ""

    def changed_files(self) -> list[str]:
        return list(self.writes)

    def snapshot(self) -> dict[str, VirtualFile]:
        return copy.deepcopy(self.files)


@dataclass
class VirtualDatabase:
    """An in-memory database with a transaction log and rollback support."""

    tables: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    transaction_log: list[str] = field(default_factory=list)

    def insert(self, table: str, row: dict[str, Any]) -> None:
        self.tables.setdefault(table, []).append(copy.deepcopy(row))
        self.transaction_log.append(f"{utcnow()} INSERT {table}")

    def query(self, table: str) -> list[dict[str, Any]]:
        return copy.deepcopy(self.tables.get(table, []))

    def snapshot(self) -> dict[str, Any]:
        return {
            "tables": copy.deepcopy(self.tables),
            "log": list(self.transaction_log),
        }

    def rollback(self, snapshot: dict[str, Any]) -> None:
        self.tables = copy.deepcopy(snapshot["tables"])
        self.transaction_log = list(snapshot["log"])


@dataclass
class VirtualDeployment:
    """A simulated deployment environment with staging health checks."""

    environment: str
    healthy_checks: list[str] = field(default_factory=list)

    def deploy(self, build_id: str, checks: list[str]) -> tuple[bool, list[str]]:
        """Simulate a deployment; succeeds only when all checks pass."""
        self.healthy_checks = checks
        passed = all(checks)
        return passed, [f"{build_id} -> {self.environment} check: {check}" for check in checks]


@dataclass
class VirtualInfrastructure:
    """A simulated infrastructure budget (CPU, memory, disk, time)."""

    cpu_available: float = 100.0
    memory_available: float = 100.0
    disk_available: float = 100.0

    def can_run(self, cpu: float, memory: float, disk: float) -> bool:
        return self.cpu_available >= cpu and self.memory_available >= memory and self.disk_available >= disk

    def consume(self, cpu: float, memory: float, disk: float) -> bool:
        if not self.can_run(cpu, memory, disk):
            return False
        self.cpu_available -= cpu
        self.memory_available -= memory
        self.disk_available -= disk
        return True


@dataclass
class VirtualKnowledge:
    """A simulated knowledge graph that replays artifact transitions."""

    artifacts: dict[str, str] = field(default_factory=dict)  # id -> lifecycle
    replay: list[str] = field(default_factory=list)

    def transition(self, artifact_id: str, target_lifecycle: str) -> bool:
        if artifact_id not in self.artifacts:
            self.artifacts[artifact_id] = "draft"
        self.artifacts[artifact_id] = target_lifecycle
        self.replay.append(f"{artifact_id} -> {target_lifecycle}")
        return True


@dataclass
class VirtualRollback:
    """Simulated rollback using snapshots."""

    snapshots: list[Any] = field(default_factory=list)

    def snapshot(self, payload: Any) -> None:
        self.snapshots.append(copy.deepcopy(payload))

    def rollback(self) -> Any:
        if not self.snapshots:
            return None
        return self.snapshots.pop()


@dataclass
class SimulationResult:
    """The outcome of a simulated mission."""

    mission_id: str
    passed: bool
    steps: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)

    @property
    def summary(self) -> str:
        status = "PASSED" if self.passed else "FAILED"
        return f"simulation {self.mission_id}: {status} ({len(self.steps)} steps, {len(self.failures)} failures)"


def simulate_mission(mission_id: str, steps: list[dict[str, Any]]) -> SimulationResult:
    """Execute a mission entirely in simulation.

    Each ``step`` declares the virtual resource it touches. When any step
    fails, the mission stops immediately (Phase 11 mandatory rule).
    """
    repo = VirtualRepository()
    database = VirtualDatabase()
    deployment = VirtualDeployment(mission_id)
    infrastructure = VirtualInfrastructure()
    knowledge = VirtualKnowledge()
    result = SimulationResult(mission_id=mission_id, passed=True)

    for index, step in enumerate(steps, start=1):
        kind = step.get("kind", "file")
        name = step.get("name", f"step-{index}")
        ok, message = _run_step(kind, step, repo, database, deployment, infrastructure, knowledge)
        result.steps.append(f"[{index:02d}] {kind}:{name} -> {'OK' if ok else 'FAILED'} {message}")
        if not ok:
            result.failures.append(f"step {index} ({kind}:{name}): {message}")
            result.passed = False
            break
    return result


def _run_step(
    kind: str,
    step: dict[str, Any],
    repo: VirtualRepository,
    database: VirtualDatabase,
    deployment: VirtualDeployment,
    infrastructure: VirtualInfrastructure,
    knowledge: VirtualKnowledge,
) -> tuple[bool, str]:
    if kind == "file":
        repo.write(step["path"], step.get("content", ""))
        return True, f"virtual write {step['path']}"
    if kind == "db":
        database.insert(step["table"], step.get("row", {}))
        return True, f"virtual insert {step['table']}"
    if kind == "deploy":
        return deployment.deploy(step.get("build", "sim-build"), step.get("checks", [True]))
    if kind == "infra":
        ok = infrastructure.consume(
            step.get("cpu", 1.0),
            step.get("memory", 1.0),
            step.get("disk", 1.0),
        )
        return ok, "virtual infrastructure budget satisfied" if ok else "insufficient virtual resources"
    if kind == "knowledge":
        knowledge.transition(step["artifact"], step.get("lifecycle", "verified"))
        return True, f"virtual knowledge transition {step['artifact']}"
    if kind == "assert":
        ok = step.get("pass", True)
        return ok, step.get("message", "virtual assertion")
    return False, f"unknown simulation step kind '{kind}'"


def require_simulation_pass(result: SimulationResult) -> None:
    """Stop the mission when simulation fails (Phase 11 mandatory rule)."""
    if not result.passed:
        raise RuntimeError(result.summary)

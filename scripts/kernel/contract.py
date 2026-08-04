"""Phase 3 — Engine Contract.

Define one interface used by every engine. The Kernel contract extends the
Governor's Phase 10 communication contract (inputs, outputs, events, errors,
artifacts, dependencies, health, progress, status) with execution metadata:
ownership, checkpoint, capabilities, resources, timeout, retry, and version.

Every engine must conform. No engine may communicate outside the contract.
"""

from __future__ import annotations

from dataclasses import dataclass

from .core import KERNEL_CONTRACT_FIELDS

# The Governor Phase 10 base fields plus the Kernel execution metadata fields.
GOVERNOR_FIELDS = ("inputs", "outputs", "status", "events", "progress", "health", "errors", "artifacts", "dependencies", "completion")
KERNEL_FIELDS = ("ownership", "checkpoint", "capabilities", "resources", "timeout", "retry", "version")


@dataclass
class Contract:
    """An engine's declared Kernel contract."""

    engine: str
    contract: dict

    def missing_fields(self) -> list[str]:
        return [f for f in KERNEL_CONTRACT_FIELDS if f not in self.contract]

    def is_conformant(self) -> bool:
        return not self.missing_fields()

    def violations(self) -> list[str]:
        return [
            f"{self.engine} missing contract field '{f}'"
            for f in self.missing_fields()
        ]


def validate_engine(engine: str, contract: dict) -> Contract:
    return Contract(engine=engine, contract=contract)


def contract_violations(registry: dict) -> list[str]:
    """Validate every registered engine against the full Kernel contract."""
    violations: list[str] = []
    for engine, contract in registry.items():
        violations.extend(validate_engine(engine, contract).violations())
    return violations


def is_kernel_engine(engine: str) -> bool:
    return engine in {"governor", "kernel"} or engine in __import__(
        "scripts.kernel.core", fromlist=["ENGINE_REGISTRY"]
    ).ENGINE_REGISTRY

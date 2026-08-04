"""Phase 10 — Engine Communication.

Standardize communication. Every engine must expose: Inputs, Outputs,
Status, Events, Progress, Health, Errors, Artifacts, Dependencies,
Completion. No direct undocumented communication.
"""

from __future__ import annotations

from dataclasses import dataclass

CONTRACT_FIELDS = (
    "inputs",
    "outputs",
    "status",
    "events",
    "progress",
    "health",
    "errors",
    "artifacts",
    "dependencies",
    "completion",
)


@dataclass
class EngineContract:
    """The standardized communication contract for a governed engine."""

    engine: str
    contract: dict

    def missing_fields(self) -> list[str]:
        return [field_name for field_name in CONTRACT_FIELDS if field_name not in self.contract]

    def is_conformant(self) -> bool:
        return not self.missing_fields()

    def violations(self) -> list[str]:
        return [
            f"{self.engine} missing contract field '{field_name}'"
            for field_name in self.missing_fields()
        ]


def validate_engine(engine: str, contract: dict) -> EngineContract:
    """Validate that an engine exposes the full communication contract."""
    return EngineContract(engine=engine, contract=contract)


def validate_all_engines(registry: dict) -> list[str]:
    """Validate every registered engine's communication contract."""
    violations: list[str] = []
    for engine, contract in registry.items():
        valid = validate_engine(engine, contract)
        violations.extend(valid.violations())
    return violations

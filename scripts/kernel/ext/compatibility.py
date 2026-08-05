"""GULA-KERNEL-EXT-001 Phase 3 — Compatibility Framework.

Detect breaking changes for contracts, plugins, policies, schemas, and
configs. Maintain a versioned compatibility matrix (human + machine
readable) and enforce the backward-compatibility constitution
(docs/constitution/23_BACKWARD_COMPATIBILITY.md).

Pure functions only; no I/O at import time. Reuses the Kernel engine
contract (scripts/kernel/contract.py) and the SDK manifest validator
(scripts/kernel/ext/plugin.py) — nothing is duplicated here.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..contract import Contract
from ..core import KERNEL_CONTRACT_FIELDS, utcnow

_SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")

COMPAT_DIR = ".ai/core/compat/"

VALID_KINDS = ("contract", "plugin", "policy", "schema", "config")


class CompatibilityError(Exception):
    """Raised for invalid compatibility inputs."""


def parse_version(version: str) -> tuple[int, int, int]:
    """Strict semantic version parse (X.Y.Z)."""
    match = _SEMVER_RE.match(version.strip())
    if not match:
        raise CompatibilityError(f"invalid semantic version: {version!r}")
    return tuple(int(part) for part in match.groups())


def compare_versions(a: str, b: str) -> int:
    """Return -1, 0, or 1 comparing semantic versions a and b."""
    av, bv = parse_version(a), parse_version(b)
    return (av > bv) - (av < bv)


def is_breaking_change(from_version: str, to_version: str) -> bool:
    """A major-version bump is a breaking change by SemVer convention."""
    return parse_version(from_version)[0] != parse_version(to_version)[0]


def check_contract(contract: dict) -> list[str]:
    """Return missing Kernel contract fields for an engine contract dict."""
    return [f for f in KERNEL_CONTRACT_FIELDS if f not in contract]


@dataclass
class CompatibilityRecord:
    """One row of the compatibility matrix."""

    kind: str
    name: str
    from_version: str
    to_version: str
    compatible: bool
    notes: str = ""
    checked_at: str = field(default_factory=utcnow)

    def __post_init__(self) -> None:
        if self.kind not in VALID_KINDS:
            raise CompatibilityError(f"unknown kind: {self.kind!r}")
        parse_version(self.from_version)
        parse_version(self.to_version)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "name": self.name,
            "from_version": self.from_version,
            "to_version": self.to_version,
            "compatible": self.compatible,
            "notes": self.notes,
            "checked_at": self.checked_at,
        }


@dataclass
class CompatibilityMatrix:
    """Versioned, searchable matrix of compatibility checks."""

    records: list[CompatibilityRecord] = field(default_factory=list)

    def add(self, kind: str, name: str, from_version: str, to_version: str,
            compatible: bool, notes: str = "") -> CompatibilityRecord:
        record = CompatibilityRecord(kind, name, from_version, to_version, compatible, notes)
        self.records.append(record)
        return record

    def entries(self, kind: str | None = None) -> list[CompatibilityRecord]:
        if kind is None:
            return list(self.records)
        return [r for r in self.records if r.kind == kind]

    def for_name(self, name: str) -> list[CompatibilityRecord]:
        return [r for r in self.records if r.name == name]

    def breaking(self) -> list[CompatibilityRecord]:
        return [r for r in self.records if not r.compatible]

    def is_compatible(self, name: str) -> bool:
        """Latest recorded check for name is compatible (default True)."""
        if not self.records:
            return True
        matches = self.for_name(name)
        if not matches:
            return True
        latest = max(matches, key=lambda r: parse_version(r.to_version))
        return latest.compatible

    def snapshot(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0.0",
            "records": [r.to_dict() for r in self.records],
        }

    def save(self, path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.snapshot(), indent=2) + "\n", encoding="utf-8")
        return path

    @classmethod
    def load(cls, path: str | Path) -> CompatibilityMatrix:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls([CompatibilityRecord(**r) for r in data["records"]])

    def render_markdown(self) -> str:
        lines = [
            "# COMPATIBILITY MATRIX",
            "",
            f"_Generated: {utcnow()}_",
            "",
            "| Kind | Name | From | To | Compatible | Notes |",
            "|---|---|---|---|---|---|",
        ]
        for record in self.records:
            status = "PASS" if record.compatible else "**BREAKING**"
            lines.append(
                f"| {record.kind} | {record.name} | {record.from_version} "
                f"| {record.to_version} | {status} | {record.notes} |"
            )
        return "\n".join(lines)


def engine_matrix(registry: dict) -> CompatibilityMatrix:
    """Build a compatibility matrix for every engine in the Kernel registry."""
    matrix = CompatibilityMatrix()
    for engine, contract in registry.items():
        missing = check_contract(contract)
        if missing:
            matrix.add("contract", engine, "0.0.0", str(contract.get("version", "0.0.0")),
                       False, f"missing fields: {', '.join(missing)}")
        else:
            matrix.add("contract", engine, "0.0.0", str(contract.get("version", "0.0.0")),
                       True, "kernel contract conformant")
    return matrix


def is_contract_conformant(contract: dict) -> bool:
    """True when the contract dict satisfies the full Kernel contract."""
    return Contract(engine="check", contract=contract).is_conformant()

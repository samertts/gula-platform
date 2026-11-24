"""Contract tests: explicit versioning and the no-exposed-endpoint guarantee."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
from app.health_core.contracts.version import (
    COMPATIBLE_MAJOR,
    CONTRACT_STATUS,
    HEALTH_CORE_CONTRACT_VERSION,
    contract_major,
    is_compatible_version,
)

CONTRACTS_DIR = Path(__file__).resolve().parents[2] / "app" / "health_core" / "contracts"


def test_version_constant_is_explicit_prerelease() -> None:
    assert HEALTH_CORE_CONTRACT_VERSION == "1.0.0-alpha1"
    assert "-" in HEALTH_CORE_CONTRACT_VERSION
    assert CONTRACT_STATUS == "LOCAL_SYNTHETIC_ONLY"


def test_contract_major_parses_prerelease() -> None:
    assert contract_major(HEALTH_CORE_CONTRACT_VERSION) == 1
    assert contract_major("2.4.7") == 2


@pytest.mark.parametrize("version", ["", "1", "1.0", "alpha.1", "x.0.0"])
def test_malformed_versions_are_rejected(version: str) -> None:
    with pytest.raises(ValueError):
        contract_major(version)


def test_compatibility_is_major_scoped() -> None:
    assert COMPATIBLE_MAJOR == 1
    assert is_compatible_version("1.9.9")
    assert is_compatible_version(HEALTH_CORE_CONTRACT_VERSION)
    assert not is_compatible_version("2.0.0")


def test_contracts_package_contains_expected_modules() -> None:
    names = {path.stem for path in CONTRACTS_DIR.glob("*.py")}
    assert {
        "__init__",
        "authorization",
        "catalogue",
        "errors",
        "events",
        "idempotency",
        "models",
        "version",
    } <= names


def test_contracts_package_creates_no_fastapi_router_or_route() -> None:
    """No contract module may import FastAPI or construct an APIRouter."""
    violations: list[str] = []
    for path in sorted(CONTRACTS_DIR.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            module = ""
            if isinstance(node, ast.ImportFrom) and node.module:
                module = node.module
            elif isinstance(node, ast.Import):
                module = node.names[0].name if node.names else ""
            if module.split(".", 1)[0] == "fastapi":
                violations.append(f"{path.name}:{node.lineno} imports {module}")
            if isinstance(node, ast.Name) and node.id in {"APIRouter", "FastAPI"}:
                violations.append(f"{path.name}:{node.lineno} references {node.id}")
    assert violations == [], "contracts must not expose endpoints:\n" + "\n".join(violations)

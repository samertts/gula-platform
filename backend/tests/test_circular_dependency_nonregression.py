"""Unit tests for the CI guard that rejects newly introduced import cycles."""

from __future__ import annotations

import importlib.util
import pathlib
from types import ModuleType

SCRIPT_PATH = (
    pathlib.Path(__file__).resolve().parents[2] / "scripts" / "circular_dependency_nonregression.py"
)


def load_guard() -> ModuleType:
    spec = importlib.util.spec_from_file_location("circular_dependency_nonregression", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_canonical_cycle_ignores_rotation_and_terminal_repeat() -> None:
    guard = load_guard()

    assert guard.canonical_cycle(("beta", "gamma", "alpha", "beta")) == ("alpha", "beta", "gamma")
    assert guard.canonical_cycle(("gamma", "alpha", "beta", "gamma")) == ("alpha", "beta", "gamma")


def test_extract_l2_cycles_uses_canonical_identities() -> None:
    guard = load_guard()
    report = {
        "results": [
            {
                "rule": "L2",
                "details": [
                    "Found 2 circular dependenc(ies):",
                    "  - alpha → beta → gamma → alpha",
                    "  - beta → gamma → alpha → beta",
                ],
            }
        ]
    }

    assert guard.extract_l2_cycles(report) == {("alpha", "beta", "gamma")}


def test_extract_l2_cycles_rejects_missing_l2() -> None:
    guard = load_guard()

    try:
        guard.extract_l2_cycles({"results": []})
    except ValueError as exc:
        assert "L2" in str(exc)
    else:
        raise AssertionError("expected malformed architecture report to be rejected")

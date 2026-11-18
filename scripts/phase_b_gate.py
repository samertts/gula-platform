#!/usr/bin/env python3
"""Deterministic Phase B integration gate for the National Integration Program.

Runs the full evidence ladder against the integration checkout and reports a
single machine-readable verdict. It is deliberatelyREAD-ONLY: it never stages,
commits, migrates, writes a file, or touches a database. Every check is a
subprocess invocation whose exit status and trailing output are captured.

Checks (in mandatory order):
  1. preservation  - protected md5s, both repo HEADs, zero tracked deletions
  2. registry      - national_integration_verify.py returns PASS
  3. focused       - every Phase B / Phase A focused test file
  4. static        - ruff on the new source packages + governance scripts
  5. types         - mypy on the Health Core package (project invocation)
  6. regression    - the 773-test Health Core gate

Exit 0 = all checks PASS; exit 1 = at least one FAIL. A missing expected test
file or source package is a FAIL, never a silent skip.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
VENV = Path("/home/samertts/workspace/projects/gula-platform/backend/.venv/bin")
PYTHON = VENV / "python"
RUFF = VENV / "ruff"
MYPY = VENV / "mypy"

INTEGRATION_REPO = REPO_ROOT
PLATFORM_REPO = Path("/home/samertts/workspace/projects/gula-platform")

EXPECTED_INTEGRATION_BRANCH = "integration/gula-unification-v1"
# The platform worktree is READ-ONLY for this program, so its HEAD is a hard pin.
EXPECTED_PLATFORM_HEAD = "f478676b6fc375338648dde46fbf076c015a3f91"
# The integration branch is explicitly authorized to advance via local reviewed
# commits, so its HEAD is verified for shape/branch, not pinned to one hash.
HEAD_RE = re.compile(r"^[0-9a-f]{40}$")

PROTECTED = {
    "GOVERNANCE/FINAL_DECISION.md": "effdfeaf10234678d83b2668c4489552",
    "GOVERNANCE/IDENTITY_REMEDIATION/MPI_FINAL_INDEPENDENT_AUDIT.md": "1a02c01563c93b07a7cdb92c0462bf36",
    "GOVERNANCE/IDENTITY_REMEDIATION/MPI_INDEPENDENT_AUDIT_FINDINGS.md": "ea3969d09aaf7b0b28a065838b44a594",
}

FOCUSED_TESTS = (
    "backend/tests/unit/test_national_integration_registry.py",
    "backend/tests/unit/test_nr011_metadata_discovery.py",
    "backend/tests/unit/test_terminology_checkdigit.py",
    "backend/tests/unit/test_reliability_durable_queue.py",
    "backend/tests/unit/test_audit_anchor.py",
    "backend/tests/unit/test_fhir_http_endpoints.py",
)

RUFF_TARGETS = (
    "scripts/national_integration_verify.py",
    "scripts/phase_b_gate.py",
    "backend/app/health_core/terminology",
    "backend/app/health_core/reliability",
    "backend/app/health_core/audit_anchor",
    # The FHIR HTTP interface lives in app/interoperability, NOT app/health_core:
    # the WS-E structural guard requires the synthetic Health Core slice to stay
    # free of FastAPI/HTTP boundary dependencies.
    "backend/app/interoperability/fhir_http",
    "backend/tests/unit/test_national_integration_registry.py",
    "backend/tests/unit/test_terminology_checkdigit.py",
    "backend/tests/unit/test_reliability_durable_queue.py",
    "backend/tests/unit/test_audit_anchor.py",
    "backend/tests/unit/test_fhir_http_endpoints.py",
)


@dataclass
class Check:
    name: str
    ok: bool
    detail: str
    commands: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": "PASS" if self.ok else "FAIL",
            "detail": self.detail,
            "commands": self.commands,
        }


def _run(cmd: list[str], cwd: Path, *, env_extra: dict[str, str] | None = None) -> tuple[int, str]:
    import os

    env = os.environ.copy()
    env.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    if env_extra:
        env.update(env_extra)
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=600,
            check=False,
            env=env,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return 127, f"cannot execute {cmd[0]!r}: {exc}"
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def _record(commands: list[dict[str, Any]], cmd: list[str], rc: int, out: str) -> None:
    commands.append(
        {
            "command": " ".join(str(part) for part in cmd),
            "exit": rc,
            "tail": out.splitlines()[-6:],
        }
    )


def _md5(path: Path) -> str:
    digest = hashlib.md5()  # integrity checksum, not a security primitive
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check_preservation() -> Check:
    failures: list[str] = []
    commands: list[dict[str, Any]] = []
    for relpath, expected in PROTECTED.items():
        target = INTEGRATION_REPO / relpath
        if not target.is_file():
            failures.append(f"missing protected file: {relpath}")
        elif _md5(target) != expected:
            failures.append(f"protected md5 changed: {relpath}")
    # Platform worktree: hard HEAD pin (read-only for this program).
    rc, out = _run(["git", "rev-parse", "HEAD"], PLATFORM_REPO)
    _record(commands, ["git", "rev-parse", "HEAD"], rc, out)
    if rc != 0 or out.strip() != EXPECTED_PLATFORM_HEAD:
        failures.append(f"platform HEAD drifted (expected {EXPECTED_PLATFORM_HEAD[:8]}, got {out[:8]})")

    # Integration branch: verify the authorized branch and a well-formed HEAD.
    # Its hash is intentionally NOT pinned because local reviewed commits must
    # be able to advance it.
    rc, out = _run(["git", "branch", "--show-current"], INTEGRATION_REPO)
    _record(commands, ["git", "branch", "--show-current"], rc, out)
    if rc != 0 or out.strip() != EXPECTED_INTEGRATION_BRANCH:
        failures.append(f"wrong branch (expected {EXPECTED_INTEGRATION_BRANCH}, got {out.strip()})")
    rc, out = _run(["git", "rev-parse", "HEAD"], INTEGRATION_REPO)
    _record(commands, ["git", "rev-parse", "HEAD"], rc, out)
    if rc != 0 or not HEAD_RE.fullmatch(out.strip()):
        failures.append(f"integration HEAD malformed: {out[:8]}")

    rc, out = _run(["git", "status", "--porcelain=v1"], INTEGRATION_REPO)
    _record(commands, ["git", "status", "--porcelain=v1"], rc, out)
    deletions = [line for line in out.splitlines() if line[:2].strip() and "D" in line[:2]]
    if rc != 0:
        failures.append("git status failed")
    elif deletions:
        failures.append(f"tracked deletions present: {len(deletions)}")
    return Check(
        "preservation",
        not failures,
        "protected md5s intact; platform HEAD pinned; authorized integration branch; 0 tracked deletions"
        if not failures
        else "; ".join(failures),
        commands,
    )


def check_registry() -> Check:
    cmd = [
        str(PYTHON),
        "scripts/national_integration_verify.py",
        "--registry",
        "GOVERNANCE/NATIONAL_INTEGRATION/status_registry.json",
        "--repo-root",
        ".",
    ]
    rc, out = _run(cmd, INTEGRATION_REPO)
    commands: list[dict[str, Any]] = []
    _record(commands, cmd, rc, out)
    return Check("registry", rc == 0, out.splitlines()[-1] if out else "no output", commands)


def check_focused() -> Check:
    commands: list[dict[str, Any]] = []
    failures: list[str] = []
    for relpath in FOCUSED_TESTS:
        path = INTEGRATION_REPO / relpath
        if not path.is_file():
            failures.append(f"missing expected test file: {relpath}")
            continue
        cmd = [
            str(PYTHON),
            "-m",
            "pytest",
            f"tests/unit/{path.name}",
            "-q",
            "--tb=short",
        ]
        rc, out = _run(
            cmd,
            INTEGRATION_REPO / "backend",
            env_extra={"ENV": "test", "PYTHONPATH": ".:.."},
        )
        _record(commands, cmd, rc, out)
        summary = next((line for line in reversed(out.splitlines()) if " passed" in line or " error" in line), "")
        if rc != 0:
            failures.append(f"{relpath}: {summary or 'failed'}")
    return Check(
        "focused",
        not failures,
        f"{len(FOCUSED_TESTS) - len(failures)}/{len(FOCUSED_TESTS)} focused suites passed"
        if not failures
        else "; ".join(failures),
        commands,
    )


def check_ruff() -> Check:
    existing = [target for target in RUFF_TARGETS if (INTEGRATION_REPO / target).exists()]
    missing = [target for target in RUFF_TARGETS if target not in existing]
    cmd = [str(RUFF), "check", *existing, "--output-format", "concise"]
    rc, out = _run(cmd, INTEGRATION_REPO)
    commands: list[dict[str, Any]] = []
    _record(commands, cmd, rc, out)
    detail = out.splitlines()[-1] if out else "no output"
    if missing:
        detail += f" (MISSING TARGETS: {', '.join(missing)})"
    return Check("static", rc == 0 and not missing, detail, commands)


# Documented pre-existing MyPy errors (PROGRAM-BACKEND-001 baseline): the two
# untyped helpers in app/domain/order_state.py. They are pulled in transitively
# by Health Core imports and are NOT owned by this program. Every other error
# is a new regression and fails the gate.
BASELINE_MYPY_ERRORS = (
    "app/domain/order_state.py:63: error: Function is missing a type annotation",
    "app/domain/order_state.py:81: error: Function is missing a type annotation",
)


def check_mypy() -> Check:
    cmd = [str(MYPY), "app/health_core", "--ignore-missing-imports"]
    rc, out = _run(cmd, INTEGRATION_REPO / "backend")
    commands: list[dict[str, Any]] = []
    _record(commands, cmd, rc, out)
    lines = out.splitlines()
    errors = [line for line in lines if ": error:" in line]
    new_errors = [
        line
        for line in errors
        if not any(line.startswith(known) for known in BASELINE_MYPY_ERRORS)
    ]
    detail = (
        f"{len(new_errors)} new MyPy error(s); {len(errors) - len(new_errors)} documented baseline tolerated"
        if new_errors
        else f"0 new MyPy errors ({len(errors) - len(new_errors)} documented baseline tolerated)"
    )
    if new_errors:
        detail += " :: " + " | ".join(new_errors[:3])
    return Check("types", not new_errors, detail, commands)


def check_regression() -> Check:
    cmd = [str(PYTHON), "-m", "pytest", "tests/health_core", "-q", "--tb=short"]
    rc, out = _run(
        cmd,
        INTEGRATION_REPO / "backend",
        env_extra={"ENV": "test", "RUNTIME_MODE": "test", "PYTHONPATH": ".:.."},
    )
    commands: list[dict[str, Any]] = []
    _record(commands, cmd, rc, out)
    summary = next((line for line in reversed(out.splitlines()) if " passed" in line or " failed" in line), "no summary")
    return Check("regression", rc == 0 and "773 passed" in out, summary, commands)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit full JSON result")
    parser.add_argument("--only", nargs="*", help="run only named checks")
    args = parser.parse_args(argv)

    all_checks = {
        "preservation": check_preservation,
        "registry": check_registry,
        "focused": check_focused,
        "static": check_ruff,
        "types": check_mypy,
        "regression": check_regression,
    }
    selected = args.only if args.only else list(all_checks)
    unknown = [name for name in selected if name not in all_checks]
    if unknown:
        sys.stderr.write(f"unknown checks: {unknown}\n")
        return 2

    results = [all_checks[name]() for name in selected]
    verdict = "PASS" if all(check.ok for check in results) else "FAIL"
    if args.json:
        payload = {
            "verdict": verdict,
            "checks": [check.as_dict() for check in results],
        }
        sys.stdout.write(json.dumps(payload, indent=2) + "\n")
    else:
        for check in results:
            sys.stdout.write(f"[{'PASS' if check.ok else 'FAIL'}] {check.name}: {check.detail}\n")
        sys.stdout.write(f"PHASE B INTEGRATION GATE: {verdict}\n")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

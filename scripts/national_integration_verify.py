#!/usr/bin/env python3
"""Validate the National Integration machine-readable status registry.

The registry (``GOVERNANCE/NATIONAL_INTEGRATION/status_registry.json``) is the
single machine-readable index of the national integration program. This tool
verifies that it is internally consistent and still matches the on-disk
evidence it claims to describe:

* required document set (``00`` ... ``14`` + registry) exists;
* the declared vocabulary is **exactly** the canonical seven statuses, and
  **every** key named ``status`` anywhere in the registry uses one of them;
* protected governance records are all present and still carry their md5s;
* the seven workstreams and the owner-gated decision IDs are all present;
* every workstream survey referenced by the registry exists;
* the git HEAD fields are syntactically valid (a mismatch is a WARNING:
  the recorded value is a baseline snapshot, not a moving pointer);
* the safety invariant ``production_ready_items == 0`` holds.

This is a governance-integrity tool. It makes no production claim, performs no
network or database access, and never modifies any file. The vocabulary is
pinned in this script — a registry cannot widen its own status set to pass.

Exit codes: 0 = PASS (warnings allowed), 1 = one or more integrity failures.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_REL = Path("GOVERNANCE") / "NATIONAL_INTEGRATION" / "status_registry.json"
REQUIRED_DOCS = tuple(f"{n:02d}" for n in range(15))

# Pinned canonical vocabulary — deliberately NOT read from the registry.
CANONICAL_STATUS: tuple[str, ...] = (
    "IMPLEMENTED",
    "TESTED",
    "INTEGRATED",
    "INDEPENDENTLY VERIFIED",
    "PRODUCTION READY",
    "BLOCKED",
    "NOT IMPLEMENTED",
)

EXPECTED_PROTECTED_PATHS: tuple[str, ...] = (
    "GOVERNANCE/FINAL_DECISION.md",
    "GOVERNANCE/IDENTITY_REMEDIATION/MPI_FINAL_INDEPENDENT_AUDIT.md",
    "GOVERNANCE/IDENTITY_REMEDIATION/MPI_INDEPENDENT_AUDIT_FINDINGS.md",
)
EXPECTED_WORKSTREAMS: tuple[str, ...] = tuple(f"WS-{n:02d}" for n in range(1, 8))
EXPECTED_GOVERNANCE_IDS: tuple[str, ...] = (
    "HOLD",
    "MPI REJECT",
    "MP-001",
    "ODR-001",
    "ODR-002",
    "ODR-003",
    "ODR-004",
    "D-020",
    "D-021",
    "ADR-A",
    "ADR-B",
    "ADR-C",
    "ADR-D",
    "ADR-E",
    "ADR-F",
    "ADR-G",
    "ADR-H",
    "ADR-I",
    "ADR-J",
    "NR-011",
    "AUD-02",
    "AUD-07",
    "AUD-16",
)

SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
MD5_RE = re.compile(r"^[0-9a-f]{32}$")


def load_registry(path: Path) -> dict[str, Any]:
    """Load and return the registry JSON (raises on malformed JSON)."""
    return json.loads(path.read_text(encoding="utf-8"))


def file_md5(path: Path) -> str:
    """Return the lowercase md5 of a file, read in bounded chunks."""
    digest = hashlib.md5()  # integrity checksum, not a security primitive
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_head(repo_root: Path) -> str | None:
    """Return a repo's HEAD, or None when git is unavailable."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def iter_statuses(node: Any, path: str = "registry") -> Iterator[tuple[str, Any]]:
    """Yield ``(path, value)`` for every key named ``status`` in a nested value."""
    if isinstance(node, dict):
        for key, value in node.items():
            child = f"{path}.{key}"
            if key == "status":
                yield child, value
            yield from iter_statuses(value, child)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from iter_statuses(value, f"{path}[{index}]")


def validate(registry: dict[str, Any], repo_root: Path = REPO_ROOT) -> tuple[list[str], list[str]]:
    """Validate a registry against an on-disk repository root.

    Returns ``(errors, warnings)``. Pure function with respect to its inputs:
    nothing is written.
    """
    errors: list[str] = []
    warnings: list[str] = []
    gi_dir = repo_root / "GOVERNANCE" / "NATIONAL_INTEGRATION"

    required_keys = (
        "schema_version",
        "status_vocabulary",
        "repositories",
        "protected_evidence",
        "baseline",
        "phases",
        "workstreams",
        "governance_items",
        "production_ready_items",
    )
    for key in required_keys:
        if key not in registry:
            errors.append(f"registry is missing required key: {key}")
    if errors:
        return errors, warnings

    # 1. Vocabulary is pinned here; the registry may not define its own.
    declared = registry["status_vocabulary"]
    if (
        not isinstance(declared, list)
        or len(declared) != len(CANONICAL_STATUS)
        or set(declared) != set(CANONICAL_STATUS)
    ):
        errors.append(
            "status_vocabulary must state exactly the seven canonical statuses "
            f"({', '.join(CANONICAL_STATUS)})"
        )
    for where, value in iter_statuses(registry):
        if value not in CANONICAL_STATUS:
            errors.append(f"{where}: undeclared status {value!r}")

    # 2. Required numbered documents.
    for prefix in REQUIRED_DOCS:
        if not list(gi_dir.glob(f"{prefix}_*.md")):
            errors.append(f"missing required document {prefix}_* in {gi_dir}")

    # 3. Structural completeness: empty containers must never pass silently.
    protected = registry["protected_evidence"]
    if not isinstance(protected, list) or not protected:
        errors.append("protected_evidence must be a non-empty list")
    else:
        seen_paths = {
            str(record.get("path")) for record in protected if isinstance(record, dict)
        }
        for expected in EXPECTED_PROTECTED_PATHS:
            if expected not in seen_paths:
                errors.append(f"protected_evidence is missing required record: {expected}")

    workstreams = registry["workstreams"]
    if not isinstance(workstreams, dict) or not workstreams:
        errors.append("workstreams must be a non-empty object")
    else:
        for expected in EXPECTED_WORKSTREAMS:
            if expected not in workstreams:
                errors.append(f"workstreams is missing required entry: {expected}")
        for ws_id, ws in workstreams.items():
            if not isinstance(ws, dict):
                errors.append(f"workstreams.{ws_id} must be an object")
                continue
            survey = ws.get("survey")
            if survey and not (gi_dir / str(survey)).is_file():
                errors.append(f"workstreams.{ws_id}: survey file missing: {survey}")

    governance = registry["governance_items"]
    if not isinstance(governance, list) or not governance:
        errors.append("governance_items must be a non-empty list")
    else:
        seen_ids = {str(item.get("id")) for item in governance if isinstance(item, dict)}
        for expected in EXPECTED_GOVERNANCE_IDS:
            if expected not in seen_ids:
                errors.append(f"governance_items is missing required entry: {expected}")

    # 4. Protected evidence md5s still match on disk.
    for record in protected if isinstance(protected, list) else []:
        if not isinstance(record, dict):
            errors.append("protected_evidence contains a non-object record")
            continue
        target = repo_root / str(record.get("path", ""))
        expected_md5 = str(record.get("md5", ""))
        if not MD5_RE.fullmatch(expected_md5):
            errors.append(f"protected evidence has invalid md5: {record.get('path')}")
            continue
        if not str(record.get("verdict", "")):
            errors.append(f"protected evidence has empty verdict: {record.get('path')}")
        if not target.is_file():
            errors.append(f"protected evidence file missing: {record.get('path')}")
            continue
        actual = file_md5(target)
        if actual != expected_md5:
            errors.append(
                f"protected evidence md5 changed: {record['path']} "
                f"(expected {expected_md5}, found {actual})"
            )

    # 5. Git HEAD fields are well formed; mismatch is advisory only.
    repositories = registry["repositories"]
    if not isinstance(repositories, dict) or not repositories:
        errors.append("repositories must be a non-empty object")
    else:
        for name, repo in repositories.items():
            if not isinstance(repo, dict):
                errors.append(f"repositories.{name} must be an object")
                continue
            head = str(repo.get("head", ""))
            if not SHA1_RE.fullmatch(head):
                errors.append(f"repositories.{name}: malformed HEAD {head!r}")
                continue
            path = Path(str(repo.get("path", "")))
            if not path.is_dir():
                warnings.append(f"repositories.{name}: path not present here ({path})")
                continue
            current = _git_head(path)
            if current is None:
                warnings.append(f"repositories.{name}: git HEAD unavailable")
            elif current != head:
                warnings.append(
                    f"repositories.{name}: HEAD moved since baseline "
                    f"(recorded {head[:8]}, current {current[:8]})"
                )

    # 6. Safety invariant: this program must never self-award production readiness.
    if registry["production_ready_items"] != 0:
        errors.append(
            "production_ready_items must be 0 — owner sign-off is required "
            "for any production-ready claim"
        )

    return errors, warnings


def _emit(text: str, *, error: bool = False) -> None:
    """Write CLI output without using the project-banned print builtin."""
    stream = sys.stderr if error else sys.stdout
    stream.write(text if text.endswith("\n") else text + "\n")
    stream.flush()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--registry",
        type=Path,
        default=REPO_ROOT / REGISTRY_REL,
        help="path to status_registry.json",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="repository root that the registry describes",
    )
    parser.add_argument("--json", action="store_true", help="emit a JSON result")
    args = parser.parse_args(argv)

    try:
        registry = load_registry(args.registry)
    except (OSError, json.JSONDecodeError) as exc:
        message = f"cannot load registry: {exc}"
        if args.json:
            _emit(json.dumps({"verdict": "FAIL", "errors": [message], "warnings": []}))
        else:
            _emit(f"FAIL: {message}\n", error=True)
        return 1

    errors, warnings = validate(registry, args.repo_root)
    verdict = "PASS" if not errors else "FAIL"
    if args.json:
        _emit(
            json.dumps(
                {
                    "verdict": verdict,
                    "errors": errors,
                    "warnings": warnings,
                    "registry": str(args.registry),
                },
                indent=2,
            )
        )
    else:
        for warning in warnings:
            _emit(f"WARN: {warning}\n")
        for error in errors:
            _emit(f"ERROR: {error}\n", error=True)
        _emit(f"NATIONAL INTEGRATION REGISTRY VERDICT: {verdict}\n")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

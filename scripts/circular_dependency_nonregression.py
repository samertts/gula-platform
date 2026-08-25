#!/usr/bin/env python3
"""Fail a change when it introduces a new backend circular dependency.

This check deliberately compares canonical L2 cycles between a base ref and a
head ref. Historical cycles remain visible in the report, but a pull request
cannot add another cycle or alter one into a new cycle without failing CI.
It does not declare the historical baseline compliant.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Iterable
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
ENGINE_RELATIVE_PATH = pathlib.Path("scripts/architecture_compliance_engine.py")


def run_git(*args: str, cwd: pathlib.Path = REPO_ROOT) -> str:
    """Run Git read-only/temporary-worktree operations with bounded output."""
    proc = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "git command failed")
    return proc.stdout.strip()


def resolve_ref(ref: str) -> str:
    return run_git("rev-parse", "--verify", f"{ref}^{{commit}}")


def canonical_cycle(cycle: Iterable[str]) -> tuple[str, ...]:
    """Normalize a directed cycle by rotation while preserving edge direction."""
    nodes = tuple(node for node in cycle if node)
    if len(nodes) > 1 and nodes[0] == nodes[-1]:
        nodes = nodes[:-1]
    if not nodes:
        return ()
    rotations = [nodes[index:] + nodes[:index] for index in range(len(nodes))]
    return min(rotations)


def extract_l2_cycles(report: dict[str, Any]) -> set[tuple[str, ...]]:
    """Extract canonical cycle identities from architecture-engine JSON output."""
    results = report.get("results")
    if not isinstance(results, list):
        raise ValueError("architecture report has no results list")
    for item in results:
        if not isinstance(item, dict) or item.get("rule") != "L2":
            continue
        details = item.get("details", [])
        if not isinstance(details, list):
            raise ValueError("L2 details are malformed")
        cycles: set[tuple[str, ...]] = set()
        for detail in details:
            if not isinstance(detail, str) or not detail.lstrip().startswith("-"):
                continue
            parts = [part.strip() for part in detail.lstrip()[1:].split("→")]
            normalized = canonical_cycle(parts)
            if normalized:
                cycles.add(normalized)
        return cycles
    raise ValueError("architecture report has no L2 result")


def run_engine(worktree: pathlib.Path, source_engine: pathlib.Path) -> set[tuple[str, ...]]:
    """Run the same checked-in engine against an isolated ref worktree."""
    destination = worktree / ENGINE_RELATIVE_PATH
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_engine, destination)
    proc = subprocess.run(
        [
            sys.executable,
            str(destination),
            "--json",
            "--focus",
            "L2",
            "--exclude-dirs",
            "tests,migrations,__pycache__",
        ],
        cwd=worktree,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    try:
        report = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"architecture engine produced invalid JSON for {worktree.name}: {proc.stderr.strip()}"
        ) from exc
    return extract_l2_cycles(report)


def render_cycle(cycle: tuple[str, ...]) -> str:
    return " → ".join((*cycle, cycle[0]))


def build_report(base_ref: str, head_ref: str) -> dict[str, Any]:
    base_sha = resolve_ref(base_ref)
    head_sha = resolve_ref(head_ref)
    source_engine = REPO_ROOT / ENGINE_RELATIVE_PATH
    if not source_engine.is_file():
        raise RuntimeError(f"architecture engine is missing: {source_engine}")

    with tempfile.TemporaryDirectory(prefix="gula-circular-nonregression-") as temp_dir:
        temp_root = pathlib.Path(temp_dir)
        base_tree = temp_root / "base"
        head_tree = temp_root / "head"
        created: list[pathlib.Path] = []
        try:
            run_git("worktree", "add", "--detach", "--quiet", str(base_tree), base_sha)
            created.append(base_tree)
            run_git("worktree", "add", "--detach", "--quiet", str(head_tree), head_sha)
            created.append(head_tree)
            base_cycles = run_engine(base_tree, source_engine)
            head_cycles = run_engine(head_tree, source_engine)
        finally:
            for worktree in reversed(created):
                subprocess.run(
                    ["git", "worktree", "remove", "--force", str(worktree)],
                    cwd=REPO_ROOT,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=60,
                )

    new_cycles = sorted(head_cycles - base_cycles)
    resolved_cycles = sorted(base_cycles - head_cycles)
    return {
        "status": "FAIL" if new_cycles else "PASS",
        "base_ref": base_ref,
        "base_sha": base_sha,
        "head_ref": head_ref,
        "head_sha": head_sha,
        "baseline_cycle_count": len(base_cycles),
        "head_cycle_count": len(head_cycles),
        "new_cycles": [render_cycle(cycle) for cycle in new_cycles],
        "resolved_cycles": [render_cycle(cycle) for cycle in resolved_cycles],
        "note": (
            "Historical cycles are reported as baseline debt. Any new canonical directed cycle fails this gate."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fail when a change introduces a new circular backend dependency."
    )
    parser.add_argument("--base-ref", required=True)
    parser.add_argument("--head-ref", required=True)
    parser.add_argument("--report", type=pathlib.Path)
    args = parser.parse_args(argv)

    try:
        report = build_report(args.base_ref, args.head_ref)
    except (OSError, RuntimeError, subprocess.TimeoutExpired, ValueError) as exc:
        report = {
            "status": "ERROR",
            "base_ref": args.base_ref,
            "head_ref": args.head_ref,
            "error": str(exc),
        }

    serialized = json.dumps(report, indent=2, sort_keys=True)
    if args.report:
        args.report.write_text(serialized + "\n", encoding="utf-8")
    print(serialized)  # noqa: T201 - CI contract: emit the machine-readable report.
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

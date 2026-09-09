#!/usr/bin/env python3
"""Fail CI when a change increases Ruff or MyPy errors.

The gate deliberately does not require repository-wide zero debt. It enforces
non-regression in changed Python files and in the configured critical scopes.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

DEFAULT_CRITICAL_SCOPES = (
    "backend/app/security",
    "backend/app/identity",
    "backend/app/clinical_gateway",
    "backend/app/audit",
    "backend/app/authorization",
)

MYPY_ERROR_RE = re.compile(
    r"^(?P<path>.*?):(?P<line>\d+): error: (?P<message>.*?)(?: \[(?P<code>[\w-]+)\])?$"
)


@dataclass(frozen=True)
class Diagnostic:
    path: str
    line: int | None
    code: str | None
    message: str


@dataclass(frozen=True)
class ToolResult:
    tool: str
    scope: str
    returncode: int
    diagnostics: tuple[Diagnostic, ...]
    stdout: str
    stderr: str
    execution_error: str | None = None

    @property
    def measured(self) -> bool:
        """Whether this result is evidence of anything.

        A tool that failed to start, crashed, or was invoked wrongly produces no
        analysis. Its empty diagnostic list means "unknown", never "clean", and
        every consumer below has to know the difference.
        """
        return self.execution_error is None

    @property
    def counts(self) -> Counter[str]:
        return Counter(diagnostic.path for diagnostic in self.diagnostics)


def run(command: Sequence[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        cwd=cwd,
        check=False,
        text=True,
        capture_output=True,
    )


def git_ref(repo: Path, ref: str) -> str:
    result = run(("git", "rev-parse", "--verify", ref), repo)
    if result.returncode != 0:
        raise RuntimeError(f"Git ref does not resolve: {ref}\n{result.stderr.strip()}")
    return result.stdout.strip()


def changed_python_files(repo: Path, base: str, head: str) -> list[str]:
    result = run(("git", "diff", "--name-only", "--diff-filter=ACMR", f"{base}...{head}"), repo)
    if result.returncode != 0:
        raise RuntimeError(f"Unable to determine changed files:\n{result.stderr.strip()}")
    paths = {
        line.strip().replace(os.sep, "/")
        for line in result.stdout.splitlines()
        if line.strip().endswith(".py")
    }
    return sorted(path for path in paths if not path.startswith("/"))


def normalise_path(repo: Path, raw_path: str) -> str:
    path = raw_path.strip().replace("\\", "/")
    try:
        candidate = Path(path)
        if candidate.is_absolute():
            path = candidate.relative_to(repo).as_posix()
        else:
            path = candidate.as_posix()
    except ValueError:
        path = Path(path).name
    return path.removeprefix("./")


def parse_ruff_json(repo: Path, output: str) -> tuple[Diagnostic, ...]:
    if not output.strip():
        return ()
    try:
        payload = json.loads(output)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Ruff returned invalid JSON: {exc}") from exc
    diagnostics: list[Diagnostic] = []
    for item in payload:
        location = item.get("location") or {}
        diagnostics.append(
            Diagnostic(
                path=normalise_path(repo, str(item.get("filename", ""))),
                line=location.get("row"),
                code=item.get("code"),
                message=str(item.get("message", "")),
            )
        )
    return tuple(diagnostics)


def parse_mypy_text(repo: Path, output: str) -> tuple[Diagnostic, ...]:
    diagnostics: list[Diagnostic] = []
    for raw_line in output.splitlines():
        match = MYPY_ERROR_RE.match(raw_line.strip())
        if not match:
            continue
        diagnostics.append(
            Diagnostic(
                path=normalise_path(repo, match.group("path")),
                line=int(match.group("line")),
                code=match.group("code"),
                message=match.group("message"),
            )
        )
    return tuple(diagnostics)


def limit_to_requested_paths(
    diagnostics: Sequence[Diagnostic], paths: Sequence[str],
) -> tuple[Diagnostic, ...]:
    """Keep only diagnostics emitted for the exact files this gate evaluates.

    MyPy follows imports and prints errors from transitive modules.  Those
    modules are not evidence of a regression in the changed-file or critical
    scope being compared, so including them makes the baseline comparison
    depend on unrelated import-graph changes.
    """
    requested = {path.replace(os.sep, "/") for path in paths}
    return tuple(diagnostic for diagnostic in diagnostics if diagnostic.path in requested)


def run_ruff(repo: Path, paths: Sequence[str], scope: str) -> ToolResult:
    if not paths:
        return ToolResult("ruff", scope, 0, (), "", "")
    result = run(("ruff", "check", "--output-format", "json", *paths), repo)
    # Ruff: 0 = clean, 1 = violations found, anything else = it did not run.
    execution_error = (
        None
        if result.returncode in (0, 1)
        else (result.stderr.strip() or result.stdout.strip() or f"ruff exited {result.returncode}")
    )
    diagnostics = parse_ruff_json(repo, result.stdout) if execution_error is None else ()
    return ToolResult(
        "ruff",
        scope,
        result.returncode,
        diagnostics,
        result.stdout,
        result.stderr,
        execution_error,
    )


def run_mypy(repo: Path, paths: Sequence[str], scope: str) -> ToolResult:
    if not paths:
        return ToolResult("mypy", scope, 0, (), "", "")
    # Do not reuse a repository-local cache: baseline and head are checked in
    # different worktrees and stale semantic caches can cause MyPy internal
    # errors or make the comparison depend on run order.  Imports remain
    # available so framework base classes preserve their type information.
    # Invoke through THIS interpreter rather than a bare `mypy` on PATH. MyPy
    # has to import the project's dependencies to load its SQLAlchemy and
    # Pydantic plugins, so a `mypy` belonging to some other environment exits 2
    # with "No module named 'sqlalchemy'" and analyses nothing.
    result = run(
        (
            sys.executable,
            "-m",
            "mypy",
            "--no-incremental",
            "--show-error-codes",
            "--no-error-summary",
            *paths,
        ),
        repo,
    )
    # MyPy: 0 = clean, 1 = type errors found, anything else = it did not
    # complete (fatal error, bad configuration, missing plugin, crash).
    execution_error = (
        None
        if result.returncode in (0, 1)
        else (result.stderr.strip() or result.stdout.strip() or f"mypy exited {result.returncode}")
    )
    # Deliberately empty when the run failed: parsing the output of a tool that
    # never completed would turn "we do not know" into "we found nothing".
    diagnostics = (
        limit_to_requested_paths(
            parse_mypy_text(repo, f"{result.stdout}\n{result.stderr}"),
            paths,
        )
        if execution_error is None
        else ()
    )
    return ToolResult(
        "mypy",
        scope,
        result.returncode,
        diagnostics,
        result.stdout,
        result.stderr,
        execution_error,
    )


def existing_python_paths(repo: Path, paths: Iterable[str]) -> list[str]:
    return sorted(
        path
        for path in paths
        if (repo / path).is_file() and path.endswith(".py")
    )


def scope_paths(repo: Path, scopes: Sequence[str]) -> list[str]:
    paths: set[str] = set()
    for scope in scopes:
        candidate = repo / scope
        if candidate.is_file() and candidate.suffix == ".py":
            paths.add(candidate.relative_to(repo).as_posix())
        elif candidate.is_dir():
            paths.update(
                path.relative_to(repo).as_posix()
                for path in candidate.rglob("*.py")
                if path.is_file()
            )
    return sorted(paths)


def execution_blockers(baseline: ToolResult, head: ToolResult) -> list[str]:
    """Report every run that produced no analysis, on either side.

    This used to fire only when the head's execution error *differed* from the
    baseline's, so a tool that failed identically on both sides — the usual case,
    since both sides run in the same environment — reported zero diagnostics and
    the gate printed PASS. A tool that never ran had certified the change.

    Zero diagnostics is only evidence when the tool actually ran. An unmeasured
    baseline is no better: there is nothing to compare the candidate against, so
    non-regression cannot be established either. Both are blockers.
    """
    blockers: list[str] = []
    if not head.measured:
        blockers.append(
            f"{head.tool} [{head.scope}] did not run on the candidate, so it produced no "
            f"analysis and cannot show the change is clean: {head.execution_error}"
        )
    if not baseline.measured:
        blockers.append(
            f"{baseline.tool} [{baseline.scope}] did not run on the baseline, so there is "
            f"nothing to compare against: {baseline.execution_error}"
        )
    return blockers


def compare_counts(
    baseline: Counter[str], head: Counter[str], label: str
) -> list[str]:
    failures: list[str] = []
    for path in sorted(set(baseline) | set(head)):
        before = baseline[path]
        after = head[path]
        if after > before:
            failures.append(f"{label}: {path}: {before} -> {after} (+{after - before})")
    return failures


def result_payload(result: ToolResult) -> dict[str, object]:
    return {
        "tool": result.tool,
        "scope": result.scope,
        "returncode": result.returncode,
        "diagnostic_count": len(result.diagnostics),
        "counts": dict(sorted(result.counts.items())),
        "diagnostics": [asdict(diagnostic) for diagnostic in result.diagnostics],
        "execution_error": result.execution_error,
    }


def checkout_ref(repo: Path, ref: str) -> tuple[tempfile.TemporaryDirectory[str], Path]:
    temp_dir = tempfile.TemporaryDirectory(prefix="quality-gate-base-")
    worktree = Path(temp_dir.name) / "repo"
    result = run(("git", "worktree", "add", "--detach", str(worktree), ref), repo)
    if result.returncode != 0:
        temp_dir.cleanup()
        raise RuntimeError(f"Unable to create baseline worktree:\n{result.stderr.strip()}")
    return temp_dir, worktree


def remove_worktree(repo: Path, worktree: Path, temp_dir: tempfile.TemporaryDirectory[str]) -> None:
    run(("git", "worktree", "remove", "--force", str(worktree)), repo)
    temp_dir.cleanup()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-ref", default=os.getenv("QUALITY_BASE_REF", "origin/main"))
    parser.add_argument("--head-ref", default=os.getenv("QUALITY_HEAD_REF", "HEAD"))
    parser.add_argument("--report", type=Path, default=Path("quality-gate-report.json"))
    parser.add_argument(
        "--critical-scope",
        action="append",
        dest="critical_scopes",
        default=None,
        help="Critical directory or file. May be supplied more than once.",
    )
    parser.add_argument(
        "--require-python-change",
        action="store_true",
        help="Fail when the change contains no Python files.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = Path.cwd().resolve()
    critical_scopes = tuple(args.critical_scopes or DEFAULT_CRITICAL_SCOPES)
    temp_dir: tempfile.TemporaryDirectory[str] | None = None
    baseline_repo: Path | None = None
    report: dict[str, object] = {
        "base_ref": args.base_ref,
        "head_ref": args.head_ref,
        "critical_scopes": list(critical_scopes),
    }
    failures: list[str] = []

    try:
        base = git_ref(repo, args.base_ref)
        head = git_ref(repo, args.head_ref)
        changed = changed_python_files(repo, base, head)
        report["base_sha"] = base
        report["head_sha"] = head
        report["changed_python_files"] = changed
        sys.stdout.write(f"Quality gate baseline: {base}\n")
        sys.stdout.write(f"Quality gate head:     {head}\n")
        sys.stdout.write(f"Changed Python files:  {len(changed)}\n")

        if not changed and args.require_python_change:
            failures.append("No changed Python files were found; Python changes are required for this invocation.")

        temp_dir, baseline_repo = checkout_ref(repo, base)
        baseline_changed = existing_python_paths(baseline_repo, changed)
        head_changed = existing_python_paths(repo, changed)
        baseline_critical = scope_paths(baseline_repo, critical_scopes)
        head_critical = scope_paths(repo, critical_scopes)

        baseline_results = {
            "ruff_changed": run_ruff(baseline_repo, baseline_changed, "changed-files"),
            "mypy_changed": run_mypy(baseline_repo, baseline_changed, "changed-files"),
            "ruff_critical": run_ruff(baseline_repo, baseline_critical, "critical-scope"),
            "mypy_critical": run_mypy(baseline_repo, baseline_critical, "critical-scope"),
        }
        head_results = {
            "ruff_changed": run_ruff(repo, head_changed, "changed-files"),
            "mypy_changed": run_mypy(repo, head_changed, "changed-files"),
            "ruff_critical": run_ruff(repo, head_critical, "critical-scope"),
            "mypy_critical": run_mypy(repo, head_critical, "critical-scope"),
        }

        blockers: list[str] = []
        for name in baseline_results:
            blockers.extend(
                execution_blockers(baseline_results[name], head_results[name]),
            )

        failures.extend(
            compare_counts(
                baseline_results["ruff_changed"].counts,
                head_results["ruff_changed"].counts,
                "Ruff changed-file regression",
            )
        )
        failures.extend(
            compare_counts(
                baseline_results["mypy_changed"].counts,
                head_results["mypy_changed"].counts,
                "MyPy changed-file regression",
            )
        )
        failures.extend(
            compare_counts(
                baseline_results["ruff_critical"].counts,
                head_results["ruff_critical"].counts,
                "Ruff critical-scope regression",
            )
        )
        failures.extend(
            compare_counts(
                baseline_results["mypy_critical"].counts,
                head_results["mypy_critical"].counts,
                "MyPy critical-scope regression",
            )
        )

        report["baseline"] = {key: result_payload(value) for key, value in baseline_results.items()}
        report["head"] = {key: result_payload(value) for key, value in head_results.items()}
        report["failures"] = failures
        report["blockers"] = blockers
        # BLOCKED is its own outcome, distinct from FAIL: nothing is known to be
        # wrong with the change, but nothing is known to be right either.
        if blockers:
            report["status"] = "BLOCKED"
        elif failures:
            report["status"] = "FAIL"
        else:
            report["status"] = "PASS"
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        for section, results in (("baseline", baseline_results), ("head", head_results)):
            for name, result in results.items():
                if result.measured:
                    sys.stdout.write(f"{section}.{name}: {len(result.diagnostics)} diagnostics\n")
                else:
                    # Never print a diagnostic count for a run that did not happen.
                    sys.stdout.write(f"{section}.{name}: DID NOT RUN\n")
        if blockers:
            sys.stdout.write("QUALITY_CHANGED_FILES_GATE: BLOCKED\n")
            for blocker in blockers:
                sys.stdout.write(f"- {blocker}\n")
            for failure in failures:
                sys.stdout.write(f"- {failure}\n")
            return 1
        if failures:
            sys.stdout.write("QUALITY_CHANGED_FILES_GATE: FAIL\n")
            for failure in failures:
                sys.stdout.write(f"- {failure}\n")
            return 1
        sys.stdout.write("QUALITY_CHANGED_FILES_GATE: PASS\n")
        return 0
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        report["status"] = "ERROR"
        report["failures"] = [str(exc)]
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        sys.stderr.write(f"QUALITY_CHANGED_FILES_GATE: ERROR: {exc}\n")
        return 2
    finally:
        if temp_dir is not None and baseline_repo is not None:
            remove_worktree(repo, baseline_repo, temp_dir)


if __name__ == "__main__":
    raise SystemExit(main())

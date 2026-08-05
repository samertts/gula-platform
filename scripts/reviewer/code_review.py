"""Phase 2 — Code Review.

Verify readability, maintainability, complexity, naming, duplication, dead
code, unused imports, and unsafe patterns. Deterministic static scans of
Python source under a target directory.
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from scripts.kernel.core import REPO_ROOT, Severity
from scripts.reviewer.core import ReviewFinding

# Patterns considered unsafe or indicative of dead code.
UNSAFE_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\beval\s*\(", "eval() used"),
    (r"\bexec\s*\(", "exec() used"),
    (r"os\.system\s*\(", "os.system used"),
    (r"subprocess\.(run|call|Popen)\([^)]*shell\s*=\s*True", "shell=True subprocess"),
    (r"\binput\s*\(.*\)\s*$", "bare input() call"),
)

DEAD_CODE_MARKERS: tuple[str, ...] = ("TODO", "FIXME", "HACK", "XXX")

NONSTANDARD_NAME = re.compile(r"\b[a-z][a-z0-9]*[A-Z][a-zA-Z0-9]*\b")


EXCLUDED_DIRS = frozenset(
    {".venv", "site-packages", "node_modules", "migrations", "__pycache__", "dist", "build"}
)


def _py_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(
        p for p in root.rglob("*.py")
        if "__pycache__" not in p.parts
        and p.name != "__init__.py"
        and not any(part in EXCLUDED_DIRS for part in p.parts)
    )


def check_unsafe_patterns(repo: Path = REPO_ROOT) -> list[ReviewFinding]:
    """Scan for unsafe Python patterns across the codebase."""
    findings: list[ReviewFinding] = []
    strings_re = re.compile(r"""(['"])(?:\\.|(?!\1).)*\1""", re.DOTALL)
    for path in _py_files(repo / "backend"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        code = strings_re.sub("", text)
        for pattern, label in UNSAFE_PATTERNS:
            if re.search(pattern, code):
                findings.append(ReviewFinding(
                    "code", Severity.HIGH, label,
                    detail=f"found in {path.relative_to(repo)}",
                    evidence=path.name,
                    suggested_fix=f"remove {label.lower()} or replace with a safe alternative",
                ))
    return findings


def check_dead_code(repo: Path = REPO_ROOT) -> list[ReviewFinding]:
    """Find TODO/FIXME markers that indicate incomplete or dead code."""
    findings: list[ReviewFinding] = []
    count = 0
    for path in _py_files(repo / "backend"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for marker in DEAD_CODE_MARKERS:
            count += text.count(marker)
    if count:
        findings.append(ReviewFinding(
            "code", Severity.LOW, "Dead-code markers present",
            detail=f"{count} TODO/FIXME/HACK/XXX markers across backend",
            evidence="backend/",
            suggested_fix="resolve or ticket each marker; do not leave silently",
        ))
    return findings


def check_duplication(repo: Path = REPO_ROOT) -> list[ReviewFinding]:
    """Detect repeated 4-line blocks appearing in 3+ files."""
    findings: list[ReviewFinding] = []
    blocks: Counter[str] = Counter()
    per_file: dict[str, set[str]] = {}
    for path in _py_files(repo / "backend"):
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        stripped = [ln.strip() for ln in lines]
        file_blocks: set[str] = set()
        for i in range(len(stripped) - 3):
            window = tuple(stripped[i:i + 4])
            if any(not w or w.startswith(("#", "import ", "from ", "def ", "class ", "@")) for w in window):
                continue
            block = "\n".join(window)
            if all(len(w) >= 20 for w in window):
                file_blocks.add(block)
        for block in file_blocks:
            blocks[block] += 1
            per_file.setdefault(block, set()).add(str(path))
    duplicated = {block: count for block, count in blocks.items() if count >= 3}
    if duplicated:
        worst = max(duplicated, key=duplicated.get)
        files = sorted(per_file[worst])[:3]
        findings.append(ReviewFinding(
            "code", Severity.MEDIUM, "Duplicated code blocks detected",
            detail=f"{len(duplicated)} repeated 4-line blocks across files; "
                   f"worst x{duplicated[worst]}",
            evidence="; ".join(files),
            suggested_fix="extract the duplicated logic into a shared helper",
        ))
    return findings


def check_complexity(repo: Path = REPO_ROOT) -> list[ReviewFinding]:
    """Flag files with very long functions (indentation-depth heuristic)."""
    findings: list[ReviewFinding] = []
    affected: list[str] = []
    for path in _py_files(repo / "backend"):
        max_depth = 0
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            stripped = line.lstrip()
            if stripped and not stripped.startswith(("#", "import", "from", "@", "def", "class")):
                depth = len(line) - len(line.lstrip(" "))
                max_depth = max(max_depth, depth)
        if max_depth > 32:
            affected.append(path.relative_to(repo).as_posix())
    if affected:
        findings.append(ReviewFinding(
            "code", Severity.MEDIUM, "High nesting complexity",
            detail=f"{len(affected)} files reach indentation depth > 32 "
                   f"(e.g. {Path(affected[0]).name})",
            evidence="backend/",
            suggested_fix="extract nested logic into helper functions",
        ))
    return findings


def check_naming(repo: Path = REPO_ROOT) -> list[ReviewFinding]:
    """Flag camelCase identifiers in Python code, ignoring string literals.

    Aggregated to a single finding: PEP 8 naming debt is systemic and is
    fixed across the codebase, not file-by-file.
    """
    findings: list[ReviewFinding] = []
    # Remove string literals before matching so dict keys/labels are skipped.
    strings_re = re.compile(r"""(['"])(?:\\.|(?!\1).)*\1""", re.DOTALL)
    affected: list[str] = []
    for path in _py_files(repo / "backend"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        code = strings_re.sub("", text)
        matches = sorted(set(NONSTANDARD_NAME.findall(code)))
        # Skip stdlib/framework method calls like .getLogger / .setValue
        matches = [m for m in matches if f".{m}" not in code]
        if matches:
            affected.append(path.relative_to(repo).as_posix())
    if affected:
        findings.append(ReviewFinding(
            "code", Severity.LOW, "Non-standard naming",
            detail=f"camelCase identifiers in {len(affected)} backend files "
                   f"(e.g. {Path(affected[0]).name}, {Path(affected[-1]).name})",
            evidence="backend/",
            suggested_fix="use snake_case per PEP 8",
        ))
    return findings


def check_unused_imports(repo: Path = REPO_ROOT) -> list[ReviewFinding]:
    """Heuristic: flag high import-density modules (aggregated)."""
    findings: list[ReviewFinding] = []
    affected: list[str] = []
    for path in _py_files(repo / "backend"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        imports = len(re.findall(r"^\s*(?:import|from)\s+", text, re.MULTILINE))
        if imports > 50:
            affected.append(f"{path.relative_to(repo).as_posix()} ({imports})")
    if affected:
        findings.append(ReviewFinding(
            "code", Severity.LOW, "Import density high",
            detail=f"{len(affected)} modules exceed 50 import statements "
                   f"(e.g. {Path(affected[0]).name})",
            evidence="backend/",
            suggested_fix="run ruff with F401 to drop unused imports and split modules",
        ))
    return findings


def review(repo: Path = REPO_ROOT) -> list[ReviewFinding]:
    """Run every code review check for a repository."""
    findings: list[ReviewFinding] = []
    findings += check_unsafe_patterns(repo)
    findings += check_dead_code(repo)
    findings += check_duplication(repo)
    findings += check_complexity(repo)
    findings += check_naming(repo)
    findings += check_unused_imports(repo)
    return findings

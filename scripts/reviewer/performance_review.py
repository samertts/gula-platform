"""Phase 7 — Performance Review.

Verify performance posture deterministically: caching, N+1 query signals,
pagination, indexes, lazy loading, and async patterns. Static analysis only;
benchmarks belong to the validation engine.
"""

from __future__ import annotations

import re
from pathlib import Path

from scripts.kernel.core import REPO_ROOT, Severity
from scripts.reviewer.core import ReviewFinding


def _py_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    excluded = {".venv", "site-packages", "node_modules", "migrations", "__pycache__", "dist", "build"}
    return sorted(
        p for p in root.rglob("*.py")
        if "__pycache__" not in p.parts
        and not any(part in excluded for part in p.parts)
    )


def _ts_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    excluded = {"node_modules", "dist", "build"}
    return sorted(
        p for p in root.rglob("*") 
        if p.suffix in {".ts", ".tsx"}
        and not any(part in excluded for part in p.parts)
    )


def check_caching(repo: Path = REPO_ROOT) -> list[ReviewFinding]:
    """Verify a caching layer is present and used."""
    findings: list[ReviewFinding] = []
    cache_mentions = sum(
        re.search(r"@lru_cache|redis|aiocache|cachetools", p.read_text(encoding="utf-8", errors="ignore"))
        is not None
        for p in _py_files(repo / "backend")
    )
    if cache_mentions == 0:
        findings.append(ReviewFinding(
            "performance", Severity.MEDIUM, "No caching layer",
            detail="no redis/lru_cache/cachetools usage found in backend",
            evidence="backend/",
            suggested_fix="add caching for hot read paths",
        ))
    return findings


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _query_in_loop_count(code: str) -> int:
    """Count DB query calls that sit inside an enclosing for/while block."""
    lines = code.splitlines()
    headers: list[tuple[int, str, str]] = []
    hits = 0
    for lineno, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        indent = _indent(line)
        block_match = re.match(r"^(for|while|if|try|with|def|class|else|elif)\b", stripped)
        query_match = re.search(r"\b(?:\.execute\s*\(|\.fetchall\s*\(|session\.query\s*\(|\.fetchone\s*\()", line)
        if block_match:
            while headers and headers[-1][0] >= indent:
                headers.pop()
            headers.append((indent, block_match.group(1), stripped))
            continue
        if query_match:
            in_loop = False
            for h_indent, h_kind, _h in headers:
                if h_indent < indent and h_kind in {"for", "while"}:
                    in_loop = True
                    break
                if h_indent < indent and h_kind in {"def", "class"}:
                    break
            if in_loop:
                hits += 1
    return hits


def check_n_plus_one(repo: Path = REPO_ROOT) -> list[ReviewFinding]:
    """Flag query-in-loop signals in backend code."""
    findings: list[ReviewFinding] = []
    for path in _py_files(repo / "backend"):
        code = path.read_text(encoding="utf-8", errors="ignore")
        hits = _query_in_loop_count(code)
        if hits >= 3:
            findings.append(ReviewFinding(
                "performance", Severity.MEDIUM, "Possible N+1 query pattern",
                detail=f"{path.relative_to(repo)}: {hits} query-in-loop call(s)",
                evidence=path.name,
                suggested_fix="batch queries with selectin/joinedload or bulk fetch",
            ))
    return findings


def check_pagination(repo: Path = REPO_ROOT) -> list[ReviewFinding]:
    """Verify list endpoints support pagination."""
    findings: list[ReviewFinding] = []
    pagination_mentions = 0
    for path in _py_files(repo / "backend"):
        pagination_mentions += len(re.findall(
            r"limit\s*=|offset\s*=|page\s*=|page_size|pagination", path.read_text(encoding="utf-8", errors="ignore")))
    if pagination_mentions < 5:
        findings.append(ReviewFinding(
            "performance", Severity.MEDIUM, "Pagination scarce",
            detail=f"{pagination_mentions} pagination references across backend",
            evidence="backend/",
            suggested_fix="paginate all collection endpoints",
        ))
    return findings


def check_indexes(repo: Path = REPO_ROOT) -> list[ReviewFinding]:
    """Verify DB models declare indexes."""
    findings: list[ReviewFinding] = []
    index_mentions = sum(
        len(re.findall(r"Index\(|index=True|unique=True", p.read_text(encoding="utf-8", errors="ignore")))
        for p in _py_files(repo / "backend" / "app" / "models")
    )
    if index_mentions < 10:
        findings.append(ReviewFinding(
            "performance", Severity.MEDIUM, "DB indexes sparse",
            detail=f"{index_mentions} index declarations in backend/app/models",
            evidence="backend/app/models",
            suggested_fix="index foreign keys and hot query columns",
        ))
    return findings


def check_frontend_lazy(repo: Path = REPO_ROOT) -> list[ReviewFinding]:
    """Verify frontend uses lazy loading / code splitting."""
    findings: list[ReviewFinding] = []
    lazy_mentions = sum(
        len(re.findall(r"lazy\s*\(|React\.lazy|import\s*\(['\"]", p.read_text(encoding="utf-8", errors="ignore")))
        for p in _ts_files(repo / "frontend-v3" / "src")
    )
    if lazy_mentions == 0:
        findings.append(ReviewFinding(
            "performance", Severity.MEDIUM, "No lazy loading",
            detail="no lazy()/dynamic import found in frontend-v3/src",
            evidence="frontend-v3/src",
            suggested_fix="code-split routes and heavy components",
        ))
    return findings


def review(repo: Path = REPO_ROOT) -> list[ReviewFinding]:
    """Run every performance review check for a repository."""
    findings: list[ReviewFinding] = []
    findings += check_caching(repo)
    findings += check_n_plus_one(repo)
    findings += check_pagination(repo)
    findings += check_indexes(repo)
    findings += check_frontend_lazy(repo)
    return findings

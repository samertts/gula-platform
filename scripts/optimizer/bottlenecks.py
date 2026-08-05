"""Phase 2 — Bottleneck Detection.

Automatically detect performance and scalability bottlenecks: slow APIs,
duplicate queries, N+1 queries, unused/dead code, large bundles, slow
builds, blocking operations, large dependencies, memory leaks, CPU
hotspots, and storage waste. A bottleneck emerges when the same area crosses
a repeat threshold; the Optimizer then elevates it with a severity and a
remediation recommendation. Detection is evidence-driven and deterministic.
"""

from __future__ import annotations

from pathlib import Path

from scripts.kernel.core import utcnow
from scripts.optimizer.core import (
    BOTTLENECK_DIR,
    BOTTLENECK_KINDS,
    Bottleneck,
    read_json,
    write_json,
)

AREA_ALIASES = {
    "api": "api",
    "route": "api",
    "endpoint": "api",
    "service": "api",
    "query": "database",
    "sql": "database",
    "model": "database",
    "migration": "database",
    "frontend": "frontend",
    "typescript": "frontend",
    "react": "frontend",
    "bundle": "frontend",
    "build": "build",
    "webpack": "build",
    "vite": "build",
    "backend": "backend",
    "task": "backend",
    "worker": "backend",
    "cache": "backend",
    "redis": "infrastructure",
    "docker": "infrastructure",
    "container": "infrastructure",
    "storage": "infrastructure",
    "volume": "infrastructure",
    "dependency": "dependencies",
    "package": "dependencies",
    "memory": "memory",
    "cpu": "cpu",
}

# Recommendation template per bottleneck kind.
RECOMMENDATIONS: dict[str, str] = {
    "slow-api": "Profile the hot endpoint, add caching, and benchmark the fix before merging.",
    "duplicate-queries": "Collapse repeated queries into a single prepared statement and reuse the result.",
    "n-plus-one": "Eager-load the related collection with a JOIN or an IN query instead of per-row lookups.",
    "unused-code": "Remove unreachable imports and unused modules after confirming no references remain.",
    "dead-code": "Delete the dead branch and add a regression test guarding the live path.",
    "large-bundle": "Apply code splitting and lazy loading so users download only what they need.",
    "slow-build": "Cache build layers, parallelize stages, and prune the dependency graph.",
    "blocking-operation": "Move the blocking I/O into an async task or worker pool with a bounded queue.",
    "large-dependency": "Replace the heavy dependency with a lighter alternative or a standard-library solution.",
    "memory-leak": "Release references on completion, bound the cache size, and add a memory stress test.",
    "cpu-hotspot": "Profile the hotspot, hoist the inner-loop work, and add a micro-benchmark.",
    "storage-waste": "Enable compression, prune unused volumes, and archive cold data off hot storage.",
}


def detect_bottlenecks(items: list[tuple[str, str]]) -> list[Bottleneck]:
    """Detect bottlenecks from (area, text) evidence pairs."""
    counts: dict[tuple[str, str], list[str]] = {}
    for area, text in items:
        resolved = _resolve_area(area, text)
        if resolved:
            counts.setdefault(resolved, []).append(text)
    bottlenecks: list[Bottleneck] = []
    for (area, kind), evidence in sorted(counts.items()):
        if kind not in BOTTLENECK_KINDS:
            continue
        if len(evidence) < _threshold(kind):
            continue
        bottlenecks.append(Bottleneck(
            bottleneck_id=f"BOT-{len(bottlenecks) + 1:06d}",
            kind=kind,
            area=area,
            severity=_severity(kind, len(evidence)),
            count=len(evidence),
            evidence=sorted(set(evidence))[:5],
            recommendation=RECOMMENDATIONS.get(kind, ""),
        ))
    return bottlenecks


def persist_bottlenecks(bottlenecks: list[Bottleneck]) -> Path:
    BOTTLENECK_DIR.mkdir(parents=True, exist_ok=True)
    path = BOTTLENECK_DIR / "bottlenecks.json"
    payload = {
        "bottlenecks": [b.to_dict() for b in bottlenecks],
        "updated_at": utcnow(),
    }
    write_json(path, payload)
    return path


def load_bottlenecks() -> list[Bottleneck]:
    data = read_json(BOTTLENECK_DIR / "bottlenecks.json")
    return [Bottleneck(**item) for item in data.get("bottlenecks", [])]


def _resolve_area(area: str, text: str) -> tuple[str, str] | None:
    kind = _classify_kind(text)
    if not kind:
        return None
    alias = AREA_ALIASES.get(area.lower(), area.lower())
    return alias, kind


def _classify_kind(text: str) -> str | None:
    lowered = text.lower()
    scoring = {
        "slow-api": ("latency", "slow", "timeout", "ms", "p99", "endpoint"),
        "duplicate-queries": ("duplicate", "repeated", "same query", "twice"),
        "n-plus-one": ("n+1", "n-plus-one", "per-row", "lazy", "for each"),
        "unused-code": ("unused", "unused import", "no references"),
        "dead-code": ("dead", "unreachable", "dead code", "orphan"),
        "large-bundle": ("bundle", "bundle size", "chunk", "js size"),
        "slow-build": ("build", "slow build", "compile", "docker build"),
        "blocking-operation": ("blocking", "sync io", "wait", "sleep", "block"),
        "large-dependency": ("dependency", "package", "node_modules", "heavy"),
        "memory-leak": ("leak", "memory leak", "growth", "retained"),
        "cpu-hotspot": ("hotspot", "cpu", "loop", "hot path"),
        "storage-waste": ("storage", "volume", "disk", "unused space"),
    }
    best: tuple[str, int] | None = None
    for kind, keywords in scoring.items():
        score = sum(1 for keyword in keywords if keyword in lowered)
        if score and (best is None or score > best[1]):
            best = (kind, score)
    return best[0] if best else None


def _threshold(kind: str) -> int:
    return 2


def _severity(kind: str, count: int) -> str:
    if kind in {"memory-leak", "cpu-hotspot", "blocking-operation"}:
        return "critical" if count >= 3 else "high"
    if kind in {"duplicate-queries", "n-plus-one", "slow-api", "large-dependency"}:
        return "high" if count >= 3 else "medium"
    if kind in {"unused-code", "dead-code", "storage-waste"}:
        return "medium"
    return "medium"

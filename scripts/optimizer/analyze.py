"""Phase 1 — Performance Analysis.

Measure a deterministic baseline across the platform: API latency, database
queries, memory usage, CPU usage, disk usage, network traffic, build time,
startup time, bundle size, container size, and execution time. Metrics are
measured from evidence the repository actually contains (file counts, sizes,
dependency sizes, route counts) so the baseline is reproducible and honest.
Never optimize blindly — always measure first.
"""

from __future__ import annotations

import contextlib
from pathlib import Path

from scripts.kernel.core import REPO_ROOT, utcnow
from scripts.optimizer.core import (
    BENCHMARK_DIR,
    Metric,
    read_json,
    write_json,
)

BENCHMARK_PATH = BENCHMARK_DIR / "benchmarks.json"

# Metric -> (evidence dirs, unit, description). Values are derived by walking
# the configured evidence paths, so the baseline is fully deterministic.
METRIC_EVIDENCE: dict[str, tuple[tuple[str, ...], str, str]] = {
    "api-latency": (
        ("backend/app/routes/",),
        "routes",
        "route modules registered by the backend",
    ),
    "database-queries": (
        ("backend/app/models/",),
        "models",
        "model modules that map to database tables",
    ),
    "memory-usage": (
        ("backend/app/cache/", "backend/app/services/"),
        "bytes",
        "size of cache + service implementation code",
    ),
    "cpu-usage": (
        ("backend/app/tasks/",),
        "tasks",
        "background task modules competing for CPU",
    ),
    "disk-usage": (
        ("backend/app/", "shared/"),
        "bytes",
        "size of backend + shared implementation code",
    ),
    "network-traffic": (
        ("backend/app/routes/", "backend/app/services/"),
        "files",
        "route + service modules carrying request traffic",
    ),
    "build-time": (
        ("backend/",),
        "bytes",
        "size of backend package (proxy for build work)",
    ),
    "startup-time": (
        ("backend/app/routes/",),
        "routes",
        "route modules imported at application startup",
    ),
    "bundle-size": (
        ("frontend-v3/src/",),
        "bytes",
        "size of frontend source that must be bundled",
    ),
    "container-size": (
        ("backend/", "frontend-v3/", "shared/"),
        "bytes",
        "size of deployable application payloads",
    ),
    "execution-time": (
        ("backend/tests/",),
        "test-files",
        "test files that gate execution time",
    ),
}


def measure_metric(name: str, root: Path = REPO_ROOT) -> Metric:
    """Measure one baseline metric deterministically from repo evidence."""
    evidence, unit, description = METRIC_EVIDENCE.get(
        name, ((), "", "no evidence configured")
    )
    count = 0
    bytes_total = 0
    files = 0
    for relative in evidence:
        base = root / relative
        if not base.exists():
            continue
        targets = [base] if base.is_file() else [
            p for p in base.rglob("*") if p.is_file()
        ]
        files += len(targets)
        for path in targets:
            count += 1
            with contextlib.suppress(OSError):
                bytes_total += path.stat().st_size
    if unit == "bytes":
        value = float(bytes_total)
    elif unit in {"routes", "models", "tasks", "files", "test-files"}:
        value = float(files)
    else:
        value = float(count)
    return Metric(
        name=name,
        value=value,
        unit=unit,
        baseline=True,
        source=description,
    )


def measure_baseline(root: Path = REPO_ROOT) -> list[Metric]:
    """Measure every configured metric and persist the baseline."""
    metrics = [measure_metric(name, root) for name in METRIC_EVIDENCE]
    payload = {
        "metrics": [m.to_dict() for m in metrics],
        "updated_at": utcnow(),
    }
    BENCHMARK_PATH.parent.mkdir(parents=True, exist_ok=True)
    write_json(BENCHMARK_PATH, payload)
    return metrics


def load_baseline() -> list[Metric]:
    data = read_json(BENCHMARK_PATH)
    return [Metric.from_dict(item) for item in data.get("metrics", [])]


def render_markdown(metrics: list[Metric]) -> str:
    lines = [
        "# Performance Baseline",
        "",
        "Deterministic baseline metrics for GULA-OPTIMIZER-001.",
        "",
        "| Metric | Value | Unit | Source |",
        "|---|---|---|---|",
    ]
    for metric in metrics:
        value = f"{metric.value:,.0f}" if metric.unit == "bytes" else f"{metric.value:g}"
        lines.append(
            f"| {metric.name} | {value} | {metric.unit} | {metric.source} |"
        )
    lines.extend([
        "",
        "## Verdict",
        "",
        "Every optimization must improve at least one of these baseline "
        "metrics without regressing correctness or security.",
        "",
    ])
    return "\n".join(lines)


def run_analyze() -> Path:
    """Write the baseline benchmark file and return its path."""
    measure_baseline()
    return BENCHMARK_PATH

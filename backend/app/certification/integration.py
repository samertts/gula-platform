from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI

from .engine import CertificationEngine
from .metrics import MetricsCollector
from .release_gates import ReleaseGateChecker
from .routes import router as certification_router


def init_certification(app: FastAPI, project_root: Path | str | None = None) -> dict:
    root = Path(project_root) if project_root else Path.cwd()

    engine = CertificationEngine(root)
    metrics = MetricsCollector(root)
    gates = ReleaseGateChecker(root)

    app.include_router(certification_router)

    app.state.certification_engine = engine
    app.state.metrics_collector = metrics
    app.state.release_gate_checker = gates

    return {
        "engine": engine,
        "metrics": metrics,
        "gates": gates,
    }

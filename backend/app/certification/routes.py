from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from ..security.dependencies import require_permission
from .engine import CertificationEngine
from .enums import CertificationDimension, MetricCategory, ReleaseGate
from .metrics import MetricsCollector
from .release_gates import ReleaseGateChecker
from .report import generate_pdf_report

PROJECT_ROOT = Path(__file__).resolve().parents[3]

router = APIRouter(
    prefix="/certification",
    tags=["certification"],
    dependencies=[Depends(require_permission("system:admin"))],
)

engine = CertificationEngine(project_root=str(PROJECT_ROOT))
metrics_collector = MetricsCollector()
gate_checker = ReleaseGateChecker()


def _safe_target(module_path: str | None) -> Path:
    """Resolve a module path and reject any target outside the platform root."""
    if module_path is None:
        return PROJECT_ROOT
    candidate = Path(module_path)
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate
    try:
        candidate = candidate.resolve()
    except (OSError, RuntimeError):
        raise HTTPException(status_code=403, detail="Invalid module path") from None
    if candidate != PROJECT_ROOT and PROJECT_ROOT not in candidate.parents:
        raise HTTPException(status_code=403, detail="Path is outside the platform root")
    return candidate


class ReleaseCheckRequest(BaseModel):
    gates: list[ReleaseGate] | None = Field(default=None, description="Specific gates to check")

    model_config = ConfigDict(use_enum_values=True)


class ReleaseCheckResponse(BaseModel):
    release_readiness: bool
    total_gates: int
    passed: int
    failed: int
    blocking_failures: int
    details: list[dict[str, Any]]


class DimensionCheck(BaseModel):
    name: str
    description: str
    evaluator: str


@router.post("/evaluate/{module_path:path}")
async def evaluate_module(module_path: str | None = None):
    target = _safe_target(module_path)
    report = engine.evaluate_module(str(target))
    return report.to_dict()


@router.get("/level/{module_path:path}")
async def get_certification_level(module_path: str | None = None):
    target = _safe_target(module_path)
    level = engine.get_certification_level(str(target))
    return {
        "module_path": str(target),
        "certification_level": level.value,
    }


@router.get("/report/{module_path:path}")
async def get_report(
    module_path: str | None = None,
    format: str = Query("json", pattern="^(json|markdown|html|pdf)$"),
):
    target = _safe_target(module_path)
    report = engine.evaluate_module(str(target))

    if format == "json":
        return report.to_dict()
    if format == "markdown":
        from fastapi.responses import PlainTextResponse

        return PlainTextResponse(content=report.to_markdown())
    if format == "html":
        from fastapi.responses import HTMLResponse

        return HTMLResponse(content=report.to_html())
    if format == "pdf":
        output_dir = Path(os.environ.get("GULA_TEMP_DIR", tempfile.gettempdir()))
        output = output_dir / f"certification_report_{target.name}.pdf"
        generate_pdf_report(report, output)
        from fastapi.responses import FileResponse

        return FileResponse(str(output), media_type="application/pdf", filename=output.name)
    return None


@router.get("/metrics")
async def get_all_metrics():
    results = metrics_collector.collect_all()
    return {
        "metrics": [
            {
                "name": r.name,
                "value": r.value,
                "category": r.category.value,
                "unit": r.unit,
                "threshold": r.threshold,
                "passed": r.passed,
                "details": r.details,
            }
            for r in results
        ],
    }


@router.get("/metrics/{category}")
async def get_metrics_by_category(category: MetricCategory):
    results = metrics_collector.collect_category(category)
    if not results:
        raise HTTPException(status_code=404, detail=f"No metrics found for category: {category}")
    return {
        "category": category.value,
        "metrics": [
            {
                "name": r.name,
                "value": r.value,
                "unit": r.unit,
                "threshold": r.threshold,
                "passed": r.passed,
                "details": r.details,
            }
            for r in results
        ],
    }


@router.post("/release/check")
async def check_release_gates(request: ReleaseCheckRequest | None = None):
    if request and request.gates:
        results = [gate_checker.check_gate(g) for g in request.gates]
        passed = [r for r in results if r.passed]
        failed = [r for r in results if not r.passed]
        return {
            "release_readiness": len([r for r in failed if r.blocking]) == 0,
            "total_gates": len(results),
            "passed": len(passed),
            "failed": len(failed),
            "details": [
                {
                    "gate": r.gate.value,
                    "name": r.name,
                    "status": r.status,
                    "score": r.score,
                    "blocking": r.blocking,
                    "evidence": r.evidence,
                    "remediations": r.remediations,
                }
                for r in results
            ],
        }
    return gate_checker.validate_release()


@router.post("/release/validate")
async def validate_release():
    validation = gate_checker.validate_release()
    validation["recommendation"] = (
        "RELEASE BLOCKED — blocking gates must pass before deployment"
        if not validation["release_readiness"]
        else "RELEASE READY — all gates passed"
    )
    return validation


@router.get("/dimensions")
async def list_dimensions():
    return {
        "dimensions": [
            {
                "name": dim.value,
                "description": _dimension_description(dim),
            }
            for dim in CertificationDimension
        ],
    }


@router.get("/dimensions/{dimension}/checks")
async def get_dimension_checks(dimension: CertificationDimension):
    evaluator_cls = engine.evaluators.get(dimension)
    if evaluator_cls is None:
        raise HTTPException(status_code=404, detail=f"Unknown dimension: {dimension}")
    evaluator = evaluator_cls(PROJECT_ROOT)
    result = evaluator.evaluate()
    return {
        "dimension": dimension.value,
        "score": result.score,
        "passed": result.passed,
        "evidence": [
            {
                "name": e.name,
                "value": str(e.value) if e.value is not None else None,
                "source": e.source,
                "passed": e.passed,
            }
            for e in result.evidence
        ],
        "remediations": [
            {
                "severity": r.severity,
                "message": r.message,
                "effort": r.effort,
            }
            for r in result.remediations
        ],
    }


def _dimension_description(dim: CertificationDimension) -> str:
    descriptions = {
        CertificationDimension.ARCHITECTURE: "Clean architecture, DDD compliance, layer violations, circular dependencies",
        CertificationDimension.SECURITY: "OWASP ASVS, vulnerability scanning, secret detection, RBAC",
        CertificationDimension.PERFORMANCE: "Response time, throughput, resource efficiency, connection pooling",
        CertificationDimension.ACCESSIBILITY: "WCAG 2.1 AA compliance, RTL support, screen reader, dark mode",
        CertificationDimension.FHIR_COMPLIANCE: "FHIR R4/R5 conformance, search parameters, operations",
        CertificationDimension.OFFLINE: "Sync reliability, conflict resolution, delta sync, offline queue",
        CertificationDimension.RELIABILITY: "Circuit breakers, retry patterns, graceful shutdown, health checks",
        CertificationDimension.MAINTAINABILITY: "Cyclomatic complexity, maintainability index, code duplication",
        CertificationDimension.TEST_COVERAGE: "Line coverage, branch coverage, property-based tests, integration tests",
        CertificationDimension.DOCUMENTATION: "ADR coverage, API docs, README, changelog, docstrings",
        CertificationDimension.CODE_QUALITY: "Linting, type hints, code smells, naming conventions",
        CertificationDimension.API_COMPATIBILITY: "Backward compatibility, versioning, deprecation headers",
        CertificationDimension.DB_INTEGRITY: "Migration policy, referential integrity, indexes, optimistic locking",
    }
    return descriptions.get(dim, "")

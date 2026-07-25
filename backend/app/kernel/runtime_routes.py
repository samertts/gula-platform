from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query

from app.kernel.integration import get_kernel, is_kernel_ready
from app.security.dependencies import get_current_user

router = APIRouter(prefix="/kernel/runtime", tags=["kernel-runtime"])


def _require_kernel():
    if not is_kernel_ready():
        raise HTTPException(status_code=503, detail="Kernel not ready")
    return get_kernel()


def _get_component(name: str):
    kernel = _require_kernel()
    component = kernel.get_component(name)
    if not component:
        raise HTTPException(status_code=404, detail=f"Component not available: {name}")
    return component


@router.get("/health")
async def runtime_health(_user=Depends(get_current_user)):
    kernel = _require_kernel()
    components = [
        "ai_runtime",
        "rules_runtime",
        "policy_runtime",
        "resource_manager",
        "runtime_governor",
        "runtime_observer",
        "reliability_engine",
        "performance_optimizer",
        "digital_twin",
        "runtime_validator",
    ]
    status = {}
    for name in components:
        comp = kernel.get_component(name)
        status[name] = comp is not None
    return {
        "status": "ok" if all(status.values()) else "degraded",
        "components": status,
    }


@router.get("/metrics")
async def runtime_metrics(_user=Depends(get_current_user)):
    kernel = _require_kernel()
    metrics: dict[str, Any] = {}
    ai = kernel.get_component("ai_runtime")
    if ai:
        metrics["ai"] = ai.get_metrics()
    rules = kernel.get_component("rules_runtime")
    if rules:
        metrics["rules"] = rules.get_stats()
    policy = kernel.get_component("policy_runtime")
    if policy:
        metrics["policy"] = policy.get_stats()
    rm = kernel.get_component("resource_manager")
    if rm:
        metrics["resources"] = rm.get_diagnostics()
    governor = kernel.get_component("runtime_governor")
    if governor:
        metrics["governance"] = governor.get_stats()
    observer = kernel.get_component("runtime_observer")
    if observer:
        metrics["observability"] = observer.get_metrics_snapshot()
    reliability = kernel.get_component("reliability_engine")
    if reliability:
        metrics["reliability"] = reliability.get_stats()
    optimizer = kernel.get_component("performance_optimizer")
    if optimizer:
        metrics["performance"] = optimizer.get_stats()
    dt = kernel.get_component("digital_twin")
    if dt:
        metrics["digital_twin"] = dt.get_stats()
    validator = kernel.get_component("runtime_validator")
    if validator:
        metrics["validation"] = validator.get_stats()
    return metrics


@router.get("/digital-twin")
async def runtime_digital_twin(_user=Depends(get_current_user)):
    dt = _get_component("digital_twin")
    return dt.get_snapshot_data()


@router.get("/topology")
async def runtime_topology(_user=Depends(get_current_user)):
    observer = kernel = _require_kernel()
    observer = kernel.get_component("runtime_observer")
    if not observer:
        raise HTTPException(status_code=404, detail="Observer not available")
    return observer.get_topology_snapshot()


@router.get("/resources")
async def runtime_resources(_user=Depends(get_current_user)):
    rm = _get_component("resource_manager")
    return rm.get_diagnostics()


@router.post("/optimize")
async def runtime_optimize(_user=Depends(get_current_user)):
    optimizer = _get_component("performance_optimizer")
    result = optimizer.optimize_all()
    return {"status": "optimization triggered", "result": result}


@router.get("/observability/slow-queries")
async def runtime_slow_queries(
    limit: int = Query(50, ge=1, le=500),
    _user=Depends(get_current_user),
):
    kernel = _require_kernel()
    observer = kernel.get_component("runtime_observer")
    if not observer:
        return {"slow_queries": [], "count": 0}
    queries = observer.get_slow_queries_snapshot(limit=limit)
    return {"slow_queries": queries, "count": len(queries)}


@router.get("/validation/report")
async def runtime_validation_report(
    limit: int = Query(5, ge=1, le=50),
    _user=Depends(get_current_user),
):
    validator = _get_component("runtime_validator")
    history = validator.get_history(limit=limit)
    return {"reports": history, "count": len(history)}


@router.post("/validation/run")
async def runtime_validation_run(
    name: str = Body("manual-validation"),
    _user=Depends(get_current_user),
):
    validator = _get_component("runtime_validator")
    report = validator.validate_all(name=name)
    return {
        "id": report.id,
        "name": report.name,
        "passed": report.passed,
        "failed": report.failed,
        "warnings": report.warnings,
        "total": report.total_checks,
        "healthy": report.is_healthy(),
        "duration_ms": round(report.total_duration_ms, 1),
        "summary": report.summary,
    }


@router.get("/ai/models")
async def runtime_ai_models(_user=Depends(get_current_user)):
    ai = _get_component("ai_runtime")
    models = []
    for model in ai.registry.list_models():
        models.append(
            {
                "name": model.name,
                "version": model.version,
                "provider": model.provider.value,
                "model_id": model.model_id,
                "description": model.description,
                "loaded": ai.is_loaded(model.name),
            },
        )
    return {"models": models, "count": len(models)}


@router.post("/ai/infer")
async def runtime_ai_infer(
    model_name: str = Body(...),
    prompt: str = Body(...),
    operation: str = Body("suggest_interpretation"),
    temperature: float = Body(0.3),
    max_tokens: int = Body(1024),
    entity_type: str = Body(""),
    entity_id: int = Body(None),
    _user=Depends(get_current_user),
):
    ai = _get_component("ai_runtime")
    if not ai.is_loaded(model_name):
        loaded = ai.load_model(model_name)
        if not loaded:
            raise HTTPException(status_code=400, detail=f"Model not available: {model_name}")

    from app.kernel.ai_runtime import InferenceContext

    ctx = InferenceContext(
        model_name=model_name,
        prompt=prompt,
        temperature=temperature,
        max_tokens=max_tokens,
        operation=operation,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    suggestion = ai.infer(ctx)
    if not suggestion:
        raise HTTPException(status_code=500, detail="Inference failed")

    approval = ai._approval_store.submit(suggestion)
    return {
        "suggestion_id": suggestion.id,
        "approval_id": approval.id,
        "operation": suggestion.operation,
        "operation_type": suggestion.operation_type.value,
        "confidence": suggestion.confidence,
        "requires_approval": approval.status.value == "pending",
        "duration_ms": round(ctx.duration_ms, 1),
    }


@router.get("/rules")
async def runtime_rules(_user=Depends(get_current_user)):
    rules_runtime = _get_component("rules_runtime")
    rulesets = []
    for rs in rules_runtime.list_rulesets():
        rulesets.append(
            {
                "id": rs.id,
                "name": rs.name,
                "strategy": rs.strategy,
                "rules_count": rs.count(),
                "effective_rules": len(rs.effective_rules()),
                "enabled": rs.enabled,
            },
        )
    return {"rulesets": rulesets, "count": len(rulesets)}


@router.get("/policies")
async def runtime_policies(_user=Depends(get_current_user)):
    policy = _get_component("policy_runtime")
    stats = policy.get_stats()
    return {"stats": stats}

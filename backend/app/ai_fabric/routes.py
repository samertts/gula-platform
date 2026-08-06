from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from app.ai_fabric.agents.base import AgentContext
from app.ai_fabric.governance import EvaluationDimension, PromptStatus, PromptVersion
from app.ai_fabric.knowledge_graph import TraversalStrategy
from app.ai_fabric.public_health import (
    AlertLevel,
)
from app.ai_fabric.rag import SearchMode
from app.ai_fabric.sdk import UnifiedAISDK
from app.security.dependencies import get_current_user

logger = logging.getLogger("gula.ai_fabric.routes")

router = APIRouter(
    prefix="/ai/fabric",
    tags=["AI Fabric"],
    dependencies=[Depends(get_current_user)],
)
sdk = UnifiedAISDK()


@router.get("/health")
async def fabric_health():
    return {"status": "ok", "version": "2.1.0", "components": sdk.get_health()}


@router.post("/chat")
async def fabric_chat(
    prompt: str = Query(..., min_length=1), model: str = "gpt-4o-mini", temperature: float = 0.3,
):
    text = await sdk.chat(prompt, model=model, temperature=temperature)
    return {"response": text, "model": model}


@router.post("/embed")
async def fabric_embed(texts: list[str]):
    embeddings = await sdk.embed(texts)
    return {"embeddings": embeddings, "dimension": len(embeddings[0]) if embeddings else 0}


@router.get("/gateway/providers")
async def list_providers():
    return {
        "providers": [
            {"name": p.name.value, "models": p.models} for p in sdk.gateway.router.list_available()
        ],
    }


@router.get("/gateway/cost")
async def gateway_cost():
    return {
        "total_spent": sdk.gateway.cost_optimizer.total_spent,
        "avg_cost": sdk.gateway.cost_optimizer.average_cost,
    }


@router.get("/local-ai/status")
async def local_ai_status():
    return sdk.local_ai.get_status()


@router.post("/rag/query")
async def rag_query(
    query: str = Query(..., min_length=1),
    collection: str = "default",
    top_k: int = 10,
    search_mode: str = "hybrid",
):
    mode = (
        SearchMode(search_mode)
        if search_mode in ("semantic", "keyword", "hybrid")
        else SearchMode.HYBRID
    )
    return await sdk.rag.query(query, collection=collection, top_k=top_k, search_mode=mode)


@router.post("/rag/index")
async def rag_index(collection: str, texts: list[str], sources: list[str] | None = None):
    from app.ai_fabric.rag import Chunk

    chunks = [
        Chunk(text=text, source=sources[i] if sources and i < len(sources) else "")
        for i, text in enumerate(texts)
    ]
    count = await sdk.rag.index_documents(collection, chunks)
    return {"indexed": count, "collection": collection}


@router.get("/knowledge-graph/entity")
async def kg_entity(qualified_name: str):
    entity = await sdk.knowledge_graph.query.find_entity(qualified_name)
    if not entity:
        raise HTTPException(404, "Entity not found")
    return entity


@router.get("/knowledge-graph/related")
async def kg_related(qualified_name: str, max_depth: int = 2):
    return await sdk.knowledge_graph.query.find_related(qualified_name, max_depth=max_depth)


@router.get("/knowledge-graph/search")
async def kg_search(query: str):
    return await sdk.knowledge_graph.query.search_entities(query)


@router.get("/knowledge-graph/statistics")
async def kg_statistics():
    return await sdk.knowledge_graph.get_statistics()


@router.get("/knowledge-graph/traverse")
async def kg_traverse(start: str, strategy: str = "bfs", max_depth: int = 3):
    strat = (
        TraversalStrategy(strategy)
        if strategy in ("bfs", "dfs", "shortest_path")
        else TraversalStrategy.BFS
    )
    return await sdk.knowledge_graph.traverse(start, strategy=strat, max_depth=max_depth)


@router.post("/clinical/analyze")
async def clinical_analyze(results: list[dict[str, Any]]):
    recommendations = await sdk.clinical.analyze_results(results)
    return {
        "recommendations": [
            {
                "type": r.type,
                "severity": r.severity,
                "title": r.title,
                "description": r.description,
                "action": r.action,
            }
            for r in recommendations
        ],
    }


@router.post("/clinical/summarize")
async def clinical_summarize(patient_id: str, results: list[dict[str, Any]]):
    summary = await sdk.summarizer.summarize_results(patient_id, results)
    return {"summary": summary.summary, "model": summary.model, "patient_id": patient_id}


@router.post("/clinical/drug-interaction")
async def drug_interaction(medications: list[dict[str, Any]]):
    interactions = sdk.drug_interaction.check_prescription(medications)
    return {
        "interactions": [
            {
                "drug_a": i.drug_a,
                "drug_b": i.drug_b,
                "severity": i.severity,
                "description": i.description,
            }
            for i in interactions
        ],
    }


@router.post("/lab/delta-check")
async def lab_delta_check(patient_results: list[dict[str, Any]]):
    results = sdk.delta_checker.batch_check(patient_results)
    return {
        "results": [
            {
                "test": r.test_name,
                "delta_pct": r.delta_pct,
                "significant": r.significant,
                "flag": r.flag,
            }
            for r in results
        ],
    }


@router.post("/lab/critical-detector")
async def lab_critical_detector(results: list[dict[str, Any]]):
    criticals = sdk.critical_detector.batch_detect(results)
    return {
        "criticals": [
            {
                "test": c.test_name,
                "value": c.value,
                "direction": c.direction,
                "severity": c.severity,
            }
            for c in criticals
        ],
    }


@router.post("/lab/qc-analyze")
async def lab_qc_analyze(control_values: list[float], mean: float, sd: float):
    metric = sdk.qc_analyzer.analyze(control_values, mean, sd)
    return {
        "in_control": metric.in_control,
        "cv_pct": metric.cv_pct,
        "rules_violated": metric.rules_violated,
    }


@router.post("/lab/workload-predict")
async def lab_workload_predict(order_type: str = "routine", backlog: int = 0):
    return sdk.workload_predictor.predict_tat(order_type, current_backlog=backlog)


@router.post("/public-health/surveillance")
async def ph_surveillance(disease: str, location: str, case_count: int):
    signal = sdk.surveillance.analyze(disease, location, case_count)
    return {
        "alert_level": signal.alert_level.value,
        "z_score": signal.z_score,
        "recommendation": signal.recommendation,
    }


@router.get("/public-health/alerts")
async def ph_alerts(min_level: str = "warning"):
    level = (
        AlertLevel(min_level)
        if min_level in ("information", "surveillance", "warning", "outbreak", "critical")
        else AlertLevel.WARNING
    )
    signals = sdk.surveillance.get_recent_alerts(level)
    return {
        "signals": [
            {"disease": s.disease, "location": s.location, "alert_level": s.alert_level.value}
            for s in signals
        ],
    }


@router.post("/public-health/outbreak-detect")
async def ph_outbreak_detect(disease: str, region: str, cases: list[dict[str, Any]]):
    alert = sdk.outbreak.detect_cluster(disease, region, cases)
    return alert or {"detected": False}


@router.post("/governance/prompt/register")
async def gov_prompt_register(name: str, content: str, version: str = "1.0.0", author: str = ""):
    prompt = PromptVersion(name=name, content=content, version=version, author=author)
    sdk.governance.prompt_registry.register(prompt)
    return {"id": prompt.id, "name": name, "version": version}


@router.get("/governance/prompt/{name}")
async def gov_prompt_get(name: str, version: str | None = None):
    prompt = sdk.governance.prompt_registry.get(name, version)
    if not prompt:
        raise HTTPException(404, f"Prompt {name} v{version or 'latest'} not found")
    return {
        "name": prompt.name,
        "version": prompt.version,
        "content": prompt.content,
        "status": prompt.status.value,
    }


@router.post("/governance/promote")
async def gov_prompt_promote(name: str, version: str, status: str):
    target = (
        PromptStatus(status)
        if status in ("draft", "review", "approved", "active", "deprecated", "retired")
        else PromptStatus.ACTIVE
    )
    prompt = sdk.governance.prompt_registry.promote(name, version, target)
    if not prompt:
        raise HTTPException(404, f"Prompt {name} v{version} not found")
    return {"name": name, "version": version, "status": target.value}


@router.post("/governance/model/submit")
async def gov_model_submit(model_name: str, version: str, submitted_by: str):
    return sdk.governance.model_approval.submit(model_name, version, submitted_by)


@router.post("/governance/model/approve")
async def gov_model_approve(model_name: str, version: str, reviewer: str):
    record = sdk.governance.model_approval.approve(model_name, version, reviewer)
    if not record:
        raise HTTPException(404, "Model approval record not found")
    return record


@router.post("/governance/evaluate")
async def gov_evaluate(model: str, version: str, dimension: str, score: float):
    dim = (
        EvaluationDimension(dimension)
        if dimension
        in ("accuracy", "bias", "safety", "hallucination", "toxicity", "fairness", "robustness")
        else EvaluationDimension.ACCURACY
    )
    result = sdk.governance.evaluation_framework.evaluate(model, version, dim, score)
    return {"model": model, "dimension": dim.value, "score": result.score, "passed": result.passed}


@router.get("/governance/constitution")
async def gov_constitution(severity: str | None = None):
    return {"articles": sdk.governance.constitution.list_articles(severity)}


@router.get("/observability/statistics")
async def obs_statistics(window_hours: float = 24.0):
    return sdk.observer.get_statistics(window_hours)


@router.get("/observability/errors")
async def obs_errors(limit: int = 50):
    return {"errors": sdk.observer.get_recent_errors(limit)}


@router.get("/observability/daily-usage")
async def obs_daily_usage(days: int = 30):
    return {"daily": sdk.observer.get_daily_usage(days)}


@router.get("/observability/model/{model}")
async def obs_model_performance(model: str):
    return sdk.observer.get_model_performance(model)


@router.post("/security/inspect-input")
async def sec_inspect_input(text: str):
    return sdk.firewall.inspect_input(text)


@router.post("/security/inspect-output")
async def sec_inspect_output(text: str):
    return sdk.firewall.inspect_output(text)


@router.post("/security/redact")
async def sec_redact(text: str):
    result = sdk.firewall.pii.redact(text)
    return {
        "redacted": result.redacted_text,
        "pii_types": result.pii_types_found,
        "count": result.count,
    }


@router.get("/agents")
async def list_agents():
    return {"agents": sdk.agent_registry.list_agents()}


@router.get("/agents/statistics")
async def agent_statistics():
    return sdk.agent_registry.get_statistics()


@router.post("/agents/run")
async def run_agent(
    agent_name: str, action: str, user_id: str = "", lab_id: str = "", **kwargs: Any,
):
    context = AgentContext(user_id=user_id, lab_id=lab_id)
    return (
        sdk.agent_registry.get_by_name(agent_name).run(context, kwargs | {"action": action})
        if sdk.agent_registry.get_by_name(agent_name)
        else {"error": f"Agent {agent_name} not found"}
    )


@router.post("/agents/initialize-all")
async def initialize_agents():
    count = sdk.agent_registry.initialize_all()
    return {"initialized": count}


@router.get("/gateway/providers/available")
async def available_providers():
    return {
        "providers": [
            {"name": p.name.value, "base_url": p.base_url, "models": p.models}
            for p in sdk.gateway.router.list_available()
        ],
    }

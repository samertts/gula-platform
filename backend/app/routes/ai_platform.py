"""
AI Platform Routes — GULA Platform
====================================
Enterprise AI platform endpoints for vector search, RAG, knowledge graph,
agent execution, orchestration, governance, healthcare CDS, and observability.

All routes integrate with the existing guardrails layer.
No route mutates clinical state directly — AI is always an assistant.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.ai.agent_runtime import AgentContext, agent_runtime, list_tools
from app.ai.approval import approval_store
from app.ai.embeddings import embedding_model_info
from app.ai.governance import evaluator, model_registry, prompt_manager
from app.ai.healthcare_cds import cds
from app.ai.knowledge_graph import knowledge_graph
from app.ai.memory import memory_store
from app.ai.observability import get_metrics, track_request
from app.ai.orchestrator import orchestrator
from app.ai.rag_pipeline import rag
from app.ai.security import sanitize_response, scan_input
from app.ai.vector_store import vector_store
from app.database import get_db
from app.security.dependencies import get_current_user

logger = logging.getLogger("gula.ai.platform")

router = APIRouter(prefix="/api/ai/v2", tags=["AI Platform"])

_DOCTOR_ROLES = {"doctor", "admin", "lab_admin", "province_admin", "ministry_admin", "master_admin"}


def _require_doctor(user) -> None:
    if user.role not in _DOCTOR_ROLES:
        raise HTTPException(status_code=403, detail="Only doctors and administrators may access this.")


# ─── Schemas ──────────────────────────────────────────────────────────────────


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    content_type: str | None = None
    limit: int = Field(default=10, ge=1, le=100)
    threshold: float = Field(default=0.0, ge=0.0, le=1.0)


class IndexRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=50000)
    content_type: str = Field(..., min_length=1, max_length=64)
    content_id: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RAGQueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    content_type: str | None = None
    max_docs: int = Field(default=5, ge=1, le=20)


class AgentRequest(BaseModel):
    task: str = Field(..., min_length=1, max_length=2000)
    session_id: str | None = None


class SessionMessageRequest(BaseModel):
    session_id: str
    message: str = Field(..., min_length=1, max_length=2000)


class OrchestrateRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    session_id: str | None = None


class CDSEvaluateRequest(BaseModel):
    test_name: str
    value: float
    unit: str = ""
    normal_low: float | None = None
    normal_high: float | None = None
    patient_age: int | None = None
    patient_gender: str | None = None


class CDSEvaluateOrderRequest(BaseModel):
    results: list[dict[str, Any]]
    patient_age: int | None = None
    patient_gender: str | None = None


class KGSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    node_type: str | None = None
    limit: int = Field(default=20, ge=1, le=100)


# ─── Vector Search Routes ────────────────────────────────────────────────────


@router.post("/search", summary="Semantic vector search")
async def semantic_search(
    body: SearchRequest,
    current_user=Depends(get_current_user),
):
    start = time.monotonic()
    results = await vector_store.search(
        query=body.query,
        content_type=body.content_type,
        limit=body.limit,
        threshold=body.threshold,
        lab_id=current_user.lab_id,
    )
    track_request("vector_search", "vector_store")
    return {
        "count": len(results),
        "results": [
            {"id": r.id, "content_type": r.content_type, "text": r.text[:200], "score": r.score, "metadata": r.metadata}
            for r in results
        ],
        "duration_ms": round((time.monotonic() - start) * 1000, 1),
    }


@router.post("/index", summary="Index content for vector search")
async def index_content(
    body: IndexRequest,
    current_user=Depends(get_current_user),
):
    result = await vector_store.index_text(
        text=body.text,
        content_type=body.content_type,
        content_id=body.content_id,
        metadata=body.metadata,
        lab_id=current_user.lab_id,
    )
    track_request("index", "vector_store")
    return result


@router.get("/embedding-info", summary="Embedding model configuration")
def get_embedding_info():
    return embedding_model_info()


# ─── RAG Routes ──────────────────────────────────────────────────────────────


@router.post("/rag/query", summary="Retrieval Augmented Generation query")
async def rag_query(
    body: RAGQueryRequest,
    current_user=Depends(get_current_user),
):
    start = time.monotonic()
    result = await rag.query(
        question=body.question,
        content_type=body.content_type,
        lab_id=current_user.lab_id,
        max_docs=body.max_docs,
    )
    track_request("rag_query", "rag_pipeline")
    return {
        **result,
        "duration_ms": round((time.monotonic() - start) * 1000, 1),
    }


# ─── Knowledge Graph Routes ──────────────────────────────────────────────────


@router.get("/knowledge-graph/info", summary="Knowledge graph statistics")
def kg_info():
    knowledge_graph.initialize()
    return {
        "node_count": len(knowledge_graph.nodes),
        "edge_count": len(knowledge_graph.edges),
        "node_types": list({n.node_type for n in knowledge_graph.nodes.values()}),
        "relationship_types": list({e.relationship for e in knowledge_graph.edges}),
    }


@router.post("/knowledge-graph/search", summary="Search knowledge graph")
def kg_search(body: KGSearchRequest):
    knowledge_graph.initialize()
    nodes = knowledge_graph.search_nodes(query=body.query, node_type=body.node_type, limit=body.limit)
    return {
        "count": len(nodes),
        "results": [
            {"id": n.id, "type": n.node_type, "label": n.label, "description": n.description, "aliases": n.aliases, "external_id": n.external_id}
            for n in nodes
        ],
    }


@router.get("/knowledge-graph/node/{node_id}", summary="Get knowledge graph node details")
def kg_node(node_id: int):
    knowledge_graph.initialize()
    node = knowledge_graph.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    neighbors = knowledge_graph.get_neighbors(node_id)
    return {
        "node": {"id": node.id, "type": node.node_type, "label": node.label, "description": node.description, "aliases": node.aliases, "external_id": node.external_id},
        "neighbors": [{"id": n.id, "label": n.label, "type": n.node_type, "relationship": rel, "weight": w} for n, rel, w in neighbors],
    }


@router.get("/knowledge-graph/path", summary="Shortest path between two nodes")
def kg_path(source: int = Query(...), target: int = Query(...)):
    knowledge_graph.initialize()
    path = knowledge_graph.shortest_path(source, target)
    if path is None:
        raise HTTPException(status_code=404, detail="No path found")
    return {"path": [{"id": n.id, "type": n.node_type, "label": n.label} for n in path]}


# ─── Agent Routes ────────────────────────────────────────────────────────────


@router.get("/agents/tools", summary="List available agent tools")
def list_agent_tools():
    return {"tools": list_tools()}


@router.post("/agents/execute", summary="Execute an agent task")
async def execute_agent(
    body: AgentRequest,
    current_user=Depends(get_current_user),
):
    _require_doctor(current_user)
    start = time.monotonic()
    results = await agent_runtime.run_session(
        session_id=body.session_id or f"agent-{time.time()}",
        task=body.task,
        lab_id=current_user.lab_id,
        user_id=current_user.id,
    )
    track_request("agent_execute", "agent_runtime")
    return {
        "results": [
            {
                "agent": r.agent_name,
                "success": r.success,
                "output": r.output,
                "duration_ms": round(r.duration_ms, 1),
                "error": r.error or None,
                "requires_approval": r.requires_approval,
            }
            for r in results
        ],
        "total_duration_ms": round((time.monotonic() - start) * 1000, 1),
    }


# ─── Orchestrator Routes ─────────────────────────────────────────────────────


@router.post("/orchestrate", summary="Route query to appropriate AI subsystem")
async def orchestrate_query(
    body: OrchestrateRequest,
    current_user=Depends(get_current_user),
):
    start = time.monotonic()
    result = await orchestrator.process_query(
        query=body.query,
        lab_id=current_user.lab_id,
        user_id=current_user.id,
        session_id=body.session_id,
    )
    track_request("orchestrate", "orchestrator")
    return {**result, "duration_ms": round((time.monotonic() - start) * 1000, 1)}


@router.get("/orchestrate/tasks", summary="List orchestration tasks")
def list_tasks(status: str | None = None, limit: int = 20):
    return {"tasks": orchestrator.list_tasks(status=status, limit=limit)}


# ─── Memory Routes ───────────────────────────────────────────────────────────


@router.post("/sessions", summary="Create a new conversation session")
async def create_session(current_user=Depends(get_current_user)):
    conv = await memory_store.create_session(
        lab_id=current_user.lab_id,
        user_id=current_user.id,
    )
    return {"session_id": conv.session_id, "created_at": conv.messages[0].created_at if conv.messages else None}


@router.post("/sessions/message", summary="Add message to session")
async def add_message(
    body: SessionMessageRequest,
    current_user=Depends(get_current_user),
):
    msg = await memory_store.add_message(body.session_id, "user", body.message)
    return {"role": msg.role, "content_length": len(msg.content), "created_at": msg.created_at}


@router.get("/sessions/{session_id}", summary="Get session history")
async def get_session(
    session_id: str,
    current_user=Depends(get_current_user),
):
    conv = await memory_store.get_session(session_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session_id": conv.session_id,
        "message_count": len(conv.messages),
        "messages": [{"role": m.role, "content": m.content[:500], "created_at": m.created_at} for m in conv.messages[-50:]],
    }


# ─── Healthcare CDS Routes ────────────────────────────────────────────────


@router.post("/cds/evaluate", summary="Evaluate a single lab result")
async def evaluate_result(
    body: CDSEvaluateRequest,
    current_user=Depends(get_current_user),
):
    _require_doctor(current_user)
    result = await cds.generate_clinical_guidance(
        test_name=body.test_name,
        value=body.value,
        unit=body.unit,
        normal_low=body.normal_low,
        normal_high=body.normal_high,
    )
    return result


@router.post("/cds/evaluate-order", summary="Evaluate an entire order's results")
async def evaluate_order(
    body: CDSEvaluateOrderRequest,
    current_user=Depends(get_current_user),
):
    _require_doctor(current_user)
    result = await cds.evaluate_order(
        results=body.results,
        patient_age=body.patient_age,
        patient_gender=body.patient_gender,
    )
    return result


# ─── Governance Routes ────────────────────────────────────────────────────


@router.get("/governance/models", summary="List AI models in registry")
def list_models(model_type: str | None = None):
    return {"models": model_registry.list_models(model_type=model_type)}


@router.get("/governance/prompts", summary="List managed prompts")
def list_prompts():
    return {"prompts": prompt_manager.list_prompts()}


@router.get("/governance/evaluations", summary="Evaluation statistics")
def get_evaluation_stats():
    return evaluator.get_stats()


# ─── Security Routes ──────────────────────────────────────────────────────


@router.post("/security/scan", summary="Scan input for PII and prompt injection")
async def scan_security(
    text: str,
    current_user=Depends(get_current_user),
):
    result = await scan_input(text)
    return {
        "is_safe": result.is_safe,
        "safety_score": result.safety_score,
        "injection_score": result.injection_score,
        "pii_found": result.pii_found,
        "issues": result.issues,
    }


# ─── Observability Routes ────────────────────────────────────────────────


@router.get("/metrics", summary="AI platform metrics")
def get_ai_metrics():
    return get_metrics()


@router.get("/metrics/prometheus", summary="Prometheus-formatted metrics")
def get_prometheus_metrics():
    from app.ai.observability import format_for_prometheus

    from fastapi.responses import PlainTextResponse

    return PlainTextResponse(format_for_prometheus())

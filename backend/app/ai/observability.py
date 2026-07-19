from __future__ import annotations

import logging
import time
from typing import Any

logger = logging.getLogger("gula.ai.observability")

_metrics: dict[str, Any] = {
    "requests_total": 0,
    "requests_by_intent": {},
    "requests_by_model": {},
    "requests_by_status": {},
    "latency_sum_ms": 0.0,
    "latency_count": 0,
    "tokens_total": 0,
    "tokens_input": 0,
    "tokens_output": 0,
    "cost_total_usd": 0.0,
    "errors_total": 0,
    "errors_by_type": {},
    "guardrail_violations": 0,
    "approvals_total": 0,
    "approvals_approved": 0,
    "approvals_rejected": 0,
    "awaiting_approval": 0,
    "rag_queries": 0,
    "vector_searches": 0,
    "agent_executions": 0,
    "orchestrator_tasks": 0,
    "embeddings_created": 0,
    "eval_scores": [],
}


def track_request(intent: str, model: str, status: str = "success") -> None:
    _metrics["requests_total"] += 1
    _metrics["requests_by_intent"][intent] = _metrics["requests_by_intent"].get(intent, 0) + 1
    _metrics["requests_by_model"][model] = _metrics["requests_by_model"].get(model, 0) + 1
    _metrics["requests_by_status"][status] = _metrics["requests_by_status"].get(status, 0) + 1
    if status == "error":
        _metrics["errors_total"] += 1


def track_latency(duration_ms: float) -> None:
    _metrics["latency_sum_ms"] += duration_ms
    _metrics["latency_count"] += 1


def track_tokens(input_tokens: int, output_tokens: int, cost_usd: float = 0.0) -> None:
    _metrics["tokens_input"] += input_tokens
    _metrics["tokens_output"] += output_tokens
    _metrics["tokens_total"] += input_tokens + output_tokens
    _metrics["cost_total_usd"] += cost_usd


def track_guardrail_violation() -> None:
    _metrics["guardrail_violations"] += 1


def track_approval(status: str) -> None:
    _metrics["approvals_total"] += 1
    if status == "approved":
        _metrics["approvals_approved"] += 1
    elif status == "rejected":
        _metrics["approvals_rejected"] += 1


def track_rag() -> None:
    _metrics["rag_queries"] += 1


def track_vector_search() -> None:
    _metrics["vector_searches"] += 1


def track_agent() -> None:
    _metrics["agent_executions"] += 1


def track_orchestrator() -> None:
    _metrics["orchestrator_tasks"] += 1


def track_embedding() -> None:
    _metrics["embeddings_created"] += 1


def track_eval(score: float) -> None:
    _metrics["eval_scores"].append(score)
    _metrics["eval_scores"] = _metrics["eval_scores"][-1000:]


def track_error(error_type: str) -> None:
    _metrics["errors_by_type"][error_type] = _metrics["errors_by_type"].get(error_type, 0) + 1


def get_metrics() -> dict[str, Any]:
    avg_latency = 0.0
    if _metrics["latency_count"] > 0:
        avg_latency = round(_metrics["latency_sum_ms"] / _metrics["latency_count"], 1)

    avg_eval = 0.0
    if _metrics["eval_scores"]:
        avg_eval = round(sum(_metrics["eval_scores"]) / len(_metrics["eval_scores"]), 2)

    return {
        "requests": {
            "total": _metrics["requests_total"],
            "by_intent": dict(_metrics["requests_by_intent"]),
            "by_model": dict(_metrics["requests_by_model"]),
            "by_status": dict(_metrics["requests_by_status"]),
        },
        "latency_ms": {
            "avg": avg_latency,
            "samples": _metrics["latency_count"],
        },
        "tokens": {
            "total": _metrics["tokens_total"],
            "input": _metrics["tokens_input"],
            "output": _metrics["tokens_output"],
        },
        "cost_usd": round(_metrics["cost_total_usd"], 6),
        "errors": {
            "total": _metrics["errors_total"],
            "by_type": dict(_metrics["errors_by_type"]),
        },
        "guardrails": {
            "violations": _metrics["guardrail_violations"],
        },
        "approvals": {
            "total": _metrics["approvals_total"],
            "approved": _metrics["approvals_approved"],
            "rejected": _metrics["approvals_rejected"],
        },
        "rag": {
            "queries": _metrics["rag_queries"],
        },
        "vector_search": {
            "total": _metrics["vector_searches"],
        },
        "agent": {
            "executions": _metrics["agent_executions"],
        },
        "orchestrator": {
            "tasks": _metrics["orchestrator_tasks"],
        },
        "embeddings": {
            "created": _metrics["embeddings_created"],
        },
        "evaluation": {
            "avg_score": avg_eval,
            "samples": len(_metrics["eval_scores"]),
        },
    }


def reset_metrics() -> None:
    _metrics["requests_total"] = 0
    _metrics["requests_by_intent"] = {}
    _metrics["requests_by_model"] = {}
    _metrics["requests_by_status"] = {}
    _metrics["latency_sum_ms"] = 0.0
    _metrics["latency_count"] = 0
    _metrics["tokens_total"] = 0
    _metrics["tokens_input"] = 0
    _metrics["tokens_output"] = 0
    _metrics["cost_total_usd"] = 0.0
    _metrics["errors_total"] = 0
    _metrics["errors_by_type"] = {}
    _metrics["guardrail_violations"] = 0
    _metrics["approvals_total"] = 0
    _metrics["approvals_approved"] = 0
    _metrics["approvals_rejected"] = 0
    _metrics["rag_queries"] = 0
    _metrics["vector_searches"] = 0
    _metrics["agent_executions"] = 0
    _metrics["orchestrator_tasks"] = 0
    _metrics["embeddings_created"] = 0
    _metrics["eval_scores"] = []


def format_for_prometheus(prefix: str = "gula_ai") -> str:
    data = get_metrics()
    lines = []
    lines.append(f"# HELP {prefix}_requests_total Total AI requests processed")
    lines.append(f"# TYPE {prefix}_requests_total counter")
    lines.append(f"{prefix}_requests_total {data['requests']['total']}")
    lines.append(f"\n# HELP {prefix}_errors_total Total AI errors")
    lines.append(f"# TYPE {prefix}_errors_total counter")
    lines.append(f"{prefix}_errors_total {data['errors']['total']}")
    lines.append(f"\n# HELP {prefix}_latency_avg_ms Average request latency in ms")
    lines.append(f"# TYPE {prefix}_latency_avg_ms gauge")
    lines.append(f"{prefix}_latency_avg_ms {data['latency_ms']['avg']}")
    lines.append(f"\n# HELP {prefix}_tokens_total Total tokens processed")
    lines.append(f"# TYPE {prefix}_tokens_total counter")
    lines.append(f"{prefix}_tokens_total {data['tokens']['total']}")
    lines.append(f"\n# HELP {prefix}_approvals_pending Pending approvals")
    lines.append(f"# TYPE {prefix}_approvals_pending gauge")
    lines.append(f"{prefix}_approvals_pending {data['approvals']['total'] - data['approvals']['approved'] - data['approvals']['rejected']}")
    lines.append(f"\n# HELP {prefix}_cost_total_usd Total cost in USD")
    lines.append(f"# TYPE {prefix}_cost_total_usd gauge")
    lines.append(f"{prefix}_cost_total_usd {data['cost_usd']}")
    lines.append(f"\n# HELP {prefix}_eval_avg_score Average evaluation score")
    lines.append(f"# TYPE {prefix}_eval_avg_score gauge")
    lines.append(f"{prefix}_eval_avg_score {data['evaluation']['avg_score']}")
    return "\n".join(lines)

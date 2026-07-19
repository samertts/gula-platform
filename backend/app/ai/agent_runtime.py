from __future__ import annotations

import asyncio
import json
import logging
import time
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import text

from app.ai.approval import ApprovalStore, PendingApproval
from app.ai.guardrails import ai_suggest
from app.ai.memory import memory_store
from app.ai.sandbox import SandboxResult
from app.database import get_db

logger = logging.getLogger("gula.ai.agent")

AgentToolFn = Callable[..., Coroutine[Any, Any, dict[str, Any]]]


@dataclass
class AgentContext:
    session_id: str
    lab_id: int | None = None
    user_id: int | None = None
    task: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    variables: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult:
    agent_name: str
    success: bool
    output: Any
    duration_ms: float
    error: str = ""
    requires_approval: bool = False
    approval: PendingApproval | None = None
    sandbox_result: SandboxResult | None = None


class AgentTool:
    def __init__(self, name: str, description: str, fn: AgentToolFn, requires_approval: bool = False):
        self.name = name
        self.description = description
        self.fn = fn
        self.requires_approval = requires_approval


_tool_registry: dict[str, AgentTool] = {}


def register_tool(name: str, description: str, requires_approval: bool = False):
    def decorator(fn: AgentToolFn):
        _tool_registry[name] = AgentTool(name, description, fn, requires_approval)
        return fn
    return decorator


@register_tool("lookup_patient", "Find a patient by name, phone, or ID. Returns patient demographics and recent orders.", requires_approval=False)
async def _lookup_patient(query: str, lab_id: int | None = None, **kwargs) -> dict[str, Any]:
    db = next(get_db())
    try:
        row = db.execute(
            text("SELECT id, name, phone, gender, birth_date FROM patients WHERE (name ILIKE :q OR phone = :q_exact OR cast(id as text) = :q_exact) AND (lab_id = :lab OR :lab IS NULL) LIMIT 1"),
            {"q": f"%{query}%", "q_exact": query, "lab": lab_id},
        ).fetchone()
        if not row:
            return {"found": False, "message": f"No patient found matching '{query}'"}
        return {"found": True, "patient": {"id": row.id, "name": row.name, "phone": row.phone, "gender": row.gender, "birth_date": str(row.birth_date) if row.birth_date else None}}
    except Exception as exc:
        return {"found": False, "error": str(exc)}
    finally:
        db.close()


@register_tool("get_recent_results", "Get recent lab results for a patient", requires_approval=False)
async def _get_recent_results(patient_id: int, limit: int = 10, **kwargs) -> dict[str, Any]:
    db = next(get_db())
    try:
        rows = db.execute(
            text("SELECT lr.test_name, lr.value, lr.unit, lr.normal_range_low, lr.normal_range_high, lr.result_date FROM lab_results lr JOIN lab_orders lo ON lr.order_id = lo.id WHERE lo.patient_id = :pid ORDER BY lr.result_date DESC LIMIT :lim"),
            {"pid": patient_id, "lim": limit},
        ).fetchall()
        results = [{"test_name": r.test_name, "value": r.value, "unit": r.unit, "normal_range_low": r.normal_range_low, "normal_range_high": r.normal_range_high, "result_date": str(r.result_date) if r.result_date else None} for r in rows]
        return {"patient_id": patient_id, "results": results, "count": len(results)}
    except Exception as exc:
        return {"error": str(exc)}
    finally:
        db.close()


@register_tool("analyze_lab_pattern", "Run multi-test pattern analysis on lab results", requires_approval=False)
async def _analyze_lab_pattern(patient_id: int, **kwargs) -> dict[str, Any]:
    db = next(get_db())
    try:
        rows = db.execute(
            text("SELECT lr.test_name, lr.value, lr.unit, lr.normal_range_low, lr.normal_range_high FROM lab_results lr JOIN lab_orders lo ON lr.order_id = lo.id WHERE lo.patient_id = :pid AND lr.result_date IS NOT NULL ORDER BY lr.result_date DESC LIMIT 50"),
            {"pid": patient_id},
        ).fetchall()
        result_list = [{"test_name": r.test_name, "value": r.value, "unit": r.unit, "normal_range_low": r.normal_range_low, "normal_range_high": r.normal_range_high} for r in rows]
        from app.ai.sandbox import AISandbox
        suggestion = ai_suggest("analyze_order", {"order_id": 0, "result_list": result_list}, ai_model="agent_runtime", confidence=0.9, rationale="Agent-based pattern analysis", entity_type="patient", entity_id=patient_id)
        from app.ai.approval import approval_store
        approval = approval_store.submit(suggestion)
        if approval.is_executable:
            result = AISandbox.execute(approval)
            return {"patterns": result.output.get("patterns", []), "flag_summary": result.output.get("flag_summary", {}), "interpretations": result.output.get("interpretations", [])}
        return {"message": "Analysis pending approval", "approval_id": approval.id}
    except Exception as exc:
        return {"error": str(exc)}
    finally:
        db.close()


@register_tool("get_lab_info", "Get information about the lab", requires_approval=False)
async def _get_lab_info(lab_id: int | None = None, **kwargs) -> dict[str, Any]:
    if lab_id is None:
        return {"error": "lab_id is required"}
    db = next(get_db())
    try:
        row = db.execute(
            text("SELECT id, name, name_ar, phone, city, address FROM labs WHERE id = :lab"),
            {"lab": lab_id},
        ).fetchone()
        if not row:
            return {"error": "Lab not found"}
        return {"lab": {"id": row.id, "name": row.name, "name_ar": row.name_ar, "phone": row.phone, "city": row.city, "address": row.address}}
    except Exception as exc:
        return {"error": str(exc)}
    finally:
        db.close()


@register_tool("search_knowledge_graph", "Search the medical knowledge graph for tests, conditions, medications", requires_approval=False)
async def _search_knowledge_graph(query: str, **kwargs) -> dict[str, Any]:
    from app.ai.knowledge_graph import knowledge_graph
    knowledge_graph.initialize()
    nodes = knowledge_graph.search_nodes(query, limit=10)
    return {
        "results": [
            {"type": n.node_type, "label": n.label, "description": n.description, "aliases": n.aliases, "external_id": n.external_id}
            for n in nodes
        ],
        "count": len(nodes),
    }


def list_tools() -> list[dict[str, Any]]:
    return [
        {"name": t.name, "description": t.description, "requires_approval": t.requires_approval}
        for t in _tool_registry.values()
    ]


class AgentRuntime:

    def __init__(self, approval_store_instance: ApprovalStore | None = None):
        self.approval_store = approval_store_instance
        self._running_tasks: dict[str, asyncio.Task] = {}

    async def execute_tool(
        self, tool_name: str, context: AgentContext, **kwargs
    ) -> AgentResult:
        start = time.monotonic()
        tool = _tool_registry.get(tool_name)
        if tool is None:
            return AgentResult(agent_name="tool_executor", success=False, output=None, duration_ms=(time.monotonic() - start) * 1000, error=f"Tool '{tool_name}' not found")

        try:
            output = await tool.fn(**kwargs, lab_id=context.lab_id, user_id=context.user_id)
            if not tool.requires_approval:
                return AgentResult(agent_name=tool_name, success=True, output=output, duration_ms=(time.monotonic() - start) * 1000)

            suggestion = ai_suggest(
                operation=tool_name,
                payload={"input": kwargs, "output": str(output)[:500]},
                ai_model="agent_runtime",
                confidence=0.8,
                rationale=f"Agent tool call for task: {context.task[:100]}",
                entity_type="agent",
            )
            if self.approval_store:
                approval = self.approval_store.submit(suggestion)
                duration = (time.monotonic() - start) * 1000
                return AgentResult(agent_name=tool_name, success=True, output=output, duration_ms=duration, requires_approval=True, approval=approval)

            return AgentResult(agent_name=tool_name, success=True, output=output, duration_ms=(time.monotonic() - start) * 1000)
        except Exception as exc:
            logger.error("[AgentRuntime] tool %s failed: %s", tool_name, exc)
            return AgentResult(agent_name=tool_name, success=False, output=None, duration_ms=(time.monotonic() - start) * 1000, error=str(exc))

    async def execute_plan(
        self, plan: list[dict[str, Any]], context: AgentContext
    ) -> list[AgentResult]:
        results = []
        for step in plan:
            tool_name = step.get("tool", "")
            params = step.get("params", {})
            result = await self.execute_tool(tool_name, context, **params)
            results.append(result)
            if not result.success and step.get("required", True):
                logger.warning("[AgentRuntime] plan aborted at step %s: %s", tool_name, result.error)
                break
            if result.requires_approval:
                break
        return results

    async def run_session(
        self, session_id: str, task: str, lab_id: int | None = None, user_id: int | None = None
    ) -> list[AgentResult]:
        conv = await memory_store.get_session(session_id)
        if conv is None:
            conv = await memory_store.create_session(lab_id=lab_id, user_id=user_id)

        await memory_store.add_message(session_id, "user", task)
        context = AgentContext(session_id=session_id, lab_id=lab_id, user_id=user_id, task=task)

        history = memory_store.get_history(session_id, max_tokens=500)
        llm_plan = await self._plan_tools(task, history)

        results = await self.execute_plan(llm_plan, context)

        summary_parts = []
        for r in results:
            if r.success:
                summary_parts.append(str(r.output)[:200])
        summary = "\n".join(summary_parts) if summary_parts else "No results"
        await memory_store.add_message(session_id, "assistant", f"Task results:\n{summary}", metadata={"agent_results": [{"agent": r.agent_name, "success": r.success, "duration_ms": r.duration_ms} for r in results]})

        return results

    async def _plan_tools(self, task: str, history: str) -> list[dict[str, Any]]:
        available = list_tools()
        tool_names = [t["name"] for t in available]
        prompt = (
            f"المهمة: {task}\n\n"
            f"الأدوات المتاحة: {', '.join(tool_names)}\n\n"
            f"قم بتحديد قائمة بالأدوات التي يجب استدعاؤها لتنفيذ المهمة. "
            f"أعد القائمة بتنسيق JSON بالشكل التالي:\n"
            f'[{{"tool": "اسم_الأداة", "params": {{...}}, "required": true/false}}]\n'
            f"أعد JSON فقط، بدون شرح إضافي."
        )
        try:
            from app.gateways.google_ai import generate_chat
            text = await generate_chat(prompt, context="agent_planning")
            text = text.strip()
            if "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
                if text.startswith("json"):
                    text = text[4:].strip()
            plan = json.loads(text)
            if isinstance(plan, list):
                return plan
        except Exception as exc:
            logger.warning("[AgentRuntime] LLM planning failed: %s", exc)
        return [{"tool": "search_knowledge_graph", "params": {"query": task}, "required": False}]


agent_runtime = AgentRuntime()

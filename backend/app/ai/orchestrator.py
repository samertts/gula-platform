from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from app.ai.agent_runtime import AgentContext, AgentRuntime, agent_runtime
from app.ai.rag_pipeline import rag
from app.ai.security import sanitize_response, scan_input
from app.gateways.google_ai import generate_chat

logger = logging.getLogger("gula.ai.orchestrator")


@dataclass
class OrchestrationTask:
    id: str
    type: str
    query: str
    lab_id: int | None = None
    user_id: int | None = None
    session_id: str | None = None
    status: str = "pending"
    result: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    started_at: float = field(default_factory=time.time)
    completed_at: float | None = None


class AIOrchestrator:

    def __init__(self, agent: AgentRuntime | None = None):
        self.agent = agent or agent_runtime
        self._tasks: dict[str, OrchestrationTask] = {}

    async def process_query(
        self,
        query: str,
        lab_id: int | None = None,
        user_id: int | None = None,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        security = await scan_input(query)
        if not security.is_safe:
            logger.warning("[Orchestrator] query rejected by AI safety policy")
            return {"error": "تم رفض الطلب وفق سياسة سلامة المساعد.", "intent": "blocked"}

        intent = await self._classify_intent(query)
        task_id = str(uuid.uuid4())
        task = OrchestrationTask(id=task_id, type=intent, query=query, lab_id=lab_id, user_id=user_id, session_id=session_id)
        self._tasks[task_id] = task

        try:
            task.status = "processing"
            result = await self._execute_by_intent(intent, query, lab_id, user_id, session_id)
            task.status = "completed"
            task.result = result
            task.completed_at = time.time()
            return result
        except Exception:
            task.status = "failed"
            task.error = "AI processing failed"
            logger.exception("[Orchestrator] task %s failed", task_id)
            return {"error": "AI processing failed", "intent": intent, "task_id": task_id}

    async def _classify_intent(self, query: str) -> str:
        q = query.lower().strip()
        clinical_keywords = ["test", "result", "lab", "analyze", "interpret", "normal", "abnormal", "high", "low", "تحليل", "نتيجة", "فحص"]
        patient_keywords = ["patient", "find", "lookup", "search", "name", "phone", "مريض", "اسم", "هاتف"]
        knowledge_keywords = ["what is", "explain", "meaning", "difference", "compare", "condition", "medication", "ما هو", "شرح", "معنى"]
        agent_keywords = ["execute", "run", "plan", "do", "perform", "نفذ", "اعمل", "خطط"]

        score = {"clinical": 0, "patient": 0, "knowledge": 0, "agent": 0, "chat": 1}

        for kw in clinical_keywords:
            if kw in q:
                score["clinical"] += 1
        for kw in patient_keywords:
            if kw in q:
                score["patient"] += 1
        for kw in knowledge_keywords:
            if kw in q:
                score["knowledge"] += 1
        for kw in agent_keywords:
            if kw in q:
                score["agent"] += 1

        return max(score, key=score.get)

    async def _execute_by_intent(
        self,
        intent: str,
        query: str,
        lab_id: int | None,
        user_id: int | None,
        session_id: str | None,
    ) -> dict[str, Any]:
        if intent == "clinical":
            return await self._handle_clinical(query, lab_id)
        if intent == "patient":
            return await self._handle_patient(query, lab_id)
        if intent == "knowledge":
            return await self._handle_knowledge(query)
        if intent == "agent":
            return await self._handle_agent(query, lab_id, user_id, session_id)
        return await self._handle_chat(query)

    async def _handle_clinical(self, query: str, lab_id: int | None) -> dict[str, Any]:
        rag_result = await rag.query(query, content_type="lab_result", lab_id=lab_id)
        return {
            "type": "clinical_analysis",
            "rag_response": await sanitize_response(str(rag_result.get("response", ""))),
            "citations": rag_result.get("citations", []),
        }

    async def _handle_patient(self, query: str, lab_id: int | None) -> dict[str, Any]:
        context = AgentContext(session_id=str(uuid.uuid4()), lab_id=lab_id, task=query)
        result = await agent_runtime.execute_tool("lookup_patient", context, query=query)
        if result.success:
            return {"type": "patient_lookup", "patient": result.output}
        return await self._handle_chat(query)

    async def _handle_knowledge(self, query: str) -> dict[str, Any]:
        rag_result = await rag.query(query, content_type="knowledge")
        return {
            "type": "knowledge_query",
            "response": await sanitize_response(str(rag_result.get("response", ""))),
            "citations": rag_result.get("citations", []),
            "source": "rag_pipeline",
        }

    async def _handle_agent(
        self, query: str, lab_id: int | None, user_id: int | None, session_id: str | None,
    ) -> dict[str, Any]:
        if not session_id:
            session_id = str(uuid.uuid4())
        results = await agent_runtime.run_session(session_id, query, lab_id, user_id)
        steps = []
        for result in results:
            steps.append(
                {
                    "agent": result.agent_name,
                    "success": result.success,
                    "output": await sanitize_response(str(result.output)[:300]),
                    "duration_ms": result.duration_ms,
                }
            )
        return {
            "type": "agent_execution",
            "session_id": session_id,
            "steps": steps,
        }

    async def _handle_chat(self, query: str) -> dict[str, Any]:
        try:
            response = await generate_chat(query)
            return {"type": "chat", "response": await sanitize_response(response)}
        except Exception:
            logger.exception("[Orchestrator] chat generation failed")
            return {"type": "chat", "response": "عذراً، تعذر إنشاء الرد. يرجى المحاولة لاحقاً."}

    def get_task(self, task_id: str) -> OrchestrationTask | None:
        return self._tasks.get(task_id)

    def list_tasks(self, status: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        tasks = list(self._tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        tasks.sort(key=lambda t: t.started_at, reverse=True)
        return [
            {"id": t.id, "type": t.type, "status": t.status, "query": t.query[:100], "started_at": t.started_at, "completed_at": t.completed_at}
            for t in tasks[:limit]
        ]


orchestrator = AIOrchestrator()

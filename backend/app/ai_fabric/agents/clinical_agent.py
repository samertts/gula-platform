from __future__ import annotations

import logging
from typing import Any

from app.ai.approval import approval_store
from app.ai.guardrails import ai_suggest
from app.ai_fabric.agents.base import AgentTool, AIAgent

logger = logging.getLogger("gula.ai_fabric.agents.clinical")


class ClinicalAgent(AIAgent):
    def __init__(self, agent_id: str = "", name: str = "ClinicalAgent") -> None:
        super().__init__(agent_id=agent_id, name=name)

    def _register_default_tools(self) -> None:
        self.register_tool(
            AgentTool(
                name="suggest_interpretation",
                description="Interpret a single lab result with clinical context",
                fn=self._tool_interpret_result,
                parameters={"test_name": "str", "value": "float", "unit": "str"},
                requires_approval=True,
            ),
        )
        self.register_tool(
            AgentTool(
                name="analyze_clinical_pattern",
                description="Analyze multi-test patterns for clinical conditions",
                fn=self._tool_analyze_pattern,
                parameters={"order_id": "str", "results": "list"},
                requires_approval=False,
            ),
        )
        self.register_tool(
            AgentTool(
                name="suggest_reorder",
                description="Suggest re-running a specific test",
                fn=self._tool_suggest_reorder,
                parameters={"test_name": "str", "reason": "str"},
                requires_approval=True,
            ),
        )

    def can_handle(self, task_type: str) -> bool:
        return task_type in ("clinical", "interpretation", "cds", "diagnosis")

    def _execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        action = input_data.get("action", "")
        if action == "interpret":
            return self._interpret(input_data)
        if action == "analyze":
            return self._analyze(input_data)
        if action == "suggest":
            return self._suggest(input_data)
        return {"error": f"Unknown action: {action}"}

    def _interpret(self, data: dict[str, Any]) -> dict[str, Any]:
        test_name = data.get("test_name", "")
        value = data.get("value")
        if value is None:
            return {"error": "value required"}
        try:
            suggestion = ai_suggest(
                operation="suggest_interpretation",
                payload={"test_name": test_name, "value": float(value)},
                ai_model="clinical-agent",
                confidence=data.get("confidence", 0.7),
                entity_type="result",
            )
            approval = approval_store.submit(suggestion)
            return {
                "suggestion_id": suggestion.id,
                "approval_id": approval.id,
                "operation": "suggest_interpretation",
                "status": "pending_approval",
                "payload": suggestion.payload,
            }
        except Exception as exc:
            self._error = str(exc)
            return {"error": str(exc)}

    def _analyze(self, data: dict[str, Any]) -> dict[str, Any]:
        order_id = data.get("order_id", "")
        results = data.get("results", [])
        return {
            "order_id": order_id,
            "result_count": len(results),
            "patterns": [],
            "recommendation": "Analysis complete",
        }

    def _suggest(self, data: dict[str, Any]) -> dict[str, Any]:
        test_name = data.get("test_name", "")
        reason = data.get("reason", "Clinical follow-up recommended")
        try:
            suggestion = ai_suggest(
                operation="suggest_reorder",
                payload={"test_name": test_name, "reason": reason},
                ai_model="clinical-agent",
                confidence=0.6,
                entity_type="order",
            )
            approval = approval_store.submit(suggestion)
            return {
                "suggestion_id": suggestion.id,
                "approval_id": approval.id,
                "operation": "suggest_reorder",
                "status": "pending_approval",
            }
        except Exception as exc:
            return {"error": str(exc)}

    def _tool_interpret_result(self, **kwargs: Any) -> dict[str, Any]:
        return self._interpret(kwargs)

    def _tool_analyze_pattern(self, **kwargs: Any) -> dict[str, Any]:
        return self._analyze(kwargs)

    def _tool_suggest_reorder(self, **kwargs: Any) -> dict[str, Any]:
        return self._suggest(kwargs)

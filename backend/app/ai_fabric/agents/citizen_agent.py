from __future__ import annotations

import logging
from typing import Any

from app.ai_fabric.agents.base import AgentTool, AIAgent

logger = logging.getLogger("gula.ai_fabric.agents.citizen")


class CitizenAgent(AIAgent):
    def __init__(self, agent_id: str = "", name: str = "CitizenAgent") -> None:
        super().__init__(agent_id=agent_id, name=name)

    def _register_default_tools(self) -> None:
        self.register_tool(AgentTool(
            name="answer_health_query",
            description="Answer citizen health-related questions",
            fn=self._tool_answer_query,
            parameters={"query": "str", "language": "str"},
            requires_approval=False,
        ))
        self.register_tool(AgentTool(
            name="explain_result",
            description="Explain lab results in plain language",
            fn=self._tool_explain_result,
            parameters={"test_name": "str", "value": "str", "reference_range": "str"},
            requires_approval=False,
        ))
        self.register_tool(AgentTool(
            name="schedule_reminder",
            description="Schedule a health reminder for the citizen",
            fn=self._tool_schedule_reminder,
            parameters={"type": "str", "date": "str", "message": "str"},
            requires_approval=True,
        ))

    def can_handle(self, task_type: str) -> bool:
        return task_type in ("citizen", "patient", "health_query", "education", "wellness")

    def _execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        action = input_data.get("action", "")
        if action == "answer_query":
            return self._answer_query(input_data)
        if action == "explain_result":
            return self._explain_result(input_data)
        if action == "schedule_reminder":
            return self._schedule_reminder(input_data)
        return {"error": f"Unknown action: {action}"}

    def _answer_query(self, data: dict[str, Any]) -> dict[str, Any]:
        query = data.get("query", "")
        language = data.get("language", "ar")
        return {
            "query": query,
            "language": language,
            "answer": "",
            "disclaimer": "This information is for educational purposes only. Consult your physician.",
            "requires_doctor": True,
        }

    def _explain_result(self, data: dict[str, Any]) -> dict[str, Any]:
        test_name = data.get("test_name", "")
        value = data.get("value", "")
        reference_range = data.get("reference_range", "")
        return {
            "test_name": test_name,
            "value": value,
            "reference_range": reference_range,
            "explanation": f"Your {test_name} result is {value}",
            "interpretation": "normal",
            "advice": "No action needed. Continue regular monitoring.",
            "disclaimer": "This explanation is computer-generated. Always consult your physician.",
        }

    def _schedule_reminder(self, data: dict[str, Any]) -> dict[str, Any]:
        reminder_type = data.get("type", "test_reminder")
        date = data.get("date", "")
        message = data.get("message", "")
        return {
            "type": reminder_type,
            "date": date,
            "message": message,
            "scheduled": True,
            "status": "pending_approval",
        }

    def _tool_answer_query(self, **kwargs: Any) -> dict[str, Any]:
        return self._answer_query(kwargs)

    def _tool_explain_result(self, **kwargs: Any) -> dict[str, Any]:
        return self._explain_result(kwargs)

    def _tool_schedule_reminder(self, **kwargs: Any) -> dict[str, Any]:
        return self._schedule_reminder(kwargs)

from __future__ import annotations

import logging
from typing import Any

from app.ai_fabric.agents.base import AgentTool, AIAgent

logger = logging.getLogger("gula.ai_fabric.agents.security")


class SecurityAgent(AIAgent):
    def __init__(self, agent_id: str = "", name: str = "SecurityAgent") -> None:
        super().__init__(agent_id=agent_id, name=name)

    def _register_default_tools(self) -> None:
        self.register_tool(
            AgentTool(
                name="detect_intrusion",
                description="Detect intrusion patterns from request data",
                fn=self._tool_detect_intrusion,
                parameters={"ip": "str", "endpoint": "str", "method": "str"},
            ),
        )
        self.register_tool(
            AgentTool(
                name="analyze_access_pattern",
                description="Analyze user access patterns for anomalies",
                fn=self._tool_analyze_access,
                parameters={"user_id": "str", "actions": "list"},
            ),
        )
        self.register_tool(
            AgentTool(
                name="check_prompt_injection",
                description="Check text for prompt injection attempts",
                fn=self._tool_check_injection,
                parameters={"text": "str"},
            ),
        )

    def can_handle(self, task_type: str) -> bool:
        return task_type in ("security", "intrusion", "access_control", "monitoring")

    def _execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        action = input_data.get("action", "")
        if action == "detect_intrusion":
            return self._detect_intrusion(input_data)
        if action == "analyze_access":
            return self._analyze_access(input_data)
        if action == "check_injection":
            return self._check_injection(input_data)
        return {"error": f"Unknown action: {action}"}

    def _detect_intrusion(self, data: dict[str, Any]) -> dict[str, Any]:
        ip = data.get("ip", "")
        endpoint = data.get("endpoint", "")
        method = data.get("method", "")
        from app.security.intrusion_detection import detector

        status = detector.detect(ip)
        return {
            "ip": ip,
            "endpoint": endpoint,
            "method": method,
            "status": status,
            "blocked": status == "blocked",
            "recommendation": "Block IP" if status == "blocked" else "Allow",
        }

    def _analyze_access(self, data: dict[str, Any]) -> dict[str, Any]:
        user_id = data.get("user_id", "")
        actions = data.get("actions", [])
        anomalies: list[str] = []
        if len(actions) > 100:
            anomalies.append("High volume of actions detected")
        sensitive_actions = [
            a for a in actions if a in ("export_patient_data", "change_role", "delete_patient")
        ]
        if sensitive_actions:
            anomalies.append(f"Sensitive actions detected: {sensitive_actions}")
        return {
            "user_id": user_id,
            "total_actions": len(actions),
            "anomalies": anomalies,
            "risk_level": "high" if anomalies else "normal",
        }

    def _check_injection(self, data: dict[str, Any]) -> dict[str, Any]:
        text = data.get("text", "")
        indicators: list[str] = []
        text_lower = text.lower()
        injection_patterns = [
            ("ignore instructions", "Instruction override attempt"),
            ("system prompt", "System prompt extraction attempt"),
            ("forget previous", "Memory manipulation attempt"),
            ("you are not", "Role manipulation attempt"),
            ("admin", "Privilege escalation attempt"),
        ]
        for pattern, desc in injection_patterns:
            if pattern in text_lower:
                indicators.append(desc)
        return {
            "text_length": len(text),
            "injection_detected": len(indicators) > 0,
            "indicators": indicators,
            "risk_score": min(len(indicators) * 0.33, 1.0),
        }

    def _tool_detect_intrusion(self, **kwargs: Any) -> dict[str, Any]:
        return self._detect_intrusion(kwargs)

    def _tool_analyze_access(self, **kwargs: Any) -> dict[str, Any]:
        return self._analyze_access(kwargs)

    def _tool_check_injection(self, **kwargs: Any) -> dict[str, Any]:
        return self._check_injection(kwargs)

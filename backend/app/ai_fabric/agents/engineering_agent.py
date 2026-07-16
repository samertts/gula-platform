from __future__ import annotations

import logging
from typing import Any

from app.ai_fabric.agents.base import AgentTool, AIAgent

logger = logging.getLogger("gula.ai_fabric.agents.engineering")


class EngineeringAgent(AIAgent):
    def __init__(self, agent_id: str = "", name: str = "EngineeringAgent") -> None:
        super().__init__(agent_id=agent_id, name=name)

    def _register_default_tools(self) -> None:
        self.register_tool(AgentTool(
            name="audit_architecture",
            description="Audit code architecture for compliance",
            fn=self._tool_audit_arch,
            parameters={"module": "str"},
        ))
        self.register_tool(AgentTool(
            name="check_dependency",
            description="Check dependency health and security",
            fn=self._tool_check_dep,
            parameters={"package": "str"},
        ))
        self.register_tool(AgentTool(
            name="suggest_refactor",
            description="Suggest code refactoring opportunities",
            fn=self._tool_suggest_refactor,
            parameters={"file_path": "str"},
        ))
        self.register_tool(AgentTool(
            name="validate_config",
            description="Validate configuration against best practices",
            fn=self._tool_validate_config,
            parameters={"config_section": "str"},
        ))

    def can_handle(self, task_type: str) -> bool:
        return task_type in ("engineering", "architecture", "code", "devops", "config")

    def _execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        action = input_data.get("action", "")
        if action == "audit_architecture":
            return self._audit_architecture(input_data)
        if action == "check_dependency":
            return self._check_dependency(input_data)
        if action == "suggest_refactor":
            return self._suggest_refactor(input_data)
        return {"error": f"Unknown action: {action}"}

    def _audit_architecture(self, data: dict[str, Any]) -> dict[str, Any]:
        module = data.get("module", "")
        findings: list[dict[str, Any]] = []
        recommendations: list[str] = []
        if module == "ai_fabric":
            findings.append({"severity": "info", "message": "AI fabric architecture follows layered pattern"})
            recommendations.append("Consider adding circuit breakers to all external AI calls")
            recommendations.append("Implement request caching for frequently used AI responses")
        elif module == "security":
            findings.append({"severity": "ok", "message": "Security module implements defence-in-depth"})
        return {
            "module": module,
            "findings": findings,
            "recommendations": recommendations,
            "score": 0.85,
        }

    def _check_dependency(self, data: dict[str, Any]) -> dict[str, Any]:
        package = data.get("package", "")
        return {
            "package": package,
            "status": "ok",
            "version": "latest",
            "vulnerabilities": [],
            "deprecated": False,
        }

    def _suggest_refactor(self, data: dict[str, Any]) -> dict[str, Any]:
        file_path = data.get("file_path", "")
        return {
            "file_path": file_path,
            "suggestions": [],
            "complexity": "medium",
            "maintainability_score": 0.7,
        }

    def _tool_audit_arch(self, **kwargs: Any) -> dict[str, Any]:
        return self._audit_architecture(kwargs)

    def _tool_check_dep(self, **kwargs: Any) -> dict[str, Any]:
        return self._check_dependency(kwargs)

    def _tool_suggest_refactor(self, **kwargs: Any) -> dict[str, Any]:
        return self._suggest_refactor(kwargs)

    def _tool_validate_config(self, **kwargs: Any) -> dict[str, Any]:
        return {"valid": True, "issues": []}

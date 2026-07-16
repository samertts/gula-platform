from __future__ import annotations

import logging
from typing import Any

from app.ai_fabric.agents.base import AIAgent
from app.ai_fabric.enums import AgentStatus

logger = logging.getLogger("gula.ai_fabric.agents.registry")


class AgentRegistry:
    _instance: AgentRegistry | None = None

    def __new__(cls) -> AgentRegistry:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._agents: dict[str, AIAgent] = {}
            cls._instance._initialized = False
        return cls._instance

    def register(self, agent: AIAgent) -> None:
        if agent.id in self._agents:
            logger.warning("Agent %s already registered, overwriting", agent.id)
        self._agents[agent.id] = agent
        logger.info("Registered agent: %s (%s)", agent.name, agent.id)

    def unregister(self, agent_id: str) -> bool:
        agent = self._agents.pop(agent_id, None)
        if agent:
            agent.shutdown()
            logger.info("Unregistered agent: %s", agent_id)
            return True
        return False

    def get(self, agent_id: str) -> AIAgent | None:
        return self._agents.get(agent_id)

    def get_by_name(self, name: str) -> AIAgent | None:
        for agent in self._agents.values():
            if agent.name == name:
                return agent
        return None

    def find_for_task(self, task_type: str) -> AIAgent | None:
        for agent in self._agents.values():
            if agent.can_handle(task_type) and agent.lifecycle.value == 1:
                return agent
        return None

    def list_agents(self) -> list[dict[str, Any]]:
        return [
            {
                "id": a.id,
                "name": a.name,
                "status": a.status.value,
                "lifecycle": a.lifecycle.name,
                "invocations": a.invocations,
                "error": a.error or "",
                "tools": list(a.tools.keys()),
            }
            for a in self._agents.values()
        ]

    def list_by_status(self, status: AgentStatus) -> list[AIAgent]:
        return [a for a in self._agents.values() if a.status == status]

    def initialize_all(self) -> int:
        count = 0
        for agent in self._agents.values():
            try:
                agent.initialize()
                count += 1
            except Exception as exc:
                logger.error("Failed to initialize agent %s: %s", agent.name, exc)
        self._initialized = True
        logger.info("Initialized %d/%d agents", count, len(self._agents))
        return count

    def shutdown_all(self) -> int:
        count = 0
        for agent in self._agents.values():
            agent.shutdown()
            count += 1
        self._agents.clear()
        self._initialized = False
        return count

    def agent_heartbeats(self) -> list[dict[str, Any]]:
        return [a.heartbeat() for a in self._agents.values()]

    def get_statistics(self) -> dict[str, Any]:
        total = len(self._agents)
        by_status: dict[str, int] = {}
        for a in self._agents.values():
            by_status[a.status.value] = by_status.get(a.status.value, 0) + 1
        return {
            "total_agents": total,
            "by_status": by_status,
            "initialized": self._initialized,
            "total_invocations": sum(a.invocations for a in self._agents.values()),
        }

    @property
    def initialized(self) -> bool:
        return self._initialized

    @property
    def count(self) -> int:
        return len(self._agents)


agent_registry = AgentRegistry()

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

from app.ai_fabric.enums import AgentStatus

logger = logging.getLogger("gula.ai_fabric.agents.base")


class AgentLifecycle(Enum):
    INITIALIZED = auto()
    READY = auto()
    RUNNING = auto()
    ERROR = auto()
    SHUTDOWN = auto()


@dataclass
class AgentMemory:
    short_term: dict[str, Any] = field(default_factory=dict)
    long_term: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    max_short_term: int = 100

    def remember(self, key: str, value: Any) -> None:
        if len(self.short_term) >= self.max_short_term:
            oldest = next(iter(self.short_term))
            self.long_term.setdefault("_archived", []).append(
                {"key": oldest, "value": self.short_term[oldest], "at": time.time()},
            )
            del self.short_term[oldest]
        self.short_term[key] = value

    def recall(self, key: str) -> Any:
        return self.short_term.get(key)

    def store_long(self, namespace: str, entry: dict[str, Any]) -> None:
        self.long_term.setdefault(namespace, []).append(entry)

    def retrieve_long(self, namespace: str, limit: int = 50) -> list[dict[str, Any]]:
        return self.long_term.get(namespace, [])[-limit:]

    def clear_short_term(self) -> None:
        self.short_term.clear()


@dataclass
class AgentTool:
    name: str = ""
    description: str = ""
    fn: Callable[..., Any] = lambda **kwargs: None
    parameters: dict[str, Any] = field(default_factory=dict)
    requires_approval: bool = False

    def execute(self, **kwargs: Any) -> Any:
        logger.debug("Agent tool %s executing with %s", self.name, kwargs)
        return self.fn(**kwargs)


@dataclass
class AgentContext:
    agent_id: str = ""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    lab_id: str = ""
    request_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    start_time: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "lab_id": self.lab_id,
            "request_id": self.request_id,
            "metadata": self.metadata,
        }


class AIAgent:
    def __init__(self, agent_id: str = "", name: str = "") -> None:
        self._id = agent_id or str(uuid.uuid4())
        self._name = name or self.__class__.__name__
        self._lifecycle = AgentLifecycle.INITIALIZED
        self._status = AgentStatus.IDLE
        self._memory = AgentMemory()
        self._tools: dict[str, AgentTool] = {}
        self._context: AgentContext | None = None
        self._error: str = ""
        self._started_at: float = 0.0
        self._invocations: int = 0
        self._register_default_tools()
        logger.info("Agent %s (%s) initialized", self._name, self._id)

    def _register_default_tools(self) -> None:
        pass

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def lifecycle(self) -> AgentLifecycle:
        return self._lifecycle

    @property
    def status(self) -> AgentStatus:
        return self._status

    @property
    def memory(self) -> AgentMemory:
        return self._memory

    @property
    def tools(self) -> dict[str, AgentTool]:
        return self._tools

    @property
    def error(self) -> str:
        return self._error

    @property
    def invocations(self) -> int:
        return self._invocations

    def register_tool(self, tool: AgentTool) -> None:
        self._tools[tool.name] = tool
        logger.debug("Agent %s registered tool: %s", self._name, tool.name)

    def initialize(self) -> None:
        self._lifecycle = AgentLifecycle.READY
        self._started_at = time.time()
        logger.info("Agent %s ready", self._name)

    def run(self, context: AgentContext, input_data: dict[str, Any]) -> dict[str, Any]:
        if self._lifecycle != AgentLifecycle.READY and self._lifecycle != AgentLifecycle.RUNNING:
            return {"error": f"Agent {self._name} not ready (lifecycle={self._lifecycle.name})"}

        self._lifecycle = AgentLifecycle.RUNNING
        self._status = AgentStatus.BUSY
        self._context = context
        self._memory.remember("last_context", context.to_dict())
        self._memory.remember("last_input", input_data)
        self._invocations += 1

        try:
            result = self._execute(input_data)
            self._status = AgentStatus.IDLE
            return result
        except Exception as exc:
            self._lifecycle = AgentLifecycle.ERROR
            self._status = AgentStatus.ERROR
            self._error = str(exc)
            logger.error("Agent %s error: %s", self._name, exc)
            return {"error": str(exc)}

    def _execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("Subclasses must implement _execute")

    def can_handle(self, task_type: str) -> bool:
        return False

    def shutdown(self) -> None:
        self._lifecycle = AgentLifecycle.SHUTDOWN
        self._status = AgentStatus.IDLE
        self._memory.clear_short_term()
        logger.info("Agent %s shut down", self._name)

    def heartbeat(self) -> dict[str, Any]:
        return {
            "id": self._id,
            "name": self._name,
            "lifecycle": self._lifecycle.name,
            "status": self._status.value,
            "error": self._error or "",
            "invocations": self._invocations,
            "tools": list(self._tools.keys()),
            "uptime_s": round(time.time() - self._started_at, 2) if self._started_at else 0.0,
        }

    def get_metrics(self) -> dict[str, Any]:
        return {
            "invocations": self._invocations,
            "tools_registered": len(self._tools),
            "short_term_memory_size": len(self._memory.short_term),
            "long_term_memory_namespaces": list(self._memory.long_term.keys()),
            "current_status": self._status.value,
        }

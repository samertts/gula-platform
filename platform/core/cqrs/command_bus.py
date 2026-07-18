import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable


@dataclass
class Command:
    command_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)


CommandHandler = Callable[[Command], Any]


class CommandBus:
    def __init__(self):
        self._logger = logging.getLogger("gula.cqrs.command")
        self._handlers: dict[str, list[CommandHandler]] = {}
        self._middleware: list[Callable] = []

    def register(self, command_type: str, handler: CommandHandler) -> None:
        self._handlers.setdefault(command_type, []).append(handler)
        self._logger.debug("Handler registered for command: %s", command_type)

    def unregister(self, command_type: str, handler: CommandHandler) -> None:
        handlers = self._handlers.get(command_type)
        if handlers and handler in handlers:
            handlers.remove(handler)

    def add_middleware(self, middleware: Callable) -> None:
        self._middleware.append(middleware)

    async def dispatch(self, command_type: str, command: Command) -> list[Any]:
        async def _execute() -> list[Any]:
            handlers = self._handlers.get(command_type, [])
            if not handlers:
                self._logger.warning("No handlers for command: %s", command_type)
                return []
            results = []
            for handler in handlers:
                result = handler(command)
                if hasattr(result, "__await__"):
                    result = await result
                results.append(result)
            return results

        pipeline = _execute()
        for mw in reversed(self._middleware):
            pipeline = mw(command_type, command, pipeline)
        return await pipeline

    def handler_count(self) -> int:
        return sum(len(h) for h in self._handlers.values())

    def registered_commands(self) -> list[str]:
        return list(self._handlers.keys())

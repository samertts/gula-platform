from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from backend.app.engineering.generators.base import BaseGenerator, GenerateResult


@dataclass
class CQRSSpec:
    name: str
    commands: list[str] = field(default_factory=list)
    queries: list[str] = field(default_factory=list)
    command_handlers: bool = True
    query_handlers: bool = True
    bus: bool = True
    decorators: bool = True


class CQRSGenerator(BaseGenerator):
    def generate(self, **kwargs: Any) -> GenerateResult:
        spec = kwargs.get("spec", kwargs.get("cqrs"))
        if isinstance(spec, dict):
            spec = CQRSSpec(**spec)
        if spec is None:
            spec = CQRSSpec(name=kwargs.get("name", "unnamed"))

        spec.name.lower()
        spec.name[0].upper() + spec.name[1:]

        self._ensure_dir("commands")
        self._ensure_dir("queries")
        self._ensure_dir("handlers")
        (self.target_dir / "commands" / "__init__.py").touch()
        (self.target_dir / "queries" / "__init__.py").touch()
        (self.target_dir / "handlers" / "__init__.py").touch()

        for cmd in spec.commands:
            Cmd = cmd[0].upper() + cmd[1:]
            self._write(
                f"commands/{cmd}.py",
                f"""from __future__ import annotations

from dataclasses import dataclass


@dataclass
class {Cmd}Command:
    pass
""",
            )

            if spec.command_handlers:
                self._write(
                    f"handlers/{cmd}_handler.py",
                    f"""from __future__ import annotations

from commands.{cmd} import {Cmd}Command


class {Cmd}CommandHandler:
    async def handle(self, command: {Cmd}Command) -> None:
        pass
""",
                )

        for qry in spec.queries:
            Qry = qry[0].upper() + qry[1:]
            self._write(
                f"queries/{qry}.py",
                f"""from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class {Qry}Query:
    pass


@dataclass
class {Qry}Result:
    data: Any = None
""",
            )

            if spec.query_handlers:
                self._write(
                    f"handlers/{qry}_handler.py",
                    f"""from __future__ import annotations

from queries.{qry} import {Qry}Query, {Qry}Result


class {Qry}QueryHandler:
    async def handle(self, query: {Qry}Query) -> {Qry}Result:
        return {Qry}Result()
""",
                )

        if spec.bus:
            self._write(
                "bus.py",
                """from __future__ import annotations

from typing import Any, Callable

from commands import *
from queries import *
from handlers import *


class CommandBus:
    _handlers: dict[type, Callable] = {}

    @classmethod
    def register(cls, command_type: type, handler: Callable) -> None:
        cls._handlers[command_type] = handler

    async def dispatch(self, command: Any) -> Any:
        handler = self._handlers.get(type(command))
        if handler is None:
            raise ValueError(f"No handler registered for {type(command).__name__}")
        return await handler(command)


class QueryBus:
    _handlers: dict[type, Callable] = {}

    @classmethod
    def register(cls, query_type: type, handler: Callable) -> None:
        cls._handlers[query_type] = handler

    async def ask(self, query: Any) -> Any:
        handler = self._handlers.get(type(query))
        if handler is None:
            raise ValueError(f"No handler registered for {type(query).__name__}")
        return await handler(query)
""",
            )

        if spec.decorators:
            self._write(
                "decorators.py",
                """from __future__ import annotations

import functools
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def command_handler(command_type: type) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            return await func(*args, **kwargs)
        wrapper._command_type = command_type
        return wrapper
    return decorator


def query_handler(query_type: type) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            return await func(*args, **kwargs)
        wrapper._query_type = query_type
        return wrapper
    return decorator
""",
            )

        return self._result

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("gula.knowledge_graph.event_catalog")


@dataclass
class EventEntry:
    name: str
    version: str
    description: str = ""
    summary: str = ""
    schema_def: dict | None = None
    publisher: str = ""
    consumers: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    correlation_id: str | None = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "summary": self.summary,
            "schema": self.schema_def,
            "publisher": self.publisher,
            "consumers": self.consumers,
            "tags": self.tags,
            "correlation_id": self.correlation_id,
        }


@dataclass
class EventFlowEntry:
    event: EventEntry
    producers: list[str] = field(default_factory=list)
    consumers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "event": self.event.name,
            "producers": self.producers,
            "consumers": self.consumers,
        }


class EventCatalog:
    def __init__(self):
        self._events: dict[str, EventEntry] = {}

    def discover_events(self) -> list[EventEntry]:
        try:
            from app.contracts.events import EVENT_REGISTRY

            for name, spec in EVENT_REGISTRY.items():
                self._events[name] = EventEntry(
                    name=name,
                    version=spec.get("version", "1.0.0"),
                    description=spec.get("description", ""),
                    summary=spec.get("summary", ""),
                    schema_def=spec.get("payload", {}),
                    tags=spec.get("tags", []),
                    correlation_id=spec.get("correlation_id"),
                )
            logger.info("Discovered %d events from contract registry", len(self._events))
        except ImportError:
            logger.warning("app.contracts.events not available, scanning AST")

        self._scan_event_modules()
        self._scan_kernel_events()
        return list(self._events.values())

    def get_event_flow(self, event_name: str | None = None) -> list[EventFlowEntry]:
        producers: dict[str, set[str]] = {}
        consumers: dict[str, set[str]] = {}

        for name in self._events:
            if name not in producers:
                producers[name] = set()
            if name not in consumers:
                consumers[name] = set()

        try:
            import ast as _ast

            backend_app = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "app"
            )
            for root, _dirs, files in os.walk(backend_app):
                for fname in files:
                    if not fname.endswith(".py") or fname.startswith("__"):
                        continue
                    fpath = os.path.join(root, fname)
                    try:
                        with open(fpath, encoding="utf-8", errors="replace") as f:
                            tree = _ast.parse(f.read())
                    except SyntaxError:
                        continue
                    for node in _ast.walk(tree):
                        if isinstance(node, _ast.Call) and isinstance(node.func, _ast.Attribute):
                            if node.func.attr in ("publish", "emit", "dispatch"):
                                for arg in node.args:
                                    if isinstance(arg, _ast.Constant) and isinstance(arg.value, str):
                                        producers.setdefault(arg.value, set()).add(os.path.relpath(fpath, backend_app))
                                    elif isinstance(arg, _ast.Name):
                                        producers.setdefault(arg.id, set()).add(os.path.relpath(fpath, backend_app))
                            elif node.func.attr in ("subscribe", "on", "listen", "handle"):
                                for arg in node.args:
                                    if isinstance(arg, _ast.Constant) and isinstance(arg.value, str):
                                        consumers.setdefault(arg.value, set()).add(os.path.relpath(fpath, backend_app))
                                    elif isinstance(arg, _ast.Name):
                                        consumers.setdefault(arg.id, set()).add(os.path.relpath(fpath, backend_app))
        except Exception as exc:
            logger.debug("Error scanning event flow: %s", exc)

        flows = []
        for name, entry in self._events.items():
            if event_name and name != event_name:
                continue
            flows.append(EventFlowEntry(
                event=entry,
                producers=sorted(producers.get(name, [])),
                consumers=sorted(consumers.get(name, [])),
            ))
        return flows

    def get_event(self, name: str) -> EventEntry | None:
        return self._events.get(name)

    def search(self, query: str) -> list[EventEntry]:
        q = query.lower()
        return [
            e for e in self._events.values()
            if q in e.name.lower() or q in e.description.lower() or q in e.summary.lower()
            or any(q in t.lower() for t in e.tags)
        ]

    def get_summary(self) -> dict:
        return {
            "total_events": len(self._events),
            "events": sorted(self._events.keys()),
        }

    def _scan_event_modules(self) -> None:
        backend_app = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "app"
        )
        for root, _dirs, files in os.walk(backend_app):
            for fname in files:
                if not fname.endswith(".py") or fname.startswith("__"):
                    continue
                if fname.endswith(("_events.py", "events.py")):
                    fpath = os.path.join(root, fname)
                    try:
                        import ast
                        with open(fpath, encoding="utf-8", errors="replace") as f:
                            tree = ast.parse(f.read())
                        for node in ast.walk(tree):
                            if isinstance(node, ast.ClassDef) and "Event" in node.name:
                                event_name = node.name
                                if event_name not in self._events:
                                    self._events[event_name] = EventEntry(
                                        name=event_name,
                                        version="1.0.0",
                                        description=ast.get_docstring(node) or "",
                                        tags=["event"],
                                        schema_def=self._class_to_schema(node),
                                    )
                    except (SyntaxError, Exception) as exc:
                        logger.debug("Error scanning %s: %s", fpath, exc)

    def _scan_kernel_events(self) -> None:
        try:
            from app.kernel.event_bus.events import Event
            if hasattr(Event, "__subclasses__"):
                for subclass in Event.__subclasses__():
                    name = subclass.__name__
                    if name not in self._events:
                        self._events[name] = EventEntry(
                            name=name,
                            version="1.0.0",
                            description=subclass.__doc__ or "",
                            tags=["kernel", "event"],
                        )
        except ImportError:
            pass

    def _class_to_schema(self, node: Any) -> dict:
        try:
            import ast
            props: dict[str, str] = {}
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    props[item.target.id] = ast.dump(item.annotation) if item.annotation else "Any"
            return {
                "type": "object",
                "properties": {k: {"type": "inferred"} for k in props},
            }
        except Exception:
            return {"type": "object"}


event_catalog = EventCatalog()

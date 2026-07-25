from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from app.kernel import Kernel

logger = logging.getLogger("gula.kernel.runtime_sdk")


@dataclass
class PluginHook:
    name: str
    handler: Callable[[dict[str, Any]], Any]
    priority: int = 0
    phase: str = "startup"

    def execute(self, context: dict[str, Any] | None = None) -> Any:
        return self.handler(context or {})


@dataclass
class ModuleRegistration:
    name: str
    version: str
    description: str = ""
    dependencies: list[str] = field(default_factory=list)
    entry_points: list[str] = field(default_factory=list)
    enabled: bool = True
    registered_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowStep:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    handler: Callable[[dict[str, Any]], dict[str, Any]] | None = None
    compensation: Callable[[dict[str, Any]], None] | None = None
    timeout: float = 30.0
    retry_count: int = 0
    max_retries: int = 3
    depends_on: list[str] = field(default_factory=list)


@dataclass
class WorkflowInstance:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    steps: list[WorkflowStep] = field(default_factory=list)
    current_step: int = 0
    state: dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    saga: bool = False
    created_at: float = field(default_factory=time.time)
    completed_at: float = 0.0
    error: str = ""

    def is_complete(self) -> bool:
        return self.status in ("completed", "failed", "compensated")


class PluginRuntimeAPI:
    def __init__(self, kernel: Kernel):
        self._kernel = kernel
        self._hooks: dict[str, list[PluginHook]] = {}
        self._plugin_states: dict[str, str] = {}

    def register_hook(self, plugin_name: str, hook: PluginHook) -> None:
        if hook.name not in self._hooks:
            self._hooks[hook.name] = []
        self._hooks[hook.name].append(hook)
        self._hooks[hook.name].sort(key=lambda h: h.priority)
        self._plugin_states[plugin_name] = "registered"
        logger.info(
            "Plugin hook registered",
            extra={"plugin": plugin_name, "hook": hook.name, "phase": hook.phase},
        )

    def execute_hooks(self, hook_name: str, context: dict[str, Any] | None = None) -> list[Any]:
        results = []
        for hook in self._hooks.get(hook_name, []):
            try:
                result = hook.execute(context)
                results.append(result)
            except Exception as exc:
                logger.error("Plugin hook failed", extra={"hook": hook.name, "error": str(exc)})
        return results

    def get_state(self, plugin_name: str) -> str | None:
        return self._plugin_states.get(plugin_name)

    def set_state(self, plugin_name: str, state: str) -> None:
        self._plugin_states[plugin_name] = state

    def publish_event(self, event_name: str, data: dict[str, Any]) -> None:
        eb = self._kernel.get_component("event_bus")
        if eb:
            from app.kernel.event_bus.events import Event

            eb.publish(Event(name=event_name, data=data, source="plugin_api"))
        else:
            logger.warning(
                "Event bus not available for event publishing", extra={"event": event_name},
            )

    def get_service(self, name: str) -> Any | None:
        return self._kernel.get_service(name)

    def get_component(self, name: str) -> Any | None:
        return self._kernel.get_component(name)


class ModuleRuntimeAPI:
    def __init__(self, kernel: Kernel):
        self._kernel = kernel
        self._modules: dict[str, ModuleRegistration] = {}

    def register(self, registration: ModuleRegistration) -> None:
        if registration.name in self._modules:
            logger.warning(
                "Module already registered, updating", extra={"module": registration.name},
            )
        self._modules[registration.name] = registration
        logger.info(
            "Module registered",
            extra={"module": registration.name, "version": registration.version},
        )

    def unregister(self, name: str) -> bool:
        if name in self._modules:
            del self._modules[name]
            return True
        return False

    def get(self, name: str) -> ModuleRegistration | None:
        return self._modules.get(name)

    def list_modules(self) -> list[ModuleRegistration]:
        return list(self._modules.values())

    def enable(self, name: str) -> bool:
        mod = self._modules.get(name)
        if mod:
            mod.enabled = True
            return True
        return False

    def disable(self, name: str) -> bool:
        mod = self._modules.get(name)
        if mod:
            mod.enabled = False
            return True
        return False


class WorkflowRuntimeAPI:
    def __init__(self, kernel: Kernel):
        self._kernel = kernel
        self._workflows: dict[str, WorkflowInstance] = {}
        self._step_registry: dict[str, type[WorkflowStep]] = {}

    def create_workflow(
        self, name: str, steps: list[WorkflowStep], saga: bool = False,
    ) -> WorkflowInstance:
        wf = WorkflowInstance(name=name, steps=steps, saga=saga)
        self._workflows[wf.id] = wf
        logger.info(
            "Workflow created", extra={"id": wf.id, "name": name, "steps": len(steps), "saga": saga},
        )
        return wf

    def execute_step(self, workflow_id: str, context: dict[str, Any]) -> dict[str, Any] | None:
        wf = self._workflows.get(workflow_id)
        if not wf or wf.is_complete():
            return None
        if wf.current_step >= len(wf.steps):
            wf.status = "completed"
            wf.completed_at = time.time()
            return None

        step = wf.steps[wf.current_step]
        wf.state.update(context)
        try:
            result = step.handler(wf.state) if step.handler else wf.state
            wf.current_step += 1
            if wf.current_step >= len(wf.steps):
                wf.status = "completed"
                wf.completed_at = time.time()
            return result
        except Exception as exc:
            wf.status = "failed"
            wf.error = str(exc)
            if wf.saga:
                self._compensate(wf)
            return None

    def _compensate(self, wf: WorkflowInstance) -> None:
        for step in reversed(wf.steps[: wf.current_step]):
            if step.compensation:
                try:
                    step.compensation(wf.state)
                except Exception as exc:
                    logger.error(
                        "Compensation failed",
                        extra={"workflow": wf.id, "step": step.name, "error": str(exc)},
                    )
        wf.status = "compensated"
        wf.completed_at = time.time()

    def get_workflow(self, workflow_id: str) -> WorkflowInstance | None:
        return self._workflows.get(workflow_id)

    def list_workflows(self) -> list[WorkflowInstance]:
        return list(self._workflows.values())


class ObservabilityAPI:
    def __init__(self, kernel: Kernel):
        self._kernel = kernel
        self._metrics: dict[str, list[float]] = {}
        self._max_metrics: int = 10000

    def emit_metric(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        if name not in self._metrics:
            self._metrics[name] = []
        self._metrics[name].append(value)
        if len(self._metrics[name]) > self._max_metrics:
            self._metrics[name].pop(0)

    def emit_trace(
        self, name: str, duration_ms: float, attributes: dict[str, Any] | None = None,
    ) -> None:
        observer = self._kernel.get_component("runtime_observer")
        if observer:
            span = observer.start_trace(name=name, service="sdk")
            span.finish("ok" if duration_ms < 1000 else "slow")
            span.duration_ms = duration_ms
            if attributes:
                span.attributes.update(attributes)
            observer.end_trace(span.span_id)
        else:
            logger.debug(
                "Trace emitted (no observer)", extra={"name": name, "duration_ms": duration_ms},
            )

    def emit_log(self, level: str, message: str, extra: dict[str, Any] | None = None) -> None:
        observer = self._kernel.get_component("runtime_observer")
        if observer:
            observer.record_log(level, message, extra)
        else:
            log_fn = getattr(logger, level.lower(), logger.info)
            log_fn(message, extra=(extra or {}))

    def get_metrics_snapshot(self) -> dict[str, Any]:
        snapshot = {}
        for name, values in self._metrics.items():
            if values:
                snapshot[name] = {
                    "count": len(values),
                    "min": round(min(values), 2),
                    "max": round(max(values), 2),
                    "avg": round(sum(values) / len(values), 2),
                }
        return snapshot


class RuntimeSDK:
    def __init__(self, kernel: Kernel):
        self._kernel = kernel
        self.plugins = PluginRuntimeAPI(kernel)
        self.modules = ModuleRuntimeAPI(kernel)
        self.workflows = WorkflowRuntimeAPI(kernel)
        self.observability = ObservabilityAPI(kernel)

    def emit_metric(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        self.observability.emit_metric(name, value, tags)

    def emit_log(self, level: str, message: str, extra: dict[str, Any] | None = None) -> None:
        self.observability.emit_log(level, message, extra)

    def get_service(self, name: str) -> Any | None:
        return self._kernel.get_service(name)

    def get_component(self, name: str) -> Any | None:
        return self._kernel.get_component(name)

    def register_service(self, name: str, service: Any) -> None:
        self._kernel.register_service(name, service)

    def publish_event(self, event_name: str, data: dict[str, Any]) -> None:
        eb = self._kernel.get_component("event_bus")
        if eb:
            from app.kernel.event_bus.events import Event

            eb.publish(Event(name=event_name, data=data, source="sdk"))

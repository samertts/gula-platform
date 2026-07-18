import logging
from typing import Any

from platform.core.workflow.context import WorkflowContext
from platform.core.workflow.step import StepResult, StepStatus, WorkflowStep


class WorkflowEngine:
    def __init__(self):
        self._logger = logging.getLogger("gula.workflow")
        self._workflows: dict[str, list[WorkflowStep]] = {}
        self._history: dict[str, list[dict[str, Any]]] = {}

    def define(self, name: str, steps: list[WorkflowStep]) -> None:
        self._workflows[name] = steps
        self._logger.info("Workflow defined: %s (%d steps)", name, len(steps))

    def get_workflow(self, name: str) -> list[WorkflowStep] | None:
        return self._workflows.get(name)

    def defined_workflows(self) -> list[str]:
        return list(self._workflows.keys())

    async def execute(self, name: str, initial_data: dict[str, Any] | None = None) -> WorkflowContext:
        steps = self._workflows.get(name)
        if not steps:
            raise ValueError(f"Unknown workflow: {name}")

        context = WorkflowContext(workflow_name=name)
        if initial_data:
            context.data.update(initial_data)

        step_results = []
        for step in steps:
            self._logger.debug("Executing step: %s", step.name)
            try:
                result = await step.execute(context.data)
                step_results.append({
                    "step": step.name,
                    "status": result.status.value,
                    "error": result.error,
                })
                if result.status == StepStatus.FAILED:
                    self._logger.error("Workflow '%s' failed at step '%s': %s",
                                       name, step.name, result.error)
                    break
                if result.data:
                    context.data.update(result.data)
            except Exception as e:
                self._logger.error("Workflow '%s' exception at step '%s': %s",
                                   name, step.name, e)
                step_results.append({
                    "step": step.name,
                    "status": StepStatus.FAILED.value,
                    "error": str(e),
                })
                break

        self._history.setdefault(name, []).append({
            "workflow_id": context.workflow_id,
            "steps": step_results,
        })
        return context

    def get_history(self, name: str) -> list[dict[str, Any]]:
        return list(self._history.get(name, []))

    def clear_history(self, name: str | None = None) -> None:
        if name:
            self._history.pop(name, None)
        else:
            self._history.clear()

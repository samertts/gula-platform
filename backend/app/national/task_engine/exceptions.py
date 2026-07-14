from __future__ import annotations


class TaskEngineError(Exception):
    pass


class TaskNotFoundError(TaskEngineError):
    def __init__(self, task_id: str) -> None:
        self.task_id = task_id
        super().__init__(f"Task not found: {task_id}")


class TaskQueueNotFoundError(TaskEngineError):
    def __init__(self, queue_id: str) -> None:
        self.queue_id = queue_id
        super().__init__(f"Task queue not found: {queue_id}")


class TaskInvalidTransitionError(TaskEngineError):
    def __init__(self, task_id: str, current: str, target: str) -> None:
        self.task_id = task_id
        self.current = current
        self.target = target
        super().__init__(f"Invalid task transition: {task_id} from {current} to {target}")


class TaskSLABreachError(TaskEngineError):
    def __init__(self, task_id: str, sla_due_at: str) -> None:
        self.task_id = task_id
        self.sla_due_at = sla_due_at
        super().__init__(f"Task SLA breached: {task_id} due at {sla_due_at}")


class TaskAssignmentError(TaskEngineError):
    def __init__(self, task_id: str, reason: str) -> None:
        self.task_id = task_id
        self.reason = reason
        super().__init__(f"Task assignment error: {task_id}: {reason}")

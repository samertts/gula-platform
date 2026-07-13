"""GULA Platform — async task queue.

Public surface:
    from app.tasks.schema   import TaskPayload, TaskStatus, TaskResult
    from app.tasks.queue    import task_queue
    from app.tasks.registry import task_handler, get_handler
    from app.tasks.worker   import TaskWorker
"""

from .queue import task_queue
from .registry import get_handler, task_handler
from .schema import TaskPayload, TaskResult, TaskStatus
from .worker import TaskWorker

__all__ = [
    "TaskPayload",
    "TaskResult",
    "TaskStatus",
    "TaskWorker",
    "get_handler",
    "task_handler",
    "task_queue",
]

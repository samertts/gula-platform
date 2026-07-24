from __future__ import annotations

import pytest
from app.kernel.background.task_queue import Task, TaskQueue


class TestTaskQueue:
    def test_enqueue_and_dequeue(self):
        tq = TaskQueue()
        task = Task(id="t1", name="process", handler=lambda: None)
        tq.enqueue(task)
        assert tq.size() == 1
        dequeued = tq.dequeue()
        assert dequeued is not None
        assert dequeued.name == "process"

    def test_priority_ordering(self):
        tq = TaskQueue()
        tq.enqueue(Task(id="low", name="low", handler=lambda: None, priority=1))
        tq.enqueue(Task(id="high", name="high", handler=lambda: None, priority=10))
        assert tq.dequeue().name == "high"
        assert tq.dequeue().name == "low"

    def test_empty(self):
        tq = TaskQueue()
        assert tq.dequeue() is None
        assert tq.size() == 0

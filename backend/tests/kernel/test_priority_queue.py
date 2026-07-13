from __future__ import annotations

import pytest

from backend.app.kernel.background.priority_queue import PriorityQueue, PriorityTask


class TestPriorityQueue:
    def test_priority_ordering(self):
        pq = PriorityQueue()
        pq.push(PriorityTask(priority=1, name="low"))
        pq.push(PriorityTask(priority=10, name="high"))
        pq.push(PriorityTask(priority=5, name="medium"))
        assert pq.pop().name == "high"
        assert pq.pop().name == "medium"
        assert pq.pop().name == "low"

    def test_empty(self):
        pq = PriorityQueue()
        assert pq.pop() is None
        assert pq.peek() is None
        assert pq.size() == 0

    def test_peek(self):
        pq = PriorityQueue()
        assert pq.peek() is None
        pq.push(PriorityTask(priority=5, name="test"))
        assert pq.peek().name == "test"
        assert pq.size() == 1

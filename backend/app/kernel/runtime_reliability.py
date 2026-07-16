from __future__ import annotations

import asyncio
import logging
import pickle
import threading
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from app.kernel import Kernel

logger = logging.getLogger("gula.kernel.runtime_reliability")


class ShutdownPriority(Enum):
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    LOWEST = 4


@dataclass
class ShutdownTask:
    name: str
    handler: Callable[[], Any]
    priority: ShutdownPriority = ShutdownPriority.NORMAL
    timeout: float = 30.0
    component: str = ""
    depends_on: list[str] = field(default_factory=list)


@dataclass
class Checkpoint:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    component: str = ""
    state: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    version: int = 1


@dataclass
class RecoveredState:
    component: str
    checkpoint: Checkpoint | None
    recovered: bool
    replay_events: list[dict[str, Any]] = field(default_factory=list)
    recovery_time_ms: float = 0.0
    message: str = ""


class GracefulShutdown:
    def __init__(self, shutdown_timeout: float = 30.0):
        self._tasks: list[ShutdownTask] = []
        self._shutdown_timeout = shutdown_timeout
        self._is_shutting_down = False
        self._shutdown_completed = asyncio.Event()
        self._lock = threading.Lock()

    def register(self, task: ShutdownTask) -> None:
        with self._lock:
            self._tasks.append(task)
            self._tasks.sort(key=lambda t: t.priority.value)

    def unregister(self, name: str) -> bool:
        with self._lock:
            before = len(self._tasks)
            self._tasks = [t for t in self._tasks if t.name != name]
            return len(self._tasks) < before

    async def shutdown(self) -> dict[str, Any]:
        self._is_shutting_down = True
        results: dict[str, Any] = {}
        logger.info("Graceful shutdown starting with %d tasks", len(self._tasks))

        for task in self._tasks:
            start = time.monotonic()
            try:
                result = task.handler()
                if hasattr(result, "__await__"):
                    await asyncio.wait_for(result, timeout=task.timeout)
                elapsed = time.monotonic() - start
                results[task.name] = {"status": "completed", "duration_ms": round(elapsed * 1000)}
                logger.info("Shutdown task completed", extra={"task": task.name, "duration_ms": round(elapsed * 1000)})
            except TimeoutError:
                results[task.name] = {"status": "timeout", "duration_ms": task.timeout * 1000}
                logger.warning("Shutdown task timed out", extra={"task": task.name, "timeout": task.timeout})
            except Exception as exc:
                results[task.name] = {"status": "error", "error": str(exc)}
                logger.error("Shutdown task failed", extra={"task": task.name, "error": str(exc)})

        self._is_shutting_down = False
        self._shutdown_completed.set()
        logger.info("Graceful shutdown complete")
        return results

    @property
    def is_active(self) -> bool:
        return self._is_shutting_down


class StateRecovery:
    def __init__(self, checkpoint_dir: str = "/var/lib/gula/kernel/checkpoints"):
        self._checkpoint_dir = Path(checkpoint_dir)
        self._checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self._checkpoints: dict[str, Checkpoint] = {}
        self._replay_queue: list[dict[str, Any]] = []

    def save_checkpoint(self, component: str, state: dict[str, Any]) -> Checkpoint:
        cp = Checkpoint(component=component, state=state)
        self._checkpoints[component] = cp
        filepath = self._checkpoint_dir / f"{component}_{cp.id}.ckpt"
        try:
            filepath.write_bytes(pickle.dumps({"id": cp.id, "component": cp.component, "state": cp.state, "version": cp.version}))
            logger.info("Checkpoint saved", extra={"component": component, "path": str(filepath)})
        except Exception as exc:
            logger.error("Checkpoint write failed", extra={"component": component, "error": str(exc)})
        return cp

    def load_checkpoint(self, component: str) -> Checkpoint | None:
        cp = self._checkpoints.get(component)
        if cp:
            return cp
        pattern = f"{component}_*.ckpt"
        try:
            files = sorted(self._checkpoint_dir.glob(pattern), key=lambda f: f.stat().st_mtime, reverse=True)
            if files:
                data = pickle.loads(files[0].read_bytes())
                cp = Checkpoint(id=data["id"], component=data["component"], state=data["state"], version=data.get("version", 1))
                self._checkpoints[component] = cp
                return cp
        except Exception as exc:
            logger.error("Checkpoint load failed", extra={"component": component, "error": str(exc)})
        return None

    def recover(self, component: str, replay_events: list[dict[str, Any]] | None = None) -> RecoveredState:
        start = time.monotonic()
        cp = self.load_checkpoint(component)
        if not cp:
            return RecoveredState(
                component=component,
                checkpoint=None,
                recovered=False,
                recovery_time_ms=(time.monotonic() - start) * 1000,
                message="No checkpoint found for recovery",
            )
        events_replayed = replay_events or []
        for event in self._replay_queue:
            if event.get("target") == component:
                events_replayed.append(event)
        duration_ms = (time.monotonic() - start) * 1000
        logger.info("State recovered", extra={"component": component, "duration_ms": round(duration_ms, 1)})
        return RecoveredState(
            component=component,
            checkpoint=cp,
            recovered=True,
            replay_events=events_replayed,
            recovery_time_ms=duration_ms,
            message=f"Recovered from checkpoint v{cp.version} with {len(events_replayed)} replay events",
        )

    def enqueue_replay(self, event: dict[str, Any]) -> None:
        self._replay_queue.append(event)
        if len(self._replay_queue) > 1000:
            self._replay_queue.pop(0)

    def clear_replay_queue(self, component: str | None = None) -> int:
        if component:
            before = len(self._replay_queue)
            self._replay_queue = [e for e in self._replay_queue if e.get("target") != component]
            return before - len(self._replay_queue)
        count = len(self._replay_queue)
        self._replay_queue.clear()
        return count


class QueueRecovery:
    def __init__(self):
        self._lost_messages: dict[str, list[dict[str, Any]]] = {}
        self._recovered_messages: dict[str, int] = {}

    def record_lost(self, queue: str, message: dict[str, Any]) -> None:
        if queue not in self._lost_messages:
            self._lost_messages[queue] = []
        self._lost_messages[queue].append(message)
        if len(self._lost_messages[queue]) > 10000:
            self._lost_messages[queue].pop(0)

    def recover_queue(self, queue: str, replay_fn: Callable[[dict[str, Any]], bool] | None = None) -> dict[str, Any]:
        lost = self._lost_messages.get(queue, [])
        if not lost:
            return {"queue": queue, "recovered": 0, "failed": 0, "total": 0}

        recovered = 0
        failed = 0
        if replay_fn:
            for msg in lost:
                try:
                    if replay_fn(msg):
                        recovered += 1
                    else:
                        failed += 1
                except Exception:
                    failed += 1
        else:
            recovered = len(lost)

        self._recovered_messages[queue] = recovered
        logger.info("Queue recovered", extra={"queue": queue, "recovered": recovered, "failed": failed, "total": len(lost)})
        return {"queue": queue, "recovered": recovered, "failed": failed, "total": len(lost)}

    def get_pending_recovery(self, queue: str | None = None) -> dict[str, int]:
        if queue:
            return {queue: len(self._lost_messages.get(queue, []))}
        return {q: len(msgs) for q, msgs in self._lost_messages.items()}

    def clear_lost(self, queue: str | None = None) -> int:
        if queue:
            count = len(self._lost_messages.get(queue, []))
            self._lost_messages.pop(queue, None)
            return count
        count = sum(len(msgs) for msgs in self._lost_messages.values())
        self._lost_messages.clear()
        return count


class ReliabilityEngine:
    def __init__(self, kernel: Kernel | None = None):
        self._kernel = kernel
        self.shutdown = GracefulShutdown()
        self.state_recovery = StateRecovery()
        self.queue_recovery = QueueRecovery()
        self._recovery_history: list[dict[str, Any]] = []
        self._started_at: float = time.time()
        self._recovery_count: int = 0

    def attempt_recovery(self, component: str, context: dict[str, Any] | None = None) -> RecoveredState:
        self._recovery_count += 1
        state = self.state_recovery.recover(component)
        self._recovery_history.append({
            "timestamp": time.time(),
            "component": component,
            "recovered": state.recovered,
            "duration_ms": round(state.recovery_time_ms, 1),
        })
        if len(self._recovery_history) > 200:
            self._recovery_history.pop(0)
        logger.info("Recovery attempted", extra={"component": component, "success": state.recovered})
        return state

    def get_stats(self) -> dict[str, Any]:
        return {
            "uptime_seconds": round(time.time() - self._started_at, 1),
            "recovery_attempts": self._recovery_count,
            "pending_recovery": self.queue_recovery.get_pending_recovery(),
            "checkpoints": len(self.state_recovery._checkpoints),
            "shutdown_tasks": len(self.shutdown._tasks),
            "replay_queue_size": len(self.state_recovery._replay_queue),
        }

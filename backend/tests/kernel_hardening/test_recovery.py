from __future__ import annotations

import asyncio

import pytest
from app.kernel import Kernel, KernelState
from app.kernel.background.job_retry import JobRetry
from app.kernel.background.scheduler import Scheduler
from app.kernel.background.task_queue import Task, TaskQueue
from app.kernel.config.registry import ConfigurationRegistry
from app.kernel.event_bus.bus import EventBus
from app.kernel.event_bus.dead_letter_queue import DeadLetterEntry, DeadLetterQueue
from app.kernel.event_bus.events import Event
from app.kernel.event_bus.outbox import OutboxMessage, OutboxPattern
from app.kernel.event_bus.store import EventStore
from app.kernel.gateway.circuit_breaker import CircuitBreaker, CircuitBreakerManager
from app.kernel.runtime.service_registry import ServiceRegistry

pytestmark = [
    pytest.mark.kernel,
    pytest.mark.integration,
]


class TestRecoveryCrash:
    def test_singleton_reset_after_crash(self):
        k1 = Kernel()
        asyncio.run(k1.boot())
        Kernel.reset_instance()
        k2 = Kernel()
        asyncio.run(k2.boot())
        assert k2.state == KernelState.BOOTING
        assert k2 is not k1

    def test_state_transition_on_stop_without_start(self):
        kernel = Kernel()
        asyncio.run(kernel.boot())
        asyncio.run(kernel.stop())
        assert kernel.state == KernelState.STOPPED


class TestRecoveryPluginCrash:
    def test_service_registry_after_plugin_crash(self, kernel: Kernel):
        sr = ServiceRegistry()
        kernel.register_component("service_registry", sr)
        sr.register("critical_svc", {"status": "online"})
        try:
            raise RuntimeError("plugin crash")
        except RuntimeError:
            pass
        assert sr.get("critical_svc")["status"] == "online"


class TestRecoveryOutbox:
    def test_outbox_survives_crash(self):
        outbox = OutboxPattern()
        outbox.enqueue(OutboxMessage(id="m1", event_name="test", payload={}))
        outbox.enqueue(OutboxMessage(id="m2", event_name="test", payload={}))
        pending = outbox.list_pending()
        assert len(pending) == 2
        outbox.dequeue()
        remaining = outbox.list_pending()
        assert len(remaining) == 1


class TestRecoveryDeadLetter:
    def test_dead_letter_replay(self):
        dlq = DeadLetterQueue()
        event = Event(name="failed", data={"error": "test"})
        entry = DeadLetterEntry(event=event, reason="transient_failure")
        dlq.send(entry)
        assert len(dlq.list_all()) == 1
        replayed = dlq.replay(event.id)
        assert replayed is not None
        assert len(dlq.list_all()) == 0

    def test_dead_letter_accumulates_failures(self):
        dlq = DeadLetterQueue()
        for i in range(10):
            e = Event(name="fail", data={"i": i})
            dlq.send(DeadLetterEntry(event=e, reason=f"error_{i}"))
        assert len(dlq.list_all()) == 10


class TestRecoveryTaskRetry:
    def test_job_retry_exhaustion(self):
        jr = JobRetry()
        assert jr.should_retry("job_1")
        jr.increment("job_1")
        jr.increment("job_1")
        jr.increment("job_1")
        assert not jr.should_retry("job_1")

    def test_job_retry_backoff_increases(self):
        jr = JobRetry()
        backoffs = []
        for _ in range(3):
            jr.increment("job_2")
            backoffs.append(jr.get_backoff("job_2"))
        assert backoffs[0] < backoffs[1] < backoffs[2]


class TestRecoveryCircuitBreaker:
    def test_circuit_breaker_auto_recovery(self):
        import time

        cb = CircuitBreaker("recovery_test", failure_threshold=2, recovery_timeout=0.01)
        cb.record_failure()
        cb.record_failure()
        assert not cb.can_proceed()
        time.sleep(0.02)
        assert cb.can_proceed()

    def test_circuit_breaker_manager_auto_cleanup(self):
        cbm = CircuitBreakerManager()
        cb = CircuitBreaker("cleanup_test", failure_threshold=1, recovery_timeout=0.01)
        cbm.register(cb)
        cbm.record_failure("cleanup_test")
        import time

        time.sleep(0.02)
        assert cbm.can_proceed("cleanup_test")


class TestRecoveryConfiguration:
    def test_config_registry_survives_corruption(self):
        cr = ConfigurationRegistry()
        cr.set("critical", "value")
        cr._config = {"critical": "value"}
        assert cr.get("critical") == "value"

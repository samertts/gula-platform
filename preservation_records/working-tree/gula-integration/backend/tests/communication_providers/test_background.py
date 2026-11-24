"""Background dispatcher tests: submit, status tracking, cancellation,
failure capture (PROGRAM-COMM-002).

Deterministic by construction: worker jobs are gated with threading.Event so
assertions never race the thread pool.
"""

from __future__ import annotations

import threading
import time

from shared.communication_providers.background import BackgroundDispatcher

_POLL_TIMEOUT = 5.0


def _wait_status(dispatcher: BackgroundDispatcher, ref: str, status: str) -> None:
    deadline = time.time() + _POLL_TIMEOUT
    record = dispatcher.status(ref)
    while record is None or record.status != status:
        if time.time() > deadline:
            raise AssertionError(f"timed out waiting for {ref} to be {status}")
        time.sleep(0.005)
        record = dispatcher.status(ref)


class TestBackgroundDispatcher:
    def test_submit_and_complete(self):
        dispatcher = BackgroundDispatcher(provider="tg", max_workers=2)
        gate = threading.Event()

        def work():
            gate.wait(timeout=_POLL_TIMEOUT)
            return True

        record = dispatcher.submit("r1", work)
        assert dispatcher.status("r1") is record
        assert record.status in ("queued", "running")  # not delivered yet
        gate.set()
        _wait_status(dispatcher, "r1", "delivered")
        dispatcher.shutdown()

    def test_failure_captured(self):
        dispatcher = BackgroundDispatcher(provider="tg", max_workers=2)

        def boom():
            raise RuntimeError("boom")

        dispatcher.submit("r1", boom)
        _wait_status(dispatcher, "r1", "failed")
        status = dispatcher.status("r1")
        assert "boom" in (status.error or "")  # type: ignore[union-attr]
        dispatcher.shutdown()

    def test_false_result_marks_failed(self):
        dispatcher = BackgroundDispatcher(provider="tg", max_workers=2)
        dispatcher.submit("r1", lambda: False)
        _wait_status(dispatcher, "r1", "failed")
        dispatcher.shutdown()

    def test_cancel_queued(self):
        dispatcher = BackgroundDispatcher(provider="tg", max_workers=1)
        gate = threading.Event()
        dispatcher.submit("slow", lambda: gate.wait(timeout=_POLL_TIMEOUT) or True)
        # Wait until the single worker is occupied by "slow", then queue a
        # second delivery behind it so we can cancel it while still queued.
        _wait_status(dispatcher, "slow", "running")
        dispatcher.submit("queued2", lambda: True)
        assert dispatcher.cancel("queued2") is True
        assert dispatcher.status("queued2").status == "cancelled"  # type: ignore[union-attr]
        gate.set()
        dispatcher.shutdown()

    def test_cancel_unknown_returns_false(self):
        dispatcher = BackgroundDispatcher(provider="tg", max_workers=1)
        assert dispatcher.cancel("ghost") is False
        dispatcher.shutdown()

    def test_snapshot_shape(self):
        dispatcher = BackgroundDispatcher(provider="tg", max_workers=1)
        dispatcher.submit("r1", lambda: True)
        _wait_status(dispatcher, "r1", "delivered")
        snapshot = dispatcher.snapshot()
        assert snapshot[0]["delivery_ref"] == "r1"
        assert snapshot[0]["provider"] == "tg"
        dispatcher.shutdown()

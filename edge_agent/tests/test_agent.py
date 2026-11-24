"""EdgeAgent: sandbox enforcement (kind allowlist, payload size, timeout)
and resource gating — previously zero test coverage on the module whose
own docstring calls these out as the security-relevant rules ("Sandboxing
rules enforced here (NOT delegated to the runtime)").
"""
from __future__ import annotations

import asyncio

import pytest
from gula_edge_agent.agent import EdgeAgent
from gula_edge_agent.runtime import Runtime
from gula_edge_agent.state import AgentState


class RecordingRuntime(Runtime):
    def __init__(self, *, delay: float = 0.0, result: dict | None = None):
        self.delay = delay
        self.result = result if result is not None else {"ok": True}
        self.calls: list[tuple[str, dict]] = []

    async def run(self, kind, payload):
        self.calls.append((kind, payload))
        if self.delay:
            await asyncio.sleep(self.delay)
        return self.result


def _make_agent(tmp_path, runtime, **overrides):
    state = AgentState(str(tmp_path))
    state.set(device_id="DEV-1", agent_token="tok-abc")
    agent = EdgeAgent(
        backend_url="http://backend.invalid", edge_path="/edge",
        state=state, runtime=runtime, **overrides,
    )
    reported: list[dict] = []

    async def _fake_post(path, body, *, timeout=30.0):
        reported.append({"path": path, "body": body})
        return {}

    agent._post = _fake_post  # type: ignore[method-assign]
    return agent, reported


def test_unknown_kind_is_rejected_without_reaching_the_runtime(tmp_path):
    runtime = RecordingRuntime()
    agent, reported = _make_agent(tmp_path, runtime)

    asyncio.run(agent._execute_task({
        "task_uid": "T-1", "kind": "shell.exec", "payload": {}, "timeout_s": 5,
    }))

    assert runtime.calls == []  # sandbox must stop it before the runtime sees it
    assert reported[0]["body"]["success"] is False
    assert "rejects unknown kind" in reported[0]["body"]["error"]


def test_oversized_payload_is_rejected_without_reaching_the_runtime(tmp_path):
    runtime = RecordingRuntime()
    agent, reported = _make_agent(tmp_path, runtime)

    huge_text = "x" * (300 * 1024)  # > MAX_PAYLOAD_BYTES (256 KiB)
    asyncio.run(agent._execute_task({
        "task_uid": "T-2", "kind": "diag.ping",
        "payload": {"text": huge_text}, "timeout_s": 5,
    }))

    assert runtime.calls == []
    assert reported[0]["body"]["success"] is False
    assert "payload too large" in reported[0]["body"]["error"]


def test_allowed_kind_within_size_reaches_the_runtime_and_reports_success(tmp_path):
    runtime = RecordingRuntime(result={"pong": True})
    agent, reported = _make_agent(tmp_path, runtime)

    asyncio.run(agent._execute_task({
        "task_uid": "T-3", "kind": "diag.ping", "payload": {}, "timeout_s": 5,
    }))

    assert runtime.calls == [("diag.ping", {})]
    assert reported[0]["body"]["success"] is True
    assert reported[0]["body"]["result"] == {"pong": True}
    assert reported[0]["body"]["duration_ms"] >= 0


def test_runtime_exceeding_timeout_s_is_reported_as_failed_not_hung_forever(tmp_path):
    runtime = RecordingRuntime(delay=1.0)
    agent, reported = _make_agent(tmp_path, runtime)

    asyncio.run(agent._execute_task({
        "task_uid": "T-4", "kind": "diag.ping", "payload": {}, "timeout_s": 0,
    }))

    assert reported[0]["body"]["success"] is False
    assert "timeout" in reported[0]["body"]["error"]


@pytest.mark.parametrize(
    "telemetry, expected_ok",
    [
        ({"cpu_pct": 10.0}, True),
        ({"cpu_pct": 95.0}, False),  # above default cpu_cap_pct=60
        ({"on_battery": True, "battery_pct": 10.0}, False),  # below default floor=30
        ({"on_battery": True, "battery_pct": 80.0}, True),
        ({"on_battery": False, "battery_pct": 5.0}, True),  # plugged in -> floor doesn't apply
    ],
)
def test_can_take_work_resource_gate(tmp_path, telemetry, expected_ok):
    agent, _ = _make_agent(tmp_path, RecordingRuntime())
    ok, _reason = agent._can_take_work(telemetry)
    assert ok is expected_ok

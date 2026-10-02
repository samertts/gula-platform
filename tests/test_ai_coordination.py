from __future__ import annotations

import pytest

from tools.ai_coordination.coordination import (
    AgentCoordinator,
    AgentIdentity,
    CoordinationConflict,
)


def _agent(agent_id: str, branch: str) -> AgentIdentity:
    return AgentIdentity(agent_id, "claude", "test-model", f"session-{agent_id}", branch, "abc123")


def test_agents_claim_tasks_and_cannot_claim_same_task(tmp_path) -> None:
    coordinator = AgentCoordinator(tmp_path / "coord.sqlite3")
    coordinator.register_agent(_agent("claude-a", "work/claude-a"))
    coordinator.register_agent(_agent("claude-b", "work/claude-b"))
    task_id = coordinator.create_task("Improve gateway", "Add tests", "human")
    claim = coordinator.claim_task(task_id, "claude-a")

    with pytest.raises(CoordinationConflict, match="already claimed"):
        coordinator.claim_task(task_id, "claude-b")

    coordinator.release_task(claim, "done")
    assert coordinator.status()["counts"]["claims"] == 0


def test_overlapping_file_intents_are_rejected_until_closed(tmp_path) -> None:
    coordinator = AgentCoordinator(tmp_path / "coord.sqlite3")
    coordinator.register_agent(_agent("claude-a", "work/claude-a"))
    coordinator.register_agent(_agent("claude-b", "work/claude-b"))
    first = coordinator.declare_intent("task-a", "claude-a", ["backend/app/ai/orchestrator.py"], "modify", "abc")

    with pytest.raises(CoordinationConflict, match="path overlap"):
        coordinator.declare_intent("task-b", "claude-b", ["backend/app/ai"], "modify", "abc")

    coordinator.close_intent(first.intent_id, "claude-a")
    second = coordinator.declare_intent("task-b", "claude-b", ["backend/app/ai"], "review", "abc")
    assert second.status == "active"


def test_messages_are_shared_and_marked_read(tmp_path) -> None:
    coordinator = AgentCoordinator(tmp_path / "coord.sqlite3")
    coordinator.register_agent(_agent("claude-a", "work/claude-a"))
    coordinator.register_agent(_agent("claude-b", "work/claude-b"))
    message_id = coordinator.send_message("claude-a", {"commit": "abc", "tests": "pass"}, "claude-b", "handoff")
    messages = coordinator.receive_messages("claude-b")
    assert messages[0]["message_id"] == message_id
    assert messages[0]["body"]["commit"] == "abc"
    assert coordinator.receive_messages("claude-b") == []


def test_protected_branches_are_rejected(tmp_path) -> None:
    coordinator = AgentCoordinator(tmp_path / "coord.sqlite3")
    with pytest.raises(Exception, match="protected branch"):
        coordinator.register_agent(_agent("unsafe", "main"))

"""Phase 1 — Execution State.

One global execution state for the whole platform. Tracks the current
mission, mission history, running/completed/waiting/blocked tasks, engine
status, execution context, context/resource budgets, health, locks, current
owner, current authority, the execution timeline, and the checkpoint pointer.
"""

from __future__ import annotations

from .core import (
    STATE_DIR,
    ExecutionState,
    MissionStatus,
    Task,
    TaskStatus,
    read_json,
    utcnow,
    write_json,
)

STATE_FILE = STATE_DIR / "execution_state.json"
TASKS_FILE = STATE_DIR / "tasks.json"


def _empty_state() -> ExecutionState:
    return ExecutionState()


def load_state() -> ExecutionState:
    """Load the global execution state (or a fresh empty state)."""
    data = read_json(STATE_FILE)
    state = ExecutionState()
    for field_name in ("current_mission", "health", "current_owner",
                       "current_authority", "checkpoint_pointer", "updated_at"):
        if field_name in data:
            setattr(state, field_name, data[field_name])
    for field_name in ("mission_history", "running_tasks", "completed_tasks",
                       "waiting_tasks", "blocked_tasks", "locks", "execution_timeline"):
        if field_name in data:
            setattr(state, field_name, list(data[field_name]))
    if "engine_status" in data:
        state.engine_status = dict(data["engine_status"])
    if "execution_context" in data:
        state.execution_context = dict(data["execution_context"])
    if "context_budget" in data:
        state.context_budget = dict(data["context_budget"])
    if "resource_budget" in data:
        state.resource_budget = dict(data["resource_budget"])
    return state


def save_state(state: ExecutionState) -> None:
    """Persist the global execution state."""
    write_json(STATE_FILE, state.to_dict())


def start_mission(state: ExecutionState, mission_id: str, owner: str, authority: str) -> ExecutionState:
    """Begin a new mission, recording it as current and in history."""
    state.current_mission = mission_id
    if mission_id not in state.mission_history:
        state.mission_history.append(mission_id)
    state.current_owner = owner
    state.current_authority = authority
    state.health = "running"
    state.updated_at = utcnow()
    state.execution_timeline.append(f"{utcnow()} mission.started {mission_id}")
    return state


def complete_mission(state: ExecutionState, mission_id: str) -> ExecutionState:
    """Mark the current mission completed and reset the current pointer."""
    state.health = "healthy"
    state.updated_at = utcnow()
    state.execution_timeline.append(f"{utcnow()} mission.completed {mission_id}")
    return state


def record_task(state: ExecutionState, task: Task) -> ExecutionState:
    """Move a task into the appropriate bucket of the global state."""
    if task.status == TaskStatus.RUNNING.value:
        _move(state, task.task_id, state.running_tasks, "running")
    elif task.status == TaskStatus.COMPLETED.value:
        _move(state, task.task_id, state.completed_tasks, "completed")
    elif task.status == TaskStatus.BLOCKED.value:
        _move(state, task.task_id, state.blocked_tasks, "blocked")
    elif task.status == TaskStatus.FAILED.value:
        state.blocked_tasks = [t for t in state.blocked_tasks if t != task.task_id]
        state.running_tasks = [t for t in state.running_tasks if t != task.task_id]
    else:  # WAITING
        _move(state, task.task_id, state.waiting_tasks, "waiting")
    state.updated_at = utcnow()
    state.execution_timeline.append(f"{utcnow()} task.{task.status} {task.task_id}")
    return state


def _move(state: ExecutionState, task_id: str, bucket: list[str], label: str) -> None:
    for other in (state.running_tasks, state.completed_tasks,
                  state.waiting_tasks, state.blocked_tasks):
        if task_id in other and other is not bucket:
            other.remove(task_id)
    if task_id not in bucket:
        bucket.append(task_id)


def set_checkpoint_pointer(state: ExecutionState, phase: str, path: str) -> ExecutionState:
    """Update the checkpoint pointer after a checkpoint is created."""
    state.checkpoint_pointer = f"{phase}:{path}"
    state.updated_at = utcnow()
    return state


def load_tasks() -> list[Task]:
    data = read_json(TASKS_FILE)
    return [Task(**raw) for raw in data.get("tasks", [])]


def save_tasks(tasks: list[Task]) -> None:
    write_json(TASKS_FILE, {"tasks": [vars(t) for t in tasks]})


def add_task(tasks: list[Task], task: Task) -> list[Task]:
    tasks.append(task)
    return tasks


def snapshot_summary(state: ExecutionState) -> dict[str, object]:
    """Return a compact human-readable snapshot of the execution state."""
    return {
        "current_mission": state.current_mission,
        "mission_history": state.mission_history,
        "running_tasks": state.running_tasks,
        "completed_tasks": state.completed_tasks,
        "waiting_tasks": state.waiting_tasks,
        "blocked_tasks": state.blocked_tasks,
        "health": state.health,
        "current_owner": state.current_owner,
        "current_authority": state.current_authority,
        "checkpoint_pointer": state.checkpoint_pointer,
        "mission_status": MissionStatus.RUNNING.value if state.current_mission else MissionStatus.QUEUED.value,
    }

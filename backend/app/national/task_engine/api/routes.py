from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from app.national.task_engine.application.service import TaskEngineService
from app.national.task_engine.domain.entities import (
    NationalTask,
    TaskQueue,
    TaskSLADefinition,
)
from app.national.task_engine.domain.enums import (
    TaskCategory,
    TaskPriority,
)
from app.national.task_engine.exceptions import TaskFieldNotUpdatableError
from app.national.task_engine.infrastructure.repository import (
    SQLAlchemyNationalTaskRepository,
    SQLAlchemyTaskAssignmentRepository,
    SQLAlchemyTaskAuditLogRepository,
    SQLAlchemyTaskCommentRepository,
    SQLAlchemyTaskEscalationRepository,
    SQLAlchemyTaskQueueRepository,
    SQLAlchemyTaskSLARepository,
)
from app.security.dependencies import get_current_user, require_permission


def _actor(current_user: Any) -> str | None:
    """The authenticated caller, and the only source of an actor on this router.

    NR-070: `assigned_by` came from the request body while `current_user` sat on
    the same handler, so an audit reader could be told anything. Every actor
    field on this router is now resolved here.
    """
    actor = getattr(current_user, "id", None)
    return str(actor) if actor is not None else None

#: NR-070. The permission is not new. Every one of the thirteen national
#: routers that guards itself guards itself with exactly this string, at the
#: router rather than the handler, and no other permission string appears
#: anywhere in `app/national`. Reuse, not invention.
router = APIRouter(
    prefix="/national/tasks",
    tags=["National Task Engine"],
    dependencies=[Depends(require_permission("system:admin"))],
)


def _get_service() -> TaskEngineService:
    return TaskEngineService(
        task_repo=SQLAlchemyNationalTaskRepository(),
        queue_repo=SQLAlchemyTaskQueueRepository(),
        assignment_repo=SQLAlchemyTaskAssignmentRepository(),
        escalation_repo=SQLAlchemyTaskEscalationRepository(),
        sla_repo=SQLAlchemyTaskSLARepository(),
        comment_repo=SQLAlchemyTaskCommentRepository(),
        audit_repo=SQLAlchemyTaskAuditLogRepository(),
    )


@router.post("/")
def create_task(data: dict, current_user: Any = Depends(get_current_user)):
    svc = _get_service()
    task = NationalTask(
        id=str(uuid.uuid4()),
        title=data["title"],
        description=data.get("description", ""),
        priority=TaskPriority(data.get("priority", "medium")),
        category=TaskCategory(data.get("category", "general")),
        task_type=data.get("task_type", "general"),
        queue_id=data.get("queue_id"),
        sla_due_at=None,
        tags=data.get("tags", []),
        metadata=data.get("metadata", {}),
        correlation_id=data.get("correlation_id"),
        created_by=_actor(current_user),
    )
    result = svc.create_task(task, _actor(current_user))
    return {"success": True, "id": result.id}


@router.post("/bulk")
def bulk_create(data: list[dict], current_user: Any = Depends(get_current_user)):
    svc = _get_service()
    tasks = []
    for item in data:
        task = NationalTask(
            id=str(uuid.uuid4()),
            title=item["title"],
            description=item.get("description", ""),
            priority=TaskPriority(item.get("priority", "medium")),
            category=TaskCategory(item.get("category", "general")),
            queue_id=item.get("queue_id"),
            tags=item.get("tags", []),
            created_by=_actor(current_user),
        )
        tasks.append(task)
    results = svc.bulk_create(tasks, _actor(current_user))
    return {"success": True, "count": len(results), "ids": [r.id for r in results]}


@router.get("/")
def list_tasks(
    status: str | None = Query(None),
    priority: str | None = Query(None),
    category: str | None = Query(None),
    assignee: str | None = Query(None),
    queue_id: str | None = Query(None),
    search: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: Any = Depends(get_current_user),
):
    svc = _get_service()
    filters = {}
    if status:
        filters["status"] = status
    if priority:
        filters["priority"] = priority
    if category:
        filters["category"] = category
    if assignee:
        filters["assignee"] = assignee
    if queue_id:
        filters["queue_id"] = queue_id
    if search:
        filters["search"] = search
    tasks = svc.list_tasks(skip=skip, limit=limit, filters=filters)
    return {"items": tasks, "total": len(tasks), "skip": skip, "limit": limit}


@router.get("/dashboard")
def get_dashboard(current_user: Any = Depends(get_current_user)):
    svc = _get_service()
    return svc.get_dashboard()


@router.get("/{task_id}")
def get_task(task_id: str, current_user: Any = Depends(get_current_user)):
    svc = _get_service()
    task = svc.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/{task_id}")
def update_task(
    task_id: str, data: dict, current_user: Any = Depends(get_current_user),
):
    svc = _get_service()
    try:
        task = svc.update_task(task_id, data, _actor(current_user))
    except TaskFieldNotUpdatableError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"success": True, "id": task.id}


@router.delete("/{task_id}")
def delete_task(task_id: str, current_user: Any = Depends(get_current_user)):
    svc = _get_service()
    try:
        svc.delete_task(task_id)
        return {"success": True}
    except ValueError as e:
        raise HTTPException(status_code=409, detail="Resource conflict") from e


@router.post("/{task_id}/assign")
def assign_task(
    task_id: str, data: dict, current_user: Any = Depends(get_current_user),
):
    svc = _get_service()
    result = svc.assign_task(
        task_id, data["assignee_id"], _actor(current_user),
    )
    return {"success": True, "status": result.status.value}


@router.post("/{task_id}/start")
def start_task(task_id: str, current_user: Any = Depends(get_current_user)):
    svc = _get_service()
    result = svc.start_task(task_id, _actor(current_user), _actor(current_user))
    return {"success": True, "status": result.status.value}


@router.post("/{task_id}/complete")
def complete_task(
    task_id: str, data: dict | None = None, current_user: Any = Depends(get_current_user),
):
    svc = _get_service()
    result = svc.complete_task(
        task_id, data.get("result") if data else None, _actor(current_user),
    )
    return {"success": True, "status": result.status.value}


@router.post("/{task_id}/fail")
def fail_task(
    task_id: str, data: dict, current_user: Any = Depends(get_current_user),
):
    svc = _get_service()
    result = svc.fail_task(
        task_id, data.get("error", "unknown error"), _actor(current_user),
    )
    return {"success": True, "status": result.status.value}


@router.post("/{task_id}/cancel")
def cancel_task(
    task_id: str, data: dict | None = None, current_user: Any = Depends(get_current_user),
):
    svc = _get_service()
    result = svc.cancel_task(
        task_id, (data or {}).get("reason"), _actor(current_user),
    )
    return {"success": True, "status": result.status.value}


@router.post("/{task_id}/escalate")
def escalate_task(
    task_id: str, data: dict, current_user: Any = Depends(get_current_user),
):
    svc = _get_service()
    result = svc.escalate_task(
        task_id, data.get("reason", ""), data.get("escalated_to"), _actor(current_user),
    )
    return {"success": True, "status": result.status.value}


@router.post("/{task_id}/delegate")
def delegate_task(
    task_id: str, data: dict, current_user: Any = Depends(get_current_user),
):
    svc = _get_service()
    result = svc.delegate_task(
        task_id, data["to_user"], data.get("reason"), _actor(current_user),
    )
    return {"success": True, "status": result.status.value}


@router.post("/{task_id}/hold")
def hold_task(task_id: str, current_user: Any = Depends(get_current_user)):
    svc = _get_service()
    result = svc.hold_task(task_id, _actor(current_user))
    return {"success": True, "status": result.status.value}


@router.post("/{task_id}/resume")
def resume_task(task_id: str, current_user: Any = Depends(get_current_user)):
    svc = _get_service()
    result = svc.resume_task(task_id, _actor(current_user))
    return {"success": True, "status": result.status.value}


@router.post("/{task_id}/comments")
def add_comment(
    task_id: str, data: dict, current_user: Any = Depends(get_current_user),
):
    svc = _get_service()
    comment = svc.add_comment(
        task_id,
        _actor(current_user) or "unknown",
        data.get("author_name", ""),
        data["content"],
    )
    return {"success": True, "comment_id": comment.id}


@router.get("/{task_id}/comments")
def get_comments(task_id: str, current_user: Any = Depends(get_current_user)):
    svc = _get_service()
    comments = svc.get_comments(task_id)
    return {"comments": comments}


@router.get("/{task_id}/history")
def get_history(task_id: str, current_user: Any = Depends(get_current_user)):
    svc = _get_service()
    history = svc.get_history(task_id)
    return {"history": history}


@router.get("/queues")
def list_queues(current_user: Any = Depends(get_current_user)):
    svc = _get_service()
    queues = svc.list_queues()
    return {"queues": queues}


@router.post("/queues")
def create_queue(data: dict, current_user: Any = Depends(get_current_user)):
    svc = _get_service()
    queue = TaskQueue(
        id=str(uuid.uuid4()),
        name=data["name"],
        description=data.get("description", ""),
    )
    result = svc.create_queue(queue)
    return {"success": True, "id": result.id}


@router.put("/queues/{queue_id}")
def update_queue(
    queue_id: str, data: dict, current_user: Any = Depends(get_current_user),
):
    svc = _get_service()
    svc.update_queue(queue_id, data)
    return {"success": True}


@router.get("/sla-definitions")
def list_slas(current_user: Any = Depends(get_current_user)):
    svc = _get_service()
    slas = svc.list_slas()
    return {"sla_definitions": slas}


@router.post("/sla-definitions")
def create_sla(data: dict, current_user: Any = Depends(get_current_user)):
    svc = _get_service()
    sla = TaskSLADefinition(
        id=str(uuid.uuid4()),
        task_category=TaskCategory(data.get("category", "general")),
        task_type=data.get("task_type", "general"),
        priority=TaskPriority(data.get("priority", "medium")),
        warning_threshold_s=data.get("warning_threshold_s", 3600),
        breach_threshold_s=data.get("breach_threshold_s", 7200),
    )
    result = svc.create_sla(sla)
    return {"success": True, "id": result.id}


@router.put("/sla-definitions/{sla_id}")
def update_sla(
    sla_id: str, data: dict, current_user: Any = Depends(get_current_user),
):
    svc = _get_service()
    svc.update_sla(sla_id, data)
    return {"success": True}


@router.get("/pending")
def get_pending_tasks(current_user: Any = Depends(get_current_user)):
    svc = _get_service()
    user_id = _actor(current_user) or "unknown"
    tasks = svc.get_pending_tasks(user_id)
    return {"tasks": tasks}


@router.get("/overdue")
def get_overdue_tasks(current_user: Any = Depends(get_current_user)):
    svc = _get_service()
    tasks = svc.get_overdue_tasks()
    return {"tasks": tasks}


@router.get("/stats")
def get_stats(current_user: Any = Depends(get_current_user)):
    svc = _get_service()
    return svc.get_stats()


@router.get("/health")
def health():
    return {"status": "ok", "module": "task_engine", "version": "1.0.0"}

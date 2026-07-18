from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from app._compat import UTC
from enum import Enum
from typing import Any

logger = logging.getLogger("gula.national.intelligence.automation")


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class EscalationLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class AutomationTask:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    action: str = ""
    params: dict[str, Any] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 0
    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    completed_at: float | None = None
    error: str = ""
    retry_count: int = 0
    max_retries: int = 3
    result: Any = None
    assigned_to: str = ""
    tags: list[str] = field(default_factory=list)


@dataclass
class AutomationRule:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    condition: Callable[[dict[str, Any]], bool] | None = None
    actions: list[Callable[[dict[str, Any]], Any]] = field(default_factory=list)
    priority: int = 0
    enabled: bool = True
    description: str = ""


@dataclass
class ScheduleDefinition:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    cron_expression: str = ""
    task: AutomationTask | None = None
    timezone: str = "UTC"
    enabled: bool = True
    last_run: float | None = None
    next_run: float | None = None
    created_at: float = field(default_factory=time.time)


@dataclass
class NotificationRule:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    event_type: str = ""
    condition: Callable[[dict[str, Any]], bool] | None = None
    channels: list[str] = field(default_factory=list)
    template: str = ""
    recipients: list[str] = field(default_factory=list)
    enabled: bool = True


@dataclass
class EscalationPath:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    levels: list[dict[str, Any]] = field(default_factory=list)
    timeout_seconds: int = 300
    escalation_action: Callable[[dict[str, Any]], Any] | None = None
    enabled: bool = True


@dataclass
class CompensationAction:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    action_type: str = ""
    rollback_function: Callable[[dict[str, Any]], Any] | None = None
    params: dict[str, Any] = field(default_factory=dict)
    description: str = ""


@dataclass
class JobStep:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    action: str = ""
    params: dict[str, Any] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    retry_count: int = 0
    max_retries: int = 2
    result: Any = None
    error: str = ""


@dataclass
class JobDefinition:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    steps: list[JobStep] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    completed_at: float | None = None
    error: str = ""


class TaskAutomationEngine:
    def __init__(self) -> None:
        self._tasks: dict[str, AutomationTask] = {}
        self._handlers: dict[str, Callable[[dict[str, Any]], Any]] = {}

    def register_handler(self, action: str, handler: Callable[[dict[str, Any]], Any]) -> None:
        self._handlers[action] = handler

    def schedule_task(
        self,
        name: str,
        action: str,
        params: dict[str, Any] | None = None,
        priority: int = 0,
        max_retries: int = 3,
    ) -> AutomationTask:
        task = AutomationTask(
            name=name,
            action=action,
            params=params or {},
            priority=priority,
            max_retries=max_retries,
        )
        self._tasks[task.id] = task
        logger.info(
            "[TaskAutomation] scheduled task=%s action=%s priority=%d",
            task.id,
            action,
            priority,
        )
        return task

    def execute_task(self, task_id: str) -> Any:
        task = self._tasks.get(task_id)
        if task is None:
            raise ValueError(f"Task {task_id!r} not found")
        if task.status == TaskStatus.CANCELLED:
            raise RuntimeError(f"Task {task_id} is cancelled")
        handler = self._handlers.get(task.action)
        if handler is None:
            raise ValueError(f"No handler registered for action '{task.action}'")
        task.status = TaskStatus.RUNNING
        task.started_at = time.time()
        try:
            result = handler(task.params)
            task.result = result
            task.status = TaskStatus.COMPLETED
            task.completed_at = time.time()
            logger.info("[TaskAutomation] completed task=%s action=%s", task_id, task.action)
            return result
        except Exception as exc:
            task.error = str(exc)
            if task.retry_count < task.max_retries:
                task.status = TaskStatus.RETRYING
                task.retry_count += 1
                logger.warning(
                    "[TaskAutomation] retrying task=%s attempt=%d/%d error=%s",
                    task_id,
                    task.retry_count,
                    task.max_retries,
                    exc,
                )
                return self.execute_task(task_id)
            task.status = TaskStatus.FAILED
            task.completed_at = time.time()
            logger.error("[TaskAutomation] failed task=%s error=%s", task_id, exc)
            raise

    def retry_task(self, task_id: str) -> Any:
        task = self._tasks.get(task_id)
        if task is None:
            raise ValueError(f"Task {task_id!r} not found")
        if task.status not in (TaskStatus.FAILED, TaskStatus.RETRYING):
            raise ValueError(f"Task {task_id} is not in a retryable state (status={task.status})")
        task.retry_count = 0
        task.status = TaskStatus.PENDING
        return self.execute_task(task_id)

    def cancel_task(self, task_id: str) -> None:
        task = self._tasks.get(task_id)
        if task is None:
            raise ValueError(f"Task {task_id!r} not found")
        if task.status in (TaskStatus.COMPLETED, TaskStatus.CANCELLED):
            raise ValueError(f"Task {task_id} already in terminal state (status={task.status})")
        task.status = TaskStatus.CANCELLED
        task.completed_at = time.time()
        logger.info("[TaskAutomation] cancelled task=%s", task_id)

    def get_task_status(self, task_id: str) -> dict[str, Any]:
        task = self._tasks.get(task_id)
        if task is None:
            raise ValueError(f"Task {task_id!r} not found")
        return {
            "id": task.id,
            "name": task.name,
            "action": task.action,
            "status": task.status.value,
            "priority": task.priority,
            "retry_count": task.retry_count,
            "max_retries": task.max_retries,
            "error": task.error,
            "created_at": task.created_at,
            "started_at": task.started_at,
            "completed_at": task.completed_at,
        }

    def list_tasks(self, status: TaskStatus | None = None) -> list[dict[str, Any]]:
        tasks = self._tasks.values()
        if status:
            tasks = [t for t in tasks if t.status == status]
        return [
            {
                "id": t.id,
                "name": t.name,
                "action": t.action,
                "status": t.status.value,
                "priority": t.priority,
                "created_at": t.created_at,
            }
            for t in sorted(tasks, key=lambda x: (-x.priority, x.created_at))
        ]


class RuleAutomationEngine:
    def __init__(self) -> None:
        self._rules: dict[str, AutomationRule] = {}

    def register_rule(self, rule: AutomationRule) -> str:
        self._rules[rule.id] = rule
        logger.info("[RuleAutomation] registered rule=%s name=%s", rule.id, rule.name)
        return rule.id

    def evaluate_rules(self, context: dict[str, Any], rules: list[AutomationRule] | None = None) -> list[dict[str, Any]]:
        target_rules = rules or list(self._rules.values())
        triggered: list[dict[str, Any]] = []
        for rule in sorted(target_rules, key=lambda r: -r.priority):
            if not rule.enabled:
                continue
            if rule.condition is None:
                continue
            try:
                if rule.condition(context):
                    triggered.append({
                        "rule_id": rule.id,
                        "rule_name": rule.name,
                        "context": context,
                        "matched_at": time.time(),
                    })
                    logger.info("[RuleAutomation] rule triggered id=%s name=%s", rule.id, rule.name)
            except Exception as exc:
                logger.error("[RuleAutomation] rule evaluation error id=%s error=%s", rule.id, exc)
        return triggered

    def execute_actions(self, actions: list[Callable[[dict[str, Any]], Any]], context: dict[str, Any]) -> list[Any]:
        results = []
        for action in actions:
            try:
                result = action(context)
                results.append(result)
            except Exception as exc:
                logger.error("[RuleAutomation] action execution error: %s", exc)
                results.append(None)
        return results

    def trigger_automation(self, event: dict[str, Any]) -> list[dict[str, Any]]:
        triggered = self.evaluate_rules(event)
        outcomes = []
        for match in triggered:
            rule = self._rules.get(match["rule_id"])
            if rule and rule.actions:
                action_results = self.execute_actions(rule.actions, match["context"])
                outcomes.append({
                    "rule_id": rule.id,
                    "rule_name": rule.name,
                    "actions_executed": len(rule.actions),
                    "action_results": action_results,
                })
        return outcomes


class ScheduleAutomationEngine:
    def __init__(self) -> None:
        self._schedules: dict[str, ScheduleDefinition] = {}

    @staticmethod
    def _parse_cron(cron_expression: str) -> list[int]:
        parts = cron_expression.strip().split()
        if len(parts) != 5:
            raise ValueError(f"Invalid cron expression: {cron_expression!r}")
        return [int(p) if p != "*" else -1 for p in parts]

    @staticmethod
    def _matches_cron(cron_parts: list[int], dt: datetime) -> bool:
        minute, hour, day, month, day_of_week = cron_parts
        if minute != -1 and dt.minute != minute:
            return False
        if hour != -1 and dt.hour != hour:
            return False
        if day != -1 and dt.day != day:
            return False
        if month != -1 and dt.month != month:
            return False
        return not (day_of_week != -1 and dt.weekday() != day_of_week)

    def create_schedule(
        self,
        cron_expression: str,
        task: AutomationTask,
        timezone: str = "UTC",
    ) -> ScheduleDefinition:
        self._parse_cron(cron_expression)
        schedule = ScheduleDefinition(
            name=task.name,
            cron_expression=cron_expression,
            task=task,
            timezone=timezone,
            next_run=self._compute_next_run(cron_expression),
        )
        self._schedules[schedule.id] = schedule
        logger.info(
            "[ScheduleAutomation] created schedule=%s cron=%s task=%s",
            schedule.id,
            cron_expression,
            task.name,
        )
        return schedule

    def _compute_next_run(self, cron_expression: str) -> float:
        cron_parts = self._parse_cron(cron_expression)
        now = datetime.now(UTC)
        for minutes_ahead in range(525600):
            candidate = now + timedelta(minutes=minutes_ahead)
            if self._matches_cron(cron_parts, candidate):
                return candidate.timestamp()
        return now.timestamp() + 86400

    def enable_schedule(self, schedule_id: str) -> None:
        schedule = self._schedules.get(schedule_id)
        if schedule is None:
            raise ValueError(f"Schedule {schedule_id!r} not found")
        schedule.enabled = True
        logger.info("[ScheduleAutomation] enabled schedule=%s", schedule_id)

    def disable_schedule(self, schedule_id: str) -> None:
        schedule = self._schedules.get(schedule_id)
        if schedule is None:
            raise ValueError(f"Schedule {schedule_id!r} not found")
        schedule.enabled = False
        logger.info("[ScheduleAutomation] disabled schedule=%s", schedule_id)

    def get_due_tasks(self) -> list[ScheduleDefinition]:
        now = time.time()
        due = []
        for schedule in self._schedules.values():
            if not schedule.enabled:
                continue
            if schedule.next_run and now >= schedule.next_run:
                due.append(schedule)
                schedule.last_run = schedule.next_run
                schedule.next_run = self._compute_next_run(schedule.cron_expression)
        return due


class NotificationAutomationEngine:
    def __init__(self) -> None:
        self._rules: dict[str, NotificationRule] = {}

    def create_notification_rule(
        self,
        name: str,
        event_type: str,
        channels: list[str],
        template: str,
        recipients: list[str],
        condition: Callable[[dict[str, Any]], bool] | None = None,
    ) -> NotificationRule:
        rule = NotificationRule(
            name=name,
            event_type=event_type,
            channels=channels,
            template=template,
            recipients=recipients,
            condition=condition,
        )
        self._rules[rule.id] = rule
        logger.info(
            "[NotificationAutomation] created rule=%s event_type=%s channels=%s",
            rule.id,
            event_type,
            channels,
        )
        return rule

    def evaluate_notification_triggers(self, event: dict[str, Any]) -> list[NotificationRule]:
        triggered = []
        event_type = event.get("type", "")
        for rule in self._rules.values():
            if not rule.enabled:
                continue
            if rule.event_type != event_type:
                continue
            if rule.condition and not rule.condition(event):
                continue
            triggered.append(rule)
            logger.info(
                "[NotificationAutomation] trigger matched rule=%s event_type=%s",
                rule.id,
                event_type,
            )
        return triggered

    def dispatch_notification(self, rule: NotificationRule, context: dict[str, Any]) -> dict[str, Any]:
        message = rule.template
        for key, value in context.items():
            placeholder = f"{{{key}}}"
            message = message.replace(placeholder, str(value))
        dispatch_record = {
            "rule_id": rule.id,
            "rule_name": rule.name,
            "channels": rule.channels,
            "recipients": rule.recipients,
            "message": message,
            "dispatched_at": time.time(),
        }
        for channel in rule.channels:
            logger.info(
                "[NotificationAutomation] dispatched channel=%s recipients=%s message=%.80s",
                channel,
                rule.recipients,
                message,
            )
        return dispatch_record


class EscalationEngine:
    def __init__(self) -> None:
        self._paths: dict[str, EscalationPath] = {}
        self._active_escalations: dict[str, dict[str, Any]] = {}

    def define_escalation_path(
        self,
        name: str,
        levels: list[dict[str, Any]],
        timeout_seconds: int = 300,
    ) -> EscalationPath:
        path = EscalationPath(
            name=name,
            levels=levels,
            timeout_seconds=timeout_seconds,
        )
        self._paths[path.id] = path
        logger.info(
            "[EscalationEngine] defined path=%s levels=%d timeout=%ds",
            path.id,
            len(levels),
            timeout_seconds,
        )
        return path

    def evaluate_escalation(self, context: dict[str, Any]) -> dict[str, Any]:
        severity = context.get("severity", EscalationLevel.INFO.value)
        for path in self._paths.values():
            if not path.enabled:
                continue
            for level in path.levels:
                if level.get("level") == severity:
                    escalation_id = str(uuid.uuid4())
                    record = {
                        "escalation_id": escalation_id,
                        "path_id": path.id,
                        "path_name": path.name,
                        "level": level,
                        "context": context,
                        "created_at": time.time(),
                        "resolved": False,
                    }
                    self._active_escalations[escalation_id] = record
                    logger.info(
                        "[EscalationEngine] escalated id=%s path=%s level=%s",
                        escalation_id,
                        path.name,
                        severity,
                    )
                    return record
        return {
            "escalation_id": None,
            "message": "No escalation path matched",
            "severity": severity,
        }

    def execute_escalation(self, escalation_id: str) -> dict[str, Any]:
        record = self._active_escalations.get(escalation_id)
        if record is None:
            raise ValueError(f"Escalation {escalation_id!r} not found")
        if record["resolved"]:
            raise ValueError(f"Escalation {escalation_id} already resolved")
        path = self._paths.get(record["path_id"])
        if path and path.escalation_action:
            try:
                result = path.escalation_action(record["context"])
                record["result"] = result
                record["resolved"] = True
                record["resolved_at"] = time.time()
                logger.info("[EscalationEngine] executed escalation id=%s", escalation_id)
                return record
            except Exception as exc:
                logger.error("[EscalationEngine] execution failed id=%s error=%s", escalation_id, exc)
                record["error"] = str(exc)
                return record
        record["resolved"] = True
        record["resolved_at"] = time.time()
        return record


class CompensationEngine:
    def __init__(self) -> None:
        self._compensations: dict[str, CompensationAction] = {}
        self._transaction_log: list[dict[str, Any]] = []

    def define_compensation(
        self,
        name: str,
        action_type: str,
        rollback_function: Callable[[dict[str, Any]], Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> CompensationAction:
        action = CompensationAction(
            name=name,
            action_type=action_type,
            rollback_function=rollback_function,
            params=params or {},
        )
        self._compensations[action.id] = action
        logger.info("[CompensationEngine] defined compensation=%s type=%s", action.id, action_type)
        return action

    def execute_compensation(self, failed_action: dict[str, Any]) -> dict[str, Any]:
        action_id = failed_action.get("compensation_id", "")
        compensation = self._compensations.get(action_id)
        if compensation is None:
            return {
                "success": False,
                "error": f"No compensation defined for action {action_id}",
            }
        if compensation.rollback_function is None:
            return {
                "success": True,
                "message": f"No rollback for {compensation.name}",
                "compensation_id": action_id,
            }
        try:
            result = compensation.rollback_function(compensation.params)
            record = {
                "compensation_id": action_id,
                "action_type": compensation.action_type,
                "result": result,
                "executed_at": time.time(),
            }
            self._transaction_log.append(record)
            logger.info("[CompensationEngine] executed compensation=%s", action_id)
            return {"success": True, "result": result, "compensation_id": action_id}
        except Exception as exc:
            logger.error("[CompensationEngine] compensation failed id=%s error=%s", action_id, exc)
            return {"success": False, "error": str(exc), "compensation_id": action_id}

    def rollback_transaction(self, transaction_id: str) -> dict[str, Any]:
        for record in reversed(self._transaction_log):
            if record.get("compensation_id") == transaction_id:
                logger.info("[CompensationEngine] rolled back transaction=%s", transaction_id)
                return {"success": True, "transaction_id": transaction_id}
        return {
            "success": False,
            "error": f"Transaction {transaction_id!r} not found",
        }


class JobOrchestrator:
    def __init__(self) -> None:
        self._jobs: dict[str, JobDefinition] = {}
        self._handlers: dict[str, Callable[[dict[str, Any]], Any]] = {}

    def register_handler(self, action: str, handler: Callable[[dict[str, Any]], Any]) -> None:
        self._handlers[action] = handler

    def define_job(self, name: str, steps: list[JobStep]) -> JobDefinition:
        job = JobDefinition(name=name, steps=steps)
        self._jobs[job.id] = job
        logger.info("[JobOrchestrator] defined job=%s steps=%d", job.id, len(steps))
        return job

    def execute_job(self, job_id: str) -> dict[str, Any]:
        job = self._jobs.get(job_id)
        if job is None:
            raise ValueError(f"Job {job_id!r} not found")
        job.status = TaskStatus.RUNNING
        job.started_at = time.time()
        completed_steps: set[str] = set()
        step_results: list[dict[str, Any]] = []
        for step in job.steps:
            deps_met = all(dep in completed_steps for dep in step.dependencies)
            if not deps_met:
                step.status = TaskStatus.PENDING
                step_results.append({
                    "step_id": step.id,
                    "step_name": step.name,
                    "status": step.status.value,
                    "message": "Waiting for dependencies",
                })
                continue
            handler = self._handlers.get(step.action)
            if handler is None:
                step.status = TaskStatus.FAILED
                step.error = f"No handler for '{step.action}'"
                job.status = TaskStatus.FAILED
                job.error = step.error
                job.completed_at = time.time()
                step_results.append({
                    "step_id": step.id,
                    "step_name": step.name,
                    "status": step.status.value,
                    "error": step.error,
                })
                return {
                    "job_id": job.id,
                    "job_name": job.name,
                    "status": job.status.value,
                    "error": job.error,
                    "step_results": step_results,
                }
            step.status = TaskStatus.RUNNING
            try:
                result = handler(step.params)
                step.result = result
                step.status = TaskStatus.COMPLETED
                completed_steps.add(step.id)
                step_results.append({
                    "step_id": step.id,
                    "step_name": step.name,
                    "status": step.status.value,
                    "result": result,
                })
            except Exception as exc:
                step.status = TaskStatus.FAILED
                step.error = str(exc)
                job.status = TaskStatus.FAILED
                job.error = step.error
                job.completed_at = time.time()
                step_results.append({
                    "step_id": step.id,
                    "step_name": step.name,
                    "status": step.status.value,
                    "error": step.error,
                })
                return {
                    "job_id": job.id,
                    "job_name": job.name,
                    "status": job.status.value,
                    "error": job.error,
                    "step_results": step_results,
                }
        all_completed = all(s.status == TaskStatus.COMPLETED for s in job.steps)
        job.status = TaskStatus.COMPLETED if all_completed else TaskStatus.FAILED
        job.completed_at = time.time()
        logger.info(
            "[JobOrchestrator] job=%s completed status=%s steps_completed=%d/%d",
            job.id,
            job.status.value,
            len(completed_steps),
            len(job.steps),
        )
        return {
            "job_id": job.id,
            "job_name": job.name,
            "status": job.status.value,
            "step_results": step_results,
        }

    def get_job_status(self, job_id: str) -> dict[str, Any]:
        job = self._jobs.get(job_id)
        if job is None:
            raise ValueError(f"Job {job_id!r} not found")
        return {
            "id": job.id,
            "name": job.name,
            "status": job.status.value,
            "steps": [
                {
                    "id": s.id,
                    "name": s.name,
                    "status": s.status.value,
                    "dependencies": s.dependencies,
                    "error": s.error,
                }
                for s in job.steps
            ],
            "created_at": job.created_at,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
            "error": job.error,
        }

    def cancel_job(self, job_id: str) -> None:
        job = self._jobs.get(job_id)
        if job is None:
            raise ValueError(f"Job {job_id!r} not found")
        if job.status in (TaskStatus.COMPLETED, TaskStatus.CANCELLED):
            raise ValueError(f"Job {job_id} already in terminal state")
        job.status = TaskStatus.CANCELLED
        job.completed_at = time.time()
        for step in job.steps:
            if step.status in (TaskStatus.PENDING, TaskStatus.RUNNING):
                step.status = TaskStatus.CANCELLED
        logger.info("[JobOrchestrator] cancelled job=%s", job_id)

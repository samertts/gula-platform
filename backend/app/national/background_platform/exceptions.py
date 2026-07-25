from __future__ import annotations

from app.national.exceptions import NationalDomainError


class JobNotFoundError(NationalDomainError):
    def __init__(self, job_id: str) -> None:
        self.job_id = job_id
        super().__init__(f"Job not found: {job_id}")


class JobValidationError(NationalDomainError):
    def __init__(self, job_id: str, reason: str) -> None:
        self.job_id = job_id
        self.reason = reason
        super().__init__(f"Job validation failed: {job_id}: {reason}")


class JobExecutionError(NationalDomainError):
    def __init__(self, job_id: str, execution_id: str, reason: str) -> None:
        self.job_id = job_id
        self.execution_id = execution_id
        self.reason = reason
        super().__init__(f"Job execution failed: {job_id}/{execution_id}: {reason}")


class JobScheduleNotFoundError(NationalDomainError):
    def __init__(self, schedule_id: str) -> None:
        self.schedule_id = schedule_id
        super().__init__(f"Job schedule not found: {schedule_id}")


class JobDependencyError(NationalDomainError):
    def __init__(self, job_id: str, depends_on_job_id: str, reason: str) -> None:
        self.job_id = job_id
        self.depends_on_job_id = depends_on_job_id
        self.reason = reason
        super().__init__(f"Job dependency error: {job_id} depends on {depends_on_job_id}: {reason}")


class InvalidCronExpressionError(NationalDomainError):
    def __init__(self, expression: str, reason: str) -> None:
        self.expression = expression
        self.reason = reason
        super().__init__(f"Invalid cron expression: {expression}: {reason}")


class JobStateTransitionError(NationalDomainError):
    def __init__(self, job_id: str, current_status: str, target_status: str) -> None:
        self.job_id = job_id
        self.current_status = current_status
        self.target_status = target_status
        super().__init__(
            f"Invalid state transition for job {job_id}: {current_status} -> {target_status}",
        )


class JobTimeoutError(NationalDomainError):
    def __init__(self, job_id: str, execution_id: str, timeout_s: int) -> None:
        self.job_id = job_id
        self.execution_id = execution_id
        self.timeout_s = timeout_s
        super().__init__(f"Job timed out: {job_id}/{execution_id} exceeded {timeout_s}s")

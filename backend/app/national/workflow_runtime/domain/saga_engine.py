from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any

from datetime import UTC
from backend.app.national.workflow_runtime.domain.entities import SagaLog
from backend.app.national.workflow_runtime.domain.enums import CompensationStrategy

logger = logging.getLogger("gula.workflow_runtime.saga")


class SagaEngine:
    def __init__(self) -> None:
        self._logs: list[SagaLog] = []
        self._compensation_strategy: CompensationStrategy = CompensationStrategy.REVERSE_ORDER

    async def execute_step(
        self, saga_id: str, step_id: str, step_type: str, data: dict[str, Any],
    ) -> SagaLog:
        log = SagaLog(
            id=str(uuid.uuid4()),
            saga_id=saga_id,
            step_id=step_id,
            step_type=step_type,
            action="forward",
            status="running",
            data=data,
        )
        self._logs.append(log)
        logger.debug("Saga step %s executing (forward)", step_id)
        return log

    async def complete_step(self, saga_id: str, step_id: str, result: dict[str, Any]) -> SagaLog:
        for log in self._logs:
            if log.saga_id == saga_id and log.step_id == step_id and log.action == "forward":
                log.status = "completed"
                log.data = result
                return log
        log = SagaLog(
            id=str(uuid.uuid4()),
            saga_id=saga_id,
            step_id=step_id,
            action="forward",
            status="completed",
            data=result,
        )
        self._logs.append(log)
        return log

    async def fail_step(self, saga_id: str, step_id: str, error: str) -> SagaLog:
        for log in self._logs:
            if log.saga_id == saga_id and log.step_id == step_id and log.action == "forward":
                log.status = "failed"
                log.error = error
                return log
        log = SagaLog(
            id=str(uuid.uuid4()),
            saga_id=saga_id,
            step_id=step_id,
            action="forward",
            status="failed",
            error=error,
        )
        self._logs.append(log)
        return log

    async def compensate(
        self, saga_id: str, completed_steps: list[str],
    ) -> list[SagaLog]:
        compensated: list[SagaLog] = []
        steps_to_compensate: list[str] = list(completed_steps)

        if self._compensation_strategy == CompensationStrategy.REVERSE_ORDER:
            steps_to_compensate = list(reversed(steps_to_compensate))

        for step_id in steps_to_compensate:
            log = SagaLog(
                id=str(uuid.uuid4()),
                saga_id=saga_id,
                step_id=step_id,
                action="compensate",
                status="completed",
                data={"compensated": True},
                created_at=datetime.now(UTC),
            )
            self._logs.append(log)
            compensated.append(log)
            logger.info("Saga compensated step %s in saga %s", step_id, saga_id)

        return compensated

    async def rollback(self, saga_id: str) -> list[SagaLog]:
        rolled: list[SagaLog] = []
        for log in self._logs:
            if log.saga_id == saga_id and log.status in ("completed", "running"):
                log.status = "rolled_back"
                rolled.append(log)
        return rolled

    def get_saga_logs(self, saga_id: str) -> list[SagaLog]:
        return [log for log in self._logs if log.saga_id == saga_id]

    def set_compensation_strategy(self, strategy: CompensationStrategy) -> None:
        self._compensation_strategy = strategy

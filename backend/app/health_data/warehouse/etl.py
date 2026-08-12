from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime

from app._compat import UTC

logger = logging.getLogger("gula.health_data.warehouse.etl")


@dataclass
class ETLResult:
    job_name: str
    rows_extracted: int
    rows_transformed: int
    rows_loaded: int
    errors: int
    duration_ms: float
    started_at: datetime
    completed_at: datetime
    error_messages: list[str] = field(default_factory=list)


@dataclass
class ETLJob:
    name: str
    extract_fn: Callable[[], list[dict]]
    transform_fn: Callable[[list[dict]], list[dict]]
    load_fn: Callable[[list[dict]], int]
    enabled: bool = True
    schedule: str = ""
    description: str = ""


class ETLPipeline:
    def __init__(self):
        self._jobs: dict[str, ETLJob] = {}

    def register(self, job: ETLJob) -> None:
        self._jobs[job.name] = job
        logger.info("ETL job registered: %s", job.name)

    def unregister(self, job_name: str) -> None:
        self._jobs.pop(job_name, None)

    def get(self, job_name: str) -> ETLJob | None:
        return self._jobs.get(job_name)

    def list_jobs(self) -> list[ETLJob]:
        return list(self._jobs.values())

    async def run(self, job_name: str) -> ETLResult:
        import time

        job = self._jobs.get(job_name)
        if not job:
            raise ValueError(f"ETL job not found: {job_name}")
        if not job.enabled:
            raise ValueError(f"ETL job disabled: {job_name}")

        started_at = datetime.now(UTC)
        start = time.monotonic()
        errors: list[str] = []

        try:
            raw_data = job.extract_fn()
            rows_extracted = len(raw_data)
            logger.debug("ETL %s: extracted %d rows", job_name, rows_extracted)
        except Exception as exc:
            logger.error("ETL %s: extract failed: %s", job_name, exc)
            return ETLResult(
                job_name=job_name, rows_extracted=0, rows_transformed=0, rows_loaded=0,
                errors=1, duration_ms=0, started_at=started_at, completed_at=datetime.now(UTC),
                error_messages=[f"Extract failed: {exc}"],
            )

        try:
            transformed = job.transform_fn(raw_data)
            rows_transformed = len(transformed)
            logger.debug("ETL %s: transformed %d rows", job_name, rows_transformed)
        except Exception as exc:
            logger.error("ETL %s: transform failed: %s", job_name, exc)
            return ETLResult(
                job_name=job_name, rows_extracted=rows_extracted, rows_transformed=0, rows_loaded=0,
                errors=1, duration_ms=0, started_at=started_at, completed_at=datetime.now(UTC),
                error_messages=[f"Transform failed: {exc}"],
            )

        try:
            rows_loaded = job.load_fn(transformed)
            logger.debug("ETL %s: loaded %d rows", job_name, rows_loaded)
        except Exception as exc:
            logger.error("ETL %s: load failed: %s", job_name, exc)
            return ETLResult(
                job_name=job_name, rows_extracted=rows_extracted, rows_transformed=rows_transformed,
                rows_loaded=0, errors=1, duration_ms=0, started_at=started_at,
                completed_at=datetime.now(UTC), error_messages=[f"Load failed: {exc}"],
            )

        duration = (time.monotonic() - start) * 1000
        completed_at = datetime.now(UTC)
        result = ETLResult(
            job_name=job_name,
            rows_extracted=rows_extracted,
            rows_transformed=rows_transformed,
            rows_loaded=rows_loaded,
            errors=len(errors),
            duration_ms=round(duration, 1),
            started_at=started_at,
            completed_at=completed_at,
            error_messages=errors,
        )

        logger.info("ETL %s: %d→%d→%d rows in %.1fms", job_name, rows_extracted, rows_transformed, rows_loaded, duration)
        return result

    async def run_all(self) -> list[ETLResult]:
        results = []
        for job_name in self._jobs:
            if self._jobs[job_name].enabled:
                result = await self.run(job_name)
                results.append(result)
        return results

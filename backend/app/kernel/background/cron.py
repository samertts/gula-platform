from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass

logger = logging.getLogger("gula.kernel.background.cron")


@dataclass
class CronJob:
    name: str
    schedule: str
    handler: Callable
    enabled: bool = True


class CronEngine:
    def __init__(self):
        self._jobs: dict[str, CronJob] = {}

    def register(self, job: CronJob) -> None:
        self._jobs[job.name] = job

    def unregister(self, name: str) -> None:
        self._jobs.pop(name, None)

    def list_jobs(self) -> list[CronJob]:
        return list(self._jobs.values())

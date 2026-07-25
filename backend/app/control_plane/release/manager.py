from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

from app._compat import UTC
from app.control_plane.enums import ReleaseChannel

logger = logging.getLogger("gula.control_plane.release.manager")


class ReleaseStatus:
    PENDING = "pending"
    APPROVED = "approved"
    DEPLOYING = "deploying"
    DEPLOYED = "deployed"
    ROLLING_BACK = "rolling_back"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Release:
    release_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    version: str = ""
    channel: ReleaseChannel = ReleaseChannel.STABLE
    component: str = ""
    artifacts: dict[str, str] = field(default_factory=dict)
    config: dict[str, Any] = field(default_factory=dict)
    status: str = ReleaseStatus.PENDING
    approved_by: str | None = None
    deployed_by: str | None = None
    rollback_version: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    deployed_at: str | None = None


class ReleaseManager:
    def __init__(self):
        self._releases: dict[str, Release] = {}
        self._approval_required: bool = True

    def create_release(
        self,
        name: str,
        version: str,
        channel: ReleaseChannel = ReleaseChannel.STABLE,
        component: str = "",
        artifacts: dict | None = None,
        config: dict | None = None,
    ) -> Release:
        release = Release(
            name=name,
            version=version,
            channel=channel,
            component=component,
            artifacts=artifacts or {},
            config=config or {},
        )
        self._releases[release.release_id] = release
        logger.info("Release created: %s v%s [%s]", name, version, channel.value)
        return release

    def approve(self, release_id: str, user: str) -> Release | None:
        release = self._releases.get(release_id)
        if not release:
            return None
        release.status = ReleaseStatus.APPROVED
        release.approved_by = user
        logger.info("Release %s approved by %s", release_id, user)
        return release

    async def deploy(self, release_id: str, user: str) -> Release | None:
        release = self._releases.get(release_id)
        if not release:
            return None
        if self._approval_required and release.status != ReleaseStatus.APPROVED:
            raise ValueError(f"Release {release_id} requires approval before deployment")

        release.status = ReleaseStatus.DEPLOYING
        release.deployed_by = user
        logger.info("Deploying release: %s v%s", release.name, release.version)

        try:
            import asyncio

            await asyncio.sleep(0.3)
            release.status = ReleaseStatus.DEPLOYED
            release.deployed_at = datetime.now(UTC).isoformat()
            logger.info("Release deployed: %s v%s", release.name, release.version)
        except Exception as e:
            release.status = ReleaseStatus.FAILED
            logger.error("Release deploy failed: %s", e)

        return release

    async def rollback(self, release_id: str) -> Release | None:
        release = self._releases.get(release_id)
        if not release:
            return None
        release.status = ReleaseStatus.ROLLING_BACK
        await __import__("asyncio").sleep(0.2)
        release.status = ReleaseStatus.ROLLED_BACK
        logger.info("Release rolled back: %s v%s", release.name, release.version)
        return release

    def get(self, release_id: str) -> Release | None:
        return self._releases.get(release_id)

    def list_releases(
        self,
        component: str | None = None,
        channel: ReleaseChannel | None = None,
        status: str | None = None,
    ) -> list[Release]:
        result = list(self._releases.values())
        if component:
            result = [r for r in result if r.component == component]
        if channel:
            result = [r for r in result if r.channel == channel]
        if status:
            result = [r for r in result if r.status == status]
        return result

    def canary_rollout(
        self,
        name: str,
        version: str,
        component: str = "",
        percentage: int = 10,
    ) -> Release:
        release = self.create_release(
            name=name,
            version=version,
            channel=ReleaseChannel.CANARY,
            component=component,
            config={"canary_percentage": percentage},
        )
        logger.info("Canary rollout created: %s v%s (%d%%)", name, version, percentage)
        return release

    def summary(self) -> dict[str, Any]:
        return {
            "total": len(self._releases),
            "by_status": {
                s: sum(1 for r in self._releases.values() if r.status == s)
                for s in [
                    ReleaseStatus.PENDING,
                    ReleaseStatus.APPROVED,
                    ReleaseStatus.DEPLOYED,
                    ReleaseStatus.ROLLED_BACK,
                    ReleaseStatus.FAILED,
                ]
            },
            "by_channel": {
                c.value: sum(1 for r in self._releases.values() if r.channel == c)
                for c in ReleaseChannel
            },
        }

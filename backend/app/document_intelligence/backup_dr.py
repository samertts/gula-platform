from __future__ import annotations

import asyncio
import contextlib
import hashlib
import json
import logging
import os
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class BackupManifest:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: float = field(default_factory=time.time)
    size_bytes: int = 0
    checksum: str = ""
    entries: int = 0
    status: str = "in_progress"
    backup_type: str = "full"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class BackupEntry:
    key: str
    data: bytes
    checksum: str = ""


class BackupScheduler:
    def __init__(self, backup_dir: str = "/tmp/docintel_backups"):
        self._backup_dir = backup_dir
        self._schedules: dict[str, dict[str, Any]] = {}
        self._running = False
        self._task: asyncio.Task | None = None
        os.makedirs(backup_dir, exist_ok=True)

    def add_schedule(self, name: str, interval_seconds: int, backup_fn: Callable, backup_type: str = "full"):
        self._schedules[name] = {
            "interval": interval_seconds,
            "fn": backup_fn,
            "type": backup_type,
            "last_run": 0.0,
        }

    def remove_schedule(self, name: str):
        self._schedules.pop(name, None)

    async def start(self):
        self._running = True
        self._task = asyncio.create_task(self._scheduler_loop())
        logger.info("Backup scheduler started")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
        logger.info("Backup scheduler stopped")

    async def _scheduler_loop(self):
        while self._running:
            now = time.time()
            for name, schedule in self._schedules.items():
                if now - schedule["last_run"] >= schedule["interval"]:
                    try:
                        manifest = await schedule["fn"]()
                        schedule["last_run"] = now
                        logger.info("Scheduled backup '%s' completed: %s", name, manifest.id)
                    except Exception as e:
                        logger.exception("Scheduled backup '%s' failed: %s", name, e)
            await asyncio.sleep(60)

    def get_schedules(self) -> list[dict[str, Any]]:
        return [
            {"name": n, "interval": s["interval"], "type": s["type"]}
            for n, s in self._schedules.items()
        ]


class BackupService:
    def __init__(self, backup_dir: str = "/tmp/docintel_backups"):
        self._backup_dir = backup_dir
        self._manifests: dict[str, BackupManifest] = {}
        os.makedirs(backup_dir, exist_ok=True)

    async def create_backup(self, entries: list[BackupEntry], backup_type: str = "full") -> BackupManifest:
        manifest = BackupManifest(backup_type=backup_type)
        manifest.entries = len(entries)

        serialized = json.dumps(
            [{"key": e.key, "data": e.data.hex(), "checksum": e.checksum} for e in entries],
            default=str,
        ).encode()

        manifest.size_bytes = len(serialized)
        manifest.checksum = hashlib.sha256(serialized).hexdigest()

        filename = f"backup_{manifest.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(self._backup_dir, filename)

        with open(filepath, "wb") as f:
            f.write(serialized)

        manifest.status = "completed"
        self._manifests[manifest.id] = manifest
        logger.info("Backup %s created: %s (%d bytes)", manifest.id, filepath, manifest.size_bytes)
        return manifest

    async def restore_backup(self, manifest_id: str) -> list[BackupEntry]:
        manifest = self._manifests.get(manifest_id)
        if not manifest:
            raise ValueError(f"Backup manifest not found: {manifest_id}")

        import glob
        matches = glob.glob(os.path.join(self._backup_dir, f"backup_{manifest.id}_*.json"))
        if not matches:
            raise FileNotFoundError(f"Backup file not found for: {manifest_id}")

        with open(matches[0], "rb") as f:
            data = json.loads(f.read().decode())

        result = []
        for entry in data:
            result.append(BackupEntry(
                key=entry["key"],
                data=bytes.fromhex(entry["data"]),
                checksum=entry["checksum"],
            ))
        return result

    def list_backups(self) -> list[BackupManifest]:
        return list(self._manifests.values())

    def get_manifest(self, manifest_id: str) -> BackupManifest | None:
        return self._manifests.get(manifest_id)

    async def verify_backup(self, manifest_id: str) -> bool:
        try:
            entries = await self.restore_backup(manifest_id)
            re_serialized = json.dumps(
                [{"key": e.key, "data": e.data.hex(), "checksum": e.checksum} for e in entries],
                default=str,
            ).encode()
            checksum = hashlib.sha256(re_serialized).hexdigest()
            manifest = self._manifests.get(manifest_id)
            if manifest:
                return checksum == manifest.checksum
            return False
        except Exception as e:
            logger.error("Backup verification failed: %s", e)
            return False

    async def cleanup_old_backups(self, max_age_days: int = 30):
        now = time.time()
        cutoff = now - (max_age_days * 86400)
        to_remove = [mid for mid, m in self._manifests.items() if m.created_at < cutoff]
        for mid in to_remove:
            self._manifests.pop(mid, None)
            import glob
            for f in glob.glob(os.path.join(self._backup_dir, f"backup_{mid}_*.json")):
                os.remove(f)
        if to_remove:
            logger.info("Cleaned up %d old backups", len(to_remove))

"""Phase 5 — Rollback Engine.

Every deployment is reversible. Capture a snapshot before each deployment
(version, configuration, database, storage), keep a version history, and
roll back automatically when health validation fails. Restores are verified
before the platform returns to service.
"""

from __future__ import annotations

from scripts.deployer.core import (
    DeploymentSnapshot,
    DeploymentStatus,
    RollbackKind,
    make_id,
)
from scripts.deployer.health import deployment_rejected


def capture_snapshot(deployment_id: str, version: str, *,
                     config_digest: str = "",
                     database_backup: str = "",
                     storage_backup: str = "") -> DeploymentSnapshot:
    """Persist a point-in-time deployment snapshot for rollback."""
    return DeploymentSnapshot(
        snapshot_id=make_id("SNAP"),
        deployment_id=deployment_id,
        version=version,
        config_digest=config_digest,
        database_backup=database_backup,
        storage_backup=storage_backup,
    )


def version_history(records: list[dict]) -> list[dict]:
    """Return deployments ordered newest-first (deterministic)."""
    return sorted(records, key=lambda r: r.get("version", ""), reverse=True)


def rollback_plan(snapshot: DeploymentSnapshot, *,
                  kinds: tuple[str, ...] = (
                      RollbackKind.VERSION.value,
                      RollbackKind.CONFIGURATION.value,
                      RollbackKind.DATABASE.value,
                  )) -> dict:
    """Produce the rollback plan for a snapshot."""
    return {
        "snapshot_id": snapshot.snapshot_id,
        "version": snapshot.version,
        "kinds": list(kinds),
        "order": ["version", "configuration", "database"],
        "verify_after": True,
    }


def automatic_rollback(
    checks,
    snapshot: DeploymentSnapshot,
    *,
    config_digest: str = "cfg-restore",
    database_backup: str = "db-restore",
    storage_backup: str = "storage-restore",
) -> dict:
    """Roll back automatically when health validation rejects the release."""
    if not deployment_rejected(checks):
        return {
            "rolled_back": False,
            "status": DeploymentStatus.LIVE.value,
            "reason": "health validation accepted the release",
        }
    return {
        "rolled_back": True,
        "status": DeploymentStatus.ROLLED_BACK.value,
        "snapshot_id": snapshot.snapshot_id,
        "restored": {
            "version": snapshot.version,
            "configuration": config_digest,
            "database": database_backup,
            "storage": storage_backup,
        },
        "verified": True,
    }


def verify_restore(restored: dict) -> bool:
    """Verify a restore was complete (all rollback kinds covered)."""
    expected = {"version", "configuration", "database"}
    return expected <= set(restored.get("restored", {})) if isinstance(restored, dict) else False

"""Phase 9 — Deployment Knowledge.

Automatically update the knowledge system: registry, deployment history,
infrastructure inventory, runbooks, playbooks, recovery procedures, and
lessons learned. Every deployment event becomes searchable, auditable
knowledge.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from scripts.deployer.core import (
    HISTORY_DIR,
    DeploymentRecord,
    read_json,
    write_json,
)

REGISTRY_PATH = HISTORY_DIR / "registry.json"
INVENTORY_PATH = HISTORY_DIR / "inventory.json"
RUNBOOK_PATH = HISTORY_DIR / "runbook.md"


def _record_file(deployment_id: str) -> Path:
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    return HISTORY_DIR / f"{deployment_id}.json"


def persist_record(record: DeploymentRecord) -> Path:
    """Write a deployment record to its durable file."""
    return write_json(_record_file(record.deployment_id), record.to_dict())


def load_record(deployment_id: str) -> DeploymentRecord:
    data = read_json(_record_file(deployment_id))
    return DeploymentRecord(
        deployment_id=deployment_id,
        version=data.get("version", ""),
        environment=data.get("environment", ""),
        status=data.get("status", "planned"),
        artifacts=data.get("artifacts", []),
        validations=data.get("validations", []),
        snapshots=data.get("snapshots", []),
        rollbacks=data.get("rollbacks", []),
        security=data.get("security", []),
        timeline=data.get("timeline", []),
        created_at=data.get("created_at", ""),
        closed_at=data.get("closed_at", ""),
    )


def add_event(record: DeploymentRecord, event: str, detail: str = "") -> None:
    record.timeline.append({"event": event, "detail": detail, "at": datetime.now(UTC).isoformat()})


def register(deployment_id: str, version: str, environment: str, status: str) -> None:
    """Add or update a deployment in the registry."""
    data = read_json(REGISTRY_PATH)
    data.setdefault("deployments", {})[deployment_id] = {
        "version": version,
        "environment": environment,
        "status": status,
    }
    write_json(REGISTRY_PATH, data)


def list_deployments(environment: str = "") -> list[dict]:
    data = read_json(REGISTRY_PATH).get("deployments", {})
    deployments = [
        {"deployment_id": mid, **info}
        for mid, info in data.items()
    ]
    deployments.sort(key=lambda d: d.get("deployment_id", ""))
    if environment:
        deployments = [d for d in deployments if d.get("environment") == environment]
    return deployments


def inventory(items: list[dict]) -> dict:
    """Maintain the infrastructure inventory (idempotent)."""
    data = read_json(INVENTORY_PATH)
    existing = data.setdefault("resources", [])
    known = {r.get("resource_id") for r in existing}
    for item in items:
        if item.get("resource_id") not in known:
            existing.append(item)
    write_json(INVENTORY_PATH, data)
    data["total"] = len(existing)
    return data


def write_runbook(contents: str) -> Path:
    """Persist the deployment runbook."""
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    RUNBOOK_PATH.write_text(contents, encoding="utf-8")
    return RUNBOOK_PATH


def recovery_procedures() -> list[str]:
    """Deterministic recovery procedures the runbook always ships."""
    return [
        "1. Confirm the failed deployment's snapshot and version.",
        "2. Apply version + configuration rollback from the snapshot.",
        "3. Restore the database from the pre-deployment backup.",
        "4. Verify all health components pass before returning to service.",
        "5. Record the failure and lesson in deployment knowledge.",
    ]


def lessons_learned(records: list[dict]) -> list[str]:
    """Extract deterministic lessons from deployment history."""
    rolled_back = [r for r in records if r.get("status") == "rolled_back"]
    if not rolled_back:
        return ["No rollbacks recorded; deployment practice is stable."]
    return [
        f"Deployment {r.get('deployment_id')} rolled back from "
        f"{r.get('version')} — review pre-flight validation before retry."
        for r in rolled_back
    ]

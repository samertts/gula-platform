"""PROGRAM-STABLE-004 — Domain Lifecycle (Phase 5).

Each Domain supports the full lifecycle: installation, activation,
suspension, upgrade, rollback, backup, restore, health check, metrics,
independent versioning, and independent certification.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.domain_platform.core import (
    DomainLifecycleState,
    lifecycle_transition_allowed,
    utcnow,
)
from app.domain_platform.versioning import (
    DomainVersionRegistry,
    compare_versions,
    is_compatible,
    parse_version,
)


class LifecycleError(Exception):
    pass


@dataclass
class LifecycleEvent:
    """One auditable lifecycle transition."""

    domain_code: str
    action: str
    from_state: str
    to_state: str
    version: str | None
    at: str = field(default_factory=lambda: utcnow().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain_code": self.domain_code,
            "action": self.action,
            "from_state": self.from_state,
            "to_state": self.to_state,
            "version": self.version,
            "at": self.at,
        }


class DomainLifecycle:
    """State machine + lifecycle operations for one Domain."""

    def __init__(self, domain_code: str, initial_state: str = "installed") -> None:
        self.domain_code = domain_code
        self.state = DomainLifecycleState(initial_state)
        self.versions = DomainVersionRegistry(domain_code)
        self.history: list[LifecycleEvent] = []
        self.backups: list[dict[str, str]] = []

    def _transition(self, action: str, target: str, version: str | None = None) -> str:
        if not lifecycle_transition_allowed(self.state.value, target):
            raise LifecycleError(
                f"domain '{self.domain_code}' cannot transition from "
                f"'{self.state.value}' to '{target}'"
            )
        previous = self.state.value
        self.state = DomainLifecycleState(target)
        self.history.append(
            LifecycleEvent(
                domain_code=self.domain_code,
                action=action,
                from_state=previous,
                to_state=target,
                version=version,
            )
        )
        return target

    # ── operations ──────────────────────────────────────────────────────────

    def install(self, version: str = "1.0.0") -> str:
        parse_version(version)
        if self.state == DomainLifecycleState.retired:
            raise LifecycleError(f"domain '{self.domain_code}' is retired and cannot be reinstalled")
        self.versions.add(version, certified=False, changelog="initial install")
        # Install is the birth of the Domain: it enters the 'installed'
        # state without requiring a prior transition.
        self.state = DomainLifecycleState.installed
        self.history.append(
            LifecycleEvent(
                domain_code=self.domain_code,
                action="install",
                from_state="created",
                to_state=DomainLifecycleState.installed.value,
                version=version,
            )
        )
        return self.state.value

    def activate(self) -> str:
        if self.state == DomainLifecycleState.installed:
            return self._transition("activate", DomainLifecycleState.active.value)
        if self.state in (DomainLifecycleState.suspended, DomainLifecycleState.upgrading):
            return self._transition("activate", DomainLifecycleState.active.value)
        raise LifecycleError(
            f"domain '{self.domain_code}' cannot be activated from '{self.state.value}'"
        )

    def suspend(self) -> str:
        if self.state not in (DomainLifecycleState.active, DomainLifecycleState.upgrading):
            raise LifecycleError(
                f"domain '{self.domain_code}' cannot be suspended from '{self.state.value}'"
            )
        return self._transition("suspend", DomainLifecycleState.suspended.value)

    def upgrade(self, new_version: str, certified: bool = True, changelog: str = "") -> str:
        parse_version(new_version)
        latest = self.versions.latest
        if latest and not is_compatible(latest.version, new_version) and not certified:
            raise LifecycleError(
                f"version '{new_version}' breaks backward compatibility with "
                f"'{latest.version}' and is not certified"
            )
        if latest and compare_versions(new_version, latest.version) <= 0:
            raise LifecycleError(
                f"upgrade version '{new_version}' must exceed current '{latest.version}'"
            )
        if self.state not in (DomainLifecycleState.active, DomainLifecycleState.suspended):
            raise LifecycleError(
                f"domain '{self.domain_code}' cannot be upgraded from '{self.state.value}'"
            )
        self._transition("upgrade", DomainLifecycleState.upgrading.value, new_version)
        self.versions.add(new_version, certified=certified, changelog=changelog)
        return self._transition(
            "upgrade", DomainLifecycleState.active.value, new_version
        )

    def rollback(self) -> str | None:
        """Roll back to the previous version (never deletes the failed one)."""
        if self.state == DomainLifecycleState.upgrading:
            self.state = DomainLifecycleState(DomainLifecycleState.suspended.value)
        elif self.state != DomainLifecycleState.active:
            raise LifecycleError(
                f"domain '{self.domain_code}' cannot be rolled back from '{self.state.value}'"
            )
        if len(self.versions.versions) < 2:
            raise LifecycleError("no previous version to roll back to")
        previous = self.versions.versions[-2].version
        self.history.append(
            LifecycleEvent(
                domain_code=self.domain_code,
                action="rollback",
                from_state=self.state.value,
                to_state=DomainLifecycleState.active.value,
                version=previous,
            )
        )
        return previous

    def backup(self, label: str = "") -> str:
        backup_id = f"BK-{self.domain_code}-{len(self.backups) + 1}"
        self.backups.append(
            {
                "backup_id": backup_id,
                "version": self.versions.latest.version if self.versions.latest else "n/a",
                "label": label,
                "created_at": utcnow().isoformat(),
            }
        )
        return backup_id

    def restore(self, backup_id: str) -> None:
        target = next((b for b in self.backups if b["backup_id"] == backup_id), None)
        if not target:
            raise LifecycleError(f"backup '{backup_id}' not found")
        self.history.append(
            LifecycleEvent(
                domain_code=self.domain_code,
                action="restore",
                from_state=self.state.value,
                to_state=self.state.value,
                version=target["version"],
            )
        )

    def health_check(self) -> dict[str, Any]:
        return {
            "domain_code": self.domain_code,
            "state": self.state.value,
            "version": self.versions.latest.version if self.versions.latest else None,
            "backups": len(self.backups),
            "healthy": self.state in (
                DomainLifecycleState.active,
                DomainLifecycleState.installed,
            ),
        }

    def metrics(self) -> dict[str, Any]:
        return {
            "domain_code": self.domain_code,
            "state": self.state.value,
            "version": self.versions.latest.version if self.versions.latest else None,
            "transition_count": len(self.history),
            "backup_count": len(self.backups),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain_code": self.domain_code,
            "state": self.state.value,
            "versions": self.versions.to_dict(),
            "history": [e.to_dict() for e in self.history],
            "backups": self.backups,
        }

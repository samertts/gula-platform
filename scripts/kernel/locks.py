"""Phase 6 — Lock Manager.

File locks, module locks, knowledge locks, registry locks, deployment locks,
and database locks. Deadlock detection via the wait-for graph, automatic
unlock for expired locks, and conflict resolution by owner priority.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from .core import LOCK_TYPES, Lock, utcnow


@dataclass
class WaitForEdge:
    """A single wait-for relationship in the deadlock graph."""

    holder: str
    waiter: str
    resource: str


class LockConflictError(Exception):
    """Raised when a lock cannot be acquired without conflict."""


class LockManager:
    """In-process lock manager with deadlock detection and auto unlock."""

    def __init__(self) -> None:
        self._locks: dict[str, Lock] = {}

    @property
    def locks(self) -> dict[str, Lock]:
        return dict(self._locks)

    def acquire(
        self,
        resource: str,
        lock_type: str,
        owner: str,
        ttl_seconds: int = 0,
    ) -> Lock:
        """Acquire a lock, raising LockConflictError when already held."""
        if lock_type not in LOCK_TYPES:
            raise ValueError(f"Unknown lock type '{lock_type}'; expected one of {LOCK_TYPES}")
        self.auto_unlock()
        existing = self._locks.get(resource)
        if existing is not None:
            raise LockConflictError(
                f"resource '{resource}' already locked by '{existing.owner}'"
            )
        lock = Lock(
            lock_id=f"{lock_type}:{resource}",
            resource=resource,
            lock_type=lock_type,
            owner=owner,
            ttl_seconds=ttl_seconds,
        )
        self._locks[resource] = lock
        return lock

    def release(self, resource: str, owner: str) -> Lock | None:
        """Release a lock if the caller owns it (strict ownership)."""
        lock = self._locks.get(resource)
        if lock is None:
            return None
        if lock.owner != owner:
            raise PermissionError(
                f"cannot release '{resource}': held by '{lock.owner}', not '{owner}'"
            )
        lock.released_at = utcnow()
        self._locks.pop(resource, None)
        return lock

    def is_locked(self, resource: str) -> bool:
        return resource in self._locks

    def owner_of(self, resource: str) -> str:
        lock = self._locks.get(resource)
        return lock.owner if lock else ""

    def auto_unlock(self) -> list[str]:
        """Release locks whose TTL has expired; return the released resources."""
        now = datetime.now(UTC)
        expired: list[str] = []
        for resource, lock in list(self._locks.items()):
            if not lock.ttl_seconds:
                continue
            try:
                acquired = datetime.fromisoformat(lock.acquired_at)
            except ValueError:  # pragma: no cover - defensive
                continue
            if (now - acquired).total_seconds() >= lock.ttl_seconds:
                lock.released_at = utcnow()
                expired.append(resource)
                self._locks.pop(resource, None)
        return expired

    def _wait_for_edges(self, pending: dict[str, tuple[str, str]]) -> list[WaitForEdge]:
        """Build wait-for edges from (waiter, resource) pending requests."""
        edges: list[WaitForEdge] = []
        for waiter, (resource, _owner) in pending.items():
            holder = self.owner_of(resource)
            if holder:
                edges.append(WaitForEdge(holder=holder, waiter=waiter, resource=resource))
        return edges

    def detect_deadlock(self, pending: dict[str, tuple[str, str]]) -> list[str]:
        """Detect a deadlock cycle among pending lock waiters.

        ``pending`` maps a waiter owner to ``(resource, lock_type)``. Returns
        the cycle of owners when a cycle exists, otherwise an empty list.
        """
        edges = self._wait_for_edges(pending)
        adjacency: dict[str, set[str]] = {edge.waiter: set() for edge in edges}
        for edge in edges:
            adjacency.setdefault(edge.waiter, set()).add(edge.holder)
        visited: dict[str, int] = {}
        stack: list[str] = []
        cycle: list[str] = []

        def visit(node: str) -> bool:
            visited[node] = 0
            stack.append(node)
            for neighbor in adjacency.get(node, ()):
                if visited.get(neighbor) == 0:
                    cycle.extend([*stack[stack.index(neighbor):], neighbor])
                    return True
                if visited.get(neighbor) == 1:
                    continue
                if visit(neighbor):
                    return True
            stack.pop()
            visited[node] = 1
            return False

        for node in adjacency:
            if node not in visited and visit(node):
                return cycle
        return []

    def resolve_conflict(
        self,
        resource: str,
        contender: str,
        priority: dict[str, int],
        break_cycle: bool = False,
    ) -> str:
        """Resolve a lock conflict by owner priority.

        The higher-priority owner wins. When ``break_cycle`` is True and the
        contenders are equal, the incumbent is released to break a deadlock.
        """
        incumbent = self.owner_of(resource)
        if not incumbent:
            return ""
        incumbent_priority = priority.get(incumbent, 0)
        contender_priority = priority.get(contender, 0)
        if contender_priority > incumbent_priority:
            return self._force_release(resource, incumbent)
        if break_cycle and contender_priority == incumbent_priority:
            return self._force_release(resource, incumbent)
        raise LockConflictError(
            f"conflict on '{resource}': {contender} cannot preempt {incumbent}"
        )

    def _force_release(self, resource: str, owner: str) -> str:
        lock = self._locks.get(resource)
        if lock and lock.owner == owner:
            lock.released_at = utcnow()
            self._locks.pop(resource, None)
            return resource
        return ""

    def snapshot(self) -> dict[str, Any]:
        return {
            resource: vars(lock)
            for resource, lock in self._locks.items()
        }

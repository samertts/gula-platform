"""PROGRAM-BETA-COMMIT-0.1 — Dormancy Registry (ADR-026).

The GULA Constitution guarantees that dormant enterprise modules are
strategic assets and must never be removed. The Dormancy Registry makes
this invariant explicit and enforceable:

  * every source module carries an explicit lifecycle state;
  * dormant / archived / retired modules are *protected* — migration work
    must never delete them;
  * the canonical data lives in a committed configuration file
    (``config/dormancy.json``) encoding the C1.4 archive policy: the archive
    set covers only ``ai/``, ``nhop-platform/`` and ``edge_agent/``;
    ``platform/`` stays ``active_development`` (deferred, never archived).

Abstraction layer: the certification engine depends only on the
``DormancySource`` interface. The default source is a JSON configuration
file; future sources (database-backed metadata, a governance service) can be
plugged in through ``build_dormancy_source`` without touching the engine.
"""

from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Protocol, runtime_checkable

from app.domain_platform.core import utcnow


class ModuleLifecycleState(StrEnum):
    active_development = "active_development"
    dormant = "dormant"
    archived = "archived"
    retired = "retired"


# States whose modules are strategic assets and MUST NOT be removed.
PROTECTED_STATES: frozenset[str] = frozenset(
    {ModuleLifecycleState.dormant, ModuleLifecycleState.archived, ModuleLifecycleState.retired}
)


class DormancySourceError(ValueError):
    """Raised when a DormancySource cannot be loaded or is invalid."""


class DormancyRegistryError(DormancySourceError):
    """Raised on an invalid or conflicting lifecycle declaration."""


@dataclass(frozen=True)
class DormancyRecord:
    """One explicit lifecycle declaration for a source module."""

    module: str
    state: ModuleLifecycleState
    rationale: str
    effective_since: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "module": self.module,
            "state": str(self.state.value),
            "rationale": self.rationale,
            "effective_since": self.effective_since,
        }


def _today_iso() -> str:
    return utcnow().date().isoformat()


@runtime_checkable
class DormancySource(Protocol):
    """The lifecycle registry interface the certification engine depends on.

    The engine must never rely on a concrete source implementation; any
    data source (config file, database, governance service) that satisfies
    this protocol is interchangeable.
    """

    def find_record(self, module: str) -> DormancyRecord | None: ...

    def record_of(self, module: str) -> DormancyRecord | None: ...

    def state_of(self, module: str) -> ModuleLifecycleState | None: ...

    def is_declared(self, module: str) -> bool: ...

    def is_protected(self, module: str) -> bool: ...

    def undeclared(self, modules: list[str]) -> list[str]: ...

    def modules_in_state(self, state: ModuleLifecycleState | str) -> list[str]: ...

    def assert_not_removed(self, removed_modules: list[str]) -> None: ...

    def to_dict(self) -> dict[str, Any]: ...

    def __len__(self) -> int: ...


class DormancyRegistry:
    """In-memory lifecycle registry over source module paths.

    A declaration for ``ai`` covers ``ai/agent.py`` (longest-prefix
    matching). Declarations are immutable — a state cannot silently change
    once recorded. This is the default, mutable source used by tests and
    programmatic registration.
    """

    def __init__(self, records: list[DormancyRecord] | None = None) -> None:
        self._records: dict[str, DormancyRecord] = {}
        for record in records or ():
            self.register(
                record.module,
                record.state,
                record.rationale,
                record.effective_since,
            )

    def register(
        self,
        module: str,
        state: ModuleLifecycleState | str,
        rationale: str,
        effective_since: str | None = None,
    ) -> DormancyRecord:
        try:
            state = ModuleLifecycleState(state)
        except ValueError as exc:
            raise DormancyRegistryError(f"unknown lifecycle state: {state!r}") from exc
        if not module or not module.strip():
            raise DormancyRegistryError("module must not be empty")
        if not rationale or not rationale.strip():
            raise DormancyRegistryError(f"module '{module}' requires a rationale")
        existing = self._records.get(module)
        if existing is not None and existing.state != state:
            raise DormancyRegistryError(
                f"module '{module}' already declared as '{existing.state.value}', "
                f"cannot re-register as '{state.value}'"
            )
        record = DormancyRecord(
            module=module,
            state=state,
            rationale=rationale.strip(),
            effective_since=effective_since or _today_iso(),
        )
        self._records[module] = record
        return record

    def _match(self, module: str) -> DormancyRecord | None:
        """Longest registered key that is a path prefix of ``module``."""
        best: DormancyRecord | None = None
        for key, record in self._records.items():
            matches = module == key or module.startswith(key.rstrip("/") + "/")
            if matches and (best is None or len(key) > len(best.module)):
                best = record
        return best

    def find_record(self, module: str) -> DormancyRecord | None:
        return self._match(module)

    def record_of(self, module: str) -> DormancyRecord | None:
        return self._match(module)

    def state_of(self, module: str) -> ModuleLifecycleState | None:
        record = self._match(module)
        return record.state if record is not None else None

    def is_declared(self, module: str) -> bool:
        return self._match(module) is not None

    def is_protected(self, module: str) -> bool:
        record = self._match(module)
        return record is not None and record.state in PROTECTED_STATES

    def undeclared(self, modules: list[str]) -> list[str]:
        return sorted(m for m in modules if self._match(m) is None)

    def modules_in_state(self, state: ModuleLifecycleState | str) -> list[str]:
        state = ModuleLifecycleState(state)
        return sorted(m for m, r in self._records.items() if r.state == state)

    @property
    def dormant_modules(self) -> list[str]:
        return self.modules_in_state(ModuleLifecycleState.dormant)

    @property
    def archived_modules(self) -> list[str]:
        return self.modules_in_state(ModuleLifecycleState.archived)

    @property
    def retired_modules(self) -> list[str]:
        return self.modules_in_state(ModuleLifecycleState.retired)

    @property
    def active_modules(self) -> list[str]:
        return self.modules_in_state(ModuleLifecycleState.active_development)

    def assert_not_removed(self, removed_modules: list[str]) -> None:
        """Fail if a migration/refactor commit would remove a protected asset."""
        protected = sorted(m for m in removed_modules if self.is_protected(m))
        if protected:
            raise DormancyRegistryError(
                "protected strategic assets must never be removed (ADR-026): "
                + ", ".join(protected)
            )

    def to_dict(self) -> dict[str, Any]:
        return {"records": [r.to_dict() for r in self._records.values()]}

    def __len__(self) -> int:
        return len(self._records)


def _record_from_dict(entry: Any, source: str) -> DormancyRecord:
    if not isinstance(entry, dict):
        raise DormancySourceError(f"{source}: each record must be a JSON object")
    missing = [k for k in ("module", "state", "rationale") if k not in entry]
    if missing:
        raise DormancySourceError(
            f"{source}: record missing required field(s): {', '.join(missing)}"
        )
    module = entry.get("module")
    rationale = entry.get("rationale")
    state = entry.get("state")
    try:
        state = ModuleLifecycleState(state)
    except ValueError as exc:
        raise DormancySourceError(
            f"{source}: unknown lifecycle state {state!r} for module {module!r}"
        ) from exc
    if not module or not module.strip():
        raise DormancySourceError(f"{source}: module must not be empty")
    if not rationale or not rationale.strip():
        raise DormancySourceError(f"{source}: module {module!r} requires a rationale")
    effective_since = entry.get("effective_since") or _today_iso()
    return DormancyRecord(
        module=module,
        state=state,
        rationale=rationale.strip(),
        effective_since=str(effective_since),
    )


class JsonDormancySource(DormancyRegistry):
    """Configuration-file backed source (ADR-026, replaceable data source #1).

    Records are loaded from a JSON document of the form::

        {"schema_version": 1, "records": [
            {"module": "ai", "state": "archived",
             "rationale": "...", "effective_since": "2026-08-06"}
        ]}

    The source is read-only after load; duplicate or malformed declarations
    raise :class:`DormancySourceError` instead of being silently ignored.
    """

    def __init__(self, path: str | pathlib.Path) -> None:
        self.path = pathlib.Path(path)
        super().__init__()
        self._load()

    def register(
        self,
        module: str,
        state: ModuleLifecycleState | str,
        rationale: str,
        effective_since: str | None = None,
    ) -> DormancyRecord:
        raise DormancySourceError(
            "JsonDormancySource is read-only; edit the configuration file "
            f"({self.path}) instead"
        )

    def _load(self) -> None:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise DormancySourceError(f"cannot read dormancy config: {self.path}") from exc
        except json.JSONDecodeError as exc:
            raise DormancySourceError(
                f"invalid JSON in dormancy config {self.path}: {exc}"
            ) from exc
        if not isinstance(raw, dict) or "records" not in raw:
            raise DormancySourceError(
                f"dormancy config {self.path} must contain a 'records' list"
            )
        records = raw.get("records")
        if not isinstance(records, list):
            raise DormancySourceError(
                f"dormancy config {self.path}: 'records' must be a list"
            )
        for entry in records:
            record = _record_from_dict(entry, str(self.path))
            if record.module in self._records:
                raise DormancySourceError(
                    f"duplicate module declaration in {self.path}: {record.module}"
                )
            self._records[record.module] = record

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "records": [r.to_dict() for r in self._records.values()],
        }


# Canonical data source: the committed JSON configuration file.
_DEFAULT_CONFIG: pathlib.Path = (
    pathlib.Path(__file__).resolve().parent / "config" / "dormancy.json"
)

# Documented future providers — intentionally not implemented yet. They are
# registered here so the factory fails loudly instead of silently ignoring a
# requested source kind.
_FUTURE_SOURCE_KINDS: tuple[str, ...] = ("database", "governance")


def load_default_dormancy_source(
    path: str | pathlib.Path | None = None,
) -> DormancySource:
    """Load the canonical source from the committed JSON configuration.

    Fails fast (raises :class:`DormancySourceError`) when the configuration
    is missing or invalid — a silently-empty registry would silently disable
    the protection invariant.
    """
    return JsonDormancySource(pathlib.Path(path) if path else _DEFAULT_CONFIG)


def build_dormancy_source(
    kind: str,
    *,
    path: str | pathlib.Path | None = None,
) -> DormancySource:
    """Factory for a :class:`DormancySource` (the only implementation seam).

    ``kind`` selects the data source:

    * ``canonical`` — the committed JSON configuration file (default);
    * ``inmemory`` — an empty mutable in-memory registry;
    * ``json`` — a JSON configuration file at ``path``;
    * ``database`` / ``governance`` — documented future providers (raise
      until implemented; the engine and this seam already support them).

    The certification engine calls only this factory or accepts an injected
    source, so a future data source is a one-line change here.
    """
    if kind == "canonical":
        return load_default_dormancy_source()
    if kind == "inmemory":
        return DormancyRegistry()
    if kind == "json":
        if path is None:
            raise DormancySourceError("json dormancy source requires a 'path'")
        return JsonDormancySource(path)
    if kind in _FUTURE_SOURCE_KINDS:
        raise DormancySourceError(
            f"dormancy source kind '{kind}' is a documented future provider; "
            "implement DormancySource and register it in build_dormancy_source (ADR-026)"
        )
    raise DormancySourceError(f"unknown dormancy source kind: {kind!r}")


# The authoritative default source every Domain certification uses unless
# another source is injected.
CANONICAL_DORMANCY_REGISTRY: DormancySource = load_default_dormancy_source()

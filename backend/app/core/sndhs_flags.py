"""
SNDHS-lite Phase 1 — environment-controlled feature flags.

These flags are intentionally separate from the per-tenant feature
matrix in ``backend/app/core/feature_flags.py`` (which is per-lab,
subscription-tier driven). The SNDHS-lite flags are *deployment-wide*
toggles that gate the rollout of new schema usage:

- ``ENABLE_VISITS``       — read/write the new ``visits`` table and
                            ``lab_orders.visit_id`` column. When ``False``
                            the platform behaves exactly as before.
- ``ENABLE_NATIONAL_ID``  — accept the new ``patients.national_id``
                            and ``sndhs_health_id`` columns from the
                            API surface. When ``False`` those fields
                            are accepted but ignored on writes and
                            never returned on reads.

Dual-read rules
---------------
1. While ``ENABLE_VISITS`` is False, ``lab_orders.visit_id`` may exist
   in the schema (after migration 0004) but no code path SHOULD read
   or filter by it.
2. While ``ENABLE_NATIONAL_ID`` is False, the existing
   ``national_id_hash`` column remains the lookup key.
3. When a flag flips True at runtime, code MUST tolerate rows that
   have the new column populated AND rows that don't (no dependency
   on backfill having run).

Operational toggle
------------------
- Set via env vars at process start::

    SNDHS_ENABLE_VISITS=true
    SNDHS_ENABLE_NATIONAL_ID=true

- Or, for emergency rollback at runtime, call
  ``disable_visits()`` / ``disable_national_id()`` from the admin
  control surface (``backend/app/routes/admin``). This flips an
  in-process override that takes precedence over the env var until
  the process is restarted.

Defence-in-depth
----------------
Flags are read-only-by-default. ``enable_*`` / ``disable_*`` calls are
audit-emitted via ``sndhs_audit_logs`` so any production toggle is
legally traceable.
"""

from __future__ import annotations

import logging
import os
import threading

log = logging.getLogger("gula.sndhs.flags")


# ── Lock & overrides ─────────────────────────────────────────────────────────
_lock = threading.RLock()
_overrides: dict[str, bool] = {}


def _read_env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


# ── Public flag readers ──────────────────────────────────────────────────────


def visits_enabled() -> bool:
    with _lock:
        if "ENABLE_VISITS" in _overrides:
            return _overrides["ENABLE_VISITS"]
    return _read_env_bool("SNDHS_ENABLE_VISITS", False)


def national_id_enabled() -> bool:
    with _lock:
        if "ENABLE_NATIONAL_ID" in _overrides:
            return _overrides["ENABLE_NATIONAL_ID"]
    return _read_env_bool("SNDHS_ENABLE_NATIONAL_ID", False)


# ── Runtime toggles (admin-only) ─────────────────────────────────────────────


def _set_override(name: str, value: bool | None) -> None:
    with _lock:
        if value is None:
            _overrides.pop(name, None)
        else:
            _overrides[name] = value
    log.warning("sndhs flag override: %s=%s", name, value)


def enable_visits() -> None:
    _set_override("ENABLE_VISITS", True)


def disable_visits() -> None:
    _set_override("ENABLE_VISITS", False)


def reset_visits_override() -> None:
    _set_override("ENABLE_VISITS", None)


def enable_national_id() -> None:
    _set_override("ENABLE_NATIONAL_ID", True)


def disable_national_id() -> None:
    _set_override("ENABLE_NATIONAL_ID", False)


def reset_national_id_override() -> None:
    _set_override("ENABLE_NATIONAL_ID", None)


# ── FastAPI helpers ──────────────────────────────────────────────────────────
# Imported lazily so this module can be used in non-FastAPI contexts
# (the backfill script, for instance).


def require_visits():
    """FastAPI dependency. Returns None when ENABLE_VISITS is on,
    raises 503 otherwise. Use as ``Depends(require_visits)``."""
    from fastapi import HTTPException, status

    def _dep() -> None:
        if not visits_enabled():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "code": "SNDHS_FEATURE_DISABLED",
                    "feature": "visits",
                    "message": "Visit-based endpoints are disabled in this deployment.",
                },
            )

    return _dep


def require_national_id():
    """FastAPI dependency. 503 unless ``ENABLE_NATIONAL_ID`` is on."""
    from fastapi import HTTPException, status

    def _dep() -> None:
        if not national_id_enabled():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "code": "SNDHS_FEATURE_DISABLED",
                    "feature": "national_id",
                    "message": "National-ID endpoints are disabled in this deployment.",
                },
            )

    return _dep


def status_snapshot() -> dict[str, bool]:
    """Return the currently-effective values, useful for ``/health/status``
    and ``/admin/sndhs/flags``."""
    return {
        "visits_enabled": visits_enabled(),
        "national_id_enabled": national_id_enabled(),
    }

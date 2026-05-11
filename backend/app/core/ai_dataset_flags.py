"""AI Interaction Dataset — deployment-wide feature flags.

These flags gate the *operational medical-intelligence collection* pipeline
introduced for the production launch on 2026-05-11. They follow the same
pattern as ``sndhs_flags`` (env-default + in-process override) so the
pipeline can be enabled/disabled per deployment without code changes and
emergency-killed at runtime without a restart.

Flags
-----
- ``ENABLE_AI_DATASET``     master switch. When False every route in
                            ``backend/app/routes/ai_telemetry.py`` returns
                            503 with code ``AI_DATASET_DISABLED``. The
                            tables exist after the migration runs but no
                            writes or reads happen.
- ``ENABLE_AI_FEEDBACK``    gates the feedback endpoint specifically
                            (``POST /api/ai/feedback``). Off by default
                            until ``ENABLE_AI_DATASET`` is on.

Why two flags
-------------
The dataset can be collecting interactions in shadow-mode (writes from
the AI gateway, no end-user surface) while feedback is still gated to a
pilot lab. Independent control lets us roll the two on different
timelines.

Safety
------
All collection is **anonymised**: the routes accept only
``anonymous_session_id`` (a hashed token) and ``lab_id`` from the
caller's JWT. No raw national IDs, phone numbers, or names are accepted
or stored — the schema does not have columns for them. See
``docs/ai/AI_ARCHITECTURE_CONSTRAINTS.md`` for the full data-protection
contract.
"""
from __future__ import annotations

import logging
import os
import threading

log = logging.getLogger("gula.ai_dataset.flags")

_lock = threading.RLock()
_overrides: dict[str, bool] = {}


def _read_env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def ai_dataset_enabled() -> bool:
    with _lock:
        if "ENABLE_AI_DATASET" in _overrides:
            return _overrides["ENABLE_AI_DATASET"]
    return _read_env_bool("ENABLE_AI_DATASET", False)


def ai_feedback_enabled() -> bool:
    if not ai_dataset_enabled():
        return False
    with _lock:
        if "ENABLE_AI_FEEDBACK" in _overrides:
            return _overrides["ENABLE_AI_FEEDBACK"]
    return _read_env_bool("ENABLE_AI_FEEDBACK", False)


def _set_override(name: str, value: bool | None) -> None:
    with _lock:
        if value is None:
            _overrides.pop(name, None)
        else:
            _overrides[name] = value
    log.warning("ai_dataset flag override: %s=%s", name, value)


def enable_dataset()       -> None: _set_override("ENABLE_AI_DATASET",  True)
def disable_dataset()      -> None: _set_override("ENABLE_AI_DATASET",  False)
def reset_dataset_override() -> None: _set_override("ENABLE_AI_DATASET",  None)
def enable_feedback()      -> None: _set_override("ENABLE_AI_FEEDBACK", True)
def disable_feedback()     -> None: _set_override("ENABLE_AI_FEEDBACK", False)
def reset_feedback_override() -> None: _set_override("ENABLE_AI_FEEDBACK", None)


def status_snapshot() -> dict[str, bool]:
    return {
        "ai_dataset_enabled":  ai_dataset_enabled(),
        "ai_feedback_enabled": ai_feedback_enabled(),
    }


def require_dataset():
    """FastAPI dependency. 503 unless ENABLE_AI_DATASET is on."""
    from fastapi import HTTPException, status

    def _dep() -> None:
        if not ai_dataset_enabled():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "code": "AI_DATASET_DISABLED",
                    "feature": "ai_dataset",
                    "message": "AI interaction dataset collection is disabled in this deployment.",
                },
            )
    return _dep


def require_feedback():
    """FastAPI dependency. 503 unless ENABLE_AI_FEEDBACK is on."""
    from fastapi import HTTPException, status

    def _dep() -> None:
        if not ai_feedback_enabled():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "code": "AI_FEEDBACK_DISABLED",
                    "feature": "ai_feedback",
                    "message": "AI feedback collection is disabled in this deployment.",
                },
            )
    return _dep

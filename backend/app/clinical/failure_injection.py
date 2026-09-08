from __future__ import annotations

import os


_ALLOWED_STAGES = {
    "after_claim",
    "after_business_effect",
    "after_inventory_movement",
    "after_audit_preparation",
}


def maybe_fail(stage: str) -> None:
    """Raise only when an explicit test-runtime stage is selected."""
    if os.getenv("ENV", "production").lower() != "test":
        return
    if os.getenv("RUNTIME_MODE", "api").lower() != "test":
        return
    if os.getenv("GULA_TEST_FAILURE_STAGE", "") == stage and stage in _ALLOWED_STAGES:
        raise RuntimeError(f"test-only failure injection: {stage}")

"""FastAPI dependency enforcing a fresh NIAM step-up signal.

This dependency is intentionally separate from the control-plane role guard
(``AUD-SEC-001``): a privileged role establishes *authority*, while a fresh
step-up event establishes *recent proof of possession of the admin's own
second factor*. Both are required for sensitive cross-account operations.
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.identity.api.workspaces import NiamActor, get_current_niam_actor
from app.identity.services.step_up_service import StepUpError, StepUpService

_STEP_UP_PURPOSE = "sensitive_administrative_action"


async def require_fresh_niam_step_up(
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_db),
) -> NiamActor:
    """Deny unless the authenticated principal has fresh own-account MFA evidence."""
    try:
        await StepUpService(db).assert_fresh(actor, purpose=_STEP_UP_PURPOSE)
    except StepUpError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Step-up authentication required: {exc}",
        ) from exc
    return actor

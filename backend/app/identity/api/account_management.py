from __future__ import annotations

import os

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.clinical_gateway.session_facade import SyncSessionAsyncFacade
from app.identity.api.workspaces import NiamActor
from app.identity.services.authorization_decision import (
    AuthorizationActor,
    AuthorizationDecisionService,
    AuthorizationRequest,
)


def get_governance_organization_id() -> str:
    governance_organization_id = os.getenv("NIAM_GOVERNANCE_ORGANIZATION_ID", "").strip()
    if not governance_organization_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Governance authorization is not configured.",
        )
    return governance_organization_id


async def require_governance_management(
    actor: NiamActor,
    db: Session,
    *,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    resource_exists: bool = True,
) -> None:
    """Authorize lifecycle mutations using a server-configured governance scope.

    The governance organization is never accepted from the client. If operations
    has not configured it, the endpoint fails closed with 503 rather than falling
    back to a role string or allowing a global mutation.
    """
    governance_organization_id = get_governance_organization_id()

    facade = SyncSessionAsyncFacade(db)
    decision = await AuthorizationDecisionService(facade).authorize(
        AuthorizationActor(account=actor.account, session=actor.session),
        AuthorizationRequest(
            subject_account_id=actor.account.id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            sensitivity="critical",
            resource_context={
                "exists": resource_exists,
                "governance_organization_id": governance_organization_id,
            },
        ),
    )
    if not decision.allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Governance authorization denied.",
        )

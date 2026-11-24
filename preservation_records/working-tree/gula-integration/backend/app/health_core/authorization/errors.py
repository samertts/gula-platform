"""Authorization failure error, derived from the shared Health Core error contract."""

from __future__ import annotations

from app.health_core.authorization.models import PUBLIC_DENIAL_REASON, AuthorizationDecision
from app.health_core.common.errors import ForbiddenSyntheticOperationError

__all__ = ["AuthorizationDenied"]


class AuthorizationDenied(ForbiddenSyntheticOperationError):
    """Raised by the guard before a denied operation reaches any service.

    The public error body is deliberately generic. The full internal decision
    (including policy id) is available on ``decision`` for audit review and tests;
    it is never exposed in the serialised error envelope.
    """

    code = "AUTHORIZATION_DENIED"
    status_code = 403

    def __init__(self, decision: AuthorizationDecision) -> None:
        self.decision = decision
        super().__init__(PUBLIC_DENIAL_REASON, details={})

"""Fail-closed guards for clinical routes that are not yet durable/canonical.

Legacy clinical documentation and order endpoints used process-local stores and
were not able to prove actor/workspace/patient scope. They remain registered for
compatibility, but every request is stopped until a reviewed canonical command
contract replaces the route. This module intentionally does not provide a
fallback or bypass.
"""

from __future__ import annotations

import logging
from typing import NoReturn

from fastapi import Depends, HTTPException, Request, status

from app.models.lab_user import LabUser
from app.security.dependencies import get_current_user

logger = logging.getLogger("gula.security.legacy_clinical")


def block_legacy_clinical_route(
    request: Request,
    current_user: LabUser = Depends(get_current_user),
) -> NoReturn:
    """Stop non-canonical clinical routes with an explicit migration response."""

    logger.warning(
        "legacy_clinical_route_blocked path=%s method=%s user_id=%s user_role=%s",
        request.url.path,
        request.method,
        getattr(current_user, "id", None),
        getattr(current_user, "role", None),
    )
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail=(
            "This clinical route is disabled while its durable, workspace-scoped "
            "canonical replacement is being implemented."
        ),
        headers={
            "Deprecation": "true",
            "Cache-Control": "no-store",
            "Link": '</api/v1/clinical>; rel="successor-version"',
        },
    )

"""Fail-closed containment for legacy appointment mutations."""

from __future__ import annotations

import logging

from fastapi import Depends, HTTPException, Request, status

from app.security.dependencies import get_current_user

logger = logging.getLogger("gula.security.legacy_appointment")


_SUCCESSOR = "/api/v1/clinical/appointments"


def block_legacy_appointment_write(
    request: Request,
    current_user=Depends(get_current_user),
):
    """Stop non-canonical appointment mutations with an explicit successor."""

    logger.warning(
        "legacy_appointment_write_blocked path=%s method=%s user_id=%s lab_id=%s",
        request.url.path,
        request.method,
        getattr(current_user, "id", None),
        getattr(current_user, "lab_id", None),
    )
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail=(
            "This appointment write route is disabled. Use the workspace-scoped "
            "canonical clinical appointment API instead."
        ),
        headers={
            "Deprecation": "true",
            "Cache-Control": "no-store",
            "Link": f'<{_SUCCESSOR}>; rel="successor-version"',
        },
    )

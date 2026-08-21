"""Fail-closed containment for non-canonical referral write routes."""

from __future__ import annotations

import logging

from fastapi import Depends, HTTPException, Request, status

from app.security.dependencies import get_current_user

logger = logging.getLogger("gula.security.legacy_referral")


_CANONICAL_SUCCESSOR = "/care-continuum/referrals"


def block_legacy_referral_write(
    request: Request,
    current_user=Depends(get_current_user),
):
    """Stop legacy referral mutations until they use the tenant-scoped aggregate."""

    logger.warning(
        "legacy_referral_write_blocked path=%s method=%s user_id=%s lab_id=%s",
        request.url.path,
        request.method,
        getattr(current_user, "id", None),
        getattr(current_user, "lab_id", None),
    )
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail=(
            "This referral write route is disabled. Use the tenant-scoped canonical "
            "care-continuum referral API instead."
        ),
        headers={
            "Deprecation": "true",
            "Cache-Control": "no-store",
            "Link": f'<{_CANONICAL_SUCCESSOR}>; rel="successor-version"',
        },
    )

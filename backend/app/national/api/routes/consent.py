"""Compatibility guard for the retired national consent placeholder.

The operational consent service lives at /consent. These endpoints deliberately
fail closed instead of returning a fake success response.
"""
from fastapi import APIRouter, Depends, HTTPException, status

from app.security.dependencies import require_permission

router = APIRouter(
    prefix="/consents",
    tags=["Consent"],
    # Retired compatibility surface: keep the legacy system-admin guard and
    # require the canonical consent permission as defense in depth.
    dependencies=[
        Depends(require_permission("system:admin")),
        Depends(require_permission("consent:manage")),
    ],
)


def _canonical_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_410_GONE,
        detail={
            "error": "consent_endpoint_retired",
            "canonical_endpoint": "/consent",
            "message": "Use the canonical consent service at /consent.",
            "message_ar": "تم إيقاف هذا المسار؛ استخدم خدمة الموافقة الموحدة /consent.",
        },
    )


@router.post("/")
def create_consent():
    raise _canonical_error()


@router.get("/{consent_id}")
def get_consent(consent_id: str):
    raise _canonical_error()


@router.put("/{consent_id}/revoke")
def revoke_consent(consent_id: str):
    raise _canonical_error()

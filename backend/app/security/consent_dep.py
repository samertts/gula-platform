"""require_consent — FastAPI dependency that gates reads of citizen data.

Access policy, evaluated in this exact order:

  1. Owner bypass
     The subject is reading their own record.
     Path: current_user.role == 'citizen' AND current_user links to the same
     citizen (gpid).

  2. Lab write-path bypass
     The lab that is producing/owning the record can read it without a
     separate consent. Lab-ownership ABAC is enforced by the route itself
     (require_own_lab). Reading rows you wrote is lawful without consent.

  3. Emergency break-glass
     If the request carries X-Emergency-Access: true AND the actor is a
     doctor (role='doctor'), allow and audit loudly. Later review is
     mandatory. This is deliberate — saving a life outweighs a consent lag.

  4. Normal check
     A Consent row must exist with:
        gpid == <subject>, grantee_id == <actor>, scope == <required>,
        status == 'active', expires_at > now.

  Every decision (allow / deny / emergency) writes a single audit row.

  The dependency factory returns a callable that reads `gpid` from the path
  and emits an HTTPException(403, consent_required) on miss.
"""

from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.lab_user import LabUser
from ..services import consent_service
from .dependencies import get_current_user


def _actor_id_for(user: LabUser) -> str:
    """Actor identifier written into Consent.grantee_id.

    Format: 'user:<id>'. Keeping it namespaced leaves room for future
     service-account or external-integration actors ('svc:<name>').
    """
    return f"user:{user.id}"


def _is_owner(user: LabUser, gpid: str) -> bool:
    """True if the current user IS the citizen identified by gpid.

    LabUser exposes `national_id_hash` but not `citizen_ulid` directly;
    citizen-role users carry their citizen_ulid in a JWT claim surfaced
    through the user object when the portal authenticates them. Until the
    citizen portal is fully live we treat owner-bypass as: citizen role AND
    an attached attribute `citizen_ulid` matching gpid.
    """
    if user.role != "citizen":
        return False
    owned = getattr(user, "citizen_ulid", None)
    return owned is not None and owned == gpid


def _emergency_header(request: Request) -> bool:
    """Break-glass flag. Header must be exactly 'true' (case-insensitive)."""
    value = request.headers.get("X-Emergency-Access", "")
    return value.strip().lower() == "true"


def require_consent(
    scope: str,
    *,
    gpid_path_param: str = "citizen_ulid",
) -> Callable:
    """Produce a FastAPI dependency that enforces consent for `scope`.

    Usage:
        @router.get("/citizens/{citizen_ulid}/labs",
                    dependencies=[Depends(require_consent("read:lab_results"))])

    The dependency:
      - reads the subject ULID from `path_params[gpid_path_param]`
      - evaluates the 4 bypass/check rules
      - 403s with {"error": "consent_required", ...} on deny
      - logs every decision
    """

    def dep(
        request: Request,
        current_user: LabUser = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> LabUser:
        gpid: str | None = request.path_params.get(gpid_path_param)
        if gpid is None:
            # Mis-wired route — fail closed.
            raise HTTPException(
                status_code=500,
                detail=f"consent dep: missing path param {gpid_path_param}",
            )

        actor_id = _actor_id_for(current_user)
        ip = request.client.host if request.client else None

        # 1. Owner bypass
        if _is_owner(current_user, gpid):
            consent_service.log_access_decision(
                db,
                actor_user_id=current_user.id,
                actor_role=current_user.role,
                gpid=gpid,
                scope=scope,
                result="allow",
                reason="owner",
                ip_address=ip,
            )
            return current_user

        # 2. Emergency break-glass (doctors only)
        if _emergency_header(request):
            if current_user.role != "doctor":
                consent_service.log_access_decision(
                    db,
                    actor_user_id=current_user.id,
                    actor_role=current_user.role,
                    gpid=gpid,
                    scope=scope,
                    result="deny",
                    reason="emergency_requires_doctor_role",
                    emergency=True,
                    ip_address=ip,
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "emergency_access_denied",
                        "message": "Emergency access requires doctor role.",
                    },
                )
            consent_service.log_access_decision(
                db,
                actor_user_id=current_user.id,
                actor_role=current_user.role,
                gpid=gpid,
                scope=scope,
                result="allow",
                reason="emergency_break_glass",
                emergency=True,
                ip_address=ip,
            )
            return current_user

        # 3. Normal check
        row = consent_service.check_active_consent(
            db,
            gpid=gpid,
            grantee_id=actor_id,
            scope=scope,
        )
        if row is None:
            consent_service.log_access_decision(
                db,
                actor_user_id=current_user.id,
                actor_role=current_user.role,
                gpid=gpid,
                scope=scope,
                result="deny",
                reason="no_active_consent",
                ip_address=ip,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "consent_required",
                    "message": "No active consent for this subject/scope.",
                    "scope": scope,
                    "gpid": gpid,
                },
            )

        consent_service.log_access_decision(
            db,
            actor_user_id=current_user.id,
            actor_role=current_user.role,
            gpid=gpid,
            scope=scope,
            result="allow",
            reason=f"consent_id={row.id}",
            ip_address=ip,
        )
        return current_user

    return dep

"""Authorization policy for national platform governance surfaces (S-04).

The national lifecycle, pilot-platform, certification and contract routers were
previously mounted with no authentication or authorization dependency at all.
This module defines one policy for all of them so the rule cannot drift between
modules.

Policy
------
* **Reads** — any authenticated operational role (a ``citizen`` is not an
  operator and is denied explicitly).
* **Writes** — the platform operator (``master_admin``) only.

Authentication itself is provided by the canonical ``get_current_user``
dependency. Health/liveness routes stay public: they are deliberately *not*
wrapped by these dependencies in their routers.
"""

from __future__ import annotations

from app.security.rbac import require_role

# Every canonical operational role except ``citizen``. Listing them explicitly
# means a future role is denied by default instead of silently trusted.
GOVERNANCE_READ_ROLES: tuple[str, ...] = (
    "master_admin",
    "ministry_admin",
    "province_admin",
    "admin",
    "lab_admin",
    "finance_controller",
    "refund_reviewer",
    "reconciler",
    "finance_auditor",
    "finance_operator",
    "cashier",
    "doctor",
    "staff",
    "lab_staff",
    "technician",
)

GOVERNANCE_WRITE_ROLES: tuple[str, ...] = ("master_admin",)

require_governance_reader = require_role(*GOVERNANCE_READ_ROLES)
require_governance_writer = require_role(*GOVERNANCE_WRITE_ROLES)


# S-09: AI platform internals (sandbox operation catalogue, provider
# reachability/base URLs, dataset flag state) are operator surfaces, not public
# metadata. Reuse the same clinician/administrator set that already governs the
# rest of ``/api/ai`` (CWE-200). ``citizen`` — and any future role — is denied.
AI_OPERATOR_ROLES: tuple[str, ...] = (
    "master_admin",
    "ministry_admin",
    "national_admin",
    "directorate_admin",
    "province_admin",
    "admin",
    "lab_admin",
    "doctor",
)

require_ai_operator = require_role(*AI_OPERATOR_ROLES)


def actor_identity(user) -> str:
    """Server-derived operator identity for governance audit fields.

    Never trust a caller-supplied ``approved_by`` / ``approver`` /
    ``assessed_by`` / ``deployed_by`` value: the audit-relevant identity comes
    from the authenticated principal.
    """
    email = getattr(user, "email", None)
    if email:
        return str(email)
    return f"user:{getattr(user, 'id', 'unknown')}"

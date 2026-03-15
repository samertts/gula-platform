"""
Audit logging service for GULA Platform.
Logs all important actions for security and compliance.
"""

from sqlalchemy.orm import Session
from ..models.audit_log import AuditLog


def log_action(
    db: Session,
    action: str,
    resource_type: str,
    resource_id: int = None,
    user_id: int = None,
    user_role: str = None,
    details: str = None,
    ip_address: str = None,
):
    """Log an action to the audit trail."""
    entry = AuditLog(
        user_id=user_id,
        user_role=user_role,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address,
    )
    db.add(entry)
    # Don't commit here - let the caller's transaction handle it

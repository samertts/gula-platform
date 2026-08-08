"""Audit log writer.

Rows are flushed but not committed — the calling transaction commits (or
rolls back) along with its business writes. This keeps audit entries tied to
the underlying change.
"""

from sqlalchemy.orm import Session

from ..models.audit_log import AuditLog


def log_action(
    db: Session,
    *,
    action: str,
    target_type: str,
    target_id: str,
    actor_id: str | None = None,
    ip_address: str | None = None,
    metadata: dict | None = None,
) -> AuditLog:
    row = AuditLog(
        action=action,
        target_type=target_type,
        target_id=target_id,
        actor_id=actor_id,
        ip_address=ip_address,
        metadata_json=metadata or None,
    )
    db.add(row)
    db.flush()
    return row

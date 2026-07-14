"""Bridge to shared AuditService."""
import warnings

warnings.warn(
    "services/shared/audit.py is deprecated. Import from 'shared.audit' instead.",
    DeprecationWarning,
    stacklevel=2,
)

from shared.audit import AuditService, compute_chain_hash, create_audit_entry

__all__ = [
    "AuditService",
    "compute_chain_hash",
    "create_audit_entry",
]

"""Bridge to shared AuditService."""
import warnings
warnings.warn(
    "services/shared/audit.py is deprecated. Import from 'shared.audit' instead.",
    DeprecationWarning,
    stacklevel=2,
)

from shared.audit import AuditService, create_audit_entry, compute_chain_hash

__all__ = [
    "AuditService",
    "create_audit_entry",
    "compute_chain_hash",
]

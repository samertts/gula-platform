"""Audit logging — use services/audit_service.py directly.

Compatibility module. Renamed from audit_log.py so the submodule name does
not shadow the audit_log decorator exported by app.audit.__init__.
"""

from ..services.audit_service import log_action

__all__ = ["log_action"]

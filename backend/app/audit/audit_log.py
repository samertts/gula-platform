"""
Audit logging — use services/audit_service.py directly.

This module is kept for import compatibility only.
"""

from ..services.audit_service import log_action

__all__ = ["log_action"]

GSF-006: Audit Module — Immutable audit logging.

Provides tamper-evident audit logging with SHA-256 hash chaining
for all security-relevant events in the GULA platform. Supports
structured log entries, forward integrity, log export to SIEM
systems, and compliant log retention for Iraqi healthcare regulations.

Exports:
    AuditLogger: Core audit logging service
    HashChain: SHA-256 hash chain for tamper evidence
    LogExporter: SIEM-compatible log export (Syslog, JSON, CEF)
    AuditQuery: Audit trail query and reconstruction
    RetentionPolicy: Configurable log retention and archival
"""

from security.modules.audit.logger import AuditLogger
from security.modules.audit.hashchain import HashChain
from security.modules.audit.export import LogExporter
from security.modules.audit.query import AuditQuery
from security.modules.audit.retention import RetentionPolicy

__all__ = [
    "AuditLogger",
    "HashChain",
    "LogExporter",
    "AuditQuery",
    "RetentionPolicy",
]

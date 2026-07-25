GSF-010: Database Module — Database encryption and masking.

Provides database-level security controls for the GULA platform including
transparent column-level encryption (CLE), dynamic data masking,
SQL audit trigger generation, and database activity monitoring.
Protects PHI at rest within the GULA database layer.

Exports:
    DatabaseSecurityEngine: Database security orchestration
    ColumnEncryptor: Transparent column-level encryption (AES-256-GCM)
    DataMasker: Dynamic data masking of PII/PHI fields
    AuditTriggerGenerator: SQL audit trigger generation
    DatabaseMonitor: Database activity monitoring
    SchemaAnalyzer: Sensitive data schema discovery
"""

from security.modules.database.engine import DatabaseSecurityEngine
from security.modules.database.encryption import ColumnEncryptor
from security.modules.database.masking import DataMasker
from security.modules.database.triggers import AuditTriggerGenerator
from security.modules.database.monitoring import DatabaseMonitor
from security.modules.database.schema import SchemaAnalyzer

__all__ = [
    "DatabaseSecurityEngine",
    "ColumnEncryptor",
    "DataMasker",
    "AuditTriggerGenerator",
    "DatabaseMonitor",
    "SchemaAnalyzer",
]

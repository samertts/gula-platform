"""GSF-010: Database Module — Database encryption and masking.

Provides database-level security controls for the GULA platform including
column-level encryption, dynamic data masking, and audit triggers.

The primary implementation lives in crypto/ module:
- field_encryption.py — Field-level encryption
- phi_encryption.py — PHI-specific encryption
"""

__all__: list[str] = []

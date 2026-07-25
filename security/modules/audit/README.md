# GSF-008: Audit Module

Immutable audit logging system with hash-chained entries, cryptographic verification, and forensic analysis support.

## Components

### AuditService
- Event creation and storage
- Immutable log chain
- Log verification (tamper detection)
- Querying with advanced filters
- Retention enforcement
- Export to JSON, CSV, FHIR, Syslog
- Real-time alert rules

### ImmutableAuditLog
- Hash-chained log entries
- Cryptographic HMAC-SHA256 signature per entry
- Periodic Merkle root computation and publication
- Log integrity verification
- Tamper detection
- Forensic analysis support
- Standalone chain verification tool

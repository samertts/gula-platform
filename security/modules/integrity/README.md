# GSF-008: Integrity Module

File and database integrity monitoring with tamper detection and configuration drift detection.

## Components

### IntegrityVerifier
- File integrity monitoring (critical system and application files)
- Binary signature verification (Ed25519, RSA-PSS)
- Database integrity verification (SQLite integrity_check)
- Configuration drift detection
- Baseline creation and comparison
- Permission and ownership change detection

# GSF-009: Compliance Module

Multi-framework compliance validation with cross-framework mapping, automated checks, and unified reporting.

## Components

### ASVSValidator
- Full OWASP ASVS Level 3 control mapping (14 chapters, ~200 controls)
- Automated control verification
- Gap analysis by chapter
- Remediation tracking

### NISTCSFValidator
- Full NIST CSF 2.0 mapping (Govern, Identify, Protect, Detect, Respond, Recover)
- Tier assessment (Partial, Risk Informed, Repeatable, Adaptive)
- Profile management (current vs target)
- Risk register integration

### ISO27001Validator
- Annex A control mapping (93 controls across 4 domains)
- ISMS implementation verification
- Statement of Applicability (SOA) generation
- Evidence management

### HIPAAValidator
- HIPAA Security Rule (Administrative, Physical, Technical safeguards)
- HIPAA Privacy Rule controls
- HITECH Act requirements
- Breach notification procedures
- EDI transaction security
- Covered entity vs business associate verification

### GDPRValidator
- Data subject rights (access, rectification, erasure, portability, objection)
- Consent management verification
- DPIA (Data Protection Impact Assessment)
- Breach notification (72-hour rule)
- DPA requirements verification
- International transfer safeguards
- Data retention and minimization

### ComplianceMapper
- Cross-framework control mapping (HIPAA ↔ NIST ↔ ISO ↔ ASVS ↔ GDPR)
- Control deduplication
- Composite compliance score
- Unified evidence collection
- Framework-specific view with unified underlying implementation

### ComplianceEngine
- Registration of compliance frameworks
- Automated periodic checks
- Evidence collection and management
- Report generation (JSON, HTML)
- Remediation plan management
- Dashboard integration

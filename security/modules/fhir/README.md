# GSF-006: Healthcare Security Module

Part of the GULA Security Framework (GSF).

## Components

| Component | File | Description |
|-----------|------|-------------|
| Models | `models.py` | FHIR security vocabulary, consent, audit models |
| SMART on FHIR | `smart.py` | SMART on FHIR launch flows and scope validation |
| Consent | `consent.py` | Patient consent management and enforcement |
| Break Glass | `break_glass.py` | Emergency access workflow with audit |
| Clinical Audit | `audit.py` | Immutable hash-chained audit log |
| Privacy | `privacy.py` | PHI classification, masking, de-identification |

## Integration

Integrates with:
- `backend/app/security/oauth2_provider.py` - OAuth2 token exchange
- `backend/app/services/audit_service.py` - Backend audit logging
- SMARTS on FHIR authorization flows via OIDC/OAuth2
- FHIR Consent resource for patient-directed access control
- Clinical safety systems via break glass notifications

## Standards

- FHIR R4 (AuditEvent, Consent, Provenance resources)
- SMART on FHIR v1.0.0 / v2.0.0
- HIPAA Privacy Rule (minimum necessary, patient rights)
- ISO 15189 (laboratory quality and competence)
- CAP (College of American Pathologists) checklist items

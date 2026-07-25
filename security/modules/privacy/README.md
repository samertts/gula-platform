# GSF-009: Privacy Module

Data privacy enforcement with dynamic masking, anonymization, pseudonymization, and consent management.

## Components

### PrivacyEnforcer
- Data classification (PHI, PII, Restricted, Confidential, Internal, Public)
- Dynamic data masking based on user role (admin, practitioner, patient, analyst)
- Data anonymization (k-anonymity, l-diversity)
- Field-level minimization
- Purpose limitation enforcement via consent management
- Storage limitation (TTL enforcement)
- Pseudonymization (deterministic SHA-256 based)
- De-identification for analytics

# GULA Data Constitution

## Data Ownership

1. **Patient data belongs to the patient.** GULA is the custodian, not the owner. Patients have the right to access, export, correct, and request deletion of their data within legal and regulatory boundaries.

2. **Clinical data is attributed** to the originating clinician or facility. Attribution is never removed, only supplemented.

3. **Derived data** (aggregates, analytics, AI training data) is de-identified before use. Re-identification is prohibited without governance approval.

## Data Classification

| Classification | Definition | Examples | Controls |
|---------------|------------|----------|----------|
| **Public** | Non-identifying, non-clinical | Test catalog, reference ranges, facility directory | No restrictions |
| **Internal** | Operational, not patient-identifying | Staff directory, inventory levels, shift schedules | Authenticated access |
| **Sensitive** | Patient-identifying but not highly restricted | Name, phone, address, visit dates | Role-based access, encryption, audit |
| **Restricted** | Highly sensitive clinical or identity data | National ID, mental health records, HIV status, genetic data | Field-level encryption, purpose-limited, audit, consent verification |
| **Critical** | Life-critical operational data | Critical alerts, emergency contacts, drug allergy records | High availability, immediate replication, break-glass access |

## Data Quality

4. **Validation at entry** — data is validated at the point of entry (API, UI, integration) before persistence.

5. **Deduplication** — the Master Patient Index (MPI) maintains unique patient identities across the platform.

6. **Data freshness** — time-sensitive data (lab results, vital signs, inventory levels) has freshness metadata. Stale data is flagged.

7. **Referential integrity** — foreign keys and application-level checks prevent orphaned records.

## Retention and Archival

8. **Medical records** are retained per Iraqi Ministry of Health regulations (minimum 10 years after last encounter).

9. **Audit logs** are retained for a minimum of 7 years.

10. **Archived data** is preserved in a format that can be restored to the active system if needed. Archival does not mean deletion.

11. **Purge policy** is documented, governed, and executed only with regulatory approval.

## Data Exchange

12. **HL7 FHIR** is the canonical format for data exchange with external systems.

13. **Export formats** include FHIR JSON/XML, CSV, PDF, and HL7 v2.

14. **Import validation** sanitizes and validates all imported data against the same quality rules as internally created data.

## Backup and Recovery

15. **Automated backups** run daily with point-in-time recovery capability.

16. **Recovery time objective (RTO):** 4 hours. **Recovery point objective (RPO):** 1 hour.

17. **Backup verification** includes automated restore testing quarterly.

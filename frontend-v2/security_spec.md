# Security Specification for GULA Medical Platform

## Data Invariants
1. A patient must have an `ownerId` matching the clinician who created the record.
2. Medical records and lab results must belong to a valid patient.
3. Clinicians can only read/write patients they own or if they are admins.
4. Users cannot modify their own `role`.

## The Dirty Dozen (Attack Payloads)
1. **Self-Promotion:** Authenticated user tries to `update` their own profile setting `role: 'admin'`.
2. **Patient Hijacking:** User A tries to `update` User B's patient record setting `ownerId` to User A.
3. **Ghost Records:** Creating a `MedicalRecord` for a non-existent `patientId`.
4. **Data Injection:** Injecting a 2MB string into a `testName` field in `LabResult`.
5. **ID Poisoning:** Using `../../shadow/passwords` as a `patientId` path variable.
6. **Orphaned Writes:** Creating a `LabResult` without an accompanying status.
7. **Privilege Escalation:** Anonymous user attempting to read the `users` collection.
8. **Relational Leak:** User A attempting to `list` patients owned by User B.
9. **Terminal State Bypass:** Attempting to change an `Appointment` status from `completed` back to `scheduled`.
10. **Identity Spoofing:** Creating a patient with an `ownerId` that doesn't match `request.auth.uid`.
11. **PII Scraping:** Querying `users` collection without a specific `uid` filter.
12. **Future Timestamping:** Creating a record with a `createdAt` date in the year 2099.

## Test Scenarios (Red Team Simulation)
The `firestore.rules` will be validated against these payloads to ensure `PERMISSION_DENIED`.

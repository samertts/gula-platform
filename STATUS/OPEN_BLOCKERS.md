# Open Blockers — GULA Stable v1.0.0

**Snapshot:** Phase 0 initial GitHub inspection  
**Evidence baseline:** main `46158e905fd97f57ca21c61bb5574d03aed90293`

| ID | Severity | Finding | Current status | Required closure evidence |
|---|---|---|---|---|
| NR-003 | P0 | Pharmacy PK type divergence between migrations and ORM; 23 tables reported in existing register | OPEN / decision required | Approved canonical identity ADR; reviewed forward migration; clean DB and representative existing DB upgrade proofs; FK/data integrity checks; rollback/restore rehearsal |
| NR-006 | P1 | `national_facilities` mapped by two ORM packages | OPEN | One authoritative writable owner; architecture decision; test enforcing one owner |
| NR-007 | P1 | Entity-agnostic clinical state machine | OPEN | Entity-scoped transition model; exhaustive/property-based invalid-transition tests |
| MIG-EXISTING | P0 | Existing-database upgrade path not verified by latest commit evidence | NOT VERIFIED | Upgrade rehearsal from supported prior schema snapshots with preserved rows and constraints |
| CI-RUN-EVIDENCE | P1 | No PR-triggered workflow run returned for the inspected main commit | UNKNOWN | Inspect current Actions runs and retain job logs; absence of returned PR runs is not evidence of CI failure |
| WEB-SURFACE | P1 | `frontend-v3` and companion `gula-web-suite` relationship needs operational ownership reconciliation | PARTIAL / NOT CLOSED | Approved deployment/source-of-truth map, API contract parity, auth/role boundary and release ownership |
| AUDIT-COVERAGE | P1 | Existing register says most of 123 risk categories were not audited | NOT AUDITED | Category-by-category evidence matrix; explicit NOT AUDITED where no proof exists |
| SECURITY-PRIVACY | P1 | Full privacy, consent, tenant isolation, audit and recovery posture not independently verified in this setup | UNKNOWN | Reproducible security/privacy tests, threat model, data-flow and retention review, backup/restore evidence |

## Rules
- Do not downgrade severity without evidence and an approved review.
- Do not mark a blocker fixed because code was changed; require reproduction and closure tests.
- Existing register entries are referenced, not silently overwritten.
- This is an initial snapshot, not a complete platform audit.
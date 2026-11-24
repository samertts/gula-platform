# PRG-00…PRG-10 implementation status — 2026-11-24

Statuses are engineering-workspace observations, not owner acceptance. A
program may have existing code and still be `NOT ACCEPTED` because contract
conformance, gate evidence, or owner authority is missing. No G1–G12 gate is
passed in this workspace.

| Program | Domain | Status in this execution batch | Evidence / unresolved blocker |
| --- | --- | --- | --- |
| PRG-00 | Core contracts, identity, governance | PARTIAL | Live OpenAPI drift guard, correlation contract, schema endpoints, and capability ownership migrations implemented. C01–C15 conformance and owner decisions NV2-D01…D15 remain unresolved. |
| PRG-01 | Clinical/EHR | NOT ACCEPTED | Existing routes remain; no new synthetic 15-step journey passed. C04 clinical resource conformance remains outstanding. |
| PRG-02 | Hospital/HIS/EMS | NOT ACCEPTED | Existing service code only; no new contracted slice evidence in this batch. |
| PRG-03 | Diagnostics/LIMS/Radiology/Blood bank | NOT ACCEPTED | Existing LIMS tests pass in full regression; DICOM strategy and blood-bank ownership remain blocked by owner decisions. This is not audit package `P-03`. |
| PRG-04 | Pharmacy/medication | NOT ACCEPTED | Duplicate-prescription zero-trust scenario still requires execution evidence. |
| PRG-05 | Public health | BLOCKED (policy) | Generic CRUD surface now durable, but legal scope decision NV2-D08 is absent. Policy-dependent behavior remains isolated. |
| PRG-06 | Specialty care | BLOCKED | Component gaps (dental, rehabilitation, mental health) remain unresolved; owner resource decision required. |
| PRG-07 | Health operations | NOT ACCEPTED | Existing workforce/assets/billing/quality code only; no duplicate-audit-truth consolidation proof. |
| PRG-08 | Access channels/frontend | PARTIAL (bootstrap only) | Four bootstrap surfaces (`session.read` and three registered `/authz/me*` reads) now have typed clients, allowlisted reads, fail-closed state, unit tests, and 56/56 E2E green. The other 90 inventoried surfaces, including all clinical/business pages, remain non-operational or blocked. |
| PRG-09 | Analytics/warehouse | PARTIAL (infrastructure only) | Reporting-service generic CRUD now durable; derived-only analytics truth and offline consolidation remain unverified. |
| PRG-10 | Security, audit, reliability, DR, load, CI | PARTIAL | P-02 remains decision-ready; P-03 chain fix and cross-track PG validation executed; CI guard expanded. Event consolidation engineering seam implemented with one authority, adapters, migration, and PG evidence, but not activated as sole runtime bus. G2/G6/G7/G10 remain unproven: no DR drill, no load report, no accepted zero-trust harness, no owner-approved cross-stack architecture. |

## Highest-impact next implementation batch

1. Obtain owner decisions on event/offline stack authority, ADR-J/J1, BK-017,
   and C09/C10/C11 version bumps before activating any consolidated runtime bus.
2. Operationalize the next bounded frontend batch only after contract registry,
   server-side enforcement, and rollout-policy decisions exist for those pages.
3. Execute DR/PITR restore drill and reproducible k6 load evidence only after
   owner-approved numeric targets exist.
4. Obtain owner decisions D1–D5 for P-03, NV2-D08 for public health, and G1–G12
   acceptance evidence before any release-status change.

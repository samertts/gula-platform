# GULA Service Coverage Reassessment

**Directive:** GULA-PBR-2026-11-19, §7 (Priority P2 — service-layer test coverage) and §4 (open "0-audit-writes" observation)  \n**Repository:** `gula-integration` · **Branch:** `integration/gula-unification-v1`  \n**HEAD:** `2206654dc713ea2de8c564a3207dfe05fde23549` · **Date:** 2026-11-19  \n**Method:** read-only source/test scan (`find`, `grep`, `read`). No test executed (full suite running), no code changed, no DB/Redis touched.

---

## 1. Correcting a stale coverage claim

The workspace summary carried an older list of "active services with no unit test file". A fresh scan shows that list is **stale**: five of the eight named services now have dedicated tests.

| Service | Prior claim | Fresh evidence | Status |
|---|---|---|---|
| `consent_service` | no test | `backend/tests/test_consent.py` | `TESTED` (test present) |
| `device_trust_service` | no test | `backend/tests/test_device_trust.py` | `TESTED` |
| `offline_sync_service` | no test | `backend/tests/test_offline_sync.py` | `TESTED` |
| `risk_based_auth_service` | no test | `backend/tests/test_risk_based_auth.py` | `TESTED` |
| `patient_service` | no test | `test_patient_card.py`, `test_mdm_patient_identity_synthetic.py` | `TESTED` (indirect) |
| `care_continuum_service` | no dedicated unit test | `tests/migrations/test_care_continuum_closure_migration.py` (migration lifecycle only) | `PARTIAL` |
| `hospital_service` | no test | `tests/test_emergency_surgery_workflow_p0.py` (workflow-level) + audit positional regression | `PARTIAL` (no dedicated unit file) |
| `claims_service` | no test | `backend/app/insurance/api/claims.py` has canonical `log_action`; no matching test file found | `NOT IMPLEMENTED` (dedicated test) |

**Conclusion:** only **two** service-layer modules lack a dedicated unit-test file (`hospital_service`, `claims_service`); `claims_service` also has no workflow-level test that names it. This corrects the stale eight-item list. No new test was authored here because a full suite is running and no behavior change is in scope for this workstream.

## 2. Test-file density by service area (dedicated `test_*.py` files)

| Area | Files | Area | Files |
|---|---:|---|---:|
| identity | 33 | national | 7 |
| mpi | 10 | blood_bank | 9 |
| lims | 4 | financial | 4 |
| pharmacy | 2 | radiology | 3 |
| emergency | 1 | nursing | 1 |
| care_continuum | 1 | offline | 3 |
| nhdw | 0 | insurance | 0 |

`nhdw` and `insurance` have zero dedicated test files despite active code; this is consistent with the migration/ownership `BLOCKED` status already recorded in `GOVERNANCE/NATIONAL_SERVICE_INVENTORY.md` (F-085 `InsBase` unregistered; 84 unserved insurance endpoints).

---

## 3. Resolving the "0-audit-writes" observation

`GOVERNANCE/ACTIVATION_FINAL_REPORT.md:121` and `NATIONAL_SERVICE_CONTRACTS.md` §11 record that several cross-service journeys (J1/J5) have "0 audit". `GULA_COMPONENT_INVENTORY.md:115` flagged this as requiring service-layer analysis.

**Resolution (read-only evidence):**

1. **This is not a canonical audit-chain bypass.** The audit-architecture scan (`GULA_AUDIT_ARCHITECTURE_COMPLETENESS_REPORT.md`) found exactly one active chained writer (`log_action`), 59 modules calling it, and zero direct `AuditLog(...)` writes outside it. No module writes critical or clinical events outside the chain.
2. **The "0 audit" journeys are mostly unmaterialised services.** J1/J5 depend on `cc_*` tables with 0 % migration coverage and services named dental / rehabilitation / mental health that are classified `NOT_IMPLEMENTED` (0 ops, 0 tables). There is no service code emitting an audit event because there is no service execution path — not a writer that bypasses the chain.
3. **Where the service exists, canonical audit is wired.** Insurance (`claims`, `coverages`, `referrals`, `payments`, `policies`, `providers`, `network`) calls canonical `log_action` in each API module. Laboratory, pharmacy, radiology, emergency, blood bank and LNursing likewise route through `log_action`, now with correct positional mapping (`AUDIT-POSITIONAL-001`).
4. **Correct interpretation:** "0 audit" is a **journey-level observability gap** (synthetic journeys were never executed end-to-end, so no audit events were produced), not a defect in audit implementation. It remains a genuine blocker for claiming those journeys `TESTED`/`INTEGRATED`, and is **not** silently adjudicated as resolved for release purposes.

**Status:** observation `IMPLEMENTED` (analysis complete, correctly classified). The underlying journeys remain `BLOCKED` (no E2E execution, migration gaps, ADR-C/I/J owner decisions).

---

## 4. Strict status and non-claims

| Item | Status |
|---|---|
| Stale coverage list corrected | `IMPLEMENTED` (read-only evidence) |
| "0-audit-writes" observation classified | `IMPLEMENTED` (not a chain bypass; journey observability gap) |
| Dedicated unit tests for `hospital_service` / `claims_service` | `NOT IMPLEMENTED` |
| Journey E2E verification | `BLOCKED` (migration + owner decisions) |

No `PRODUCTION READY`, no `INDEPENDENTLY VERIFIED` award. No clinical/legal/regulatory/release claim. No test run in this workstream (full suite in progress; no concurrent pytest). No DB/Redis, PHI, secrets, commit, push, merge, PR or deployment. Standing release decision **HOLD**; Stable v1.0.0 **NOT declared**.

---

## 5. Updated 18-service coverage verification (GULA-OWNER-GATE-2026-11-20)

**Additive update.** Sections 1–4 above are preserved verbatim as the 2026-11-19 evidence. This section is a fresh, read-only verification for directive §4.1. **A model, a route or a directory is never counted as service completion.** Only the final `Strict status` column uses the exclusive seven-term status vocabulary; all intermediate columns are observational evidence quoted from existing reports, which retain their source taxonomy (inventory taxonomy IMPLEMENTED / PARTIAL / CROSS_CUTTING / DATA-ONLY / NOT_IMPLEMENTED, §2 of `GOVERNANCE/NATIONAL_SERVICE_INVENTORY.md`). No source taxonomy is relabelled.

### 5.1 Verification matrix

Legend: `API contract` — global contract gate is `0 STABLE / 5 DRAFT / 11 BLOCKED / 3 NOT IMPLEMENTED`, so no service has an award here; `Authz` — route-level guards exist per inventory §4 and scoped probes are `TESTED`, but per-route re-verification is not performed here and SEC-004's 56 unguarded operations remain open; `Audit signal` — inventory observation (✅ / ⚠️ / ❌), not a strict status award; `Frontend` — consumption mapping was **not** verified in this read-only pass; `Offline` — durable behaviour absent across all three engines (`GULA_OFFLINE_SYNC_REASSESSMENT.md` §2–§4); `Tests` — dedicated `test_*.py` files per inventory §3. Strict-status mapping of the inventory verdict is given in §5.2.

| # | Service | Domain owner | DB owner (base / coverage) | API contract | Authz | Audit signal (inventory) | Integration dependencies | Frontend | Offline | Dedicated tests | Operational limitations | Strict status |
|---:|---|---|---|---|---|---|---|---|---|---|---|---|
| 01 | Laboratory | `lims` | registered base; 35 tables, 100 % migrated | `BLOCKED` (no STABLE) | `TESTED` (scoped) | `IMPLEMENTED` (canonical `log_action`) | LIMS workflows, analyzer integration, EHR results | `NOT IMPLEMENTED` (verification) | `NOT IMPLEMENTED` (durable) | 6 files | No E2E journey; no DR proof | `IMPLEMENTED` (engineering scope) |
| 02 | Hospital | `hospital` + `nursing` + critical care | `HospitalBase` 14→1, `NursingBase` 15→13, critical 13→13 | `BLOCKED` | `TESTED` (scoped) | `PARTIAL` (mixed) | Emergency surgery, patient card, care continuum | `NOT IMPLEMENTED` | `NOT IMPLEMENTED` | 4 files | Mixed migration coverage; no E2E | `BLOCKED` |
| 03 | Primary healthcare | `care_continuum` (primary care) | `CareContinuumBase` 5 `cc_*`; closure `20261119_0003` now source-covered | `BLOCKED` | `IMPLEMENTED` (`get_current_user` + lab scope, inventory §4) | `NOT IMPLEMENTED` (0 audit in journey) | Referral, public health, family medicine | `NOT IMPLEMENTED` | `NOT IMPLEMENTED` | 0 | Journey-level observability gap; no E2E | `BLOCKED` |
| 04 | Pharmacy & medication | `pharmacy` | `PharmacyBase` 27/27 | `BLOCKED` | `TESTED` (scoped) | `IMPLEMENTED` | EHR medication, billing, radiology | `NOT IMPLEMENTED` | `NOT IMPLEMENTED` | 3 files | No E2E; no DR proof | `IMPLEMENTED` (engineering scope) |
| 05 | Radiology & imaging | `radiology` | `RadiologyBase` 18/17 (94.4 %) | `BLOCKED` | `TESTED` (scoped) | `IMPLEMENTED` | LIMS orders, pharmacy, emergency | `NOT IMPLEMENTED` | `NOT IMPLEMENTED` | 5 files | 1 unmigrated table; no E2E | `IMPLEMENTED` (engineering scope) |
| 06 | Emergency & ambulance | `emergency` | registered base; 12/12 | `BLOCKED` | `TESTED` (scoped) | `IMPLEMENTED` | Hospital, ICU/LIMS, blood bank | `NOT IMPLEMENTED` | `NOT IMPLEMENTED` | 2 files | Strict gate: emergency surgery 2/4 on migrated schema; no E2E | `IMPLEMENTED` (engineering scope) |
| 07 | Blood bank | `blood_bank` | registered base; 17/17 | `BLOCKED` | `TESTED` (scoped) | `NOT IMPLEMENTED` (columns only) | LIMS, hospital transfusion | `NOT IMPLEMENTED` | `NOT IMPLEMENTED` | 8 files | No audit path; no E2E | `BLOCKED` |
| 08 | Immunization | `care_continuum` + `ehr` | `CareContinuumBase` 6 + `EHRBase` 1; closure now source-covered | `BLOCKED` | `IMPLEMENTED` (care-continuum scope) | `NOT IMPLEMENTED` | Public health, EHR, cold chain | `NOT IMPLEMENTED` | `NOT IMPLEMENTED` | 0 | 0-audit journey; no E2E | `BLOCKED` |
| 09 | Public health & surveillance | `public_health` + `nhdw` | `NHDWBase` 14/14 (93.3 %) + 6 base tables | `BLOCKED` | `TESTED` (scoped) | `NOT IMPLEMENTED` | NHDW reporting, immunization, care continuum | `NOT IMPLEMENTED` | `NOT IMPLEMENTED` | 2 files | No audit path; no E2E | `BLOCKED` |
| 10 | Dental | no service | no tables | `NOT IMPLEMENTED` | `NOT IMPLEMENTED` | `NOT IMPLEMENTED` | none | `NOT IMPLEMENTED` | `NOT IMPLEMENTED` | 0 | Nothing beyond incidental strings | `NOT IMPLEMENTED` |
| 11 | Maternal & child health | `care_continuum` (maternal) | `CareContinuumBase` 7; closure now source-covered | `BLOCKED` | `IMPLEMENTED` (care-continuum scope) | `NOT IMPLEMENTED` | Referral, EHR, community care | `NOT IMPLEMENTED` | `NOT IMPLEMENTED` | 0 | 0-audit journey; no E2E | `BLOCKED` |
| 12 | Chronic disease mgmt | `care_continuum` (chronic) | `CareContinuumBase` 5; closure now source-covered | `BLOCKED` | `IMPLEMENTED` (care-continuum scope) | `NOT IMPLEMENTED` | Primary care, referral, patient tasks | `NOT IMPLEMENTED` | `NOT IMPLEMENTED` | 1 | 0-audit journey; no E2E | `BLOCKED` |
| 13 | Rehabilitation / physio | no service | no tables | `NOT IMPLEMENTED` | `NOT IMPLEMENTED` | `NOT IMPLEMENTED` | none | `NOT IMPLEMENTED` | `NOT IMPLEMENTED` | 0 | Nothing beyond incidental strings | `NOT IMPLEMENTED` |
| 14 | Mental health | analytics only | no dedicated tables | `NOT IMPLEMENTED` | `NOT IMPLEMENTED` | `NOT IMPLEMENTED` | reporting only | `NOT IMPLEMENTED` | `NOT IMPLEMENTED` | 0 | Data/analytics signals only | `NOT IMPLEMENTED` |
| 15 | Referral & continuity | `care_continuum` (referral) | `CareContinuumBase` 12; closure now source-covered | `BLOCKED` | `IMPLEMENTED` (care-continuum scope) | `NOT IMPLEMENTED` | Hospital, primary care, home care, EHR | `NOT IMPLEMENTED` | `NOT IMPLEMENTED` | 0 | 0-audit journey; no E2E | `BLOCKED` |
| 16 | Insurance & claims | `insurance` + billing | `InsBase` 30 **unregistered** + `FinBase` billing | `BLOCKED` | `TESTED` (scoped) | `IMPLEMENTED` (canonical in each API module) | Claims, billing, patient identity | `NOT IMPLEMENTED` | `NOT IMPLEMENTED` | 3 files | 84 unserved endpoints; 30 tables invisible to Alembic; ADR-G/I | `BLOCKED` |
| 17 | Home healthcare | `care_continuum` (home care) | `CareContinuumBase` 2; closure now source-covered | `BLOCKED` | `IMPLEMENTED` (care-continuum scope) | `NOT IMPLEMENTED` | Referral, community care | `NOT IMPLEMENTED` | `NOT IMPLEMENTED` | 0 | 0-audit journey; no E2E | `BLOCKED` |
| 18 | Medical equipment | biomedical / devices | registered base; 12 + 10 tables, 100 % | `BLOCKED` | `TESTED` (scoped) | `NOT IMPLEMENTED` | Analyzer integration, hospital, LIMS | `NOT IMPLEMENTED` | `NOT IMPLEMENTED` | 1 | No audit path; no E2E | `BLOCKED` |

### 5.2 Evidence and interpretation notes

1. **Historical vs current migration coverage.** The inventory's `0 %` for `cc_*` tables is a 2026-11-17 observation. The source-based ORM report (2026-11-19) shows the care-continuum closure migration `20261119_0003` created 45 `cc_*` + 17 `national_*` tables, so those tables are now source-covered. The historical observation is retained; **runtime E2E remains `BLOCKED`** — DDL closure is not service integration.
2. **Complete services.** Laboratory, pharmacy, radiology and emergency are `IMPLEMENTED` in engineering scope only (API + models + migrations + canonical audit + dedicated tests). None is `INTEGRATED`, `INDEPENDENTLY VERIFIED` or `PRODUCTION READY`. **Verdict-to-strict mapping (non-destructive):** the four inventory `IMPLEMENTED` verdicts map to strict `IMPLEMENTED` (engineering scope); the nine inventory `PARTIAL`/`CROSS_CUTTING`/`DATA-ONLY` verdicts map to strict `BLOCKED` for release; the three signal-only verdicts map to strict `NOT IMPLEMENTED`. The inventory's own taxonomy is not rewritten.
3. **No service satisfies the full directive §4.1 checklist.** Frontend consumption mapping is `NOT IMPLEMENTED` for all 18 (Web has 15 unit files + 13 e2e specs but no per-service mapping verified here). Durable offline behaviour is `NOT IMPLEMENTED` for all 18 (three in-memory engines; digests only, no payload recovery). No clinical journey is E2E verified (`0 E2E_VERIFIED`).
4. **"0 audit" is an observability gap, not a chain bypass** (§3 above). It persists as a blocker for J1/J5 journey claims and is not adjudicated as resolved for release.
5. **No test was run, no code changed, no route count or model existence promoted to completion.** Standing decision **HOLD**; Stable v1.0.0 **NOT declared**; no `PRODUCTION READY` and no new `INDEPENDENTLY VERIFIED` award in this section.

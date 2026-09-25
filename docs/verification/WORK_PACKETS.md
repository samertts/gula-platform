# Work Packets

**Generated:** 2026-09-25 · **Head:** `d8c2a31b`

Ordered by blast radius × clinical or security impact × evidence weakness. Each
packet defines what must be _proven_, not how to write the code, except where the
implementation is itself the verification boundary.

---

## Claim table

The shared work queue for these packets. `CLAIMED_BY` follows the collaboration
protocol: a packet claimed by one agent is not worked by the other. Roles —
**ABU_ALI**: PostgreSQL, Alembic, schema truth, migration verification, concurrency,
failure injection, clinical safety evidence, recovery evidence. **MUSTAFA**:
orchestration, architecture, `gula_intel`, coherence, contracts, integration,
readiness, dependency analysis.

| TASK_ID | PRIORITY | OWNER                            | STATUS          | DEPENDENCIES                  | BLOCKERS                                      | EVIDENCE_REQUIRED                              | CLAIMED_BY                  |
| ------- | -------- | -------------------------------- | --------------- | ----------------------------- | --------------------------------------------- | ---------------------------------------------- | --------------------------- |
| WP-001  | P0       | Critical Care + Platform/Alembic | **BLOCKED**     | NR-003, NR-028                | HUMAN_APPROVAL_REQUIRED — schema change       | REAL_HTTP_POSTGRES on canonical head           | — (blocked; packets issued) |
| WP-002  | P0       | Clinical platform                | UNCLAIMED       | —                             | none                                          | FAILURE_INJECTION per stage + durable record   | —                           |
| WP-003  | P1       | Identity + Clinical governance   | **BLOCKED**     | —                             | HUMAN_APPROVAL_REQUIRED — authorization model | owner names the capability                     | — (decision)                |
| WP-004  | P1       | Identity                         | UNCLAIMED       | NR-025                        | none — **schema blocker cleared 2026-09-25**  | REAL_HTTP_POSTGRES lockout behaviour           | —                           |
| WP-005  | P1       | Platform / Data                  | **IN_PROGRESS** | —                             | none                                          | RECOVERY_PROOF — interrupt, restart, re-assert | **ABU_ALI**                 |
| WP-006  | P1       | Platform / per-domain owners     | UNCLAIMED       | WP-001 for pharmacy/radiology | partial                                       | CONCURRENCY_POSTGRES per domain                | —                           |
| WP-007  | P1       | National + Core                  | **BLOCKED**     | —                             | HUMAN_APPROVAL_REQUIRED — ownership decision  | ownership decision                             | — (decision)                |

**Claimed now:** WP-005 by ABU_ALI — the only P1 in the PostgreSQL/recovery lane with
no blocker and no human decision in front of it. FM-010–013 and FM-022–025 have **no
mechanism** at all, so this is net-new capability rather than a re-measurement.

**Not claimed, and why:** WP-001/003/007 are `HUMAN_APPROVAL_REQUIRED` — recorded, not
waited on. WP-002 and WP-006 are in this lane and unclaimed; WP-002 is next. WP-004's
schema blocker was cleared by the canonical-head measurement, so it is now executable
and is queued behind WP-005.

---

## WP-001 — Make the ICU verification columns reachable · **P0** · needs human authorization

| Field               | Value                                                                                                                                                                                                                                                                                                                                                                                |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Finding             | NR-023                                                                                                                                                                                                                                                                                                                                                                               |
| Risk                | A high-alert infusion (norepinephrine, insulin, heparin, potassium chloride…) cannot be activated. The second-actor safety check returns 500.                                                                                                                                                                                                                                        |
| Operation           | `POST /critical-care/infusions/{id}/verify`                                                                                                                                                                                                                                                                                                                                          |
| Failure mode        | FM-019 schema mismatch, FM-026 masking                                                                                                                                                                                                                                                                                                                                               |
| Invariant           | INV-SCHEMA-01, INV-SCHEMA-02                                                                                                                                                                                                                                                                                                                                                         |
| Current evidence    | POSTGRESQL — 500, `UndefinedColumn`, 0 receipts, 0 audit rows                                                                                                                                                                                                                                                                                                                        |
| Missing evidence    | The same operation succeeding on a database built only by migrations                                                                                                                                                                                                                                                                                                                 |
| Minimum test        | The existing slice, with its tripwires rewritten to Part B's expectations                                                                                                                                                                                                                                                                                                            |
| Environment         | PostgreSQL 16+, schema from migrations alone                                                                                                                                                                                                                                                                                                                                         |
| Negative proof      | Already executed — see the evidence package, Part C. Adding the columns makes every invariant pass; dropping them restores the defect.                                                                                                                                                                                                                                               |
| Acceptance          | `alembic upgrade <target>` on an empty database yields `critical_care_infusions` with `verified_by` and `verified_at`, and B1–B9 pass unmodified                                                                                                                                                                                                                                     |
| **Stop conditions** | **A new migration is a schema change and needs explicit human approval per `CLAUDE.md`. Not written here.** Do not modify `20260820_0005` or any other historical revision. The cleanest fix is to make `head` applicable — i.e. fix NR-003 — rather than to duplicate the column addition onto another branch; duplicating risks a double-add on databases that later reach `head`. |
| Regression guard    | `test_schema_drift_guard.py`, already merged                                                                                                                                                                                                                                                                                                                                         |

---

## WP-002 — A failing clinical command must leave a trace · **P0**

| Field                 | Value                                                                                                                                                                                                                                                                                            |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Finding               | NR-024                                                                                                                                                                                                                                                                                           |
| Risk                  | Repeated failed attempts to activate a vasopressor infusion leave the platform with no evidence that anything was attempted. Incident reconstruction is impossible.                                                                                                                              |
| Failure mode          | FM-016 missing audit, FM-027 shared-dependency failure path                                                                                                                                                                                                                                      |
| Invariant             | INV-AUDIT-01                                                                                                                                                                                                                                                                                     |
| Current evidence      | REAL_HTTP_POSTGRES — 500 with 0 receipts and 0 audit rows, asserted as a delta so it cannot pass vacuously                                                                                                                                                                                       |
| Missing evidence      | Any record surviving a failed protected command                                                                                                                                                                                                                                                  |
| Minimum test          | Provoke a failure at each `failure_injection` stage and assert that an audit row or metric exists in every case                                                                                                                                                                                  |
| Root cause to address | The route's `except` branch calls `guard.reject`, which writes to the database that just refused the statement. The rejection path shares a dependency with the thing it guards. A durable fallback — structured log, metric, outbox — is needed for the case where the database is the failure. |
| Acceptance            | For every injected stage, exactly one durable record of the attempt exists, and no partial clinical effect                                                                                                                                                                                       |
| Stop conditions       | Do not weaken `guard.reject`. Do not swallow the exception to make a test pass.                                                                                                                                                                                                                  |

---

## WP-003 — Decide the ICU authorization model · **P1** · decision, not code

| Field              | Value                                                                                                                                                                                                                                 |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Finding            | new — recorded in `INVARIANTS.md` §"deliberately not asserted"                                                                                                                                                                        |
| Measured           | The whole `critical-care` router carries `dependencies=[Depends(require_permission("system:admin"))]`. Of the 16 roles in `EXTENDED_VALID_ROLES`, exactly **one** — `master_admin` — holds `system:admin`.                            |
| Consequence        | No intensivist, nurse, `doctor`, `lab_admin` or `technician` can record vitals, set a ventilator, start an infusion or perform the second-actor verification. Conversely any platform super-admin can perform a bedside clinical act. |
| Invariant          | INV-AUTHZ-01 holds as written; whether it is the _right_ boundary is the question                                                                                                                                                     |
| Required           | The owner names the capability each ICU operation should require, and which roles hold it                                                                                                                                             |
| **Stop condition** | **Not changed here.** Authorization changes need human approval per `CLAUDE.md`, and a clinical access model is not a defect to patch unilaterally.                                                                                   |

---

## WP-004 — Prove or remove account lockout · **P1**

| Field            | Value                                                                                                                                                                                                                                |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Finding          | NR-025                                                                                                                                                                                                                               |
| Risk             | `failed_login_attempts` and `locked_until` are declared by both `LabUser` and `User` and exist in **neither** physical table. Either the brute-force control is dead, or any code path touching it raises. Which one is **UNKNOWN**. |
| Failure mode     | FM-006, FM-007                                                                                                                                                                                                                       |
| Invariant        | INV-AUTHN-02                                                                                                                                                                                                                         |
| Current evidence | POSTGRESQL — the drift, pinned exactly                                                                                                                                                                                               |
| Missing evidence | Repeated failed authentications against real PostgreSQL, observing whether a lock is recorded, whether it is enforced, and whether it survives a restart                                                                             |
| Minimum test     | N failed authentications, then a correct credential; assert refusal while locked and success after expiry                                                                                                                            |
| Environment      | REAL_HTTP_POSTGRES                                                                                                                                                                                                                   |
| Acceptance       | Either lockout is proven end to end, or the dead attributes are removed from the ORM so nothing writes them                                                                                                                          |
| Stop conditions  | Do not test against a shared database. Do not add the columns without WP-001's authorization path.                                                                                                                                   |

---

## WP-005 — Give the layer a recovery mechanism · **P1**

| Field           | Value                                                                                                                                                                                                   |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Finding         | FM-010 – FM-013, FM-022 – FM-025 have **no mechanism**                                                                                                                                                  |
| Risk            | No claim about database disconnect, service restart or dependency failure can be supported by this repository today, although the app ships a circuit breaker, degraded mode and an auto-repair engine. |
| Invariant       | INV-RECOVERY-01                                                                                                                                                                                         |
| Minimum test    | Interrupt the database mid-transaction on a disposable instance, restart, and re-assert INV-TXN-01, INV-IDEM-01 and INV-AUDIT-01 for one operation                                                      |
| Stop conditions | Disposable instances only. Never inject a failure that could damage persistent or shared data.                                                                                                          |

---

## WP-006 — Extend the slice to the six untested guarded domains · **P1**

| Field            | Value                                                                                                                                                                                                                    |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Measured         | 23 `ClinicalCommandGuard`-protected commands outside blood_bank; `lims` 7, `radiology` 4, `critical_care` 7 more, `pharmacy` 2, `ems` 1, `hospital` 1. PostgreSQL tests: 0 for lims, radiology, pharmacy, ems, hospital. |
| Invariant        | INV-IDEM-01, INV-CAS-01, INV-CONC-01, INV-TENANT-01, INV-AUDIT-01 per operation                                                                                                                                          |
| Current evidence | none                                                                                                                                                                                                                     |
| Minimum test     | Per domain, the nine-scenario shape from the ICU slice, using `harness` — the harness is why this is now a day's work per domain rather than a week's                                                                    |
| Blocked by       | WP-001 for any domain whose tables drift: `pharmacy_prescriptions` (15 columns) and `radiology_orders` (7) will fail the same way ICU did                                                                                |
| Acceptance       | Each domain has an evidence package with the same table shape                                                                                                                                                            |

---

## WP-007 — Resolve the `national_facilities` dual ownership · **P1**

| Field          | Value                                                                                                                                                                                                                                                              |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Finding        | NR-006, sharpened                                                                                                                                                                                                                                                  |
| Measured       | One physical table, two ORM owners. `app.national.domain.facility.Facility` declares **24 columns the table lacks**; `app.models.clinical_scope.NationalFacility` matches exactly. Which module a caller imports decides whether the write succeeds.               |
| Conflict       | Task #74 records "retire the duplicate `national_facilities` ORM owner" as completed, yet both classes load in one process on this branch. **Not reconciled** — the register and the running code disagree and the discrepancy is recorded rather than guessed at. |
| Invariant      | INV-SCHEMA-03                                                                                                                                                                                                                                                      |
| Minimum test   | `test_only_the_known_table_is_mapped_by_more_than_one_class` already fails if this spreads; the packet is to make the set empty                                                                                                                                    |
| Stop condition | Retiring an owner is an ownership decision with FK consequences; do not delete a model to make a guard pass.                                                                                                                                                       |

---

## Packet summary

| ID     | Severity | Blocked on                              | Type            |
| ------ | -------- | --------------------------------------- | --------------- |
| WP-001 | P0       | human authorization for a schema change | fix             |
| WP-002 | P0       | —                                       | fix + prove     |
| WP-003 | P1       | owner decision                          | decision        |
| WP-004 | P1       | WP-001                                  | prove or remove |
| WP-005 | P1       | —                                       | build mechanism |
| WP-006 | P1       | WP-001                                  | prove           |
| WP-007 | P1       | ownership decision                      | reconcile       |

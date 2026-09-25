# GULA Master Negative Register

**Generated:** 2026-09-25 · **Head:** `288b57fe` · **production_ready:** `false`
**Machine-readable companion:** [`GULA_MASTER_NEGATIVE_REGISTER.json`](./GULA_MASTER_NEGATIVE_REGISTER.json)
**Remediation plan:** [`GULA_MASTER_REMEDIATION_PLAN.md`](./GULA_MASTER_REMEDIATION_PLAN.md)

## 0. How to read this register (integrity statement)

This is a **first evidence-driven pass**, not a completed audit.

Every finding below is backed by something that was **actually executed or read** in this
session. Nothing was inferred from plausibility. Where evidence is weak, the finding says so.

> **Absence of a finding in a category does NOT mean that category is clean.**
> The majority of the 123 requested risk categories were **not audited**. See
> §7 Audit Coverage Matrix and finding **NR-013**. Treat unaudited categories as
> _unknown risk_, never as _no risk_.

Existing architecture standards were **linked, not duplicated** — see
`CANONICAL_ARCHITECTURE.md`, `ARCHITECTURE_RULES_PROGRAM_CONSTITUTION_001.md`,
`MODULE_DEPENDENCY_MATRIX.md`, `ENTITY_CATALOG.md`, `DEPENDENCY_APPROVAL_POLICY.md`,
and `docs/adr/`.

## 1. Summary

| Severity  | Count  | Fixed & verified | Partially closed | Accepted design | Open / not started |
| --------- | ------ | ---------------- | ---------------- | --------------- | ------------------ |
| P0        | 6      | 4                | 0                | 0               | 2                  |
| P1        | 7      | 2                | 2                | 0               | 3                  |
| P2        | 6      | 0                | 0                | 1               | 5                  |
| P3        | 3      | 0                | 0                | 0               | 3                  |
| **Total** | **22** | **6**            | **2**            | **1**           | **13**             |

The first pass recorded NR-001..NR-015. NR-016..NR-022 were added by later sessions;
their full detail is in the JSON companion only.

**Only remaining blocker to `alembic upgrade head`:** **NR-003** — pharmacy primary-key
type divergence.

That is not the only open P0. **NR-019** is an open, verified authorization defect: every
adaptive-auth endpoint taking `account_id` binds the caller zero times. It is unfixed
because the fix shape is a policy decision, not because it is low risk. A deployment
claim that cites NR-003 alone would be false.

## 2. Findings index

| ID     | Sev | Domain                   | Title                                                                           | Status                             |
| ------ | --- | ------------------------ | ------------------------------------------------------------------------------- | ---------------------------------- |
| NR-001 | P0  | Platform/Alembic         | Duplicate revision id made `clinical_command_receipts` unreachable              | FIXED — VERIFIED                   |
| NR-002 | P0  | Platform/Alembic         | Three unmerged heads made clean deployment impossible                           | FIXED — VERIFIED                   |
| NR-003 | P0  | Pharmacy                 | PK type divergence blocks any full `upgrade head`                               | **OPEN — BLOCKED**                 |
| NR-004 | P1  | Blood Bank               | Shared transition table shadowed the blood-unit `reserved` state                | FIXED — VERIFIED                   |
| NR-005 | P1  | Platform/Alembic         | Unguarded duplicate index could never succeed                                   | FIXED — VERIFIED                   |
| NR-006 | P1  | National + Core          | `national_facilities` mapped by two ORM classes                                 | OPEN — DECISION                    |
| NR-007 | P1  | Clinical/Blood Bank      | State machine is entity-agnostic by construction                                | OPEN — ARCH DECISION               |
| NR-008 | P2  | Platform                 | `signxml` missing from lock file                                                | OPEN                               |
| NR-009 | P2  | Platform CI              | Artifact quota exhausted; evidence jobs all red                                 | OPEN — EXTERNAL                    |
| NR-010 | P2  | Platform CI              | `if:always()` upload masks the true failing step                                | OPEN                               |
| NR-011 | P2  | frontend-v3              | Mobile nav accessible name contradicts its test                                 | OPEN                               |
| NR-012 | P2  | Clinical                 | Replay returns deterministic 409, not original response                         | ACCEPTED DESIGN                    |
| NR-013 | P3  | Platform                 | Audit coverage is narrow                                                        | NOT STARTED                        |
| NR-014 | P3  | Platform                 | No verified national capacity numbers                                           | NOT STARTED — GAP                  |
| NR-015 | P3  | Platform CI              | Postgres auth failure in migration gate                                         | OPEN — LOW EVIDENCE                |
| NR-016 | P0  | Biomedical               | Completing a work order freed a still-faulty device, for any tenant, repeatedly | FIXED — VERIFIED                   |
| NR-017 | P1  | Platform-wide            | Mutating service methods select a row by id with no tenant predicate            | MEASURED — count is an upper bound |
| NR-018 | P1  | Command Center           | Emergency `resolved_by` is caller-supplied free text                            | OPEN — DECISION                    |
| NR-019 | P0  | Identity / adaptive auth | Every `account_id` endpoint binds the caller zero times (IDOR)                  | **OPEN — DECISION**                |
| NR-020 | P1  | Blood Bank               | Only 2 of 7 declared `TransfusionStatus` states had a transition key            | PARTIALLY CLOSED                   |
| NR-021 | P0  | Command Center           | An emergency could be resolved cross-tenant, repeatedly and concurrently        | FIXED — VERIFIED                   |
| NR-022 | P2  | Platform CI              | Constitution Compliance cannot pass any backend change: 3 of 25 rules misfire   | OPEN — MEASURED                    |

Full per-finding detail (root cause, all impact axes, minimal safe fix, acceptance
criteria, regression risk, owner, wave) is in the JSON companion.

## 3. The most important discovery

**NR-001 was far wider than Blood Bank.** `ClinicalCommandGuard` — and therefore the
`clinical_command_receipts` table that never existed — is used by **eight domains**:

```
blood_bank · pharmacy · radiology · lims · ems · critical_care · clinical · routes
```

So the shadowed migration disabled the durable idempotency claim for **every guarded
clinical command across the platform**, not only transfusion. Earlier documentation
described this as a Blood Bank issue; that understated it.

## 4. Contradiction register

| ID         | Contradiction                                                                                                                                                                                                                                                           | Evidence       | Status                                                    |
| ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------- | --------------------------------------------------------- |
| C-01       | Policy "every migration must be idempotent" vs. a shipped unguarded migration                                                                                                                                                                                           | NR-005         | **VERIFIED** — resolved                                   |
| C-02       | Policy "never modify an existing migration" vs. the need to repair a migration that never ran anywhere                                                                                                                                                                  | NR-001         | **VERIFIED** — resolved on evidence that no DB applied it |
| C-03       | Pharmacy ORM uses `String(26)` ULIDs; pharmacy migrations create `Integer` ids                                                                                                                                                                                          | NR-003         | **VERIFIED** — unresolved                                 |
| C-04       | Per-entity clinical state semantics vs. one shared entity-agnostic transition table                                                                                                                                                                                     | NR-004, NR-007 | **VERIFIED** — partially resolved                         |
| C-05       | `production_ready=false` gating vs. CI that structurally cannot certify (all evidence jobs fail at upload)                                                                                                                                                              | NR-009         | **VERIFIED**                                              |
| C-06       | Domain ownership boundaries vs. two domains mapping one physical table                                                                                                                                                                                                  | NR-006         | **VERIFIED**                                              |
| C-07       | Reproducible-build intent vs. lock file that cannot start the app                                                                                                                                                                                                       | NR-008         | **VERIFIED**                                              |
| C-08       | "National scale" ambition vs. absence of any capacity numbers                                                                                                                                                                                                           | NR-014         | **VERIFIED as a gap**                                     |
| C-09..C-20 | offline-first vs clinical authority · CRDT vs clinical truth · privacy vs emergency access · consent withdrawal vs legal retention · AI assistance vs clinical responsibility · HA vs strong consistency · green vs performance · citizen ownership vs record integrity | —              | **NOT AUDITED** — candidates only, no evidence gathered   |

## 5. Intersection register

| ID   | Change point                                                                               | Domains affected                                                                 | Evidence                                                   |
| ---- | ------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| I-01 | `ClinicalCommandGuard` / `clinical_command_receipts`                                       | blood_bank, pharmacy, radiology, lims, ems, critical_care, clinical, routes      | grep of guard usage (8 packages)                           |
| I-02 | Alembic graph                                                                              | every domain — no schema without it                                              | NR-001/002                                                 |
| I-03 | Pharmacy id type                                                                           | pharmacy + any FK referencing pharmacy entities                                  | NR-003                                                     |
| I-04 | Blood Bank state machine                                                                   | units, orders, samples, crossmatches, transfusions, reactions (one shared table) | NR-004/007                                                 |
| I-05 | `national_facilities`                                                                      | national platform + core clinical scope + authorization scoping                  | NR-006                                                     |
| I-06 | Identity change → Patient → Consent → Clinical → Lab → Pharmacy → Audit → FHIR → Analytics | all                                                                              | **NOT AUDITED** — asserted by the brief, not verified here |

**Rule:** none of I-01..I-05 may be remediated inside a single domain in isolation.

## 6. Source-of-truth / data-ownership matrix (partial)

Only rows with real evidence are filled. Everything else is explicitly unaudited.

| Domain / data                                                | Source of truth                             | Writable by                           | Consumers                                | Failure behaviour                | Status                |
| ------------------------------------------------------------ | ------------------------------------------- | ------------------------------------- | ---------------------------------------- | -------------------------------- | --------------------- |
| Clinical command idempotency claims                          | `clinical_command_receipts` (single table)  | `ClinicalCommandGuard` only           | 8 domains (I-01)                         | Guard fails closed → 409         | **VERIFIED**          |
| Blood unit lifecycle state                                   | `blood_bank_units.status` via state machine | Blood Bank routes/service under guard | traceability, reservations, issue        | Transition rejected → 422        | **VERIFIED**          |
| Blood inventory movements                                    | `blood_bank_inventory_movements`            | Blood Bank service                    | traceability, reconciliation             | Rolled back with the transaction | **VERIFIED**          |
| `national_facilities`                                        | **CONTESTED — two ORM owners**              | `app/models` and `app/national`       | authorization scoping, national platform | Undefined                        | **CONFLICT (NR-006)** |
| Pharmacy catalog / substitution                              | Undefined — schema and ORM disagree         | n/a (cannot deploy)                   | pharmacy                                 | Migration fails                  | **BROKEN (NR-003)**   |
| Patient / MPI / National ID                                  | —                                           | —                                     | —                                        | —                                | **NOT AUDITED**       |
| Consent, provider identity, device identity, analytics, FHIR | —                                           | —                                     | —                                        | —                                | **NOT AUDITED**       |

828 mapped tables were scanned for dual ownership; exactly one conflict was found (NR-006).

## 7. Audit coverage matrix

| Category group                                                                              | Status                                         |
| ------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| Migration safety, deployment reproducibility                                                | **AUDITED — findings NR-001/002/003/005**      |
| Clinical state machines (Blood Bank)                                                        | **AUDITED — NR-004/007**                       |
| Idempotency, concurrency, transaction boundaries, failure/retry (Blood Bank + shared guard) | **VERIFIED in Phases 14B/14B.1/14C**           |
| Authorization / IDOR (Blood Bank cross-facility only)                                       | **PARTIALLY VERIFIED** — Blood Bank paths only |
| Source-of-truth / data ownership (ORM table mapping)                                        | **AUDITED — NR-006**                           |
| Dependency reproducibility                                                                  | **AUDITED — NR-008**                           |
| CI/CD failure classification                                                                | **AUDITED — NR-009/010/015**                   |
| Frontend accessibility (one component)                                                      | **AUDITED — NR-011**                           |
| National identity / MPI / duplicate patients / newborn / deceased / proxy                   | **NOT STARTED**                                |
| Consent, break-glass, privacy, purpose-of-use                                               | **NOT STARTED**                                |
| Offline / sync / CRDT / event ordering / outbox / inbox                                     | **NOT STARTED**                                |
| FHIR / HL7 / DICOM / terminology                                                            | **NOT STARTED**                                |
| AI safety and governance                                                                    | **NOT STARTED**                                |
| Security (authn, secrets, PKI, uploads, export, insider threat)                             | **NOT STARTED**                                |
| Backup / restore / DR / failover / split-brain                                              | **NOT STARTED**                                |
| Performance, scalability, capacity, Green GULA                                              | **NOT STARTED — NR-014**                       |
| Legal, retention, portability, localization, accessibility programme-wide                   | **NOT STARTED**                                |
| Pharmacy, imaging, hospital, EMS, public health, maternal/child, vaccination domains        | **NOT STARTED** (except NR-003)                |

## 8. Offline capability matrix

**NOT STARTED.** No offline/sync behaviour was examined in this pass. Producing this
matrix requires a dedicated pass over the sync layer, and it is scheduled in the
remediation plan rather than guessed at here.

## 9. Verification / evidence gap matrix (Blood Bank — the only certified-depth domain)

| Control                                                                 | Evidence              | Result              |
| ----------------------------------------------------------------------- | --------------------- | ------------------- |
| HTTP replay idempotency (reservation, issue)                            | Phase 14B             | VERIFIED            |
| Concurrent same-key HTTP (reservation, issue)                           | Phase 14B / 14B.1     | VERIFIED            |
| Sequential + concurrent payload collision                               | Phase 14B             | VERIFIED            |
| Failure before commit (7 boundaries)                                    | Phase 14C             | VERIFIED            |
| Failure after commit / lost response                                    | Phase 14C             | VERIFIED            |
| Lifecycle E2E (reserve → trace → release)                               | Phase 14D             | VERIFIED            |
| Cross-facility IDOR                                                     | Phase 14B             | VERIFIED            |
| Schema built by migrations alone                                        | Migration remediation | VERIFIED            |
| Full `upgrade head`                                                     | —                     | **FAILED — NR-003** |
| Existing-database upgrade path                                          | —                     | **NOT VERIFIED**    |
| Contract / property-based / mutation / chaos / performance / DR restore | —                     | **NOT STARTED**     |

## 10. Decisions required (do not guess)

| Ref    | Decision                                                                     | Owner                    |
| ------ | ---------------------------------------------------------------------------- | ------------------------ |
| NR-003 | Canonical pharmacy primary-key type, then a migration strategy for 23 tables | Pharmacy + Platform/Data |
| NR-006 | Which domain owns `national_facilities`; the other becomes a consumer        | National + Core          |
| NR-007 | Per-entity state machine keying vs. accepting union semantics                | Clinical Standards       |
| NR-012 | Whether stored-response replay is required by API clients                    | Clinical Standards + API |
| NR-014 | National capacity targets                                                    | Programme                |

# MPI Cross-Component Impact Analysis — PROPOSED, NOT APPROVED

**Status:** `PROPOSED — NOT APPROVED`. Analysis/planning artifact only. No component is modified.
**Repository:** `/home/samertts/workspace/projects/gula-integration` @
`integration/gula-unification-v1`, HEAD `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0`.
**Release:** HOLD. D-020 / D-021 `PENDING_APPROVAL`. D-MPI-1 `NEEDS_OWNER_DECISION`.
**Primary inventories:** `MPI_CROSS_DOMAIN_INTEGRITY_REPORT.md` (§3–§6),
`MPI_INTEGRITY_CONCURRENCY_REMEDIATION_REPORT.md` (§9, 13-row domain table).
**Architecture basis:** `MPI_SERIALIZATION_ARCHITECTURE_DECISION.md`.

**Hard exclusions (restated):** this document does **not** repoint any cross-domain foreign key or
soft reference, does **not** propose MPI unmerge/split, and does **not** canonicalize NHID or merge
national identity stores. Ownership of the reference sites is unresolved; they are documented only.

Evidence classes: `VERIFIED_IN_SOURCE` (file read), `FROM_GOVERNANCE` (stated in an existing report),
`INFERRED` (design reasoning), `UNKNOWN_OWNERSHIP`, `OWNER_DECISION` (D-MPI-3).

---

## 1. The ~90 reference sites — what is actually known

- The documents state an **approximate `~90`** (`~90 FK/soft-reference sites`), not an enumerated
  list. The phrase appears at `MPI_CROSS_DOMAIN_INTEGRITY_REPORT.md:160`,
  `MPI_INTEGRITY_CONCURRENCY_REMEDIATION_REPORT.md:23,340`, `IMPLEMENTATION_BACKLOG.md:28`,
  `IMPLEMENTATION_PROGRESS.md:76`, `NEXT_PHASE_AUTHORIZATION_REQUEST.md:60,126`,
  `CHANGE_RISK_REGISTER.md:27` (`FROM_GOVERNANCE`).
- **No file enumerates 90 individual rows, and no numeric per-category breakdown exists.** §3 of the
  cross-domain report groups sites qualitatively by domain/class; the concurrency report §9 lists a
  13-row domain table. Treating `~90` as a precise, classified count would be fabrication.
- Independent scale datum (`VERIFIED_IN_SOURCE`, **not** equated to the 90):
  `rg 'citizen_id = Column' backend/app --glob '*.py'` → **96 declarations**
  (national 39, citizen_platform 18, ehr 11, services 9, national_data 9, care_continuum 8,
  routes 7, identity 7, governance 7, blood_bank 4, pharmacy 3, models 3, health_data 2,
  security 1, core 1).
- Governing rule (`FROM_GOVERNANCE`, `MPI_CROSS_DOMAIN_INTEGRITY_REPORT.md:98-99`): **"canonical vs
  alias"** — every reference is canonical within its own store; MPI repointing today covers exactly
  **one alias bridge, `IdentityClaim`** (`resolver.py:506-511`). This is the only repoint that occurs.

### 1.1 Classification (as the reports actually classify them)

| Class used in the documents | Evidence | Source examples (`VERIFIED_IN_SOURCE`) |
|---|---|---|
| **Direct BigInteger FK into MPI `citizens`** | `MPI_CROSS_DOMAIN_INTEGRITY_REPORT.md:49-55` | `IdentityClaim.citizen_id` (repointed), `MergeAudit.primary/secondary_citizen_id` (ledger), `TestResult.citizen_id` (`models/test_result.py:52`), `CitizenLink.citizen_id` (`models/canonical_patient.py:93`) |
| **Audit/ledger reference** | `:53`; concurrency report `:203` — "ledger, not repointed", risk informational | `mpi_merge_audit` primary/secondary; `national_merge_audit` (`national/domain/merge_record.py:47-48`) |
| **External identifier / separate store (String(26) ULID)** | `:57-66`, `:98-99` | `national/domain/citizen.py:50,91-93`; `national/domain/patient.py:11,43-45`; `citizen_ulid` (`services/mpi/models.py:45,61`) |
| **Soft reference (no FK)** | `:78-80` | `Consent.gpid`, pharmacy plain columns, `national_id.py:9`, `patient_ulid` projections |
| **Integer FKs into LIMS `patients`** | `:82-87` | `lab_order`, `claim`, `canonical_patient`, `authorization`, nursing/billing/insurance/devices/trust |
| **Authentication identity — must NOT be repointed** | `:88-90`; concurrency report `:213` | `niam_identities.id` refs (`account.py:29`, `workspace.py:60`, `membership.py:91,141`, …) |
| **Other merge-capable stores / own chains** | `:91-96` | `health_data/mdm/models.py:13,49`, `governance/models/health_number.py:63-76`, `health_data/mdm/service.py:77-120` — none wired to `merge_citizens` |
| **Unknown ownership** | concurrency report `:216-218`: "Ownership could not be proven for any reference above; each is therefore `NEEDS_OWNER_DECISION`… No assumption was made that 'has patient_id ⇒ must be repointed'." | All 13 domain rows except MPI's own and the informational auth-identity row |

The five labels requested in the mission (foreign key / soft reference / audit reference / external
identifier / unknown ownership) are represented by the first, fourth, second, third and last rows
above respectively; the two additional classes (LIMS-patient integer FKs, auth identity) are documented
because the source reports include them. A numeric breakdown per label is **not available**.

---

## 2. Components that call or depend on MPI (proven call sites)

| Component | Evidence | Nature / impact of the proposed design |
|---|---|---|
| **HTTP MPI API** | `services/mpi/api.py:22,73,159,278` | Calls `resolve_identity` / `merge_citizens`. MPI-05/06/07/10 change internal behaviour; no endpoint/schema change. |
| **App registration** | `factory.py:616-617` (`include_router(mpi_router)`) | Router mount unchanged. |
| **Patient identity service** | `services/patient_service.py:16,407-441` (`_resolve_mpi`), audit on failure `:442-450` | Resolve path shares `create_patient`'s outer commit (`patient_service.py:198`); MPI-01's advisory lock must be acquired at that level (MPI-06). |
| **Canonical patient service / routes** | `services/mpi/canonical_service.py:13-15,18-133`; `routes/canonical_patient.py:14-19,184,207,222` | **Separate, weaker merge path** — no locks/SAVEPOINT/audit; version increments at `canonical_service.py:128,130`. In scope only for MPI-03 and gated by **D-MPI-6**. |
| **Citizen self-registration** | `routes/register.py:17-21,48-101,338,372,620` | Creates/queries `Citizen` directly; reuses MPI hashing/blocking. No design change proposed. |
| **Health-data MDM** | `health_data/mdm/service.py:10,140` | Reuses MPI `build_profile`; independent merge store. Not repointed. |
| **Identity matching (competing scorer)** | `services/identity_matching.py` (tests `test_identity_matching.py:20-27`) | Separate scorer; architecture study calls it fragmented (`MASTER_PATIENT_INDEX_DESIGN.md:52,88`). No change proposed. |
| **Laboratory records** | `models/test_result.py:52` (RESTRICT FK), LIMS FKs in report §3c | Not repointed by MPI merge. No change. |
| **Identity claims** | `services/mpi/models.py:115-147` | Only repointed bridge; `uq_identity_claims_lab_patient` (`:124`) reused by MPI-05 — **no schema change**. |
| **Audit services** | `canonical_audit.py:90-260`; `identity/services/audit_service.py:15-201`; `services/audit_service.py:90-270`; `mpi/resolver.py:118-208` | **Three independent NIAM/global chains + the MPI chain**, none sharing a payload format. See §3 — the proposed advisory lock serializes only the MPI chain; other chains are untouched. |
| **Session / authorization** | `identity/api/audit.py:11-16,54-75`; `identity/api/router.py:32,49` | Consent/RBAC gates audit reads. `niam_identities.id` is auth identity and **must not** be repointed. |
| **Patient / clinical / EHR / national / care-continuum / pharmacy / consent** | report §3b–3c (`:57-96`); `identity/models/citizen_relationship.py:55`, `national/domain/patient.py:11` | String(26) or Integer references in separate stores; none repointed. No change. |

### Impact verdict by domain (derived from the analysis, not a repointing proposal)

| Domain | Affected by recommended design? | Detail |
|---|---|---|
| Identity matching | No | Pure matching functions unchanged; no repointing. |
| Canonical identity services | **Yes — bounded** | `merge_canonicals` version increments only (MPI-03, D-MPI-6); separate path otherwise unchanged. |
| Patient identity | **Yes — transaction ownership** | Resolve merges share `create_patient` commit; MPI-06 addresses the post-commit response window. |
| Identity claims | **Yes — replay handling** | MPI-05 uses existing unique constraint; no schema change; only repointed bridge. |
| Audit services | **Yes — MPI chain only** | Advisory lock + in-transaction segment check; other three chains untouched. |
| Session / authorization | No | Read-only audit gating; auth identity never repointed. |
| Patient / laboratory / clinical / EHR / national / care-continuum / pharmacy / consent | **No** | No FK/soft-reference repoint; no unmerge; no canonicalization. |

---

## 3. Audit-consistency cross-check (relevant to MPI-08)

Lock status of each hash-chained tail (`VERIFIED_IN_SOURCE`):

| Ledger | Tail read | Genesis protection | Verifier | In scope for this design? |
|---|---|---|---|---|
| MPI `mpi_merge_audit` | **unlocked** (`resolver.py:110-115`) | none | `verify_merge_audit_chain()` `:175-208` — detection only, **no production caller** | **Yes** (MPI-01/02/08) |
| NIAM canonical (v2) | **locked** `.with_for_update()` (`canonical_audit.py:139`) | empty table defeats row lock (`INFERRED` from SQL semantics) | `CanonicalAuditService.verify()` `:223-260`, `/niam/audit/integrity` | No — precedent only |
| NIAM legacy `AuditService` | **unlocked** (`audit_service.py:20-28`) | none | `verify_chain_integrity` `:162-201` (different payload; chains not mutually verifiable — `INFERRED`) | No |
| Global LIMS `audit_logs` | **unlocked** (`services/audit_service.py:106-112`) | none | `:238-270`, `GET /audit-integrity` + HMAC anchor | No |

Archive/export: the only audit export endpoint found is `GET /niam/audit/export`
(`identity/api/audit.py:110-146`), which also appends a `DATA_EXPORT_REQUESTED` event. **There is no
MPI hash-chain verification or archive endpoint** in `services/mpi/api.py`. MPI-08's full-chain
exposure path is gated by D-MPI-3/4; this design does not add the endpoint itself.

---

## 4. Existing MPI test inventory and gaps (feeds MPI-09)

Exact counts via `grep -cE '^\s*(async )?def test_'` (`VERIFIED_IN_SOURCE`):

| Path | Count | Asserts |
|---|---:|---|
| `backend/tests/test_mpi_matcher.py` | 35 | Pure matcher/normalization/blocking tests + a *reimplementation* of chain hash (genesis zeros, determinism, tamper propagation) |
| `backend/tests/test_identity_matching.py` | 31 | **Not MPI** — competing `identity_matching` scorer, HID checksum, duplicate search |
| `backend/tests/test_mpi_merge_integrity.py` | 6 | Claim repoint + audit, idempotent replay, self/cycle/blank-reason rejection, rollback on injected audit failure |
| `backend/tests/test_mpi_hash_chain_integrity.py` | 11 | SQLite: row reproduces hash, clean/forked chains, tamper detection, retry-audits-once, rejection cases, both argument lock orders, one key-ordered `FOR UPDATE` source invariant |
| `backend/tests/test_security_merge_regression_synthetic.py` | 8 | **Not MPI merge** — canonical-patient route role/cross-tenant guards |
| `backend/tests/identity/test_security_audit_phase9.py` | 10 (3 canonical) | Canonical chain linked/verifiable, tamper detection, secret redaction; rest consent/incident/SSRF + read-only audit surface |
| `backend/tests/identity/test_security_audit_migration_phase9.py` | 1 | Phase-9 schema/catalog presence |
| Adjacent legacy: `test_niam.py` 44, `test_niam_v2.py` 45 | — | Legacy audit record/hash-chain tests with mocked sessions |

**Gaps (absent tests, not proposed code changes):**
- **Concurrency:** no two-session/two-thread merge or append test; SQLite emits no `FOR UPDATE`
  (test docstring `:9-11`); lock-order test `:270-279` is a source-string check, not runtime contention.
- **Genesis:** only static 64-zero assertions and a sequential first row plus a *forged* fork
  (`:156-197`); no two concurrent first appends.
- **Lock timeout / deadlock:** no `55P03`/`40P01` test in `backend/tests`; only governance evidence.
- **Retry:** `:200-219` monkeypatches `_write_audit` failure, not a `40001` DB retry; no bounded policy.
- **Idempotency:** merge replay covered; resolve idempotency has constraint (`models.py:124`) but **no
  dedicated regression test** (`MPI_INTEGRITY_CONCURRENCY_REMEDIATION_REPORT.md:190`, F9 PARTIAL).
- **Canonical audit:** mocked `_AuditSession` discards SQL, so `.with_for_update()` is **not asserted**.
- These gaps are the direct input to MPI-09; the PostgreSQL harness (outside production) is required.

---

## 5. Ownership and historical-integrity questions (unresolved — document only)

From `MPI_CROSS_DOMAIN_INTEGRITY_REPORT.md:149-170` and concurrency report `:216-218`:

1. **Schema/single-writer ownership** of `citizens`, `patients`, `canonical_patients`,
   `national_citizens`, `national_patients` — `NEEDS_OWNER_DECISION` (MPI-01/NI-03/W-038);
   `DATABASE_OWNERSHIP_MATRIX.md:43` says canonical patient identity is **not enforced**.
2. **No reference-change log** exists for MPI: a per-row `(table, row_pk, column, old, new, event)`
   record across the ~90 sites is absent (`:159-160`).
3. **No unmerge/split implementation**: no compensating repoint, `event_type='split'` writer or
   consent re-evaluation exists (`:161-162`; `resolver.py` writes only `create`/`manual_merge`,
   `models.py:167`). Not proposed here.
4. **Correctness prerequisites before any reversal**: verifiable hash chain, locked allocation, lock
   ordering, claim locking, review-reject audit gap (`:163`, §4 items 1–3, 5, 7). Note §4 of that report
   lists older findings since addressed in current source (`_occurred_at_iso` `:93-107`, verifier
   `:175-208`, one key-ordered `FOR UPDATE` `:459-465`); its line pointers are **stale**. The unlocked
   MPI audit tail (`:110-115`) and lack of serialization selection remain confirmed.
5. **Complete repointing coverage + migration readiness**, RPO/RTO unmeasured (`:164-166`).
6. **Required gates**: `NEEDS_OWNER_DECISION`, `SECURITY_REVIEW_REQUIRED` (clinical-safety sign-off),
   `LEGAL_REVIEW_REQUIRED` (historical retention); unmerge is `BLOCKED` and **no destructive deletion
   was performed** (`:168-170`, `:18-20`).

---

## 6. Impact summary

- The recommended architecture changes **internal concurrency behaviour of the MPI merge/resolve
  path and the canonical version counters only**. It creates **no new cross-domain reference**,
  repoints **none**, and adds **no schema object**.
- Every affected component keeps its endpoint, contract, FK direction and store ownership.
- The ~90 reference sites remain an **inventory/documentation item under D-MPI-3**, with unresolved
  ownership; this analysis deliberately makes no claim that any of them must change.
- No MPI unmerge, NHID canonicalization, cross-tenant change or patient-data use is introduced.

**STOP — PROPOSED — NOT APPROVED. Await explicit owner approval of D-MPI-1 and D-MPI-3 before any
implementation touching cross-domain references.**


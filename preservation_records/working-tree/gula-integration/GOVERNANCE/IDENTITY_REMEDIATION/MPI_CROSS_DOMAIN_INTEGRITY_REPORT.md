# MPI Merge Integrity & Cross-Domain Reference Report

> **Tranche:** bounded, uncommitted session/MPI/NHID readiness work. **Release
> decision remains HOLD** (`GOVERNANCE/FINAL_DECISION.md`, md5 `effdfeaf…`).
> D-020/D-021 remain `PENDING_APPROVAL`. No runtime/E2E/clinical/production
> claim. Paths are inside `gula-integration` @ `integration/gula-unification-v1`,
> HEAD `2827c1ff…`. `APP` below = `backend/app`.

## 1. Classification and status

| Item | Classification | Status |
|---|---|---|
| Revalidate P0-E1 merge integrity controls in source | `OWNER_APPROVED` | `VERIFIED_IN_SOURCE` |
| Bounded non-destructive merge corrections | `OWNER_APPROVED` | `VERIFIED_IN_SOURCE` (no new correction required — see §4) |
| Cross-domain reference inventory | `OWNER_APPROVED` | `VERIFIED_IN_SOURCE` |
| Unmerge / cross-domain reference migration | `BLOCKED_BY_EXTERNAL_DEPENDENCY` / `NEEDS_OWNER_DECISION` / `SECURITY_REVIEW_REQUIRED` | `BLOCKED` (not implemented) |

**No unmerge or cross-domain reference migration was performed.** Historical
event/reference-change data and schema ownership decisions are missing; no
destructive deletion of historical identity records occurred.

## 2. MPI models (source-verified) — `APP/services/mpi/models.py`

| Entity (table) | FK-bearing field | Target / ondelete | Line |
|---|---|---|---|
| `Citizen` (`citizens`) | `merged_into_id` BigInteger | `citizens.id` **RESTRICT**, nullable; self-FK, bounded 10-hop `canonical()` | 82-84, 96, 99-112 |
| `Citizen` | — | `claims` dynamic relationship to `IdentityClaim` | 97 |
| `IdentityClaim` (`identity_claims`) | `citizen_id` BigInteger | `citizens.id` RESTRICT, NOT NULL | 131 |
| `IdentityClaim` | `lab_id` Integer | `labs.id` CASCADE | 132 |
| `IdentityClaim` | `local_patient_id` Integer | `patients.id` CASCADE; unique `(lab_id, local_patient_id)` idempotency key | 133-135 |
| `IdentityClaim` | `claimed_by_user_id` Integer | `lab_users.id` SET NULL | 142-144 |
| `IdentityClaim` | provenance JSON: `match_method`, `match_score`, `match_features` | merge provenance | 137-140 |
| `MergeAudit` (`mpi_merge_audit`) | `primary_citizen_id`, `secondary_citizen_id` | `citizens.id` RESTRICT | 169-174 |
| `MergeAudit` | `decided_by_user_id` Integer | `lab_users.id` SET NULL | 180-182 |
| `MergeAudit` | `prev_hash` / unique `entry_hash` String(64) | SHA-256 chain over `prev_hash || canonical_json(row)` | 150-156, 185-187 |

`Citizen` has **no other FK**; its canonical identity is the external String(26)
`citizen_ulid`. Only `create` and `manual_merge` `event_type` values are ever
written (`resolver.py:314,440`); `split`/`reassign` are declared but unused.

## 3. Cross-domain reference inventory (source-verified)

Three distinct, unreconciled identity stores exist: MPI `citizens` (BigInteger,
`citizen_ulid`), national `national_citizens`/`national_patients` (String(26)
ULID), health-data MDM (`hd_mdm_patient_index`), plus `CanonicalPatient`.
`GOVERNANCE/DATABASE_OWNERSHIP_MATRIX.md:43` records that canonical patient
identity is **not enforced** across LIMS/MPI/EHR/national.

### 3a. Direct FKs into MPI `citizens` (BigInteger)
| File | Entity / field | Repointed on MPI merge? |
|---|---|---|
| `APP/services/mpi/models.py` | `IdentityClaim.citizen_id` | **Yes** — atomic in SAVEPOINT with provenance (`resolver.py:425-448`) |
| `APP/services/mpi/models.py` | `MergeAudit.primary/secondary_citizen_id` | n/a (ledger) |
| `APP/models/test_result.py` | `TestResult.citizen_id` (RESTRICT, :52-57) | **No** |
| `APP/models/canonical_patient.py` | `CitizenLink.citizen_id` (RESTRICT, :93-95) | **No** |

### 3b. National / EHR / care-continuum references (String(26) ULID — separate store)
- National core: `national/domain/citizen.py:50,91-93` (`merged_into_id`, `merge_into()`),
  `national/domain/patient.py:11,43-45` (`citizen_id`, `guardian_id`, `merged_into_patient_id`
  **without FK**).
- `national/domain/` — 9 classes with paired `patient_id`+`citizen_id` FKs
  (`encounter`, `visit`, `episode_of_care`, `observation`, `referral`,
  `appointment`, `consent`, `coverage`, `advance_directive`), plus
  `admission`, `discharge`, `guardian`, `family`, `newborn`, `death_record`,
  `biometrics`, `health_card`, `identity_resolution`, `merge_record`,
  `emergency_contact`, `national_id` — all RESTRICT, **none repointed by MPI merge**.
- `APP/ehr/models/*.py` (11 files) — `patient_id`/`citizen_id` on allergy,
  attachment, care plan, clinical note, problem list, condition, diagnosis,
  family history, immunization, medication statement/request/administration,
  risk factor, social history, patient timeline — FK → national_patients CASCADE /
  national_citizens RESTRICT; **none repointed**.
- `APP/pharmacy/models.py` — `Prescription`, `DispenseRecord`, `DrugReturn`
  `patient_id` FKs (:154,255,540); `PharmacySale`, `DrugSubstitutionRequest`
  plain columns (:794-798,927-928); **none repointed**.
- `APP/care_continuum/models/*` — ~40 classes with paired `patient_id`/`citizen_id`
  FKs; **none repointed**.
- `APP/identity/models/citizen_relationship.py:55-59` — `citizen_id`/`patient_id` FKs.
- Soft references (no FK): `models/consent.py:42` `Consent.gpid` (citizen_ulid),
  `pharmacy` plain patient/citizen ids, `national_id.py:9`, `patient_ulid`
  projections — **none repointed** (consent scopes could silently mis-resolve).

### 3c. LIMS `patients` (Integer) and NIAM identities
- LIMS `patients.id` FKs: `lab_order.py:27`, `claim.py:34`, `canonical_patient.py:70-75`,
  `authorization.py:199`, `nursing/models.py` (11 sites), `billing/models.py:37,88,113`,
  `insurance/domain/*` (~10 sites), `devices/models.py:247`, `trust/models.py:24,74`.
  `canonical_service.merge_canonicals` repoints only `PatientLink.canonical_id`
  (:116-121); all other LIMS FKs untouched by MPI merge.
- NIAM `identity_id` → `niam_identities.id` (`account.py:29`, `workspace.py:60`,
  `membership.py:91,141`, `verification_record.py:48`, …) is an **authentication**
  identity with no link to MPI `Citizen` and **must not be repointed**.
- Separate merge-capable stores: `health_data/mdm/models.py:13,49` (MDM index +
  `merged_into_id`), `governance/models/health_number.py:63-76`
  (`gov_merged_identities.historical_data_json` + a `/health-numbers/split`
  endpoint in `governance/routes/governance_routes.py:226-233`),
  `health_data/mdm/service.py:77-120` (`merge_history` + in-memory `split()`).
  **None is wired to MPI `merge_citizens`.**

**Canonical vs alias:** every reference above is treated as canonical within its
own store; MPI repointing covers exactly one alias bridge (`IdentityClaim`).

## 4. P0-E1 merge-integrity revalidation (source + prior tests)

Controls present in `APP/services/mpi/resolver.py`:
- self-merge guard (:377-380); cycle/duplicate guard via canonical ids + status
  (:411-420); idempotent retry returns the original `MergeAudit` (:393-409);
- claim repointing **is implemented** (:422-432) with provenance in claim JSON +
  audit `repointed_claim_ids` (:429-430, :444) — the older study note claiming
  "claims not repointed" is stale versus current source;
- hash-chained audit writer (:93-140); post-merge consistency assertions
  (:450-455); nested SAVEPOINT with rollback on any exception (:425-459);
  `with_for_update()` on both citizens (:384-389).
Prior tranche regression suite `backend/tests/test_mpi_merge_integrity.py`
(6 tests) passed; this tranche re-ran it as part of combined verification.

**Source-verified weaknesses/correctness concerns (no code change made — each is
a documented finding, not silently "fixed"):**
1. **Hash chain not verifiable as written.** `_write_audit` hashes `occurred_at`
   computed at `resolver.py:122`, but the persisted `MergeAudit.occurred_at` uses
   the model default lambda (`models.py:183`), a different timestamp; no verification
   function exists. (Evidence-grade concern; requires bounded fix decision.)
2. **Concurrent merge race on audit chain.** `_last_audit_hash` reads
   `ORDER BY id DESC LIMIT 1` with no lock (:93-98); two merges can fork the ledger.
3. **Lock-order deadlock.** `primary` locked before `secondary` (:384-389);
   concurrent A→B and B→A can deadlock; no retry/detection at `api.py:158-168`.
4. **Incomplete repointing.** Only `IdentityClaim` is repointed; `TestResult`,
   `CitizenLink` and all national/EHR/care-continuum references remain on the
   absorbed identity.
5. **Claims not locked** (:422) — a concurrent insert can cause a spurious
   post-merge verification rollback.
6. **Unmerge explicitly absent** (`resolver.py:374-375`; `api.py` exposes no
   split endpoint; `split`/`reassign` never written).
7. **Review-reject path** deletes a claim (`api.py:275`) despite "Rows are never
   deleted" (`models.py:15`) and claims an audit row that is not written
   (`api.py:243-302`); `ResolveDecision.reason` is unused.
8. **Idempotency edge case** (:396-409) if the primary is later merged elsewhere.
9. **NID fast path** auto-matches on HMAC equality alone (`resolver.py:226-236`);
   current NID hashing is consistent (`identity.hash_national_id` used by both
   `identity.py` and `routes/register.py:344,622`), so the older study note about
   divergence is stale versus current source.
10. **`canonical()` masks corruption** — returns `self` on a broken chain
    (`models.py:110-111`); 10-hop bound can leave deep chains unresolved.
11. **`canonical_service.merge_canonicals`** is weaker (no locks/SAVEPOINT/audit,
    mutates names and nulls identifiers; `routes/canonical_patient.py:180-184`).

These are pre-existing source properties, not regressions introduced by this
tranche. Fixing the verifiable hash chain / locked allocation / lock ordering is
a candidate for a **separately authorized** bounded-correction tranche.

## 5. Unmerge readiness — BLOCKED

**Bounded, non-destructive unmerge is NOT implementable from current source.**
A narrow, claim-only reversal could be hand-built from
`MergeAudit.match_features.repointed_claim_ids` + per-claim
`merged_from_citizen_ulid`/`merge_reason`, but that is not general or verifiable
(no table name, no old/new FK values, no replay code). Missing prerequisites:
1. Schema/single-writer ownership decision for `citizens`, `patients`,
   `canonical_patients`, `national_citizens`, `national_patients`
   (`DATABASE_OWNERSHIP_MATRIX.md:43`; MPI-01/NI-03/W-038) — `NEEDS_OWNER_DECISION`.
2. A reference-change log with per-row `(table, row_pk, column, old, new, event)`
   across the ~90 FK/soft-reference sites in §3 — none exists for MPI.
3. An unmerge/split implementation with compensating repoint, `event_type='split'`
   writer and consent re-evaluation — none exists in MPI.
4. Correctness fixes before reversal is trustworthy (§4 items 1-3, 5, 7).
5. Complete repointing coverage (§3) and migration readiness
   (EHR/CC/insurance/national at 0-8% migrated, F-085 unregistered bases,
   RPO/RTO unmeasured — `DATABASE_OWNERSHIP_MATRIX.md:31-41,72-75,104-106`).

Required decisions: `NEEDS_OWNER_DECISION` (schema ownership, unmerge policy),
`SECURITY_REVIEW_REQUIRED` (clinical-safety sign-off), `LEGAL_REVIEW_REQUIRED`
(historical-record retention). No destructive deletion was performed.

## 6. Verification boundary
Inventory and control revalidation are `VERIFIED_IN_SOURCE`. Prior 6-test MPI
suite re-executed in this tranche's combined verification (see
`ACCEPTANCE_EVIDENCE.md`). No production/operational database access, no DDL,
no patient data, and no unmerge code was written. Not E2E or runtime verified.

---

**Post-analysis pointer (read-only, 2026-11-18):** the ~90 reference sites and ownership questions
above were analyzed in `MPI_CROSS_COMPONENT_IMPACT.md` (`PROPOSED — NOT APPROVED`) with a per-class
classification and component impact matrix. **No cross-domain FK or soft reference is repointed and
no MPI unmerge is proposed**; all sites remain `NEEDS_OWNER_DECISION` (D-MPI-3). The current-source
line pointers in §4 are partially stale (the verifier, `_occurred_at_iso` and one key-ordered
`FOR UPDATE` now exist in `resolver.py`); the unlocked MPI audit tail remains confirmed. Related
artifacts: `MPI_SERIALIZATION_ARCHITECTURE_DECISION.md`, `MPI_IMPLEMENTATION_EXECUTION_PLAN.md`,
`MPI_FAILURE_RECOVERY_MATRIX.md`. HOLD, D-020/D-021 and D-MPI-1 unchanged.

# GULA National Identity Architecture Study — Master Patient Index Design

**Program:** National Identity, Citizen Registration, Authentication & Document Intelligence — Master Architecture Study (READ-ONLY)
**Repository:** `/home/samertts/workspace/projects/gula-integration` · **Branch:** `integration/gula-unification-v1` @ `2827c1ff…`
**Document status:** ARCHITECTURE STUDY / RECOMMENDATION — **not an implementation authorization**
**Release posture:** `FINAL_DECISION.md` remains **HOLD**; D-020 and D-021 remain `PENDING_APPROVAL`.

---

## 0. Evidence convention

See `MASTER_ARCHITECTURE.md` §0. Labels: `VERIFIED_IN_SOURCE`, `TEST_VERIFIED` (test **source exists** — **not executed here**), `PARTIAL`, `SOURCE_PRESENT`, `DORMANT`, `NOT_IMPLEMENTED`, `BLOCKED`, `UNVERIFIABLE`. Source presence is never runtime verification; no tests run, no DB contacted, no application file modified. No match threshold or accuracy figure is asserted; thresholds must be calibrated on authorized de-identified/synthetic data.

---

## 1. Governing decisions

- **D-IDENTITY-07** — Hybrid duplicate resolution: deterministic auto-merge only under explicit safeguards, human review otherwise, auditable merge/unmerge.
- **D-IDENTITY-02** — NHID stable and never reused (MPI links must survive merges/corrections).
- **D-IDENTITY-04** — Twins have independent NHIDs; relationships are attributes, not shared identifiers.
- **D-IDENTITY-11** — Authentication ≠ patient-record access.

Product-design decisions only; no implementation authorized.

---

## 2. Current MPI source inventory (verified directly)

`backend/app/services/mpi/` is the strongest national MPI candidate.

### 2.1 Data model — `VERIFIED_IN_SOURCE`

| Item | Evidence |
|---|---|
| `Citizen` → `citizens`, `IdentityClaim` → `identity_claims`, `MergeAudit` → `mpi_merge_audit` | `mpi/models.py:42-48,115-122,150-158` |
| `Citizen.canonical()` follows `merged_into_id` up to 10 hops | `mpi/models.py:99-112` |
| Resolver idempotency key `(lab_id, local_patient_id)` | `mpi/resolver.py:183-200` |
| Hash-chained audit | `mpi/resolver.py:93-140` |

### 2.2 API surface — `VERIFIED_IN_SOURCE` (routing wired in source)

`mpi/api.py`: prefix `/mpi` (`:35`); `POST /mpi/resolve` (`:41`), `GET /citizens/{ulid}` (`:101`), `POST /merge` (`:142`), `/review` (`:182`), `/review/{claim}/decide` (`:226`), `GET /citizens/{ulid}/access` (`:313`); registered at `factory.py:617`.

**Controls present in source:** `get_current_user` (`:45`), rate limiting (`:53,55`), lab ABAC (`:104-110`), admin-only merge/projection (`:145-150`), consent-gated cross-lab read (`:313-318`). Static tests: `test_mpi_matcher.py` (35), `test_security_merge_regression_synthetic.py` (8) — not executed.

### 2.3 Matching — `PARTIAL`

| Component | Evidence |
|---|---|
| Fellegi-Sunter weights, NID short-circuit, Jaro-Winkler, thresholds | `mpi/matcher.py:32-46,108-114,147-154,178-187` |
| Blocking | `mpi/blocking.py:29-76` |
| Competing scorers (fragmentation) | `services/identity_matching.py:151-157,231-321` (queries `Patient`, not MPI `Citizen` at `:270-292`); `health_data/mdm/matching.py:31-325` (name-only safety `:56-72`); `data_platform_service.py:75-99` (persists supplied probability, no computation) |

### 2.4 Merge defect — verified

`mpi/resolver.py:354-400`: manual merge sets `secondary.merged_into_id = primary.id` and `status="merged"`, appends a `MergeAudit`, but **explicitly does not repoint `secondary.claims`** — comment at `:367-369` defers it to a follow-up migration. No unmerge/split endpoint found. `canonical()` follows chains but claims remain attached to the merged-away record → broken linkage (D-IDENTITY-07 violation).

---

## 3. Target MPI design (recommendations)

### 3.1 Authority & boundaries

- MPI becomes the **national patient-identity authority** only after owner decision (currently lab-centric and one of several stores) → `NEEDS_OWNER_DECISION`.
- MPI owns: person identity linkage, NHID mapping, identity claims, duplicate resolution, merge/unmerge history. It does **not** own authentication (D-IDENTITY-11) or civil-registry truth.

### 3.2 Deterministic fast path + probabilistic + human review (D-IDENTITY-07)

```
capture → normalize NID once (digit-normalized HMAC, NATIONAL_IDENTITY_MODEL §4.1)
   → deterministic NID match (HMAC equality) ──► exact match → auto-link (safeguards)
   → else blocking (DOB, name keys) → Fellegi-Sunter/Jaro-Winkler score
        ├─ above HIGH threshold + independent agreement → auto-merge under safeguards
        ├─ GREY zone → HUMAN REVIEW queue
        └─ below LOW → create new citizen / provisional link
```
- Auto-merge safeguards (target): high-confidence deterministic key OR multi-field score above calibrated threshold; no conflicting protected attributes; two-person approval for cross-facility merges; full audit; reversible.
- Thresholds must be **calibrated** on authorized de-identified/synthetic Iraqi data — none asserted here → `BLOCKED_BY_EXTERNAL_DEPENDENCY` for calibration data.

### 3.3 Merge/unmerge correctness (fix verified defect)

- On merge, **atomically repoint all `IdentityClaim` rows** from secondary to primary (within a transaction), update `merged_into_id`/status, write hash-chained audit with reason + approver + before/after.
- Provide auditable **unmerge/split**: reverse claims to the secondary identity, notify downstream consumers, preserve full history. Never hard-delete.
- Twins (D-IDENTITY-04): separate citizens/NHIDs always; relationship recorded as an attribute; matcher must not merge on shared guardian/family attributes alone.

### 3.4 Consolidation of matchers

- One configurable matching engine reused across LIMS/MDM/data-platform; retire the 3 divergent scorers behind a single interface. Safety rule preserved: name-only never auto-matches (`health_data/mdm/matching.py:56-72`). → `NEEDS_OWNER_DECISION`.

### 3.5 Consent & access

- Preserve consent-gated cross-lab read (`api.py:313-318`) and lab ABAC (`:104-110`); patient-record access never follows from MPI resolution alone (D-IDENTITY-11).

---

## 4. Test requirements (design-level; no tests run here)

| Level | Coverage |
|---|---|
| Unit | `canonical()` chain limit; NID fast-path equality; matcher weights/threshold boundaries; blocking recall on synthetic names. |
| Integration (synthetic) | Registration→resolve→auto-merge; **claim repointing regression** (defect at `resolver.py:367-369`); unmerge/split; twin non-merge; cross-lab consent gate. |
| Security | Admin-only merge; hash-chain integrity; unauthorized merge denial; no auth-to-access escalation. |
| Data (calibration) | Measure precision/recall on authorized de-identified/synthetic data; set thresholds from evidence; record engine version. |

Synthetic / legally authorized de-identified data only.

---

## 5. Architecture decisions register

| ID | Decision | Problem | Alternatives | Advantages | Disadvantages | Legal | Security | Ops/cost | Dependencies | Failure | Reversibility | Evidence | Classification |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MPI-01 | MPI as national patient-identity authority after consolidation | Competing stores | Keep lab-centric MPI | Single truth | Consolidation effort | Ownership law | Positive | High | Owner decision | Conflicting records | Reversible via migration | §2 | `NEEDS_OWNER_DECISION` |
| MPI-02 | Hybrid auto-merge + human review + auditable unmerge | D-IDENTITY-07 | Auto-merge only / manual only | Safe + scalable | Review capacity | Merge authority | Positive | Moderate | Calibration data | Wrong merges | Reversible | §2.4, §3.2/3.3 | `OWNER_APPROVED` (D-IDENTITY-07) |
| MPI-03 | Fix claim repointing on merge | Orphaned claims | Leave deferred | Correct linkage | Transaction work | None | Positive | Low | Executed test | Broken linkage | Reversible | §2.4 | `SECURITY_REVIEW_REQUIRED` |
| MPI-04 | One configurable matcher; retire 3 scorers | Divergent thresholds | Keep all | Consistency | Migration | None | Positive | Moderate | Owner decision | Inconsistent matches | Reversible | §2.3, §3.4 | `NEEDS_OWNER_DECISION` |
| MPI-05 | Calibrate thresholds on authorized data | No evidence-based thresholds | Vendor defaults | Defensible | Data access | Data-sharing law | Neutral | Moderate | De-identified data | Unsafe merges | Reversible | §0, §3.2 | `BLOCKED_BY_EXTERNAL_DEPENDENCY` |
| MPI-06 | Twins never share NHID; relationships as attributes | D-IDENTITY-04 | Shared family ID | Correctness | Matcher rule | None | Positive | Low | Owner decision (accepted) | Wrongful merge | Reversible | §3.3 | `OWNER_APPROVED` (D-IDENTITY-04) |

---

## 6. Open questions

1. Which store is authoritative for patient identity (MPI vs national vs canonical patients)?
2. Which merge cases are safe for deterministic auto-merge, and who approves? (`LEGAL_REVIEW_REQUIRED` / `NEEDS_OWNER_DECISION`.)
3. Can authorized de-identified data be obtained for threshold calibration? (`BLOCKED_BY_EXTERNAL_DEPENDENCY`.)
4. Who is notified on unmerge/split, and what is the SLA?

---

## 7. Cross-references

`MASTER_ARCHITECTURE.md` · `NATIONAL_IDENTITY_MODEL.md` · `IDENTITY_LIFECYCLE.md` · `CITIZEN_REGISTRATION_DESIGN.md` · `API_AND_INTEGRATION_CONTRACTS.md` · `TESTING_AND_ACCEPTANCE_STRATEGY.md` · `IMPLEMENTATION_ROADMAP.md` (Phases 3, 5, 6).

# MPI Final Independent Audit

**Audit ID:** MPI-FIA-001
**Date:** 2026-11-18
**Repository:** `gula-integration` · branch `integration/gula-unification-v1` · HEAD `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0`
**Basis:** fresh independent re-inspection of actual source and evidence regenerated in this session; detailed evidence in `MPI_FINAL_VERIFICATION_REPORT.md`.
**Decision reference:** `GOVERNANCE/FINAL_DECISION.md` (md5 `effdfeaf10234678d83b2668c4489552`, `HOLD`) — read-only.
**Primary findings reference:** `MPI_INDEPENDENT_AUDIT_FINDINGS.md` (verdict `REJECT`) — unmodified.

---

## 1. Independence statement

This is a **new** audit, not a copy of a prior one. Conclusions derive from direct reads of the shipped source (`resolver.py`, `api.py`, `canonical_service.py`, `reliability.py`, `models.py`, `schemas.py`, `routes/canonical_patient.py`, `routes/compliance.py`) and from evidence **re-generated in this session**: a fresh MPI regression run (**127 passed, 0 failed**), the completed full-suite log (**3843 passed, 1 pre-existing order-dependent baseline failure, 27 skipped**), and direct re-opening of the real-PostgreSQL HTTP proof artifacts (28/28 checks × 2 profiles, real Alembic schema). No prior report was treated as final proof.

No `gula-platform` file was touched; `FINAL_DECISION.md` unchanged; no commit/push/merge/rebase/PR/deploy; no `git reset`/`clean`/`add .`/`add -A`; no migration/DDL/schema change; no NHID canonicalization change; no unmerge; no scope expansion; synthetic data only.

---

## 2. Finding counts by severity

Baseline severities are those of the authoritative `MPI_INDEPENDENT_AUDIT_FINDINGS.md`; "open" means an owner decision or owner-authorized migration is still required before the finding can be closed.

| Severity | Count (baseline) | Closed / PASS | Open | Open IDs |
|---|---:|---:|---:|---|
| **CRITICAL** | **0** | 0 | 0 | — |
| **HIGH** | **3** | 2 | **1** | AUD-02 (PARTIAL — DB `UNIQUE` not applied; MP-001) |
| **MEDIUM** | **9** | 8 | **1** | AUD-07 (BLOCKED — D-MPI-5 / ODR-002) |
| **LOW** | **2** | 2 | 0 | — |
| **INFORMATIONAL** | **2** | 1 (measured/documented) | **1** | AUD-16 (BLOCKED — D-MPI-3/4 / ODR-003) |
| **Total** | **16** | **13 PASS + 1 documented PASS** | **3** | AUD-02, AUD-07, AUD-16 |

No finding is `FAIL`. No assertion was deleted and no coverage was reduced. **One HIGH-severity finding (AUD-02) remains open** at the schema/data-ownership layer.

---

## 3. Per-finding independent verdicts

| ID | Severity | Independent verdict | Basis (short) |
|---|---|---|---|
| AUD-01 | HIGH | **PASS** | `create_detached_citizen()` never scores/reuses; NID not transferred; replay guard under advisory lock; chained decision audit. |
| AUD-02 | HIGH | **PARTIAL** | App-layer authz (`require_link_actor` + `require_own_lab`) and conflict-safe advisory-locked links verified; DB `UNIQUE` not applied (MP-001 owner-gated). |
| AUD-03 | HIGH | **PASS** | Request `db` closed before `bounded_retry`; fresh session per attempt; no second pinned connection. Proof: 6/6 200 on 2-conn pool, 0 pool-timeout 503s. |
| AUD-04 | MEDIUM | **PASS** | NID re-read under the advisory lock in the create branch; idempotent NID registration. Proof: 10/10 200, one ULID, one row. |
| AUD-05 | MEDIUM | **PASS** | Merge/review/resolve reconcile on fresh sessions; failed sessions closed before replay. |
| AUD-06 | MEDIUM | **PASS** | Unordered-pair idempotency inside the locked region; swapped replay returns original (proof `[200,200]`, one audit row). |
| AUD-07 | MEDIUM | **BLOCKED** | No payload-fingerprint / re-resolve behavior change; requires owner decision D-MPI-5 (ODR-002). Left open by design, not hidden. |
| AUD-08 | MEDIUM | **PASS** | Full verifier wired into `GET /compliance/audit-integrity` (additive, admin-only, fail-closed detection). |
| AUD-09 | MEDIUM | **PASS** | Real Alembic schema + real `SessionLocal` + HTTP `TestClient` proof; legacy hand-DDL harness relabeled strategy-only. |
| AUD-10 | MEDIUM | **PASS** | Worker scaling E[2/5/10/20] asserts `errors==[]`; all 200; exact audit deltas. |
| AUD-11 | MEDIUM | **PASS** | Review decisions write chained audit rows with reviewer/reason/rejected candidate; replay refused. |
| AUD-12 | MEDIUM | **PASS** | Canonical merge/link writes chained `audit_logs` row in same transaction; commit failure → 503 with rollback. |
| AUD-13 | LOW | **PASS** | `BrokenCanonicalChainError` + `canonical(strict=True)` on decision paths; warned fallback on read paths. |
| AUD-14 | LOW | **PASS** | Score quantized to persisted representation on write and verify; stable sorted JSON; UTC ISO timestamp normalization. |
| AUD-15 | INFORMATIONAL | **PASS (documented)** | Versioned bigint advisory key, one-arg overload, correct lock order; throughput/p95 measured and disclosed. |
| AUD-16 | INFORMATIONAL | **BLOCKED** | Detection-only, fail-closed, no auto-repair; fork-response policy requires owner decision D-MPI-3/4 (ODR-003). |

---

## 4. Mandated wrong-patient / lost-reference determination

- **Wrong-patient identity linkage path — remediated in the change set:** AUD-01 (review reject no longer re-links or auto-matches to a high-scoring alternative; mints a detached citizen and excludes the rejected record). AUD-02 cross-tenant/lab link by non-admin is blocked at the app layer (DB uniqueness still pending MP-001).
- **Lost-reference path — remediated:** conflict-safe one-canonical-per-patient/citizen links (AUD-02); NID reconciliation (AUD-04); unordered-pair merge replay (AUD-06); broken-chain detection (AUD-13).
- **Residual wrong-patient risk:** AUD-07 (a corrected NID/name/DOB cannot be re-resolved through `/mpi/resolve` until D-MPI-5 is decided) remains a real, disclosed MEDIUM risk. It is not a new wrong link created by this code, but it can leave a known-wrong link uncorrected.

---

## 5. Acceptance gate evaluation

The acceptance condition in `MPI_INDEPENDENT_AUDIT_FINDINGS.md` is explicit: **do not accept MPI while any HIGH or CRITICAL finding is open.**

- CRITICAL open: **0**.
- HIGH open: **1** — AUD-02 is `PARTIAL` because DB `UNIQUE(patient_id)`/`UNIQUE(citizen_id)` requires an owner-authorized migration (MP-001) that was **not** executed.
- Therefore `ACCEPT` is **not permissible**.

---

## 6. Final verdict

# `REJECT`

**The MPI verdict is unchanged and carried forward.** This audit does not autonomously change `REJECT` to `ACCEPT`/`CONDITIONAL ACCEPT`, and `GOVERNANCE/FINAL_DECISION.md` remains `HOLD` with unchanged md5.

**Rationale:**
1. Baseline classifications remain CRITICAL 0 / HIGH 3 / MEDIUM 9 / LOW 2 / INFORMATIONAL 2; one HIGH (AUD-02) is still open at the schema/data-ownership layer.
2. AUD-07 (MEDIUM) and AUD-16 (INFORMATIONAL) are explicitly owner-blocked (D-MPI-5, D-MPI-3/4).
3. The acceptance gate forbids `ACCEPT` while any HIGH/CRITICAL finding is open.
4. No explicit owner authorization to change the verdict exists.

**What is proven complete:** 13 findings independently re-verified `PASS`, AUD-15 measured/documented, all 16 re-checked against actual source; 127 MPI/AUD regression tests re-run clean in this session; both real-PostgreSQL HTTP proof profiles 28/28; static gates clean; OpenAPI stable; no user work lost; no repository schema change; no commit/push.

**What is NOT claimed:** that the full backend suite is green (it has 1 pre-existing order-dependent Identity failure, documented in `MPI_POST_REMEDIATION_AUDIT.md §6`); that DB uniqueness is enforced (MP-001 pending); that fork response or payload-change semantics are decided (ODR-002/003 pending); that MPI is clinically acceptable or production-ready.

---

## 7. Owner decisions required before the verdict may be reconsidered

| Artifact | Finding | Decision owner |
|---|---|---|
| MP-001 — DB uniqueness migration proposal | AUD-02 | Data owner + migration authority |
| ODR-001 — review-decision audit taxonomy (D-MPI-4) | AUD-01/11/12 | Identity/data governance owner |
| ODR-002 — resolve payload-change semantics (D-MPI-5) | AUD-07 | Identity owner |
| ODR-003 — fork-response policy (D-MPI-3/4) | AUD-16 | Security/governance owner |
| ODR-004 — canonical hardening scope (D-MPI-6) | AUD-02 | Architecture owner |

None was executed. See Phase 4 review in `MPI_AND_HEALTH_CORE_FINAL_STATUS.md`.

---

## 8. Integrity attestations

- `GOVERNANCE/FINAL_DECISION.md` md5 `effdfeaf10234678d83b2668c4489552` — **unchanged**; `HOLD` intact.
- `GOVERNANCE/IDENTITY_REMEDIATION/MPI_INDEPENDENT_AUDIT_FINDINGS.md` — **unmodified**; `REJECT` intact.
- `/home/samertts/workspace/projects/gula-platform` — **untouched**.
- Uncommitted user work — **256 entries preserved**; **no** commit/push/merge/rebase/PR/deploy/reset/clean/add-all.
- Synthetic data only; no real patient data; no secrets printed or hardcoded.

**End of report.**

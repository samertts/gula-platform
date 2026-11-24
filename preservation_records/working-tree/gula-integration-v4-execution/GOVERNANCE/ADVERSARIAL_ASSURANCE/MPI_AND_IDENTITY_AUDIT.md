# Team A — MPI and Identity Reassessment (A3)

**Audit ID:** A3
**Date:** 2026-11-18
**Repository:** `gula-integration`
**Audited ref:** working tree at HEAD `2206654dc713ea2de8c564a3207dfe05fde23549`
**Sibling boundary:** `/home/samertts/workspace/projects/gula-platform` observed at `f478676b6fc375338648dde46fbf076c015a3f91`; read-only, not modified.
**Mode:** adversarial, read-only, synthetic/static evidence only.

---

## 1. Decision boundary (unchanged)

This reassessment does **not** overturn any protected verdict. The following decisions remain exactly as recorded:

| Decision / finding | Owner state after this audit |
|---|---|
| MPI implementation verdict | **REJECT** — unchanged |
| Release decision (`GOVERNANCE/FINAL_DECISION.md`) | **HOLD** — unchanged |
| AUD-02 | **OPEN** — HIGH; app-layer controls implemented, DB uniqueness still absent |
| AUD-07 | **OPEN** — BLOCKED on owner decision D-MPI-5 / ODR-002 |
| AUD-16 | **OPEN** — BLOCKED on owner decision D-MPI-3/4 / ODR-003 |
| MP-001 | **UNCHANGED** — owner-authorized DB uniqueness migration not executed |
| ODR-001, ODR-002, ODR-003, ODR-004 | **UNCHANGED** — owner decisions still required |
| D-020, D-021, ADR-A…ADR-J | **UNCHANGED** — no approval or state change made |

No elevated assurance status was awarded to any audited implementation. The assurance vocabulary used below is limited to `IMPLEMENTED`, `TESTED`, `INTEGRATED`, `BLOCKED`, and `NOT IMPLEMENTED`.

Protected MD5s were rechecked and match the recorded values:

| Protected file | MD5 |
|---|---|
| `GOVERNANCE/FINAL_DECISION.md` | `effdfeaf10234678d83b2668c4489552` |
| `GOVERNANCE/IDENTITY_REMEDIATION/MPI_FINAL_INDEPENDENT_AUDIT.md` | `1a02c01563c93b07a7cdb92c0462bf36` |
| `GOVERNANCE/IDENTITY_REMEDIATION/MPI_INDEPENDENT_AUDIT_FINDINGS.md` | `ea3969d09aaf7b0b28a065838b44a594` |

---

## 2. Method and evidence limits

**Performed:** static source inspection, call-site/grep analysis, controlled comparison against the protected decision and audit documents, and construction of synthetic reproduction/falsification designs.

**Not performed:** database connections, runtime HTTP execution, network access, full test-suite execution, use of real patient data, secret access, git staging/commit/push, or modification of any pre-existing file.

**Working-tree note:** the integration tree contains concurrent, uncommitted team changes. This audit reports the source as observed in the current working tree. No concurrent change was altered. The sibling repository was not written to.

---

## 3. Reassessment of the protected AUD-01…AUD-16 set

The table below records engineering-state observations only. It does not convert any prior finding into an accepted item, and it does not close an owner gate.

| Prior finding | Prior classification | Reassessment evidence observed | Current assurance status | Owner gate |
|---|---|---|---|---|
| AUD-01 | HIGH | `backend/app/services/mpi/api.py:425-557` delegates reject/create-new decisions to `create_detached_citizen()`; `backend/app/services/mpi/resolver.py:642-810` never scores/reuses a candidate, refuses non-pending replay, excludes the disputed NID, and writes a chained decision audit row. Regression file `backend/tests/unit/test_mpi_audit01_review_lifecycle.py` exists. | `INTEGRATED` / `TESTED` | ODR-001 taxonomy remains open; no closure claimed. |
| AUD-02 | HIGH | App-layer auth is present at `backend/app/routes/canonical_patient.py:37-47` (institutional lab role required) and conflict-safe locked links are present in `backend/app/services/mpi/canonical_service.py:173-268`. However `backend/app/models/canonical_patient.py:61-101` still has indexes only on `patient_links` and `citizen_links`; no `UNIQUE(patient_id)` or `UNIQUE(citizen_id)` is declared. | App control `IMPLEMENTED` / `TESTED`; DB control `NOT IMPLEMENTED`; overall `BLOCKED` | **MP-001** and **ODR-004** remain open. Finding remains HIGH and open. |
| AUD-03 | HIGH | Request session is closed before retry work at `backend/app/services/mpi/api.py:206-211`, `:361-362`, and `:453-467`; fresh-session reconcile follows. | `INTEGRATED` / `TESTED` | None re-opened by this pass. |
| AUD-04 | MEDIUM | NID lookup is re-read after the advisory lock before genesis in `backend/app/services/mpi/resolver.py:494-517`; the loser reuses the committed citizen instead of duplicating it. | `INTEGRATED` / `TESTED` | None re-opened by this pass. |
| AUD-05 | MEDIUM | Merge reconcile uses a fresh `SessionLocal()` with `finally: session.close()` at `backend/app/services/mpi/api.py:349-359`. | `INTEGRATED` / `TESTED` | None re-opened by this pass. |
| AUD-06 | MEDIUM | Unordered-pair idempotency is implemented at `backend/app/services/mpi/api.py:131-175` and `backend/app/services/mpi/resolver.py:874-902`; swapped replay returns the original audit outcome. | `INTEGRATED` / `TESTED` | None re-opened by this pass. |
| AUD-07 | MEDIUM | `backend/app/services/mpi/resolver.py:377-394` still returns the existing claim solely by `(lab_id, local_patient_id)` without comparing a payload fingerprint; `backend/app/services/mpi/models.py:149-181` has no payload-fingerprint or claim-version column. A corrected NID/name/DOB is still silently discarded. | `NOT IMPLEMENTED` / `BLOCKED` | **D-MPI-5 / ODR-002** remains open. Finding remains open. |
| AUD-08 | MEDIUM | Verifier moved from test-only to production-callable at `backend/app/services/mpi/resolver.py:300-334` and wired into the admin governance probe at `backend/app/routes/compliance.py:707-712`. It is explicitly detection-only (`policy` string at `resolver.py:326`). | `INTEGRATED` (detection only) | Fork-response policy **D-MPI-3/4 / ODR-003** remains open. |
| AUD-09 | MEDIUM | Prior protected verification recorded real-schema/real-session/HTTP evidence. This pass did not re-execute PostgreSQL probes and found no source contradiction in the current tree. | `TESTED` (prior evidence carried forward, not re-run here) | No new gate. |
| AUD-10 | MEDIUM | Prior protected verification recorded worker-error assertions and exact audit deltas. This pass did not re-run the concurrency harness. | `TESTED` (prior evidence carried forward, not re-run here) | No new gate. |
| AUD-11 | MEDIUM | Both review decisions append chained rows: `backend/app/services/mpi/resolver.py:756-810` (`confirm_reviewed_match`) and `:642-753` (reject/create-new), reached from `api.py:425-557`. | `INTEGRATED` / `TESTED` | ODR-001 taxonomy remains recorded as open. |
| AUD-12 | MEDIUM | Canonical writes use the chained `audit_logs` helper at `backend/app/routes/canonical_patient.py:50-89`; production sessions receive the durable row in the same transaction. | `INTEGRATED` / `TESTED` | ODR-001 taxonomy remains recorded as open. |
| AUD-13 | LOW | `backend/app/services/mpi/models.py:113-146` raises `BrokenCanonicalChainError` under `strict=True` on decision/write paths and logs a warning on read fallbacks. | `IMPLEMENTED` / `TESTED` | No new gate. |
| AUD-14 | LOW | Prior protected verification recorded score quantization and stable canonical JSON. This pass found no current source contradiction and did not re-run the numeric round-trip harness. | `TESTED` (prior evidence carried forward, not re-run here) | No new gate. |
| AUD-15 | INFORMATIONAL | Single global advisory key remains documented as a throughput ceiling; protected final audit records measured disclosure. No sharding change observed. | `IMPLEMENTED` (documented ceiling) | Capacity action remains operational, not closed here. |
| AUD-16 | INFORMATIONAL | Detection-only probe at `backend/app/services/mpi/resolver.py:300-334` explicitly reports `forked` and logs a warning; there is no auto-repair and no executed fork-response policy. | `BLOCKED` | **D-MPI-3/4 / ODR-003** remains open. |

**Net effect:** the engineering posture is materially improved versus the original REJECT findings, but the protected outcome cannot change while AUD-02 remains HIGH/open at the schema layer and AUD-07/AUD-16 remain owner-blocked.

---

## 4. New MPI findings discovered by this pass

These are additions, not replacements for AUD-01, AUD-02, AUD-07, or AUD-16. Full machine-readable detail is in `GOVERNANCE/ADVERSARIAL_ASSURANCE/FINDINGS_A3_MPI_CLINICAL.json`.

### AUD-MPI-001 — Unverified lab-supplied NID short-circuits identity matching into an auto-claim

- **Severity:** HIGH; **likelihood:** MEDIUM.
- **Evidence:** `backend/app/services/mpi/resolver.py:420-430` treats any `nid_hash` equality hit as `best_method="nid_exact"` with score `1.0`; `:476-480` auto-claims on that method regardless of other demographics; `backend/app/services/mpi/models.py:79` defines `nid_verified` with `default=False`; grep across backend write paths shows no assignment of `nid_verified=True` in MPI registration (`resolver.py:522` and `:702` explicitly set `False`; `backend/app/routes/register.py:94` sets `False`). `backend/app/config.py:215-220` permits a non-production fallback HMAC key and only warns, so environment key-stability discipline is a contributing control concern, not a replacement for provenance verification.
- **Synthetic reproduction:** seed citizen A with NID hash H, name/DOB/gender of A; seed patient P in a lab with name/DOB/gender of B but submit raw national ID that hashes to H; call `/mpi/resolve`. Observe the returned citizen is A, `match_method="nid_exact"`, `match_score=1.0`, and `nid_verified` remains `False`. No real data is needed.
- **Falsification:** the finding is false if a verified/authoritative NID gate blocks or downgrades an unverified `nid_exact` hit before auto-claim, or if a test proves `nid_verified=True` is required and set by an authoritative verification step for this path.
- **Root cause:** the fast path conflates "hash equality of a submitted identifier" with "verified national identity"; the existing `nid_verified` field is never used as an authorization signal for auto-match.
- **Impact:** a wrong NID supplied by an upstream lab, registration error, or stale identifier can bind one lab patient to another person's canonical identity, propagating results and demographics to the wrong record. This is a distinct path from AUD-01 (review reject) and AUD-04 (concurrent NID race).
- **Remediation:** require an authoritative verification signal before granting `nid_exact` auto-claim authority; otherwise downgrade to probabilistic scoring and force `pending_review` when demographics disagree; persist verification provenance and reviewer; add a synthetic regression test asserting an unverified NID cannot produce score `1.0` auto-claim.
- **Alternatives:** (a) NID-verification service assertion with cached expiry; (b) dual-factor match requiring NID plus DOB/name agreement; (c) lab-trusted-identifier allowlist with owner approval. No alternative may silently auto-claim on an unverified hash.
- **Owner gating:** yes — identity-proofing policy for NID provenance must be decided by the identity/data owner.

### AUD-MPI-002 — Latent non-atomic canonical auto-create has no lock or DB uniqueness fence

- **Severity:** LOW; **likelihood:** LOW (currently latent; no callers found).
- **Evidence:** `backend/app/services/mpi/canonical_service.py:20-61` performs `get_canonical_by_patient()` / `get_canonical_by_citizen()` then inserts `CanonicalPatient` plus a link row without `acquire_canonical_link_lock()`; the lock is imported at `:17` and used only at `:191` and `:237` in the explicit link functions. `backend/app/models/canonical_patient.py:61-101` still lacks DB uniqueness. Static grep found no in-repo caller of `find_or_create_canonical()`.
- **Synthetic reproduction:** if a future caller invokes this function for the same patient from two sessions, both can observe "no existing canonical", insert two canonical rows and two links, and a later `.first()` lookup will strand one canonical. This is a design proof only; no runtime execution was performed.
- **Falsification:** the finding is false if all callers are proven to hold `acquire_canonical_link_lock()` and DB uniqueness prevents duplicate links, or if the function is removed/archived.
- **Root cause:** helper was written on a check-then-insert pattern while the repository's canonical write discipline was added only to the explicit link endpoints.
- **Impact:** dormant split-identity risk if the helper is wired into national onboarding; overlaps the unresolved MP-001 schema concern but is a distinct code path.
- **Remediation:** acquire the canonical link lock inside the helper, re-check under lock, use conflict-safe insert, and require MP-001 uniqueness before exposing callers; add a concurrency regression test before first use.
- **Alternatives:** delete the unused helper, or convert it to a thin wrapper over the locked link service.
- **Owner gating:** yes — full fence depends on MP-001 / ODR-004.

---

## 5. Why REJECT and HOLD are unchanged

1. **New wrong-patient route:** AUD-MPI-001 shows an unverified identifier can bypass demographic matching and auto-claim a canonical identity.
2. **Open HIGH schema gap:** AUD-02/MP-001 still lacks `UNIQUE(patient_id)` and `UNIQUE(citizen_id)`; application locks do not provide a database-level invariant.
3. **Owner-blocked correction paths:** AUD-07 and AUD-16 remain dependent on ODR-002 and ODR-003; no decision was made or inferred here.
4. **Clinical safety gaps:** the companion hazard register records a critical-result notification no-op and validation handoff defects that independently block a production-readiness argument.
5. **Evidence boundary:** no DB, runtime, network, or real-data verification was permitted; this pass cannot upgrade assurance.
6. **No protected state change:** protected MD5s, ADRs, decision registry items, and the sibling repository are unchanged; no commit or staging operation was performed.

**Conclusion:** the protected MPI verdict **REJECT** and release verdict **HOLD** stand. This audit adds six new findings (see JSON) and does not close, downgrade, or reinterpret any protected finding.

---

## 6. Artifact control statement

The only files created by this audit are:

- `GOVERNANCE/ADVERSARIAL_ASSURANCE/MPI_AND_IDENTITY_AUDIT.md`
- `GOVERNANCE/ADVERSARIAL_ASSURANCE/CLINICAL_SAFETY_HAZARD_REGISTER.md`
- `GOVERNANCE/ADVERSARIAL_ASSURANCE/FINDINGS_A3_MPI_CLINICAL.json`

No pre-existing file, including the concurrent Team A6 artifact in the same directory, was modified. No secret, credential, or patient datum is included; all examples are synthetic.

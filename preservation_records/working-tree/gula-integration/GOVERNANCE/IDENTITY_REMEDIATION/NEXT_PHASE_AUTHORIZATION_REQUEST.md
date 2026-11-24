# Next-Phase Authorization Request — Identity Remediation

**Status: REQUEST ONLY — nothing below is approved or started.**

**Repository:** `/home/samertts/workspace/projects/gula-integration` @
`integration/gula-unification-v1`, HEAD `2827c1ff…`.
**Release decision:** `FINAL_DECISION.md` remains **HOLD** (md5 `effdfeaf…`).
**D-020 / D-021:** remain `PENDING_APPROVAL` (`GOVERNANCE/GECS/DECISION_REGISTRY.md` §D).

## 1. What this tranche delivered (for review)

Source-verified P0 fixes, all uncommitted, all with synthetic regression tests:

| Unit | Delivered | Evidence |
|---|---|---|
| P0-A | Canonical NID/HMAC, canonical registration writes, no raw NID at rest, POST lookup (GET deprecated) | 17 new + 35 governance tests pass |
| P0-B | JWKS fails closed (503, no keys); `jwks_uri` kept for spec compliance; no key generated | 30 auth-infrastructure tests pass |
| P0-C | Env-configurable WebAuthn, strict base64url, namespaced single-use fail-closed challenges, 4xx translation | 18 new tests pass |
| P0-D1/D2 | Correct `bump_perm_version` signature; session revocation on password change/reset | 3 new tests pass |
| P0-D3 | `session.py` fail-closed shared store (raw `cache` → `security_store()`; `max(cached, db_version)`; malformed/stale handling) — **delivered this tranche** | 19 new tests (22 total file) pass |
| P0-E1 | MPI merge integrity (self/cycle/idempotency/reason, claim repoint + provenance, hash-chained audit, SAVEPOINT rollback) | 6 new tests pass |
| P1-01 (NHID) | Source inventory (11 families) + 23 synthetic compatibility tests (**no identifier changed**) — delivered this tranche | 23 new tests pass |

Final verification: this tranche **128 passed / 0 failed (EXIT 0, 98.99s)** over
the 6 P0 suites; prior tranche **109 passed / 0 failed (EXIT 0)**; broader
identity/auth regression **231 passed / 4 skipped / 0 failed**. Exact commands
and limits in `ACCEPTANCE_EVIDENCE.md` §2 and §6.

Also delivered this tranche (source/inventory evidence, **not implementation**):
P0-D4 device-identity evidence report, P0-E2 MPI cross-domain reference inventory
+ unmerge blockers, NHID canonicalization readiness report. See §2.

Explicitly **not** delivered: P0-D4 (device-revocation session termination),
P0-E2 (MPI unmerge / cross-domain reference migration), canonical NHID model /
migration / ADR revision, OIDC key management, passkey production activation,
OCR benchmarks, any migration/DDL, or any release-status change.

## 2. Decisions requested (each independent; none granted by this document)

### A. Session-store hardening (P0-D3) — CODE DELIVERED; policy `NEEDS_OWNER_DECISION`
The `session.py` conversion is **implemented and tested** this tranche: raw
`cache` → fail-closed `security_store()`, `max(cached, db_version)`, malformed/
stale handling, authoritative-DB fallback with CRITICAL logs. Only one clean
file was changed; user-modified files were read-only. Remaining owner decisions:
the production `ALLOW_DEGRADED_REDIS` policy and whether to impose a strict
503-on-any-store-outage policy (R-D3 — would require editing the user-modified
`dependencies.py`). Dev fallback is documented; **no HA/failover claim**.

### B. Device-revocation session termination (P0-D4) — `NEEDS_OWNER_DECISION`
**Source evidence delivered this tranche** (`DEVICE_IDENTITY_AND_REVOCATION_REPORT.md`):
`Device.account_id` is a NIAM ULID; two disjoint session families exist; no
device→session/credential edge exists in the enforced auth path (`revoke_device`
only flips `is_active`). Requires an owner decision on device ownership scope
(Person vs Account), revocation scope, and an account↔legacy-user bridge before
any session-termination behavior can be implemented. No numeric mapping was
invented for a NIAM ULID.

### C. MPI unmerge / cross-domain dependent repointing (P0-E2) — BLOCKED
**Source inventory delivered this tranche** (`MPI_CROSS_DOMAIN_INTEGRITY_REPORT.md`):
only `IdentityClaim` is repointed on merge; ~90 FK/soft-reference sites across
MPI/national/EHR/care-continuum remain; there is no reference-change log, no
unmerge writer, and the hash chain is not verifiable as written. Requires
historical event data and a schema/ownership decision covering national patients,
encounters, orders, samples, results, documents, claims and audit. Owner +
clinical-safety + legal decisions required.

### D. OIDC activation — `SECURITY_REVIEW_REQUIRED`
Approve an asymmetric key-management scheme (generation, storage, rotation,
revocation). Until then the JWKS endpoint stays fail-closed; no key is generated.

### E. Passkey / WebAuthn activation — `SECURITY_REVIEW_REQUIRED`
Confirm production RP ID and origin, plus an authenticator/attestation policy.
Code correctness is in place; activation is not.

### F. OCR / document verification — `LEGAL_REVIEW_REQUIRED` +
`BLOCKED_BY_EXTERNAL_DEPENDENCY`
Provide a legally authorized de-identified Iraqi-document corpus and legal
rulings on document/privacy/consent/retention before any benchmark or L0→higher
movement. ID Scan stays advisory (`needs_confirmation`, no authenticity check).

### F1. Canonical NHID adoption (P1-01) — `NEEDS_OWNER_DECISION` + `LEGAL_REVIEW_REQUIRED`
**Source inventory + 23 synthetic compatibility tests delivered this tranche**
(`NHID_CANONICALIZATION_READINESS.md`); no identifier changed and no canonical
model implemented. 11 competing identifier families exist and `IQ…` is falsely
claimed as sole authority in ADRs. Requires an owner decision on a single issuer/
namespace/checksum, a legal ruling on NID usage/retention/consent, an approved
migration/alias strategy (no bulk renumbering), and ADR-012 / national ADR
revision.

### G. F-085 / NR-011 metadata completeness — `NEEDS_OWNER_DECISION`
Registering `DocIntelBase` / `InsBase` would alter the protected
`env.py +49/-0` delta. Needs explicit authorization and database-owner sign-off.

### H. Release decisions D-020 / D-021 — out of implementation authority
Human security sign-off and clinical-safety certification remain pending with
their respective owners. This tranche does not satisfy or approximate them.

## 3. Requested disposition of current work

- **Review** the uncommitted diff and the reports in this directory (the four
  original final reports plus this tranche's four new evidence reports:
  `SESSION_SECURITY_REMEDIATION_REPORT.md`,
  `DEVICE_IDENTITY_AND_REVOCATION_REPORT.md`,
  `MPI_CROSS_DOMAIN_INTEGRITY_REPORT.md`, `NHID_CANONICALIZATION_READINESS.md`).
- **Do not** treat the passing tests as production readiness.
- **Do not** commit, merge, deploy, migrate, or activate any router/engine
  without explicit owner approval.
- The session stops here pending instruction.

## 4. Honest baseline that must be preserved

0 PRODUCTION_VERIFIED · 0 RUNTIME_VERIFIED · 0 E2E_VERIFIED ·
RPO/RTO UNMEASURED · F-085 open · OCR/NFC `L0` · ID Scan advisory
`needs_confirmation` · D-020/D-021 pending · HOLD unchanged ·
`gula-platform` untouched · no commit created.

## 5. MPI integrity & concurrency tranche — new decisions requested

Evidence: `MPI_INTEGRITY_CONCURRENCY_REMEDIATION_REPORT.md`.
Final combined MPI regression **65 passed / 0 failed, EXIT 0**. All work uncommitted.

| # | Decision requested | Classification |
|---|---|---|
| D-MPI-1 | Choose audit-append serialization: sentinel-row `FOR UPDATE` (portable, needs ≥1 row) vs `pg_advisory_xact_lock` (PG-coupled, covers genesis) vs SERIALIZABLE + bounded idempotent retry. Fork detection is already in place; prevention is **not** implemented. | `NEEDS_OWNER_DECISION` |
| D-MPI-2 | Provision a dedicated disposable MPI PostgreSQL test DB + explicit `MPI_TEST_POSTGRES_URL` so two-session deadlock/fork tests can run. No PG writes were made in this tranche. | `BLOCKED_BY_EXTERNAL_DEPENDENCY` |
| D-MPI-3 | Cross-domain reference ownership/repointing policy and unmerge history design (~90 references; only `IdentityClaim` is repointed today). | `NEEDS_OWNER_DECISION` + `LEGAL_REVIEW_REQUIRED` |
| D-MPI-4 | Approve new `MergeAudit.event_type` values so review confirm/reject decisions can be hash-chained. | `NEEDS_OWNER_DECISION` + `SECURITY_REVIEW_REQUIRED` |
| D-MPI-5 | Policy for concurrent first-time `resolve_identity` claim insertion and bounded retry behaviour. | `NEEDS_OWNER_DECISION` |
| D-MPI-6 | Extend key-ordered locking/verification to `canonical_service.merge_canonicals()` in a separate tranche. | `NEEDS_OWNER_DECISION` |
| D-MPI-7 | Allow a docstring-only cleanup of the pre-existing `RUF002` EN DASH in `resolver.py:13`. | `RECOMMENDED` (not granted here) |

Explicitly not delivered: audit-fork prevention, PostgreSQL concurrency proof, MPI Unmerge,
cross-domain repointing, review-decision audit events, resolve-race fix, canonical-service fix,
any API/schema/migration/DDL change, or any release decision change. HOLD, D-020 and D-021 are
unchanged. **STOP — await explicit owner authorization.**

## 6. MPI PostgreSQL concurrency tranche — gate failed, new decisions requested

Evidence: `MPI_POSTGRESQL_CONCURRENCY_REMEDIATION_REPORT.md`. Phase A discovery completed without
any DB connection; the strict 7-condition safety gate **failed (0/7 proven, 4 contradicted)**.
No source file, test, migration, DDL or API changed. No commit created.

| # | Decision requested | Classification |
|---|---|---|
| D-MPI-2 *(reaffirmed, now with evidence)* | Authorize a dedicated disposable PG test DB **plus** a dedicated docker network/volume, a least-privilege role (`CONNECT` on `mpi_test` only), an explicit `MPI_TEST_POSTGRES_URL`, and written permission for synthetic-table DDL inside that DB. The only reachable instance (`gula-postgres`) is the protected platform's application DB (`gula-platform_default` network, `pgdata` volume, `POSTGRES_*` superuser keys) and **must not be contacted**. | `BLOCKED_BY_EXTERNAL_DEPENDENCY` |
| D-MPI-2a | If the last-row `FOR UPDATE` sentinel is chosen, decide the genesis case: a dedicated sentinel row would be a **schema change → STOP**, otherwise use a transaction-scoped advisory lock. | `NEEDS_OWNER_DECISION` |
| D-MPI-1 *(unchanged)* | Choose the audit-append serialization mechanism. Recommendation only: last-row `FOR UPDATE` (existing table + in-repo precedent `canonical_audit.py:139`); no benchmark possible, so no selection made. | `NEEDS_OWNER_DECISION` |

Minimal setup, isolation and disposal method, permissions, risks and €0 cost estimate: report §12.
No runtime/E2E/production evidence was produced; 0 PRODUCTION_VERIFIED, 0 RUNTIME_VERIFIED,
0 E2E_VERIFIED, RPO/RTO UNMEASURED, HOLD, D-020/D-021 pending, `gula-platform` untouched.
**STOP — await explicit owner authorization.**

### D-MPI-2 — environment now provisioned (separate authorization still required)

Evidence: `MPI_ISOLATED_POSTGRES_PROVISIONING_REPORT.md`. The dedicated environment was created
after all 10 isolation conditions were proven PASS: container `gula-mpi-pg-test`, network
`gula-mpi-test-network`, volume `gula-mpi-test-data`, DB `mpi_test`, non-superuser role
`mpi_test_user`, `MPI_TEST_POSTGRES_URL` stored out-of-repo with mode 0600. PostgreSQL 16.14;
loopback-only `127.0.0.1:55432`; `user_tables=0`; protected repo untouched; no source/schema/test
change; no Git operation. `PROVISIONING_STATUS: PASS` · `ISOLATION_STATUS: VERIFIED`.

D-MPI-2's **infrastructure portion is satisfied**. A distinct authorization is still required for
`GULA — MPI POSTGRESQL CONCURRENCY TESTING & SERIALIZATION EVALUATION`, including synthetic-table
DDL inside `mpi_test`. D-MPI-1 (serialization choice) and D-MPI-2a (genesis handling) remain open.
HOLD unchanged. **STOP.**

### D-MPI concurrency evaluation — COMPLETE (implementation still requires authorization)

Evidence: `MPI_POSTGRESQL_CONCURRENCY_TEST_REPORT.md` (22 sections). The separately authorized
evaluation tranche ran against isolated `mpi_test` using schema `mpi_concurrency_test` only, with
synthetic fixtures and independent sessions. Result: **65 passed / 0 failed / 0 skipped, EXIT 0,
87.61 s**; `DATABASE_IDENTITY: VERIFIED`, `TEST_SCHEMA: mpi_concurrency_test`. Proven: unlocked
audit-tail read forks (50/20/10/5 fork groups at 2/5/10/20 workers); naive read-modify-write loses
1/4/9/19 increments; opposite-order locking deadlocks (`40P01`); sentinel-row (A) and
transaction-scoped advisory lock (B) are fork-safe including genesis; SERIALIZABLE (C) is **not
guaranteed** (rare genesis fork reproduced despite correct full-transaction retry); atomic SQL (D)
prevents lost updates only. **No strategy was selected or implemented.** `SOURCE_FILES_CHANGED: 0`,
`APPLICATION_MIGRATIONS_CREATED: 0`, `GIT_OPERATIONS: NONE`, protected repo clean, HOLD md5
`effdfeaf…` unchanged, D-020/D-021 `PENDING_APPROVAL`, D-MPI-1 / D-MPI-2a remain
`NEEDS_OWNER_DECISION`. **STOP — await explicit owner authorization for implementation.**

### Post-analysis pointer — architecture decision preparation (read-only, 2026-11-18)

The follow-on, separately authorized **analysis-only** tranche produced four `PROPOSED — NOT APPROVED`
artifacts that build on the evidence above without changing any decision:
`MPI_SERIALIZATION_ARCHITECTURE_DECISION.md` (recommended E = B + D + existing ordered locking),
`MPI_IMPLEMENTATION_EXECUTION_PLAN.md` (MPI-01..MPI-10), `MPI_FAILURE_RECOVERY_MATRIX.md`, and
`MPI_CROSS_COMPONENT_IMPACT.md`. D-MPI-1 remains `NEEDS_OWNER_DECISION`; HOLD, D-020 and D-021 are
unchanged. No source, migration, API, configuration or Git change was made.

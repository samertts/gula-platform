# Implementation Backlog — Identity & Platform Remediation

> Source: `GOVERNANCE/IDENTITY_ARCHITECTURE_STUDY/` (22 documents), reconciled
> against live source on branch `integration/gula-unification-v1` at
> `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0`.
> **Statuses below were backfilled after the P0 tranche was executed. Execution
> detail and evidence are in `IMPLEMENTATION_PROGRESS.md` and
> `ACCEPTANCE_EVIDENCE.md`.** Marking an item IMPLEMENTED is not a release
> approval and does not change `FINAL_DECISION.md` (HOLD).

## 1. Priority 0 — current tranche

| ID | Item / source finding | Classification | Target files (all confirmed clean at Phase 0) | Test plan | Rollback | Status |
|---|---|---|---|---|---|---|
| P0-A1 | Canonicalize NID digits: `re.sub(r"[^\d]")` keeps Arabic-Indic digits, so `١٢٣` ≠ `123`. Consolidate normalization + HMAC in `backend/app/services/identity.py:213-241` | `OWNER_APPROVED` | `backend/app/services/identity.py` | New `test_national_id_canonicalization.py`: Arabic-Indic, Extended Arabic-Indic, Western, whitespace, punctuation, invalid, equivalence, no family/number collision, legacy-record compatibility | `git checkout -- <file>` (no commit made) | **IMPLEMENTED — TESTS PASSED** |
| P0-A2 | `register.py:341-343` and `:626-628` HMAC the **raw** NID; inconsistent with canonical helper → duplicate bypass | `OWNER_APPROVED` | `backend/app/routes/register.py` | Registration HMAC parity tests; duplicate detection across representations | single-file revert | **IMPLEMENTED — TESTS PASSED** |
| P0-A3 | `identity_persistence_service.py:65-72` writes raw NID to `documents_json`; `:264-267` hashes raw NID with unsalted SHA-256 fallback | `OWNER_APPROVED` | `backend/app/governance/services/identity_persistence_service.py` | Assert no raw NID at rest in `documents_json`; hash parity (digit-only NIDs canonicalized; alphanumeric references keep historical hash) | single-file revert | **IMPLEMENTED — TESTS PASSED** |
| P0-A4 | `routes/identity.py:67` exposes NID in URL query string | `OWNER_APPROVED` (add secure alternative; remove only with documented contract correction) | `backend/app/routes/identity.py` | POST body lookup test; no NID in logged request path (deprecated GET retained — removal needs owner-approved contract change) | single-file revert | **IMPLEMENTED — TESTS PASSED** |
| P0-A5 | Audit out-of-scope NID hash writers (`admin_service.py:350`, `routes/admin.py:771`, `core/seeds.py::hash_nid`) for a future compatibility tranche | `RECOMMENDED` | documentation only this tranche | — | n/a | DEFERRED |
| P0-B1 | `oauth2_provider.py:172-178` returns an empty JWKS while discovery advertises `jwks_uri`; HS256 has no public keys | `OWNER_APPROVED` / `SECURITY_REVIEW_REQUIRED` for OIDC readiness | `backend/app/security/oauth2_provider.py`, `backend/app/routes/oauth2.py`, `backend/tests/test_auth_infrastructure.py` | JWKS endpoint fails closed (503, no usable key set); `jwks_uri` **retained in discovery for OIDC spec compliance** (endpoint itself is fail-closed); regression tests updated with rationale — no asymmetric key generated | single-file reverts | **IMPLEMENTED — TESTS PASSED** (OIDC activation still `SECURITY_REVIEW_REQUIRED`) |
| P0-C1 | `shared/auth/webauthn.py:22-24` hardcoded `RP_ID`/`RP_ORIGIN`; `:50,86` `default=str` serializes bytes as `"b'…'"`; no validated config | `OWNER_APPROVED` / `SECURITY_REVIEW_REQUIRED` for passkey activation | `shared/auth/webauthn.py` | base64url challenge round-trip, config validation, invalid origin, invalid RP ID (env-configurable; passkey activation still `SECURITY_REVIEW_REQUIRED`) | single-file revert | **IMPLEMENTED — TESTS PASSED** |
| P0-C2 | `mfa_service.py:93-106,133-153` swallows cache failure → empty challenge; no single-use, shared registration/auth key | `OWNER_APPROVED` | `backend/app/security/mfa_service.py` | expired, replayed and missing challenge rejected; separate reg/auth namespaces; store errors fail closed (not swallowed); single-use consume | single-file revert | **IMPLEMENTED — TESTS PASSED** |
| P0-D1 | `password_reset.py:91` calls `bump_perm_version(db, current_user.id)` but signature is `(user, db, …)` → crash | `OWNER_APPROVED` | `backend/app/routes/password_reset.py` | regression test: change-password succeeds and bumps version with correct `(user, db, …)` signature | single-file revert | **IMPLEMENTED — TESTS PASSED** |
| P0-D2 | `reset_password` (`:57-77`) never invalidates existing sessions | `OWNER_APPROVED` | `backend/app/routes/password_reset.py` | session after reset rejected via perm-version `bump_perm_version(user, db, reason="password_reset")` | single-file revert | **IMPLEMENTED — TESTS PASSED** |
| P0-D3 | `session.py:59,87,96` uses raw cache; fail-open fallback can leave compromised sessions active | `OWNER_APPROVED` | `backend/app/security/session.py` | Converted to fail-closed `security_store()`; `max(cached, db_version)`; malformed/stale handling; dev fallback documented | single-file revert | **IMPLEMENTED — TESTS PASSED (this tranche)** — 22-test session suite; see `SESSION_SECURITY_REMEDIATION_REPORT.md`. Dev fallback true, HA/failover NOT claimed. Strict 503-on-store-outage policy = `NEEDS_OWNER_DECISION` (R-D3) |
| P0-D4 | `identity/services/device_service.py:79-85` device revocation is flag-only; `Device` has no LabUser/User id (`account_id` is a NIAM ULID) | `NEEDS_OWNER_DECISION` + `SECURITY_REVIEW_REQUIRED` | documentation only this tranche | requires account↔device ownership mapping; no numeric map invented | n/a | **BLOCKED (source evidence recorded)** — two disjoint identity universes; no device→session/credential edge in enforced auth; see `DEVICE_IDENTITY_AND_REVOCATION_REPORT.md` |
| P0-E1 | `mpi/resolver.py:354-400` merge sets `merged_into_id` but does not repoint `IdentityClaim` rows (`:367-369`) | `OWNER_APPROVED` for `IdentityClaim` only | `backend/app/services/mpi/resolver.py` + new synthetic test | self-merge/cycle rejection, idempotency, claim repoint, audit/provenance, post-merge consistency check, SAVEPOINT rollback on failure | single-file revert | **IMPLEMENTED — TESTS PASSED** |
| P0-E2 | Unmerge/split and cross-domain dependent references (national patients, encounters, orders, samples, results, documents, claims, audit) | `BLOCKED_BY_EXTERNAL_DEPENDENCY` / `NEEDS_OWNER_DECISION` / `SECURITY_REVIEW_REQUIRED` | documentation only | requires historical event data + schema decision | n/a | **BLOCKED (inventory recorded)** — ~90 FK/soft-ref sites, only `IdentityClaim` repointed; no reference-change log; see `MPI_CROSS_DOMAIN_INTEGRITY_REPORT.md` |

## 2. Priority 1 — prepared, not implemented

| ID | Item | Classification | Notes |
|---|---|---|---|
| P1-01 | Single NHID authority; reconcile `HID-`, `HN-`, `IQ…`, `NB/FR/VS/EM`, `NH-` formats | `NEEDS_OWNER_DECISION` + `LEGAL_REVIEW_REQUIRED` | **Source inventory + 23 synthetic compatibility tests delivered this tranche (`VERIFIED_IN_SOURCE` / `TEST_VERIFIED`); canonical model NOT implemented. See `NHID_CANONICALIZATION_READINESS.md`.** No bulk renumbering; issuer/namespace undecided |
| P1-02 | Consolidate 3+ matchers (MPI, `identity_matching.py`, `health_data/mdm/matching.py`) | `NEEDS_OWNER_DECISION` | Do not create a competing registry or orchestrator |
| P1-03 | Provisional identity path / emergency care without NID | `OWNER_APPROVED` product decision, `LEGAL_REVIEW_REQUIRED` for evidence | Phase 4 |
| P1-04 | Four guardian stores → single logical model; age-18 transition | `NEEDS_OWNER_DECISION` + `LEGAL_REVIEW_REQUIRED` | Biological relation ≠ legal authority |
| P1-05 | Birth/death evidence separation; remove stub `confidence: 1.0` connectors | `SECURITY_REVIEW_REQUIRED` + `LEGAL_REVIEW_REQUIRED` | Phase 7; national router stays unmounted |
| P1-06 | `national_router` activation matrix | `NEEDS_OWNER_DECISION` + `SECURITY_REVIEW_REQUIRED` | No blanket activation |
| P1-07 | NIAM guardian/death route↔service async/sync mismatch | `SECURITY_REVIEW_REQUIRED` | Phase 6/7 |
| P1-08 | `mfa_device` FK only to `lab_users` → non-lab accounts cannot enroll | `NEEDS_OWNER_DECISION` | Schema/migration; not this tranche |

## 3. Priority 2 — blocked / governance-only

| ID | Item | Classification | Notes |
|---|---|---|---|
| P2-01 | F-085: register `DocIntelBase` (21) + `InsBase` (30) in Alembic | `NEEDS_OWNER_DECISION` | Would change `env.py +49/-0`; **not authorized** |
| P2-02 | `national_facilities` duplicate ownership (F-014 / ADR-B) | `NEEDS_OWNER_DECISION` | ADR-B pending |
| P2-03 | DocIntel no-op encryption/audit/events, dummy benchmarks, undeclared OCR libs | `SECURITY_REVIEW_REQUIRED` | Keep `BLOCKED`; do not activate |
| P2-04 | OCR engine benchmark (PaddleOCR/Tesseract/docTR/EasyOCR) | `BLOCKED_BY_EXTERNAL_DEPENDENCY` | Needs synthetic/de-identified Iraqi samples; no invented metrics |
| P2-05 | Document verification / government source / NFC | `BLOCKED_BY_EXTERNAL_DEPENDENCY` + `LEGAL_REVIEW_REQUIRED` | OCR/NFC stay `L0` |
| P2-06 | D-020 human security sign-off, D-021 clinical certification | `NEEDS_OWNER_DECISION` | Out of implementation authority |
| P2-07 | RPO/RTO measurement, DR drill | `BLOCKED_BY_EXTERNAL_DEPENDENCY` | Remain UNMEASURED |
| P2-08 | Iraqi statutory interpretation (Law 3/2016, Law 21/2024, privacy, consent, retention) | `LEGAL_REVIEW_REQUIRED` | All `UNVERIFIABLE` |

## 4. Ownership map (implementation targets)

| Area | Owner role | Approval needed to go beyond this tranche |
|---|---|---|
| NID canonicalization | Backend/Identity engineer | Security lead for certification |
| OAuth/OIDC | Security engineer | Owner + key-management decision |
| WebAuthn | Security engineer | Security lead + domain/origin owner |
| Session/permission | Security engineer | Security lead |
| MPI merge | Data-integrity engineer | Data owner + clinical safety owner |
| Schema/migration | Database owner | Explicit owner authorization (not granted) |
| Legal/evidence | Qualified Iraqi counsel | Legal review (not available in this program) |

## 5. MPI integrity & concurrency tranche (this session)

Full evidence: `MPI_INTEGRITY_CONCURRENCY_REMEDIATION_REPORT.md`.

| ID | Item | Classification | Status / notes |
|---|---|---|---|
| P0-E3 | MPI audit `occurred_at` hashed value ≠ persisted value (unreproducible `entry_hash`) | `OWNER_APPROVED` (bounded) | `TEST_VERIFIED` — one timestamp instance now feeds hash and column |
| P0-E4 | MPI `MergeAudit` chain verifier (tamper + fork detection) | `OWNER_APPROVED` (bounded) | `TEST_VERIFIED` — detection only, no endpoint added |
| P0-E5 | Deterministic citizen lock order (single key-ordered `SELECT … FOR UPDATE`) | `OWNER_APPROVED` (bounded) | `TEST_VERIFIED` in source/behaviour; **not** runtime-proven on PostgreSQL |
| P0-E6 | Serialize concurrent audit appends (fork prevention) | `NEEDS_OWNER_DECISION` | `BLOCKED` — sentinel-row vs advisory-lock vs SERIALIZABLE choice required |
| P0-E7 | Dedicated disposable PostgreSQL test DB for concurrency proof | `BLOCKED_BY_EXTERNAL_DEPENDENCY` | no PG writes performed; SQLite emits no `FOR UPDATE` |
| P0-E8 | Review confirm/reject hash-chained audit events | `NEEDS_OWNER_DECISION` + `SECURITY_REVIEW_REQUIRED` | event taxonomy not changed |
| P0-E9 | `resolve_identity` concurrent first-resolve `IntegrityError` | `NEEDS_OWNER_DECISION` | not changed |
| P0-E10 | `canonical_service.merge_canonicals()` locking/audit/verification | `NEEDS_OWNER_DECISION` | separate path, not changed |
| P0-E11 | Cross-domain reference ownership / repointing / unmerge | `NEEDS_OWNER_DECISION` + `LEGAL_REVIEW_REQUIRED` | inventory only; nothing repointed |

## 6. MPI PostgreSQL concurrency tranche (this session)

Full evidence: `MPI_POSTGRESQL_CONCURRENCY_REMEDIATION_REPORT.md`. **Stopped at the database safety
gate; no DB connection, no source change, no test run.** Items below are unchanged from §5; this
section records the new evidence only.

| ID | Item | Classification | Status / notes |
|---|---|---|---|
| P0-E6 | Serialize concurrent audit appends (fork prevention) | `NEEDS_OWNER_DECISION` | **No mechanism selected** — source comparison of sentinel-row/advisory-lock/SERIALIZABLE recorded in report §6; no benchmark possible |
| P0-E7 | Dedicated disposable PostgreSQL test DB for concurrency proof | `BLOCKED_BY_EXTERNAL_DEPENDENCY` | **Gate FAILED (0/7 conditions proven)** — only reachable PG is the protected platform's `gula-postgres` (`gula-platform_default` network, `pgdata` volume, `POSTGRES_*` superuser keys); not connected |
| P0-E7a | Synthetic-table DDL inside a dedicated test DB | `BLOCKED_BY_EXTERNAL_DEPENDENCY` | even with an approved DB, tranche rules forbid DDL; written authorization must explicitly cover test-only tables |
| P0-E8 | Review confirm/reject hash-chained audit events | `NEEDS_OWNER_DECISION` + `SECURITY_REVIEW_REQUIRED` | unchanged |
| P0-E9 | `resolve_identity` concurrent first-resolve `IntegrityError` | `NEEDS_OWNER_DECISION` | unchanged |
| P0-E10 | `canonical_service.merge_canonicals()` locking/audit/verification | `NEEDS_OWNER_DECISION` | unchanged |
| P0-E11 | Cross-domain reference ownership / repointing / unmerge | `NEEDS_OWNER_DECISION` + `LEGAL_REVIEW_REQUIRED` | unchanged |

Minimal isolated-environment requirements, isolation/disposal method, account permissions, risks
and €0 cost estimate: report §12. **STOP — await explicit owner authorization.**

### Post-evaluation update (2026-11-18) — see `MPI_POSTGRESQL_CONCURRENCY_TEST_REPORT.md`

The isolated test tranche executed: 65/65 pass, `DATABASE_IDENTITY: VERIFIED`, schema
`mpi_concurrency_test`, synthetic data only. Updated item evidence (no approval implied):

| ID | Item | Status after evaluation |
|---|---|---|
| P0-E6 | Serialize concurrent audit appends | `NEEDS_OWNER_DECISION` — evidence complete: sentinel (A) and advisory (B) fork-safe incl. genesis; SERIALIZABLE (C) not guaranteed; atomic SQL (D) does not serialize predecessor selection |
| P0-E7 | Dedicated disposable PostgreSQL test DB | **SATISFIED** — `gula-mpi-pg-test`, DB `mpi_test`, loopback-only, PostgreSQL 16.14, isolation VERIFIED |
| P0-E7a | Synthetic-table DDL inside test DB | **DONE (test-only)** — `mpi_concurrency_test` schema; 0 tables in `public`; no application migration created |
| P0-E10 | `canonical_service.merge_canonicals()` locking/audit | `NEEDS_OWNER_DECISION` — unprotected version increments confirmed in source; no change made |
| P0-E9 / P0-E8 / P0-E11 | unchanged | unchanged |

No source, test, migration or API change; no commit. HOLD `effdfeaf…`, D-020/D-021
`PENDING_APPROVAL`, D-MPI-1 `NEEDS_OWNER_DECISION`. **STOP — await explicit owner authorization.**

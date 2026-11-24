# Dependency Graph — Identity & Platform Remediation

## 1. Phase dependencies

```
PHASE 0 (baseline/governance)  ──►  PHASE 1 (identity privacy + auth P0)
        │                                    │
        │                                    ▼
        └──────────────────────────►  PHASE 2 (MPI merge integrity)
                                             │
                       ┌─────────────────────┼─────────────────────┐
                       ▼                     ▼                     ▼
                  PHASE 3/4             PHASE 5/6/7           PHASE 8
                  NHID/lifecycle        registration/guardian   OCR hardening
                       │                     │                     │
                       └──────────► PHASE 9 (API/integration) ◄──────┘
                                             │
                                      PHASE 10 (validation)
                                             │
                                      PHASE 11 (pilot readiness)
```

A phase begins only when its dependencies and acceptance criteria are satisfied.
This tranche covers Phase 0 and the bounded Phase 1/2 P0 units only.

## 2. P0 unit dependency graph

```
identity.py canonical helper (P0-A1)
   ├──► register.py hashing (P0-A2)
   ├──► identity_persistence_service.py (P0-A3)
   ├──► routes/identity.py POST alternative (P0-A4)
   └──► existing consumers (hash_national_id):
         patient_service.py, mpi/resolver.py, id_scan.py, identity_matching.py
         → automatically inherit canonicalization; legacy-record verification
           requires the candidate-hash compatibility helper

oauth2_provider.py fail-closed JWKS (P0-B1)
   └──► routes/oauth2.py endpoint
         └──► test_auth_infrastructure.py (2 assertions must be updated)

shared/auth/webauthn.py config + serializer (P0-C1)
   └──► mfa_service.py challenge lifecycle (P0-C2)
         └──► mfa routes (existing; no router changes)

session.py security-store policy (P0-D3) — IMPLEMENTED this tranche: raw cache → security_store(), max(cached, db_version), malformed/stale handling, DB-authoritative fallback; user-modified files untouched
   ├──► password_reset.py signature + reset revocation (P0-D1/D2)
   └──► device_service.py (P0-D4) ──► BLOCKED: no device→session/credential edge (NIAM ULID vs numeric LabUser; two disjoint session families)

mpi/resolver.py merge guards + claim repoint (P0-E1)
   ├──► mpi/models.py IdentityClaim (no schema change)
   └──► mpi/api.py caller commits (no change expected)
         └──► unmerge / cross-domain references (P0-E2) ──► BLOCKED
                   only IdentityClaim repointed; ~90 FK/soft refs untouched;
                   no reference-change log / unmerge writer

NHID format inventory (P1-01, this tranche) — 11 competing families
   ├─► canonical NID helper (services/identity.py:214-279) — sole sanctioned input
   ├─► 23 synthetic compatibility tests (test_nhid_readiness.py) — TEST_VERIFIED
   └─► canonical NHID model / migration / ADR revision ──► NEEDS_OWNER_DECISION
```

**Second-tranche dependency notes:**
- P0-D3 depends only on the clean `session.py`; the fail-closed store primitive it
  uses already existed (P0-C2) in `redis_client.py`. User-modified files were read
  only, so no dependency on an unapproved change was introduced.
- P0-D4 and P0-E2 remain blocked by missing identity ownership / historical
  evidence — not by code that this tranche could safely add.
- P1-01 source inventory and compatibility tests are complete; the canonical
  model has external (owner + legal) dependencies and was not implemented.

## 3. Target → test inventory

| Unit | Smallest relevant suite | Related integration suite | Static analysis |
|---|---|---|---|
| P0-A | `backend/tests/unit/test_national_id_canonicalization.py` (new) | `backend/tests/test_auth_infrastructure.py`, `backend/tests/test_niam_v2.py` | Ruff on changed files; MyPy on `services/identity.py` where practical |
| P0-B | new JWKS fail-closed tests | `backend/tests/test_auth_infrastructure.py` | Ruff |
| P0-C | new `test_webauthn_correctness.py` | `backend/tests/test_auth_infrastructure.py` (MFA begin endpoints) | Ruff; MyPy on `shared/auth/webauthn.py` |
| P0-D (incl. D3 this tranche) | `test_session_revocation.py` (22 tests) | `backend/tests/test_security_regression.py`, `test_platform_security_hardening.py`, `test_auth_infrastructure.py` | Ruff (clean) |
| P0-E | new `test_mpi_merge_integrity.py` | `backend/tests/test_citizen_relationship_workflow.py`, `test_security_merge_regression_synthetic.py` | Ruff; MyPy on `services/mpi/resolver.py` |
| P1-01 (NHID, this tranche) | new `test_nhid_readiness.py` (23 tests) | `test_national_id_canonicalization.py`, `test_identity_matching.py` | Ruff (clean) |

All tests use the SQLite in-memory fixture in `backend/tests/conftest.py` and
synthetic objects only. No test connects to PostgreSQL or any operational DB.

## 4. Schema-needs inventory (documentation only — no DDL authorized)

| Need | Source | Decision |
|---|---|---|
| Device→account mapping for session termination | `Device.account_id` is a NIAM ULID; `bump_perm_version` needs a numeric LabUser/User id | `NEEDS_OWNER_DECISION`; P0-D4 documented as blocked |
| MPI unmerge / historical event data | `mpi_merge_audit` records primary/secondary but not a reversible reference-change log | `BLOCKED`; do not claim unmerge |
| Cross-domain patient reference repointing | `national_citizens` FKs in visits/encounters/orders/documents + two patient registries | `BLOCKED`; requires data-ownership decision (ADR-B etc.) |
| F-085 base registration | `DocIntelBase` 21 + `InsBase` 30 classes unregistered | `NEEDS_OWNER_DECISION`; `env.py +49/-0` preserved |
| mfa_device FK extension | `models/mfa_device.py:11-40` only `lab_users` | `NEEDS_OWNER_DECISION` |
| Raw NID cleanup in existing `documents_json` | `identity_persistence_service.py:65-72` | Future migration proposal only; no bulk transformation now |

## 5. External dependencies

| Dependency | Status | Consequence |
|---|---|---|
| Asymmetric signing keys / JWKS material | absent | OIDC stays explicitly unavailable; no keys generated |
| WebAuthn RP ID / allowed origins owner | absent | dev-safe config only; production must be configured explicitly, else fail closed |
| Government civil-registry / ID-verify API | absent + legal agreement required | `BLOCKED_BY_EXTERNAL_DEPENDENCY`; stubs remain stubs |
| NFC interface | absent | assurance `L0`; no NFC-based claim |
| Authorized de-identified Iraqi document samples | absent | OCR benchmarks `BLOCKED`; no invented accuracy numbers |
| Qualified Iraqi legal counsel | absent | all statutory questions `UNVERIFIABLE` |
| Python 3.12 test environment | isolated venv created from pinned lockfile | environment limitation recorded in `ACCEPTANCE_EVIDENCE.md` |

## 6. Rollback model

- No commits are made: every change is an isolated working-tree edit.
- Unit rollback = restore the single file from HEAD (`git checkout -- <file>`),
  which cannot affect the 228 pre-existing entries in other files.
- Tests are new files; removing them restores the prior tree.
- No database state is mutated by this tranche; rollback needs no data operation.
- Any change touching more than one file is split into single-file logical steps
  with verification between steps.

## 7. MPI integrity & concurrency tranche (this session)

```
P0-E3 occurred_at unification ──┐
P0-E4 chain verifier ───────────┼──► new test_mpi_hash_chain_integrity.py (11 tests)
P0-E5 key-ordered citizen locks ┘        └──► 65-test combined MPI regression PASS
        │
        ├──► P0-E6 audit append serialization ──► NEEDS_OWNER_DECISION (NOT implemented)
        │         (sentinel lock / advisory lock / SERIALIZABLE)
        ├──► P0-E7 disposable PG test DB ───────► BLOCKED_BY_EXTERNAL_DEPENDENCY
        │         (SQLite emits no FOR UPDATE; no PG writes performed)
        ├──► P0-E8 review event taxonomy ───────► NEEDS_OWNER_DECISION
        ├──► P0-E9 concurrent resolve claim ─────► NEEDS_OWNER_DECISION
        ├──► P0-E10 canonical_service merge ─────► NEEDS_OWNER_DECISION
        └──► P0-E11 cross-domain references ─────► NEEDS_OWNER_DECISION / LEGAL_REVIEW_REQUIRED
```

- P0-E3/E4/E5 are implemented and tested; P0-E6/7/8/9/10/11 are **not** implemented and
  introduce no new dependency on this tranche.
- The verifier is a detection control; no new API endpoint, table, column or migration was added.
- Test DB remains the SQLite fixture only. No PostgreSQL credential/env var was created.

## 8. MPI PostgreSQL concurrency tranche (this session)

Full report: `MPI_POSTGRESQL_CONCURRENCY_REMEDIATION_REPORT.md`. Discovery only — new dependency
edges recorded, none resolved.

```
DISCOVERY (read-only, no DB connection)
  docker inspect gula-postgres ──► protected gula-platform_default network + pgdata volume
                                   + POSTGRES_* superuser keys
        │
        ├──► strict 7-condition safety gate ──► FAILED (0/7 proven) ──► STOP
        │
        ├──► P0-E7 disposable PG test DB ─────► BLOCKED_BY_EXTERNAL_DEPENDENCY (unchanged)
        │       dedicated network + volume + least-privilege role + MPI_TEST_POSTGRES_URL
        │       + written authorization for synthetic-table DDL (P0-E7a)
        │
        ├──► P0-E6 serialization choice ──────► NEEDS_OWNER_DECISION (unchanged)
        │       sentinel FOR UPDATE (last-row precedent: canonical_audit.py:139)
        │       / pg_advisory_xact_lock / SERIALIZABLE + bounded retry
        │       benchmark ──► BLOCKED (no DB, no numbers fabricated)
        │
        └──► Phases B–I (baseline, fork/deadlock/atomicity proof, performance)
                └──► NOT RUN; no source/test change; no runtime/E2E/production evidence
```

- No new dependency on the protected repository, its network, its `pgdata` volume or any
  operational database was created or used.
- P0-E3/E4/E5 remain implemented from the prior tranche; this tranche added no code edge.
- Gate condition 6 (disposable + authorized) and condition 4 (no real patient data) remain
  unproven; condition 1/3/5/7 are contradicted by Docker metadata.
- Next tranche can start only after D-MPI-2 authorization; see report §12 and §17.

### 8.1 Provisioning update (separate authorization)

`MPI_ISOLATED_POSTGRES_PROVISIONING_REPORT.md`: D-MPI-2 infrastructure **provisioned and
isolation-verified** — `gula-mpi-pg-test` / `gula-mpi-test-network` / `gula-mpi-test-data`,
DB `mpi_test`, non-superuser `mpi_test_user`, PostgreSQL 16.14, loopback-only `127.0.0.1:55432`.

```
P0-E7a dedicated isolated PG environment ──► PROVISIONED / ISOLATION VERIFIED
        │
        ├──► P0-E7b synthetic MPI tables (test-only DDL inside mpi_test)
        │        └──► NOT AUTHORIZED — next-tranche owner decision required
        └──► P0-E6 serialization choice ───► still NEEDS_OWNER_DECISION
```

No code/test/schema edge was added. No concurrency test ran. HOLD unchanged. STOP.

### 8.2 Concurrency evaluation update (separate authorization)

`MPI_POSTGRESQL_CONCURRENCY_TEST_REPORT.md`: D-MPI-2's test tranche executed — 65/65 tests pass
against isolated `mpi_test` schema `mpi_concurrency_test`, synthetic fixtures only.

```
P0-E7a dedicated isolated PG environment ──► PROVISIONED / ISOLATION VERIFIED
        │
        ├──► P0-E7b synthetic MPI tables (test-only DDL inside mpi_test) ──► DONE (isolated schema only)
        ├──► P0-E6 serialization choice ───► EVIDENCE GATHERED (A/B fork-safe incl. genesis;
        │                                    C not guaranteed; D lost-update-only)
        │                                    ──► still NEEDS_OWNER_DECISION
        └──► P0-E10 version-increment hardening ──► NEEDS_OWNER_DECISION (no source change)
```

No code/test/schema edge was added to the repository (harness is out-of-repo). No commit/push.
HOLD unchanged. D-020/D-021 `PENDING_APPROVAL`, D-MPI-1 `NEEDS_OWNER_DECISION`.
**STOP — await explicit owner authorization for implementation.**

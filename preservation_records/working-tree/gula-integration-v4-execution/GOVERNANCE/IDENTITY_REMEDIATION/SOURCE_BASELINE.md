# Source Baseline — Phase 0

All values were read from the live filesystem at the start of this program.
Nothing below is inferred from the historical checkpoint alone.

## 1. Repository identity and Git state

| Check | Observed value |
|---|---|
| Working repository | `/home/samertts/workspace/projects/gula-integration` |
| Branch | `integration/gula-unification-v1` |
| HEAD | `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0` |
| `git status --porcelain=v1` entries | **228** (pre-existing staged renames + modified + untracked) |
| Staged renames | 21 `R ` entries to `archive/legacy/workflow_runtime/` (pre-existing user work; untouched) |
| Modified tracked files | 80+ pre-existing (see final Git report for the exact list) |
| Untracked governance docs | `GOVERNANCE/` tree incl. 22 study documents (pre-existing; untouched) |
| Protected repository | `/home/samertts/workspace/projects/gula-platform`, branch `remediate-security-001`, HEAD `f478676b6fc375338648dde46fbf076c015a3f91`, **clean (0 entries)** |
| `FINAL_DECISION.md` md5 | `effdfeaf10234678d83b2668c4489552` — **HOLD** unchanged |
| D-020 / D-021 | `PENDING_APPROVAL` (unchanged; not touched) |
| `backend/migrations/env.py` | pre-existing authorized delta **+49/-0** (NR-011); not modified |
| `GOVERNANCE/IDENTITY_REMEDIATION/` | did not exist before Phase 0; all files here are new |

No destructive Git operation, commit, push, merge, rebase, PR, migration, DDL
or database connection was performed.

## 2. Documentation baseline (read in full during Phase 0)

22 documents in `GOVERNANCE/IDENTITY_ARCHITECTURE_STUDY/` plus:
`FINAL_DECISION.md`, `GECS/GECS_CHECKPOINT.md`, `GECS/MASTER_CONTROL.md`,
`NATIONAL_HEALTH_PLATFORM_COMPLETION_REPORT.md`, `DATABASE_OWNERSHIP_MATRIX.md`,
`NATIONAL_SERVICE_INVENTORY.md`, `NATIONAL_SERVICE_CONTRACTS.md`,
`ADR_DECISION_REQUEST.md`.

Reconciliation result: no contradiction with the owner's authorization; the
study explicitly disclaims implementation authority and runtime verification.
Where the study and source disagree, **source wins** (example below).

## 3. Revalidated P0 findings (current source authoritative)

| Finding | Source location | Phase-0 verdict |
|---|---|---|
| R-01 raw vs normalized NID HMAC | `backend/app/services/identity.py:213-225`; `backend/app/routes/register.py:335-343`, `:617-628` | **CONFIRMED, and deeper**: `re.sub(r"[^\d]")` preserves Unicode decimal digits in Python, so Arabic-Indic `١٢٣` does not equal Western `123`; `register.py` hashes the raw string with no cleanup at all |
| R-02 raw NID at rest / NID in URL | `backend/app/governance/services/identity_persistence_service.py:65-72`, `:264-267`; `backend/app/routes/identity.py:67` | **CONFIRMED**; unsalted SHA-256 fallback when no HMAC key also confirmed |
| AUTH-OIDC-01 empty JWKS | `backend/app/security/oauth2_provider.py:172-178`; `backend/app/routes/oauth2.py:206-213`; `backend/tests/test_auth_infrastructure.py:213-226` | **CONFIRMED**; discovery advertises `jwks_uri`, endpoint returns `{"keys": []}` with 200; existing tests currently assert the insecure behavior |
| A-WEB-01/02 WebAuthn config & challenge | `shared/auth/webauthn.py:22-24,50,61,86,99` (repo-root `shared/`, **not** `backend/shared/`); `backend/app/security/mfa_service.py:92-106,133-153` | **CONFIRMED**; hardcoded production RP ID/origin, `default=str` bytes serialization, swallowed cache errors → empty challenge, shared challenge key, no single-use consumption |
| A-REC-01 perm-version signature | `backend/app/routes/password_reset.py:90-91` vs `backend/app/security/session.py:40-47` | **CONFIRMED**; arguments transposed; `reset_password` (`:57-77`) has no revocation call at all |
| SEC-04 device revocation | `backend/app/identity/services/device_service.py:79-85`; `backend/app/identity/models/device.py:11-18` | **CONFIRMED flag-only**; `Device` has `account_id` (NIAM ULID), no LabUser/User id → cannot safely map to `perm_version` without an ownership decision |
| MPI-03 merge reference loss | `backend/app/services/mpi/resolver.py:354-400` (comment `:367-369`); `backend/app/services/mpi/models.py:115-147` | **CONFIRMED**; `IdentityClaim.citizen_id` is the only explicitly owned dependent reference in the MPI package and is not repointed; caller commits at `backend/app/services/mpi/api.py:167` |
| F-085 / NR-011 | `backend/migrations/env.py` (`+49/-0`); study §2 | **CONFIRMED open**; not touched |
| Honesty baseline | `NATIONAL_HEALTH_PLATFORM_COMPLETION_REPORT.md:90,156,187` | **CONFIRMED**: 0 E2E/RUNTIME/PRODUCTION; RPO/RTO UNMEASURED |

## 4. Conflict scan of intended target files

Clean (no pre-existing user modification) — safe to modify only with narrow,
isolated edits:

- `backend/app/services/identity.py`
- `backend/app/routes/register.py`
- `backend/app/governance/services/identity_persistence_service.py`
- `backend/app/routes/identity.py`
- `backend/app/security/oauth2_provider.py`
- `backend/app/routes/oauth2.py`
- `shared/auth/webauthn.py`
- `backend/app/routes/password_reset.py`
- `backend/app/security/session.py`
- `backend/app/services/mpi/resolver.py`
- `backend/app/services/mpi/models.py`
- `backend/app/security/mfa_service.py`

**Pre-existing user modifications — DEFERRED, do not overwrite:**

- `backend/app/health_data/mdm/matching.py` (` M`)
- `backend/app/health_data/mdm/service.py` (` M`)
- `backend/app/security/dependencies.py` (` M`) — inspect before any future change
- `backend/migrations/env.py` (` M`, +49/-0) — out of scope entirely
- `backend/tests/test_auth_infrastructure.py` — clean at Phase 0, but any update
  must be limited to the two JWKS assertions with documented rationale

## 5. Test-environment baseline (honest limitations)

- `python3` = 3.10.12, has the deps but **cannot import** `app._compat` (`UTC = UTC` bug).
- `python3.11` = 3.11.0rc1, has the deps but **cannot parse** PEP 695 generic syntax
  (`class IdentityRepositoryBase[T: …]`) used by the current source.
- `python3.12` = 3.12.13, correct target but initially had no test dependencies;
  an isolated venv at `/tmp/opencode/gula-py312` was created from the repo's
  pinned `backend/requirements-lock.txt` (environment-only; no project file changed).
- Baseline `pytest backend/tests/test_auth_infrastructure.py` on 3.11 collected
  30 tests and produced 30 setup errors from the 3.12-only syntax — **not a code
  failure, an interpreter mismatch**. Actual pass/fail is recorded in
  `ACCEPTANCE_EVIDENCE.md` once the 3.12 venv is ready.
- No database URL other than SQLite `:memory:` used by `conftest.py`; no
  operational/production database accessed.

## 6. Evidence conventions

- `SOURCE_PRESENT` / `CONFIRMED` = static source inspection only.
- `TEST_VERIFIED` in the study = test file exists; **not** executed there.
- In this program, a test is called passing only after a real command was run
  and its exact exit code/counts recorded.
- No E2E, runtime, production, RPO or RTO claim is made.

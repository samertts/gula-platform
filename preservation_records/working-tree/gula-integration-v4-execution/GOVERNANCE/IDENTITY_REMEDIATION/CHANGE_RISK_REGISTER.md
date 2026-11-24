# Change Risk Register — Identity & Platform Remediation

Risk scoring is qualitative (Low / Medium / High) and reflects engineering
judgement, not measured probability. No risk is "accepted" by silence; each has
a named mitigation and rollback.

| ID | Change | Risk | Failure mode | Mitigation | Rollback | Approval |
|---|---|---|---|---|---|---|
| R-A1 | Change `hash_national_id()` normalization | **High** — existing hashes with Arabic-Indic digits become unmatchable | Silent identity duplication / lost linkage | Add `nid_hash_candidates()` legacy compatibility for verification; new writes canonical only; no bulk rewrite; tests for equivalent representations | single file | `OWNER_APPROVED`; security review for certification |
| R-A2 | Register.py raw→canonical HMAC | Medium — legacy duplicate records may not be detected | Duplicate accounts | Check both canonical and legacy candidate hashes on duplicate lookup | single file | `OWNER_APPROVED` |
| R-A3 | Remove raw NID from `documents_json` | Medium — consumers expecting the raw field | Read-path regression | Replace with hashed reference key; keep document metadata; no deletion of records; inspect all readers before edit | single file | `OWNER_APPROVED` |
| R-A4 | POST NID lookup alternative | Low/Medium — client contract drift | Existing GET callers break | Keep GET as deprecated legacy path; do not delete; document future removal decision | single file | `OWNER_APPROVED`; GET removal `NEEDS_OWNER_DECISION` |
| R-B1 | JWKS fail-closed | Medium — OIDC client expecting 200 with empty keys | Client integration failure | No working client could validate tokens from an empty set; update two assertions with rationale; no key generation | 3 single-file reverts | `OWNER_APPROVED`; OIDC readiness `SECURITY_REVIEW_REQUIRED` |
| R-C1 | WebAuthn config + serializer | **High** — challenge encoding mismatch could lock out authenticators | Registration/authentication failures | Encode bytes as base64url in options; decode back to bytes on verification; test round-trip; dev-safe defaults; explicit production config required | single file | `OWNER_APPROVED`; passkey activation `SECURITY_REVIEW_REQUIRED` |
| R-C2 | Single-use / expired challenge | Medium — race or over-strict replay rule | Legitimate retry rejected / replay accepted | Atomic one-time claim via `set_if_absent` marker with TTL; separate registration/auth namespaces; fail closed on missing challenge | single file | `OWNER_APPROVED` |
| R-D1/D2 | Fix `bump_perm_version` call + reset revocation | Medium — mobile `/auth/change-password` may shadow this route (study AUTH-07) | Broken endpoint still unreachable | Fix signature; add revocation; do not change router ordering; document shadowing as separate item | single file | `OWNER_APPROVED` |
| R-D3 | `security_store` in perm-version path (**IMPLEMENTED this tranche**) | Medium — production outage if store down | Session rejection / reliance on DB when store unavailable | Converted raw cache → `security_store()`; `max(cached, db_version)` makes stale/malformed/proc-local values harmless; DB (primary) authoritative; CRITICAL logs; dev/test fallback preserved. Strict 503-on-outage policy NOT silently imposed (needs `dependencies.py`, a user-modified file) — `NEEDS_OWNER_DECISION`. No HA/failover claim | single-file revert (`session.py`) | `OWNER_APPROVED`; policy `SECURITY_REVIEW_REQUIRED` / `NEEDS_OWNER_DECISION` |
| R-D4 | Device revocation | **High** — cannot map NIAM device to numeric account id | Partial fix misrepresented as complete | **Do not implement** session termination; document blocker and owner decision | n/a | `NEEDS_OWNER_DECISION` |
| R-E1 | MPI claim repointing | **High** — wrong repoint could corrupt patient identity | Lost clinical history / duplicate claims | Restrict to explicitly owned `IdentityClaim` rows; row locks; self/cycle checks; idempotency; post-merge consistency assertion raising before commit; full rollback on error; synthetic tests | single file | `OWNER_APPROVED` (bounded); full merge `BLOCKED` |
| R-E2 | Unmerge / cross-domain refs | **High** — irreversible reference loss | Patient-record corruption | **Do not implement**; document as blocked pending schema + event history | n/a | `BLOCKED_BY_EXTERNAL_DEPENDENCY` |
| R-G1 | User work preservation | **High** — 228 pre-existing entries could be overwritten | Loss of user changes | Conflict scan in `SOURCE_BASELINE.md`; only clean files touched; never `git add -A`/checkout of user files | n/a | mandatory |
| R-G2 | Protected repo | **High** — accidental edit to `gula-platform` | Boundary violation | All shell workdir pinned to `gula-integration`; final md5/HEAD/status verification | n/a | mandatory |
| R-G3 | Test-environment mismatch | Medium — tests run on wrong interpreter give false results | False pass/fail | Use Python 3.12 venv from pinned lockfile; record exact interpreter and command | n/a | mandatory |
| R-G4 | Overstated readiness | **High** — unit tests misread as production proof | False assurance | Keep HOLD, 0 E2E/runtime/production, RPO/RTO unmeasured in every report | n/a | mandatory |
| R-D5 | Session.py fail-closed change (**this tranche**) | Medium — over-strict read could reject legitimate sessions | Auth failures in prod store outage | DB (primary) is authoritative and read fresh per request; `max()` cannot reject a current token; outage falls back to DB, not to a permissive accept; CRITICAL logging; 22 synthetic tests | single file | `OWNER_APPROVED` (bounded) |
| R-D6 | Device revocation left unimplemented | **High** — false claim of device→session termination | Stale sessions after "revoke" | No code written; source evidence + proposed ownership/migration model documented; owner/security decisions required | n/a | `NEEDS_OWNER_DECISION` / `SECURITY_REVIEW_REQUIRED` |
| R-E3 | MPI unmerge / cross-domain refs left unimplemented | **High** — irreversible reference loss | Patient-record corruption | No code written; ~90-reference inventory + blockers documented; correctness concerns (hash-chain verification, lock ordering, audit) recorded for a bounded future tranche | n/a | `BLOCKED_BY_EXTERNAL_DEPENDENCY` / `NEEDS_OWNER_DECISION` |
| R-D7 | NHID inventory + compatibility tests (no model change) | Medium — characterization tests could be read as endorsement | False confidence in legacy HID | Tests explicitly labelled `KNOWN_RISK`/characterization with rationale; no identifier changed; canonical model/migration left as `NEEDS_OWNER_DECISION` | n/a (tests only) | `OWNER_APPROVED` for inventory/tests; model `NEEDS_OWNER_DECISION` |

## Acceptance gates before any P0 unit is called complete

1. Smallest relevant test suite passes with exact command/exit/counts recorded.
2. Related integration suite passes or any pre-existing failure is explicitly attributed.
3. Ruff clean on changed files; MyPy attempted and limitations recorded.
4. Regression test exists for each fixed defect.
5. `git diff` inspected; only authorized clean files changed.
6. HOLD md5, D-020/D-021, protected repo, `env.py +49/-0`, GECS evidence re-verified.
7. No secret, patient data, migration, DDL, router activation or production claim introduced.

## MPI integrity & concurrency tranche risks (this session)

| ID | Change / gap | Risk | Failure mode | Mitigation | Rollback | Approval |
|---|---|---|---|---|---|---|
| R-E4 | Unified `occurred_at` in hash + column | **High** — a hash-format change could invalidate previously written entries | old audit rows unverifiable by new verifier | No hash algorithm/field change; only the timestamp source is unified; new rows reproducible; legacy rows already unverifiable before this change | single isolated edit in pre-modified file | `OWNER_APPROVED` (bounded) |
| R-E5 | `verify_merge_audit_chain()` | Medium — verifier could be read as a prevention guarantee | false assurance | Docstring/report explicitly scope it to detection; no privileged-rewrite claim; no endpoint added | remove the new function | `OWNER_APPROVED` (bounded) |
| R-E6 | Key-ordered citizen locks | Medium — changes lock acquisition semantics | new contention pattern | Single statement, sorted by immutable PK; no lock held longer; source + behaviour tests; no PG runtime proof claimed | revert the single edit | `OWNER_APPROVED` (bounded) |
| R-E7 | Audit-append fork left open | **High** — non-linear ledger under concurrency | two rows share `prev_hash` | verifier detects forks; owner decision required for the serialization mechanism; no partial fix claimed | n/a (not implemented) | `NEEDS_OWNER_DECISION` |
| R-E8 | No PG concurrency test DB | **High** — lock behaviour unproven at runtime | deadlock/race undetected | no PG writes; SQLite limits documented; dedicated DB requested | n/a | `BLOCKED_BY_EXTERNAL_DEPENDENCY` |
| R-E9 | User-modified `resolver.py` edited | **High** — pre-existing work could be lost | overwrite of P0-E tranche | minimal targeted edits only; full diff reviewed; no rewrite/format; 65 tests pass | revert only this tranche's hunks | mandatory |

## MPI PostgreSQL concurrency tranche risks (this session)

Full report: `MPI_POSTGRESQL_CONCURRENCY_REMEDIATION_REPORT.md` §16. No change was implemented;
risks below are discovered/left-open, not introduced.

| ID | Change / gap | Risk | Failure mode | Mitigation | Rollback | Approval |
|---|---|---|---|---|---|---|
| R-PG-1 | Audit fork under concurrent appends | **High** — non-linear ledger | two rows share `prev_hash` (`resolver.py:110-115` unlocked predecessor read) | verifier detects; no prevention implemented; source comparison of 3 options recorded | n/a (not implemented) | `NEEDS_OWNER_DECISION` |
| R-PG-2 | No isolated PG test DB | **High** — lock/race behaviour unproven | deadlock/race undetected | STOP before connection; no numbers fabricated; dedicated DB requested | n/a | `BLOCKED_BY_EXTERNAL_DEPENDENCY` |
| R-PG-3 | Using reachable `gula-postgres` | **Critical** — protected operational DB access | patient-data exposure or accidental writes | **STOP** — metadata proves platform app DB; never connect; no candidate probed | n/a | mandatory prohibition |
| R-PG-4 | Genesis case for last-row sentinel | Medium — empty chain has no row to lock | fork on first two appends | owner decision: dedicated sentinel row (**schema change → STOP**) vs advisory lock | n/a | `NEEDS_OWNER_DECISION` |
| R-PG-5 | Session-scoped advisory lock | Medium — leak across pooled connections | lock held after return to pool | transaction-scoped lock only if chosen; pool lifecycle review | n/a | `SECURITY_REVIEW_REQUIRED` |
| R-PG-6 | SERIALIZABLE retry | Medium — unbounded retries / reuse of failed transaction | throughput collapse or invalid commit | bounded, idempotent retries on 40001/40P01 only; fresh transaction | n/a | `SECURITY_REVIEW_REQUIRED` |
| R-PG-7 | `secondary.version += 1` (`resolver.py:515`) | **High** — lost version update | stale counter reduces invalidation level | atomic increment / version guard requires owner decision | n/a | `NEEDS_OWNER_DECISION` |
| R-PG-8 | Synthetic-table DDL inside dedicated test DB | Medium — tranche DDL prohibition | unauthorized schema change | explicit written authorization needed even for test-only tables | n/a | `BLOCKED_BY_EXTERNAL_DEPENDENCY` |
| R-PG-9 | DBA rewriting whole hash chain | Medium — false assurance if claimed | undetectable full rewrite | documented non-claim: hash chain is not a DBA defence | n/a | accepted |

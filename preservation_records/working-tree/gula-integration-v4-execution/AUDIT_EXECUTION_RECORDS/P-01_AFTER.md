# P-01 / AUD-F01 — AFTER record (dormant raw audit writer redirected)

**Generated:** 2026-11-20 UTC · **Repo:** `gula-integration`, branch `integration/gula-unification-v1`
**HEAD:** `2206654dc713ea2de8c564a3207dfe05fde23549` (unchanged — no commit)
**Posture:** HOLD · Stable v1.0.0 NOT declared · PRODUCTION READY NOT authorized · `production_ready_items = 0`.
**Data:** synthetic only, disposable SQLite test DB; no PHI, secrets, production DB or anchor.

## 1. Implementation

| File | Change |
|---|---|
| `shared/audit/service.py` | `create_audit_entry` and `AuditService.log` now delegate to canonical `log_action`; `query_audit_log` and `AuditService.query` read canonical columns only. Internal `commit()` and raw `INSERT INTO audit_logs` removed. `compute_chain_hash` retained (deprecated) for the separate P-04 tooling package, but no writer calls it. Added `_coerce_resource_id`, `_legacy_entity_id`, `_iso`, `_canonical_audit_service`. Review follow-up: unique hex correlation token pins the inserted row under concurrency; LIKE wildcards in string identifiers are escaped; import resolution is deterministic on the `app` namespace. |
| `backend/tests/test_f01_legacy_audit_writer.py` | NEW — 7 synthetic regression tests. |
| `AUDIT_EXECUTION_RECORDS/P-01_BEFORE.md` | NEW — defect evidence and redirect strategy. |

**Constitution compliance:** the dormant `EnterpriseAudit` / `SharedAuditService` modules are
**preserved and redirected**, not removed. No schema, migration, active route, canonical audit
behavior or staged `R100` rename changed.

Mapping decisions:
- `entity_type` → canonical `resource_type` (verbatim).
- integer / numeric-string `entity_id` → canonical `resource_id`; non-numeric identifiers are kept
  verbatim in `details.legacy_entity_id` and `details.legacy_entity_type`, and reconstructed on read.
- `previous_hash` is read immediately before the canonical write and returned to legacy callers;
  it is not persisted as a row (the canonical schema has no such column).
- Caller owns the transaction: no writer commits internally.

`_canonical_audit_service()` resolves `app.services.audit_service` or
`backend.app.services.audit_service` to whichever namespace is already loaded, preventing
duplicate SQLAlchemy mapper registries.

## 2. Verification

Environment: Python 3.12.13 (`/tmp/opencode/gula-int-py312/bin/python`), pytest 9.1.1,
`ENV=test PYTHONPATH=..:/home/samertts/workspace/projects/gula-integration`.

| Phase | Command | Result | Exit |
|---|---|---|---:|
| RED (before fix) | `pytest tests/test_f01_legacy_audit_writer.py -q` | **7 failed** — SQLite `near "FOR"`, raw INSERT into non-existent columns, static guards | 1 |
| GREEN (initial fix) | same | **7 passed**, 1 warning, 184.14 s | 0 |
| GREEN (post-review, 2 added tests) | same | **9 passed**, 1 warning, 82.31 s | 0 |
| Related suites | 11 audit / control-plane / P-13 / P-15 modules | **120 passed, 9 skipped**, 11 warnings, 114.19 s (re-run after review fixes) | 0 |
| Ruff | `ruff check shared/audit/service.py backend/tests/test_f01_legacy_audit_writer.py` | All checks passed | 0 |
| `git diff --check` | repo root | clean | 0 |

Related suites executed: `test_audit_chain_integrity`, `test_audit_chain_isolation_guard`,
`test_audit_positional_regression`, `test_audit_bypass_regression`, `test_audit_anchor`,
`test_compliance_integrity`, `test_control_plane_authorization`,
`test_governance_audit_authorization`, `test_mpi_audit0416_integrity`,
`test_p13_financial_audit_integrity`, `test_p15_password_reset_audit_integrity`.

## 3. Test coverage map

| Test | Pins |
|---|---|
| `test_f01_legacy_writer_creates_canonical_chained_row` | canonical columns, non-null chain hash, canonical verifier accepts the row, legacy response shape |
| `test_f01_legacy_writer_does_not_commit_callers_transaction` | no internal commit |
| `test_f01_legacy_query_reads_canonical_schema` | reads target canonical columns and map back |
| `test_f01_non_integer_entity_id_is_preserved_in_details` | string identifiers survive |
| `test_f01_enterprise_audit_and_service_delegate_to_canonical_writer` | both dormant facades reach the canonical chain |
| `test_f01_source_has_no_raw_insert_no_internal_commit` | static AST guard |
| `test_f01_legacy_hash_is_no_longer_used_by_any_writer` | no writer calls the divergent hash |
| `test_f01_concurrent_writer_cannot_hijack_legacy_response` | deterministic racing-writer simulation: returned id/hash identify our row, not a lower-id competing row |
| `test_f01_non_numeric_entity_id_filter_escapes_like_wildcards` | `%`/`_` escaped; a literal `"a%"` filter cannot match `"abc"` |

## 4. Independent review

**Verdict: PASS WITH CONDITIONS. CRITICAL: 0. HIGH: 0.** Fresh-context, read-only reviewer
(no repository modification). Reproduced focused 7/7 and related 65 passed / 9 skipped, exit 0;
confirmed the HEAD defect from `git show HEAD:shared/audit/service.py` and the non-vacuity of the
AST guards. Confirmed canonical delegation, no raw INSERT, no internal commit, correct identifier
mapping, dormant-module preservation, and no scope/invariant violation.

| ID | Sev | Condition | Resolution | Evidence |
|---|---|---|---|---|
| 1 | MED | Concurrent writers could return another writer's row (`id > max_before … ASC LIMIT 1`) | Replaced with a unique hex `legacy_write_token` in `details` and an exact JSON-text LIKE lookup (hex has no wildcard characters). | `test_f01_concurrent_writer_cannot_hijack_legacy_response` |
| 2 | LOW | `%`/`_` in a non-numeric `entity_id` acted as LIKE wildcards | Escape `\`, `%`, `_` in the bound value and use `LIKE … ESCAPE '\'`; no injection (value is bound). | `test_f01_non_numeric_entity_id_filter_escapes_like_wildcards` |
| 3 | LOW | `backend.app…` fallback could not import the canonical module in a pure namespace | Removed the fresh `backend.app` import attempt; reuse either namespace only if already loaded, otherwise import `app.services.audit_service` deterministically. Documented that `previous_hash` is advisory-only. | code + docstring |
| 4 | INFO | AFTER record not updated | This section. | — |

**Residual (disclosed, not self-accepted):** `previous_hash` is advisory-only — read before the
canonical serialization lock and not persisted by the canonical schema. `query_audit_log` returns
`None` for that legacy field. No integrity impact; canonical chain remains authoritative.

Status: `TESTED` + `INDEPENDENTLY REVIEWED` (conditions cleared). NOT `ACCEPTED`,
NOT `PRODUCTION READY`. No commit, staging change, merge, deploy or production access.

# Command Center — Concurrency Audit

**LIVE status**: table-backed (`cc_*`, 4 tables per the live-surface map), router mounted unconditionally at `/command-center` (`system:admin`-gated), zero pre-existing tests.

**Mutation count**: 6 mutating service methods (`declare_emergency`, `resolve_emergency`, `request_resource`, `fulfill_resource`, `publish_situation_report`, `complete_after_action`). 4 are INSERT-only (no CAS need). 2 are read-modify-write on an existing row: `resolve_emergency`, `fulfill_resource`.

## P0/P1 finding — FIXED

`resolve_emergency` and `fulfill_resource` read `EmergencyDeclarationModel`/`ResourceRequestModel` with a plain unlocked `SELECT`, despite both models inheriting `OptimisticLockMixin` (unused `version` column). Neither had a terminal-state guard.

**Real PostgreSQL 16 proof**: two concurrent `resolve_emergency` calls on the same emergency both succeeded pre-fix — the situation summary shows **both** actors' `[RESOLVED]` notes appended, `version` never incremented. Post-fix: one succeeds, one gets a clean `EmergencyAlreadyResolvedError` (409), byte-identical restore verified in between.

**Fix**: `.with_for_update()` + `version += 1` on both methods; new `EmergencyAlreadyResolvedError`/`ResourceRequestAlreadyFulfilledError` (409, not the existing 404 not-found errors) guard the terminal states (`resolved` / `fulfilled`).

**Regression**: `tests/test_command_center_emergency_cas.py` (4 new tests, command_center had zero prior coverage) — negative-proofed (collection fails against pre-fix code, since the new exception classes don't exist yet).

## Tenant scope

All queries and mutations filter (or scope) correctly by the router's `system:admin` gate — same SYSTEM_CONTROLLED shape as the pre-existing `tenant-scope-sweep` disposition for this domain family; no new BOLA found.

## Authorization

No gap — router-level gate is uniform and already correct.

## Disposition

**VERIFIED CLOSED** (real-Postgres-proven, negative-proofed, zero regressions).

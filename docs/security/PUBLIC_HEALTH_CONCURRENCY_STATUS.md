# Public Health — Concurrency Audit

**LIVE status**: table-backed (`ph_*`, 6 tables per the live-surface map), router mounted unconditionally at `/public-health` (`system:admin`-gated), zero pre-existing tests.

**Mutation count**: 6 mutating service methods (`report_case`, `raise_alert`, `update_alert_status`, `record_signal`, `record_vaccination`, `publish_report`). 5 are INSERT-only. `update_alert_status` is the one read-modify-write mutation on an existing row.

## P0/P1 finding — FIXED

`update_alert_status` had three independent gaps: (1) no concurrency guard despite `OutbreakAlertModel` inheriting `OptimisticLockMixin` (unused `version`); (2) no validation that the client-supplied `status` string is a real `OutbreakStatus` enum member — any string was accepted and persisted; (3) no terminal-state protection — `OutbreakStatus.DECLARED_OVER` is the outbreak's real terminal state (the model has a one-way `declared_over_at` timestamp), yet a declared-over outbreak could be silently reopened or re-"declared over" again.

Not invented: the fix does not impose a full legal-transition graph across `monitoring → investigating → confirmed → contained` (no evidence in this codebase constrains those transitions today) — only the two provable gaps (enum validity, terminal-state re-entry) were closed, consistent with this session's own precedent of not inventing business rules beyond what's evidenced (`imaging-slice-order-transition-graph`).

**Real PostgreSQL 16 proof**: two concurrent `update_alert_status(..., "declared_over")` calls on the same outbreak alert both succeeded pre-fix — `investigation_notes` shows **both** actors' notes appended, `version` never incremented. Post-fix: one succeeds, one gets a clean `OutbreakAlreadyDeclaredOverError` (409), byte-identical restore verified in between.

**Fix**: `OutbreakStatus(status)` enum-membership validation (raises `InvalidOutbreakStatusError`, 400) + `.with_for_update()` + `version += 1` + terminal-state guard (`OutbreakAlreadyDeclaredOverError`, 409, distinct from the existing 404 not-found error).

**Regression**: `tests/test_public_health_outbreak_cas.py` (4 new tests, public_health had zero prior coverage) — negative-proofed.

## Tenant scope / Authorization

Same `system:admin` router gate as command_center/biomedical; no new BOLA found — consistent with the pre-existing `tenant-scope-sweep` disposition for this domain family.

## Disposition

**VERIFIED CLOSED** (real-Postgres-proven, negative-proofed, zero regressions).

## Surveillance-integrity note

The directive's concern that "incorrect duplicate or lost state can affect surveillance integrity" is exactly what this race demonstrated: a duplicated `[RESOLVED]`-style note is a corrupted audit trail on a real outbreak record, not a cosmetic issue — this is the actual justification for treating it as P1 rather than a lower-priority polish item.

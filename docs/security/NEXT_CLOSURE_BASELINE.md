# Next Closure Directive — Phase 0 Baseline

## Raw baseline

```
HEAD:      3c04462acc1bc39ebf09697fab37869add725d83
Branch:    claude/mustafa-parallel-engineering
Migration: single head, 20260908_0005
Git status: clean
Focused regression tier (identity + migrations + payments + device
outbox + biomedical + command_center + public_health):
  320 passed, 4 skipped, zero failures
```

## Classification of everything already known, per this directive's required lifecycle

No silent UNKNOWN. Every row below is either carried forward from an
existing document (cited) or newly classified this pass.

| Area | Status | Evidence |
|---|---|---|
| NIAM sync/async lifecycle (135 defects) | **VERIFIED** | `docs/security/NIAM_SYNC_ASYNC_CLOSURE_FINAL_REPORT.md` |
| Platform Authority authorization path | **PARTIALLY VERIFIED** | Governance batches 7a/7b/7c hardened `app/identity/governance/`; no repo-wide Authorization Expansion registry built yet |
| Payments capture/refund CAS | **VERIFIED** | `docs/security/PAYMENTS_CAPTURE_REFUND_CAS_STATUS.md` |
| Devices outbox CAS | **VERIFIED** | `docs/security/DEVICES_OUTBOX_CAS_STATUS.md` |
| Biomedical work-order/device CAS | **VERIFIED** | `docs/security/BIOMEDICAL_WORK_ORDER_CAS_STATUS.md` |
| Command Center emergency/resource CAS | **VERIFIED** | `docs/security/COMMAND_CENTER_CONCURRENCY_STATUS.md` |
| Public Health outbreak-alert CAS | **VERIFIED** | `docs/security/PUBLIC_HEALTH_CONCURRENCY_STATUS.md` |
| Blood Bank concurrency | **VERIFIED** | Re-ran `tests/blood_bank/` (7 files) against a genuinely head-migrated disposable Postgres 16 DB — 32/32 passed |
| Critical Care concurrency | **PARTIALLY VERIFIED** | Route-to-service call audit confirmed all live mutation paths use the `_safely` hardened variants and legacy unsafe twins are unreached; not independently re-run against real Postgres the way Blood Bank was (no dedicated test suite exists for it) |
| Systemic concurrency pattern (unused version + no terminal guard) | **VERIFIED**, 3 instances closed | `docs/security/SYSTEMIC_CONCURRENCY_PATTERN_REGISTER.md` |
| Outbox implementation inventory (3 found) | **VERIFIED** | `docs/security/SYSTEMIC_CONCURRENCY_FINDINGS.md` |
| Live-runtime surface map (88 routers) | **PARTIALLY VERIFIED** | `docs/architecture/LIVE_RUNTIME_SURFACE_MAP.md` — corrected this pass, see below |
| Governance schema gap (58/64 missing) | **BLOCKED** | Human-approved migration + domain-owner scoping required |
| National schema gap (103/114 missing) | **BLOCKED** | Same |
| CI (GitHub Actions) | **BLOCKED / UNKNOWN** (external, not code) | `runner_id=0`, ~0ms execution, no runner dispatch — reproduced identically on every commit this session, most recently `3c04462a`; documented once, not re-litigated per this session's own standing rule |
| Authorization Expansion (full repo-wide capability inventory) | **NOT STARTED** | No route/method/capability/scope machine-readable inventory exists yet |
| Idempotency closure (repo-wide) | **PARTIALLY VERIFIED this pass** | See `docs/security/IDEMPOTENCY_CLOSURE_STATUS.md` — new this pass |
| Transaction integrity (repo-wide) | **NOT STARTED** | No dedicated trace-every-mutation pass has been done; only incidentally verified for the 6 CAS fixes already closed (each individually proved commit/rollback correctness as part of its own proof) |
| Certificates/Trust/Federation final sweep | **NOT STARTED this pass** | Prior session findings on certificate authorization gaps (`rotate_certificate`, `register_ca`, `generate_crl`, `generate_api_key`, `revoke_api_key`, `rotate_api_key`) are referenced in the repair queue but not re-verified this pass |
| AI/Clinical safety re-check | **NOT STARTED this pass** | No new AI-path audit performed |
| Production Readiness matrix rebuild | **NOT STARTED this pass** | `docs/architecture/PRODUCTION_READINESS_DELTA.md` already exists from a prior pass; not updated this pass since no new evidence changes its categories beyond what the repair queue already tracks |

## What this baseline does NOT claim

This directive's 14 phases are, collectively, a multi-week program against
an already-large, previously-audited monorepo. This baseline does not
claim any phase beyond Phase 0 and the bounded Phase-2 idempotency
investigation below is complete. Every phase not explicitly marked
VERIFIED/PARTIALLY VERIFIED above is NOT STARTED, recorded honestly per
this directive's own Section on forbidden claims ("all secure",
"production ready" etc. are not being asserted anywhere in this pass).

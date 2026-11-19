# Failure Mode Catalog

**Generated:** 2026-09-25 · **Head:** `d8c2a31b`

A shared vocabulary so two tests in two domains mean the same thing by
"concurrent". Coverage is what has been executed against real PostgreSQL, not
what a test is named after.

`Mechanism` names the thing that would exercise the mode. Where none exists, the
mode is `NO MECHANISM` and no claim about it may be made in any report.

| ID     | Failure mode                                             | Mechanism                                                                                     | Coverage                                                                                                            |
| ------ | -------------------------------------------------------- | --------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| FM-001 | Duplicate request, same idempotency key                  | Second HTTP POST with the same key                                                            | **blood_bank** VERIFIED · **critical_care** verified under repair · 6 guarded domains untested                      |
| FM-002 | Concurrent request, two actors, one row                  | `harness.race` — two connections, barrier-released                                            | **blood_bank** VERIFIED · **critical_care** verified under repair · rest untested                                   |
| FM-003 | Stale version (`If-Match` mismatch)                      | Header with an old version                                                                    | **critical_care** verified under repair (409) · rest untested                                                       |
| FM-004 | Unauthorized actor                                       | Authenticated caller whose role lacks the capability                                          | **critical_care** VERIFIED (403, 5 roles)                                                                           |
| FM-005 | Cross-tenant actor                                       | Actor whose `lab_id` differs from the row's                                                   | **critical_care** verified under repair (404) · **blood_bank** VERIFIED                                             |
| FM-006 | Expired session                                          | —                                                                                             | **NO MECHANISM** in the verification layer                                                                          |
| FM-007 | Revoked authority mid-flight                             | `perm_version` bump / `blacklist:jti`                                                         | **NO MECHANISM** here; Redis-backed, untested under failure                                                         |
| FM-008 | Transaction rollback before commit                       | `failure_injection` stages `after_claim`, `after_business_effect`, `after_inventory_movement` | **blood_bank** VERIFIED · elsewhere no call sites                                                                   |
| FM-009 | Failure after commit, before response                    | `failure_injection` stage `after_commit`                                                      | **blood_bank** VERIFIED · elsewhere no call sites                                                                   |
| FM-010 | Database disconnect                                      | —                                                                                             | **NO MECHANISM**. The app has a circuit breaker and degraded mode; neither is exercised by a verification scenario. |
| FM-011 | Service restart                                          | —                                                                                             | **NO MECHANISM**                                                                                                    |
| FM-012 | Dependency timeout                                       | —                                                                                             | **NO MECHANISM**                                                                                                    |
| FM-013 | Dependency 500                                           | —                                                                                             | **NO MECHANISM**                                                                                                    |
| FM-014 | Duplicate state transition                               | Second attempt at an already-made transition                                                  | **critical_care** verified under repair · **biomedical**, **command_center** VERIFIED                               |
| FM-015 | Terminal-state mutation                                  | Attempt against a closed/resolved/completed row                                               | **biomedical**, **command_center** VERIFIED (NR-016, NR-021)                                                        |
| FM-016 | Missing audit                                            | Count audit rows around an operation                                                          | **critical_care** DEFECT FOUND (NR-024)                                                                             |
| FM-017 | Wrong tenant filter                                      | Static scan plus a cross-tenant request                                                       | **blood_bank**, **biomedical**, **command_center** VERIFIED; ~21 NR-017 candidates untraced                         |
| FM-018 | Missing idempotency boundary                             | Absent `Idempotency-Key`                                                                      | **critical_care** verified under repair (400)                                                                       |
| FM-019 | Schema mismatch (ORM writes a column the database lacks) | `harness.drift_report`                                                                        | **VERIFIED DEFECT** — 84 tables, 692 columns, platform-wide                                                         |
| FM-020 | Migration mismatch / unreachable revision                | `alembic upgrade head` on an empty database                                                   | **VERIFIED DEFECT** — stops at `20260505_0005`                                                                      |
| FM-021 | Partial write                                            | Read committed state after a failure                                                          | **critical_care** VERIFIED (no partial effect) · **blood_bank** VERIFIED                                            |
| FM-022 | Retry storm                                              | —                                                                                             | **NO MECHANISM**                                                                                                    |
| FM-023 | Stale cache                                              | —                                                                                             | **NO MECHANISM**                                                                                                    |
| FM-024 | Duplicate event                                          | Outbox tests exist; not under failure injection                                               | **PARTIAL**                                                                                                         |
| FM-025 | Out-of-order event                                       | —                                                                                             | **NO MECHANISM**                                                                                                    |

## Added by this pass

Two modes were added because the repository produced evidence for them, not
because the list looked short.

| ID     | Failure mode                                                  | Why it earned an entry                                                                                                                                                                                                                                                                                                                             |
| ------ | ------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| FM-026 | **An earlier error masks every downstream control**           | Proven: one absent column turned a cross-tenant attempt into 500 instead of 404, a stale `If-Match` into 500 instead of 409, and an absent key into 500 instead of 400. Each of those controls is present and correct in the source, and none of them could be reached. A report that read the source would have marked four invariants satisfied. |
| FM-027 | **The failure path depends on the same resource that failed** | Proven: the route's `except` branch calls `guard.reject`, which writes to the database that just refused the statement, so the rejection is lost too. A control whose error handling shares a dependency with the thing it guards is not a control at the moment it is needed most.                                                                |

## Coverage summary

- 27 modes catalogued.
- **11 have executed evidence in at least one domain.**
- **9 have no mechanism at all** in the verification layer (FM-006, 010, 011, 012, 013, 022, 023, 025, and FM-007 in this layer).
- 2 were discovered by this pass.

No claim of resilience against FM-010 through FM-013 or FM-022 through FM-025
may be made from this repository's current evidence.

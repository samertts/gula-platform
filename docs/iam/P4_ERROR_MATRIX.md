# P4 Error and Denial Matrix

**Rule:** A status is `OBSERVED` only when a test or source assertion demonstrates it. `MAPPED` means frontend/server mapping exists but full end-to-end evidence is not complete. `REQUIRED` means a reproducible test or runtime verification is still needed.

| Status or failure | Backend evidence | Frontend evidence | Leakage control | Current state | Next safe action |
|---|---|---|---|---|---|
| 401 Unauthorized | Security and workspace hardening tests assert unauthorized behavior | `workspaceScopedReads` maps 401 to `missing_workspace` | Safe blocked message; no sensitive response expected | OBSERVED/PARTIAL | Add route-level matrix coverage for all protected P4 routes |
| 403 Forbidden | Authorization/security tests assert privilege and scope denials; workspace switch denial is audited | `workspaceScopedReads` maps 403 to `permission_denied` | No legacy fallback; blocked state | OBSERVED/PARTIAL | Add cross-org/facility/workspace route matrix |
| 404 Not Found | Some route tests cover missing resources | Generic frontend transport mapping exists for >=400 | Must not enumerate sensitive resources | PARTIAL | Complete resource-enumeration checks |
| 409 Conflict | Account Request/idempotency and state-machine surfaces exist; full matrix not complete | Generic safe transport mapping | No duplicate side effect and no sensitive conflict disclosure | PARTIAL | Add replay/concurrency assertions for all relevant transitions |
| 422 Validation | Security regression tests assert malformed validation inputs | Generic safe mapping | Validation messages must not expose secrets or raw identity data | OBSERVED/PARTIAL | Expand schema/error contract tests |
| 429 Rate limited | Account Request and auth rate-limit tests exist | `workspaceScopedReads` maps 429 to safe unavailable state | No rate-limit internals or identity enumeration | OBSERVED/PARTIAL | Add route-level rate-limit matrix and retry policy checks |
| 500 Internal Error | No complete P4 route matrix; backend framework provides generic handling | Generic safe mapping for error responses | Require redaction and correlation ID | REQUIRED | Add non-production fault injection tests |
| 503 Unavailable/disabled | Clinical gateway disabled path and national identity stub-safe path exist | `workspaceScopedReads` maps 503 to disabled/unavailable | No fallback to legacy or ungoverned data | OBSERVED/PARTIAL | Add canonical gateway disabled E2E and runtime checks |
| Timeout/network failure | Tests and client mapping cover unavailable transport in selected surfaces | `workspaceScopedReads` maps no response to safe unavailable state | No stale sensitive data or bypass | MAPPED | Add bounded timeout/retry assertions |

## Current conclusion

The critical canonical clinical read boundary has safe 401/403/429/503/no-response mappings and no legacy fallback in frontend-v3. Full P4 error closure requires broader route coverage, fault-injection tests, and approved runtime evidence; this document does not mark the remaining rows as PASS.

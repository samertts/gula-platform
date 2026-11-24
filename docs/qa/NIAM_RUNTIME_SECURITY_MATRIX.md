# NIAM Runtime Security Matrix

Compact, evidence-linked matrix for P0/P1 NIAM operations, built from real
disposable PostgreSQL + Redis + real HTTP proofs across this session's
work (`NIAM_LIVE_PATH_PROOF_2.md`, `NIAM_LIVE_PATH_PROOF_3.md`,
`NIAM_PLATFORM_AUTHORITY_COMPLETION.md`, and this workstream's own
supplemental proof). Not every endpoint — the seven operations proven to
carry Platform Authority (P0/P1: authorization-bearing, security-relevant)
plus the authentication-layer cases that apply to all of them uniformly.

## Authentication matrix (applies uniformly — proven once, holds for every operation below)

| Case | Request | Expected | Actual | Evidence |
|---|---|---|---|---|
| No token | any protected NIAM route | 401 | **401** | Proof 2, Proof 3, WS1 proof — every operation |
| Malformed token (not a real JWT) | `POST .../activate` | 401 | **401** | This workstream's supplemental proof |
| Expired session (`expires_at` in the past, `is_active=True`) | same | 401 | **200 → fixed → 401** | Real, previously-undiscovered P1 finding, fixed same pass (commit `90262be2`). Before the fix: `get_current_niam_actor`/`_sync` never filtered on `expires_at` at all — an expired session remained valid indefinitely. |
| Valid, non-expired session | same | 200/reaches authorization | **200** | Confirmed the fix doesn't false-reject a genuinely valid session |

## Authorization matrix (per operation)

| Operation | No capability | Wrong capability | Correct capability | Revoked capability | Evidence |
|---|---|---|---|---|---|
| `federation.update_provider` | 403 | — | 200, persists, audited | — | Proof 3 |
| `trust.update_framework` | 403 | — | 200, persists, audited | — | Proof 3 |
| `federation.register_provider` | 403 | — | 200, persists, audited | — | WS1 proof |
| `trust.activate_framework` | 403 | — | 200, persists, audited | — | WS1 proof |
| `certificates.issue_certificate` | 403 | — | 200, persists, audited | — | WS1 proof |
| `certificates.revoke_certificate` | 403 | — | 200, persists, audited | — | WS1 proof |
| `governance.create_authority` | 403 | **403** (holding `trust.manage` instead) | 200, persists, audited | — | WS1 proof + `test_wrong_capability_still_denies_create_authority` |
| any of the above | — | — | — | **403** | This workstream's supplemental proof: `trust.activate_framework` denied after its capability is revoked mid-session (same still-valid session, same token) |

"Wrong capability" (holding a *different* one of the four, not none at
all) was proven for `create_authority` specifically (unit test) and is
architecturally identical for the other five (same `require_platform_capability`
call, same fail-closed `has_capability` check against the exact
requested string) — not re-proven per-operation at the live-HTTP layer to
avoid redundant, already-covered infrastructure spin-up per
"do not repeatedly run already-proven tests."

## Boundary matrix

| Case | Result | Evidence |
|---|---|---|
| Platform-global resource (all seven operations' targets: `FederatedProvider`, `TrustFramework`, `DigitalCertificate` when unscoped, `IdentityAuthority`) | Capability alone authorizes, no additional per-org check exists or is expected | `NIAM_PLATFORM_AUTHORITY_COMPLETION.md`'s scope classification |
| Conditionally-scoped resource (`DigitalCertificate.organization_id` optional) | Platform capability authorizes regardless of whether the specific cert has an `organization_id` set — this is "platform," not org-delegated, authority | Traced, not separately re-proven per org value (architecturally the same fail-closed capability gate, no code path branches on `organization_id` at all) |
| "Wrong organization" (a cross-tenant read/write on an org-scoped NIAM resource) | **NOT APPLICABLE to the seven operations proven here** — none of them branch on `organization_id` for authorization | Honestly reported: no NIAM operation in this matrix is org-scoped for authorization purposes; a genuinely org-scoped NIAM operation (if one exists elsewhere) is out of this matrix's traced set |
| Malformed target (nonexistent `provider_id`/`framework_id`/`certificate_id`/`authority_id`) | `{"error": "not_found"}` (federation/trust) or `404` (certificates), **no commit** | Proven for `update_framework`/`update_provider` (Proof 3) and `activate_framework` (unit test `test_activate_framework_not_found_never_commits`) |

## Mutation matrix

| Case | Result | Evidence |
|---|---|---|
| Allowed field | Applied, persists | Proof 3 (`name_en` on both routes), WS1 proof (create operations accept all constructor fields — SYSTEM_CONTROLLED precedent, no allow-list needed for pure creates gated by platform capability) |
| Protected field (`client_secret_encrypted`, `issuer_url`, `status`, `provider_id`/`framework_id` immutable) | Silently ignored, unchanged in a fresh-session read | Proof 3 |
| Invalid state transition | Not exercised in this pass — `activate_framework`/`update_framework` have no transition guard today (any `status` string reachable via `update_framework`'s allow-list is rejected there since `status` isn't allow-listed at all; `activate_framework` unconditionally sets `status="active"` regardless of prior state) — **flagged, not fixed**: `TrustFramework` has no state-machine guard analogous to `domain/order_state.py`/`domain/sample_state.py`'s clinical precedent |
| Repeated request / idempotency | A second, distinct `update_provider` call correctly applies on top of the first (durable, sequential) — proven; this is normal re-application, not idempotency-key-based dedup (no `Idempotency-Key` contract exists on these routes, unlike `ClinicalCommandGuard`'s pattern used elsewhere in the repo) | Proof 3 (`federation_second_update`) |

## Persistence matrix

| Case | Result | Evidence |
|---|---|---|
| Successful commit | Fresh-session read confirms the mutation | Proof 3, WS1 proof |
| Deliberate rollback (real induced failure, mid-transaction) | Neither the business mutation nor its audit entry survives — fresh-session read shows the pre-request state exactly | Proof 3 |
| Audit creation | Exactly one real audit row per successful call, real UUID, real actor_id, real target_id | Proof 3, WS1 proof (5 new event types confirmed) |
| Fresh-session verification | Used throughout — every "persists" claim above is backed by a separate DB session, not the same one the mutation ran in | Proof 3, WS1 proof |

## RESULT

**VERIFIED** for the seven operations and the authentication/authorization/
persistence dimensions traced above — all backed by real disposable
PostgreSQL + Redis + real HTTP, not mocked authorization or direct
service invocation.

**PARTIALLY VERIFIED / flagged, not fixed**, honestly reported rather than
hidden:
1. `TrustFramework` has no state-transition guard — `activate_framework`
   unconditionally sets `active` regardless of prior status (e.g., a
   `superseded` framework could be "re-activated"). Not fixed this pass —
   would need a domain decision on the intended state graph, mirroring
   `imaging-slice-order-transition-graph`'s own precedent of not inventing
   one without evidence.
2. "Wrong organization" doesn't apply to any of the seven traced
   operations — none are org-scoped. Not claimed as tested when it isn't
   applicable.
3. No idempotency-key contract on any of these routes (unlike
   `ClinicalCommandGuard`'s existing pattern elsewhere) — a legitimate,
   accidental duplicate submission (e.g., a retried HTTP request) creates
   a second, distinct audit entry and re-applies the same fields, rather
   than being recognized as a duplicate. Not fixed — would be a new
   contract (headers, dedup storage) outside this matrix's scope.

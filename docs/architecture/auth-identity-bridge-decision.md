# AUTH-002 — Identity Bridge Decision

**Program:** AUTH-002 · **Status:** VERIFIED · **Recommendation: OPTION A.**
No production authentication code was changed.

---

## 1. The exact failure boundary, measured

Executed against a database at head, resolving the real dependencies with real
tokens (read-only; no rows created):

| # | Flow | Result |
|---|---|---|
| C | legacy dependency ← legacy token | **200 OK** — `role=blood_bank_technician` |
| D | **NIAM dependency ← legacy token** | **401 "Invalid NIAM access token"** |
| E | legacy dependency ← NIAM-shaped token | **401 "Invalid token payload"** |
| F | **legacy dependency ← dual-claim token** | **200 OK** — extra claims ignored |
| G | NIAM dependency ← dual-claim token, no session row | **401 "Inactive or invalid NIAM session"** |

Token claims from `/login`: `exp, iat, jti, lab_id, perm_ver, role, type, user_id`.

**The boundary is D**, and it is a *claims* failure, not a cryptographic one.
`get_current_niam_actor` calls the same `decode_token` with the same
`SECRET_KEY`; the signature verifies. It rejects because `account_uuid` is absent.

**G is the decisive measurement.** A token carrying both claim sets clears the
NIAM claims check and fails only on the missing `niam_sessions` row. So the gap
between the two stacks is exactly two things — **claims, and a session row** —
and nothing else.

**F is the second decisive measurement.** The legacy dependency accepts a
dual-claim token unchanged, because it reads only the claims it knows. Adding
NIAM claims is therefore **backward compatible with every existing legacy
consumer**.

## 2. The bridge already exists in code and is already in production use

This is not a greenfield decision. `app/identity/models/legacy_account_link.py`
plus `app/identity/services/legacy_mapping_service.py` implement a **reversible,
audited, non-destructive** legacy→canonical bridge:

* `LegacyAccountLinkSource = {user, lab_user}` — **the discriminator the legacy
  token lacks** (§D1 of `auth-identity-model.md`).
* Statuses `pending → validated → migrated`, plus `collision`, `rolled_back`,
  `blocked` — the ADD/BACKFILL/VALIDATE/SWITCH/RETIRE ladder, already modelled.
* HMAC `source_fingerprint`; the model stores no email, phone, national ID or
  credential.
* `rollback_token` + an explicit `rollback()`; every transition audited.
* Its own docstring: *"never creates canonical accounts, copies legacy
  credentials, runs backfills, enables dual-write, or changes authorization
  decisions. Those actions require separate approved waves."*

And `ClinicalAuthorizationContextService` **already consumes it in production**:
four clinical read gates (`clinical_gateway`, `radiology`, `ehr`, `nursing`)
take a legacy `LabUser` from a legacy token and resolve it through
`LegacyAccountLink → Account → IdentityRecord → assignment → facility →
organization → tenant`, failing closed on unresolved, ambiguous or inactive.

**The platform has already answered the direction question in code:** legacy
authenticates, NIAM is canonical for identity and authorization, and the link
table is the bridge. `niam_legacy_account_links` currently holds **0 rows**, so
those gates deny today — correctly, but universally.

## 3. Option A — `/login` becomes the canonical entry and establishes a NIAM session

| Axis | Assessment |
|---|---|
| Identity integrity | **Strong.** One canonical subject (`Account.uuid`); the `user`/`lab_user` ambiguity (D1) is resolved by `LegacyAccountLinkSource`. |
| Security | **Improves.** Closes D1. Adds device/IP/UA capture and per-session revocation. |
| Session lifecycle | **Gained.** Legacy has no session table at all; NIAM has expiry, last-activity, MFA flag. |
| Authorization | Unchanged during the bridge — legacy `role`/`perm_ver` keeps working while NIAM roles are populated. No authorization is weakened at any step. |
| Workspace architecture | **Unblocked.** `list_eligible` / `switch` become reachable with no change to either. |
| Migration complexity | Moderate, and **the machinery exists**. |
| Backward compatibility | **Proven by measurement F** — legacy consumers ignore the added claims. |
| Frontend impact | **Zero for the bridge itself.** `AuthContext` already calls `/login` and already fetches memberships and workspaces; those calls simply stop returning 401. |
| Backend impact | Confined to `login.py` (mint extra claims, create a session row) plus resolution through the existing mapping service. |
| Audit | **Improves** — `AuditService` records workspace and session events. |
| Revocation | **Improves** — per-session and terminate-all, instead of blacklisting a `jti`. |
| Refresh | Refresh becomes session-bound rather than a free-floating JWT. |
| National identity integration | **Required.** `niam_identities` (person) separate from `niam_accounts` (account) is the shape civil-identity integration needs; legacy has no person layer at all. |
| Organization authentication | Uses `niam_organizations` + representatives/ownerships — already how `list_eligible` works. |
| Citizen authentication | `ensure_citizen_workspace` already runs on NIAM login; citizen becomes a context, not an account type. |
| Operational complexity | One login path to operate; a link table to monitor for `collision`. |
| Technical debt | **Reduces.** Ends with one authentication path. |
| Failure modes | An account with no migrated link → the bridge must **fail open to legacy behaviour, never fail open to NIAM authorization**. Collisions are an explicit status, not an exception. |
| Long-term maintainability | **Best.** One entry, one identity, contextual workspaces. |

## 4. Option B — NIAM accepts legacy tokens

| Axis | Assessment |
|---|---|
| Identity integrity | **Fails.** NIAM would have to accept `user_id`, an identifier that is ambiguous across two tables (D1). It would import the defect into the canonical model. |
| Security | **Worse.** Two token shapes accepted at one door is a token-confusion surface; `account_uuid` would have to be inferred per request. |
| Session lifecycle | **No gain.** Legacy tokens have no session row, so `/niam/sessions`, device trust and terminate-all stay impossible — the Privacy Centre stays blocked. |
| Authorization | Workspace eligibility needs an `Account`; a legacy token would force a lookup on every request, or a synthesised account — a **fake session**, which is forbidden. |
| Workspace architecture | Would need `list_eligible` to accept a non-Account subject — changing correct code to accommodate incorrect input. |
| Migration complexity | Lower **today**, higher forever: the migration is deferred, not avoided. |
| Backward compatibility | Total — which is precisely the trap. |
| Frontend impact | Zero. |
| Backend impact | Every `/niam/*` dependency changes; the blast radius is larger than Option A's. |
| Audit | Weaker — no session to attribute events to. |
| Revocation | Unchanged: blacklist-only. |
| Refresh | Unchanged: unbound. |
| National identity integration | **Blocks it.** No person layer, no canonical subject. |
| Failure modes | Silent identity collision under D1 — the worst class here. |
| Long-term maintainability | **Worst.** Enshrines dual authentication permanently, which §6 of the brief forbids without a demonstrable requirement. No such requirement was found. |

## 5. Recommendation — **OPTION A**, implemented as an extension of the existing bridge

Not "both are possible". Option B fails on identity integrity before any other
axis: it would make the canonical model accept an identifier that cannot
distinguish a citizen from a laboratory user.

Concretely, `/login` should, after it has authenticated exactly as it does today:

1. resolve the legacy subject to a canonical `Account` via
   `LegacyMappingService` using `source_kind = user | lab_user` — the
   discriminator legacy lacks;
2. mint the **same** token it mints today **plus** `account_uuid` and
   `identity_id` (measurement F proves this breaks nothing);
3. create a `niam_sessions` row bound to the access and refresh `jti`
   (measurement G proves this is the only remaining requirement);
4. keep `role` and `perm_ver` authoritative for legacy authorization until NIAM
   roles are populated and proven — **authorization is not switched in the same
   step as authentication**.

When no migrated link exists, the login must succeed with legacy claims only and
NIAM-dependent features must stay 401. **Fail open to legacy behaviour; never
fail open to NIAM authorization.**

## 6. Migration strategy (proposed, not implemented)

| Stage | Action | Rollback |
|---|---|---|
| **ADD** | Mint `account_uuid`/`identity_id` **only when a migrated link exists**; create the session row. Behind a feature flag, one cohort. | Disable the flag; tokens revert to legacy shape. No data written that legacy reads. |
| **BACKFILL** | Create `Account` + `IdentityRecord` per legacy subject; `ensure_pending_link` for each; resolve `collision` by hand — never automatically. | `rollback()` per link using `rollback_token`; accounts remain, unused. |
| **VALIDATE** | Transition `pending → validated`: prove one and only one active link per legacy subject, and that both subjects agree on the person. | Return to `pending`. |
| **SHADOW** | Mint both claim sets for the whole cohort but keep legacy authorization authoritative. Compare NIAM-derived and legacy decisions; log divergence; act on none. | Disable the flag. |
| **SWITCH** | Make NIAM roles/permissions authoritative, per domain, only where shadow showed zero divergence. | Per-domain revert; legacy claims are still in the token. |
| **RETIRE** | Remove `/citizen/login`; stop minting legacy claims; drop `perm_ver`. | Point of no return — requires an explicit go/no-go. |

**Rollback requirements:** every stage before RETIRE must be reversible by
disabling a flag or calling `rollback()`, with no destructive change to `users`
or `lab_users`. The token must carry both claim sets throughout, so a rollback
never invalidates issued sessions.

## 7. Security analysis

| Risk | Assessment |
|---|---|
| **Identity collision (D1)** | **Live and structural.** `user_id` is ambiguous across `users` and `lab_users`. Unexploitable only because `users` is empty. Option A closes it; Option B imports it. |
| Token confusion | Option A: one token shape, superset claims — low. Option B: two shapes at one door — high. |
| Token substitution | Same signing key across both stacks, so a NIAM token is *cryptographically* valid at legacy endpoints; it is rejected only because `user_id` is absent (measurement E). This is thin. Option A makes the claim sets deliberately consistent; a future hardening should add an explicit token-purpose claim. **Recorded as AUTH-F6.** |
| Session fixation | Option A adds a server-side session created at authentication — an improvement over none. |
| Privilege escalation | No authorization change is proposed at ADD/BACKFILL/VALIDATE/SHADOW. SWITCH is per-domain and gated on zero shadow divergence. |
| Workspace escalation | `switch()` re-derives eligibility server-side and audits denial. Unchanged by either option. |
| Account takeover | Mitigated by resolving D1. |
| Revocation / logout | Legacy blacklists a `jti` with no session record; Option A adds real per-session revocation. During the bridge **both** must be honoured, or logout regresses. **Recorded as AUTH-F7.** |
| Cross-tenant context | `lab_id` (legacy) and `organization_id` (NIAM) must not diverge. The mapping is exactly what the clinical gates already prove. Divergence must be a SHADOW-stage alarm. |
| Organization impersonation | Eligibility comes from active representative/ownership rows only; no client input participates. |

## 8. Findings

| ID | Sev | Finding | Status |
|---|---|---|---|
| **AUTH-F5** | P2 | `niam_memberships` does not feed `list_eligible`; only representative/ownership status does. Membership needs a stated purpose or must feed eligibility. | VERIFIED |
| **AUTH-F6** | P2 | Legacy and NIAM tokens share a signing key and differ only by claims; there is no explicit token-purpose claim. | VERIFIED |
| **AUTH-F7** | P2 | Two revocation mechanisms (jti blacklist, session row) must both be honoured during the bridge or logout regresses. | VERIFIED |
| **AUTH-F8** | P1 | `user_id` is ambiguous across `users` and `lab_users` (D1). Latent account-takeover class; unexploitable only while `users` is empty. | VERIFIED |

## 9. Blockers

**None for the decision.** The evidence is sufficient and Option A is chosen.

Two things must be settled **before** implementation, and neither is an
engineering call:

1. **Cohort and go/no-go owner** for each migration stage.
2. **Collision policy** — what happens when one person maps to both a `users`
   and a `lab_users` row. The model has a `collision` status; the resolution
   rule is a governance decision.

## 10. Verification evidence

| Command | Result | Status |
|---|---|---|
| Resolve both dependencies with 4 token shapes | C 200, D 401, E 401, F 200, G 401 | VERIFIED |
| `decode_token(create_token(build_token_payload(...)))` | no `account_uuid` | VERIFIED |
| `niam_legacy_account_links` / `niam_accounts` / `niam_sessions` counts | 0 / 0 / 0 | VERIFIED |
| Bridge code present and consumed | `legacy_mapping_service.py`, `clinical_authorization_context_service.py`, 4 clinical gates | VERIFIED |
| `list_eligible` derivation | ownership + active representative/ownership only | VERIFIED |

## 11. Next implementation batch

**AUTH-003 — ADD stage only.** Mint `account_uuid`/`identity_id` and create a
`niam_sessions` row when a migrated link exists, behind a feature flag, for one
cohort, with legacy authorization untouched. It is the smallest step that makes
the bridge real and is fully reversible by disabling the flag.

**AUTH-001** (the `RoleGuard` fix) stays separate and can land before or after —
it is not an authorization mechanism and must not be treated as one.

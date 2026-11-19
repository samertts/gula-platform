# NIAM Sync/Async Closure Engine — Batch 5: `adaptive_auth`

Phase 8 of the "NIAM SYNC/ASYNC CLOSURE ENGINE — REAL P1 CLOSURE — BOUNDED
BATCHES WITH AUTOMATIC GATES" workstream. Target: 16 occurrences in
`app/identity/adaptive_auth/routes.py`.

**This batch's scope was explicitly widened by direct user authorization**
after discovery revealed that the mechanical sync/async fix alone would
convert a pre-existing, currently-crash-masked P0 horizontal-authorization
gap into a live, exploitable one the moment these routes became reachable.
Per that authorization, this batch closes the sync/async defect AND the
authorization gap together, treated as a P0 security closure — not merely
a mechanical transformation.

## Discovery

All 16 routes declared `db: AsyncSession = Depends(get_db)` against
`AdaptiveAuthService`/`SessionGovernanceService` (already correctly
`__init__(self, session: AsyncSession)`). **Category A**, identical
pattern to every prior batch.

Distinct from every prior batch: **none of the 16 routes took an
authenticated actor at all** — the only gate was the parent router's
`_AUTH_REQUIRED = [Depends(get_current_niam_actor)]` (any authenticated
NIAM account, any role). Nine of the 16 routes operate on account- or
session-scoped resources (risk evaluation/history, MFA challenges/
verification, device/travel records, session counts/enforcement/validity)
identified by a client-supplied `account_id`/`mfa_id`/`session_id`, with
**zero check that the target belonged to the caller**. Before this fix,
any authenticated NIAM account of any role could read another account's
login-risk history, create or attempt to answer another account's MFA
challenge, enumerate another account's active sessions, or force another
account's session-policy enforcement — masked only by the fact that these
routes crashed (`TypeError`) on the broken sync dependency before ever
reaching that code.

Four routes (`create_risk_policy`, `update_risk_policy`,
`create_session_policy`, `update_session_policy`) were already correctly
fail-closed via an existing `_require_policy_admin()` gate (with a
documented rationale for why no NIAM authority currently covers
platform-wide risk/session policy management) — left untouched. Two
routes (`list_risk_policies`, `list_session_policies`) are global,
non-sensitive reads — left untouched. One route (`check_session_expiry`)
is a global maintenance sweep, not object-scoped — see "Separate findings"
below.

## Authorization decision: self-access only, no cross-account admin path

Investigated whether any existing NIAM authority concept could legitimately
authorize cross-account access (e.g., a security team investigating another
user's risk history) before adding a check, per the explicit instruction
not to reach for `governance_manage` merely because it exists:

- NIAM's 4 `PlatformCapability` values (`federation_manage`, `trust_manage`,
  `certificates_manage`, `governance_manage`) are platform-administrative
  concepts (managing federation trust, certificate authorities, governance
  policy) with no documented ownership semantics over another individual
  account's personal security posture.
- `AuthorizationDecisionService` (NIAM's ABAC engine) is organization-scoped
  by design (per its own `_POLICY_AUTHORITY_UNAVAILABLE` precedent already
  in this file) — it does not fit an account-to-account check either.
- The legacy, non-NIAM `app/security/rbac.py` permission catalog has a
  `security:manage_mfa` permission, but it belongs to a completely separate
  authorization system (different actor/session model) — bridging it in
  would be a larger architectural decision, not "reuse an existing
  capability."

**Conclusion: no existing capability legitimately authorizes cross-account
access to these resources.** Per instruction, rather than invent one
unilaterally, `_require_self()` fails closed to self-access-only — proven
in the HTTP matrix below by granting the test actor a real
`governance_manage` platform-authority assignment and confirming it still
does **not** unlock cross-account access. This mirrors the existing
`_require_policy_admin()` precedent already in this file (fail closed,
document the gap, don't invent a permission).

## Repair

- `app/identity/adaptive_auth/routes.py`: `Depends(get_db)` →
  `Depends(get_niam_db)` on all 16 routes; `await db.commit()` added to
  every mutating route (10 total: `evaluate_risk`, `create_mfa_challenge`,
  `verify_mfa_challenge`, `create_risk_policy`, `update_risk_policy`,
  `create_session_policy`, `update_session_policy`, `detect_new_device`,
  `enforce_session_policy`, `check_session_expiry`).
- Added `_require_self(actor, account_id)` — a minimal object-ownership
  check (`account_id != actor.account.id` → 403) — to the 9
  account/session-scoped routes: `evaluate_risk`, `get_risk_history`,
  `create_mfa_challenge`, `verify_mfa_challenge` (ownership resolved from
  the target `AdaptiveMFASession.account_id` first, since this route takes
  no `account_id` directly), `list_travel_events`, `get_active_session_count`,
  `detect_new_device`, `enforce_session_policy`, `is_session_valid`
  (ownership resolved from the target `UserSession.account_id` first).
- Each of these 9 routes now also takes `actor: NiamActor =
  Depends(get_current_niam_actor)` to make the check possible (previously
  the actor object wasn't available inside the route function at all).
- No new Platform Authority capability was created; no change to
  `AuthorizationDecisionService`; the 4 already-gated policy-mutation
  routes and the 2 global policy-read routes are untouched.

## A third pre-existing, unrelated bug found and fixed: `AdaptiveMFASession.session_id` FK drift

While proving `create_mfa_challenge`, discovered
`app/identity/adaptive_auth/models.py`'s `AdaptiveMFASession.session_id`
declared `ForeignKey("niam_user_sessions.id")` — but the real table is
`niam_sessions` (confirmed via `pg_get_constraintdef`: the **actual,
already-deployed database constraint** correctly references
`niam_sessions(id)`). This is pure Python-side model/reality drift with
**zero schema risk** — identical in nature and remedy to this session's
earlier `niam-trust-fk-drift` finding (TrustFramework's `authority_id`).
Fixed by correcting the string to `"niam_sessions.id"` — no migration
needed, since the database was already correct. Without this fix,
`create_mfa_challenge` (and thus `verify_mfa_challenge`) would have failed
with a `NoReferencedTableError` on every real call, unconditionally,
regardless of sync or async engine.

## A fourth pre-existing, unrelated bug found and documented (NOT fixed): `UserSession.account_type`

`SessionGovernanceService.is_session_valid()` and `.check_session_expiry()`
both reference `session.account_type`, but `UserSession` (confirmed via
its model definition) has no such column — only `session_type`. This
crashes with `AttributeError` on any real row, independent of sync/async.
Proven precisely: `is_session_valid`'s ownership check correctly executes
first (cross-account attempts get 403 without ever reaching this bug;
malformed/nonexistent session lookups return the correct `{"valid":
false}`), and only the **legitimate self-access** path reaches the
underlying crash (500). This is out of scope for a sync/async batch — a
route/service attribute-reference bug, unrelated to the engine choice —
documented rather than silently fixed or silently left unmentioned.
Likely intended field: either add a real `account_type` derivation (join
to `Account`) or use `session.session_type`; needs a design decision, not
a mechanical fix.

## Separate finding, not touched: `check_session_expiry` is a global, ungated maintenance action

Any authenticated NIAM actor can currently trigger a full session-expiry
sweep across the entire platform. Unlike the 9 fixed routes, there is no
"ownership" to check here (`check_session_expiry` doesn't accept a
target). This is the same class of gap as the already-acknowledged
`_POLICY_AUTHORITY_UNAVAILABLE` situation — a genuinely global
administrative action with no platform-admin authority model yet to gate
it. Documented for a future, correctly-scoped pass rather than addressed
here (it also currently 500s due to the `account_type` bug above, which
would need fixing first regardless).

## Real HTTP + PostgreSQL proof

Seeded two real accounts (Alice, Bob), including granting Alice a real
`PlatformAuthorityAssignment(capability=governance_manage)` specifically to
prove that capability does **not** unlock cross-account access. Full
matrix against real PostgreSQL (`gula_certproof`), router path
`/niam/niam/adaptive-auth/*` (double `/niam` prefix — this router declares
its own `/niam/adaptive-auth` prefix, then mounts under the parent `/niam`
router, matching the `trust`/`certificates` pattern already documented
this session):

| Route | No token | Expired session | Self | Other account | Other + governance_manage | Malformed account |
|---|---|---|---|---|---|---|
| `evaluate_risk` | 401 | 401 | 200 | 403 | 403 | 403 |
| `get_risk_history` | 401 | 401 | 200 | 403 | — | — |
| `create_mfa_challenge` | 401 | 401 | 200 | 403 | — | — |
| `verify_mfa_challenge` | 401 | — | 200 (wrong code, self) | 403 | — | — (nonexistent mfa_id → 200, unchanged not-found semantics) |
| `list_travel_events` | 401 | — | 200 | 403 | — | — |
| `get_active_session_count` | 401 | — | 200 | 403 | — | — |
| `detect_new_device` | 401 | — | 200 | 403 | — | — |
| `enforce_session_policy` | 401 | — | 200 | 403 | — | — |
| `is_session_valid` | 401 | — | 500 (pre-existing bug, see above) | 403 | — | — (nonexistent session_id → 200) |

Global/unchanged routes confirmed still working as before: `list_risk_policies`/
`list_session_policies` return 200 for any authenticated actor;
`create_risk_policy`/`create_session_policy` still return 403
unconditionally (pre-existing fail-closed gate, untouched).

**Fresh-session persistence + isolation proof**: Alice's risk events
persisted; Bob's cross-account `evaluate_risk` attempt produced **zero**
risk events under Bob's own account (blocked before any write); Alice's
MFA session persisted with the correct `account_id`; its `attempts`
counter incremented exactly once — from Alice's own wrong-code attempt —
proving Bob's blocked attempt never reached (and never mutated) the
session.

## Failure injection (rollback proof)

Monkeypatched `AsyncSession.commit` to raise immediately after
`create_mfa_challenge`'s flush. Result: `500`, and a fresh-session query
confirmed exactly one MFA session row for the test account afterward (the
control request's, none orphaned from the injected failure).

## Negative proof (authorization-focused, not just sync/async)

Given this batch's central risk is the authorization gap, the negative
proof targeted that property directly: temporarily removed the
`_require_self(actor, account_id)` call from `evaluate_risk` and re-ran the
full matrix. Result: `evaluate_risk_other_account_by_b` and
`evaluate_risk_other_account_with_governance_manage` both flipped from
`403` to **`200`** — Bob could trigger risk evaluation against Alice's
account. Confirmed the ownership check is the actual load-bearing control,
not incidental. Restored `routes.py` from a pre-change backup; `md5sum`
and `git diff` both confirmed byte-identical restoration to the fixed
state before continuing.

## Regression

`pytest tests/identity/ tests/test_migrations.py
tests/test_migration_resilience.py`: **255 passed, 4 skipped** — identical
to every prior batch's baseline; the FK-string fix in `models.py` and the
new ownership checks introduced zero regressions in the existing suite.

## GATE 1 (extended for this batch's security scope)

- All 16 occurrences correctly classified: **yes**.
- Category-A dependency fix applied to all 16: **yes**.
- Missing commits added to all 10 mutating routes: **yes**.
- Horizontal-authorization gap identified precisely (9 routes, with
  reasoning for the other 7): **yes**.
- No capability invented without justification; existing capabilities
  checked and confirmed not applicable, with a real capability grant
  proving that in the HTTP matrix rather than merely asserted: **yes**.
- Self-access preserved, cross-account access denied, across every
  affected route: **yes**, full 401/403/200 matrix.
- Malformed/nonexistent target identifiers handled safely (403 or a
  pre-existing 200 not-found body, never a crash from the ownership
  check itself): **yes**.
- Unexpected DB/application errors surface as real 500s, never silently
  downgraded to a 403 deny by the new check: **yes** (`is_session_valid`'s
  and `check_session_expiry`'s pre-existing `account_type` bug still
  produces genuine 500s).
- Real HTTP + PostgreSQL proof, including persistence and cross-account
  data-isolation evidence: **yes**.
- Failure-injection rollback proof: **yes**, zero orphaned rows.
- Negative proof on the authorization property itself (not just the DB
  engine), confirmed real regression, source restored byte-identical:
  **yes**.
- Regression suite: **yes**, 255 passed / 4 skipped, no change from
  baseline.
- Two additional pre-existing bugs found: one fixed (zero-risk FK-string
  correction, matching an already-deployed, already-correct database
  constraint), one documented but not fixed (`account_type` attribute
  bug, a genuine design question, not sync/async).

## RESULT

**VERIFIED** (both the sync/async defect and the discovered authorization
gap). Sync/async defect count: 96 → 80 (16 closed: `adaptive_auth`). Two
separate findings remain open and documented for future, correctly-scoped
work: the `UserSession.account_type` attribute bug, and
`check_session_expiry`'s missing global-action gate. Batch 6
(`federation`, 15 occurrences) may now begin.

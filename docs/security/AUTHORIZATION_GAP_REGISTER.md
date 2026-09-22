# Authorization Gap Register

Findings only — dispositions, not blanket claims. Severity assigned by
concrete impact, not by domain name.

## Sampling method this pass

Rather than eyeballing every route, cross-referenced the count of
`@router.post/put/patch/delete` decorators against the count of
`require_platform_capability`/`require_permission`/`get_current_user`
call sites within the same function body, for the 4 Platform-Authority
domains (federation, trust, certificates, governance — small enough to
check exhaustively, 100 mutating routes total). This surfaced 2
candidates for manual review; both resolved as correctly-designed, not
gaps (below). Zero new findings from this specific check.

## GAP-1 (carried forward, not new) — `adaptive-auth-account-id-idor`

- **Severity**: P1 (candidate — broad IDOR shape, NEEDS_DECISION)
- **Route**: ~10 endpoints in `app/identity/adaptive_auth/routes.py`
  (`evaluate_risk`, `get_risk_history`, `create_mfa_challenge`,
  `verify_mfa_challenge`, `list_travel_events`,
  `get_active_session_count`, `detect_new_device`,
  `enforce_session_policy`, `check_session_expiry`, `is_session_valid`)
- **Current mechanism**: bare NIAM authentication only
- **Missing control**: no self-or-admin ownership check on a
  client-supplied `account_id`/`session_id`
- **Tenant impact**: none (this is account-scoped, not tenant-scoped)
- **Ownership impact**: any authenticated actor can evaluate/read/act on
  an arbitrary other account's risk/session state
- **Exploitability**: real, but the correct semantics are genuinely
  ambiguous without deeper context on NIAM's login/step-up-auth call
  graph (some of these endpoints plausibly need to be system-invoked
  mid-login, before the acting account's own session exists)
- **Evidence**: originally found and documented in
  `docs/engineering/MUSTAFA_ACTIVE_REPAIR_QUEUE.md`
  (`adaptive-auth-account-id-idor` row), prior session
- **Recommended control**: a domain owner must state, per endpoint,
  whether the caller is (a) the account itself, (b) an
  unauthenticated-at-that-point login-internal caller, or (c) a
  legitimate cross-account admin/security caller
- **Status**: **BLOCKED — NEEDS_DECISION.** Not re-investigated this
  pass (no new evidence); carried forward as-is per this pass's
  explicit "reconcile, don't repeat" instruction.

## Checked and confirmed NOT a gap this pass

### `POST /federation/sessions`, `POST /federation/sessions/{id}/terminate`

Initial automated scan flagged these as lacking a
`require_platform_capability` call (unlike their 10 sibling mutations
in the same file). Manual read: both are correctly self-service —
`create_federated_session` calls `_require_self(actor, account_id)`;
`terminate_federated_session` resolves the target session's owning
`account_id` server-side *before* calling `_require_self` on it (with
an explicit code comment recording the reasoning: "a client can never
terminate another account's federated session merely by
guessing/obtaining its session_id"). Platform capability would be the
wrong control here — a user managing their own federated login session
should not need platform-admin rights. **Disposition: VERIFIED, not a
gap.**

## Platform Authority grant/revoke — confirmed NOT_IMPLEMENTED (not a gap)

Per `docs/security/AUTHORIZATION_COVERAGE_MATRIX.md`: there is no HTTP
route anywhere that grants or revokes a `PlatformAuthorityAssignment`.
The only path is `app/identity/platform_authority/bootstrap.py`, which
its own docstring states is "never exposed via any HTTP route,
deployment/environment-controlled." This is recorded as **NOT
IMPLEMENTED (by design)**, not a gap — per this directive's own
instruction not to fabricate a route that doesn't exist, and not to
treat "operation doesn't exist" as equivalent to "operation exists but
is unguarded."

## Summary

| ID | Severity | Status |
|---|---|---|
| `adaptive-auth-account-id-idor` | P1 | BLOCKED — NEEDS_DECISION (carried forward) |
| federation self-service session routes | — | VERIFIED (checked this pass, not a gap) |
| Platform Authority grant/revoke | — | NOT IMPLEMENTED (by design, not a gap) |

**Zero new P0/P1 authorization gaps found in this bounded pass.** This
reflects the narrow scope checked (4 Platform Authority domains, ~100
routes, cross-referenced mechanically) rather than a claim that the
remaining ~78 unaudited routers are gap-free — see the UNKNOWN bucket
in `docs/security/AUTHORIZATION_COVERAGE_MATRIX.md`.

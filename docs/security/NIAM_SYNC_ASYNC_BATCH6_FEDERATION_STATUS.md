# NIAM Sync/Async Closure Engine — Batch 6: `federation`

Phase 9 of the "NIAM SYNC/ASYNC CLOSURE ENGINE — REAL P1 CLOSURE — BOUNDED
BATCHES WITH AUTOMATIC GATES" workstream. Target: 15 occurrences in
`app/identity/federation/routes.py` (2 of the file's 17 total routes,
`register_provider`/`update_provider`, were already fixed in an earlier
phase this session — not part of this batch's 15).

## Discovery and a second authorization gap, resolved by direct precedent (no new pause needed)

All 15 remaining routes declared `db: AsyncSession = Depends(get_db)`
against `FederationService`/`CrossOrgTrustService`/`FederationAgreementService`
(already correctly `__init__(self, session: AsyncSession)`). **Category A**.

As with `adaptive_auth` (Batch 5), none of these 15 routes had any
authorization beyond the parent router's authentication-only
`_AUTH_REQUIRED`. Unlike `adaptive_auth`, this did **not** require a new
design decision or another pause: this exact file already establishes the
correct pattern for 2 of its own routes (`register_provider`/
`update_provider`, fixed in an earlier phase, gated by
`PlatformCapability.federation_manage`), and 7 of the 15 remaining routes
are unambiguously the same class of platform-federation-administration
action already covered by that exact capability:

- `link_identity` / `unlink_identity` — linking/removing a federated
  identity link for a person, an identity-administration action.
- `establish_trust` / `suspend_trust` / `terminate_trust` — cross-organization
  trust relationship management.
- `create_agreement` / `sign_agreement` — federation agreement management.

These were gated with `require_platform_capability(actor, db,
PlatformCapability.federation_manage.value)` — reusing the file's own
established capability, not inventing one.

Two routes (`create_federated_session`/`terminate_federated_session`) are
account-scoped (a specific account's external-IdP login session), the same
shape as `adaptive_auth`'s account-scoped routes — gated with a
`_require_self(actor, account_id)` ownership check, directly reusing the
pattern and rationale explicitly authorized for Batch 5
(`docs/security/NIAM_SYNC_ASYNC_BATCH5_ADAPTIVE_AUTH_STATUS.md`).
`terminate_federated_session` takes no `account_id` directly; its target
session's owning account is resolved first, mirroring
`adaptive_auth.is_session_valid`'s identical pattern.

The remaining 6 routes (`list_providers`, `get_provider`,
`get_person_identities`, `get_trust_relationships`, `list_agreements`,
`get_agreement`) are reads — left authenticated-only, unchanged, matching
this session's established precedent for read endpoints throughout every
prior batch.

No new Platform Authority capability was created in this batch; both
`federation_manage` and the `_require_self` ownership-check pattern are
direct extensions of already-proven, already-reviewed precedent from this
exact file and the immediately preceding batch — not a fresh judgment
call.

## Repair

- `app/identity/federation/routes.py`: `Depends(get_db)` →
  `Depends(get_niam_db)` on all 15 routes; `await db.commit()` added to
  all 9 mutating routes (`link_identity`, `unlink_identity`,
  `establish_trust`, `suspend_trust`, `terminate_trust`,
  `create_agreement`, `sign_agreement`, `create_federated_session`,
  `terminate_federated_session`); `require_platform_capability` added to
  7 administrative mutations; `_require_self` added to 2 account-scoped
  mutations.
- No `id=...` crash bug present (confirmed by reading `services.py` in
  full — uses `uuid.uuid4()` directly for business keys, never overrides
  the model's `id`).

## Real HTTP + PostgreSQL proof

Seeded 5 accounts (no-capability, wrong-capability [`trust_manage`],
correct-capability [`federation_manage`], and two self-service accounts),
2 real organizations, and 1 real federation provider. Full matrix against
real PostgreSQL:

| Route | No token | Expired | No cap. | Wrong cap. | Correct cap. |
|---|---|---|---|---|---|
| `link_identity` | 401 | 401 | 403 | 403 | 200 |
| `unlink_identity` | 401 | 401 | 403 | 403 | 200 |
| `establish_trust` | 401 | 401 | 403 | 403 | 200 |
| `suspend_trust` | 401 | 401 | 403 | 403 | 200 |
| `terminate_trust` | 401 | 401 | 403 | 403 | 200 |
| `create_agreement` | 401 | 401 | 403 | 403 | 200 |
| `sign_agreement` | 401 | 401 | 403 | 403 | 200 |

| Route | No token | Other account | Self |
|---|---|---|---|
| `create_federated_session` | 401 | 403 | 200 |
| `terminate_federated_session` | 401 | 403 | 200 |

Read routes (`get_person_identities`, `get_trust_relationships`,
`list_agreements`, `get_agreement`, `list_providers`, `get_provider`):
401 with no token, 200 for any authenticated actor — unchanged.

**Fresh-session persistence proof**: `FederatedIdentity` correctly
`unlinked` after `unlink_identity`; both `CrossOrganizationTrust` rows
correctly `suspended`/`terminated`; `FederationAgreement` correctly
`active` with `signed_at` set after `sign_agreement`; `FederatedSession`
correctly attributed to the self-service account and correctly terminated.

## Failure injection (rollback proof)

Monkeypatched `AsyncSession.commit` to raise immediately after
`establish_trust`'s flush. Result: `500`, and a fresh-session query
confirmed **zero orphaned rows**. A control request after the monkeypatch
was removed returned `200` and persisted normally.

## Negative proof (authorization-focused)

Temporarily removed `require_platform_capability(...)` from
`establish_trust` and confirmed, with a freshly-seeded account holding
**zero** platform authority grants, the request flipped from `403` to
**`200`** — a real, reproducible privilege-escalation regression. Restored
`routes.py` from a pre-change backup; `md5sum` and `git diff` both
confirmed byte-identical restoration to the fixed state before
continuing.

## Regression

`pytest tests/identity/ tests/test_migrations.py
tests/test_migration_resilience.py`: **255 passed, 4 skipped** — identical
to every prior batch's baseline.

## GATE 1

- All 15 occurrences correctly classified: **yes**.
- Category-A dependency fix + missing commits applied to all 15: **yes**.
- Authorization gap on 9 mutating routes closed using only already-
  established, already-reviewed patterns (this file's own
  `federation_manage`, and the immediately-preceding batch's
  `_require_self`) — no new capability invented, no unreviewed judgment
  call: **yes**.
- Real HTTP + PostgreSQL proof, full capability/ownership matrix: **yes**.
- Failure-injection rollback proof: **yes**, zero orphaned rows.
- Negative proof on the authorization property itself, confirmed real
  regression, source restored byte-identical: **yes**.
- Regression suite: **yes**, 255 passed / 4 skipped, no change from
  baseline.

## RESULT

**VERIFIED** (sync/async defect and the discovered authorization gap both
closed). Sync/async defect count: 80 → 65 (15 closed: `federation`).
Batch 7 (`governance`, 24 occurrences, explicitly to be sub-batched to
max 8 per the directive) may now begin.

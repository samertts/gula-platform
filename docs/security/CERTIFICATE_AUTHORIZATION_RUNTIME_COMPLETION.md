# Certificate Authorization Runtime Completion

Closes the six certificate/CA/API-key operations left open by
`docs/security/NEXT_P0_P1_SECURITY_STATUS.md`'s `niam-cert-router-gap`
finding: `rotate_certificate`, `register_ca`, `generate_crl`,
`generate_api_key`, `revoke_api_key`, `rotate_api_key`.

## Phase 1 — forensics (per operation)

All six live in `app/identity/certificates/routes.py`, mounted under
`/niam/certificates` inside the `/niam` router, which applies
`_AUTH_REQUIRED = [Depends(get_current_niam_actor)]` at
`app/identity/api/router.py:50` — every request already required a valid
NIAM session before reaching any of these six. What was missing was
authorization (a platform-capability check), audit, and a working
transaction:

| Operation | Pre-fix state | Scope |
|---|---|---|
| `rotate_certificate` | No capability check, no audit, `Depends(get_db)` (sync engine + `await` on it — crashes), no commit | Platform-global |
| `register_ca` | Same shape | Platform-global |
| `generate_crl` | Same shape | Platform-global |
| `generate_api_key` | Same shape, **plus** `organization_id`/`person_id`/`enterprise_account_id`/`created_by` passed straight into FK columns with no existence check | Platform-global |
| `revoke_api_key` | Same shape | Platform-global |
| `rotate_api_key` | Same shape | Platform-global |

**Scoping determination:** all six are platform-global, identical to the
already-fixed `issue_certificate`/`revoke_certificate` siblings — Platform
Authority itself is explicitly platform-global by design
(`platform_authority/models.py`'s own docstring: "never an organization
account role and never an organization_id"), so no organization-scoping
dimension applies to any of the six. No new capability was created — all
six now require the existing `PlatformCapability.certificates_manage`.

**Fix applied** (`app/identity/certificates/{routes,services}.py`):
`require_platform_capability(actor, db, PlatformCapability.certificates_manage.value)`
+ a `CanonicalAuditService` event per operation
(`CERTIFICATE_ROTATED`, `CERTIFICATE_AUTHORITY_REGISTERED`,
`CERTIFICATE_CRL_GENERATED`, `API_KEY_GENERATED`, `API_KEY_REVOKED`,
`API_KEY_ROTATED`) + route-level `await db.commit()` + switched from the
broken `Depends(get_db)` to the real `Depends(get_niam_db)` async
dependency (also applied to the module's read-only GET routes, which
shared the identical crash — no capability change needed there, read-only).

**Incidental fix — mass assignment (Phase 2H):** `generate_api_key`
accepted a client-supplied `created_by` (and `organization_id`/
`person_id`/`enterprise_account_id`) with no existence check against the
real FK targets. A spoofed/non-existent reference crashed with a raw 500
`ForeignKeyViolation` instead of being rejected — and a real, existing
person's id could have been silently accepted as `created_by`
(attribution spoofing). Added `APIKeyService._require_existing_reference`
(one shared helper, not four duplicated checks) and a route-level
`try/except ValueError -> HTTPException(422)`.

## Phase 2/3/4 — real HTTP + PostgreSQL proof

Disposable local PostgreSQL 16 (`gula_certproof`, migrated to
`20260815_0022` then `IdentityBase.metadata.create_all()`, per this
repo's established workaround for the one known-broken
`pharmacy_drug_substitution_rules` migration) + disposable local Redis,
real JWTs via `app.security.auth.create_token`, real
`fastapi.testclient.TestClient(app)` lifespan. Full script:
`/tmp/.../scratchpad/cert_ws_proof.py` (session-scratchpad, not
committed — the results below are the durable evidence).

| Operation | A: no token | B: malformed token | C: no capability | D: wrong capability | E: correct capability | G: malformed target |
|---|---|---|---|---|---|---|
| `rotate_certificate` | 401 | 401 (+ expired-session 401) | 403 | 403 | **200**, new cert `active`, old cert `expired`/inactive | 404 |
| `register_ca` | 401 | 401 | 403 | 403 | **200** | n/a (create) |
| `generate_crl` | 401 | 401 | 403 | 403 | **200**, CA's `revoked_certificate_count` incremented | 404 |
| `generate_api_key` | 401 | 401 | 403 | 403 | **200** (+ spoofed `created_by` → **422**, not 500) | n/a (create) |
| `revoke_api_key` | 401 | 401 | 403 | 403 | **200**, persisted `status=revoked`/`is_active=false` | 404 |
| `rotate_api_key` | 401 | 401 | 403 | 403 | **200**, new key persisted, `key_hash` real SHA-256 (not plaintext) | 404 |

**H — sensitive fields:** `register_ca`'s response body never contains
`-----BEGIN...PRIVATE KEY` (only the public-key PEM, which is expected);
`private_key_encrypted` is stored via the existing canonical
`app.security.encryption.encrypt()` (Fernet), confirmed
`not ca.private_key_encrypted.startswith("-----BEGIN")` from a fresh
session. `generate_api_key`'s `raw_key` is returned exactly once (the
caller needs it) — the persisted `key_hash` is a 64-char SHA-256 digest,
never the plaintext key.

**Fresh-session persistence** (separate SQLAlchemy session, new
connection): every mutation above is durably visible after the
`TestClient` context exits — new certificate `active`, old certificate
`expired`/`is_active=false`, new CA row present with encrypted key, CRL
count incremented, revoked API key `status=revoked`, rotated API key
persisted with a real hash. Audit table (`niam_audit_entries`) shows all
six event types, every row has a non-null `uuid` and `actor_id` matching
the acting account.

**Phase 4 — transaction/rollback:** `sqlalchemy.ext.asyncio.AsyncSession.commit`
monkeypatched to raise immediately after a `register_ca` request (i.e.
after the service's `flush()` + audit `flush()`, before the route's own
`commit()`). Result: HTTP 500, and a fresh session shows **no** CA row
named `rollback-proof-ca` and **no** orphaned `CERTIFICATE_AUTHORITY_REGISTERED`
audit row for it (`audit_count_for_ca_registered` stayed at exactly 2 —
the two legitimate calls, not a third). Business state and audit state
rolled back atomically, matching the established `get_niam_db` contract
(`except Exception: await session.rollback()`).

## Regression tests

`backend/tests/identity/test_platform_authority_certificate_cluster.py` —
20 tests (deny-without-capability / succeed-with-audit-and-commit /
not-found-never-commits per operation, plus the `created_by`/
`organization_id` mass-assignment rejection tests and the
never-stores-raw-private-key test). All pass; full `tests/identity/`
suite (236 tests) re-run clean, zero regressions.

## GATE A

- All six routes have explicit authorization: **yes** (real 403 proof).
- No unauthenticated access: **yes** (real 401 proof, including expired-session).
- No capability bypass: **yes** (wrong-capability 403 proof).
- No cross-boundary access: **n/a** — platform-global by design, documented above, not fabricated an org-scope check.
- Sensitive fields protected: **yes** (H proof).
- Audit proven: **yes** (all six event types, fresh-session).
- Transaction proven: **yes** (Phase 4 rollback proof).
- Successful persistence proven: **yes**.
- Negative proofs pass: **yes**.

## RESULT

**VERIFIED.**

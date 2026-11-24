# Security Remediation Report — P0 Identity Tranche

> Scope: the source-verified P0 security fixes implemented in this bounded
> tranche. This is a **unit/integration evidence record**, not a security
> certification. No human security sign-off (D-020) exists. All changes are
> uncommitted. Synthetic fixtures only.

## 1. Verdict

| Dimension | Status |
|---|---|
| Security certification | **NOT CERTIFIED** — D-020 `PENDING_APPROVAL` |
| Release decision | **HOLD** — `FINAL_DECISION.md` md5 `effdfeaf…`, unchanged |
| Fixes implemented | NID protection (A), JWKS fail-closed (B), WebAuthn correctness (C), session revocation (D1/D2) |
| Evidence | 109 unit/integration tests pass; 231 pass / 4 skip broader regression |
| Production/runtime/E2E claim | **NONE** |
| RPO / RTO | **UNMEASURED / NOT VERIFIED** |

## 2. What was fixed (evidence-based, current source authoritative)

### 2.1 NID privacy (P0-A)
- **Canonicalization:** `backend/app/services/identity.py` now normalizes
  Arabic-Indic and Extended Arabic-Indic digits to Western digits before HMAC,
  so the same national ID produces one hash regardless of the input script.
  Family-name hashing is separated so no cross-field collision is introduced.
- **No raw NID at rest:** `governance/services/identity_persistence_service.py`
  stores only a hash; digit-bearing, letter-free identifiers are canonicalized,
  while alphanumeric legacy/synthetic references keep their historical hash
  (this preserves existing behavior — see evidence correction in
  `ACCEPTANCE_EVIDENCE.md` §2).
- **Registration parity:** `routes/register.py` uses the canonical helper for
  both hashing and duplicate detection, closing the duplicate-bypass where the
  raw NID was hashed inconsistently.
- **Lookup:** `routes/identity.py` gained a preferred POST body lookup. The
  legacy GET-with-NID-in-query path is retained but deprecated; removing it
  requires an owner-approved API contract change. NID is no longer exposed in
  new request paths.

### 2.2 OAuth2 / OIDC JWKS fail-closed (P0-B)
- `security/oauth2_provider.py` no longer publishes a successful empty JWKS.
  When no usable asymmetric key is configured, `GET /oauth2/jwks.json` returns
  **503** with no `keys` field — a relying party cannot mistake "no keys" for
  a valid key set.
- `jwks_uri` is **retained** in discovery for OIDC specification compliance;
  the endpoint itself is fail-closed. This was an explicit decision (recorded
  in `IMPLEMENTATION_BACKLOG.md` P0-B1) — the earlier plan to remove it was
  corrected because OIDC discovery clients expect the field.
- **No asymmetric key was generated.** Full OIDC activation remains
  `SECURITY_REVIEW_REQUIRED`.

### 2.3 WebAuthn / passkey correctness (P0-C)
- `shared/auth/webauthn.py`: relying-party ID and origin are env-configurable
  and validated (HTTPS required off localhost; origin host must match RP ID).
  Options serialize the challenge as strict base64url rather than Python
  `bytes` repr (`b'…'`). Typed `PublicKeyCredentialDescriptor` values are
  constructed; the webauthn 3.x `VerifiedRegistration` `transports` mismatch
  found by MyPy was fixed with `getattr`.
- `security/mfa_service.py`: challenges are namespaced (`reg` / `auth`),
  single-use via an atomic `set_if_absent` claim, expire after 300 s, and use
  the fail-closed shared security store. Store errors are **not swallowed** —
  a challenge that cannot be written or read fails the ceremony instead of
  silently proceeding with an empty challenge. Missing, expired and replayed
  challenges raise `WebAuthnError`.
- `routes/mfa.py` translates `WebAuthnError` to 4xx (400 registration / 401
  authentication); invalid challenges never register or authenticate a
  credential.
- Passkey activation still requires a security lead + domain/origin owner.

### 2.4 Session revocation on password change/reset (P0-D1/D2)
- `routes/password_reset.py::change_password` had called
  `bump_perm_version(db, current_user.id)` — the wrong signature; it raised a
  `TypeError` after writing the new hash but before commit. Fixed to the
  correct `(user, db, reason=…)` form.
- `reset_password` now revokes all active sessions via `bump_perm_version(…,
  reason="password_reset")` before commit; a stolen token no longer survives a
  password reset. A failed/invalid reset does not revoke.

## 3. Verification summary

- Combined final verification: **109 passed, 0 failed, EXIT 0** (147.64 s).
- Broader identity/auth regression: **231 passed, 4 skipped, 0 failed, EXIT 0**.
- Ruff on changed scope: no new findings (one pre-existing `RUF001` in
  `register.py:305`, untouched). MyPy clean on `shared/auth/webauthn.py`.
- Exact commands, exit codes, counts and limitations: `ACCEPTANCE_EVIDENCE.md`.

## 4. Deliberately out of scope / not fixed

- **P0-D3** — `security/session.py` raw-cache fail-open: **NOT implemented**.
  The fail-closed store is used by WebAuthn challenges (C2) only. Do not claim
  session-store hardening is complete.
- **P0-D4** — device-revocation session termination: blocked; `Device.account_id`
  is a NIAM ULID with no numeric LabUser/User mapping.
- OIDC key management, passkey activation, government ID / civil registry / NFC
  integrations, and legal interpretations: external/approval blockers.

## 5. Residual risk

- OIDC remains fail-closed and not activatable without an approved key
  management solution; there is no key rotation story yet.
- Passkeys have corrected challenge handling but no production origin/RP
  rollout or device-attestation policy was exercised.
- Environment's `python_version` target is 3.14 in `pyproject.toml`; tests were
  run on Python 3.12.13 (the repo's fixed runtime target). This is a
  configuration inconsistency to raise, not a code defect fixed here.

## 6. Honest non-claims

0 PRODUCTION_VERIFIED · 0 RUNTIME_VERIFIED · 0 E2E_VERIFIED ·
RPO/RTO UNMEASURED · F-085 open · OCR/NFC `L0` · ID Scan advisory
`needs_confirmation` · D-020/D-021 pending · HOLD unchanged.

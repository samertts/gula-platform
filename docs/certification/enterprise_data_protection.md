# Enterprise Certification — Security & Data Protection v1.0

**Platform:** GULA National Health Platform
**Date:** 2026-08-02
**Level:** Enterprise Certification (P4 program)

## Scope

Transport security, application security, data-at-rest encryption, immutable
audit, and privacy controls — live-verified.

## 1. Transport & Header Security — CERTIFIED (35/35 live)

- 9 headers verified on live responses (P4 Phase 5): nosniff,
  X-Frame-Options DENY, X-XSS-Protection, Referrer-Policy, Permissions-Policy
  (camera/mic/geolocation disabled), COOP same-origin, CSP
  (`default-src 'self'`, frame-ancestors none), Cache-Control no-store,
  HSTS in production (`middleware.py:162`).
- CORS: foreign-origin preflight emits no allow-origin (probe-verified).

## 2. Application Security — CERTIFIED

- 21 sensitive endpoints reject anonymous access (401/403) — probe sweep.
- SQLi pattern probe rejected; oversized body (100 KB) rejected; method
  confusion (PATCH on GET-only routes) rejected.
- Docs guarded behind JWT in production; `ENABLE_API_DOCS` defaults false.
- Rate limiting (auth/public), max body/upload limits, startup guard,
  error redaction, setup route disabled in production.
- 80/80 security regression tests (tokens, hashing, encryption, brute-force,
  input validation, national-ID hashing).

## 3. Data-at-Rest & Key Handling — CERTIFIED

- AES encryption module (`shared/security/encryption.py`, ValueError on
  InvalidToken); encryption-key policy (`security/encryption.py:18-22`).
- NID HMAC-hashed (deterministic, non-reversible); AUDIT_ANCHOR_KEY with
  prev-key rotation support.
- Production fail-fast on missing/weak secrets (`config.py` sys.exit).
- **P4 remediation (`e1c7486e`):** `.env.production` with live secrets was
  committed — untracked + gitignored; **rotation required** (operator
  action, `SECRET_ROTATION_PLAN.md`).

## 4. Immutable Audit Log — CERTIFIED

- SHA-256 hash chain: each entry hashes `(prev_chain_hash + record)` with
  genesis `"0"*64` (`audit_service.py:73`), HMAC-anchored file checkpoints
  every 100 entries with key rotation (`_write_anchor`), full-chain
  verification (`:121-263`).
- Chain enforced across identity audit (`identity/models/audit.py:155`),
  LIMS result audit (`lims/models.py:1083`), national security audit
  (`national/security/audit.py`), health-data governance
  (`health_data/governance/audit.py`).
- Live: `/admin/audit-logs` operational; backup verifier validates audit
  chain after restore (PROGRAM-011).

## 5. Privacy Controls — CERTIFIED

- Consent engine with expiry (72h cap), grant/revoke/check audited; ABAC
  `require_consent` dependency; break-glass emergency access with policy
  (`BREAK_GLASS_POLICY.md`); HIPAA/GDPR capability tags
  (`kernel/generate_capabilities.py:209`).
- PII minimization: national ID stored hashed; citizen portal OTP-gated.

## Verdict

**SECURITY & DATA PROTECTION: CERTIFIED v1.0** — transport, application,
data-at-rest, immutable audit chain, and privacy controls all verified live
(35/35 header+access probes, 80/80 security suite). One committed-secrets
defect remediated; secret rotation is the sole outstanding operational
obligation.

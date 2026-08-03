# OTP / TOTP Configuration — GULA Platform

*Read-only audit · generated 2026-08-02*

## 1. OTP-enabled accounts (discovered)

### 1.1 Production-relevant: P5 demo MFA roles (3 accounts)

| Role | Email | TOTP secret location | Backup codes |
|---|---|---|---|
| `auditor` | `demo.auditor@demo.local` | `/tmp/opencode/p5_mfa_secrets.json` | 8, stored SHA-256-hashed |
| `security_officer` | `demo.security_officer@demo.local` | `/tmp/opencode/p5_mfa_secrets.json` | 8, stored SHA-256-hashed |
| `pathologist` | `demo.pathologist@demo.local` | `/tmp/opencode/p5_mfa_secrets.json` | 8, stored SHA-256-hashed |

Enrolled at provisioning time by `scripts/p5_demo_users.py:91-116` (idempotent; `MFAService.setup_totp`). The **plaintext secrets are written to `/tmp/opencode/p5_mfa_secrets.json`** (`p5_demo_users.py:118-121`) — world-readable in default /tmp perms. If the store is lost, re-run `scripts/p5_demo_users.py` — it re-enrolls only when no active TOTP device exists.

### 1.2 Test-only TOTP accounts (ephemeral, runtime secrets)

| Email | Role | Secret | Source |
|---|---|---|---|
| `boss@mfa.gula` | `master_admin` | runtime `generate_totp_secret()` | `backend/tests/test_auth_infrastructure.py:433-476` |
| `audit@mfa.gula` | `auditor` | runtime `generate_totp_secret()` | `backend/tests/test_auth_infrastructure.py:515-559` |

These verify the ASVS 2.4 privileged-login MFA challenge flow (`POST /login` → `mfa_pending` → `POST /mfa-verify`); secrets never leave the test process.

### 1.3 No OTP (confirmed absent)

- Master admin bootstrap: `requires_mfa=false` — P5 script asserts no MFA pending (`p5_demo_users.py:54-56`).
- National admin accounts, demo clinical users, generator users: no TOTP devices.

## 2. Secret generation — exact logic (nothing hardcoded)

```python
# shared/auth/mfa.py:10-11
def generate_totp_secret() -> str:
    return pyotp.random_base32()          # 16-char Base32 secret

# shared/auth/mfa.py:14-15
def generate_totp_uri(secret: str, email: str, issuer: str = "GULA Health") -> str:
    return pyotp.totp.TOTP(secret).provisioning_uri(name=email, issuer_name=issuer)

# shared/auth/mfa.py:23-25  — 8 backup codes, hex(4) uppercase, hashed at rest
def generate_backup_codes(count: int = 8) -> list[str]:
    import secrets
    return [secrets.token_hex(4).upper() for _ in range(count)]

# shared/auth/mfa.py:36-37
def hash_backup_codes(codes: list[str]) -> list[str]:
    return [hashlib.sha256(c.encode()).hexdigest() for c in codes]

# backend/app/security/mfa_service.py:43-57  — enrollment transaction
secret = generate_totp_secret()
uri = generate_totp_uri(secret, email)
backup = generate_backup_codes()
device = MFADevice(user_id=..., device_type="totp", secret=secret, ...,
                   backup_codes=json.dumps(hash_backup_codes(backup)))
db.add(device); db.commit()
return {"secret": secret, "uri": uri, "backup_codes": backup, "device_id": device.id}
```

Verification: `shared/auth/mfa.py:18-20` — `pyotp.TOTP(secret).verify(token, valid_window=1)` (drift window ±1 step). Backup-code redemption consumes the code (`mfa_service.py:74-81`).

## 3. MFA enforcement model

- **Privileged roles require MFA at login** (ASVS 2.4): `master_admin`, `ministry_admin`, `organization_admin`, `directorate_admin`, `province_admin`, `lab_manager`, `lab_admin`, `hospital_admin`, `phc_admin`, `security_officer`, `auditor`, `pathologist` → `POST /login` returns `{"mfa_pending": true, "mfa_session": ...}` instead of a token.
- **Role-table-driven**: any role with `requires_mfa=True` in `authorization.roles` is challenged (`test_auth_infrastructure.py:515-559`).
- **MFA session**: single-use token, 10-minute TTL (`mfa_service.py:216-242`, `MFA_SESSION_TTL_MINUTES = 10`).
- **Rate limiting**: MFA verify endpoint rate-limited; wrong code → 400 (`test_auth_infrastructure.py:507-512`).
- **Bootstrap exception**: first admin bypasses MFA challenge when no master admin exists (`p5_demo_users.py:54-56` documents `requires_mfa=false` for the seeded master admin).
- WebAuthn/passkeys supported as alternative devices (`mfa_service.py:85-212`); not enrolled for any demo account.

## 4. OTP data at rest

| Storage | Format | Location |
|---|---|---|
| TOTP secret | plaintext Base32 | `mfa_devices.secret` column |
| Backup codes | SHA-256 hashes, JSON array | `mfa_devices.backup_codes` column |
| Demo TOTP secrets (digest) | **plaintext JSON** | `/tmp/opencode/p5_mfa_secrets.json` |
| MFA sessions | random `secrets.token_urlsafe(32)` token | `mfa_sessions` table (10-min expiry) |

Schema: `backend/app/models/mfa_device.py`; migration `backend/migrations/versions/20260716_0015_auth_security_tables.py:54`.

## 5. Findings & risks

1. **Plaintext TOTP secrets exported to `/tmp/opencode/p5_mfa_secrets.json`** — should be 0600 and excluded from any backup/CI artifact. Secrets for `demo.auditor@demo.local`, `demo.security_officer@demo.local`, `demo.pathologist@demo.local` are recoverable from this file on the dev machine.
2. Demo MFA roles are the **only real OTP-enabled accounts**; the platform master admin has **no** TOTP enrolled (bootstrap exception) — recommend enrolling one in production.
3. No OTP seeds are hardcoded in the repository source — generation is runtime-only (positive finding).
4. Backup codes are single-use and consumed atomically; stored hashed (positive finding).

## 6. Operations

```bash
# Re-enroll (idempotent) — re-runs TOTP enrollment for auditor/security_officer/pathologist
backend/.venv/bin/python scripts/p5_demo_users.py

# View demo TOTP secrets (dev machine only)
cat /tmp/opencode/p5_mfa_secrets.json

# Manual enrollment for any user via API:
#   POST /mfa/totp/setup  (device_name)  → {secret, uri, backup_codes}
#   POST /mfa/totp/verify (token)        → activates device
# Login flow for MFA users: POST /login → POST /mfa-verify {mfa_session, code}
```

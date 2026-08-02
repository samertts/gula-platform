# Demo Credentials — PROGRAM-05

For local development & certification runs. **Not for production.**

## Access

- Pattern: `demo.{role}@demo.local`
- Shared password: `Demo@2026!Pass`
- Login: `POST /login` → `{"token": "..."}` (plain roles)
- MFA roles: `POST /login` → `{"mfa_pending": true, "mfa_session": "..."}` → `POST /mfa-verify` with TOTP code

## MFA roles (TOTP)

| Role | Email | TOTP secret location |
|---|---|---|
| `auditor` | `demo.auditor@demo.local` | `/tmp/opencode/p5_mfa_secrets.json` |
| `security_officer` | `demo.security_officer@demo.local` | `/tmp/opencode/p5_mfa_secrets.json` |
| `pathologist` | `demo.pathologist@demo.local` | `/tmp/opencode/p5_mfa_secrets.json` |

TOTP enrollment performed at provisioning time (secrets stored by the provisioning script;
re-enroll if the store is lost — `scripts/p5_demo_users.py` is idempotent).

## API header

```
Authorization: Bearer <token>
```

## Fresh provisioning

```bash
cd /home/samertts/workspace/projects/gula-platform
backend/.venv/bin/python scripts/p5_demo_users.py   # idempotent
```

## Full account registry

See `demo_accounts.md` (25 roles, levels, existence state).

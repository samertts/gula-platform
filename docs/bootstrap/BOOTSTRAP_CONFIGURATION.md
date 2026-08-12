# GULA Platform — Bootstrap Configuration Reference

**Version:** 1.0 | **Last Updated:** 2026-07-23

## Environment Variables

### Bootstrap Master Switches

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_BOOTSTRAP` | `true` | Master switch — when false, no bootstrap runs |
| `ENABLE_NATIONAL_BOOTSTRAP` | `true` | Enables ministry, directorate, facility seeding |
| `ENABLE_DEMO_DATA` | `false` | Generates deterministic demo patients/orders/results |

### Country & Locale

| Variable | Default | Description |
|----------|---------|-------------|
| `BOOTSTRAP_COUNTRY` | `IQ` | ISO 3166-1 alpha-2 country code |
| `BOOTSTRAP_LANGUAGE` | `ar` | Default language code for seeded data |
| `BOOTSTRAP_TIMEZONE` | `Asia/Baghdad` | Default timezone for seeded entities |

### Master Admin Account

| Variable | Default | Description |
|----------|---------|-------------|
| `GULA_ADMIN_EMAIL` | `admin@gula-platform.org` | Master admin login email |
| `GULA_ADMIN_NAME` | `GULA Platform Admin` | Display name |
| `GULA_ADMIN_PASSWORD` | *(required)* | Plaintext password (hashed at runtime) |
| `GULA_ADMIN_PASSWORD_HASH` | — | Pre-hashed bcrypt password (takes priority) |
| `MASTER_ADMIN_NID` | — | National ID to link to master admin account |

### National Admin Accounts

All accounts are optional — they are created only when their password env var is
set. Passwords must come ONLY from environment variables, never hardcoded.

| Variable | Default Email | Purpose |
|----------|---------------|---------|
| `MINISTRY_ADMIN_EMAIL` | `ministry@gula-platform.org` | Ministry-level admin login |
| `MINISTRY_ADMIN_PASSWORD` | — | Ministry admin password |
| `MINISTRY_ADMIN_PASSWORD_HASH` | — | Pre-hashed password |
| `ORGANIZATION_ADMIN_EMAIL` | `org-admin@gula-platform.org` | Organization admin login |
| `ORGANIZATION_ADMIN_PASSWORD` | — | Organization admin password |
| `ORGANIZATION_ADMIN_PASSWORD_HASH` | — | Pre-hashed password |
| `DIRECTORATE_ADMIN_EMAIL` | `directorate-admin@gula-platform.org` | Directorate admin login |
| `DIRECTORATE_ADMIN_PASSWORD` | — | Directorate admin password |
| `DIRECTORATE_ADMIN_PASSWORD_HASH` | — | Pre-hashed password |
| `LAB_MANAGER_EMAIL` | `lab-manager@gula-platform.org` | Lab manager login |
| `LAB_MANAGER_PASSWORD` | — | Lab manager password |
| `LAB_MANAGER_PASSWORD_HASH` | — | Pre-hashed password |
| `AUDITOR_EMAIL` | `auditor@gula-platform.org` | System auditor login |
| `AUDITOR_PASSWORD` | — | Auditor password |
| `AUDITOR_PASSWORD_HASH` | — | Pre-hashed password |
| `SECURITY_OFFICER_EMAIL` | `security@gula-platform.org` | Security officer login |
| `SECURITY_OFFICER_PASSWORD` | — | Security officer password |
| `SECURITY_OFFICER_PASSWORD_HASH` | — | Pre-hashed password |

### Password Precedence

For each account, the password is resolved in this order:

1. `*_PASSWORD_HASH` env var (pre-hashed bcrypt string) — highest priority
2. `*_PASSWORD` env var (plaintext, hashed at runtime)
3. Account is **skipped** if neither is set

## .env.example Integration

All bootstrap variables are documented in `.env.example` under the sections:

```
# ── Admin Bootstrap ───────────────────────────────────────────────────────────
# ── National Bootstrap Engine ─────────────────────────────────────────────────
```

## Configuration Resolution

Bootstrap configuration is resolved at runtime by `BootstrapConfig.from_env()`
in `backend/app/core/bootstrap/config.py`. The config dataclass provides typed
access to all bootstrap settings.

## Security Rules

1. **Never hardcode passwords** in source code — always use env vars
2. **Pre-hashed passwords** should be generated with `python -c "import bcrypt; print(bcrypt.hashpw(b'password', bcrypt.gensalt()).decode())"`
3. **Password env vars** are read at boot time — changes require restart
4. **National IDs** are never stored in plaintext — HMAC-SHA256 hashed at input

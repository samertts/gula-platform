# Demo Accounts Audit — GULA Platform

*Read-only audit · generated 2026-08-02 · no files modified except this report tree*

Scope: entire repository (docs/, backend/, frontend*/ , shared/, scripts/, seed/, fixtures/, tests/, docker/, compose/, migrations/, platform/, nhop-platform/, archive/).

---

## 1. Executive Summary

| Metric | Count |
|---|---|
| Total demo / seeded / generated accounts discovered | **247+** (25 role-demo + 6 demo clinical + 1 demo admin + ~200+ generator users + 12 preview mocks + 6+ bootstrap admins + ~12 test fixtures) |
| Administrator-role accounts (master_admin / ministry / org / directorate / lab_manager / lab_admin / admin / hospital_admin / phc_admin / province_admin) | **~20** (10 P5 role-demo admins + 7 bootstrap admins + 1 generator demo admin + 2 MFA test admins) |
| Seeded users (created by code at startup / provision scripts) | **8–39** depending on env config (1 master admin + up to 6 national admins + 6 demo clinical users + 25 P5 role users) |
| OTP / TOTP-enabled accounts | **3 production-relevant** (P5 demo auditor, security_officer, pathologist) + test-only TOTP devices |
| Accounts immediately usable | P5 demo users **yes** (docs report all 25 "exists"); master admin **only if `GULA_ADMIN_PASSWORD` was configured** |
| Manual seeding required | **Yes** — every account family requires an env var or a script run (see §6) |

Hardcoded passwords in source: `Demo@2026!Pass`, `Master@2026!E2E`, `Demo@123`, `Demo@ADMIN!`, `Demo@ADMIN!` variants, plus test passwords (`password123`, `Testpass1`, `Pa55word`, `Admin@Pass123`, `Tech1234`, `TestAdmin@123`, `Ministry@123`, `OrgAdmin@123`, `DirAdmin@123`, `LabMgr@123`, `Auditor@123`, `Security@123`). Service/DB defaults: `gula_dev_2026`, `gula_default_pg_pass`, `gula:gula`, `gula_rabbit_2024`, `postgres`.

---

## 2. Account Families

### 2.1 Master Admin — startup bootstrap (A-class, most important)

| Field | Value |
|---|---|
| Username (email) | `admin@gula-platform.org` (default; env `GULA_ADMIN_EMAIL`) |
| Name | `GULA Platform Admin` / `GULA Admin` (env `GULA_ADMIN_NAME`) |
| Password | From `GULA_ADMIN_PASSWORD` (plaintext, hashed at runtime) **or** `GULA_ADMIN_PASSWORD_HASH` (bcrypt) — **no default; bootstrap skips if unset** |
| Role | `master_admin` |
| Workspace | Lab `GULA Platform` (auto-created) |
| OTP | Not enrolled by default (script expects `requires_mfa=false`) |
| Status | Created only on fresh DB when no `master_admin` exists |
| Source | `backend/app/core/bootstrap/master_admin.py:40-95` (`_ensure_master_admin`), `backend/app/core/seeds.py:46-126` (`ensure_master_admin`), config defaults `backend/app/core/bootstrap/config.py:36-38` |

**Immediately usable:** only if `GULA_ADMIN_PASSWORD` was exported at first startup. If not, no master admin exists.

### 2.2 National admin accounts — startup bootstrap (6 roles)

Created by `backend/app/core/bootstrap/users.py:19-62` (`ADMIN_ACCOUNTS`) via `seed_national_admin_accounts()`. **Skipped entirely unless the per-role password env var is set.**

| Role | Default email (env override) | Password env | Hash env |
|---|---|---|---|
| `ministry_admin` | `ministry@gula-platform.org` | `MINISTRY_ADMIN_PASSWORD` | `MINISTRY_ADMIN_PASSWORD_HASH` |
| `organization_admin` | `org-admin@gula-platform.org` | `ORGANIZATION_ADMIN_PASSWORD` | `ORGANIZATION_ADMIN_PASSWORD_HASH` |
| `directorate_admin` | `directorate-admin@gula-platform.org` | `DIRECTORATE_ADMIN_PASSWORD` | `DIRECTORATE_ADMIN_PASSWORD_HASH` |
| `lab_manager` | `lab-manager@gula-platform.org` | `LAB_MANAGER_PASSWORD` | `LAB_MANAGER_PASSWORD_HASH` |
| `auditor` | `auditor@gula-platform.org` | `AUDITOR_PASSWORD` | `AUDITOR_PASSWORD_HASH` |
| `security_officer` | `security@gula-platform.org` | `SECURITY_OFFICER_PASSWORD` | `SECURITY_OFFICER_PASSWORD_HASH` |

All in Lab `GULA Platform`; all `is_active=True`; **no OTP** by default. Source: `backend/app/core/bootstrap/users.py:101-175`. Defaults also documented in `docs/bootstrap/BOOTSTRAP_CONFIGURATION.md:27-46` and `.env.example:70-89`.

### 2.3 NIAM identity master admin (dormant async seed)

`admin@niam.gula.iq` — `Person` record only, **no credentials / no account row** (`backend/app/identity/bootstrap/seed.py:11-23`). Not usable for login. Orgs seeded: `GULA-PLATFORM` / `IRQ-MOH` (p5 script).

### 2.4 Demo clinical users — `ENABLE_DEMO_DATA=true` bootstrap

`backend/app/core/bootstrap/demo_data.py` (`seed_demo_data`), step 11 of `backend/app/core/bootstrap/bootstrap.py:105-112`.

| Account | Email | Password (hardcoded) | Role | Phone |
|---|---|---|---|---|
| Technician One | `tech1@demo.gula.iq` | `Demo@123` | `technician` | — |
| Technician Two | `tech2@demo.gula.iq` | `Demo@123` | `technician` | — |
| Technician Three | `tech3@demo.gula.iq` | `Demo@123` | `technician` | — |
| Dr. Ahmed Al-Jubouri | `doctor1@demo.gula.iq` | `Demo@123` | `doctor` | — |
| Dr. Sarah Al-Tikriti | `doctor2@demo.gula.iq` | `Demo@123` | `doctor` | — |
| Dr. Karim Al-Maliki | `doctor3@demo.gula.iq` | `Demo@123` | `doctor` | — |

Password hashed at runtime via `hash_password("Demo@123")` (`demo_data.py:114`). Plus **15 demo patients** (no login; phones `07700000001`–`07700000015`). Guard: skips if `>5` patients exist; requires an active lab. No OTP. Cleanup SQL: `DELETE FROM lab_users WHERE email LIKE '%@demo.gula.iq';` (`docs/bootstrap/BOOTSTRAP_WORKFLOW.md:122`).

### 2.5 P5 certification demo users — 25 roles (documented, idempotent)

Provisioned by `scripts/p5_demo_users.py` through the platform API (`POST /admin/users`, never direct DB):

- Pattern: `demo.{role}@demo.local` for all 25 roles (`p5_demo_users.py:35-41`).
- **Shared password: `Demo@2026!Pass`** (`p5_demo_users.py:26`).
- All assigned to `lab_id=1`.
- **MFA roles (TOTP enrolled at provisioning):** `demo.auditor@demo.local`, `demo.security_officer@demo.local`, `demo.pathologist@demo.local` (`p5_demo_users.py:32, 91-116`).
- Status per generated `docs/certification/demo_accounts.md` (2026-08-02): **all 25 "exists"**.
- Script requires live master admin login: `admin@gula-platform.org` / **`Master@2026!E2E`** (hardcoded credential — `p5_demo_users.py:24-25`).

Full 25-role table with levels: `docs/certification/demo_accounts.md:9-35` (reproduced in `DEMO_CREDENTIALS.md`).

### 2.6 National demo-data generator — 200+ users (script)

`scripts/generate_demo_data.py` (PROGRAM-DEMO-NATIONAL-001):

- **Demo admin (hardcoded):** `admin@demo.gula.iq` / `Demo@ADMIN!` — role `master_admin` (`generate_demo_data.py:617-639`).
- **Generated users:** 200+ (demo mode) or 10K+ (twin mode). Email `{role_name}.{secrets.token_hex(3)}@gula-demo.iq`; password `"Demo@" + secrets.token_hex(4).upper() + "!"` e.g. `Demo@A1B2C3D4!` (`generate_demo_data.py:279-288`).
- **Passwords written in plaintext** to `DEMO_PASSWORDS.md`, `LOGIN_MATRIX.csv` in the output dir (`generate_demo_data.py:793-801, 871-876`).
- Default DB: `postgresql://gula:gula@localhost:5432/gula_demo` (`generate_demo_data.py:17, 1219`).
- Idempotent-ish: no existence guard on users (runs against dedicated demo DB).
- **No OTP.**

### 2.7 Preview / mock frontend accounts (docs only — no credentials)

`docs/preview/TESTING_GUIDE.md:3-18` lists 12 "auto-login" mock roles (`admin@demo.gula-platform.org`, `ministry@demo.gula-platform.org`, … `citizen@demo.gula-platform.org`). These are **frontend mock-mode identities (VITE_DEMO_MODE)**, not backend accounts; no passwords exist. Historically the frontend had hardcoded demo role buttons — removed per `docs/ux-audit/ZERO_REDESIGN.md:352` and `docs/ux-audit/REDESIGN_STRATEGY.md:238`.

### 2.8 Test fixtures (backend tests only — ephemeral)

| Email | Password | Role | Source |
|---|---|---|---|
| `user{n}@test.com` | `Testpass1` | configurable | `backend/tests/conftest.py:316` (`make_lab_user`) |
| `boss@mfa.gula` | `password123` | `master_admin` + TOTP (runtime secret) | `backend/tests/test_auth_infrastructure.py:433-476` |
| `audit@mfa.gula` | `password123` | `auditor` + TOTP (runtime secret) | `backend/tests/test_auth_infrastructure.py:515-559` |
| `admin@lab.com` | `Admin@Pass123` | admin | `backend/tests/test_routes_register.py:215-216` |
| `tech@lab.com` | `Tech1234` | technician | `backend/tests/test_routes_register.py:262-263` |
| `legacy@test.local` / misc | `x` / `hash` | various | `backend/tests/unit/*` |
| `*.test.gula.iq` (7 admins) | `TestAdmin@123`, `Ministry@123`, `OrgAdmin@123`, `DirAdmin@123`, `LabMgr@123`, `Auditor@123`, `Security@123` | all admin roles | `backend/tests/test_national_bootstrap.py:38-57` |
| `Pa55word` users | `Pa55word` | various | `test_security.py`, `test_clinical_safety.py`, `test_tenant_isolation_matrix.py`, `test_concurrency_safety.py`, `test_compliance_integrity.py`, `test_chaos_survival.py`, `test_performance_budgets.py` |

All test accounts live only in the test DB and are destroyed with it.

### 2.9 Infrastructure / service default credentials (not user accounts)

| Credential | Value | Source |
|---|---|---|
| Dev PostgreSQL | `POSTGRES_PASSWORD=gula_dev_2026` (local `.env`, gitignored) | `.env:6` |
| Dev Redis | `REDIS_PASSWORD=gula_dev_2026` (local `.env`, gitignored) | `.env:7` |
| Master-admin script DB default | `postgresql://postgres:gula_default_pg_pass@localhost:5432/labdb` | `scripts/create_master_admin.py:43` |
| Demo generator DB default | `postgresql://gula:gula@localhost:5432/gula_demo` | `scripts/generate_demo_data.py:17,1219` |
| RabbitMQ (archived) | `gula:gula_rabbit_2024` | `archive/scripts/integration_test.sh:68,80` |
| Docker compose v1 (archived) | `POSTGRES_PASSWORD: ${GULA_DB_PASSWORD:-postgres}` | `archive/docker-compose.v1.yml:17` |
| CI PostgreSQL | `postgres` / `test_password` | `.github/workflows/ci.yml:111`, `nightly.yml:49` |
| Placeholders (blocked at startup) | `CHANGE_ME_*` | `.env.production:28-77`, `docs/configuration/CONFIGURATION_REFERENCE.md:425-438` |

---

## 3. Dynamic Password Generation — exact logic

```python
# scripts/generate_demo_data.py:279-280
def gen_password() -> str:
    return "Demo@" + secrets.token_hex(4).upper() + "!"
# → "Demo@" + 8 hex chars + "!"  e.g. Demo@A1B2C3D4!

# scripts/generate_demo_data.py:286-288
def gen_email(name: str, domain: str = "gula-demo.iq") -> str:
    base = name.lower().replace(" ", ".").replace("'", "")
    return f"{base}.{secrets.token_hex(3)}@{domain}"

# backend/app/core/bootstrap/demo_data.py:114  (fixed, hashed at runtime)
demo_password = hash_password("Demo@123")
```

All other demo passwords are static constants: `Demo@2026!Pass` (P5), `Demo@ADMIN!` (generator admin), `Master@2026!E2E` (P5 script's master-admin login).

TOTP secrets are **always runtime-generated**: `pyotp.random_base32()` (`shared/auth/mfa.py:11`) called from `MFAService.setup_totp` (`backend/app/security/mfa_service.py:39-57`). No OTP seed is hardcoded anywhere in source.

---

## 4. PostgreSQL insertion paths (SQL)

Raw SQL insert (only direct-SQL path found):

```sql
-- scripts/create_master_admin.py:90-95
INSERT INTO lab_users (lab_id, name, email, password_hash, role, is_active, created_at)
VALUES (:lab_id, :name, :email, :pw, 'master_admin', true, now());
-- UPDATE variant with --force (password reset): create_master_admin.py:82-88
UPDATE lab_users SET email=:email, name=:name, password_hash=:pw,
  is_active=true, perm_version=COALESCE(perm_version,1)+1 WHERE id=:id;
```

All other seeding uses SQLAlchemy ORM (`LabUser(...)` + `db.add` + `db.commit`) in `backend/app/core/bootstrap/{master_admin,users,demo_data}.py`, `backend/app/core/seeds.py`, and `scripts/generate_demo_data.py:586-627`. Supabase bootstrap (`scripts/supabase_bootstrap.sh`) runs `supabase/setup.sql` — schema/privileges only, **no user inserts**.

---

## 5. Execution commands

```bash
# 1. Master admin + national admins (startup; env-driven)
export GULA_ADMIN_PASSWORD='<strong>'            # or GULA_ADMIN_PASSWORD_HASH
export MINISTRY_ADMIN_PASSWORD=... ORGANIZATION_ADMIN_PASSWORD=...
export DIRECTORATE_ADMIN_PASSWORD=... LAB_MANAGER_PASSWORD=...
export AUDITOR_PASSWORD=... SECURITY_OFFICER_PASSWORD=...
ENABLE_BOOTSTRAP=true backend/.venv/bin/python -c "from app.core.bootstrap import run_bootstrap; run_bootstrap()"

# 2. Master admin only (interactive / forced reset)
backend/.venv/bin/python scripts/create_master_admin.py --force --email admin@gula-platform.org --password '<strong>'

# 3. Demo clinical users + patients (startup step 11)
ENABLE_DEMO_DATA=true ... # set in .env and start the app (or call seed_demo_data() directly)

# 4. P5 25-role demo users (requires running app + existing master admin with the hardcoded login)
backend/.venv/bin/python scripts/p5_demo_users.py            # idempotent; enrolls TOTP for 3 roles

# 5. National demo data generator (dedicated demo DB)
python3 scripts/generate_demo_data.py --output-dir ./demo_output
python3 scripts/generate_demo_data.py --mode twin --output-dir ./twin_output

# 6. Cleanup of demo.gula.iq users
psql "$DATABASE_URL" -c "DELETE FROM lab_users WHERE email LIKE '%@demo.gula.iq';"
```

---

## 6. Findings & Risks

1. **Hardcoded production-adjacent credentials in scripts**: `Master@2026!E2E` (`scripts/p5_demo_users.py:25`) and `Demo@2026!Pass` (`p5_demo_users.py:26`, `p5_identity_cert.py:55`). The P5 master-admin login is a live credential of the real bootstrap account.
2. **Plaintext TOTP secrets on disk**: `/tmp/opencode/p5_mfa_secrets.json` (world-readable default perms) — `p5_demo_users.py:118-121`.
3. **Plaintext password dumps**: `DEMO_PASSWORDS.md` / `LOGIN_MATRIX.csv` from the generator.
4. **Shared demo password across 25 roles** (`Demo@2026!Pass`) — single compromise exposes all roles (intended for CI only; must rotate in production).
5. **Weak dev defaults in archived/script code**: `gula_default_pg_pass`, `gula:gula`, `gula_rabbit_2024`, `POSTGRES_PASSWORD=postgres` (CI).
6. **Positive controls**: bootstrap requires explicit password env (fails closed, `seeds.py:73-78`); production hard-fails on weak secrets (`backend/app/config.py:80-105`, `docs/configuration/CONFIGURATION_REFERENCE.md:425-438`); TOTP secrets never hardcoded; `.env`/`.env.production` gitignored.

**Recommendations (not applied — read-only audit):** rotate `Master@2026!E2E` and `Demo@2026!Pass` before any production deploy; protect `/tmp/opencode/p5_mfa_secrets.json`; source P5 script credentials from env vars.

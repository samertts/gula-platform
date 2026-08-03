# Demo Credentials — GULA Platform

*Read-only credential registry · generated 2026-08-02 · verified against source files*

> **WARNING: All credentials below are for local development / CI / certification ONLY. Production deployments must rotate every one of them.**

## 1. Primary demo credentials (P5 certification — 25 roles)

Pattern: `demo.{role}@demo.local` · Shared password: **`Demo@2026!Pass`** · Lab: `lab_id=1`
Provisioner: `scripts/p5_demo_users.py` (idempotent, API-only) · Status per `docs/certification/demo_accounts.md` (2026-08-02): all exist.

| Role | Level | Email | OTP | Status |
|---|---|---|---|---|
| `master_admin` | 100 | `demo.master_admin@demo.local` | no | exists |
| `ministry_admin` | 90 | `demo.ministry_admin@demo.local` | no | exists |
| `organization_admin` | 85 | `demo.organization_admin@demo.local` | no | exists |
| `directorate_admin` | 80 | `demo.directorate_admin@demo.local` | no | exists |
| `province_admin` | 80 | `demo.province_admin@demo.local` | no | exists |
| `auditor` | 70 | `demo.auditor@demo.local` | **TOTP** | exists |
| `security_officer` | 70 | `demo.security_officer@demo.local` | **TOTP** | exists |
| `hospital_admin` | 60 | `demo.hospital_admin@demo.local` | no | exists |
| `phc_admin` | 55 | `demo.phc_admin@demo.local` | no | exists |
| `lab_manager` | 50 | `demo.lab_manager@demo.local` | no | exists |
| `admin` | 50 | `demo.admin@demo.local` | no | exists |
| `lab_admin` | 50 | `demo.lab_admin@demo.local` | no | exists |
| `lab_supervisor` | 45 | `demo.lab_supervisor@demo.local` | no | exists |
| `quality_manager` | 45 | `demo.quality_manager@demo.local` | no | exists |
| `pathologist` | 40 | `demo.pathologist@demo.local` | **TOTP** | exists |
| `doctor` | 35 | `demo.doctor@demo.local` | no | exists |
| `technician` | 30 | `demo.technician@demo.local` | no | exists |
| `nurse` | 25 | `demo.nurse@demo.local` | no | exists |
| `receptionist` | 20 | `demo.receptionist@demo.local` | no | exists |
| `cashier` | 20 | `demo.cashier@demo.local` | no | exists |
| `staff` | 20 | `demo.staff@demo.local` | no | exists |
| `lab_staff` | 20 | `demo.lab_staff@demo.local` | no | exists |
| `api_client` | 5 | `demo.api_client@demo.local` | no | exists |
| `patient` | 10 | `demo.patient@demo.local` | no | exists |
| `citizen` | 10 | `demo.citizen@demo.local` | no | exists |

## 2. Bootstrap accounts (env-driven; no default passwords)

| Role | Email (default) | Password source | Default password |
|---|---|---|---|
| `master_admin` | `admin@gula-platform.org` | `GULA_ADMIN_PASSWORD` / `GULA_ADMIN_PASSWORD_HASH` | **none — skip if unset** |
| `ministry_admin` | `ministry@gula-platform.org` | `MINISTRY_ADMIN_PASSWORD` / `_HASH` | **none — skip if unset** |
| `organization_admin` | `org-admin@gula-platform.org` | `ORGANIZATION_ADMIN_PASSWORD` / `_HASH` | **none — skip if unset** |
| `directorate_admin` | `directorate-admin@gula-platform.org` | `DIRECTORATE_ADMIN_PASSWORD` / `_HASH` | **none — skip if unset** |
| `lab_manager` | `lab-manager@gula-platform.org` | `LAB_MANAGER_PASSWORD` / `_HASH` | **none — skip if unset** |
| `auditor` | `auditor@gula-platform.org` | `AUDITOR_PASSWORD` / `_HASH` | **none — skip if unset** |
| `security_officer` | `security@gula-platform.org` | `SECURITY_OFFICER_PASSWORD` / `_HASH` | **none — skip if unset** |

Sources: `backend/app/core/bootstrap/users.py:19-62`, `backend/app/core/bootstrap/config.py:36-52`, `backend/app/core/seeds.py:46-126`.

## 3. Demo clinical users (`ENABLE_DEMO_DATA=true`)

| Name | Email | Password | Role |
|---|---|---|---|
| Technician One | `tech1@demo.gula.iq` | `Demo@123` | technician |
| Technician Two | `tech2@demo.gula.iq` | `Demo@123` | technician |
| Technician Three | `tech3@demo.gula.iq` | `Demo@123` | technician |
| Dr. Ahmed Al-Jubouri | `doctor1@demo.gula.iq` | `Demo@123` | doctor |
| Dr. Sarah Al-Tikriti | `doctor2@demo.gula.iq` | `Demo@123` | doctor |
| Dr. Karim Al-Maliki | `doctor3@demo.gula.iq` | `Demo@123` | doctor |

Source: `backend/app/core/bootstrap/demo_data.py:46-56, 114-143`. No OTP. Phone: none (LabUser has no phone column).

## 4. National demo-data generator

| Account | Credentials | Notes |
|---|---|---|
| Demo Admin | `admin@demo.gula.iq` / **`Demo@ADMIN!`** | `master_admin`, hardcoded `scripts/generate_demo_data.py:617-623` |
| ~200–10K generated users | email `{name}.{6-hex}@gula-demo.iq`; password **`Demo@` + `secrets.token_hex(4).upper()` + `!`** (e.g. `Demo@A1B2C3D4!`) | plaintext dump in `DEMO_PASSWORDS.md` + `LOGIN_MATRIX.csv` |

## 5. Hardcoded credentials in scripts (elevated risk)

| Credential | Value | Location |
|---|---|---|
| Master admin login used by P5 provisioner | `admin@gula-platform.org` / **`Master@2026!E2E`** | `scripts/p5_demo_users.py:24-25` |
| P5 identity cert password | `Demo@2026!Pass` | `scripts/p5_identity_cert.py:55` |
| create_master_admin DB default | `postgresql://postgres:gula_default_pg_pass@localhost:5432/labdb` | `scripts/create_master_admin.py:43` |
| Generator DB default | `postgresql://gula:gula@localhost:5432/gula_demo` | `scripts/generate_demo_data.py:17,1219` |
| RabbitMQ (archived) | `gula:gula_rabbit_2024` | `archive/scripts/integration_test.sh:68,80` |
| Dev Postgres/Redis (local `.env`, gitignored) | `gula_dev_2026` | `.env:6-7` |
| CI Postgres | `postgres` / `test_password` | `.github/workflows/ci.yml:111`, `nightly.yml:49` |

## 6. Test-fixture credentials (ephemeral; test DB only)

`Testpass1` (conftest `make_lab_user`), `password123` (MFA tests `boss@mfa.gula`, `audit@mfa.gula`), `Admin@Pass123` / `Tech1234` (`test_routes_register.py`), `Pa55word` (security/safety suites), `TestAdmin@123` / `Ministry@123` / `OrgAdmin@123` / `DirAdmin@123` / `LabMgr@123` / `Auditor@123` / `Security@123` (`test_national_bootstrap.py:38-57`, emails `*@test.gula.iq`).

## 7. Preview mock identities (no passwords — frontend mock only)

`admin@demo.gula-platform.org`, `ministry@demo.gula-platform.org`, `directorate@demo.gula-platform.org`, `hospital@demo.gula-platform.org`, `lab.manager@demo.gula-platform.org`, `lab.tech@demo.gula-platform.org`, `doctor@demo.gula-platform.org`, `pharmacist@demo.gula-platform.org`, `nurse@demo.gula-platform.org`, `reception@demo.gula-platform.org`, `auditor@demo.gula-platform.org`, `citizen@demo.gula-platform.org` — source `docs/preview/TESTING_GUIDE.md:3-18`; auto-login mock, no credentials exist.

## 8. Password-generation recipes

```python
# scripts/generate_demo_data.py:279-280
def gen_password() -> str:
    return "Demo@" + secrets.token_hex(4).upper() + "!"   # Demo@<8 hex>!

# backend/app/core/bootstrap/demo_data.py:114
demo_password = hash_password("Demo@123")                 # static, bcrypt at runtime
```

## 9. Provisioning commands

```bash
# P5 role users (25 accounts; needs live app + master admin with hardcoded login)
backend/.venv/bin/python scripts/p5_demo_users.py

# National demo generator (dedicated demo DB; default postgresql://gula:gula@localhost:5432/gula_demo)
python3 scripts/generate_demo_data.py [--mode twin] [--output-dir ./demo_output]

# Master admin (env-driven bootstrap)
export GULA_ADMIN_PASSWORD='<strong>'; ENABLE_BOOTSTRAP=true <start app>

# Master admin reset (interactive)
backend/.venv/bin/python scripts/create_master_admin.py --force

# Remove demo clinical users
psql "$DATABASE_URL" -c "DELETE FROM lab_users WHERE email LIKE '%@demo.gula.iq';"
```

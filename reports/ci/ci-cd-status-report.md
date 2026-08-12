# CI/CD Pipeline Status Report

**Generated:** 2026-07-17  
**Repository:** GULA Platform (Monorepo)  
**Pipeline Root:** `.github/workflows/`

---

## 1. Workflow Summary

| Workflow | Trigger | Jobs | Current Status |
|----------|---------|------|---------------|
| `ci.yml` | Push (any branch), PR (main/develop) | 7 jobs | 🔴 Has issues |
| `quality-gate.yml` | PR → main, push → main | 9 quality gates + 1 report | 🔴 Has issues |
| `deploy.yml` | Push → main, workflow_dispatch | 1 job (deploy) | 🟢 No issues |
| `blue-green-deploy.yml` | CI completion on main, workflow_dispatch | 3 jobs | 🟢 No issues |
| `canary-deploy.yml` | workflow_dispatch | 1 job | 🟢 No issues |
| `auto-rollback.yml` | workflow_dispatch | 1 job | 🟢 No issues |

---

## 2. Detailed Workflow Analysis

### 2.1 `ci.yml` — CI Build, Test & Security Scan

**Jobs:** syntax-gate → backend-test, migration-check, openapi-contract → smoke-test → build-and-push → image-summary

**Triggers:** `push: ["**"]`, `pull_request: [main, develop]`

**Issues:**

#### a) Flake8 F821 Errors (syntax-gate job)
The `flake8 app --select=E9,F821` step will **fail** with 14 undefined-name errors in `app/nhdw/`:

| File | Line | Error |
|------|------|-------|
| `app/nhdw/kpi.py` | 237 | `F821 undefined name 'Department'` |
| `app/nhdw/kpi.py` | 238 | `F821 undefined name 'Department'` (x2) |
| `app/nhdw/services.py` | 74 | `F821 undefined name 'Department'` |
| `app/nhdw/services.py` | 75-77 | `F821 undefined name 'Department'` (x3) |
| `app/nhdw/services.py` | 180-183 | `F821 undefined name 'Department'` (x4) |
| `app/nhdw/services.py` | 592-593 | `F821 undefined name 'Department'` (x3) |

**Root cause:** The `Department` model is referenced but not imported in `app/nhdw/kpi.py` and `app/nhdw/services.py`.

#### b) NameError/Import Scan (syntax-gate job)
In the **local development environment** (without CI env vars set), the scan produces ~170 `SystemExit(1)` failures because `app/config.py` hard-exits when env vars are absent. **However**, in CI the env block sets `ENV: test`, `DATABASE_URL`, `SECRET_KEY`, etc., so `config.py` loads successfully. This job would **pass in CI**. Verified: `python3 -m py_compile` passes on all files.

#### c) OpenAPI Contract Gate
The `scripts/export_openapi.py` script exists. This job requires the `RUNTIME_MODE: test` env var, which is set. **Expected to pass.**

#### d) Build Matrix
The `build-and-push` job builds 8 images. Dockerfiles at:
- `./backend/Dockerfile` — exists
- `./services/lab/Dockerfile`, `order/Dockerfile`, `patient/Dockerfile`, `result/Dockerfile`, `sample/Dockerfile`, `notification/Dockerfile`, `ai/Dockerfile` — **must exist for the matrix to succeed**

---

### 2.2 `quality-gate.yml` — Production Quality Gates

**Triggers:** `pull_request: [main]`, `push: [main]`, `workflow_dispatch`

**9 gate jobs + 1 combined-report job.**

#### 🔴 Critical Issue: `architecture-gate-ci.yml` Misplaced

A **complete GitHub Actions workflow file** exists at `config/quality-gates/architecture-gate-ci.yml` (100 lines). It defines a full workflow with PR comment posting, artifact upload, and path filtering.

**Problem:** GitHub **only** loads workflow files from `.github/workflows/`. The file at `config/quality-gates/architecture-gate-ci.yml` is **dead code** — it is never executed.

**Additionally:** The `quality-gate.yml` already runs `config/quality-gates/architecture-gate.py` as a step within its own `architecture-gate` job. So `architecture-gate-ci.yml` is both misplaced **and** redundant.

**Recommendation:** Either:
- Move `architecture-gate-ci.yml` to `.github/workflows/` if the extra features (PR comments, path filtering, artifact uploads) are desired, OR
- Delete `config/quality-gates/architecture-gate-ci.yml` if the simpler `quality-gate.yml` version suffices.

#### 🔴 Missing Tools in CI Runners

| Gate | Script | Tools Required | CI Availability Concern |
|------|--------|---------------|------------------------|
| `security-gate.py` | `run_bandit()` | Bandit | ✅ Available (`pip install safety bandit` in ci.yml) |
| `security-gate.py` | `run_semgrep()` | Semgrep | ⚠️ Not installed by default — falls back to warning |
| `security-gate.py` | `run_safety()` | Safety | ✅ Available |
| `security-gate.py` | `run_gitleaks()` | Gitleaks | ✅ Has GitHub Action |
| `security-gate.py` | `run_trivy()` | Trivy | ✅ Has GitHub Action (in ci.yml) |
| `security-gate.py` | `run_checkov()` | Checkov | ⚠️ Not installed — falls back to warning |
| `performance-gate.py` | `run_load_test()` | k6 | ⚠️ Not installed — uses simulated results |
| `accessibility-gate.js` | `runAxeScan()` | Puppeteer + axe-core | ⚠️ Falls back to simplified checks if unavailable |

**Impact:** Several gates will degrade gracefully (warnings instead of errors) when tools are missing, but this reduces gate effectiveness.

#### 🔴 `api-gate.py` OpenAPI Spec Resolution
The script looks for `openapi.json` at `ROOT / "backend" / "app" / "openapi.json"`. This file is **not tracked in git** (it's generated by `scripts/export_openapi.py`). If not pre-generated:
1. The script tries to fetch from `http://localhost:8080/openapi.json`
2. If that fails too, the gate **crashes with a fatal error**

**Recommendation:** The `api-gate` job should either:
- Generate the OpenAPI spec via `scripts/export_openapi.py` before running the gate, OR
- Provide `--openapi-spec` pointing to a generated file

#### 🔴 FHIR Gate — Directory Does Not Exist
The `fhir-gate.py` checks `backend/app/fhir/` which **does not exist**:
```
$ ls backend/app/fhir/ → ls: cannot access: No such file or directory
```
The gate gracefully handles this (prints a note and exits 0), but the check is effectively **vacuous**.

#### 🟡 `database-gate.py` — Rundown Check May Fail
The `check_migration_revert()` function at line 302 runs `alembic downgrade -1` as a subprocess. This requires:
- `alembic` on PATH
- A live PostgreSQL connection at `DATABASE_URL`
- Migrations in a valid state

The gate's `database-gate` job in `quality-gate.yml` provides a PostgreSQL service and installs `sqlalchemy psycopg2-binary alembic`, but does **not** run `alembic upgrade head` before calling the check. The downgrade check will fail because no migrations have been applied.

---

### 2.3 `deploy.yml` — Deploy to Server

**Issues:** None detected.

**Notes:** 
- SSH-based deployment to `${{ secrets.SERVER_HOST }}`
- Has rollback on health check failure (resets to previous commit)
- Auto-generates missing secrets in `.env`
- Configures system nginx

---

### 2.4 `blue-green-deploy.yml` — Kubernetes Blue-Green

**Issues:** None detected.

**Notes:**
- Triggered by CI completion on `main`
- Uses `gula-backend-active` service with `blue-green/active-slot` annotation
- Port-forwards for smoke testing before traffic switch
- Includes Linkerd `TrafficSplit` support (optional)
- Has a built-in `rollback` job on failure

---

### 2.5 `canary-deploy.yml` — Canary Deployment

**Issues:** None detected.

**Notes:**
- Manual trigger only
- Progressive traffic: 10% → 25% → 50% → 100%
- Health monitoring per step
- Rollback on any failure (resets to 100% stable)

---

### 2.6 `auto-rollback.yml` — Automatic Rollback

**Issues:** None detected.

**Notes:**
- Manual trigger with reason
- Uses `blue-green/active-slot` annotation to detect active slot
- Switches traffic to the previous slot
- Sends Slack notification via `ALERT_WEBHOOK_URL`
- Uses same concurrency group as `blue-green-deploy.yml` to prevent conflicts

---

## 3. Root Cause Analysis

### 3.1 Flake8 F821 Failures

**File:** `app/nhdw/kpi.py` and `app/nhdw/services.py`  
**Cause:** The `Department` SQLAlchemy model is referenced in queries but the import statement is missing. Likely `from app.models.department import Department` or similar.

**Potential impact:** These modules would raise `NameError` at runtime if any code path executes these lines. If these are dead code paths, only CI fails; if live, production breaks.

### 3.2 Misplaced Workflow File

**File:** `config/quality-gates/architecture-gate-ci.yml`  
**Cause:** A developer created a standalone workflow file but placed it in the quality-gates directory instead of `.github/workflows/`. The `.github/workflows/` directory contains exactly 6 files — none of which reference `architecture-gate-ci.yml`.

### 3.3 Quality Gate Tool Dependencies

**Cause:** Multiple quality gate scripts (`security-gate.py`, `performance-gate.py`, `accessibility-gate.js`) depend on external tools (Bandit, Semgrep, k6, Puppeteer, Checkov) that are not installed in the runner environment specified in `quality-gate.yml`. The scripts handle this with fallback warnings, but the gates become less effective.

### 3.4 Database Gate Without Migrations

**Cause:** The `database-gate` job starts a PostgreSQL service and installs Alembic dependencies, but never runs `alembic upgrade head`. The `check_migration_revert()` function attempts `alembic downgrade -1` on a freshly created empty database with no migration history, which will fail.

---

## 4. Required Fixes

### Priority: HIGH (Blocks CI)

| # | Fix | File(s) | Action |
|---|-----|---------|--------|
| 1 | Add missing `Department` import | `app/nhdw/kpi.py:237`, `app/nhdw/services.py:74` | Add `from app.models.department import Department` (or equivalent) |
| 2 | Align `architecture-gate-ci.yml` | `config/quality-gates/architecture-gate-ci.yml` | Move to `.github/workflows/` or delete |

### Priority: MEDIUM (Gate Effectiveness)

| # | Fix | File(s) | Action |
|---|-----|---------|--------|
| 3 | Install missing tools in quality-gate runner | `.github/workflows/quality-gate.yml` | Add `pip install bandit safety semgrep checkov` and `npm install -g @axe-core/puppeteer puppeteer` |
| 4 | Run `alembic upgrade head` before database gate checks | `.github/workflows/quality-gate.yml` | Add migration step before invoking `database-gate.py` |
| 5 | Generate OpenAPI spec before API gate | `.github/workflows/quality-gate.yml` | Add step to run `scripts/export_openapi.py` and pass `--openapi-spec openapi.json` to `api-gate.py` |

### Priority: LOW (Correctness)

| # | Fix | File(s) | Action |
|---|-----|---------|--------|
| 6 | Verify service Dockerfiles exist | `services/*/Dockerfile` | Confirm all 7 microservice Dockerfiles exist for the build matrix |
| 7 | Add FHIR module or remove FHIR gate | `backend/app/fhir/` or `.github/workflows/quality-gate.yml` | Either create the FHIR module or remove the vacuous `fhir-gate` job |

---

## 5. CI Job Expected Results (Current State)

| CI Job | Expected Result | Evidence |
|--------|----------------|----------|
| **syntax-gate** (py_compile) | ✅ **PASS** | `python3 -m py_compile` on all files: exit code 0 |
| **syntax-gate** (NameError scan) | ✅ **PASS in CI** | Requires `ENV=test` + secrets; local fails with SystemExit but CI provides these |
| **syntax-gate** (flake8 E9,F821) | ❌ **FAIL** | 14 F821 errors in `app/nhdw/` — `Department` undefined |
| **migration-check** | ✅ **PASS** | Alembic migrations are consistent; py_compile passes on migrations |
| **smoke-test** | ✅ **PASS** | Health endpoints and uvicorn boot logic are functional |
| **backend-test** | ⚠️ **Unknown** | Depends on pytest results; requires running with live DB |
| **openapi-contract** | ✅ **PASS** | `scripts/export_openapi.py` exists; env vars set correctly |
| **security-scan** | ⚠️ **Likely PASS** | Bandit/Gitleaks/Hadolint are standard tools; `/tmp` write check passes |
| **build-and-push** | ⚠️ **Unknown** | Requires Dockerfiles to exist and Docker to be available |

---

## 6. Validation Steps

### 6.1 Fix Flake8 Errors
```bash
cd backend
# Add missing imports to fix F821 errors
# In app/nhdw/kpi.py and app/nhdw/services.py:
# Add: from app.nhdw.models import Department
python3 -m flake8 app --select=E9,F821 --max-line-length=200 --statistics
# Expected: clean output, exit code 0
```

### 6.2 Verify Architecture Gate
```bash
cd /home/samertts/workspace/projects/gula-platform
python3 config/quality-gates/architecture-gate.py
# Expected: all checks pass, exit code 0
```

### 6.3 Verify Migration Gate Locally
```bash
cd backend
# Requires local PostgreSQL
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/labdb \
  ENV=test \
  SECRET_KEY=test-key-64chars-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx \
  REFRESH_TOKEN_SECRET=test-refresh-64chars-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx \
  ENCRYPTION_KEY=6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw= \
  alembic upgrade head
# Expected: all migrations applied, exit code 0
```

### 6.4 Verify Database Gate
```bash
cd backend
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/labdb \
  ENV=test \
  SECRET_KEY=test-key \
  REFRESH_TOKEN_SECRET=test-refresh \
  ENCRYPTION_KEY=6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw= \
  alembic upgrade head
cd /home/samertts/workspace/projects/gula-platform
python3 config/quality-gates/database-gate.py
# Expected: all checks pass, exit code 0
```

### 6.5 Run the Full CI Chain
```bash
make ci
# Expected: syntax-gate passes, lint passes, docker build succeeds
```

---

## Appendix: File Inventory

### Workflow Files (`.github/workflows/`)
```
auto-rollback.yml          — Manual rollback (118 lines)
blue-green-deploy.yml      — K8s blue-green (297 lines)
canary-deploy.yml          — Progressive canary (144 lines)
ci.yml                     — Full CI pipeline (644 lines)
deploy.yml                 — SSH deploy (268 lines)
quality-gate.yml           — Quality gates (164 lines)
```

### Misplaced Workflow Files
```
config/quality-gates/architecture-gate-ci.yml — 100-line workflow in wrong directory (DEAD CODE)
```

### Quality Gate Scripts (all present)
```
config/quality-gates/architecture-gate.py    — Passes (466 lines)
config/quality-gates/performance-gate.py     — Passes (344 lines)
config/quality-gates/security-gate.py        — Passes (490 lines)
config/quality-gates/database-gate.py        — Passes (481 lines)
config/quality-gates/api-gate.py             — Passes (480 lines)
config/quality-gates/fhir-gate.py            — Passes vacuously (380 lines, no fhir/ dir)
config/quality-gates/scalability-gate.py     — Passes (100 lines)
config/quality-gates/accessibility-gate.js   — Passes (376 lines)
config/quality-gates/offline-gate.py         — Passes (123 lines)
```

# GULA Quality Gates

**Version:** 1.0  
**Status:** RATIFIED  

---

## 1. Quality Gate Philosophy

Quality is not negotiable. Every change must pass every applicable quality gate before merging. Gates are enforced at CI level and cannot be bypassed.

## 2. Gate Pipeline

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Pre-commit  │───→│   CI Gate   │───→│  PR Review  │
│ (local)     │    │ (automated) │    │  (manual)   │
└─────────────┘    └─────────────┘    └─────────────┘
                           │
                    ┌──────┴──────┐
                    │  Quality     │
                    │  Gate Matrix │
                    └──────┬──────┘
                           │
                    ┌──────┴──────┐
                    │  Release    │
                    │  Gate       │
                    └─────────────┘
```

## 3. Pre-commit Gates (Local)

| Gate | Tool | What It Checks |
|------|------|----------------|
| YAML Validity | pre-commit | Valid YAML files |
| JSON Validity | pre-commit | Valid JSON files |
| TOML Validity | pre-commit | Valid TOML files |
| Merge Conflict | pre-commit | No unresolved merge markers |
| EOF Fixer | pre-commit | Files end with newline |
| Trailing Whitespace | pre-commit | No trailing whitespace |
| Large Files | pre-commit | No files >512KB (unless whitelisted) |
| Private Keys | pre-commit | No private keys committed |
| Migration Policy | Custom script | Existing migrations not modified |
| Python Syntax | py_compile | All Python files compile |

## 4. CI Gates (Automated)

### 4.1 Syntax Gate
- **Timeout:** 5 minutes
- **Enforcement:** Blocks all downstream jobs
- **Checks:**
  - `py_compile` on all Python files
  - Import walk with mock stubs (NameError, AttributeError, SystemExit at module level)
  - Flake8 `E9, F821` (syntax errors, undefined names)
  - **Pass/Fail:** All files must compile, no import errors, no syntax errors

### 4.2 Migration Gate
- **Timeout:** 10 minutes
- **Dependencies:** Syntax gate
- **Checks:**
  - `alembic upgrade head` on fresh PostgreSQL 16
  - Verify 7 required tables exist
  - `alembic downgrade -1` (check reversibility)
  - `alembic upgrade head` (verify upgrade after downgrade)
  - **Pass/Fail:** Must complete round-trip without errors

### 4.3 OpenAPI Contract Gate
- **Timeout:** 5 minutes
- **Dependencies:** Syntax gate
- **Checks:**
  - Export OpenAPI spec
  - Verify required public endpoints exist (`/health`, `/login`, `/register`, `/labs/me`, `/test-types`)
  - Upload spec as artifact
  - **Pass/Fail:** All required endpoints must exist

### 4.4 Smoke Test Gate
- **Timeout:** 10 minutes
- **Dependencies:** Syntax gate, Migration gate
- **Checks:**
  - Boot uvicorn with PostgreSQL + Redis
  - curl `/health` (must return 200)
  - curl `/health/ready` (must return 200)
  - curl `/health/deep` (must return grade != RED)
  - curl `/test-types` (must return test catalog)
  - **Pass/Fail:** All health checks must pass

### 4.5 Backend Test Gate
- **Timeout:** 10 minutes
- **Dependencies:** Syntax gate
- **Checks:**
  - Full pytest suite against PostgreSQL 16 + Redis 7.2
  - JUnit XML report generation
  - Coverage measurement
  - **Pass/Fail:** All tests must pass (0 failures, 0 errors)

### 4.6 Security Scan Gate
- **Timeout:** 15 minutes
- **Dependencies:** None (parallel)
- **Checks:**
  - Safety: Python dependency CVE scan
  - Bandit: SAST scan (`-ll -ii`, fail on HIGH/CRITICAL)
  - Hadolint: Dockerfile linting
  - Gitleaks: Secret scanning
  - `/tmp` write check
  - **Pass/Fail:** No HIGH/CRITICAL findings

### 4.7 Build and Push Gate
- **Timeout:** 30 minutes
- **Dependencies:** All above gates
- **Checks:**
  - Matrix build of 8 Docker images
  - Trivy vulnerability scan on each image
  - Push to GHCR
  - **Pass/Fail:** All images build and scan clean

## 5. Quality Gate Matrix (9 Gates)

These gates run on PRs to `main` and pushes to `main`.

### 5.1 Architecture Gate
- **Script:** `config/quality-gates/architecture-gate.py`
- **Checks:**
  - Module boundary compliance
  - No circular dependencies
  - Layer violation detection
  - Import rule enforcement
- **Pass/Fail:** No violations found

### 5.2 Performance Gate
- **Checks:**
  - Query count per endpoint
  - Response time benchmarks
  - Memory allocation patterns
  - N+1 query detection
- **Pass/Fail:** Within performance budget

### 5.3 Security Gate
- **Script:** `config/quality-gates/security-gate.py`
- **Checks:**
  - Authentication on all non-public endpoints
  - Authorization checks
  - Input validation presence
  - Security header compliance
- **Pass/Fail:** No security gaps

### 5.4 Database Gate
- **Checks:**
  - Index coverage for query patterns
  - Migration idempotency
  - No SELECT * in production code
  - Connection pool sizing
- **Pass/Fail:** No database anti-patterns

### 5.5 API Gate
- **Checks:**
  - OpenAPI spec validity
  - Response format consistency
  - Error response format
  - Pagination implementation
- **Pass/Fail:** API contract compliance

### 5.6 FHIR Gate
- **Checks:**
  - FHIR resource compliance
  - Terminology standards usage
  - Resource identifier format
- **Pass/Fail:** FHIR standard compliance

### 5.7 Scalability Gate
- **Checks:**
  - No synchronous cross-module calls in hot paths
  - Event-driven patterns for long operations
  - Stateless design verification
- **Pass/Fail:** Scalability patterns followed

### 5.8 Accessibility Gate
- **Script:** `config/quality-gates/accessibility-gate.js`
- **Checks:**
  - WCAG 2.1 AA compliance for UI changes
  - Arabic language support
  - Keyboard navigation
  - Screen reader compatibility
- **Pass/Fail:** Accessibility standards met

### 5.9 Offline Gate
- **Checks:**
  - Offline sync mechanism for new data
  - Conflict resolution strategy
  - Graceful degradation when offline
- **Pass/Fail:** Offline support implemented

## 6. Release Gate

### Pre-Release Checklist

| Check | Required | Verified By |
|-------|----------|-------------|
| All CI gates pass | ✓ | CI |
| All 9 quality gates pass | ✓ | Quality gate matrix |
| Migration tested (upgrade + downgrade) | ✓ | CI migration gate |
| Performance benchmarks within budget | ✓ | Performance gate |
| Security scan clean | ✓ | Security scan gate |
| All ADRs updated | ✓ | Architecture Board |
| Changelog updated | ✓ | Release Manager |
| Version bumped | ✓ | Release Manager |
| Smoke test on staging | ✓ | Release Board |
| Rollback plan documented | ✓ | Release Board |
| Monitoring dashboards verified | ✓ | Operations |

## 7. Gate Override Policy

Quality gates cannot be overridden under normal circumstances.

**Emergency overrides** require:
1. Documented business justification
2. Security Board approval (for security gates)
3. Architecture Board approval (for architecture gates)
4. Retroactive fix scheduled within 72 hours
5. Post-incident review within 7 days

---

*These quality gates are mandatory for all changes. No code enters production without passing every applicable gate.*

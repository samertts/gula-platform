# GULA Platform Quality Gate Rules

> Version 1.0 | Last Updated: 2026-07-17
> Total Rules: 56 | Mandatory: 38 | Advisory: 18

---

## Architecture Gates (10 rules)

### ARCH-001: No Layer Violations
- **Gate**: Architecture Layer Compliance
- **Description**: Ensure that imports respect architectural layers: routes → services → models/repositories. Routes must not directly import models, services must not import route modules.
- **Check Logic**:
  ```
  FOR each .py file IN backend/app/routes/:
      EXTRACT all imports
      IF any import targets backend/app/models/ OR backend/app/database.py DIRECTLY:
          FAIL — route files must only import from services/ or security/
  
  FOR each .py file IN backend/app/services/:
      EXTRACT all imports
      IF any import targets backend/app/routes/:
          FAIL — services must not import routes (circular dependency risk)
  
  FOR each .py file IN backend/app/:
      IF any import targets services/device_bridge/:
          FAIL — monolith must not import from microservice stubs
  ```
- **Mandatory**: Yes
- **Threshold**: Zero violations
- **Failure Action**: BLOCK
- **Remediation**: Refactor routes to go through service layer. Move direct model imports to service calls.
- **Owner**: Platform Engineering
- **Last Updated**: 2026-07-17

---

### ARCH-002: No Circular Dependencies
- **Gate**: Dependency Graph Integrity
- **Description**: Detect circular import chains between modules. Use import graph analysis to identify cycles.
- **Check Logic**:
  ```
  BUILD import dependency graph from all Python files in backend/app/
  RUN Tarjan's SCC algorithm on directed graph
  FOR each strongly connected component with size > 1:
      IF cycle involves routes, services, models, OR core modules:
          FAIL
  
  SPECIAL CASE: Check app/main.py doesn't create circular import with any route module
  SPECIAL CASE: Check database.py doesn't import from any route or service module
  ```
- **Mandatory**: Yes
- **Threshold**: Zero circular dependencies
- **Failure Action**: BLOCK
- **Remediation**: Extract shared code into a separate module that both can import. Use dependency injection to break cycles. Move types to a shared `schemas.py` or `types.py`.
- **Owner**: Platform Engineering
- **Last Updated**: 2026-07-17

---

### ARCH-003: Monolith Boundary Respect
- **Gate**: Monolith Decomposition Boundary
- **Description**: Business logic must be in `backend/app/` not in top-level `services/` stubs. The monolith is the source of truth.
- **Check Logic**:
  ```
  FOR each file IN services/*/ (lab, order, patient, result, sample, notification, ai):
      IF file contains route definitions (@router.get, @router.post, etc.):
          WARN — services/ should only contain stubs
      
      IF file contains business logic beyond placeholder (imports from backend or has >50 lines of logic):
          FAIL — business logic belongs in backend/app/
  
  CHECK that services/ai/ doesn't duplicate backend/app/ai/ logic
  CHECK that services/notification/ doesn't duplicate backend/app/notifications/
  ```
- **Mandatory**: Yes
- **Threshold**: Zero violations
- **Failure Action**: BLOCK
- **Remediation**: Move business logic from services/ stubs to backend/app/. Keep services/ as thin proxies or remove them.
- **Owner**: Platform Engineering
- **Last Updated**: 2026-07-17

---

### ARCH-004: Migration Policy Compliance
- **Gate**: Migration Immutability
- **Description**: Verify no existing migration files have been modified. All schema changes MUST be new Alembic revisions.
- **Check Logic**:
  ```
  CHECK git diff against origin/main for backend/migrations/versions/
  FOR each modified migration file:
      IF file was in the previous release:
          FAIL — existing migrations must not be modified
          REMEDIATION: Create a new migration revision instead
  
  CHECK that latest migration file has datestamp > last release date
  
  IF new migration present:
      CHECK that migration uses _has_column(), _table_exists(), _index_exists() guards
      CHECK that migration is idempotent
      CHECK that new columns are nullable OR have server_default
  ```
- **Mandatory**: Yes
- **Threshold**: Zero modified existing migrations
- **Failure Action**: BLOCK
- **Remediation**: Revert changes to existing migrations. Create a new Alembic revision using `alembic revision --autogenerate -m "description"`.
- **Owner**: Backend Team Lead
- **Last Updated**: 2026-07-17

---

### ARCH-005: Lifespan Pattern Compliance
- **Gate**: FastAPI Lifespan Pattern
- **Description**: All app lifecycle hooks must use the `@asynccontextmanager lifespan(app)` pattern, not deprecated `@app.on_event("startup")` or `@app.on_event("shutdown")`.
- **Check Logic**:
  ```
  SEARCH all Python files IN backend/app/ FOR "@app.on_event("
  IF found:
      FAIL — use lifespan context manager pattern instead
  
  VERIFY backend/app/main.py uses the lifespan pattern:
      - Check that lifespan function is defined as async generator
      - Check that FastAPI(lifespan=lifespan) is used
      - Check that yield separates startup and shutdown logic
  ```
- **Mandatory**: Yes
- **Threshold**: Zero deprecated patterns
- **Failure Action**: BLOCK
- **Remediation**: Replace `@app.on_event("startup")` with startup logic before `yield` in lifespan, and `@app.on_event("shutdown")` with shutdown logic after `yield`.
- **Owner**: Backend Team Lead
- **Last Updated**: 2026-07-17

---

### ARCH-006: Middleware Order Validation
- **Gate**: Middleware Stack Order
- **Description**: Verify middleware stack matches documented order in `backend/app/main.py`.
- **Check Logic**:
  ```
  PARSE backend/app/main.py for app.add_middleware() calls in order:
  EXPECTED ORDER:
    1. MaxBodySizeMiddleware
    2. RequestIDMiddleware
    3. DocsAuthMiddleware
    4. CORSMiddleware
    5. RequestTimingMiddleware
    6. SecurityHeadersMiddleware
    7. GZipMiddleware
    8. ReadinessMiddleware
    9. DegradedModeMiddleware
    10. ConcurrencyLimitMiddleware
  
  IF order differs from expected:
      FAIL — middleware order mismatch
  
  IF any middleware from expected list is missing:
      WARN — missing middleware (non-blocking for optional middlewares)
  ```
- **Mandatory**: Yes
- **Threshold**: Exact match with documented order
- **Failure Action**: BLOCK
- **Remediation**: Reorder middleware registration in `backend/app/main.py` to match documented order. Each middleware's position matters for correct request processing.
- **Owner**: Platform Engineering
- **Last Updated**: 2026-07-17

---

### ARCH-007: Tenant Isolation Consistency
- **Gate**: Multi-Tenant Data Isolation
- **Description**: All patient-data queries must filter by `lab_id = current_user.lab_id` or equivalent tenant scoping.
- **Check Logic**:
  ```
  EXTRACT all SQLAlchemy query patterns from backend/app/routes/ and backend/app/services/
  FOR each .select()/.query() on Patient, LabOrder, LabResult, Sample tables:
      IF WHERE clause does NOT include lab_id filter:
          FAIL — missing tenant isolation
  
  CHECK backend/app/routes/patient_card.py:
      IF patient data returned without verifying lab_id match:
          FAIL — patient card exposes cross-tenant data
  
  VERIFY that admin routes have tenant filter override (for legitimate cross-tenant ops)
  ```
- **Mandatory**: Yes
- **Threshold**: Zero violations for patient-facing models
- **Failure Action**: BLOCK
- **Remediation**: Add `.filter(Model.lab_id == current_user.lab_id)` to all queries on tenant-scoped models. For admin routes that need cross-tenant access, add explicit audit logging.
- **Owner**: Security Team Lead
- **Last Updated**: 2026-07-17

---

### ARCH-008: Financial Engine Boundary
- **Gate**: Financial Module Phase A Restriction
- **Description**: `backend/app/financial/` must contain schema-only code. No business logic, routes, or services until Phase B+.
- **Check Logic**:
  ```
  CHECK backend/app/financial/ for:
      - Any file with @router.get, @router.post, @router.put, @router.delete
      - Any file with business logic classes or functions > 50 lines
      - Any file that imports from other domains (orders, results, patients)
  
  IF business logic found:
      FAIL — financial module is Phase A schema-only
  
  CHECK that ENABLE_FINANCIAL_ENGINE flag defaults to false in config.py
  CHECK that financial routes (if any) are gated behind the feature flag
  ```
- **Mandatory**: Yes
- **Threshold**: Zero business logic in financial/
- **Failure Action**: BLOCK
- **Remediation**: Remove business logic from financial/ module. Keep only SQLAlchemy model definitions. All business logic must wait for Phase B+ explicit approval.
- **Owner**: Product Engineering Lead
- **Last Updated**: 2026-07-17

---

### ARCH-009: Import Convention Compliance
- **Gate**: Python Import Standards
- **Description**: Enforce consistent import conventions: no wildcard imports, prefer relative imports within same package.
- **Check Logic**:
  ```
  SEARCH all Python files FOR "from .* import \*":
      IF found:
          FAIL — wildcard imports prohibited (except in __init__.py)
  
  SEARCH all Python files IN backend/app/routes/ FOR imports from backend.app.models:
      IF import uses absolute path (from backend.app.models import X):
          WARN — prefer relative imports
  
  SEARCH for import statements > 120 characters:
      WARN — split long imports
  
  CHECK that third-party imports are grouped before local imports
  ```
- **Mandatory**: No (Advisory)
- **Threshold**: < 5 violations (prefer 0)
- **Failure Action**: WARN
- **Remediation**: Replace wildcard imports with explicit imports. Convert absolute intra-package imports to relative imports. Follow PEP 8 import ordering.
- **Owner**: Backend Team Lead
- **Last Updated**: 2026-07-17

---

### ARCH-010: Configuration Drift Detection
- **Gate**: Environment Configuration Consistency
- **Description**: Ensure `.env.example` and production config tracks match actual env vars used in `config.py`.
- **Check Logic**:
  ```
  EXTRACT all os.getenv() / os.environ.get() calls from backend/app/config.py
  PARSE .env.example for documented variables
  COMPARE two sets:
      FOR each env var in config.py NOT in .env.example:
          FAIL — undocumented env var (add to .env.example)
      
      FOR each env var in .env.example NOT in config.py:
          WARN — documented but unused (possibly stale)
  
  CHECK config.py for weak secret detection:
      IF _is_weak_secret() returns True for any secret:
          FAIL — weak secret detected
  ```
- **Mandatory**: Yes
- **Threshold**: Zero undocumented env vars
- **Failure Action**: BLOCK
- **Remediation**: Add missing env vars to `.env.example` with description and example value. Remove stale entries. Run `make secrets-gen` for weak secrets.
- **Owner**: Platform Engineering
- **Last Updated**: 2026-07-17

---

## Security Gates (12 rules)

### SEC-001: Hardcoded Secrets Prohibited
- **Gate**: Secret Scanning
- **Description**: No hardcoded API keys, passwords, tokens, or private keys in source code.
- **Check Logic**:
  ```
  SCAN all files (excluding .git, .venv, node_modules, __pycache__) for:
      - Regex patterns matching SECRET_KEY, ENCRYPTION_KEY, NID_HMAC_KEY, etc. assignment
      - Private key patterns (---BEGIN (RSA|EC|DSA) PRIVATE KEY---)
      - Connection strings with embedded passwords
      - Generic password/passwd/pwd assignments
      - JWT tokens and bearer tokens
      - Firebase service account keys (firebase-admin SDK)
  
  USE gitleaks with custom .gitleaks.toml if available
  USE safety/bandit for Python-specific patterns
  ```
- **Mandatory**: Yes
- **Threshold**: Zero secrets found
- **Failure Action**: BLOCK
- **Remediation**: Remove hardcoded secrets immediately. Use environment variables loaded via `backend/app/config.py`. Rotate any exposed secrets. Run `make secrets-gen` for replacements.
- **Owner**: Security Team Lead
- **Last Updated**: 2026-07-17

---

### SEC-002: JWT Validation on Protected Routes
- **Gate**: Authentication Coverage
- **Description**: All protected API endpoints must validate JWT via `get_current_user` dependency.
- **Check Logic**:
  ```
  EXTRACT all route definitions from backend/app/routes/
  IDENTIFY routes requiring authentication (non-public, non-health endpoints)
  
  FOR each protected route:
      CHECK that Depends(get_current_user) is in route dependencies
      OR that router depends on Depends(get_current_user) at router level
      OR that route is in a router with AuthMiddleware or similar
  
  PUBLIC ENDPOINTS WHITELIST (exempt from JWT check):
      - /health, /health/live, /health/ready, /health/status, /health/deep
      - /docs, /redoc, /openapi.json
      - /auth/login, /auth/register, /auth/refresh
      - /test-types (CI validation endpoint)
  
  IF protected route lacks JWT dependency:
      FAIL
  ```
- **Mandatory**: Yes
- **Threshold**: Zero unprotected protected routes
- **Failure Action**: BLOCK
- **Remediation**: Add `Depends(get_current_user)` to the route or router dependency list. Verify `get_current_user` properly validates JWT signature, expiry, and user status.
- **Owner**: Security Team Lead
- **Last Updated**: 2026-07-17

---

### SEC-003: Audit Log on All Mutations
- **Gate**: Audit Trail Completeness
- **Description**: Every data mutation (CREATE, UPDATE, DELETE) must write to `AuditLog` model with hash chain.
- **Check Logic**:
  ```
  EXTRACT all route handlers from backend/app/routes/
  IDENTIFY mutation endpoints (POST, PUT, PATCH, DELETE)
  
  FOR each mutation endpoint:
      TRACE logic path through services and models
      IF no AuditLog.write() or audit_service.log() call is found:
          FAIL — mutation without audit trail
  
  SPECIAL CHECK:
      - Patient data writes (patients, lab_results, lab_orders)
      - User admin operations (create/disable users)
      - Lab configuration changes
      - Role/permission changes
  
  VERIFY audit log uses cryptographic hash chaining (SHA-256 linking)
  ```
- **Mandatory**: Yes
- **Threshold**: Zero untracked mutations
- **Failure Action**: BLOCK
- **Remediation**: Add `AuditLog.write()` call before/after every mutation. Ensure audit entry includes: actor, action, resource type, resource ID, old/new values, timestamp, and previous hash.
- **Owner**: Security Team Lead
- **Last Updated**: 2026-07-17

---

### SEC-004: Tenant Isolation Enforcement
- **Gate**: Data Leak Prevention
- **Description**: Verify that all patient-data queries are scoped to the current user's lab. Cross-lab data access must be explicitly authorized.
- **Check Logic**:
  ```
  STATIC ANALYSIS:
      Scan all SQLAlchemy queries on sensitive models
      CHECK for .filter(Model.lab_id == ...) or equivalent
  
  DYNAMIC ANALYSIS (integration test):
      CREATE user in Lab A
      ATTEMPT to read patient from Lab B via API
      EXPECT: 403 or 404 (not 200 with data)
      IF Lab B data is returned: FAIL
  
  SPECIAL CASE patient_card.py:
      Verify QR token verification includes lab_id scope
      Verify scanned patient card only returns lab's own patients
  ```
- **Mandatory**: Yes
- **Threshold**: Zero cross-tenant data leaks
- **Failure Action**: BLOCK
- **Remediation**: Add explicit `lab_id` filter to all queries. For admin-only cross-tenant access, add `IsAdmin` permission check and audit log entry. Never rely on implicit scoping.
- **Owner**: Security Team Lead
- **Last Updated**: 2026-07-17

---

### SEC-005: National ID Encryption
- **Gate**: PII Encryption at Rest
- **Description**: `patients.national_id` must be encrypted at rest. Never stored as plaintext.
- **Check Logic**:
  ```
  INSPECT backend/app/models/patient.py:
      national_id column MUST use custom encrypted type or SQLAlchemy type decorator
  
  VERIFY encryption/decryption exists in services:
      CHECK backend/app/security/ for encryption utilities
      VERIFY that writes encrypt and reads decrypt national_id
  
  CHECK that NID_HMAC_KEY is loaded from env and is strong:
      IF _is_weak_secret(NID_HMAC_KEY): FAIL
  
  SEARCH for any raw SELECT or access to national_id without decryption:
      IF found: FAIL — potential plaintext read
  
  CHECK logs for accidental national_id logging:
      SEARCH for national_id in log format strings: FAIL
  ```
- **Mandatory**: Yes
- **Threshold**: Zero plaintext national_id access
- **Failure Action**: BLOCK
- **Remediation**: Implement or use existing encryption utilities in `backend/app/security/`. Update model to use encrypted column type. Ensure all reads/writes go through encryption layer. Check config.py for NID_HMAC_KEY strength.
- **Owner**: Security Team Lead
- **Last Updated**: 2026-07-17

---

### SEC-006: CORS Configuration Correctness
- **Gate**: Cross-Origin Security
- **Description**: CORS must not use wildcard origins in production. Validate allowed origins list.
- **Check Logic**:
  ```
  CHECK backend/app/main.py CORSMiddleware configuration:
      IF allow_origins == ["*"] OR allow_origins == "*":
          FAIL — wildcard CORS in production
  
  IF allow_origin_regex is used:
      VERIFY regex is restrictive (not ".*")
  
  CHECK that allow_credentials=True when specific origins are set
  CHECK that allowed methods are restricted to needed HTTP methods
  CHECK that allowed headers are restricted to needed headers
  ```
- **Mandatory**: Yes
- **Threshold**: No wildcard CORS
- **Failure Action**: BLOCK
- **Remediation**: Replace `allow_origins=["*"]` with explicit list of allowed origins (e.g., frontend domains). Keep origin list in an environment variable. Never use wildcard in production.
- **Owner**: Platform Engineering
- **Last Updated**: 2026-07-17

---

### SEC-007: Rate Limiting on Public Endpoints
- **Gate**: Abuse Prevention
- **Description**: All public/unauthenticated endpoints must have rate limiting via the firewall module.
- **Check Logic**:
  ```
  EXTRACT public endpoints (no JWT required):
      - /auth/* (login, register, refresh)
      - /health/* (read-only, but still rate-limited)
      - /docs, /redoc, /openapi.json
  
  VERIFY rate limiting is configured for each:
      - CHECK backend/app/firewall/ for rate limit rules
      - CHECK that rate_limit middleware covers public endpoints
      - VERIFY limit values are reasonable (> 10/min for auth, > 60/min for health)
  
  IF public endpoint without rate limiting:
      WARN — rate limit recommended
  
  CHECK that auth endpoints have stricter limits (login: 5/min per IP)
  ```
- **Mandatory**: Yes
- **Threshold**: All public endpoints rate-limited
- **Failure Action**: WARN (for new endpoints), BLOCK (for auth endpoints)
- **Remediation**: Add rate limiting rules in `backend/app/firewall/` for any uncovered public endpoints. Configure limits via `RateLimitMiddleware` or per-route decorators.
- **Owner**: Security Team Lead
- **Last Updated**: 2026-07-17

---

### SEC-008: SQL Injection Prevention
- **Gate**: Query Safety
- **Description**: No raw SQL execution with string formatting. All queries must use parameterized statements.
- **Check Logic**:
  ```
  SCAN all Python files for dangerous patterns:
      - cursor.execute(f"...{...}...") or .execute("..." % ...)
      - text() with f-strings or % formatting
      - session.execute(text(f"..."))
      - raw_connection.execute(...) with string concatenation
  
  IGNORE patterns in:
      - Migration files (controlled environment)
      - Test fixtures (controlled data)
  
  IF dangerous pattern found outside exceptions:
      FAIL
  ```
- **Mandatory**: Yes
- **Threshold**: Zero raw SQL with user input
- **Failure Action**: BLOCK
- **Remediation**: Replace string-formatted SQL with SQLAlchemy ORM queries or parameterized `text()` queries (`text("SELECT * FROM t WHERE id = :id").params(id=val)`). Never use f-strings or `%` formatting in SQL queries.
- **Owner**: Backend Team Lead
- **Last Updated**: 2026-07-17

---

### SEC-009: RBAC Enforcement
- **Gate**: Role-Based Access Control
- **Description**: Verify that protected routes check the required role/permission before allowing access.
- **Check Logic**:
  ```
  EXTRACT all route handlers from backend/app/routes/
  IDENTIFY routes with role requirements (admin, manager, technician, etc.)
  
  FOR each role-protected route:
      CHECK for RoleChecker dependency or permission check
      VERIFY that backend/app/security/rbac.py defines the required role
      CHECK that the permission matrix covers 9 roles × 13 permissions
  
  SPECIAL CHECK:
      - Admin routes must check IsAdmin or equivalent
      - Lab-specific routes must check lab_id matches user's lab
      - System-level operations must check superadmin role
  ```
- **Mandatory**: Yes
- **Threshold**: Zero missing role checks
- **Failure Action**: BLOCK
- **Remediation**: Add `RoleChecker` or permission check dependency to route handlers. Define new roles/permissions in `backend/app/security/rbac.py` as needed. Ensure default-deny approach.
- **Owner**: Security Team Lead
- **Last Updated**: 2026-07-17

---

### SEC-010: Dependency Vulnerability Scan
- **Gate**: Known Vulnerability Check
- **Description**: All dependencies must be scanned for known CVEs. CRITICAL and HIGH vulnerabilities block release.
- **Check Logic**:
  ```
  RUN safety check on backend/requirements*.txt:
      safety check -r requirements.txt -r requirements-dev.txt
  
  RUN pip-audit as alternative:
      pip-audit -r requirements.txt
  
  FOR each vulnerability found:
      IF severity == CRITICAL:
          FAIL — block release
      IF severity == HIGH:
          FAIL — block release
      IF severity == MEDIUM:
          WARN — flag for review
      IF severity == LOW:
          LOG — inform only
  
  CHECK for false positives (verified by team):
      IF vulnerability is confirmed false positive, document in .safety-ignore.yml
  ```
- **Mandatory**: Yes
- **Threshold**: Zero CRITICAL or HIGH vulnerabilities
- **Failure Action**: BLOCK
- **Remediation**: Update affected package to patched version. If no patch exists, add input-level mitigation (WAF rule, input sanitization) and document in security exceptions log. Create a tracking issue for remediation.
- **Owner**: Security Team Lead
- **Last Updated**: 2026-07-17

---

### SEC-011: Security Headers Present
- **Gate**: HTTP Security Headers
- **Description**: All responses must include security headers: CSP, HSTS, X-Frame-Options, X-Content-Type-Options, etc.
- **Check Logic**:
  ```
  CHECK backend/app/main.py SecurityHeadersMiddleware:
      VERIFY Content-Security-Policy header is set
      VERIFY Strict-Transport-Security header is set (max-age >= 31536000)
      VERIFY X-Frame-Options: DENY or SAMEORIGIN
      VERIFY X-Content-Type-Options: nosniff
      VERIFY Referrer-Policy: strict-origin-when-cross-origin
      VERIFY Permissions-Policy is set
  
  PERFORM HTTP HEAD request to /health endpoint:
      PARSE response headers
      IF any required header is missing:
          FAIL
  ```
- **Mandatory**: Yes
- **Threshold**: All security headers present
- **Failure Action**: BLOCK
- **Remediation**: Update `SecurityHeadersMiddleware` in `backend/app/main.py` to add missing headers. Ensure CSP policy is restrictive but functional for the frontend domains.
- **Owner**: Platform Engineering
- **Last Updated**: 2026-07-17

---

### SEC-012: Metrics Endpoint Protection
- **Gate**: Observability Access Control
- **Description**: `/metrics/prom` endpoint requires `Bearer METRICS_BEARER_TOKEN` in production.
- **Check Logic**:
  ```
  CHECK backend/app/main.py route definition for /metrics/prom:
      IF route exists WITHOUT authentication dependency:
          FAIL — metrics endpoint must be protected
  
  VERIFY METRICS_BEARER_TOKEN is loaded and not weak:
      IF _is_weak_secret(METRICS_BEARER_TOKEN): FAIL
  
  CHECK that token validation is constant-time (no timing attack):
      Use hmac.compare_digest or secrets.compare_digest
  
  VERIFY that metrics endpoint doesn't leak sensitive data (patient data, internal IPs)
  ```
- **Mandatory**: Yes
- **Threshold**: Metrics endpoint protected
- **Failure Action**: BLOCK
- **Remediation**: Add Bearer token authentication to `/metrics/prom` route. Generate strong token via `make metrics-token`. Ensure comparison is constant-time.
- **Owner**: Platform Engineering
- **Last Updated**: 2026-07-17

---

## Testing Gates (10 rules)

### TST-001: Unit Test Coverage Minimum
- **Gate**: Coverage Threshold
- **Description**: New and changed code must have minimum 70% unit test line coverage.
- **Check Logic**:
  ```
  DETERMINE changed files via git diff against base branch (for PR)
  OR all files in backend/app/ for full release
  
  RUN pytest --cov=backend/app/ --cov-report=term-missing
  EXTRACT coverage percentage for new/changed files
  
  IF overall coverage < 70%:
      WARN — coverage below threshold
      IF coverage < 50%:
          FAIL — critically low coverage
  
  SPECIAL CHECK for core modules (security, clinical safety, audit):
      REQUIRED minimum coverage: 85%
      IF below 85%: FAIL
  ```
- **Mandatory**: No (Advisory for general code)
- **Threshold**: 70% overall, 85% for core modules
- **Failure Action**: WARN (general), WARN (core)
- **Remediation**: Add unit tests for uncovered code paths. Focus on edge cases, error handling, and security-critical paths. Use `pytest --cov-report=term-missing` to identify gaps.
- **Owner**: Quality Engineering Lead
- **Last Updated**: 2026-07-17

---

### TST-002: Integration Test Coverage
- **Gate**: Integration Test Completeness
- **Description**: Critical system paths must have integration tests covering the full request→database→response cycle.
- **Check Logic**:
  ```
  IDENTIFY critical paths:
      - Patient creation → order creation → sample assignment → result entry → result release
      - User authentication → lab selection → data access
      - Audit log write on every mutation
      - Critical alert generation and delivery
  
  FOR each critical path:
      CHECK for integration test in backend/tests/
      IF missing: FAIL
  
  VERIFY integration tests use test database (not production-like mock)
  VERIFY integration tests clean up after themselves
  ```
- **Mandatory**: Yes
- **Threshold**: All critical paths have integration tests
- **Failure Action**: BLOCK
- **Remediation**: Write integration tests for missing critical paths using TestClient. Follow patterns in existing tests like `test_comprehensive.py`. Include setup/teardown for test data isolation.
- **Owner**: Quality Engineering Lead
- **Last Updated**: 2026-07-17

---

### TST-003: Migration Round-Trip Test
- **Gate**: Migration Safety
- **Description**: All migrations must successfully upgrade and downgrade on a clean database.
- **Check Logic**:
  ```
  SETUP: Clean PostgreSQL database (docker compose down -v && docker compose up -d postgres)
  
  RUN: alembic upgrade head
  VERIFY: Required tables exist (labs, lab_users, patients, lab_orders, lab_results, outbox_events, audit_logs)
  
  IF upgrade fails:
      FAIL
  
  RUN: alembic downgrade -1
  VERIFY: downgrade completes without error
  
  RUN: alembic upgrade head
  VERIFY: upgrade from downgraded state works
  
  IF downgrade or re-upgrade fails:
      FAIL — migration is not idempotent or reversible
  ```
- **Mandatory**: Yes
- **Threshold**: Clean upgrade + downgrade + re-upgrade
- **Failure Action**: BLOCK
- **Remediation**: Fix the failing migration. For downgrade failure, add `downgrade()` function that reverses the upgrade. For upgrade failure, fix migration logic. Test locally with `make ci`.
- **Owner**: Backend Team Lead
- **Last Updated**: 2026-07-17

---

### TST-004: Smoke Test Pass
- **Gate**: Application Boot Health
- **Description**: All health endpoints must respond with HTTP 200 on application boot.
- **Check Logic**:
  ```
  START: uvicorn backend.app.main:app (or docker compose up -d)
  WAIT: For system_ready flag to become True (up to 30s timeout)
  
  TEST EACH:
      curl -f http://localhost:8000/health       → expect 200
      curl -f http://localhost:8000/health/live   → expect 200
      curl -f http://localhost:8000/health/ready  → expect 200
      curl -f http://localhost:8000/health/status → expect 200
      curl -f http://localhost:8000/health/deep   → expect 200
      curl -f http://localhost:8000/docs          → expect 200 (swagger UI)
  
  IF any returns non-200:
      FAIL
  
  CHECK response body for expected JSON structure
  ```
- **Mandatory**: Yes
- **Threshold**: All 6 health endpoints return 200
- **Failure Action**: BLOCK
- **Remediation**: Check application logs for startup errors. Verify database is reachable. Check `system_ready` flag in `backend/app/core/startup_guard.py`. Verify config is valid.
- **Owner**: Platform Engineering
- **Last Updated**: 2026-07-17

---

### TST-005: Critical Path Tests Pass
- **Gate**: Core Business Logic
- **Description**: All tests for orders, results, samples, and patient routes must pass.
- **Check Logic**:
  ```
  IDENTIFY test files covering critical paths:
      - backend/tests/test_comprehensive.py
      - backend/tests/test_stability_assertions.py
      - Any test file testing orders, results, samples, patients routes
  
  RUN: pytest backend/tests/ -v -k "order or result or sample or patient"
  
  IF any test fails:
      FAIL
  
  CHECK that test count > 20 (reasonable minimum for critical path coverage)
  ```
- **Mandatory**: Yes
- **Threshold**: Zero failures, minimum 20 tests
- **Failure Action**: BLOCK
- **Remediation**: Debug failing tests. Ensure test data setup is correct. Check for shared state between tests. Run tests in isolation to identify flakiness.
- **Owner**: Quality Engineering Lead
- **Last Updated**: 2026-07-17

---

### TST-006: Security Test Suite Passes
- **Gate**: Security Invariant Validation
- **Description**: All security-focused tests (JWT, auth, encryption) must pass.
- **Check Logic**:
  ```
  RUN: pytest backend/tests/test_security.py -v
  
  VERIFY specific tests pass:
      - test_jwt_reject_expired
      - test_jwt_reject_invalid_signature
      - test_encryption_at_rest
      - test_tenant_isolation
      - test_audit_log_invariants
      - test_rate_limiting_enforcement
  
  IF any security test fails:
      FAIL — security regression
  ```
- **Mandatory**: Yes
- **Threshold**: Zero failures
- **Failure Action**: BLOCK
- **Remediation**: Security test failure is a critical regression. Investigate immediately. Check if a code change inadvertently broke JWT validation, encryption, or auth logic. Rollback if needed.
- **Owner**: Security Team Lead
- **Last Updated**: 2026-07-17

---

### TST-007: All Test Modules Pass
- **Gate**: Full Test Suite
- **Description**: All 28 test modules must pass without errors.
- **Check Logic**:
  ```
  RUN: pytest backend/tests/ -v --tb=short
  
  IF any test fails (error or assertion failure):
      FAIL
  
  IF test suite crashes (ModuleNotFoundError, ImportError, etc.):
      FAIL — syntax or import error in test or source code
  
  COUNT passed/failed/skipped:
      IF skipped > 10% of total:
          WARN — too many skipped tests may indicate bitrot
  ```
- **Mandatory**: Yes
- **Threshold**: Zero failures
- **Failure Action**: BLOCK
- **Remediation**: Fix failing tests. Run `python -m py_compile backend/app/main.py` to catch syntax errors first. Check for environmental differences (e.g., missing Redis during test).
- **Owner**: Quality Engineering Lead
- **Last Updated**: 2026-07-17

---

### TST-008: No Flaky Tests Detected
- **Gate**: Test Reliability
- **Description**: Tests must pass consistently. Flaky tests undermine confidence in the test suite.
- **Check Logic**:
  ```
  RUN: pytest backend/tests/ -v --tb=short  (run 1)
  RUN: pytest backend/tests/ -v --tb=short  (run 2)
  RUN: pytest backend/tests/ -v --tb=short  (run 3)
  
  COMPARE results across 3 runs:
      IF a test fails in one run but passes in another:
          FAIL — flaky test detected
  
  CHECK for common flaky patterns:
      - Tests depending on test execution order (shared state)
      - Tests with timing-dependent assertions
      - Tests using random data without seed
      - Tests interacting with external services
  ```
- **Mandatory**: Yes
- **Threshold**: Zero flaky tests
- **Failure Action**: WARN (single flaky), BLOCK (multiple flaky)
- **Remediation**: Identify and fix flaky tests. Common fixes: use deterministic data, ensure test isolation, increase timeouts, use pytest-randomly to detect order dependencies.
- **Owner**: Quality Engineering Lead
- **Last Updated**: 2026-07-17

---

### TST-009: Syntax Gate Passes
- **Gate**: Python Syntax Validation
- **Description**: All Python files must compile without syntax errors.
- **Check Logic**:
  ```
  FOR each .py file IN backend/app/ and backend/migrations/:
      RUN: python -m py_compile {file}
      IF return code != 0:
          FAIL — syntax error in {file}
  
  IMPORT WALK:
      RUN: python -c "import backend.app.main" (with unittest.mock stubs for imports)
      IF NameError, AttributeError, or SystemExit raised at module level:
          FAIL — module-level error
  ```
- **Mandatory**: Yes
- **Threshold**: Zero compilation errors
- **Failure Action**: BLOCK
- **Remediation**: Fix syntax errors. Common issues: missing imports, undefined names, indentation errors. Run `make lint` locally as a pre-commit check.
- **Owner**: All developers
- **Last Updated**: 2026-07-17

---

### TST-010: Lint Check Passes
- **Gate**: Code Quality Standards
- **Description**: Code must pass flake8 error-only checks (E9, F821 categories).
- **Check Logic**:
  ```
  RUN: flake8 --select=E9,F821 backend/app/
  
  IF any error found:
      FAIL — lint error detected
  
  COUNT errors per category:
      - E9: Runtime errors (syntax errors, undefined names)
      - F821: Undefined names
  ```
- **Mandatory**: Yes
- **Threshold**: Zero lint errors
- **Failure Action**: BLOCK
- **Remediation**: Fix each flake8 error. These are real bugs or potential runtime errors. Run `make lint` before committing.
- **Owner**: All developers
- **Last Updated**: 2026-07-17

---

## Documentation Gates (6 rules)

### DOC-001: OpenAPI Documentation Completeness
- **Gate**: API Documentation
- **Description**: All public API endpoints must be documented in OpenAPI schema with request/response models.
- **Check Logic**:
  ```
  ACCESS: http://localhost:8000/openapi.json
  PARSE OpenAPI schema
  
  FOR each route in backend/app/routes/:
      IF route is public (not /health, not internal):
          IF route is NOT present in OpenAPI schema:
              FAIL — missing OpenAPI definition
          IF route missing summary or description:
              WARN — incomplete documentation
          IF route missing response model:
              WARN — missing response schema
          IF route missing request body schema (for POST/PUT):
              WARN — missing request schema
  ```
- **Mandatory**: Yes
- **Threshold**: All public routes documented
- **Failure Action**: WARN
- **Remediation**: Add Pydantic response models to route decorators. Add docstrings or description parameters to route functions. Follow existing patterns in other route files.
- **Owner**: Backend Team Lead
- **Last Updated**: 2026-07-17

---

### DOC-002: ADR Documentation
- **Gate**: Architecture Decision Records
- **Description**: Architecture decisions must be documented as ADRs in `docs/adr/`.
- **Check Logic**:
  ```
  CHECK docs/adr/ directory exists and contains .md files
  
  FOR areas with significant architectural changes in this release:
      MONOLITH vs MICROSERVICES decisions
      MIDDLEWARE changes
      DATABASE changes
      SECURITY changes
      CHECK if corresponding ADR exists
  
  ADR template check:
      Each ADR must have: Title, Status, Context, Decision, Consequences
      IF missing required sections: WARN
  ```
- **Mandatory**: No (Advisory)
- **Threshold**: ADRs exist for significant changes
- **Failure Action**: WARN
- **Remediation**: Create ADR document for any significant architecture decision. Use template: Title, Status (Proposed/Accepted/Deprecated/Superseded), Context, Decision, Consequences. Store in `docs/adr/NNNN-title.md`.
- **Owner**: Platform Engineering
- **Last Updated**: 2026-07-17

---

### DOC-003: Module READMEs Exist
- **Gate**: Module Documentation
- **Description**: Every subpackage in `backend/app/` must have a README.md explaining its purpose and usage.
- **Check Logic**:
  ```
  FOR each directory IN backend/app/:
      IF directory has __init__.py (is a Python package):
          IF directory does NOT have README.md:
              WARN — undocumented module
  
  REQUIRED READMEs:
      - backend/app/routes/ (overview of all route modules)
      - backend/app/models/ (entity relationship overview)
      - backend/app/services/ (service layer patterns)
      - backend/app/core/ (core infrastructure overview)
      - backend/app/security/ (auth patterns)
  
  CHECK README quality (minimum content):
      - Module purpose
      - Key classes/functions
      - Usage examples (if applicable)
      - Related modules
  ```
- **Mandatory**: No (Advisory)
- **Threshold**: All major modules have README
- **Failure Action**: WARN
- **Remediation**: Create README.md for undocumented modules. Follow existing README patterns for consistency. Focus on what the module does, how it's used, and how it relates to other modules.
- **Owner**: Quality Engineering Lead
- **Last Updated**: 2026-07-17

---

### DOC-004: Env File Alignment
- **Gate**: Environment Configuration Documentation
- **Description**: `.env.example` must be kept in sync with actual environment variables used.
- **Check Logic**:
  ```
  PARSE backend/app/config.py for os.getenv() calls
  PARSE .env.example for documented vars
  
  COMPARE:
      FOR each var in config.py NOT in .env.example:
          FAIL — undocumented env var
      FOR each var in .env.example NOT in config.py:
          WARN — documented but unused (remove if stale)
  
  CHECK .env.example has:
      - Variable name
      - Default value (or placeholder)
      - Description comment
      - Required/Optional marker
  ```
- **Mandatory**: Yes
- **Threshold**: All env vars documented
- **Failure Action**: BLOCK (missing vars), WARN (stale entries)
- **Remediation**: Add missing env vars to `.env.example` with descriptions. Remove stale entries. Update comments if defaults changed.
- **Owner**: Platform Engineering
- **Last Updated**: 2026-07-17

---

### DOC-005: Changelog Updated
- **Gate**: Release Notes
- **Description**: `CHANGELOG.md` must be updated for the release with accurate entries.
- **Check Logic**:
  ```
  CHECK CHANGELOG.md exists and has recent entries
  PARSE git log --oneline since last release tag
  
  FOR each notable commit:
      IF changelog entry doesn't cover it:
          WARN — missing changelog entry
  
  CHANGELOG STRUCTURE CHECK:
      - Version header with date
      - Categories: Added, Changed, Deprecated, Removed, Fixed, Security
      - Link to full changelog or compare
  ```
- **Mandatory**: No (Advisory)
- **Threshold**: Changelog is up to date
- **Failure Action**: WARN
- **Remediation**: Update CHANGELOG.md following existing format. Categorize changes properly. Reference issue/PR numbers where applicable.
- **Owner**: Product Engineering Lead
- **Last Updated**: 2026-07-17

---

### DOC-006: Migration Runbook
- **Gate**: Migration Deployment Documentation
- **Description**: Any release with database migrations must include a migration runbook.
- **Check Logic**:
  ```
  CHECK if any new migration files exist:
      git diff --name-only origin/main...HEAD -- backend/migrations/versions/
  
  IF new migrations exist:
      CHECK for runbook document in docs/migrations/ or in PR description
      REQUIRED runbook content:
          - Migration purpose
          - Expected duration
          - Impact (locking, downtime)
          - Rollback procedure
          - Verification steps
      IF missing: FAIL — migration runbook required
  ```
- **Mandatory**: Yes
- **Threshold**: Migration runbook exists for new migrations
- **Failure Action**: BLOCK
- **Remediation**: Create migration runbook document covering: SQL changes, expected timing, table locking behavior, rollback plan, and verification queries. Reference similar runbooks for format.
- **Owner**: Backend Team Lead
- **Last Updated**: 2026-07-17

---

## Performance Gates (6 rules)

### PERF-001: Latency Budget Compliance
- **Gate**: API Response Time
- **Description**: p95 endpoint response time must be under 500ms for API routes. Health endpoints must be under 200ms.
- **Check Logic**:
  ```
  IF RUNNING performance tests:
      DEPLOY application with representative load
      RUN: locust or custom load test with 100 concurrent users
  
      MEASURE p95 latency for each endpoint category:
          - API routes (orders, results, patients, samples): < 500ms
          - Health endpoints: < 200ms
          - Auth endpoints: < 1000ms (includes bcrypt/hashing)
          - Static/read endpoints: < 300ms
  
      IF p95 exceeds budget: FAIL
      IF p99 exceeds 2x budget: WARN
  
  IF NOT running performance tests:
      CHECK for any recent changes that could impact latency:
          - New middleware
          - New database queries in hot path
          - New external API calls in request path
      WARN: Manual review recommended
  ```
- **Mandatory**: Yes (when perf tests run)
- **Threshold**: p95 < 500ms API, p95 < 200ms health
- **Failure Action**: BLOCK (perf regression)
- **Remediation**: Profile the slow endpoint. Common fixes: add database index, optimize ORM query (eager load, selectinload), add caching (Redis), move heavy work to background task, reduce middleware overhead.
- **Owner**: Platform Engineering
- **Last Updated**: 2026-07-17

---

### PERF-002: No N+1 Query Patterns
- **Gate**: Query Efficiency
- **Description**: Detect database queries inside loops that cause N+1 query problem.
- **Check Logic**:
  ```
  STATIC ANALYSIS:
      FOR each Python file IN backend/app/routes/ and backend/app/services/:
          FOR each FOR loop:
              IF loop body contains session.query(), session.get(), Model.query, or .one()/.first():
                  CHECK if query result could be batched
  
  DYNAMIC ANALYSIS (SQL logging):
      RUN integration tests with SQL query logging enabled
      ANALYZE query patterns:
          IF same query pattern appears N times where N > 2:
              DETECT: potential N+1 (emit WARN)
          IF N > 10:
              FAIL — definite N+1 problem
  
  CHECK for lazy loaded relationships accessed inside loop:
      IF relationship not eagerly loaded and accessed in loop:
          FAIL — N+1 from lazy loading
  ```
- **Mandatory**: Yes
- **Threshold**: Zero confirmed N+1 patterns
- **Failure Action**: WARN
- **Remediation**: Add `selectinload()` or `joinedload()` to eagerly load related data. Batch queries using `IN` clause. Use SQLAlchemy's `subqueryload()` for collections.
- **Owner**: Backend Team Lead
- **Last Updated**: 2026-07-17

---

### PERF-003: Memory Limit Per Request
- **Gate**: Memory Efficiency
- **Description**: No single request should exceed 256MB of memory allocation (excluding static files/uploads).
- **Check Logic**:
  ```
  RUN: stress test with large payloads
      - Create patient with large profile
      - Fetch large result sets
      - Upload/process large lab results
  
  MONITOR: per-request memory using tracemalloc or memray
  
  IF any single request allocates > 256MB:
      FAIL — memory budget exceeded
  
  CHECK for memory patterns:
      - Loading entire tables into memory
      - Creating large intermediate lists/dicts
      - Not streaming large responses
      - Loading all related objects eagerly
  ```
- **Mandatory**: No (Advisory)
- **Threshold**: < 256MB per request
- **Failure Action**: WARN
- **Remediation**: Add pagination to large queries. Stream large responses using `StreamingResponse`. Use server-side cursors for large result sets. Implement Redis caching for repeated queries.
- **Owner**: Backend Team Lead
- **Last Updated**: 2026-07-17

---

### PERF-004: Connection Pool Budget Valid
- **Gate**: Database Connection Budget
- **Description**: Ensure `WEB_CONCURRENCY × (DB_POOL_SIZE + DB_MAX_OVERFLOW) < postgres.max_connections` (default 100).
- **Check Logic**:
  ```
  READ: WEB_CONCURRENCY from Dockerfile/Compose (default 3)
  READ: DB_POOL_SIZE and DB_MAX_OVERFLOW from backend/app/database.py (default 6, 12)
  READ: postgres max_connections (default 100)
  
  CALCULATE: total_connections = WEB_CONCURRENCY * (DB_POOL_SIZE + DB_MAX_OVERFLOW)
  COMPARE: total_connections vs postgres.max_connections * 0.8 (safety margin)
  
  IF total_connections >= max_connections * 0.8:
      WARN — approaching connection limit
      IF total_connections >= max_connections:
          FAIL — over budget, will cause connection errors
  
  CHECK overflow behavior:
      IF DB_MAX_OVERFLOW > 0 and overflow connections don't have timeout:
          WARN — overflow without timeout can exhaust connections
  ```
- **Mandatory**: Yes
- **Threshold**: total_connections < max_connections * 0.8
- **Failure Action**: BLOCK (over budget), WARN (approaching limit)
- **Remediation**: Reduce `DB_POOL_SIZE` or `DB_MAX_OVERFLOW`, or increase `postgres.max_connections`. Document the formula: `WEB_CONCURRENCY × (DB_POOL_SIZE + DB_MAX_OVERFLOW) < postgres.max_connections`.
- **Owner**: Platform Engineering
- **Last Updated**: 2026-07-17

---

### PERF-005: Slow Query Detection
- **Gate**: Database Query Performance
- **Description**: Detect queries performing sequential scans on large tables (missing indexes).
- **Check Logic**:
  ```
  ANALYZE: PostgreSQL query log or pg_stat_statements
  IDENTIFY queries with:
      - sequential scan on tables > 10,000 rows
      - execution time > 100ms (single query)
      - execution time > 500ms (reporting/analytics)
  
  FOR each slow query:
      CHECK if appropriate index exists:
          SHOW indexes on queried table
          IF columns in WHERE/JOIN/ORDER BY are not indexed:
              FAIL — missing index
  
  CHECK backend/app/models/ for common query patterns:
      - patient lookups by phone (exact match)
      - order lookups by lab_id + status
      - result lookups by order_id
      - sample lookups by barcode
      - date-range queries
  ```
- **Mandatory**: No (Advisory)
- **Threshold**: No full table scans on tables > 10K rows
- **Failure Action**: WARN
- **Remediation**: Add database indexes for columns used in WHERE, JOIN, and ORDER BY clauses. Use composite indexes for multi-column filters. Run `ANALYZE` after creating indexes. Create migration for new indexes.
- **Owner**: Backend Team Lead
- **Last Updated**: 2026-07-17

---

### PERF-006: Response Compression Active
- **Gate**: Bandwidth Optimization
- **Description**: GZip compression must be enabled for API responses to reduce bandwidth.
- **Check Logic**:
  ```
  VERIFY: GZipMiddleware is in middleware stack in backend/app/main.py
      app.add_middleware(GZipMiddleware, minimum_size=1000)
  
  CHECK: minimum_size parameter (should be 1000 bytes, not too high)
  
  FUNCTIONAL TEST:
      curl -H "Accept-Encoding: gzip" http://localhost:8000/health/deep
      CHECK: Response header Content-Encoding: gzip
      IF missing: WARN — compression not working
  
  CHECK: compression is not applied to already-compressed content (images, PDFs)
  ```
- **Mandatory**: No (Advisory)
- **Threshold**: Compression active and working
- **Failure Action**: WARN
- **Remediation**: Add or configure `GZipMiddleware` in middleware stack. Ensure minimum_size is reasonable (1000 bytes). Verify with curl test.
- **Owner**: Platform Engineering
- **Last Updated**: 2026-07-17

---

## Dependency Gates (4 rules)

### DEP-001: No Known Critical/High Vulnerabilities
- **Gate**: Dependency Vulnerability
- **Description**: Dependencies must have no CRITICAL or HIGH severity CVEs.
- **Check Logic**:
  ```
  RUN: safety check -r backend/requirements.txt --full-report
  RUN: pip-audit -r backend/requirements.txt
  
  PARSE results:
      FOR each vulnerability:
          IF severity == CRITICAL:
              FAIL
          IF severity == HIGH:
              FAIL
  
  EXCEPTIONS:
      IF vulnerability is documented in .safety-exceptions.yml with:
          - CVE ID
          - Justification (false positive, no fix available, mitigated)
          - Review date
          - Reviewer
      THEN allow (with WARN)
  
  CHECK for CVEs with known exploits in the wild (CISA KEV catalog)
  ```
- **Mandatory**: Yes
- **Threshold**: Zero CRITICAL/HIGH vulnerabilities (or documented exceptions)
- **Failure Action**: BLOCK
- **Remediation**: Update vulnerable packages. If no patch available, add WAF rule, input filtering, or other compensating controls. Document in exception list with review date.
- **Owner**: Security Team Lead
- **Last Updated**: 2026-07-17

---

### DEP-002: License Compliance
- **Gate**: Open Source License Compatibility
- **Description**: All dependencies must use licenses compatible with commercial deployment (no GPL/AGPL in backend).
- **Check Logic**:
  ```
  RUN: pip-licenses --format=json --with-urls --with-license-file
  
  EXTRACT all unique licenses
  
  CHECK against allowed list:
      ALLOWED: MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, ISC, MPL-2.0, LGPL, Python-2.0
      DENIED: GPL-2.0, GPL-3.0, AGPL-3.0, SSPL, BUSL-1.1
      REVIEW: Any license not in either list
      WARN: Any dependency with license that restricts commercial use
  
  IF denied license found:
      FAIL
  ```
- **Mandatory**: Yes
- **Threshold**: Zero denied-license dependencies
- **Failure Action**: BLOCK
- **Remediation**: Replace GPL/AGPL dependency with compatible alternative. If no alternative exists, contact legal for exception and document with vendor approval.
- **Owner**: Product Engineering Lead
- **Last Updated**: 2026-07-17

---

### DEP-003: No Duplicate Dependencies
- **Gate**: Dependency Deduplication
- **Description**: No package should appear more than once in requirements files (different versions of same package).
- **Check Logic**:
  ```
  PARSE: backend/requirements.txt, backend/requirements-dev.txt
  
  FOR each package:
      IF same package name appears with different version constraints:
          FAIL — duplicate dependency with version conflict
  
  CHECK frontend-v2/package.json similarly:
      IF duplicate packages detected:
          WARN
  ```
- **Mandatory**: Yes
- **Threshold**: Zero duplicates
- **Failure Action**: WARN
- **Remediation**: Remove duplicate entries, keeping only the needed version. Use `pip-compile` from pip-tools to generate consistent requirements files from a single `requirements.in`.
- **Owner**: Backend Team Lead
- **Last Updated**: 2026-07-17

---

### DEP-004: Outdated Package Check
- **Gate**: Dependency Freshness
- **Description**: Packages should not be more than 2 major versions behind the latest stable release.
- **Check Logic**:
  ```
  RUN: pip list --outdated --format=json
  
  FOR each outdated package:
      PARSE current version and latest version
      CALCULATE major version difference:
          major_diff = latest_major - current_major
      
      IF major_diff >= 2:
          FAIL — package is too far behind
      IF major_diff >= 1:
          WARN — package is one major version behind
      IF package has no updates in > 2 years:
          WARN — potentially unmaintained package
  
  SPECIAL CONSIDERATION:
      IF package is pinned intentionally (documented in requirements comment):
          ALLOW with WARN
      IF major version includes breaking API changes:
          WARN with upgrade recommendation
  ```
- **Mandatory**: No (Advisory)
- **Threshold**: No packages more than 2 major versions behind
- **Failure Action**: WARN
- **Remediation**: Update outdated packages using `pip install --upgrade <package>`. Test thoroughly for breaking changes. Update requirements files and lock files. Create tracking issue for major version upgrades.
- **Owner**: Backend Team Lead
- **Last Updated**: 2026-07-17

---

## Infrastructure Gates (4 rules)

### INFRA-001: Dockerfile Best Practices
- **Gate**: Container Build Quality
- **Description**: Dockerfiles must follow best practices: multi-stage builds, specific tags, no cache layers.
- **Check Logic**:
  ```
  CHECK Dockerfile in backend/:
      IF single-stage build (no FROM ... AS ...):
          FAIL — must use multi-stage build
  
      IF FROM uses :latest tag:
          FAIL — must use specific version tag
  
      IF no requirements install before code copy:
          FAIL — dependency caching must precede code copy
          (COPY requirements*.txt . && pip install ... BEFORE COPY . .)
  
      IF RUN apt-get without --no-install-recommends:
          WARN — bloated image size
  
      IF multi-line RUN without && chaining:
          WARN — creates unnecessary layers
  ```
- **Mandatory**: Yes
- **Threshold**: All Dockerfile best practices followed
- **Failure Action**: BLOCK (multi-stage, latest tag), WARN (others)
- **Remediation**: Refactor Dockerfile to use multi-stage build. Pin specific base image versions. Install dependencies before copying code. Clean up apt cache in same RUN layer.
- **Owner**: Platform Engineering
- **Last Updated**: 2026-07-17

---

### INFRA-002: Healthcheck Configuration
- **Gate**: Container Health Monitoring
- **Description**: All service Dockerfiles must have `HEALTHCHECK` instruction for container orchestration.
- **Check Logic**:
  ```
  CHECK each Dockerfile (backend/, services/*/):
      IF missing HEALTHCHECK instruction:
          FAIL — no container health monitoring
      HEALTHCHECK must be:
          - HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3
          - CMD curl -f http://localhost:8000/health/ready || exit 1
  
  CHECK docker-compose.yml:
      IF healthcheck is overridden in compose, verify it's correct
      IF service depends on another service with depends_on:
          VERIFY condition: service_healthy is used
  ```
- **Mandatory**: Yes
- **Threshold**: All Dockerfiles have HEALTHCHECK
- **Failure Action**: BLOCK
- **Remediation**: Add HEALTHCHECK instruction to Dockerfile. Use application's `/health/ready` endpoint for meaningful health checking. Set appropriate intervals and timeouts.
- **Owner**: Platform Engineering
- **Last Updated**: 2026-07-17

---

### INFRA-003: Non-Root User
- **Gate**: Container Security
- **Description**: Containers must run as a non-root user (principle of least privilege).
- **Check Logic**:
  ```
  CHECK each Dockerfile:
      IF USER root or no USER directive (defaults to root):
          FAIL — container runs as root
  
      VERIFY non-root user is created:
          RUN addgroup --system gula && adduser --system --ingroup gula gula
          USER gula
  
  CHECK docker-compose.yml:
      IF user: root or user: "0": FAIL
  
  CHECK that non-root user has access to required directories:
      - /tmp (for temp files)
      - /var/lib/gula/ (for data)
      - Log files directory
      - These must be chown'd in Dockerfile
  ```
- **Mandatory**: Yes
- **Threshold**: All containers run as non-root
- **Failure Action**: BLOCK
- **Remediation**: Add user creation (`addgroup` + `adduser`) to Dockerfile. Add `USER gula` before CMD. Chown necessary directories. Update compose if user override is set.
- **Owner**: Platform Engineering
- **Last Updated**: 2026-07-17

---

### INFRA-004: Resource Limits Set
- **Gate**: Container Resource Governance
- **Description**: Docker Compose must specify resource limits (memory, CPU) for all services.
- **Check Logic**:
  ```
  CHECK docker-compose.yml and docker-compose.full.yml:
      FOR each service:
          IF no mem_limit or deploy.resources.limits.memory:
              WARN — no memory limit
          IF mem_limit is unrealistically low (< 128M for backend):
              WARN — possible OOM kills
          IF no cpus or deploy.resources.limits.cpus:
              WARN — no CPU limit
  
  CHECK that resource limits are proportional:
      - gula-backend: >= 512M (FastAPI + DB connections)
      - postgres: >= 1G (default 2G recommended)
      - redis: >= 128M
      - api-gateway (nginx): >= 128M
  ```
- **Mandatory**: No (Advisory)
- **Threshold**: Backend service has memory limit
- **Failure Action**: WARN
- **Remediation**: Add resource limits to docker-compose.yml. Set memory limits based on historical usage. Add CPU limits for production deployments.
- **Owner**: Platform Engineering
- **Last Updated**: 2026-07-17

---

## Clinical Safety Gates (4 rules)

### CLN-001: Optimistic Locking on LabResult
- **Gate**: Concurrent Result Modification Protection
- **Description**: Every `LabResult` mutation must check and increment the `version` column to prevent concurrent overwrites.
- **Check Logic**:
  ```
  CHECK backend/app/models/lab_result.py:
      VERIFY version column exists (Integer, default=1)
  
  CHECK all LabResult mutation code:
      FOR each UPDATE on LabResult:
          VERIFY version check: WHERE id = :id AND version = :current_version
          VERIFY version increment: SET version = version + 1
  
      FOR each ORM update:
          VERIFY that version column is loaded and checked before flush
  
  INTEGRATION TEST:
      SIMULATE concurrent updates to same LabResult
      EXPECT: Second update fails with StaleDataError or conflict
      IF no conflict detection: FAIL
  ```
- **Mandatory**: Yes
- **Threshold**: Optimistic locking verified on ALL LabResult mutations
- **Failure Action**: BLOCK
- **Remediation**: Add version column to LabResult model if missing. Add version check to all update operations. Use SQLAlchemy's `version_id_col` or manual version checking. Add integration test for concurrent modification.
- **Owner**: Backend Team Lead
- **Last Updated**: 2026-07-17

---

### CLN-002: Patient Data Integrity
- **Gate**: Data Consistency Validation
- **Description**: No duplicate order IDs, no orphaned results (results without parent orders), no negative values in numeric fields.
- **Check Logic**:
  ```
  DB INTEGRITY CHECKS:
      RUN queries to detect:
          - Duplicate lab_order.external_ids within same lab
          - lab_results without corresponding lab_orders
          - patients with duplicate national_id (plaintext, before encryption)
          - Results with negative values in numeric test fields
          - Orders with future dates > 30 days
  
      IF any integrity violation found:
          FAIL — data integrity issue
          LOG affected record IDs for manual review
  
  REFERENTIAL INTEGRITY:
      CHECK foreign key constraints are enforced (not deferred)
      CHECK CASCADE rules are correct (no accidental cascading deletes)
  ```
- **Mandatory**: Yes
- **Threshold**: Zero data integrity violations
- **Failure Action**: BLOCK
- **Remediation**: For duplicates: add unique constraint or cleanup script. For orphaned results: restore parent order or flag for review. For negative values: add CHECK constraint at DB level. Add application-level validation.
- **Owner**: Backend Team Lead
- **Last Updated**: 2026-07-17

---

### CLN-003: Complete Audit Trail
- **Gate**: Non-Repudiation
- **Description**: Every patient data write must have a corresponding audit log entry with cryptographic chain.
- **Check Logic**:
  ```
  AUDIT TRAIL VERIFICATION:
      FOR each mutation type (CREATE, UPDATE, DELETE):
          CHECK AuditLog for entries covering:
              - Patient demographics changes
              - Order creation/status changes
              - Result entry/modification/release
              - Sample tracking changes
  
      VERIFY hash chain integrity:
          FOR each audit entry:
              COMPUTE SHA-256(previous_hash + action + resource_id + timestamp)
              VERIFY stored hash matches computed hash
          IF hash chain broken:
              FAIL — tampered audit log
  
      CHECK that audit entries are immutable (no UPDATE/DELETE on AuditLog)
  ```
- **Mandatory**: Yes
- **Threshold**: Complete, unbroken audit chain
- **Failure Action**: BLOCK
- **Remediation**: Fix missing audit log calls in mutation code paths. Audit hash chain breaks indicate potential tampering — investigate immediately. Add database-level triggers if application-level logging is missed.
- **Owner**: Security Team Lead
- **Last Updated**: 2026-07-17

---

### CLN-004: Critical Alert Delivery Guarantee
- **Gate**: Patient Safety Alerting
- **Description**: Critical lab results (panic values) must have guaranteed, non-repudiable delivery notification.
- **Check Logic**:
  ```
  CODE REVIEW:
      TRACE critical result detection logic:
          - Where are critical/panic value thresholds defined?
          - How are critical results detected?
          - What notification channels are used?
  
      VERIFY delivery guarantees:
          - Alert is persisted (DB write before notification)
          - Delivery is tracked (sent, delivered, acknowledged)
          - Failed deliveries are retried with backoff
          - Escalation path exists for unacknowledged alerts
          - Audit log entry for critical alert lifecycle
  
      CHECK that critical alert route is exempt from concurrency limiting:
          ConcurrencyLimitMiddleware exempts critical-alerts
  
  INTEGRATION TEST:
      CREATE result with panic value
      VERIFY alert is created and notification sent
      VERIFY alert has delivery tracking (status, timestamps)
  ```
- **Mandatory**: Yes
- **Threshold**: Zero gaps in critical alert delivery chain
- **Failure Action**: BLOCK
- **Remediation**: Implement persistence-first alerting. Add delivery tracking and retry with exponential backoff. Create escalation procedure for unacknowledged alerts. Ensure concurrency limiter doesn't drop critical alerts.
- **Owner**: Clinical Safety Lead
- **Last Updated**: 2026-07-17

---

## Rule Index

| Category | Rules | Mandatory | Advisory | Blocking | Warning |
|----------|-------|-----------|----------|----------|---------|
| Architecture | 10 | 9 | 1 | 9 | 1 |
| Security | 12 | 12 | 0 | 12 | 0 |
| Testing | 10 | 8 | 2 | 8 | 2 |
| Documentation | 6 | 3 | 3 | 2 | 4 |
| Performance | 6 | 2 | 4 | 2 | 4 |
| Dependencies | 4 | 3 | 1 | 3 | 1 |
| Infrastructure | 4 | 3 | 1 | 3 | 1 |
| Clinical Safety | 4 | 4 | 0 | 4 | 0 |
| **Total** | **56** | **44** | **12** | **43** | **13** |

## Rule Review Cadence

- Quarterly: Full review of all rules for relevance and threshold adjustments
- Per-release: Rules with WARN level reviewed for potential upgrade to BLOCK
- As-needed: New rules added based on production incidents or security advisories
- Owner confirmation: Each rule owner confirms their rules annually

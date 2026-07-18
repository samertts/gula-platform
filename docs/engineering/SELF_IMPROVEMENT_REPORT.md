# GULA Platform Self-Improvement Engine

> Version 1.0 | Last Updated: 2026-07-17
> Owner: Platform Engineering
> Status: Proposed

---

## Overview

The Self-Improvement Engine (SIE) is a continuous analysis system that autonomously detects code quality issues, API health problems, database anomalies, security weaknesses, testing gaps, documentation gaps, and localization gaps. It runs alongside the Quality Review Engine to provide ongoing improvement recommendations beyond the release cycle.

The SIE operates on a **detect -> assess -> prioritize -> suggest -> track** model:

1. **Detect**: Automated scanners identify issues across 8 categories
2. **Assess**: Each finding is scored by severity, impact, and effort
3. **Prioritize**: Findings are ranked and entered into the improvement backlog
4. **Suggest**: Remediation suggestions are generated and attached to each finding
5. **Track**: Findings are tracked over time to measure improvement trends

---

## 1. Code Quality Issues

### 1.1 Duplicate Code Detection

**Detection Method**: AST-based analysis using pyastgrep or custom AST walking to identify structurally identical code blocks.

**Approach**:
- Parse each Python file into AST
- Compare subtree patterns across files (ignoring variable names, focusing on structure)
- Minimum match threshold: 10 consecutive AST nodes with identical structure
- File-level similarity > 60% flagged as potential file-level duplication

**Scanner Source**: `backend/app/core/quality_engine/scanners/improvement/code_quality_scanner.py`
**Priority**: P2 (High)
**Estimated Effort**: 4 hours initial scan + 1 hour/week ongoing
**Impact Estimate**: 2-3x maintenance burden per duplicated block; estimated 5-15% of codebase is duplicated

**Detection Criteria**:

| Threshold | Action |
|-----------|--------|
| > 10 lines duplicated in 3+ places | HIGH priority |
| > 20 lines duplicated in 2 places | MEDIUM priority |
| > 50% file similarity with another file | CRITICAL priority |
| > 30 lines duplicated across microservice stubs | MEDIUM priority |

**Likely Findings in GULA**:
- `services/lab/`, `services/order/`, `services/patient/`, `services/result/`, `services/sample/`, `services/notification/`, `services/ai/` — 7 near-identical stub structures (Dockerfile, main.py, health endpoint)
- CRUD patterns repeated across 36+ route files
- Test setup code duplicated across 28 test modules

### 1.2 Dead Code Detection

**Detection Method**: Multi-pass analysis:

1. **Import scan**: Find all `import X` and `from X import Y`, then check if Y is referenced elsewhere in the file
2. **Function call scan**: Find all `def func_name`, grep for `func_name(` across codebase
3. **Route registration check**: Verify all route modules are registered in `main.py` `register_routes()`
4. **Unused migration check**: Migrations older than 6 months that have been applied everywhere
5. **Unused env var scan**: Environment variables read but never referenced in logic

**Priority**: P3 (Medium)
**Estimated Effort**: 2 days initial scan + 2 hours/week ongoing
**Impact Estimate**: Dead code increases cognitive load, compilation time, and test maintenance

**Detection Criteria**:

| Type | Threshold | Priority |
|------|-----------|----------|
| Unused function | Not called anywhere | MEDIUM |
| Unused import | Imported but not referenced | LOW |
| Unregistered route module | Exists in routes/ but not in main.py registration | HIGH |
| Unused env var | Read in config.py but never referenced | LOW |
| Orphaned migration | Not referenced in alembic history | MEDIUM |

**Likely Findings in GULA**:
- `services/` stubs — entire directories of dead code (monolith is source of truth)
- `backend/services/` and `backend/core/` api/ subdirs — experimental stubs mentioned in CLAUDE.md as "avoid committing business logic there"
- Possibly unused imports in route files after refactoring
- Unused route modules if any were replaced but not cleaned up

### 1.3 Large File Detection

**Detection Method**: File line count analysis with thresholds.

**Thresholds**:
- > 500 lines: WARN (consider refactoring)
- > 1000 lines: CRITICAL (must refactor)
- > 2000 lines: BLOCKER (immediate refactoring required)

**Priority**: P3 (Medium)
**Estimated Effort**: 1 hour for identification; effort varies per file for refactoring
**Impact Estimate**: Large files are harder to understand, test, and maintain; they often violate single responsibility principle

**Current GULA Candidates**:
- `backend/app/main.py` — 350+ lines (middleware, lifespan, routes, background loops) — approaching threshold
- `backend/app/config.py` — ~200 lines but growing with each feature flag
- `backend/app/core/self_healing.py` — circuit breaker + degraded mode + health alert = possible candidate
- Route files with many endpoints (e.g., if a single route file handles CRUD for multiple resources)

### 1.4 Complex Function Detection

**Detection Method**: Cyclomatic complexity analysis using `radon` or `mccabe`.

**Thresholds**:
- Cyclomatic complexity > 10: WARN (moderately complex)
- Cyclomatic complexity > 20: FAIL (overly complex)
- Cyclomatic complexity > 30: CRITICAL (must refactor)

**Priority**: P2 (High)
**Estimated Effort**: 2 hours initial scan + ongoing CI integration
**Impact Estimate**: Complex functions are error-prone (higher bug density), hard to test (exponential test paths), and difficult to maintain

**Check Command**:
```bash
pip install radon
radon cc backend/app/ -s -a -n C
```

**Likely Findings in GULA**:
- `core/self_healing.py` — circuit breaker state machine with multiple transitions
- `domain/order_state.py` — lab order state machine with many states
- Socket/stream parsing code in `services/device_bridge/` — ASTM protocol parsers are inherently complex
- Any route handler with multiple business logic branches

### 1.5 Code Smell Detection

**Detection Method**: pylint + flake8 with extended checkers + custom rules.

**Smells Checked**:
- Too many branches in a single function (pylint R0912)
- Too many return statements (pylint R0911)
- Too many arguments (pylint R0913)
- Too many instance attributes (pylint R0902)
- Too many public methods (pylint R0904)
- Access to protected member outside class (pylint W0212)

**Priority**: P4 (Low)
**Estimated Effort**: 30 minutes initial scan
**Impact Estimate**: Code smells indicate future maintenance problems; not blocking but worth tracking

---

## 2. API Health

### 2.1 Unused API Endpoints

**Detection Method**: Analyze API access logs (nginx/gunicorn access logs) for endpoint usage over time.

**Approach**:
- Parse Nginx/Gunicorn access logs for the past N days
- Extract unique endpoint paths + HTTP methods
- Compare against registered route table from FastAPI app
- Flag endpoints with zero calls in the analysis window

**Scanner Source**: `backend/app/core/quality_engine/scanners/improvement/api_health_scanner.py`
**Priority**: P3 (Medium)
**Estimated Effort**: 1 day for log analysis setup
**Impact Estimate**: Unused endpoints indicate dead code, potential attack surface, and maintenance burden

**Detection Criteria**:

| Window | Zero Calls | Action |
|--------|-----------|--------|
| 7 days | Yes | WARN — possible unused |
| 30 days | Yes | FAIL — almost certainly unused |
| 90 days | Yes | CRITICAL — should deprecate and remove |

### 2.2 API Version Drift

**Detection Method**: Compare OpenAPI schema against actual route behavior.

**Approach**:
- Export OpenAPI schema from `/openapi.json`
- Compare against route definitions in `backend/app/routes/`
- Check for: undocumented parameters, missing response models, status code mismatches
- Parse Pydantic model definitions and verify they match API contract

**Priority**: P2 (High)
**Estimated Effort**: 1 day for comparison tooling
**Impact Estimate**: API drift causes client breakage, integration failures, and increased support burden

**Check Command**:
```bash
# Export spec
curl -s http://localhost:8000/openapi.json | python -m json.tool > /tmp/current-spec.json
# Compare with baseline
diff <(python -m json.tool docs/api/openapi-v2.1.0.json) /tmp/current-spec.json
```

### 2.3 Deprecated Endpoints Tracker

**Detection Method**: Grep for deprecation markers in route files.

**Items Tracked**:
- Routes with `@deprecated` decorator or docstring annotation
- Routes with `deprecated=True` in OpenAPI tags
- Routes with "deprecated" or "legacy" in the path
- Query parameters or headers marked as deprecated
- Response fields that are deprecated

**Priority**: P4 (Low)
**Estimated Effort**: 2 hours initial scan
**Impact Estimate**: Deprecated endpoints that aren't tracked can remain in the codebase indefinitely, confusing developers and accumulating tech debt

---

## 3. Database Health

### 3.1 Unused Tables Detection

**Detection Method**: Analyze `pg_stat_user_tables` for access patterns.

**Approach**:
- Query `pg_stat_user_tables` for `seq_scan`, `idx_scan`, `n_tup_ins`, `n_tup_upd`, `n_tup_del`
- Tables with zero scans and zero modifications in N days are candidates for removal
- Cross-reference with SQLAlchemy model definitions

**Scanner Source**: `backend/app/core/quality_engine/scanners/improvement/database_health_scanner.py`

**SQL Query**:
```sql
SELECT schemaname, relname, seq_scan, idx_scan,
       n_tup_ins, n_tup_upd, n_tup_del, n_live_tup
FROM pg_stat_user_tables
WHERE (seq_scan + idx_scan) = 0
  AND (n_tup_ins + n_tup_upd + n_tup_del) = 0
ORDER BY relname;
```

**Priority**: P3 (Medium)
**Estimated Effort**: 1 hour for query + analysis
**Impact Estimate**: Unused tables waste storage, slow backups, confuse developers, and may indicate incomplete features

**GULA Candidates**:
- Financial engine tables (Phase A — schema only, no routes yet): `fin_campaigns`, `fin_conversions`, `fin_fraud_flags`, etc.
- Any table created for experimental features that were never fully deployed

### 3.2 Missing Indexes Detection

**Detection Method**: Analyze `pg_stat_user_tables` for sequential scans on large tables.

**Approach**:
- Query tables with `seq_scan > 1000` and `n_live_tup > 10000`
- Cross-reference with existing indexes on those tables
- Identify frequently queried columns that lack indexes
- Check for foreign key columns without indexes

**SQL Query**:
```sql
SELECT schemaname, relname, seq_scan, idx_scan, n_live_tup,
       seq_scan::float / GREATEST(idx_scan, 1) AS seq_idx_ratio
FROM pg_stat_user_tables
WHERE n_live_tup > 10000
  AND seq_scan > 1000
ORDER BY seq_scan DESC;
```

**Priority**: P2 (High)
**Estimated Effort**: 2 hours for analysis + varies for index creation
**Impact Estimate**: Missing indexes cause slow queries, timeouts, and poor user experience

**Likely Findings in GULA**:
- `audit_logs` table — high write volume, queryable by `resource_type` and `resource_id`
- `outbox_events` — polled frequently, indexed by `status` and `created_at`
- Foreign key columns across all model relationships
- Date-range query columns (created_at, updated_at) on large tables

### 3.3 Large Tables Without Partitioning

**Detection Method**: Check table size via `pg_relation_size()` against partitioning status.

**Approach**:
- Query `pg_relation_size` for all tables
- Flag tables > 100MB without partitioning
- Flag tables > 1GB as CRITICAL

**SQL Query**:
```sql
SELECT relname,
       pg_size_pretty(pg_relation_size(relid)) AS size,
       n_live_tup AS row_estimate
FROM pg_stat_user_tables
WHERE pg_relation_size(relid) > 100 * 1024 * 1024  -- > 100MB
ORDER BY pg_relation_size(relid) DESC;
```

**Priority**: P3 (Medium)
**Estimated Effort**: 1 day analysis + 3-5 days per partitioned table migration
**Impact Estimate**: Large unpartitioned tables cause slow queries, maintenance challenges, and vacuum pressure

**GULA Candidates**:
- `audit_logs` — grows continuously, primary candidate for partitioning (by month)
- `outbox_events` — grows with usage, could be partitioned or have TTL
- `lab_results` — grows with lab workload, consider partitioning by lab_id or date
- `lab_orders` — grows with lab workload

### 3.4 Index Bloat Detection

**Detection Method**: Analyze index bloat using pgstattuple extension or estimated bloat queries.

**Approach**:
- Run estimated bloat analysis on all indexes
- Flag indexes with > 30% bloat
- Flag unused indexes (low scan count relative to size)

**Priority**: P4 (Low)
**Estimated Effort**: 2 hours initial analysis
**Impact Estimate**: Bloated indexes waste disk space and RAM, slow down writes

---

## 4. Dependency Health

### 4.1 Unused Packages

**Detection Method**: Import scan vs installed packages.

**Approach**:
- Parse all Python files for import statements
- Extract top-level package names
- Compare against `requirements.txt` / `requirements-dev.txt`
- Flag packages installed but never imported

**Scanner Source**: `backend/app/core/quality_engine/scanners/improvement/dependency_health_scanner.py`

**Check Command**:
```bash
# using pip-missing-reqs or similar
pip install pip-check-reqs
pip-extra-reqs backend/requirements.txt
```

**Priority**: P4 (Low)
**Estimated Effort**: 1 hour initial scan
**Impact Estimate**: Unused packages increase attack surface, image size, and dependency maintenance burden

**Likely Findings in GULA**:
- Development-only packages in production requirements
- Packages used during initial development but no longer needed
- Test framework packages in production dependencies

### 4.2 Outdated Packages

**Detection Method**: Compare installed versions against latest PyPI releases.

**Approach**:
- Run `pip list --outdated`
- Calculate version gap (major.minor.patch delta)
- Score based on gap size and security relevance

**Priority**: P2 (High)
**Estimated Effort**: 1 hour/week for review
**Impact Estimate**: Outdated packages accumulate security vulnerabilities and miss performance improvements

**Detection Criteria**:

| Version Gap | Action |
|-------------|--------|
| Patch behind (0.0.x) | LOW — update on next patch release |
| Minor behind (0.x.0) | MEDIUM — update on next minor release |
| Major behind (x.0.0) | HIGH — plan upgrade with breaking change assessment |
| Critical CVE available | CRITICAL — update immediately |

### 4.3 Duplicate Dependencies

**Detection Method**: Parse requirements files for same package with different versions.

**Approach**:
- Parse all requirements files
- Group by package name (normalized)
- Flag any package with multiple version constraints

**Priority**: P4 (Low)
**Estimated Effort**: 30 minutes
**Impact Estimate**: Duplicate entries indicate merge conflicts or sloppy requirements management

### 4.4 Dependency Tree Conflicts

**Detection Method**: Check for incompatible transitive dependencies.

**Approach**:
- Use `pip check` to verify all dependency requirements are satisfied
- Install in clean environment and check for warnings

**Priority**: P3 (Medium)
**Estimated Effort**: 30 minutes
**Impact Estimate**: Dependency conflicts can cause runtime import errors or subtle behavioral bugs

---

## 5. Security Weaknesses

### 5.1 Pattern-Based Vulnerability Scanning

**Detection Method**: Custom bandit plugins and pattern matching for GULA-specific vulnerability patterns.

**Patterns Checked**:

| Pattern | Severity | Description |
|---------|----------|-------------|
| `eval()`, `exec()` | HIGH | Arbitrary code execution risk |
| `pickle.loads()` | HIGH | Deserialization RCE |
| `yaml.load()` without Loader | MEDIUM | Unsafe YAML deserialization |
| `assert` in non-test code | MEDIUM | `assert` disabled with `-O` |
| `tempfile.mktemp()` | LOW | Race condition (use mkstemp) |
| Hardcoded IP addresses | LOW | Configuration issue |
| `requests` without timeout | MEDIUM | Connection hang risk |
| `subprocess` with `shell=True` | HIGH | Command injection |
| SQL string concatenation | HIGH | SQL injection (caught by QRE too) |
| MD5/SHA1 for security | HIGH | Weak cryptography |

**Scanner Source**: `backend/app/core/quality_engine/scanners/improvement/health_scanner.py`
**Priority**: P1 (Critical)
**Estimated Effort**: 1 day initial scan + automated in CI
**Impact Estimate**: Each pattern represents a potential security vulnerability

### 5.2 Configuration Drift Detection

**Detection Method**: Compare actual config against documented standards.

**Items Checked**:

| Check | Expected | Detection |
|-------|----------|-----------|
| `SECRET_KEY` length | >= 32 chars | Config parser |
| `ENCRYPTION_KEY` algorithm | AES-256-GCM | Config parser |
| Debug mode off | `DEBUG=false` | ENV check |
| Log level | `INFO` or `WARNING` | ENV check |
| CORS origins | Non-wildcard | Config parser |
| DB connection string | TLS enabled | Parsing check |
| Session timeout | <= 24h | Config parser |
| Password policy | >= 8 chars, complex | Config parser |

**Priority**: P2 (High)
**Estimated Effort**: 1 day for automated checker
**Impact Estimate**: Configuration drift is a common cause of security incidents and production issues

### 5.3 Missing Security Controls

**Detection Method**: Inventory of endpoints vs expected security controls.

**Controls Checked**:
- Rate limiting on all public endpoints
- Authentication on all non-public endpoints
- Audit logging on mutation endpoints
- Input validation (Pydantic models)
- CORS configured
- Security headers present
- HTTPS enforced (at proxy level)
- Session management (refresh tokens, expiry)

**Priority**: P1 (Critical)
**Estimated Effort**: 1 day for inventory
**Impact Estimate**: Missing security controls create exploitable gaps

### 5.4 Sensitive Data in Logs

**Detection Method**: Scan logging calls for patterns that might expose PII.

**Patterns to Flag**:
- `logger.info(...)` with `patient`, `national_id`, `phone`, `email`, `address`
- Using `str()` or `repr()` on model objects with PII fields
- Logging request bodies of PII-containing endpoints
- Exception logging that includes user data

**Priority**: P2 (High)
**Estimated Effort**: 1 day for scanning + review
**Impact Estimate**: PII in logs violates HIPAA/GDPR and creates data breach risk

---

## 6. Testing Gaps

### 6.1 Untested Routes

**Detection Method**: Compare route definitions against test coverage.

**Approach**:
- Scan `backend/app/routes/` for all `@router.get/post/put/delete/patch` decorators
- Scan `backend/tests/` for test functions that exercise each route
- Flag routes with no corresponding test by endpoint path

**Scanner Source**: `backend/app/core/quality_engine/scanners/improvement/testing_gap_scanner.py`
**Priority**: P2 (High)
**Estimated Effort**: 1 day for mapping + variable for test writing
**Impact Estimate**: Untested routes are a reliability risk, especially for clinical workflows

**Check Command Concept**:
```python
# Extract routes from source
route_patterns = grep -r "@router\." backend/app/routes/ | wc -l
# Extract test references
test_patterns = grep -r "client\.(get|post|put|delete)" backend/tests/ | wc -l
# Ratio gives a rough coverage indicator
```

### 6.2 Untested Models

**Detection Method**: Compare SQLAlchemy model definitions against test coverage.

**Approach**:
- Scan `backend/app/models/` for all model classes
- Scan `backend/tests/` for tests that create, query, or validate each model
- Flag models with no dedicated test coverage

**Priority**: P3 (Medium)
**Estimated Effort**: 1 day for mapping
**Impact Estimate**: Untested models may have validation gaps, relationship errors, or constraint issues

**GULA Model Inventory** (17+ models):
- `labs`, `lab_users`, `patients`, `lab_orders`, `lab_results`, `lab_samples`
- `outbox_events`, `audit_logs`
- `visits` (SNDHS Phase 1)
- `fin_campaigns`, `fin_conversions`, `fin_fraud_flags` (Financial Phase A)
- Subscription/tier models
- Notification models
- Edge platform models

### 6.3 Missing Test Categories

**Detection Method**: Inventory of test types vs expected categories.

**Expected Test Categories** (from CLAUDE.md):

| Category | Status | Coverage |
|----------|--------|----------|
| Unit tests | Partial | Need audit |
| Integration tests | Good | test_comprehensive.py |
| Security tests | Good | test_security.py |
| Stress/performance | Good | test_stress.py |
| Clinical interpretation | Good | test_system_improvements.py |
| Patient card tests | Good | test_patient_card.py |
| MPI matching | Good | test_mpi_matcher.py |
| Outbox service | Good | test_outbox_service.py |
| Feature flags | Good | test_feature_flags.py |
| Edge platform | Good | test_edge_platform.py |
| Stability assertions | Good | test_stability_assertions.py |
| Chaos tests | Good | tests/chaos/ |
| Migration tests | Good | CI pipeline |
| UI/E2E tests | MISSING | Not covered (backend-only) |
| Accessibility tests | MISSING | Not covered |
| Localization tests | MISSING | Not covered |
| Performance regression | Partial | CI, not automated comparison |

**Priority**: P2 (High)
**Estimated Effort**: Various
**Impact Estimate**: Missing test categories mean gaps in quality assurance

### 6.4 Flaky Test Database

**Detection Method**: Analyze test run history for intermittently failing tests.

**Metrics Tracked**:
- Pass rate over last 10 CI runs
- Tests that fail in CI but pass locally
- Tests with timing-dependent assertions
- Tests with shared state (DB fixtures that aren't isolated)

**Priority**: P3 (Medium)
**Estimated Effort**: 1 day for analysis + 1-2 days per fix
**Impact Estimate**: Flaky tests destroy confidence in the test suite and waste developer time

---

## 7. Documentation Gaps

### 7.1 Undocumented Endpoints

**Detection Method**: Compare OpenAPI schema against route docstrings.

**Approach**:
- Extract all route functions from `backend/app/routes/`
- Check for docstring or `description` parameter
- Check if they appear in `/openapi.json` with summary and description
- Flag routes without documentation

**Scanner Source**: `backend/app/core/quality_engine/scanners/improvement/doc_gap_scanner.py`
**Priority**: P3 (Medium)
**Estimated Effort**: 1 hour for scan + variable for writing docs
**Impact Estimate**: Poorly documented API increases integration time and support burden

### 7.2 Undocumented Modules

**Detection Method**: Check for `__init__.py` files with docstrings or separate README.md.

**Approach**:
- For each Python package (directory with `__init__.py`):
  - Check if `__init__.py` has module docstring
  - Check for README.md
  - Flag packages missing both

**Priority**: P4 (Low)
**Estimated Effort**: 2 hours initial scan
**Impact Estimate**: Undocumented modules slow down developer onboarding and code comprehension

### 7.3 Missing READMEs

**Detection Method**: Directory inventory for README.md presence.

**Required README Locations** (from CLAUDE.md):
- `backend/app/routes/` — overview of 36 route modules
- `backend/app/models/` — entity relationship overview
- `backend/app/services/` — service layer patterns
- `backend/app/core/` — core infrastructure overview
- `backend/app/security/` — auth patterns
- `services/` — microservice stubs overview
- `frontend-v2/` — frontend architecture

**Priority**: P4 (Low)
**Estimated Effort**: 1 day for all READMEs
**Impact Estimate**: Missing READMEs hinder developer productivity and knowledge sharing

### 7.4 Stale Documentation

**Detection Method**: Compare last modification dates of docs vs source code they describe.

**Approach**:
- For each doc in `docs/`, identify which code it documents
- Compare last git commit date of doc vs source
- Flag docs that haven't been updated in > 6 months while source has changed

**Priority**: P3 (Medium)
**Estimated Effort**: 1 day for analysis
**Impact Estimate**: Stale documentation actively misleads developers and causes bugs

---

## 8. Localization Gaps

### 8.1 Untranslated Strings

**Detection Method**: Scan for i18n function calls with missing translations.

**Approach**:
- Parse frontend code for i18n translation keys (`t()`, `i18n.t()`, etc.)
- Compare against translation files (JSON, PO, etc.)
- Flag keys present in source but missing in Arabic translation file
- Flag keys present in English but missing in Arabic

**Scanner Source**: `backend/app/core/quality_engine/scanners/improvement/i18n_scanner.py`
**Priority**: P2 (High)
**Estimated Effort**: 1 day for scan + ongoing per PR
**Impact Estimate**: Untranslated strings break the Arabic-first UX promise

**GULA Concerns**:
- Arabic-first platform means Arabic translations must be complete before English additions
- Clinical terminology must be translated by domain experts, not machine translation
- Frontend-v2 (React) and frontend (PWA) may have separate i18n systems

### 8.2 Missing RTL Support Checks

**Detection Method**: Scan for RTL layout properties in CSS/Frontend code.

**Checks**:
- CSS files must have `[dir="rtl"]` or logical properties (`margin-inline-start` instead of `margin-left`)
- JavaScript components must handle RTL text direction
- Third-party UI components must support RTL
- Bidirectional text (Arabic + English numbers) must render correctly
- Form inputs must align correctly in RTL mode

**Priority**: P3 (Medium)
**Estimated Effort**: 2 days for frontend components
**Impact Estimate**: Broken RTL support makes the platform unusable for Arabic-speaking users

### 8.3 Number and Date Formatting

**Detection Method**: Scan for locale-sensitive formatting that may not handle Arabic correctly.

**Checks**:
- Date formatting uses locale-aware libraries (not hardcoded en-US format)
- Number formatting handles Arabic (Hindi) digits: 123 -> 123 in Eastern Arabic
- Calendar calculations account for Islamic calendar coexistence
- Time formats respect 12h/24h preference per locale

**Priority**: P3 (Medium)
**Estimated Effort**: 1 day for audit
**Impact Estimate**: Wrong number/date formatting causes clinical data misinterpretation

### 8.4 Text Expansion and Truncation

**Detection Method**: Layout testing with Arabic text samples.

**Checks**:
- Arabic text is typically 25-35% shorter than English (fewer characters)
- But Arabic glyphs are wider, so visual length may differ
- UI components must accommodate text expansion when switching locales
- Tables and data grids must handle longer Arabic text
- Button/action labels must not truncate in Arabic

**Priority**: P4 (Low)
**Estimated Effort**: 1 day for UI audit
**Impact Estimate**: Truncated text in clinical UI could cause misreading of critical values

---

## 9. Implementation Architecture

### 9.1 SIE Pipeline

```
                    ┌────────────────────┐
                    │  SIE Scheduler     │
                    │  (cron: daily)     │
                    └────────┬───────────┘
                             │
                    ┌────────▼───────────┐
                    │  Detection Engine  │
                    │  (scanners pool)   │
                    └────────┬───────────┘
                             │
                    ┌────────▼───────────┐
                    │  Scoring Engine    │
                    │  (priority calc)   │
                    └────────┬───────────┘
                             │
                    ┌────────▼───────────┐
                    │  Backlog Ingest    │
                    │  (IMPROVEMENT_BACKLOG.md)│
                    └────────┬───────────┘
                             │
                    ┌────────▼───────────┐
                    │  Report Generator  │
                    │  (weekly summary)  │
                    └────────┬───────────┘
                             │
                    ┌────────▼───────────┐
                    │  Notification      │
                    │  (Slack dashboard) │
                    └────────────────────┘
```

### 9.2 Scoring Formula

```
Finding Priority Score = (Impact × 3) + (Urgency × 2) + (Effort_Inverse × 1)

Where:
  Impact: 1-10 (patient safety impact, security risk, revenue impact, user satisfaction)
  Urgency: 1-10 (how quickly does this need addressing)
  Effort_Inverse: 10 - effort_rating (1 = quick fix, 10 = multi-month project)
```

### 9.3 Weekly Report Format

```markdown
# GULA Self-Improvement Report: Week {N}

**Period**: {start_date} — {end_date}
**Total Findings**: {count}
**New**: {new} | **Resolved**: {resolved} | **Carried Over**: {carried}

### Top 5 Priorities This Week
1. [P1] {finding} — {score}
2. [P2] {finding} — {score}
3. [P2] {finding} — {score}
4. [P3] {finding} — {score}
5. [P3] {finding} — {score}

### Trend
- Code Quality: {trend_indicator} ({delta}% vs last week)
- Security: {trend_indicator} ({delta}% vs last week)
- Testing: {trend_indicator} ({delta}% vs last week)
- Documentation: {trend_indicator} ({delta}% vs last week)
- Dependencies: {trend_indicator} ({delta}% vs last week)

### Improvements Made
- {description of fix or improvement}

### Recommendations
- {action item 1}
- {action item 2}
```

---

## 10. Integration with Quality Review Engine

The SIE feeds findings into the QRE's rule system and vice versa:

```
SIE Detections                       QRE Gates
     |                                   |
     |  Unused endpoint detected          |
     |----------------------------------->| New rule: DEPRECATED-001
     |                                   |
     |  QRE gate failure                  |
     |<-----------------------------------| SIE root cause analysis
     |                                   |
     |  Duplicate code cluster           |
     |----------------------------------->| Arch scanner: dedup check
     |                                   |
     |  Missing test coverage            |
     |----------------------------------->| Test scanner: coverage gate
     |                                   |
```

The combined pipeline runs:
1. **Daily**: SIE full scan (all 8 categories) — results stored, weekly report generated
2. **Pre-release**: QRE full scan (11 categories, blocking) — SIE historical data used for trend gates
3. **On-demand**: Both engines runnable via CLI with specific focus areas

---

## 11. File Layout

```
backend/app/core/quality_engine/
└── scanners/
    └── improvement/
        ├── __init__.py
        ├── base_improvement_scanner.py   # Base class for SIE scanners
        ├── code_quality_scanner.py       # Duplicate code, dead code, large files, complexity
        ├── api_health_scanner.py         # Unused endpoints, API drift, deprecated endpoints
        ├── database_health_scanner.py    # Unused tables, missing indexes, large tables
        ├── dependency_health_scanner.py  # Unused/outdated/duplicate packages
        ├── security_weakness_scanner.py  # Pattern vulns, config drift, missing controls
        ├── testing_gap_scanner.py        # Untested routes/models/categories
        ├── doc_gap_scanner.py            # Undocumented endpoints/modules/READMEs
        ├── i18n_scanner.py               # Untranslated strings, RTL support
        └── improvement_scheduler.py      # Daily/weekly scheduling and reporting
```

---

*This document is maintained by Platform Engineering. Refresh quarterly.*

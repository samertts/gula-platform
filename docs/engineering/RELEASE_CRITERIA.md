# GULA Platform Release Criteria

> Version 1.0 | Last Updated: 2026-07-17
> Owner: Platform Engineering
> Applies to: GULA Platform v2.1.0+

---

## 1. Release Levels

GULA platform defines four release levels based on change scope and risk:

| Level | Version Bump | Examples | Risk | Urgency | Approval |
|-------|-------------|----------|------|---------|----------|
| **Hotfix** | 2.1.0 → 2.1.1 | Critical security fix, patient safety fix, production outage | Critical | Immediate (< 4h) | On-call engineer + CTO |
| **Patch** | 2.1.0 → 2.1.1 | Bug fixes, minor improvements, dependency updates | Low | Days | Backend Lead |
| **Minor** | 2.1.0 → 2.2.0 | New features, route additions, model changes | Medium | 1-2 weeks | Platform Engineering Lead |
| **Major** | 2.1.0 → 3.0.0 | Breaking changes, architecture changes, major new subsystems | High | 1-3 months | CTO + review board |

### 1.1 Hotfix Criteria
- Fixes a CRITICAL severity security vulnerability
- Resolves patient data integrity issue
- Fixes production outage (platform unavailable)
- No new features, no schema changes unless required for the fix
- Bypasses most quality gates — only syntax + security + migration checks required

### 1.2 Patch Criteria
- Bug fixes for reported issues
- Non-critical security patches (MODERATE/LOW severity)
- Documentation updates
- Dependency updates (patch-level)
- Non-functional improvements (logging, monitoring, refactoring)
- No database schema changes (unless backwards-compatible additive)

### 1.3 Minor Criteria
- New features and enhancements
- New API endpoints (non-breaking)
- Database schema additions (new tables, new nullable columns)
- New integrations or third-party service connections
- Performance improvements
- Testing infrastructure improvements

### 1.4 Major Criteria
- Breaking API changes (request/response shape changes)
- Architecture changes (new microservices, database engine changes)
- Removal or deprecation of endpoints or features
- Major dependency framework upgrades (FastAPI major, SQLAlchemy major)
- Security architecture changes (auth provider swap, encryption algorithm change)

---

## 2. Mandatory Gates (Fail = Release Blocked)

These gates are evaluated in order. Any failure blocks the release pipeline.

### 2.1 GATE-SYN: Syntax Gate

**Check**: `python -m py_compile` on every `.py` file in `backend/app/` and `backend/migrations/`.

```bash
find backend/app backend/migrations -name '*.py' -exec python -m py_compile {} \;
```

**Execution Time**: < 30 seconds
**Failure Action**: **BLOCK** — release pipeline stops immediately
**Override**: None — impossible to override syntax errors
**Owner**: All developers (pre-commit check)

### 2.2 GATE-MIG: Migration Check

**Check**: Alembic upgrade + downgrade round-trip on clean database.

```bash
# Fresh PostgreSQL
docker compose down -v && docker compose up -d postgres
sleep 5  # wait for postgres

# Upgrade
docker compose run --rm gula-backend alembic upgrade head

# Verify required tables
docker compose run --rm gula-backend python -c "
from app.database import engine
from sqlalchemy import inspect
inspector = inspect(engine)
required = {'labs', 'lab_users', 'patients', 'lab_orders', 'lab_results', 'outbox_events', 'audit_logs'}
tables = set(inspector.get_table_names())
assert required.issubset(tables), f'Missing tables: {required - tables}'
print(f'All {len(tables)} tables present. Required tables verified.')
"

# Downgrade + re-upgrade
docker compose run --rm gula-backend alembic downgrade -1
docker compose run --rm gula-backend alembic upgrade head
```

**Execution Time**: 1-3 minutes
**Failure Action**: **BLOCK** — migration safety not guaranteed
**Override Possible?**: Yes — only for hotfix (CTO approval required)
**Owner**: Backend Team Lead

### 2.3 GATE-SMOKE: Smoke Test

**Check**: All health endpoints respond with HTTP 200.

```bash
# Start application
docker compose up -d gula-backend
sleep 10  # wait for startup

# Health endpoints check
endpoints=("/health" "/health/live" "/health/ready" "/health/status" "/health/deep" "/docs")
for ep in "${endpoints[@]}"; do
    status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000$ep)
    if [ "$status" != "200" ]; then
        echo "FAIL: $ep returned $status"
        exit 1
    fi
    echo "PASS: $ep → $status"
done
```

**Execution Time**: 30 seconds
**Failure Action**: **BLOCK**
**Override Possible?**: Yes — only for hotfix (on-call engineer + CTO)
**Owner**: Platform Engineering

### 2.4 GATE-SEC: Security Scan

**Check**: No CRITICAL or HIGH vulnerabilities in dependencies. No hardcoded secrets.

```bash
# Dependency CVE scan
safety check -r backend/requirements.txt --full-report
pip-audit -r backend/requirements.txt

# Secret scanning
gitleaks detect --source . --verbose
bandit -ll -ii -r backend/app/

# Docker security
hadolint backend/Dockerfile
```

**Execution Time**: 2-5 minutes
**Failure Action**: **BLOCK** for CRITICAL/HIGH
**Override Possible?**: Yes — documented exception (Security Lead + CTO)
**Owner**: Security Team Lead

### 2.5 GATE-TEST-CRITICAL: Critical Path Tests

**Check**: All tests for core business operations pass.

```bash
# Run specific critical path test files
pytest backend/tests/test_comprehensive.py -v --tb=short
pytest backend/tests/test_security.py -v --tb=short
pytest backend/tests/test_stability_assertions.py -v --tb=short
pytest backend/tests/test_patient_card.py -v --tb=short
pytest backend/tests/test_mpi_matcher.py -v --tb=short

# Additionally test all order/result/sample/patient routes
pytest backend/tests/ -v -k "order or result or sample or patient" --tb=short
```

**Execution Time**: 5-15 minutes
**Failure Action**: **BLOCK**
**Override Possible?**: No — patient data integrity is non-negotiable
**Owner**: Quality Engineering Lead

### 2.6 GATE-LINT: Lint Check

**Check**: flake8 error-only check (E9, F821 categories).

```bash
flake8 --select=E9,F821 backend/app/
```

**Execution Time**: < 10 seconds
**Failure Action**: **BLOCK** — these are runtime error patterns
**Override Possible?**: No — indicates real bugs
**Owner**: All developers

### 2.7 GATE-MIGRATION-RUNBOOK: Migration Documentation

**Check**: If new migrations exist, a migration runbook must be present.

**Execution Time**: Automatic (document check)
**Failure Action**: **BLOCK** (migration releases only)
**Override Possible?**: Yes — for patches with trivial migrations (Backend Lead)
**Owner**: Backend Team Lead

### 2.8 GATE-CLINICAL: Clinical Safety

**Check**: Optimistic locking, data integrity, audit trail, critical alert checks.

```bash
pytest backend/tests/ -v -k "locking or integrity or audit or alert" --tb=short
# Plus static analysis for tenant isolation
python -m backend.app.core.quality_engine.runner --scanners clinical_safety
```

**Execution Time**: 2-5 minutes
**Failure Action**: **BLOCK** — patient safety critical
**Override Possible?**: No — never override patient safety
**Owner**: Clinical Safety Lead

---

## 3. Advisory Gates (Fail = Warn, Manual Override Available)

These gates generate warnings that must be acknowledged but do not block the pipeline.

### 3.1 GATE-PERF: Performance Budgets

| Check | Threshold | Warning Action |
|-------|-----------|----------------|
| p95 API latency | < 500ms | WARN if exceeded |
| p95 health latency | < 200ms | WARN if exceeded |
| N+1 query patterns | Zero | WARN if detected |
| Connection pool budget | < 80% of max | WARN if exceeded |

**Override**: Engineering Lead acknowledges performance impact and schedules optimization.

### 3.2 GATE-DOCS: Documentation Completeness

| Check | Threshold | Warning Action |
|-------|-----------|----------------|
| OpenAPI docs completeness | All public routes | WARN for missing |
| Module READMEs | All packages | WARN for missing |
| ADR coverage | Significant changes | WARN for missing |
| Changelog | Up to date | WARN if outdated |
| `.env.example` alignment | All vars documented | WARN for drift |

**Override**: PM acknowledges and accepts documentation debt.

### 3.3 GATE-COVERAGE: Test Coverage Thresholds

| Check | Threshold | Warning Action |
|-------|-----------|----------------|
| Overall line coverage | ≥ 70% | WARN if below |
| Core module coverage | ≥ 85% | WARN if below |
| New code coverage | ≥ 80% | WARN if below |

**Override**: Quality Lead approves with coverage improvement plan.

### 3.4 GATE-DEPS: Dependency Freshness

| Check | Threshold | Warning Action |
|-------|-----------|----------------|
| Packages >2 major versions behind | Zero | WARN |
| Unmaintained packages (>2y no update) | Zero | WARN |
| Duplicate packages | Zero | WARN |

**Override**: Backend Lead acknowledges and schedules updates.

### 3.5 GATE-ARCH: Architecture Compliance

| Check | Threshold | Warning Action |
|-------|-----------|----------------|
| Circular dependencies | Zero | WARN if detected |
| Layer violations | Zero | WARN if detected |
| Import convention issues | < 5 | WARN if exceeded |
| Monolith boundary violations | Zero | WARN if detected |

**Override**: Platform Engineering Lead approves with remediation plan.

---

## 4. Release Artifacts

Every release must produce the following artifacts:

### 4.1 Software Bill of Materials (SBOM)

**Format**: SPDX 2.3 JSON (preferred) or CycloneDX
**Generation**:
```bash
# Python SBOM
pip-licenses --format=json --with-urls --with-license-file > sbom/python-sbom.json

# Container SBOM
docker scout sbom gula-backend:latest > sbom/container-sbom.spdx.json

# Frontend SBOM (if included)
cd frontend-v2 && npm list --json > ../sbom/frontend-sbom.json
```

**Contents**:
- All Python packages (direct + transitive) with versions and licenses
- Base Docker image information
- System packages (if applicable)
- Frontend packages (npm)

**Attached to**: GitHub Release

### 4.2 Changelog

**Format**: Markdown, following Keep a Changelog convention
**Required sections**:
- Added (new features)
- Changed (behavior changes)
- Deprecated (features to be removed)
- Removed (removed features)
- Fixed (bug fixes)
- Security (security patches)
- Migration notes (if schema changes)

**Validation**: Every commit message category should map to a changelog entry.

### 4.3 Migration Plan

**Required for**: Any release with DB migrations
**Contents**:
- Migration files included
- Expected execution duration
- Lock duration and affected tables
- Required downtime (if any)
- Verification queries to confirm migration success
- Rollback script reference

**Example**:
```markdown
## Migration Plan: v2.2.0

### Migrations
1. `20260717_0001_add_patient_phone_index.py` — adds index, zero-downtime
2. `20260717_0002_add_visit_id_to_orders.py` — adds nullable column, zero-downtime

### Duration
- Migration 1: ~2 seconds (index creation, concurrent)
- Migration 2: ~1 second (nullable column add)
- Total: ~3 seconds, no downtime

### Verification
```sql
SELECT count(*) FROM lab_orders WHERE visit_id IS NOT NULL;
SELECT * FROM pg_indexes WHERE tablename = 'patients';
```

### Rollback
Run: `alembic downgrade -2` or refer to docs/migrations/rollback-v2.2.0.sql
```

### 4.4 Rollback Plan

**Required for**: ALL releases
**Contents**:
- Deployment rollback procedure (docker compose down + previous version)
- Database rollback command (alembic downgrade)
- Data reversion steps (if migration changes data)
- Expected rollback duration
- Rollback verification steps

**Example**:
```markdown
## Rollback Plan: v2.2.0 → v2.1.0

### Deployment Rollback
```bash
docker compose down
docker compose -f docker-compose.yml -f docker-compose.rollback.yml up -d
```

### Database Rollback
```bash
# If only 1 migration was applied
alembic downgrade -1

# If multiple migrations were applied
alembic downgrade <previous_revision>
```

### Data Verification
```sql
-- Verify rollback succeeded
SELECT version FROM alembic_version;
```

### Duration
- Deployment rollback: ~30 seconds
- DB rollback: ~2 seconds
- Total: ~1 minute

### Risk
- Data written between migration and rollback may be lost
- Rollback must happen before any new data relies on new schema
```

### 4.5 Quality Review Report

**Format**: JSON + Markdown (generated by Quality Review Engine)
**Minimum content**: Scorecard with all mandatory gate results, overall grade, blocking issues
**Attached to**: PR description + GitHub Release

### 4.6 Release Tag

```bash
git tag -a v2.2.0 -m "GULA Platform v2.2.0

Release notes:
- Added patient phone number indexing
- Fixed audit log hash chain verification
- Updated FastAPI to 0.110.x

See CHANGELOG.md for full details."
git push origin v2.2.0
```

---

## 5. Approval Matrix

| Level | Required Approvals | Gate Override Authority |
|-------|-------------------|------------------------|
| **Hotfix** | On-call engineer + CTO | CTO (any gate) |
| **Patch** | Backend Lead + Quality Lead | Backend Lead (advisory gates only) |
| **Minor** | Platform Engineering Lead + Product Lead + Quality Lead | Platform Engineering Lead (advisory), CTO (mandatory) |
| **Major** | CTO + Review Board (Engineering + Product + Clinical Safety) | Review board majority vote |

### 5.1 Approval Workflow

```
                    ┌─────────────────────┐
                    │  Release Candidate  │
                    │  (git tag -rc)      │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Automated Gates    │
                    │  (all mandatory)    │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Advisory Gate      │
                    │  Warnings Review    │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Approval Step      │
                    │  (per matrix above) │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Release Artifacts  │
                    │  Generated          │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Final Tag & Deploy │
                    │  (git tag v2.x.x)   │
                    └─────────────────────┘
```

### 5.2 Approval Form Template

```markdown
## Release Approval: GULA Platform v{version}

**Level**: {hotfix|patch|minor|major}
**Release Manager**: {name}
**Target Date**: {date}

### Gate Status
- [ ] GATE-SYN: Syntax Gate — {PASS/FAIL}
- [ ] GATE-MIG: Migration Check — {PASS/FAIL}
- [ ] GATE-SMOKE: Smoke Test — {PASS/FAIL}
- [ ] GATE-SEC: Security Scan — {PASS/FAIL}
- [ ] GATE-TEST-CRITICAL: Critical Tests — {PASS/FAIL}
- [ ] GATE-LINT: Lint Check — {PASS/FAIL}
- [ ] GATE-MIGRATION-RUNBOOK: Migration Docs — {PASS/FAIL/NA}
- [ ] GATE-CLINICAL: Clinical Safety — {PASS/FAIL}
- [ ] GATE-PERF: Performance — {PASS/WARN}
- [ ] GATE-DOCS: Documentation — {PASS/WARN}
- [ ] GATE-COVERAGE: Coverage — {PASS/WARN}
- [ ] GATE-DEPS: Dependencies — {PASS/WARN}
- [ ] GATE-ARCH: Architecture — {PASS/WARN}

### Advisory Overrides
| Gate | Warning | Acknowledged By | Follow-up |
|------|---------|-----------------|-----------|
| ... | ... | ... | ... |

### Approvals
- [ ] {Role}: {Name} — {Date}
- [ ] {Role}: {Name} — {Date}
- [ ] {Role}: {Name} — {Date}

### Release Decision
- [ ] **APPROVED** — Proceed with release
- [ ] **DENIED** — Blocked until issues resolved
- [ ] **CONDITIONAL** — Approved with conditions: {conditions}
```

---

## 6. Release Checklist

### 6.1 Pre-Release (48-24 hours before)

- [ ] **Code Review Complete**: All PRs merged with required approvals
- [ ] **Feature Freeze**: No new features; only bug fixes and release prep
- [ ] **Changelog Updated**: All notable changes documented
- [ ] **Version Bumped**: `backend/app/config.py` version updated
- [ ] **Migration Plan Written**: If schema changes, runbook prepared
- [ ] **Rollback Plan Written**: Procedures documented
- [ ] **Quality Review Triggered**: `make quality-check`

### 6.2 Release Day

- [ ] **Mandatory Gates Run**: All 8 mandatory gates pass
- [ ] **Advisory Gates Reviewed**: Warnings acknowledged or resolved
- [ ] **SBOM Generated**: `make sbom`
- [ ] **Artifacts Collected**: Report, SBOM, changelog, migration/rollback plans
- [ ] **Release Candidate Tagged**: `git tag v{version}-rc1 && git push origin v{version}-rc1`
- [ ] **Staging Deployed**: RC deployed to staging environment
- [ ] **Smoke Test in Staging**: All health endpoints respond
- [ ] **Integration Test in Staging**: Critical path tests pass
- [ ] **Approval Gathered**: Required approvers sign off
- [ ] **Final Tag Created**: `git tag v{version} && git push origin v{version}`

### 6.3 Deployment

- [ ] **Backup Database**: `make backup`
- [ ] **Notify Stakeholders**: Slack #releases channel announcement
- [ ] **Deploy**: `docker compose pull && docker compose up -d`
- [ ] **Verify Deployment**: `make health-deep`
- [ ] **Run Migration**: `alembic upgrade head` (if applicable)
- [ ] **Verify Migration**: Run verification queries
- [ ] **Monitor**: Watch logs and metrics for 15 minutes post-deploy
- [ ] **Confirm**: All health endpoints GREEN

### 6.4 Post-Release (24 hours after)

- [ ] **Monitor Incident Logs**: No spike in 5xx errors or slow queries
- [ ] **Verify No Regression**: Compare quality scores with pre-release
- [ ] **Update Release Notes**: GitHub Release published
- [ ] **Close Release Issue**: All release tasks completed
- [ ] **Retrospective**: (for major releases) Schedule retro within 1 week

### 6.5 Rollback Triggers

**Immediate rollback required if**:
- Critical endpoint returns 5xx > 1% of requests
- Patient data integrity issue detected
- Security vulnerability exposed by release
- Database migration causes data loss or corruption
- Performance regression > 2x baseline

**Rollback steps**:
```bash
# 1. Notify team in #releases
# 2. Revert deployment
docker compose pull gula-backend:v{previous_version}
docker compose up -d

# 3. Revert database (if migration applied)
alembic downgrade {previous_revision}

# 4. Verify rollback
make health-deep
make quality-scorecard

# 5. Post-mortem
```

---

## 7. Quality Gate Automation

### 7.1 GitHub Actions Integration

```yaml
# .github/workflows/release-gates.yml
name: Release Gates

on:
  push:
    tags:
      - 'v*.*.*-rc*'

jobs:
  mandatory-gates:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: GATE-SYN — Syntax Check
        run: |
          find backend/app backend/migrations -name '*.py' -exec python -m py_compile {} \;
      
      - name: GATE-MIG — Migration Check
        run: |
          docker compose down -v && docker compose up -d postgres
          sleep 10
          docker compose run --rm gula-backend alembic upgrade head
          # ... full migration round-trip
      
      - name: GATE-SMOKE — Smoke Test
        run: |
          docker compose up -d gula-backend
          sleep 15
          for ep in /health /health/live /health/ready; do
            curl -sf http://localhost:8000$ep || exit 1
          done
      
      - name: GATE-SEC — Security Scan
        run: |
          safety check -r backend/requirements.txt --full-report
          bandit -ll -ii -r backend/app/
      
      - name: GATE-TEST — Critical Tests
        run: |
          pip install -r backend/requirements-dev.txt
          pytest backend/tests/test_security.py -v --tb=short
          pytest backend/tests/test_comprehensive.py -v --tb=short
      
      - name: GATE-LINT — Flake8
        run: |
          flake8 --select=E9,F821 backend/app/
      
      - name: All Gates Pass
        run: echo "✅ All mandatory release gates passed"
```

### 7.2 Makefile Integration

```makefile
# Release targets
.PHONY: release-check release-staging release-production

# Full pre-release verification
release-check:
	@echo "Running release verification..."
	$(MAKE) lint
	$(MAKE) health
	$(MAKE) quality-check
	$(MAKE) test
	@echo "✅ Release verification complete"

# Stage release candidate
release-staging: release-check
	@echo "Deploying to staging..."
	docker compose -f docker-compose.yml -f docker-compose.staging.yml up -d
	@echo "✅ Staging deployment complete"
	@echo "Run 'make health-deep' to verify"

# Production release
release-production: release-staging
	@echo "Proceeding with production release..."
	@echo "Step 1: Backup database"
	$(MAKE) backup
	@echo "Step 2: Deploy"
	docker compose pull && docker compose up -d
	@echo "Step 3: Verify"
	$(MAKE) health-deep
	@echo "✅ Production release complete"
```

---

## 8. Exception Process

When a mandatory gate cannot be met but a release is still required:

1. **Document the exception**: Create entry in `docs/release-exceptions/` with date, gate, reason
2. **Risk assessment**: Engineering Lead documents risk of proceeding
3. **Mitigation plan**: What compensating controls are in place
4. **Approval**: Per approval matrix, the designated authority signs off
5. **Follow-up**: Create JIRA issue to resolve the root cause within specified timeframe
6. **Accountability**: Exception count tracked per-team, reviewed quarterly

```markdown
# Release Exception: v2.1.1

**Date**: 2026-07-17
**Gate**: GATE-SEC — Security Scan
**Reason**: Safety check for `cryptography` package reports CVE-2026-XXXX (MEDIUM)
**Risk**: Low — CVE affects edge case not used by GULA
**Mitigation**: Input validation already prevents attack vector
**Approved By**: Security Lead (signature)
**Follow-up**: Upgrade cryptography to 42.0.5 in next patch release
**Tracking Issue**: #1234
```

---

## 9. Version Numbering

GULA follows semantic versioning: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes (incompatible API changes, architecture changes)
- **MINOR**: New features (backwards-compatible additions)
- **PATCH**: Bug fixes (backwards-compatible fixes)

Current version: **2.1.0** (from `backend/app/config.py`)

Pre-release suffixes:
- `-rc.N` (release candidate, e.g., `2.2.0-rc.1`)
- `-alpha.N` (alpha, e.g., `2.2.0-alpha.1`)
- `-beta.N` (beta, e.g., `2.2.0-beta.1`)

---

## 10. Release Communication Template

```markdown
## Release: GULA Platform v{version}

**Status**: {deploying|deployed|rolled back}
**Date**: {date}
**Duration**: {deployment duration}
**Release Manager**: {name}

### Changes
{changelog summary}

### Migration
{database changes, if any}

### Verification
{health check results}

### Monitoring
Link to Grafana dashboard: {url}
Link to Sentry: {url}

### Rollback
If issues detected, rollback procedure: {link to rollback plan}
```

---

*This document is maintained by Platform Engineering. Review quarterly or after any release incident.*

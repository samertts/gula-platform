# GULA Platform Quality Review Engine

> Version 2.0 | Last Updated: 2026-07-17
> Owner: Platform Engineering
> Status: Active

## 1. Engine Architecture

### 1.1 Overview

The Quality Review Engine (QRE) is an autonomous, event-driven pipeline that inspects the GULA platform before every release, nightly, and on-demand. It implements a scanner/dispatcher/orchestrator/reporter pattern to provide comprehensive quality assessment across 11 scan categories.

### 1.2 Architecture Diagram

```
                     ┌─────────────────────────────────────┐
                     │      QRE Orchestrator Service        │
                     │  (backend/app/core/quality_engine/)  │
                     └──────┬──────────┬──────────┬────────┘
                            │          │          │
                   ┌────────▼──┐ ┌─────▼─────┐ ┌─▼──────────┐
                   │  Scanner  │ │  Scanner  │ │  Scanner    │
                   │  Dispatcher│ │  Registry │ │  Scheduler │
                   └────────┬──┘ └─────┬─────┘ └─────┬──────┘
                            │          │              │
                   ┌────────▼──────────▼──────────────▼──────┐
                   │           Scanner Plugin Pool           │
                   │  (11 plugin types, each in own module)  │
                   │                                         │
                   │  arch     security   testing    docs    │
                   │  perf     a11y      i18n       deps    │
                   │  infra    compliance clin_safety        │
                   └──────────────────┬──────────────────────┘
                                      │
                   ┌──────────────────▼──────────────────────┐
                   │           Scoring Engine                 │
                   │  (weighted score → grade A-F)           │
                   └──────────────────┬──────────────────────┘
                                      │
                   ┌──────────────────▼──────────────────────┐
                   │           Report Generator               │
                   │  (JSON + Markdown + HTML)                │
                   └──────────────────┬──────────────────────┘
                                      │
                   ┌──────────────────▼──────────────────────┐
                   │         Integration Layer                │
                   │  ┌──────┐ ┌───────┐ ┌──────┐ ┌──────┐ │
                   │  │ GHA  │ │Makefile│ │ CLI  │ │Slack │ │
                   │  └──────┘ └───────┘ └──────┘ └──────┘ │
                   └─────────────────────────────────────────┘
```

### 1.3 Event-Driven Pipeline

The QRE uses an event-driven architecture built on Redis streams and the existing outbox pattern:

```python
# Pipeline events flow:
EVENT_SCAN_REQUESTED        → Orchestrator receives scan request
EVENT_SCANNER_DISPATCHED    → Dispatcher sends to plugin pool
EVENT_SCANNER_STARTED       → Individual scanner begins work
EVENT_SCANNER_COMPLETED     → Scanner returns results
EVENT_SCANNER_FAILED        → Scanner encountered error
EVENT_ALL_SCANNERS_DONE     → All scanners finished
EVENT_SCORING_STARTED       → Scoring engine begins
EVENT_SCORING_COMPLETED     → Grade calculated
EVENT_REPORT_GENERATED      → Report artifacts created
EVENT_REPORT_DELIVERED      → Report sent to integrations
EVENT_GATE_EVALUATED        → Quality gates checked
```

### 1.4 Scanner Lifecycle

Each scanner plugin follows this lifecycle:

1. **Registration**: Scanner registers with `ScannerRegistry` on startup
2. **Dispatch**: Orchestrator dispatches scan request via Redis stream
3. **Execution**: Scanner runs checks asynchronously
4. **Reporting**: Scanner returns `ScanResult` with checks, findings, score
5. **Retry**: On failure, scanner retries up to 3 times with exponential backoff
6. **Timeout**: Each scanner has a configurable timeout (default: 300s)

### 1.5 Configuration

The QRE is configured via `backend/app/core/quality_engine/config.py`:

```python
# config.py structure
QUALITY_ENGINE = {
    "enabled": True,
    "mode": "pre_release",  # pre_release | nightly | on_demand
    "scanner_timeout": 300,
    "max_retries": 3,
    "concurrent_scanners": 4,
    "report_dir": "/var/lib/gula/quality-reports",
    "github_checks": True,
    "slack_notifications": True,
    "blocking_gates": True,
}
```

## 2. Scan Categories

### 2.1 Architecture Review

**Purpose**: Validate architectural integrity, layering, and patterns.

**Checks**:
- `ARCH-001`: Layer violation check — ensures routes only call services, services only call models/repositories
- `ARCH-002`: Circular dependency detection — scans all `import` statements for cycles
- `ARCH-003`: Monolith boundary check — ensures business logic is not in `services/` (top-level stubs) or `backend/services/`
- `ARCH-004`: Migration policy compliance — checks no existing migrations were modified
- `ARCH-005`: Pattern consistency — verifies all routes use `lifespan` not `@app.on_event`
- `ARCH-006`: Middleware order check — validates middleware stack order matches spec
- `ARCH-007`: Tenant isolation validation — ensures all patient-data queries filter by `lab_id`
- `ARCH-008`: Module boundary check — verifies financial engine doesn't contain business logic (Phase A only)
- `ARCH-009`: Import convention check — no wildcard imports, relative imports within packages

**Scanner Module**: `scanners/architecture_scanner.py`
**Weight**: 15
**Pass Threshold**: 7/9 checks pass

### 2.2 Security Review

**Purpose**: Hard-fail on any security vulnerability or misconfiguration.

**Checks**:
- `SEC-001`: Secrets scanning — scans for hardcoded keys, tokens, passwords in codebase
- `SEC-002`: JWT validation — verifies all protected routes validate JWT via `get_current_user`
- `SEC-003`: Audit log check — ensures all mutations write to `AuditLog` model
- `SEC-004`: Tenant isolation scan — grep for patient-data queries without `lab_id` filter
- `SEC-005`: Encryption verification — confirms `patients.national_id` is encrypted at rest
- `SEC-006`: CORS check — validates CORS origins are not wildcard in production
- `SEC-007`: Rate limiting check — ensures all public endpoints have rate limiting
- `SEC-008`: SQL injection scan — checks for raw SQL execution (use parameterized queries)
- `SEC-009`: RBAC enforcement — verifies role checks on protected routes
- `SEC-010`: Dependency CVE scan — checks for known vulnerabilities in dependencies
- `SEC-011`: Security headers check — validates CSP, HSTS, X-Frame-Options are present
- `SEC-012`: Metrics endpoint check — verifies `/metrics/prom` requires `Bearer METRICS_BEARER_TOKEN`

**Scanner Module**: `scanners/security_scanner.py`
**Weight**: 25
**Pass Threshold**: 11/12 checks pass, and NO critical failures

### 2.3 Testing Review

**Purpose**: Ensure code is well-tested and release-ready.

**Checks**:
- `TST-001`: Unit test coverage — minimum 70% line coverage on new/changed code
- `TST-002`: Integration test coverage — critical paths must have integration tests
- `TST-003`: Migration test — verify `alembic upgrade head` + `downgrade -1` round-trip
- `TST-004`: Smoke test — health endpoints respond 200
- `TST-005`: Critical path coverage — orders, results, samples, patient routes must be tested
- `TST-006`: Security test coverage — JWT, auth, encryption invariants tested
- `TST-007`: Stability assertion tests — 28 test modules all pass
- `TST-008`: No flaky tests — tests must pass 3 consecutive runs

**Scanner Module**: `scanners/testing_scanner.py`
**Weight**: 20
**Pass Threshold**: 7/8 checks pass

### 2.4 Documentation Review

**Purpose**: Verify documentation completeness and accuracy.

**Checks**:
- `DOC-001`: API endpoint documentation — all public endpoints documented in OpenAPI
- `DOC-002`: ADR completeness — architecture decisions documented in `docs/adr/`
- `DOC-003`: Module READMEs — every `app/` subpackage has README
- `DOC-004`: `.env.example` matches actual env vars — no drift
- `DOC-005`: Changelog updated for release
- `DOC-006`: Migration runbook exists for any new migrations

**Scanner Module**: `scanners/documentation_scanner.py`
**Weight**: 10
**Pass Threshold**: 5/6 checks pass

### 2.5 Performance Review

**Purpose**: Prevent performance regressions.

**Checks**:
- `PERF-001`: Latency budget — p95 endpoint response < 500ms for API routes
- `PERF-002`: Query N+1 detection — detect ORM queries inside loops
- `PERF-003`: Memory limit check — no single request exceeds 256MB
- `PERF-004`: Connection pool check — `WEB_CONCURRENCY * (DB_POOL_SIZE + DB_MAX_OVERFLOW) < postgres.max_connections`
- `PERF-005`: Slow query detection — scan for missing indexes on query columns
- `PERF-006`: Static file compression — verify GZipMiddleware is active

**Scanner Module**: `scanners/performance_scanner.py`
**Weight**: 10
**Pass Threshold**: 5/6 checks pass

### 2.6 Accessibility Review

**Purpose**: Ensure WCAG compliance and Arabic/RTL support.

**Checks**:
- `A11Y-001`: RTL layout support — all UI components support `dir="rtl"`
- `A11Y-002`: Color contrast — minimum 4.5:1 ratio for text
- `A11Y-003`: Keyboard navigation — all interactive elements reachable via keyboard
- `A11Y-004`: Screen reader support — ARIA labels on dynamic content
- `A11Y-005`: Focus management — visible focus indicators on all elements

**Scanner Module**: `scanners/accessibility_scanner.py`
**Weight**: 5
**Pass Threshold**: 4/5 checks pass

### 2.7 Localization Review

**Purpose**: Verify i18n completeness and translation quality.

**Checks**:
- `L10N-001`: Translation coverage — no missing translation keys
- `L10N-002`: Arabic string quality — no machine-translated clinical terms
- `L10N-003`: Number/date formatting — Arabic numeral support (Arabic vs Hindi digits)
- `L10N-004`: Text overflow check — Arabic text fits in UI containers
- `L10N-005`: Bidirectional text support — mixed Arabic/English handles correctly

**Scanner Module**: `scanners/localization_scanner.py`
**Weight**: 5
**Pass Threshold**: 4/5 checks pass

### 2.8 Dependency Review

**Purpose**: Scan for vulnerable, outdated, or non-compliant dependencies.

**Checks**:
- `DEP-001`: Known vulnerability scan — `safety` / `pip-audit` for Python packages
- `DEP-002`: License compliance — no GPL/AGPL in commercial deployment
- `DEP-003`: Duplicate dependency check — no duplicate packages in `requirements*.txt`
- `DEP-004`: Outdated dependency check — packages not more than 2 major versions behind

**Scanner Module**: `scanners/dependency_scanner.py`
**Weight**: 10
**Pass Threshold**: 4/4 checks pass

### 2.9 Infrastructure Review

**Purpose**: Verify Docker, deployment, and infrastructure best practices.

**Checks**:
- `INFRA-001`: Dockerfile best practices — multi-stage builds, no root, no `:latest`
- `INFRA-002`: Healthcheck presence — `Dockerfile` has `HEALTHCHECK` instruction
- `INFRA-003`: Non-root user — containers run as non-root user
- `INFRA-004`: Resource limits — Docker Compose has `mem_limit` and `cpus`

**Scanner Module**: `scanners/infrastructure_scanner.py`
**Weight**: 5
**Pass Threshold**: 3/4 checks pass

### 2.10 Compliance Review

**Purpose**: Ensure regulatory compliance.

**Checks**:
- `CMP-001`: HIPAA audit controls — all PHI access logged
- `CMP-002`: Iraqi health regulations — national ID handling complies with MoH requirements
- `CMP-003`: GDPR readiness — data portability and right to deletion endpoints exist
- `CMP-004`: Data retention — patient data deletion/archival policy enforced

**Scanner Module**: `scanners/compliance_scanner.py`
**Weight**: 10
**Pass Threshold**: 3/4 checks pass

### 2.11 Clinical Safety Review

**Purpose**: Prevent patient data integrity issues (highest priority).

**Checks**:
- `CLN-001`: Optimistic locking — `LabResult` version column checked on every mutation
- `CLN-002`: Data integrity validation — no duplicate order IDs, no orphaned results
- `CLN-003`: Audit trail completeness — every patient data write has audit entry
- `CLN-004`: Critical alert delivery — critical results have non-repudiable delivery chain

**Scanner Module**: `scanners/clinical_safety_scanner.py`
**Weight**: 30
**Pass Threshold**: 4/4 checks pass, ZERO failures allowed

## 3. Scanner Implementation

### 3.1 Scanner Plugin Interface

Each scanner implements the `BaseScanner` protocol:

```python
# backend/app/core/quality_engine/scanner_base.py
from dataclasses import dataclass, field
from typing import Protocol, Any


@dataclass
class ScannerCheck:
    id: str
    name: str
    description: str
    weight: float
    passed: bool = False
    score: float = 0.0
    findings: list[dict] = field(default_factory=list)
    remediation: str = ""


@dataclass
class ScanResult:
    scanner_name: str
    scanner_version: str
    checks: list[ScannerCheck]
    total_score: float = 0.0
    max_score: float = 0.0
    grade: str = ""
    passed: bool = False
    duration_ms: float = 0.0
    errors: list[str] = field(default_factory=list)


class BaseScanner(Protocol):
    name: str
    version: str
    weight: float
    threshold: float
    timeout: int

    async def scan(self, context: dict[str, Any]) -> ScanResult: ...
    async def validate(self) -> bool: ...
    def get_checks(self) -> list[ScannerCheck]: ...
```

### 3.2 Registration

```python
# backend/app/core/quality_engine/registry.py
scanner_registry: dict[str, BaseScanner] = {}

def register_scanner(scanner: BaseScanner) -> None:
    scanner_registry[scanner.name] = scanner

def get_scanner(name: str) -> BaseScanner:
    return scanner_registry[name]

def list_scanners() -> list[str]:
    return list(scanner_registry.keys())
```

### 3.3 Scanner Configuration Matrix

| Scanner | Version | Checks | Weight | Threshold | Timeout (s) | Retries |
|---------|---------|--------|--------|-----------|-------------|---------|
| architecture | 1.0.0 | 9 | 15 | 0.78 | 120 | 2 |
| security | 1.0.0 | 12 | 25 | 0.92 | 300 | 3 |
| testing | 1.0.0 | 8 | 20 | 0.88 | 600 | 2 |
| documentation | 1.0.0 | 6 | 10 | 0.83 | 60 | 1 |
| performance | 1.0.0 | 6 | 10 | 0.83 | 120 | 2 |
| accessibility | 1.0.0 | 5 | 5 | 0.80 | 60 | 1 |
| localization | 1.0.0 | 5 | 5 | 0.80 | 60 | 1 |
| dependency | 1.0.0 | 4 | 10 | 1.00 | 300 | 3 |
| infrastructure | 1.0.0 | 4 | 5 | 0.75 | 60 | 1 |
| compliance | 1.0.0 | 4 | 10 | 0.75 | 60 | 1 |
| clinical_safety | 1.0.0 | 4 | 30 | 1.00 | 120 | 2 |

### 3.4 Scanner Implementation Example (Security Scanner)

```python
# backend/app/core/quality_engine/scanners/security_scanner.py
import re
import subprocess
from pathlib import Path

from ..scanner_base import BaseScanner, ScanResult, ScannerCheck


class SecurityScanner:
    name = "security"
    version = "1.0.0"
    weight = 25.0
    threshold = 0.92
    timeout = 300

    async def scan(self, context: dict) -> ScanResult:
        checks = await self.get_checks()
        results = []

        for check in checks:
            result = await self._run_check(check, context)
            results.append(result)

        return self._build_result(results)

    async def _run_check(self, check: ScannerCheck, context: dict) -> ScannerCheck:
        handlers = {
            "SEC-001": self._check_hardcoded_secrets,
            "SEC-002": self._check_jwt_validation,
            "SEC-003": self._check_audit_log_writes,
            "SEC-004": self._check_tenant_isolation,
            "SEC-005": self._check_encryption_at_rest,
            "SEC-006": self._check_cors_config,
            "SEC-007": self._check_rate_limiting,
            "SEC-008": self._check_sql_injection,
            "SEC-009": self._check_rbac_enforcement,
            "SEC-010": self._check_dependency_cves,
            "SEC-011": self._check_security_headers,
            "SEC-012": self._check_metrics_endpoint,
        }
        handler = handlers.get(check.id)
        if handler:
            return await handler(check, context)
        check.passed = False
        check.findings = [{"severity": "error", "message": f"Unknown check: {check.id}"}]
        return check

    async def _check_hardcoded_secrets(self, check, ctx) -> ScannerCheck:
        secrets_patterns = [
            r"(?i)(SECRET_KEY|ENCRYPTION_KEY|NID_HMAC_KEY|REFRESH_TOKEN_SECRET|DEVICE_HMAC_KEY)\s*=\s*['\"][^'\"]+['\"]",
            r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"][^'\"]+['\"]",
            r"(?i)-----BEGIN (RSA |EC )?PRIVATE KEY-----",
        ]
        findings = []
        repo_root = Path(ctx.get("repo_root", "."))
        for pattern in secrets_patterns:
            matches = self._grep(pattern, repo_root, exclude={".git", "__pycache__", ".venv", "node_modules"})
            for match in matches:
                findings.append({
                    "severity": "critical" if "KEY" in pattern else "high",
                    "check": "hardcoded_secret",
                    "file": match["file"],
                    "line": match["line"],
                    "pattern": pattern,
                })
        check.passed = len(findings) == 0
        check.findings = findings
        check.score = 1.0 if check.passed else 0.0
        check.remediation = (
            "Remove hardcoded secrets. Use environment variables loaded via "
            "backend/app/config.py. Run 'make secrets-gen' to generate strong keys."
        ) if not check.passed else ""
        return check

    def _grep(self, pattern: str, path: Path, exclude: set) -> list[dict]:
        # Uses ripgrep for fast file scanning
        result = subprocess.run(
            ["rg", "--no-heading", "--line-number", "-i", pattern, str(path)],
            capture_output=True, text=True, timeout=60,
        )
        matches = []
        for line in result.stdout.splitlines():
            if any(ex in line for ex in exclude):
                continue
            parts = line.split(":", 2)
            if len(parts) >= 2:
                matches.append({"file": parts[0], "line": parts[1], "content": parts[2] if len(parts) > 2 else ""})
        return matches

    # ... other check methods follow the same pattern
```

## 4. Scoring System

### 4.1 Weighted Scoring Formula

```
Scanner Score = Σ(check.score × check.weight) / Σ(check.weight)
             = (% passed weighted by importance)

Category Score = scanner.score × scanner.weight

Total Score = Σ(category_score) / Σ(active_scanner_weights)
```

### 4.2 Score Normalization

Each scanner's raw score (0.0 – 1.0) is normalized against its threshold:

```
Normalized = raw_score / threshold
Capped at 1.0
```

### 4.3 Grade Calculation

| Grade | Score Range | Meaning | Action |
|-------|-------------|---------|--------|
| A | 95-100% | Excellent | Release approved |
| B | 85-94% | Good | Release approved, minor warnings |
| C | 75-84% | Adequate | Release with advisory notes |
| D | 60-74% | Poor | Requires review, pre-approval needed |
| F | <60% | Failing | Release blocked |

### 4.4 Scoring Engine

```python
# backend/app/core/quality_engine/scoring.py
from dataclasses import dataclass


@dataclass
class QualityGrade:
    total_score: float
    grade: str
    scanner_scores: dict[str, float]
    individual_check_scores: dict[str, dict]
    passed: bool
    blocking_issues: list[str]
    warnings: list[str]


def calculate_grade(scanner_results: list[ScanResult],
                    scanner_configs: dict) -> QualityGrade:
    weighted_sum = 0.0
    total_weight = 0.0
    scanner_scores = {}
    blocking = []
    warnings = []

    for result in scanner_results:
        config = scanner_configs[result.scanner_name]
        weight = config["weight"]

        scanner_score = result.total_score / result.max_score if result.max_score > 0 else 0.0
        normalized = min(scanner_score / config["threshold"], 1.0)
        weighted_sum += normalized * weight
        total_weight += weight
        scanner_scores[result.scanner_name] = normalized

        if not result.passed:
            if config.get("blocking", True):
                blocking.append(f"{result.scanner_name}: score {scanner_score:.2f} < threshold {config['threshold']}")
            else:
                warnings.append(f"{result.scanner_name}: score {scanner_score:.2f} < threshold {config['threshold']}")

    total_score = (weighted_sum / total_weight) * 100.0

    if total_score >= 95:
        grade = "A"
        passed = True
    elif total_score >= 85:
        grade = "B"
        passed = True
    elif total_score >= 75:
        grade = "C"
        passed = len(blocking) == 0
    elif total_score >= 60:
        grade = "D"
        passed = len(blocking) == 0
    else:
        grade = "F"
        passed = False

    return QualityGrade(
        total_score=round(total_score, 2),
        grade=grade,
        scanner_scores=scanner_scores,
        individual_check_scores={r.scanner_name: {c.id: c.score for c in r.checks} for r in scanner_results},
        passed=passed,
        blocking_issues=blocking,
        warnings=warnings,
    )
```

### 4.5 Scanner Weight Assignment Rationale

| Weight | Reason |
|--------|--------|
| 30 | Clinical safety: patient data integrity is non-negotiable |
| 25 | Security: healthcare data breach costs and regulatory penalties |
| 20 | Testing: prevents regressions in 36+ routes and 17+ models |
| 15 | Architecture: monolith boundary discipline prevents tech debt spiral |
| 10 each | Performance, dependencies, compliance: important but recoverable |
| 5 each | Docs, A11Y, L10N, infra: important for quality but not release-blocking |

## 5. Report Format

### 5.1 JSON Schema

```json
{
  "$schema": "https://gula.platform/schemas/quality-report-v2.json",
  "type": "object",
  "required": ["metadata", "summary", "scanner_results", "grade", "gates"],
  "properties": {
    "metadata": {
      "type": "object",
      "required": ["report_id", "timestamp", "version", "mode", "commit_sha", "branch"],
      "properties": {
        "report_id": {"type": "string", "format": "uuid"},
        "timestamp": {"type": "string", "format": "date-time"},
        "version": {"type": "string", "enum": ["2.0"]},
        "mode": {"type": "string", "enum": ["pre_release", "nightly", "on_demand"]},
        "commit_sha": {"type": "string"},
        "branch": {"type": "string"},
        "triggered_by": {"type": "string"},
        "duration_ms": {"type": "number"}
      }
    },
    "summary": {
      "type": "object",
      "required": ["total_score", "grade", "passed", "total_checks", "passed_checks", "failed_checks", "blocking_issues", "warnings"],
      "properties": {
        "total_score": {"type": "number"},
        "grade": {"type": "string"},
        "passed": {"type": "boolean"},
        "total_checks": {"type": "integer"},
        "passed_checks": {"type": "integer"},
        "failed_checks": {"type": "integer"},
        "blocking_issues": {"type": "array", "items": {"type": "string"}},
        "warnings": {"type": "array", "items": {"type": "string"}}
      }
    },
    "scanner_results": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["scanner_name", "version", "score", "passed", "checks"],
        "properties": {
          "scanner_name": {"type": "string"},
          "version": {"type": "string"},
          "score": {"type": "number"},
          "passed": {"type": "boolean"},
          "duration_ms": {"type": "number"},
          "checks": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["id", "name", "passed", "score", "findings"],
              "properties": {
                "id": {"type": "string"},
                "name": {"type": "string"},
                "description": {"type": "string"},
                "passed": {"type": "boolean"},
                "score": {"type": "number"},
                "findings": {"type": "array", "items": {"type": "object"}},
                "remediation": {"type": "string"}
              }
            }
          }
        }
      }
    },
    "grade": {
      "type": "object",
      "required": ["letter", "score", "threshold", "passed"],
      "properties": {
        "letter": {"type": "string"},
        "score": {"type": "number"},
        "threshold": {"type": "number"},
        "passed": {"type": "boolean"}
      }
    },
    "gates": {
      "type": "object",
      "required": ["mandatory", "advisory"],
      "properties": {
        "mandatory": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "rule_id": {"type": "string"},
              "name": {"type": "string"},
              "passed": {"type": "boolean"},
              "action": {"type": "string"}
            }
          }
        },
        "advisory": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "rule_id": {"type": "string"},
              "name": {"type": "string"},
              "passed": {"type": "boolean"},
              "action": {"type": "string"}
            }
          }
        }
      }
    },
    "artifacts": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": {"type": "string"},
          "path": {"type": "string"},
          "mime_type": {"type": "string"}
        }
      }
    }
  }
}
```

### 5.2 Markdown Summary Template

```markdown
# Quality Review Report: #{report_id}

**Commit**: `{commit_sha}` (`{branch}`)
**Mode**: {mode} | **Date**: {timestamp}
**Duration**: {duration_ms}ms
**Triggered By**: {triggered_by}

## Summary

| Metric | Value |
|--------|-------|
| **Overall Grade** | **{grade}** |
| **Score** | {total_score}% |
| **Status** | {'✅ PASSED' if passed else '❌ FAILED'} |
| **Checks Passed** | {passed_checks}/{total_checks} |
| **Blocking Issues** | {len(blocking_issues)} |
| **Warnings** | {len(warnings)} |

## Scanner Results

| Scanner | Score | Status | Checks |
|---------|-------|--------|--------|
{scanner_rows}

## Blocking Issues

{blocking_list}

## Warnings

{warning_list}
```

### 5.3 Report Storage

Reports are stored at `/var/lib/gula/quality-reports/{commit_sha}/` with:
- `report.json` — full JSON report
- `report.md` — markdown summary
- `report.html` — HTML dashboard (for CI artifact)
- `scorecard.json` — extractable scorecard data

## 6. Integration Points

### 6.1 GitHub Actions Integration

```yaml
# .github/workflows/quality-review.yml
name: Quality Review Engine
on:
  pull_request:
    types: [opened, synchronize, reopened]
  push:
    branches: [main, develop, release/*]
  schedule:
    - cron: '0 2 * * *'  # nightly

jobs:
  quality-review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Quality Review Engine
        uses: ./scripts/qre-action
        with:
          mode: ${{ github.event_name == 'schedule' && 'nightly' || 'pre_release' }}
          report_dir: ${{ runner.temp }}/qre-reports
          blocking: ${{ github.ref == 'refs/heads/main' && 'true' || 'false' }}
      - name: Upload Report
        uses: actions/upload-artifact@v4
        with:
          name: quality-report
          path: ${{ runner.temp }}/qre-reports/
      - name: Post PR Comment
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const report = JSON.parse(fs.readFileSync('${{ runner.temp }}/qre-reports/report.json', 'utf8'));
            const summary = fs.readFileSync('${{ runner.temp }}/qre-reports/report.md', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: summary
            });
      - name: Check Quality Gates
        if: failure()
        run: |
          echo "Quality gates failed. Review report for details."
          exit 1
```

### 6.2 Makefile Integration

```makefile
# Quality Review Engine targets
.PHONY: quality-check quality-report quality-scorecard

# Run full quality review
quality-check:
	@echo "Running Quality Review Engine..."
	python -m backend.app.core.quality_engine.runner \
		--mode pre_release \
		--report-dir /tmp/qre-reports \
		$(ARGS)

# Generate quality report only (no gating)
quality-report:
	python -m backend.app.core.quality_engine.runner \
		--mode on_demand \
		--report-only \
		$(ARGS)

# Quick scorecard (fast subset of scanners)
quality-scorecard:
	python -m backend.app.core.quality_engine.runner \
		--mode on_demand \
		--scanners security,clinical_safety,testing \
		--report-only \
		$(ARGS)

# Nightly full scan
quality-nightly:
	python -m backend.app.core.quality_engine.runner \
		--mode nightly \
		--report-dir /var/lib/gula/quality-reports/$$(date +%Y%m%d) \
		--slack-notify
```

### 6.3 CLI Usage

```bash
# Full pre-release scan
python -m backend.app.core.quality_engine.runner --mode pre_release

# Single scanner
python -m backend.app.core.quality_engine.runner --scanners security

# Custom report directory
python -m backend.app.core.quality_engine.runner --report-dir ./reports/qa-20260717

# Non-blocking mode (advisory only)
python -m backend.app.core.quality_engine.runner --non-blocking

# JSON-only output (for programmatic consumption)
python -m backend.app.core.quality_engine.runner --format json

# Compare with previous report (regression detection)
python -m backend.app.core.quality_engine.runner --compare-with /var/lib/gula/quality-reports/previous/report.json
```

## 7. Scheduling

### 7.1 Pre-Release Mode

- **Trigger**: On every PR to `main`, `develop`, `release/*`
- **Scanners**: All 11 scanners run fully
- **Duration**: 2-10 minutes depending on codebase size
- **Gating**: Mandatory gates block merge; advisory gates generate warnings
- **Artifacts**: Full report, scorecard, PR comment

### 7.2 Nightly Mode

- **Trigger**: Scheduled daily at 02:00 UTC
- **Scanners**: All 11 scanners, plus historical comparison
- **Duration**: 5-15 minutes
- **Output**: Report stored, Slack notification, trend data updated
- **Purpose**: Detect regressions from multiple PRs merged during the day

### 7.3 On-Demand Mode

- **Trigger**: Manual via Makefile or CLI
- **Scanners**: Configurable subset
- **Duration**: As configured
- **Output**: Report to stdout + file
- **Purpose**: Developer debugging, targeted investigations

## 8. Scorecard Template

```markdown
# GULA Platform Quality Scorecard

## Release Information
- **Release Version**: {version}
- **Commit**: {commit_sha}
- **Date**: {date}
- **Review Mode**: {mode}
- **Overall Grade**: {grade}

---

## Architecture (15%)
- [x] ARCH-001: No layer violations
- [x] ARCH-002: No circular dependencies
- [x] ARCH-003: Monolith boundaries respected
- [ ] ARCH-004: Migration policy compliance (1 violation)
- [x] ARCH-005: Pattern consistency
- [x] ARCH-006: Middleware order correct
- [x] ARCH-007: Tenant isolation validated
- [x] ARCH-008: Module boundaries respected
- [x] ARCH-009: Import conventions followed
*Score: 8/9 | Status: ✅*

## Security (25%)
- [x] SEC-001: No hardcoded secrets
- [x] SEC-002: JWT validation on protected routes
- [x] SEC-003: Audit log writes on all mutations
- [x] SEC-004: Tenant isolation enforced
- [x] SEC-005: National ID encryption verified
- [x] SEC-006: CORS configuration correct
- [x] SEC-007: Rate limiting in place
- [x] SEC-008: No SQL injection vectors
- [x] SEC-009: RBAC enforced
- [ ] SEC-010: Dependency CVE scan (2 moderate CVEs)
- [x] SEC-011: Security headers present
- [x] SEC-012: Metrics endpoint protected
*Score: 11/12 | Status: ✅ (warnings)*

## Testing (20%)
- [x] TST-001: Unit test coverage 73% (≥70%)
- [x] TST-002: Integration tests on critical paths
- [x] TST-003: Migration round-trip verified
- [x] TST-004: Smoke tests pass
- [x] TST-005: Critical path tests cover orders/results/samples/patients
- [x] TST-006: Security test suite passes
- [x] TST-007: All 28 test modules pass
- [x] TST-008: No flaky tests (3 consecutive passes)
*Score: 8/8 | Status: ✅*

## Documentation (10%)
- [x] DOC-001: OpenAPI docs complete
- [x] DOC-002: ADRs documented
- [ ] DOC-003: Module README missing (ai/, firewall/)
- [x] DOC-004: .env.example up to date
- [x] DOC-005: Changelog updated
- [x] DOC-006: Migration runbook present
*Score: 5/6 | Status: ✅ (warnings)*

## Performance (10%)
- [x] PERF-001: p95 latency < 500ms
- [x] PERF-002: No N+1 query patterns
- [x] PERF-003: Memory per request < 256MB
- [x] PERF-004: Connection pool budget valid
- [ ] PERF-005: 2 slow queries detected (missing indexes)
- [x] PERF-006: GZip compression active
*Score: 5/6 | Status: ✅ (warnings)*

## Accessibility (5%)
- [x] A11Y-001: RTL layout supported
- [x] A11Y-002: Color contrast ratios met
- [x] A11Y-003: Keyboard navigation works
- [x] A11Y-004: Screen reader ARIA labels present
- [x] A11Y-005: Focus management correct
*Score: 5/5 | Status: ✅*

## Localization (5%)
- [x] L10N-001: No missing translation keys
- [x] L10N-002: Arabic clinical terms reviewed
- [x] L10N-003: Number/date formatting correct
- [x] L10N-004: Text overflow checked
- [x] L10N-005: Bidirectional text support
*Score: 5/5 | Status: ✅*

## Dependencies (10%)
- [x] DEP-001: No known vulnerabilities (after patch)
- [x] DEP-002: License compliance verified
- [x] DEP-003: No duplicate dependencies
- [x] DEP-004: All packages within 2 major versions
*Score: 4/4 | Status: ✅*

## Infrastructure (5%)
- [x] INFRA-001: Dockerfile uses multi-stage build
- [x] INFRA-002: HEALTHCHECK present
- [x] INFRA-003: Non-root user configured
- [x] INFRA-004: Resource limits set
*Score: 4/4 | Status: ✅*

## Compliance (10%)
- [x] CMP-001: HIPAA audit controls
- [x] CMP-002: Iraqi health regulation compliance
- [x] CMP-003: GDPR readiness
- [x] CMP-004: Data retention policy enforced
*Score: 4/4 | Status: ✅*

## Clinical Safety (30%)
- [x] CLN-001: Optimistic locking on LabResult
- [x] CLN-002: Data integrity checks pass
- [x] CLN-003: Complete audit trail
- [x] CLN-004: Critical alert delivery verified
*Score: 4/4 | Status: ✅*

---

## Final Verdict

| Metric | Result |
|--------|--------|
| **Weighted Score** | 91.4% |
| **Grade** | B |
| **Mandatory Gates** | All passed |
| **Advisory Gates** | 3 warnings |
| **Release Decision** | ✅ Approved |

## Required Follow-ups
1. [SEC-010] Patch moderate CVEs before next release
2. [DOC-003] Add READMEs to ai/ and firewall/ modules
3. [PERF-005] Add indexes for 2 slow queries
4. [ARCH-004] Tag migration 20260717 as immutable after release

---

*Report generated by GULA Quality Review Engine v2.0*
*Review ID: {report_id}*
```

## 9. Implementation Plan

### Phase 1: Core Engine (2 weeks)
- Implement `BaseScanner` protocol and `ScannerRegistry`
- Build orchestration service with Redis stream dispatching
- Implement scoring engine and grade calculation
- Build report generator (JSON + Markdown)

### Phase 2: Scanner Implementation (3 weeks)
- Implement all 11 scanner plugins
- Build scanner-specific check logic
- Write unit tests for each scanner (target: 90% coverage)

### Phase 3: Integration (1 week)
- GitHub Actions workflow
- Makefile targets
- CLI entry point
- Slack/Discord notification integration

### Phase 4: Deployment (1 week)
- Containerize engine as optional sidecar
- Deploy nightly pipeline
- Document usage and troubleshooting
- Train team on scorecard interpretation

## 10. Appendix: File Layout

```
backend/app/core/quality_engine/
├── __init__.py
├── runner.py                  # CLI entry point
├── config.py                  # Engine configuration
├── models.py                  # Pydantic models for checks/results
├── scanner_base.py            # BaseScanner protocol + ScannerCheck/ScanResult dataclasses
├── registry.py                # ScannerRegistry
├── orchestrator.py            # Orchestration service
├── dispatcher.py              # Scanner dispatcher (Redis streams)
├── scoring.py                 # Scoring engine + grade calculation
├── reporting.py               # Report generator (JSON/MD/HTML)
├── gates.py                   # Quality gate evaluation
├── integration/
│   ├── github_actions.py      # GHA checks API
│   ├── slack.py               # Slack notification
│   └── makefile.py            # Makefile output formatter
├── scanners/
│   ├── __init__.py
│   ├── architecture_scanner.py
│   ├── security_scanner.py
│   ├── testing_scanner.py
│   ├── documentation_scanner.py
│   ├── performance_scanner.py
│   ├── accessibility_scanner.py
│   ├── localization_scanner.py
│   ├── dependency_scanner.py
│   ├── infrastructure_scanner.py
│   ├── compliance_scanner.py
│   └── clinical_safety_scanner.py
└── tests/
    ├── test_orchestrator.py
    ├── test_scoring.py
    ├── test_reporting.py
    ├── test_gates.py
    └── scanners/
        ├── test_architecture_scanner.py
        ├── test_security_scanner.py
        └── ...
```

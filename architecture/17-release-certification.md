# GULA Platform — Release Certification Policy

Version: 1.0 — 2026-07-15
Status: **DRAFT** — Architecture Review Board approval pending

---

## Table of Contents

1. [Release Gates Overview](#1-release-gates-overview)
2. [Architecture Gate](#2-architecture-gate)
3. [Security Gate](#3-security-gate)
4. [Performance Gate](#4-performance-gate)
5. [Clinical Safety Gate](#5-clinical-safety-gate)
6. [Documentation Gate](#6-documentation-gate)
7. [SBOM Gate](#7-sbom-gate)
8. [Risk Assessment Gate](#8-risk-assessment-gate)
9. [Sign-Off Workflow](#9-sign-off-workflow)
10. [Emergency Release Process](#10-emergency-release-process)

---

## 1. Release Gates Overview

Every release must pass through a series of gates before deployment to production. Gates are executed in sequence; failure at any gate blocks the release.

### Gate Sequence

```
Feature Complete
    ↓
1. Architecture Gate ── FAIL → Block release, fix violations
    ↓ PASS
2. Security Gate ── FAIL → Security review, patch CVEs
    ↓ PASS
3. Performance Gate ── FAIL → Optimize, re-test
    ↓ PASS
4. Clinical Safety Gate ── FAIL → Clinical review, safety fixes
    ↓ PASS
5. Documentation Gate ── FAIL → Complete docs
    ↓ PASS
6. SBOM Gate ── FAIL → Remediate dependencies
    ↓ PASS
7. Risk Assessment Gate ── FAIL → Accept or mitigate risks
    ↓ PASS
8. Sign-off Workflow
    ↓
RELEASE APPROVED
```

### Release Types

| Type | Gates Required | Approval | Timeline |
|------|---------------|----------|----------|
| Major (MAJOR.x) | All 8 gates | Full board | 2-4 weeks |
| Minor (x.MINOR.x) | Gates 1-6 | Tech lead + Security lead | 1-2 weeks |
| Patch (x.x.PATCH) | Gates 1, 3, 5 | Tech lead | 2-3 days |
| Emergency (hotfix) | Gates 1, 3, 5 (abbreviated) | Tech lead (post-fix review) | Hours |

---

## 2. Architecture Gate

### 2.1 Purpose

Ensure the release does not introduce architectural violations — layer violations, circular dependencies, or kernel contamination.

### 2.2 Checks

| Check | Tool/Process | Pass Criteria |
|-------|-------------|---------------|
| Layer violation scan | `shared/architecture/validator.py` | Zero violations |
| Circular dependency check | Module dependency graph | Zero cycles |
| Kernel dependency audit | Import scanner | Kernel imports business = 0 |
| DDD alignment | Architecture review | Domain modules comply |
| Module isolation | Cross-module import audit | No cross-ORM imports |

### 2.3 Evidence

- Architecture validation report
- Dependency graph (highlighting any cycles → must resolve)
- Architecture review board minutes

### 2.4 Responsible

- **Reviewer**: Architecture Team Lead
- **Tool**: `shared/architecture/validator.py`

---

## 3. Security Gate

### 3.1 Purpose

Ensure the release introduces no new security vulnerabilities and maintains the platform's security posture.

### 3.2 Checks

| Check | Tool/Process | Pass Criteria |
|-------|-------------|---------------|
| SAST scan | `bandit -ll -ii` | Zero high/critical findings |
| Dependency CVE scan | `safety` | Zero critical/high CVEs |
| Container scan | `trivy` | Zero critical/high CVEs |
| Secret scan | `gitleaks` | Zero secrets found |
| API security scan | `OWASP ZAP` (optional) | Zero high-risk findings |
| Penetration test | Manual (quarterly) | All findings addressed |
| Authentication review | Manual code review | JWT, password, session controls verified |
| Authorization review | Manual code review | RBAC/ABAC enforcement verified |
| Audit log review | Manual code review | All new mutations audited |

### 3.3 Evidence

- SAST report (zero critical/high)
- Dependency CVE report (zero critical/high)
- Secret scan report (zero findings)
- Security review sign-off

### 3.4 Responsible

- **Reviewer**: Security Lead
- **Tool**: `bandit`, `safety`, `trivy`, `gitleaks`

---

## 4. Performance Gate

### 4.1 Purpose

Ensure the release maintains or improves performance characteristics and does not introduce regressions.

### 4.2 Checks

| Check | Tool/Process | Pass Criteria |
|-------|-------------|---------------|
| Load test | `make scenario-test` | P95 < 500ms, error rate < 1% |
| Stress test | Custom load test | Breakpoint identified, graceful degradation |
| Database query profile | Query logging | No new N+1 queries |
| Connection pool check | `database.py` pool status | Pool utilization < 80% at peak |
| Memory profile | Memory monitoring | Worker memory < 512MB |
| Regression check | Compare with previous release | No significant degradation |

### 4.3 Evidence

- Load test results (P50/P95/P99, throughput, error rate)
- Stress test results (breakpoint, degradation curve)
- Query profiling output
- Comparison with previous release

### 4.4 Responsible

- **Reviewer**: Performance Lead
- **Tool**: `make scenario-test`, custom load scripts

---

## 5. Clinical Safety Gate

### 5.1 Purpose

Ensure the release maintains patient safety — no risk to clinical data integrity, no incorrect results, no loss of critical functionality.

### 5.2 Checks

| Check | Tool/Process | Pass Criteria |
|-------|-------------|---------------|
| Clinical data integrity | Automated tests | All integrity tests pass |
| Order state machine | `backend/app/domain/order_state.py` | Valid transitions enforced |
| Result validation | Result processing test | No incorrect result propagation |
| Lock semantics | `assert_not_locked()` tests | Validated orders immutable |
| Tenant isolation | Tenant isolation tests | Cross-lab data leakage = 0 |
| Audit coverage | Audit log tests | All mutations audited |
| Critical alert test | Alert service test | Critical alerts delivered |
| Clinical review | Clinical safety officer review | Safety verified |

### 5.3 Evidence

- Clinical integrity test results
- Order lifecycle verification
- Tenant isolation test results
- Clinical safety officer sign-off

### 5.4 Responsible

- **Reviewer**: Clinical Safety Officer
- **Process**: Clinical validation walkthrough

---

## 6. Documentation Gate

### 6.1 Purpose

Ensure all changes are documented — ADRs for architecture decisions, API docs for new endpoints, changelog entries, and release notes.

### 6.2 Checks

| Check | Pass Criteria |
|-------|---------------|
| ADR completeness | All significant decisions have ADRs |
| API documentation | All new/modified endpoints documented in OpenAPI |
| Changelog | `CHANGELOG.md` updated with release changes |
| Release notes | Release notes drafted and reviewed |
| Migration guide | Breaking changes have migration guide |
| README updates | Relevant READMEs updated |
| Runbook updates | New operational procedures documented |

### 6.3 Evidence

- ADR index (all required ADRs exist)
- OpenAPI spec diff (documented changes match implementation)
- Changelog entry
- Release notes draft
- Migration guide (if breaking changes)

### 6.4 Responsible

- **Reviewer**: Technical Writer / Documentation Lead

---

## 7. SBOM Gate

### 7.1 Purpose

Generate and review the Software Bill of Materials (SBOM) for the release, ensuring all dependencies are known and vulnerabilities are managed.

### 7.2 Checks

| Check | Tool/Process | Pass Criteria |
|-------|-------------|---------------|
| SBOM generation | `trivy` / `syft` | Complete SBOM generated |
| Dependency review | SBOM analysis | All dependencies known and approved |
| License compliance | License scanner | All licenses compatible |
| CVE remediation | CVE analysis | Zero critical/high CVEs |
| Outdated dep check | Dep freshness check | No severely outdated deps |

### 7.3 Evidence

- SBOM document (SPDX/CycloneDX format)
- Dependency approval list
- License compliance report
- CVE remediation evidence

### 7.4 Responsible

- **Reviewer**: Security Lead
- **Tool**: `trivy`, `syft`

---

## 8. Risk Assessment Gate

### 8.1 Purpose

Identify, document, and accept (or mitigate) any residual risks associated with the release.

### 8.2 Checks

| Step | Description |
|------|-------------|
| Risk identification | Identify new risks introduced by this release |
| Risk analysis | Assess probability and impact of each risk |
| Risk evaluation | Determine risk level (low/medium/high/critical) |
| Risk treatment | Define mitigation or acceptance for each risk |
| Risk register update | Update risk register with all identified risks |
| Residual risk acceptance | Obtain sign-off on accepted residual risks |

### 8.3 Risk Categories

| Category | Examples |
|----------|----------|
| Clinical safety | Incorrect results, data loss, misidentification |
| Security | Data breach, unauthorized access, CVE exploit |
| Performance | Degradation under load, increased latency |
| Compliance | Regulatory non-compliance, audit failure |
| Operational | Deployment failure, rollback complexity |
| Vendor | Third-party deprecation, license change |

### 8.4 Evidence

- Updated risk register
- Risk treatment plan
- Residual risk acceptance form
- Stakeholder sign-off

### 8.5 Responsible

- **Reviewer**: Risk Manager / Product Owner

---

## 9. Sign-Off Workflow

### 9.1 Required Sign-Offs

| Gate | Sign-Off By | Minimum Role |
|------|-------------|-------------|
| Architecture Gate | Architecture Team Lead | Technical Lead |
| Security Gate | Security Lead | Security Lead |
| Performance Gate | Performance Lead | Senior Engineer |
| Clinical Safety Gate | Clinical Safety Officer | Clinical Lead |
| Documentation Gate | Technical Writer | Documentation Lead |
| SBOM Gate | Security Lead | Security Lead |
| Risk Assessment Gate | Product Owner | Product Owner |
| Final Release | Technical Lead + Security Lead + Clinical Lead + Product Owner | Board |

### 9.2 Sign-Off Workflow

```
1. Gate completes → Gate owner signs off
2. All gates pass → Release candidate created
3. Technical Lead signs off → Architecture + Performance verified
4. Security Lead signs off → Security + SBOM verified
5. Clinical Lead signs off → Clinical safety verified
6. Product Owner signs off → Risk assessment accepted + documentation complete
7. Release deployed
```

### 9.3 Sign-Off Documentation

Each sign-off must include:
- Date and time
- Gate owner name and role
- Evidence checklist items satisfied
- Any findings or exceptions
- Digital signature or verified approval

---

## 10. Emergency Release Process

### 10.1 Trigger

Emergency releases are used for:
- **Critical security vulnerabilities** (CVE with active exploit)
- **Patient safety issues** (incorrect results, data loss)
- **Production outage** (platform unavailable)
- **Data integrity issue** (corruption, incorrect data)

### 10.2 Abbreviated Process

| Step | Description | Time Target |
|------|-------------|-------------|
| 1. Triage | Confirm emergency, assess impact | 15 min |
| 2. Fix | Implement fix, peer review | 1-4 hours |
| 3. Quick gates | Architecture (focused) + Performance (regression) | 1 hour |
| 4. Deploy | Emergency deployment (canary first) | 30 min |
| 5. Monitor | Intensive monitoring for 24h | 24 hours |
| 6. Post-fix | Full gate review, root cause analysis, risk acceptance | 1 week |

### 10.3 Post-Release Remediation

Within 7 days of emergency release:
- Complete all skipped gates (documentation, SBOM, full security)
- Root cause analysis report
- Risk register update
- Process improvement recommendations
- All remediation items tracked and assigned

### 10.4 Approval

- **Emergency approval**: Technical Lead + Security Lead
- **Post-fix confirmation**: Architecture Review Board

---

## Document Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-15 | Architecture Team | Initial release certification policy |

**Review Cycle**: This document must be reviewed and updated semi-annually or when the release process changes.

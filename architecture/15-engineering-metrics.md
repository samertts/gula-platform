# GULA Platform — Engineering Metrics Framework

Version: 1.0 — 2026-07-15
Status: **DRAFT** — Architecture Review Board approval pending

---

## Table of Contents

1. [Code Coverage](#1-code-coverage)
2. [Cyclomatic Complexity](#2-cyclomatic-complexity)
3. [Maintainability Index](#3-maintainability-index)
4. [Technical Debt Ratio](#4-technical-debt-ratio)
5. [Architecture Violations](#5-architecture-violations)
6. [Security Score](#6-security-score)
7. [Performance Score](#7-performance-score)
8. [Reliability Score](#8-reliability-score)
9. [Availability Score](#9-availability-score)
10. [Scalability Score](#10-scalability-score)
11. [Documentation Coverage](#11-documentation-coverage)

---

## 1. Code Coverage

### 1.1 Measurement Method

| Coverage Type | Tool | Target | Measurement |
|---------------|------|--------|-------------|
| Line coverage | `pytest --cov` | ≥ 80% | `pytest --cov=app --cov-report=term --cov-report=xml` |
| Branch coverage | `pytest --cov-branch` | ≥ 70% | `pytest --cov-branch --cov=app` |
| Mutation coverage | `mutmut` / `cosmic-ray` | ≥ 60% | Mutation testing suite |

### 1.2 Tool Integration

- `Makefile: test` — Runs pytest with coverage
- `.github/workflows/ci.yml:` — `backend-test` job runs tests with coverage
- Coverage reports published as CI artifacts

### 1.3 Scoring Formula

```
Score = (line_coverage / 80) × 0.5 + (branch_coverage / 70) × 0.3 + (mutation_coverage / 60) × 0.2
Score capped at 1.0 (100%)
```

### 1.4 Alerting Thresholds

| Level | Line Coverage | Branch Coverage | Action |
|-------|---------------|-----------------|--------|
| 🔴 Critical | < 60% | < 50% | Block PR merge |
| 🟡 Warning | 60-79% | 50-69% | Flag for review |
| 🟢 Good | 80-89% | 70-79% | Monitor |
| 🟢 Excellent | ≥ 90% | ≥ 80% | No action needed |

### 1.5 Dashboard Integration

- Grafana dashboard: Code Coverage panel
- CI: Coverage report posted as PR comment
- Weekly: Coverage trend chart

---

## 2. Cyclomatic Complexity

### 2.1 Measurement Method

| Scope | Tool | Threshold |
|-------|------|-----------|
| Per function | `radon cc -s` | ≤ 10 |
| Per class | `radon cc -s` | ≤ 20 |
| Per module | `radon cc -s` | Monitor trend |

### 2.2 Tool Integration

- `radon cc backend/app/ -s` — Complexity analysis
- Integrated into CI lint job

### 2.3 Scoring Formula

```
Complexity score per function:
  ≤ 5  → 1.0 (excellent)
  6-10 → 0.8 (acceptable)
  11-20 → 0.5 (needs attention)
  > 20  → 0.0 (must refactor)

Overall = average across all functions
```

### 2.4 Alerting Thresholds

| Level | Per Function | Per Class | Action |
|-------|-------------|-----------|--------|
| 🔴 Critical | > 20 | > 40 | Must refactor |
| 🟡 Warning | 11-20 | 21-40 | Flag for review |
| 🟢 Acceptable | 6-10 | 11-20 | Monitor |
| 🟢 Excellent | ≤ 5 | ≤ 10 | No action |

---

## 3. Maintainability Index

### 3.1 Measurement Method

| Tool | Range | Interpretation |
|------|-------|----------------|
| `radon mi -s` | ≥ 70 | Green (high maintainability) |
| `radon mi -s` | 50-69 | Yellow (moderate) |
| `radon mi -s` | < 50 | Red (low maintainability) |

### 3.2 Tool Integration

- `radon mi backend/app/ -s` — Maintainability analysis
- Tracked in CI pipeline

### 3.3 Target

| Target | Threshold |
|--------|-----------|
| Excellent | ≥ 70 |
| Acceptable | ≥ 50 |
| Action Required | < 50 |

### 3.4 Scoring Formula

```
Score = MI / 100  (MI = 171 - 5.2 × ln(Halstead Volume) - 0.23 × (Cyclomatic Complexity) - 16.2 × ln(LOC))
Score capped at 1.0
```

---

## 4. Technical Debt Ratio

### 4.1 Measurement Method

| Tool | Metric | Target |
|------|--------|--------|
| SonarQube / CodeClimate | Technical Debt Ratio | < 5% excellent, < 10% good, < 20% acceptable |

### 4.2 Definitions

| Ratio | Interpretation |
|-------|----------------|
| < 5% | Excellent — well-maintained codebase |
| 5-10% | Good — manageable debt |
| 10-20% | Acceptable — needs attention |
| > 20% | Critical — requires debt reduction plan |

### 4.3 Scoring Formula

```
Score:
  < 5%  → 1.0 (excellent)
  5-10% → 0.8 (good)
  10-20% → 0.5 (acceptable)
  > 20% → 0.0 (critical)
```

---

## 5. Architecture Violations

### 5.1 Detection Method

| Violation Type | Detection Tool | Target |
|----------------|---------------|--------|
| Layer violations | `shared/architecture/validator.py` | Zero |
| Circular dependencies | Module dependency graph analysis | Zero |
| Hub module detection | Import count analysis | No hub module |
| Kernel dependency on business | Import scanner | Zero |

### 5.2 Scoring Formula

```
Score = number_of_violations == 0 ? 1.0 : max(0, 1.0 - violations × 0.1)
Each violation deducts 10% from the base score
```

### 5.3 Alerting Thresholds

| Violations | Action |
|------------|--------|
| 0 | ✅ No action |
| 1-3 | 🟡 Flag for review |
| 4+ | 🔴 Block PR merge |

---

## 6. Security Score

### 6.1 Measurement Method

| Standard | Tool | Measurement |
|----------|------|-------------|
| OWASP ASVS L1 | Manual + automated audit | % compliance |
| OWASP ASVS L2 | Manual + automated audit | % compliance |
| OWASP ASVS L3 | Manual + automated audit | % compliance |
| CVE scanning | `safety`, `trivy` | Vulnerabilities found |
| Secret scanning | `gitleaks` | Secrets leaked |

### 6.2 Scoring Formula

```python
# Weighted ASVS compliance
base_score = (L1_pct × 0.5 + L2_pct × 0.3 + L3_pct × 0.2) / 100

# Deductions for CVEs
cve_deduction = min(critical_cves × 0.2 + high_cves × 0.1, 0.5)

# Deduction for secrets
secret_deduction = secrets_found × 0.5  # Immediate zero if any secret

final_score = max(0, base_score - cve_deduction - secret_deduction)
```

### 6.3 Alerting Thresholds

| Score | Action |
|-------|--------|
| ≥ 0.9 | 🟢 No action |
| 0.7-0.89 | 🟡 Remediation plan |
| < 0.7 | 🔴 Block release |

---

## 7. Performance Score

### 7.1 Measurement Method

| Metric | Target | Tool |
|--------|--------|------|
| P50 latency | < 200ms | Load testing |
| P95 latency | < 500ms | Load testing |
| P99 latency | < 2000ms | Load testing |
| Throughput | > 1000 req/s | Load testing |
| Error rate | < 1% | Load testing |

### 7.2 Scoring Formula

```python
latency_score:
  P50 ≤ 200ms → 1.0; P50 ≤ 500ms → 0.7; else → 0.3
  P95 ≤ 500ms → 1.0; P95 ≤ 2000ms → 0.7; else → 0.3
  P99 ≤ 2000ms → 1.0; P99 ≤ 5000ms → 0.7; else → 0.3

throughput_score = min(actual_throughput / target_throughput, 1.0)
error_score = max(0, 1.0 - error_rate / 0.01)  # target < 1%

overall = latency_score × 0.4 + throughput_score × 0.3 + error_score × 0.3
```

---

## 8. Reliability Score

### 8.1 Measurement Method

| Metric | Target | Source |
|--------|--------|--------|
| SLO attainment | ≥ 99.9% | Uptime monitoring |
| Error budget | < 10% consumed | Error budget tracking |
| MTBF | > 720 hours | Incident tracking |
| MTTR | < 30 minutes | Incident tracking |
| Circuit breaker health | Never OPEN > 5 min | Self-healing metrics |

### 8.2 Scoring Formula

```python
slo_score = min(slo_attainment / 0.999, 1.0)
error_budget_score = max(0, 1.0 - error_budget_consumption)
mtbf_score = min(mtbf_hours / 720, 1.0)
mttr_score = max(0, 1.0 - mttr_minutes / 60)

overall = slo_score × 0.3 + error_budget_score × 0.3 + mtbf_score × 0.2 + mttr_score × 0.2
```

---

## 9. Availability Score

### 9.1 Measurement Method

| Metric | Target | Source |
|--------|--------|--------|
| Uptime percentage | ≥ 99.9% | Health endpoint monitoring |
| Nines of availability | Target: 3 nines | Uptime calculation |

### 9.2 Scoring Formula

```python
# Based on nines of availability
nines = floor(-log10(1 - uptime_fraction))  # 0.999 = 3 nines

score:
  nines ≥ 5 → 1.0 (telco-grade)
  nines ≥ 4 → 0.95 (carrier-grade)
  nines ≥ 3 → 0.85 (enterprise)
  nines ≥ 2 → 0.70 (standard)
  nines < 2 → 0.0 (unacceptable)
```

---

## 10. Scalability Score

### 10.1 Measurement Method

| Metric | Target | Method |
|--------|--------|--------|
| Linearity | > 0.8 (ideal = 1.0) | Load testing at scale |
| Saturation point | > 2× expected peak | Stress testing |
| Degradation curve | Gradual (not cliff) | Load ramp testing |

### 10.2 Scoring Formula

```python
linearity_score = min(linearity_coefficient, 1.0)
saturation_score = min(actual_saturation / (2 × expected_peak), 1.0)
degradation_score = gradual ? 1.0 : 0.5  # Cliff degradation = 0.5

overall = linearity_score × 0.4 + saturation_score × 0.4 + degradation_score × 0.2
```

---

## 11. Documentation Coverage

### 11.1 Measurement Method

| Document Type | Target | Check |
|---------------|--------|-------|
| ADR completeness | All decisions → ADR | ADR index vs decisions |
| API documentation | 100% of endpoints | OpenAPI spec check |
| README presence | Every module | File check |
| Architecture docs | Per major domain | Document index |
| Runbook coverage | All operations | Runbook index |

### 11.2 Scoring Formula

```python
adr_score = documented_decisions / total_decisions
api_doc_score = documented_endpoints / total_endpoints
readme_score = modules_with_readme / total_modules
arch_doc_score = documented_domains / total_domains

overall = adr_score × 0.25 + api_doc_score × 0.35 + readme_score × 0.2 + arch_doc_score × 0.2
```

### 11.3 Alerting Thresholds

| Score | Action |
|-------|--------|
| ≥ 0.9 | 🟢 No action |
| 0.7-0.89 | 🟡 Documentation review needed |
| < 0.7 | 🔴 Documentation sprint required |

---

## Dashboard Integration

All engineering metrics should be published to a central Grafana dashboard:

| Panel | Metric | Source |
|-------|--------|--------|
| Code Coverage | Line, branch, mutation | CI artifacts |
| Complexity | Cyclomatic complexity trend | CI lint job |
| Maintainability | MI trend per module | CI lint job |
| Technical Debt | Debt ratio trend | SonarQube/CodeClimate |
| Architecture | Violation count | Architecture validator |
| Security | ASVS compliance %, CVE count | Security scan job |
| Performance | P50/P95/P99 latency | Load test results |
| Reliability | SLO attainment, error budget | Monitoring |
| Availability | Uptime % | Health endpoint |
| Scalability | Linearity coefficient | Scale test results |
| Documentation | Coverage % by type | Manual + automated check |

---

## Document Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-15 | Architecture Team | Initial engineering metrics framework |

**Review Cycle**: This document must be reviewed and updated quarterly.

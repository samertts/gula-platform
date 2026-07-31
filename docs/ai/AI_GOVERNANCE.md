# GULA AI Governance — Operating Documentation

> PROGRAM-012 / PROGRAM-012A — Permanent Intelligence Layer
> Status: Ratified
> Entry point: CLAUDE.md → AGENTS.md → PROJECT_BRAIN.md → this document

This document defines how the GULA repository governs itself: the permanent
intelligence layer that every AI model, developer, and automation must pass
through. It documents the *operating procedures*; the *law* is in
`docs/constitution/32_AI_EXECUTION_CONSTITUTION.md`.

## 1. Governance Layer Architecture

```
┌───────────────────────────────────────────────────────────────┐
│  CLAUDE.md — Primary AI Operating Manual (entry point)        │
│  AGENTS.md — auto-loaded instructions + anchored state        │
│  PROJECT_BRAIN.md — live knowledge index (make brain)         │
├───────────────────────────────────────────────────────────────┤
│  Constitution (docs/constitution/, Articles 01-32)            │
│  Constitution Engine (governance/ + scripts/constitution_     │
│    enforcer.py) — machine-enforced rules                     │
├───────────────────────────────────────────────────────────────┤
│  Enterprise Validation Engine (scripts/enterprise_validation_ │
│    engine.py) — hard gates + regression gate vs baseline      │
│  Architecture Guardian (scripts/architecture_guardian.py,     │
│    scripts/architecture_compliance_engine.py)                 │
│  Cross-System Consistency (scripts/zero_drift_engine.py)      │
│  Regression Prevention (baseline.json regression gate)        │
├───────────────────────────────────────────────────────────────┤
│  Release Certification (backend/app/certification/,           │
│    scripts/certification_check.py, scripts/                   │
│    enterprise_governance_certification.py)                    │
│  Knowledge Synchronization (project_brain.py,                 │
│    knowledge_graph.py, self_audit_agent.py)                   │
└───────────────────────────────────────────────────────────────┘
```

## 2. The Deterministic Session Protocol

Every AI session on this repository MUST follow:

1. **Read**: `CLAUDE.md` → `AGENTS.md` → `docs/brain/PROJECT_BRAIN.md` → domain docs.
2. **Plan**: atomic tasks with risk/dependencies/rollback (Constitution 32.2.1).
3. **Impact analysis**: files, APIs, tests, docs, DB objects (Constitution 32.2.2).
4. **Implement** in small steps; never batch unrelated changes.
5. **Validate**: `make validate` (fast) — hard gates must pass; `--update-baseline`
   only after intentional improvement.
6. **Self-review**: correctness, architecture, security, naming, backward compat.
7. **Commit**: conventional, atomic, risk level in body for HIGH/CRITICAL.
8. **Synchronize knowledge**: `make brain` on structural changes.
9. **Report**: follow the report format in AGENTS.md; never fabricate results.

## 3. Machine-Enforced Rule Catalog (R1-R10)

Implemented by `scripts/constitution_enforcer.py` (25 rules) + the validation engine:

| Rule | Enforcement | Owner |
|------|-------------|-------|
| R1 hard-gate failures | enterprise_validation_engine.py | Validation |
| R2 regressions vs baseline | baseline.json gate | Validation |
| R3 clinical safety | constitution_enforcer (clinical rules) | Security/Clinical |
| R4 dead-code removal proof | constitution_enforcer (dead-code rule) | Architecture |
| R5 destructive migrations | check_migration_policy.sh, data-preservation gate | Database |
| R6 dependency constitution | governance/ constitution_engine.py | Governance |
| R7 no fabricated green | CI + validation engine | QA |
| R8 ADR for architecture | constitution_enforcer (ADR rule) | Architecture |
| R9 commit message quality | pre-commit hooks | Engineering |
| R10 AI code passes gates | validation engine in CI | Governance |

## 4. Certification Suites

| Certification | Tool | Output |
|---------------|------|--------|
| Enterprise governance | scripts/enterprise_governance_certification.py | NATIONAL_CERTIFICATION_REPORT.md |
| Identity | scripts/identity_enterprise_certification.py | identity_report/ |
| Live dimension engine | backend/app/certification/ | /certification API |
| Release readiness | scripts/certification_check.py | reports/ |
| Repository health | scripts/repository_scorecard.py | 0-100 grade |

## 5. Continuous Health Scores

Tracked by `scripts/repository_scorecard.py` (10 axes) and `scripts/enterprise_metrics.py`.
Regressions in any tracked metric block commits (Constitution 32.4 R2).

## 6. Multi-Agent Consensus (Constitution 32.6)

- Independent reviews before merging; never auto-merge conflicts.
- Safest implementation wins: hard gates pass → lowest risk → best compliance.

## 7. Change Ownership & Traceability

- Every generated file declares its generator (`make brain` files say "DO NOT EDIT").
- Every architectural decision has an ADR (`architecture/`, `docs/adr/`).
- Every commit has purpose + scope + risk + rollback.
- Every program has a completion report under `docs/reports/` or repo root.

## 8. Repair & Recovery

- Lint/format: `ruff --fix` (safe fixes).
- Stale knowledge: `make brain`.
- Broken CI: rerun once; second failure blocks.
- Production: `scripts/emergency-fix.sh`, `scripts/dr-failover.sh`,
  `scripts/pitr-recover.sh`, `docs/runbooks/`.

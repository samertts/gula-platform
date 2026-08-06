# Stability & Change Management Policy

**Mission:** GAIOS-MASTER-001
**Created:** 2026-08-04
**Status:** Active

---

## Purpose

Repository stability is a strategic objective. New features must never
compromise platform stability. Large architectural changes must never
be mixed with feature development.

---

## Change Classification

Every proposed change must be classified before implementation.

| Class | Type | Review Level |
|---|---|---|
| A | Bug Fix | Standard |
| B | Documentation | Standard |
| C | Feature | Enhanced |
| D | Performance Optimization | Enhanced |
| E | Security Improvement | Security Review |
| F | Refactoring | Architecture Review |
| G | Architecture Change | RFC + Approval |
| H | Infrastructure Change | RFC + Approval |
| I | Breaking Change | RFC + Explicit Approval |

---

## Refactor Policy

Major refactoring is prohibited during feature implementation.

Large refactoring requires:
- Dedicated Program
- Architecture Review
- Impact Analysis
- Migration Plan
- Rollback Plan
- Performance Validation
- Explicit Approval

Refactoring must never be hidden inside unrelated pull requests.

---

## Breaking Change Policy

Breaking changes require:
- RFC
- Impact Analysis
- Compatibility Analysis
- Migration Guide
- Rollback Strategy
- Version Increment
- Explicit Approval

No breaking change may be introduced silently.

---

## Feature Isolation Policy

Every feature must remain isolated.

A feature implementation must not:
- Rename unrelated files
- Move unrelated directories
- Rewrite unrelated modules
- Modify unrelated architecture

Unless explicitly approved.

---

## Dependency Policy

Before introducing any dependency:
1. Search for existing capability
2. Evaluate: Maintenance, Security, License, Community, Performance, Alternatives, Long-term viability
3. Generate Dependency Evaluation Report

---

## Technical Debt Policy

Technical debt must never be hidden.

Every known debt becomes DEBT-NNNNNN with:
- Description
- Impact
- Priority
- Risk
- Estimated Cost
- Recommended Resolution
- Status

---

## Rollback Policy

Every non-trivial modification requires:
- Rollback Procedure
- Rollback Validation
- Rollback Duration Estimate
- Recovery Instructions

No implementation is complete without rollback.

---

## Observability Policy

Every production-impacting feature must define:
- Logging
- Metrics
- Health Checks
- Alerts
- Tracing
- Failure Detection
- Recovery Indicators

---

## Performance Budget

Every feature must define:
- Expected Latency
- Memory Impact
- CPU Impact
- Storage Impact
- Network Impact
- Scalability Impact
- Performance Regression Risk

---

## Security Review

Security review is mandatory for:
- Authentication
- Authorization
- Encryption
- Secrets
- External APIs
- Infrastructure
- Deployment
- Data Storage

---

## Release Readiness

No release is approved until:
- Architecture Review Passed
- Security Review Passed
- Performance Review Passed
- Quality Gates Passed
- Rollback Verified
- Documentation Updated
- Knowledge Updated
- Registries Updated
- Constitution Compliance Passed

---

## Final Stability Rule

Platform stability has higher priority than feature velocity.
Engineering quality has higher priority than implementation speed.
Long-term maintainability has higher priority than short-term convenience.

No feature is allowed to reduce the overall reliability, recoverability,
security or maintainability of the GULA Platform.

---

## References

- AI_OPERATING_CONSTITUTION.md — Supreme authority
- `.ai/core/quality/GOVERNANCE_RULES.md` — Governance rules
- `.ai/core/quality/RISK_MANAGEMENT.md` — Risk management
- `.ai/core/quality/AI_DECISION_FRAMEWORK.md` — Decision framework

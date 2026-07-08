# Digital Constitution — GULA Platform

**Version:** 1.0.0
**Date:** 2026-07-08
**Classification:** Internal — Engineering

---

## Preamble

This Digital Constitution establishes the foundational principles, rights, and responsibilities governing all software engineering work on the GULA Platform. It derives authority from the Engineering Constitution (`CLAUDE.md`) and serves as the reference for architectural decisions, code quality, security, and data governance.

## Article I: Core Principles

### Section 1.1 — Patient Safety
Patient data integrity is the highest priority. No change may risk patient data loss, corruption, or unauthorised disclosure.

### Section 1.2 — Stability
Working code must not be broken to add features. Stability is a feature.

### Section 1.3 — Fix Before Feature
Bugs and security vulnerabilities take priority over new functionality.

### Section 1.4 — Test Then Commit
All changes must pass quality gates before integration. Untested code is not complete.

## Article II: Architecture

### Section 2.1 — Layered Architecture
The system follows a strict layered architecture: routes → services → models. Upper layers may depend on lower layers. Lower layers must not depend on upper layers.

### Section 2.2 — Monolith First
The monolith is the production deployment target. The microservices tree exists for future decomposition but is not the primary deployment target.

### Section 2.3 — Tenant Isolation
Every patient-data query must filter by `lab_id`. Multi-tenant isolation is non-negotiable.

## Article III: Data Governance

### Section 3.1 — Data Classification
- **Critical:** Patient data, national IDs, lab results, audit logs
- **Sensitive:** User credentials, API keys, encryption keys
- **Internal:** Configuration, logs, metrics
- **Public:** Documentation, marketing materials

### Section 3.2 — Encryption at Rest
All sensitive patient data (national_id, health_id) must be encrypted at rest using AES-256. No plaintext storage of national IDs.

### Section 3.3 — Audit Trail
Every data mutation must be recorded in the immutable audit log with hash-chain integrity. The audit trail must include user_id, lab_id, timestamp, and previous hash.

## Article IV: Security

### Section 4.1 — Authentication
All API access requires JWT authentication. Tokens must have expiry and support refresh rotation.

### Section 4.2 — Authorisation
Access control follows RBAC with 9 roles and 13 permissions. Every request must verify the user's role and lab_id.

### Section 4.3 — Rate Limiting
All endpoints must be rate-limited per user to prevent abuse.

### Section 4.4 — Secrets Management
No secrets may be hardcoded. All secrets must come from environment variables with no default values. Weakness detection must fail startup.

## Article V: Database

### Section 5.1 — Migration Immutability
Existing migrations must never be modified. All schema changes require a new Alembic revision.

### Section 5.2 — Migration Idempotency
Every migration must use `_has_column()`, `_table_exists()`, and `_index_exists()` guards.

### Section 5.3 — Nullable New Columns
New columns must be nullable or have a `server_default`. Non-nullable columns without defaults break existing rows.

## Article VI: Testing

### Section 6.1 — Quality Gates
All changes must pass:
1. Ruff lint (E9, F821 — errors only)
2. Ruff format (all files formatted)
3. PyCompile (all files compile)
4. pytest (no regressions)

### Section 6.2 — Coverage Target
The platform targets 70% overall coverage, with 90%+ in security, models, and integration.

### Section 6.3 — Test Categories
Tests must be categorised as unit, integration, security, or stress using pytest markers.

## Article VII: Decision Records

### Section 7.1 — ADR Requirement
All significant architectural decisions must be captured as Architecture Decision Records (ADRs).

### Section 7.2 — ADR Format
ADRs must follow the template in `docs/adr/README.md` and include context, decision, alternatives considered, and consequences.

### Section 7.3 — Immutability
Accepted ADRs are immutable. Superseded ADRs must reference their replacement.

## Article VIII: Autonomous Agents

### Section 8.1 — Always Safe
- Ruff lint/format fixes
- Missing indexes (as new migrations)
- Log message corrections
- Test case additions
- Documentation updates

### Section 8.2 — Requires Approval
- JWT/auth logic changes
- Billing/subscription changes
- Schema changes
- API response shape changes
- CI pipeline changes
- Production data flag toggles

### Section 8.3 — Never Autonomously
- Table deletion or truncation
- Secret default changes
- Pushing to main
- Audit log reduction
- Rate limiting disablement
- Base migration modification

## Article IX: CI/CD

### Section 9.1 — Pipeline Required
Every push must trigger CI. The pipeline must include syntax check, migration test, smoke test, full test suite, and security scan.

### Section 9.2 — Gate Enforcement
Failed gates must block merge. Quality gate bypass is not permitted.

## Article X: Amendments

### Section 10.1 — Amendment Process
Constitutional amendments require:
1. ADR documenting the proposed change
2. Engineering Lead approval
3. Team notification

### Section 10.2 — Versioning
This Constitution is versioned. Breaking changes require a new major version.

---

*This Constitution is a living document. It evolves with the platform while preserving its core principles.*

**References:**
- `CLAUDE.md` — Root Engineering Constitution
- `docs/adr/` — Architecture Decision Records
- `docs/engineering/` — Engineering assessment documents
- `QUALITY.md` — Quality gate matrix

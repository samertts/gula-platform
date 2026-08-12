# Architecture Decisions — GULA Platform

**Version:** 1.0.0
**Date:** 2026-07-08
**Classification:** Internal — Engineering

---

## Purpose

This document summarises and indexes all Architecture Decision Records (ADRs) for the GULA Platform. Each ADR captures a significant architectural decision, its context, alternatives considered, and consequences.

## ADR Index

| ADR | Title | Status | Date | Key Decision |
|-----|-------|--------|------|--------------|
| ADR-001 | Engineering Constitution as Root Authority | Accepted | 2026-07-06 | `CLAUDE.md` as root authority for all engineering decisions |
| ADR-002 | Monolith First Architecture | Accepted | 2026-01-01 | FastAPI monolith as primary deployment target |
| ADR-003 | Multi-Tenant Isolation via lab_id | Accepted | 2026-01-01 | All queries filtered by lab_id for tenant isolation |
| ADR-004 | Skill Platform Architecture | Accepted | 2026-07-06 | Plugin-based skill platform for extensibility |
| ADR-005 | PostgreSQL 16 with Redis 7 | Draft | 2026-07-08 | Database and cache technology stack |
| ADR-006 | Clinical AI Integration | Draft | 2026-07-08 | AI engine integration architecture |
| ADR-007 | Device Bridge ASTM/HL7 | Draft | 2026-07-08 | Lab instrument integration via bridge service |
| ADR-008 | Patient Card System | Draft | 2026-07-08 | QR-backed digital patient cards |
| ADR-009 | Self-Healing Infrastructure | Draft | 2026-07-08 | Circuit breakers, auto-repair, adaptive concurrency |
| ADR-010 | SNDHS-lite Government Integration | Draft | 2026-07-08 | National health data system integration |

## Pattern Decisions

### API Design

| Decision | Choice | Rationale |
|----------|--------|-----------|
| API style | RESTful | Predictable, cacheable, widely understood |
| Response format | JSON | Universal, Arabic-supported (UTF-8) |
| Versioning | URL prefix (`/v1/`) | Simple, explicit, easy to route |
| Error format | Consistent error envelope | RFC 7807-inspired Problem Details |

### Data Layer

| Decision | Choice | Rationale |
|----------|--------|-----------|
| ORM | SQLAlchemy 2.0 | Mature, async support, Alembic integration |
| Migrations | Alembic | Industry standard for SQLAlchemy |
| Connection pool | SQLAlchemy pool | Configurable, monitored, contextvar-bound |
| Caching | Redis 7 | Fast, pub/sub capability, rate limiting support |

### Security

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Auth tokens | JWT | Stateless, standard, widely supported |
| Password hashing | bcrypt | Industry standard, configurable cost |
| Encryption | AES-256 | FIPS-compliant, sufficient for healthcare |
| Audit logging | Hash chain | Tamper-evident, verifiable integrity |
| Rate limiting | Redis-backed | Distributed, performant, configurable |

### Deployment

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Container runtime | Docker | Universal, CI/CD integration |
| Orchestration | Docker Compose | Simple, sufficient for current scale |
| Load balancer | HAProxy | Battle-tested, observable |
| Cloud provider | DigitalOcean | Cost-effective, Iraqi data center option |

## Architecture Invariants

### Non-Negotiable

1. All patient-data queries filter by `lab_id`
2. All mutations write to audit log
3. National IDs encrypted at rest
4. No hardcoded secrets
5. Immutable database migrations
6. JWT verification before data access

### Enforced by Quality Gates

7. All files must pass ruff lint and format
8. All files must compile (py_compile)
9. Tests must pass before merge
10. Security scans must pass (Bandit)

### Best Practice (recommended)

11. Type annotations on all new code
12. Tests for all new routes/services
13. ADR for significant decisions
14. Feature flags for rollout control
15. Documentation alongside code changes

## Decision Log (Informal)

| Date | Decision | Rationale | Replaces |
|------|----------|-----------|----------|
| 2026-07-08 | `.venv/bin/python` for all Python commands | System Python 3.10 lacks `datetime.UTC` | N/A |
| 2026-07-08 | N818 suppression on IntegrationException | Renaming would break all consumers | N/A |
| 2026-07-08 | Keep bcrypt 4.1.3 despite deprecation warning | Passlib/bcrypt compatibility | N/A |
| 2026-07-08 | Test file rewrites instead of deletions | Preserves test intent while fixing | N/A |

## References

- `docs/adr/` — Full ADR documents
- `docs/adr/README.md` — ADR process and template
- `docs/engineering/DIGITAL-CONSTITUTION.md` — Digital Constitution
- `CLAUDE.md` — Engineering Constitution
- `QUALITY.md` — Quality gate matrix

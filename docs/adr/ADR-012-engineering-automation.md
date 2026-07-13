# ADR-012: Engineering Automation Platform

**Status:** Accepted
**Date:** 2026-07-13
**Deciders:** Engineering Lead

## Context

GULA has many repetitive engineering tasks: creating new modules, CRUD endpoints, DTOs, repositories, tests, and documentation. Manual creation is error-prone and inconsistent.

## Decision

Build an Engineering Automation Platform under `backend/app/engineering/` with:
- **Generators** — Code generation for modules, CRUD, DTOs, repositories, REST APIs, CQRS, plugins, microservices, projects, capabilities
- **Validators** — Architecture compliance checks (Clean Architecture, DDD, CQRS, SOLID, Event-Driven)
- **Intelligence** — Knowledge graph, dependency graph, duplicate detection, changelog/ADR/release automation
- **Quality Gates** — Automated quality enforcement (lint, typecheck, test, security scan)
- **CI/CD** — GitHub Actions generation and CI pipeline configuration
- **Security** — SBOM generation and vulnerability scanning

## Alternatives Considered

- **External tools (Yeoman, Plop)** — Rejected due to platform-specific requirements
- **Manual creation** — Rejected due to inconsistency and errors

## Consequences

Positive:
- Consistent code structure across the platform
- Faster development of new modules
- Automated architecture compliance
- Built-in quality enforcement

Negative:
- Maintenance burden for generator templates
- Generators must stay in sync with platform conventions

## References

- `backend/app/engineering/` — Engineering platform implementation

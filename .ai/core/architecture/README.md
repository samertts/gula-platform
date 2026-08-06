---
id: ARCH-000001
type: architecture
title: "Architecture Knowledge Bridge"
version: "1.0"
created: "2026-08-04"
status: verified
confidence: 100%
tags: [architecture, bridge, index]
---

# Architecture Knowledge — Bridge Reference

## Canonical Architecture
- `docs/architecture/CANONICAL_ARCHITECTURE.md` — Authoritative system architecture

## Architecture Decision Records (ADRs)
- `docs/adr/ADR-001-engineering-constitution.md` through `ADR-025-*` — 30 ADRs
- `docs/architecture/ADR-008-layer-architecture.md` — Layer architecture
- `docs/architecture/ADR-009-uuid-pk-strategy.md` — UUID PK strategy
- `docs/architecture/ADR-010-mtls-decision.md` — mTLS decision
- `docs/architecture/ADR-011-fhir-strategy.md` — FHIR strategy
- `docs/architecture/ADR-012-sbom-strategy.md` — SBOM strategy

## Module Structure
- `docs/architecture/MODULE_DEPENDENCY_MATRIX.md` — Dependencies
- `docs/architecture/ENTITY_CATALOG.md` — All entities
- `docs/architecture/KNOWLEDGE_GRAPH.md` — Knowledge relationships

## Deployment Architecture
- `ARCHITECTURE.md` (root) — nginx, Docker, PostgreSQL, Redis topology

## Key Decisions
- Monolith-first (ADR-002) — start monolith, extract later
- PostgreSQL + Redis (ADR-005) — primary stack
- UUID PKs (ADR-009) — multi-tenant, offline-first
- FHIR R4 (ADR-011) — national interoperability

## Related
- `.ai/core/memory/PROJECT_MEMORY.md` — Technology stack
- `.ai/core/constitution/` — Platform constitution

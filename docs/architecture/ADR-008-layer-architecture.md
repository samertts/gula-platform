# ADR-008: Layer Architecture

**Status:** Accepted
**Date:** 2026-07-18
**Constitutional Basis:** PLATFORM-CONSTITUTION.md §2

## Context

The original GULA codebase used a 3-layer architecture: Routes → Services → Models. This was documented in CLAUDE.md and implemented throughout the monolith. However, as the platform grew, two problems emerged: (1) business logic leaked into services that should have been pure domain rules, and (2) infrastructure concerns (DB access, external APIs) mixed with domain logic, creating testability and coupling issues. The Engineering Constitution and Platform Constitution both describe a 4-layer architecture (Routes → Services → Domain → Infrastructure) that resolves these problems.

## Decision

Adopt the 4-layer architecture (Routes → Services → Domain → Infrastructure) as the canonical architecture for all new code. The layer dependency rules are:

| Rule | Description |
|------|-------------|
| R1 | Routes depend on Services only — never on Domain, Models, or Infrastructure |
| R2 | Services depend on Domain only — never on Routes, other Services directly, or Infrastructure |
| R3 | Domain depends on Nothing — pure business logic, no framework imports |
| R4 | Infrastructure depends on Nothing — implements ports defined in Domain |

## Rationale

- **Testability:** Domain logic is pure and can be unit-tested without mocks
- **Coupling:** Infrastructure swaps (e.g., Postgres → different DB) don't affect domain or services
- **Clarity:** Each layer has a single responsibility
- **Migration path:** Existing code can be refactored incrementally; the 3-layer pattern is still accepted for stable code

## Consequences

- New code MUST follow the 4-layer pattern
- Existing 3-layer code is grandfathered but should be migrated during active development
- Domain modules live in `backend/app/domain/`
- Infrastructure implementations live in `backend/app/infrastructure/`
- ORM models remain in `backend/app/models/` but are accessed only through Infrastructure repositories, never directly from Services or Routes

## Compliance

- CI lint rules will flag forbidden imports (e.g., a Route importing from Models or Infrastructure)
- Architecture review gates on PRs that add new modules
- Coverage requirements apply per layer

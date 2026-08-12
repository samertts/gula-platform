# Architecture Decision Records — National Governance Layer

## ADR-001: Separate Governance Package

**Status**: Accepted  
**Date**: 2026-07-14  
**Context**: The mission requires a single National Governance Layer that must not modify Foundation or National Healthcare Domain.  
**Decision**: Create `backend/app/governance/` as a fully isolated package with its own models, services, routes, policies, and enums.  
**Consequences**: Clean separation of concerns; governance can evolve independently; all future modules consume governance policies through the defined service boundary.

## ADR-002: Custom GovernanceBase (separate declarative base)

**Status**: Accepted  
**Context**: Governance tables must not pollute core platform schema. They need their own schema namespace.  
**Decision**: Use `GovernanceBase = declarative_base()` separate from the core `Base` and `NationalBase`.  
**Consequences**: Governance tables (`gov_*`) are isolated; alembic migrations handle them separately; no risk of table name collisions.  
**Pattern**: Follows existing pattern used by `national/` domain (NationalBase).

## ADR-003: Abstract Connector Pattern (STUB/LIVE/SHADOW)

**Status**: Accepted  
**Context**: Phase 3 requires citizen registry connectors without hardcoding external APIs. The existing gateway pattern in `gateways/` already supports this mode.  
**Decision**: Use abstract `ConnectorAdapter` base class with STUB implementations for all 9 connector types. Connectors are registered in an adapter registry and can be swapped at runtime.  
**Consequences**: No external API calls in initial implementation; LIVE mode can replace STUB without changing service code; SHADOW mode allows parallel testing.

## ADR-004: Governance Policy Engine (Default DENY)

**Status**: Accepted  
**Context**: Every governance action must be evaluated against policy before execution. Unknown actions must be blocked.  
**Decision**: Implement `GovernancePolicyEngine` with 17 enumerated actions, 4 risk levels, and `require_elevated_approval()` checks. Default stance is DENY.  
**Consequences**: All governance mutations are policy-gated; new governance actions must be explicitly registered; follows existing pattern from `core/policy_engine.py`.

## ADR-005: In-Memory Productivity Ranking

**Status**: Accepted  
**Context**: National ranking of healthcare workers requires ordering by quality score + tests performed within a period.  
**Decision**: Rank is computed on write (`_update_rankings()`) by querying all records in the same period and assigning ordinal positions.  
**Consequences**: Read is O(1); write is O(N) for the period; acceptable at national scale with appropriate indexing and pagination.

## ADR-006: Health Number as Public Identifier

**Status**: Accepted  
**Context**: Health numbers are public-facing identifiers (printed on cards, barcodes, QR codes). They must be unique but must not reveal sensitive information.  
**Decision**: Health numbers use format `HN-{hash}-{month_code}` where the hash is SHA-256 of citizen_ulid + random + date, truncated to 12 hex chars.  
**Consequences**: Unforgeable; no sequential enumeration; no PII leakage; collision probability is negligible.

## ADR-007: Route Registration in main.py

**Status**: Accepted  
**Context**: Governance routes must be registered in the FastAPI app alongside existing routes.  
**Decision**: Register governance router and analytics router in `main.py` after kernel routes, clearly commented as the Governance Layer boundary.  
**Consequences**: Routes are available at `/governance/*`; consistent with existing route registration pattern; clearly demarcated in the codebase.

## ADR-008: Test Strategy

**Status**: Accepted  
**Context**: Phase 11 requires ≥95% test coverage with architecture tests, security tests, policy tests, integration tests.  
**Decision**: Create `backend/tests/test_governance.py` with unit tests for each service and route integration tests. Leverage existing pytest fixtures from `conftest.py`.  
**Consequences**: Single comprehensive test file; coverage can be measured incrementally; tests run as part of `make test`.

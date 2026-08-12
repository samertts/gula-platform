# GULA Platform Technical Debt Register

> Version 1.0 | Last Updated: 2026-07-17
> Owner: Platform Engineering
> Total Items: 10 | Total Estimated Effort: 120 days | Total Interest: ~$4,200/month (est.)

---

## Format

Each entry follows this structure:

```
ID: TD-NNN
Description: Clear description of the debt
Location: File paths or module references
Estimated Effort: Person-days to remediate
Impact: 1-10 (10 = most impactful)
Priority: P1-P5 (P1 = must fix now, P5 = nice to have)
Interest Rate: Technical debt interest — % of effort added per month of delay
Remediation Strategy: How to fix it
Owner: Responsible team/individual
Date Identified: When this debt was first recognized
Target Resolution: Desired completion date
Status: Open / In Progress / Resolved / Accepted
```

---

## TD-001: Seven Microservice Stubs

**Description**: Seven top-level `services/` directories (lab, order, patient, result, sample, notification, ai) contain only stub implementations — minimal Dockerfile, placeholder main.py, basic health endpoint. These were created as part of a future decomposition plan that was deprioritized. The monolith (`backend/app/`) remains the sole source of truth for all business logic. The stubs waste developer attention, create confusion about architecture direction, and periodically tempt teams to add logic in the wrong place.

The CLAUDE.md explicitly warns: "services/ contains independent services... monolith is still the source of truth for business logic," but the stubs remain as potential maintenance sinks.

**Location**:
- `services/lab/`
- `services/order/`
- `services/patient/`
- `services/result/`
- `services/sample/`
- `services/notification/`
- `services/ai/`

**Estimated Effort**: 5 days (decision + cleanup + documentation update)
**Impact**: 4/10
**Priority**: P3
**Interest Rate**: 2%/month — each month, more effort is needed to remember why stubs exist, and more developers waste time investigating them

**Remediation Strategy**: Choose one:
1. **Remove stubs** (recommended): Delete service directories, update CI matrix, update CLAUDE.md and docs. Simplifies the codebase significantly. Create a single `services/README.md` explaining the history.
2. **Complete stubs**: If decomposition is planned within 6 months, complete the stubs with proper API contracts, tests, and CI pipeline. Document expected timeline.
3. **Keep as-is but document**: Add prominent README to each stub explaining its purpose (or lack thereof).

**Preferred**: Option 1 — remove stubs, focus on monolith quality.

**Owner**: Platform Engineering
**Date Identified**: 2026-03-15 (monorepo consolidation)
**Target Resolution**: 2026-09-30
**Status**: Open

---

## TD-002: Backend Dual Structure — Experimental Stubs

**Description**: The `backend/` directory contains two parallel structures that create confusion:
1. `backend/services/` with `api/` subdir — experimental stubs
2. `backend/core/` with `api/` subdir — experimental stubs

The CLAUDE.md warns: "both with api/ subdirs are experimental stubs — avoid committing business logic there." This creates a confusing dual structure where developers must know which `core/` or `services/` directory is active. New team members frequently ask which one to use.

**Location**:
- `backend/services/` (vs `backend/app/services/`)
- `backend/core/` (vs `backend/app/core/`)

**Estimated Effort**: 3 days (audit + cleanup + migration)
**Impact**: 3/10
**Priority**: P4
**Interest Rate**: 1%/month — low rate because the CLAUDE.md warning is effective, but confusion persists

**Remediation Strategy**:
1. Audit each file in `backend/services/` and `backend/core/` for any business logic
2. Move any non-stub code to `backend/app/` equivalents
3. Delete `backend/services/` and `backend/core/` experimental directories
4. Update CI, linting, and documentation

**Owner**: Backend Team Lead
**Date Identified**: 2026-03-15
**Target Resolution**: 2026-12-31
**Status**: Open

---

## TD-003: Migration Volume — 47 Alembic Revisions

**Description**: The project has accumulated 47 database migration files. While migrations are a sign of active development, this many revisions create:
- Slow `alembic upgrade head` as each migration is applied
- Risk when applying all migrations sequentially (failure at step 23/47)
- Complex dependency chain between revisions
- Difficulty understanding current schema without reading all migrations
- CI migration-gate takes longer with each new migration

**Location**: `backend/migrations/versions/`
**Estimated Effort**: 5 days (squash planning + execution + testing)
**Impact**: 5/10
**Priority**: P3
**Interest Rate**: 3%/month — each new migration adds to the total; compounding slows all migration operations

**Remediation Strategy**: Squash migrations periodically (e.g., every 6 months or every 50 migrations):
1. Create a new base migration that represents the current schema
2. Renumber to `20260717_0000_squashed_migrations.py`
3. Update `alembic_version` in production to skip old migrations
4. Document the squashing process for future reference
5. Mark old migrations as superseded

**Risk**: Squashing makes `alembic downgrade` impossible for old migrations. Mitigation: Keep old migration directory as documentation; mark them as squashed.

**Owner**: Backend Team Lead
**Date Identified**: 2026-07-17
**Target Resolution**: 2026-10-31
**Status**: Open

---

## TD-004: Adaptive Concurrency — Reactive Design

**Description**: The adaptive concurrency system (`backend/app/main.py::_adaptive_concurrency_loop`) is reactive rather than proactive. It halves `_MAX_CONCURRENT` only after detecting 2 slow DB readings (>300ms) and restores after 3 fast readings (<150ms). This means:

- Performance degradation must be detected before action is taken
- The system oscillates: degrade -> recover -> degrade
- No predictive component (could anticipate load based on request patterns)
- No circuit breaker coordination (concurrency and circuit breaker operate independently)
- Concurrency limits don't account for request types (clinical writes are exempt, but other operations share the same pool)

**Location**: `backend/app/main.py` (`_adaptive_concurrency_loop`), `backend/app/core/self_healing.py`
**Estimated Effort**: 10 days (redesign + implementation + testing)
**Impact**: 6/10
**Priority**: P2
**Interest Rate**: 2%/month — each production incident caused by overload increases the urgency

**Remediation Strategy**:
1. Implement predictive concurrency using moving average of recent response times
2. Coordinate with circuit breaker (shared state for degraded mode)
3. Add per-endpoint-type concurrency pools (read vs write vs clinical)
4. Proactively reduce concurrency before thresholds are hit (anticipatory shedding)
5. Add metrics for concurrency state transitions
6. Implement gradual recovery (not binary halve/double)

**Owner**: Platform Engineering
**Date Identified**: 2026-03-15
**Target Resolution**: 2026-12-31
**Status**: Open

---

## TD-005: Circuit Breaker Coverage Gaps

**Description**: The circuit breaker in `backend/app/core/self_healing.py` covers database and Redis failures but has gaps in recovery and edge case scenarios:

**Gaps Identified**:

| Gap | Risk | Current Behavior |
|-----|------|------------------|
| DB partial availability | MEDIUM | Circuit opens on any DB failure; doesn't handle read-only mode |
| Redis partial failure | MEDIUM | Redis used for caching; circuit breaker treats as binary |
| Cascading recovery | HIGH | After circuit opens, recovery attempts may cause thundering herd |
| State machine persistence | MEDIUM | Circuit breaker state is in-memory; lost on process restart |
| Half-open timeout | MEDIUM | Single probe may not indicate true recovery |
| Manual override | LOW | No admin API to manually open/close circuit |
| Alert fatigue | MEDIUM | Same alert every 5 min during RED state without new information |
| Downstream dependency health | MEDIUM | Only checks DB/Redis, not dependent services |

**Location**: `backend/app/core/self_healing.py`
**Estimated Effort**: 15 days (gap analysis + implementation + testing)
**Impact**: 7/10
**Priority**: P2
**Interest Rate**: 3%/month — each outage where recovery fails increases interest

**Remediation Strategy**:
1. Implement graduated circuit states (not just open/closed/half-open)
2. Add persistence for circuit state (Redis or DB-backed)
3. Implement thundering herd protection (jitter, backoff coordination)
4. Add admin API for manual override (`POST /admin/circuit-breaker`)
5. Implement smart health probes that verify full functionality
6. Add circuit breaker for downstream dependencies (device bridge, SNDHS API)
7. Improve alerting with deduplication and state change aggregation

**Owner**: Platform Engineering
**Date Identified**: 2026-04-01
**Target Resolution**: 2026-11-30
**Status**: Open

---

## TD-006: Test Coverage Gaps

**Description**: The platform has 28 test modules for 36+ routes and 17+ models. While critical paths are covered, there are significant gaps:

**Known Gaps**:

| Gap | Risk | Details |
|-----|------|---------|
| Route coverage gap | MEDIUM | Not all 36 routes have individual test modules |
| Edge case coverage | HIGH | Error handling and boundary conditions may be untested |
| Integration coverage | MEDIUM | End-to-end tests cover critical paths but not all scenarios |
| UI/E2E tests | HIGH | No browser-based or API E2E tests for clinical workflows |
| Performance regression tests | MEDIUM | No automated comparison of before/after performance |
| Security regression tests | MEDIUM | test_security.py covers invariants but may miss new vectors |
| Migration test coverage | LOW | Only upgrade/downgrade tested, not data correctness |
| Chaos test coverage | LOW | Tests/chaos exists but may not cover all failure modes |

**Location**: `backend/tests/` (28 test modules)
**Estimated Effort**: 20 days (gap analysis + test writing)
**Impact**: 7/10
**Priority**: P2
**Interest Rate**: 5%/month — each release without full coverage increases regression risk; bug fixes without tests are 3x more likely to reintroduce issues

**Remediation Strategy**:
1. Map every route to a test function (create tracking spreadsheet)
2. Write tests for uncovered routes (minimum: happy path + error case)
3. Add property-based testing for domain logic (order state machine, clinical calculations)
4. Implement E2E test suite for critical clinical workflows
5. Add performance regression test harness (baseline + comparison)
6. Integrate test coverage into CI quality gates (incremental improvement)

**Owner**: Quality Engineering Lead
**Date Identified**: 2026-03-15
**Target Resolution**: 2027-03-31
**Status**: Open

---

## TD-007: Frontend Fragmentation

**Description**: The platform has three separate frontend applications, each with different tech stacks and deployment patterns:

1. **`frontend/`** — Static HTML PWA (offline-capable)
2. **`frontend-v2/`** — Rich React + Firebase UI (citizen portal, Ministry Command Centre, predictive analytics, doctor/lab dashboards)
3. **`client/`** — Lightweight tRPC + React SPA connected to gula-backend

This fragmentation creates:
- 3x maintenance burden for shared UI patterns
- Inconsistent UX across applications
- Split developer expertise (React, vanilla JS, React + tRPC)
- Complex deployment pipeline (3 frontends + backend)
- Potential security issues if one frontend lags behind in security patches
- Duplicate state management, API client code, and authentication logic

**Location**:
- `frontend/` (static PWA)
- `frontend-v2/` (React + Firebase)
- `client/` (tRPC + React)

**Estimated Effort**: 40 days (consolidation + migration)
**Impact**: 6/10
**Priority**: P3
**Interest Rate**: 2%/month — each new feature must be implemented in 1-3 frontends

**Remediation Strategy**:
1. Conduct UX audit to determine which frontend serves which use case
2. Choose primary frontend technology (recommended: frontend-v2 with React + Firebase, since it has the richest feature set)
3. Migrate `frontend/` PWA functionality into frontend-v2
4. Migrate `client/` tRPC features into frontend-v2 or merge the API patterns
5. Decommission legacy frontends once migration is complete
6. Document the chosen architecture in CLAUDE.md and ADR

**Owner**: Product Engineering Lead
**Date Identified**: 2026-03-15
**Target Resolution**: 2027-06-30
**Status**: Open

---

## TD-008: Device Bridge ASTM/HL7 Monoculture

**Description**: The device bridge (`services/device_bridge/`, formerly `samertts/LabLink-Core`) only supports ASTM and HL7 protocols for lab instrument integration. While these cover the majority of Iraqi lab instruments (Sysmex, Roche, Mindray), the monoculture creates risk:

- Cannot integrate labs with DICOM-based instruments (imaging, pathology)
- Cannot integrate with instruments using proprietary or newer protocols (LIS2-A, POCT1-A)
- Driver development is a bottleneck for new lab onboarding
- Protocol parsing code is tightly coupled (hard to add new protocols)
- No standardized device simulator for testing without physical hardware

**Location**: `services/device_bridge/`
**Estimated Effort**: 20 days (protocol abstraction + DICOM support)
**Impact**: 5/10
**Priority**: P3
**Interest Rate**: 2%/month — each new lab with unsupported instruments requires custom integration work

**Remediation Strategy**:
1. Refactor device bridge to use plugin-based protocol architecture
2. Add protocol adapter interface (`ProtocolAdapter` base class)
3. Implement DICOM support for imaging/pathology labs
4. Add device simulator harness for protocol-level testing
5. Document protocol integration guide for third-party development
6. Create lab instrument compatibility matrix

**Owner**: Device Bridge Team Lead
**Date Identified**: 2026-03-15
**Target Resolution**: 2027-03-31
**Status**: Open

---

## TD-009: Documentation Depth Gaps

**Description**: While the `docs/engineering/` directory covers architecture and operations, several areas lack sufficient depth:

**Gap Areas**:

| Area | Current State | Needed |
|------|--------------|--------|
| API reference | OpenAPI generated | Usage examples, common scenarios, error codes |
| Deployment runbooks | N/A | Per-environment deployment procedures |
| Disaster recovery | N/A | RPO/RTO, backup restoration procedure, DR test plan |
| Onboarding guide | N/A | Step-by-step for new developers |
| Clinical workflow docs | N/A | How the platform supports each clinical workflow step |
| Feature flag documentation | CLAUDE.md summary | Per-flag behavior, dependencies, rollout plan |
| Performance baseline | N/A | Documented p50/p95/p99 for all endpoint categories |
| Security architecture | Implicit | Threat model, data flow diagram, trust boundaries |
| Testing strategy | CLAUDE.md summary | How to write tests, test naming conventions, fixtures |

**Location**: `docs/` directory
**Estimated Effort**: 15 days per gap (135 days total)
**Impact**: 4/10
**Priority**: P4
**Interest Rate**: 1%/month — undocumented systems create bus-factor risk

**Remediation Strategy**:
1. Create docs inventory and prioritize by impact
2. Focus on: onboarding guide, disaster recovery, and clinical workflow docs first
3. Use ADR for architecture decisions (capture rationale)
4. Automate API reference generation from OpenAPI spec
5. Create doc templates to ensure consistency
6. Add doc review to PR checklist for significant changes

**Owner**: Platform Engineering
**Date Identified**: 2026-07-17
**Target Resolution**: 2027-12-31
**Status**: Open

---

## TD-010: Arabic-First Translation Gaps

**Description**: The platform is an "Arabic-first" healthcare platform, but the i18n implementation has gaps:

**Known Gaps**:

| Gap | Impact | Location |
|-----|--------|----------|
| Incomplete Arabic translations | Platform appears partially English | All frontends |
| Clinical term consistency | Medical terms may differ from Iraqi usage | Translation files |
| RTL layout edge cases | Occasional broken layout in Arabic mode | Frontend CSS |
| Number format handling | Arabic (Hindi) numerals vs Western numerals | Frontend rendering |
| Calendar coexistence | Islamic calendar not always supported | Date pickers |
| Machine-translated content | Clinical content must be human-reviewed | Translation files |
| Missing translate function calls | New components may skip i18n wrapper | Frontend code |

**Location**: Frontend translation files, frontend-v2 i18n configuration, frontend/ PWA
**Estimated Effort**: 15 days (audit + review + corrections)
**Impact**: 8/10
**Priority**: P1
**Interest Rate**: 5%/month — as the platform grows, more untranslated English content accumulates

**Remediation Strategy**:
1. Complete i18n audit: identify all untranslated strings across all frontends
2. Clinical terminology review: engage Iraqi medical professionals to review translations
3. RTL layout audit: test every UI component in Arabic mode
4. Implement translation CI gate: new strings require Arabic translation before merge
5. Create translation glossary for consistent clinical terms
6. Add locale switching test to E2E test suite
7. Document i18n patterns in developer onboarding guide

**Owner**: Product Engineering Lead
**Date Identified**: 2026-03-15
**Target Resolution**: 2026-09-30
**Status**: Open

---

## Summary Dashboard

| ID | Description | Effort (days) | Impact | Priority | Interest | Status |
|----|-------------|---------------|--------|----------|----------|--------|
| TD-001 | 7 Microservice Stubs | 5 | 4/10 | P3 | 2%/mo | Open |
| TD-002 | Backend Dual Structure | 3 | 3/10 | P4 | 1%/mo | Open |
| TD-003 | Migration Volume (47 revisions) | 5 | 5/10 | P3 | 3%/mo | Open |
| TD-004 | Adaptive Concurrency Reactive | 10 | 6/10 | P2 | 2%/mo | Open |
| TD-005 | Circuit Breaker Gaps | 15 | 7/10 | P2 | 3%/mo | Open |
| TD-006 | Test Coverage Gaps | 20 | 7/10 | P2 | 5%/mo | Open |
| TD-007 | Frontend Fragmentation | 40 | 6/10 | P3 | 2%/mo | Open |
| TD-008 | Device Bridge Monoculture | 20 | 5/10 | P3 | 2%/mo | Open |
| TD-009 | Documentation Depth Gaps | 15 | 4/10 | P4 | 1%/mo | Open |
| TD-010 | Arabic-First Translation Gaps | 15 | 8/10 | P1 | 5%/mo | Open |

### Priority Distribution

```
P1 (Critical):  1 item — TD-010 (Arabic translations)
P2 (High):      3 items — TD-004, TD-005, TD-006
P3 (Medium):    4 items — TD-001, TD-003, TD-007, TD-008
P4 (Low):       2 items — TD-002, TD-009
P5 (Nice to have): 0 items
```

### Monthly Interest Summary

| Priority | Monthly Interest (est.) |
|----------|------------------------|
| All items | ~$4,200/month (est.) |
| P1 items | ~$1,500/month |
| P2 items | ~$1,800/month |
| P3-P4 items | ~$900/month |

### Remediation Roadmap

```
Q3 2026 (Jul-Sep)
  ├── P1: TD-010 Arabic translations ───────────────────── 15 days
  ├── P2: TD-005 Circuit breaker gaps (phase 1) ────────── 10 days
  └── P3: TD-001 Remove microservice stubs ─────────────── 5 days

Q4 2026 (Oct-Dec)
  ├── P2: TD-004 Adaptive concurrency ──────────────────── 10 days
  ├── P2: TD-006 Test coverage gaps (phase 1) ──────────── 10 days
  ├── P3: TD-003 Squash migrations ─────────────────────── 5 days
  └── P4: TD-002 Clean up dual structure ───────────────── 3 days

Q1 2027 (Jan-Mar)
  ├── P2: TD-005 Circuit breaker gaps (phase 2) ────────── 5 days
  ├── P2: TD-006 Test coverage gaps (phase 2) ──────────── 10 days
  └── P3: TD-008 Device bridge protocol expansion ─────── 20 days

Q2-Q4 2027
  ├── P3: TD-007 Frontend consolidation ────────────────── 40 days
  └── P4: TD-009 Documentation depth ───────────────────── 15 days
```

## Addendum: Adding New Debt Items

When adding a new technical debt item:

1. Assign next available ID (TD-011, TD-012, ...)
2. Include all required fields
3. Estimate effort conservatively (actual work is usually 1.5x estimate)
4. Set interest rate based on compounding impact per month delayed
5. Get owner acknowledgment before adding to register
6. Update the summary dashboard

## Review Cadence

- **Monthly**: Review open items, update status, adjust priorities
- **Quarterly**: Re-estimate effort and impact, recalculate interest
- **Per-release**: Assess whether any debt items can be partially resolved
- **Annual**: Full review of all items, close resolved or obsolete entries

---

*This register is maintained by Platform Engineering. Monthly review required.*

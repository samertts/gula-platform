# GULA Platform Improvement Backlog

> Version 1.0 | Last Updated: 2026-07-17
> Owner: Platform Engineering
> Total Items: 45 | Estimated Total Effort: 320 days

---

## Quick Wins (1-2 days, High Impact)

Items that can be completed in 1-2 days with disproportionate positive impact.

### QW-001: Add README to undocumented modules

**Title**: Document undocumented Python packages
**Description**: The following packages lack README files: `backend/app/ai/`, `backend/app/firewall/`, `backend/app/edge/`, `backend/app/gateways/`. Each needs a short README explaining purpose, key classes, and relationships.
**Motivation**: Developer onboarding suffers when module purposes are unclear. These packages handle important functions (AI integration, firewall/rate-limiting, edge sync, API gateways) that new team members need to understand.
**Estimated Effort**: 1 day
**Impact Score**: 6/10
**Risk Reduction Score**: 3/10
**Dependencies**: None
**Acceptance Criteria**: Each of the 4 modules has README.md with: purpose statement, main components, usage example, related modules
**Suggested Assignee**: Quality Engineering Lead

### QW-002: Add flake8 pre-commit hook

**Title**: Automate lint check before commits
**Description**: Add a pre-commit hook configuration that runs `flake8 --select=E9,F821` on staged files before each commit. Use `pre-commit` framework or `.git/hooks/pre-commit` script.
**Motivation**: Catches syntax errors and undefined names before they reach CI. Reduces CI pipeline failures and speeds up feedback loops. CLAUDE.md already documents `make lint` but doesn't enforce pre-commit.
**Estimated Effort**: 0.5 day
**Impact Score**: 7/10
**Risk Reduction Score**: 6/10
**Dependencies**: None
**Acceptance Criteria**: Pre-commit hook installed and working; `git commit` with lint error is blocked with helpful message
**Suggested Assignee**: Platform Engineering

### QW-003: Add database indexes for slow query patterns

**Title**: Index missing columns on large tables
**Description**: Based on `pg_stat_user_tables` analysis, add indexes for frequently queried columns on `audit_logs`, `outbox_events`, and `lab_results`. Likely candidates: `audit_logs.resource_type`, `outbox_events.status`, `lab_results.order_id`.
**Motivation**: Slow queries cause timeouts and poor UX. Indexes are the highest-leverage performance improvement. Must be done via new Alembic migration.
**Estimated Effort**: 1 day
**Impact Score**: 8/10
**Risk Reduction Score**: 7/10
**Dependencies**: DB access, Alembic migration
**Acceptance Criteria**: New migration adds indexes; `EXPLAIN ANALYZE` shows index usage; migration round-trip verified
**Suggested Assignee**: Backend Team Lead

### QW-004: Add Arabic translation CI gate

**Title**: Block PRs with missing Arabic translations
**Description**: Add a CI check that verifies any new i18n keys in frontend code have corresponding Arabic translations before merge. Can be a simple script that compares translation files.
**Motivation**: Arabic-first platform must enforce Arabic translation completeness. Currently relies on developer discipline. One CI check prevents English-only content from reaching users.
**Estimated Effort**: 1 day
**Impact Score**: 9/10
**Risk Reduction Score**: 8/10
**Dependencies**: Frontend translation files identified
**Acceptance Criteria**: CI fails if PR adds new i18n keys without Arabic translation; pass if all new keys have translations
**Suggested Assignee**: Product Engineering Lead

### QW-005: Add health check timeout configuration

**Title**: Make health check timeouts configurable via env vars
**Description**: Docker HEALTHCHECK intervals and timeouts are currently hardcoded in Dockerfile. Move to environment variables with sensible defaults so operators can tune without rebuilding.
**Motivation**: During startup, the 40s start period may be insufficient for slow environments. Quick config change avoids rebuild.
**Estimated Effort**: 0.5 day
**Impact Score**: 4/10
**Risk Reduction Score**: 5/10
**Dependencies**: None
**Acceptance Criteria**: HEALTHCHECK parameters configurable via env vars; defaults match current values; documented in .env.example
**Suggested Assignee**: Platform Engineering

### QW-006: Add Slack release notification

**Title**: Automate release deployment notifications to Slack
**Description**: When a release tag is pushed, send a notification to #releases channel with version, changelog summary, and deployment status link.
**Motivation**: Keeps the team informed about releases without manual Slack messages. Reduces communication overhead.
**Estimated Effort**: 0.5 day
**Impact Score**: 5/10
**Risk Reduction Score**: 2/10
**Dependencies**: Slack webhook URL
**Acceptance Criteria**: Release tag push triggers Slack message with version, link to changelog, deployment status
**Suggested Assignee**: Platform Engineering

### QW-007: Add pytest-randomly for order-independent tests

**Title**: Enable random test ordering to detect order dependencies
**Description**: Add `pytest-randomly` plugin to requirements-dev.txt and configure it in pytest.ini. Run tests in random order in CI for a few cycles to detect flaky tests with order dependencies.
**Motivation**: Test order dependencies are a common source of flaky tests. Early detection prevents CI failures and wasted debugging time.
**Estimated Effort**: 0.5 day
**Impact Score**: 6/10
**Risk Reduction Score**: 6/10
**Dependencies**: None
**Acceptance Criteria**: pytest-randomly installed and configured; CI runs random order tests weekly; any failures logged for investigation
**Suggested Assignee**: Quality Engineering Lead

### QW-008: Add system_ready log message on startup

**Title**: Log startup milestone for debugging
**Description**: Add a clear INFO log message when `system_ready` transitions from False to True in `backend/app/core/startup_guard.py`. Include startup duration and component health summary.
**Motivation**: Currently, operators must infer startup completion from health endpoint responses. A clear log message pinpoints startup duration and any issues.
**Estimated Effort**: 0.5 day
**Impact Score**: 4/10
**Risk Reduction Score**: 4/10
**Dependencies**: None
**Acceptance Criteria**: Log line emitted at INFO level when system_ready=True; includes startup duration in ms and component status summary
**Suggested Assignee**: Backend Team Lead

### QW-009: Add Makefile quality-check shortcut

**Title**: Create `make quality` shortcut for quality checks
**Description**: Add a single `make quality` target that runs lint, type-check (if applicable), and the quality review engine scorecard. This is a developer convenience for fast feedback.
**Motivation**: Developers need a single command to check code quality before pushing. Reduces CI cycle time and catches issues earlier.
**Estimated Effort**: 0.5 day
**Impact Score**: 5/10
**Risk Reduction Score**: 5/10
**Dependencies**: Quality Review Engine implemented
**Acceptance Criteria**: `make quality` runs lint + quality scorecard; outputs pass/fail in under 30 seconds
**Suggested Assignee**: Platform Engineering

### QW-010: Add migration verification to CI

**Title**: Run migration round-trip in CI for every PR
**Description**: Add a CI job that starts a fresh PostgreSQL, runs `alembic upgrade head`, verifies required tables, then runs `downgrade -1` and `upgrade head`. Fail the PR if any step fails.
**Motivation**: Migration failures are often caught late (during release). Early detection in PR stage prevents merge of broken migrations. CI already does this for main branch.
**Estimated Effort**: 1 day
**Impact Score**: 8/10
**Risk Reduction Score**: 9/10
**Dependencies**: GitHub Actions with PostgreSQL service container
**Acceptance Criteria**: CI job added to PR workflow; fresh PostgreSQL migration round-trip passes; failure blocks merge
**Suggested Assignee**: Backend Team Lead

---

## Short-Term (1-2 weeks, 10 items)

### ST-001: Complete OpenAPI documentation for all endpoints

**Title**: Add Pydantic response models and descriptions to all routes
**Description**: Audit all 36+ route modules for missing OpenAPI documentation (response models, summary, description, request body schemas). Add missing docs.
**Motivation**: API consumers (frontend, device bridge, third-party integrations) rely on OpenAPI spec for development. Missing docs cause integration delays.
**Estimated Effort**: 5 days
**Impact Score**: 6/10
**Risk Reduction Score**: 4/10
**Dependencies**: None
**Acceptance Criteria**: All public routes have summary, description, and response model in OpenAPI schema; documentation coverage >= 95%
**Suggested Assignee**: Backend Team Lead

### ST-002: Implement migration squashing

**Title**: Create squashed base migration to reduce migration count
**Description**: Squash the 47 existing migrations into a single base migration representing current schema. Mark old migrations as superseded. Update alembic configuration.
**Motivation**: Reduces migration application time, lowers risk of sequential migration failure, simplifies schema understanding.
**Estimated Effort**: 5 days (see TD-003)
**Impact Score**: 7/10
**Risk Reduction Score**: 6/10
**Dependencies**: Agreement on squashing approach
**Acceptance Criteria**: New base migration created; all 47 old migrations superseded; `alembic upgrade head` on clean DB works; round-trip documented
**Suggested Assignee**: Backend Team Lead

### ST-003: Add performance regression test harness

**Title**: Automated baseline performance comparison
**Description**: Create a test harness that records endpoint latency baselines and compares them on each PR. Use locust or custom script to hit key endpoints, measure p50/p95/p99, and compare against baseline.
**Motivation**: Performance regressions are currently caught manually or in production. Automated detection prevents slow-downs from reaching users.
**Estimated Effort**: 8 days
**Impact Score**: 7/10
**Risk Reduction Score**: 7/10
**Dependencies**: Performance baseline established
**Acceptance Criteria**: Harness measures and records p50/p95/p99 for 10 key endpoints; CI compares PR vs baseline; warning on >20% regression; fail on >50% regression
**Suggested Assignee**: Platform Engineering

### ST-004: Implement circuit breaker admin API

**Title**: Manual circuit breaker control endpoint
**Description**: Add `GET /admin/circuit-breaker` (status) and `POST /admin/circuit-breaker` (set state) endpoints protected by admin JWT. Allow operators to manually open/close reset circuit breakers.
**Motivation**: During incidents, operators need to manually control circuit breakers without restarting the process. Currently only automatic behavior is available.
**Estimated Effort**: 3 days
**Impact Score**: 6/10
**Risk Reduction Score**: 8/10
**Dependencies**: RBAC for admin endpoint
**Acceptance Criteria**: GET returns current state of all circuit breakers; POST accepts state/reset commands; admin JWT required; audit logged
**Suggested Assignee**: Platform Engineering

### ST-005: Add clinical safety E2E test suite

**Title**: End-to-end tests for critical clinical workflows
**Description**: Write end-to-end tests covering the complete clinical workflow: patient registration -> order creation -> sample collection -> result entry -> result validation -> result release -> critical alert. Test with realistic data and verify audit trail at each step.
**Motivation**: Patient safety is non-negotiable. Current testing covers components but not the full workflow end-to-end. Integration gaps cause incidents.
**Estimated Effort**: 8 days
**Impact Score**: 9/10
**Risk Reduction Score**: 9/10
**Dependencies**: Test data fixtures, test database
**Acceptance Criteria**: E2E test covers full clinical workflow; verifies audit log entries at each step; runs in CI on every PR; < 2 minutes execution
**Suggested Assignee**: Quality Engineering Lead

### ST-006: Implement outbox pattern monitoring

**Title**: Monitor outbox_events processing health
**Description**: Add monitoring for the outbox event system: queue depth, processing latency, failure rate, retry count. Add alerts for queue backlog or sustained failures.
**Motivation**: The outbox pattern (`backend/app/services/outbox_service.py`) is critical for guaranteed event delivery. Undetected failures cause missed notifications, audit gaps, and integration failures.
**Estimated Effort**: 3 days
**Impact Score**: 7/10
**Risk Reduction Score**: 8/10
**Dependencies**: Prometheus metrics infrastructure
**Acceptance Criteria**: Metrics for queue depth, processing latency, error rate, retry count; alerts for queue depth > 1000 or error rate > 5%; Grafana dashboard
**Suggested Assignee**: Platform Engineering

### ST-007: Add audit log data retention policy

**Title**: Implement audit log archival and cleanup
**Description**: Create a retention policy for audit logs (default: 7 years for healthcare compliance). Implement archival to cold storage (S3/object store) and cleanup of archived data from main table. Must be configurable and default to off.
**Motivation**: Audit logs grow unbounded, slowing queries and increasing storage costs. Healthcare regulations require retention but not necessarily in the primary database.
**Estimated Effort**: 5 days
**Impact Score**: 6/10
**Risk Reduction Score**: 5/10
**Dependencies**: Object storage access
**Acceptance Criteria**: Configurable retention period; automated archival job; cleanup removes archived rows; audit chain integrity maintained across archive
**Suggested Assignee**: Backend Team Lead

### ST-008: Implement request tracing across services

**Title**: Add correlation ID propagation to downstream calls
**Description**: Ensure `X-Request-ID` is propagated from API gateway -> backend -> outbox events -> device bridge -> any external API calls. Add tracing context to all async task executions.
**Motivation**: Debugging distributed issues currently requires manual correlation. End-to-end tracing reduces incident mean-time-to-resolution by 40-60%.
**Estimated Effort**: 5 days
**Impact Score**: 6/10
**Risk Reduction Score**: 6/10
**Dependencies**: RequestIDMiddleware already implemented
**Acceptance Criteria**: X-Request-ID propagated to all downstream calls; logged in outbox event processing; visible in device bridge calls; visible in external API call logs
**Suggested Assignee**: Platform Engineering

### ST-009: Add device bridge protocol abstraction layer

**Title**: Refactor device bridge for protocol plugin architecture
**Description**: Create `ProtocolAdapter` base class with abstract methods for connect, disconnect, parse, send. Refactor existing ASTM/HL7 parser into adapter. Document adapter interface for third-party development.
**Motivation**: Enables future protocol support (DICOM, LIS2-A) without rewriting the bridge. Reduces coupling between transport, parsing, and business logic layers.
**Estimated Effort**: 10 days
**Impact Score**: 5/10
**Risk Reduction Score**: 4/10
**Dependencies**: None
**Acceptance Criteria**: ProtocolAdapter base class defined; ASTM adapter implements interface; HL7 adapter implements interface; existing functionality unchanged; adapter documentation written
**Suggested Assignee**: Device Bridge Team Lead

### ST-010: Implement rate limit by endpoint category

**Title**: Differentiated rate limiting per endpoint type
**Description**: Configure rate limits based on endpoint sensitivity: auth endpoints (5 req/min), CRUD endpoints (100 req/min), read endpoints (500 req/min), health endpoints (1000 req/min). Use Redis-backed rate limiter.
**Motivation**: Current rate limiting treats all endpoints uniformly. Differentiated limits provide better protection for sensitive endpoints while allowing higher throughput for safe operations.
**Estimated Effort**: 3 days
**Impact Score**: 6/10
**Risk Reduction Score**: 7/10
**Dependencies**: Redis rate limiting infrastructure
**Acceptance Criteria**: Rate limits configurable per endpoint group; auth endpoints limited to 5/min; CRUD to 100/min; health to 1000/min; Redis-backed counter; proper rate limit headers in response
**Suggested Assignee**: Security Team Lead

---

## Medium-Term (1-3 months, 10 items)

### MT-001: Implement predictive adaptive concurrency

**Title**: Proactive concurrency management with ML-based prediction
**Description**: Replace reactive concurrency halving with predictive model using moving average of response times, request queue depth, and DB connection pool utilization. Gradually adjust concurrency before thresholds are hit.
**Motivation**: Reactive concurrency causes oscillation and unnecessary quality degradation. Predictive model maintains throughput while protecting DB.
**Estimated Effort**: 10 days
**Impact Score**: 7/10
**Risk Reduction Score**: 6/10
**Dependencies**: Current adaptive concurrency (TD-004)
**Acceptance Criteria**: Predictive model implemented; no oscillation during load tests; throughput maintained within 10% of optimal; metrics for prediction accuracy; graceful fallback to reactive mode
**Suggested Assignee**: Platform Engineering

### MT-002: Complete SNDHS Phase 1 integration tests

**Title**: Full test coverage for SNDHS-lite features
**Description**: Write comprehensive tests for SNDHS Phase 1 features: visit tracking, national ID handling, enhanced audit log v2, visit_id on orders. Test with SNDHS flag on and off. Test backfill scenarios.
**Motivation**: SNDHS features touch patient data and audit trail — the most sensitive parts of the system. Insufficient testing risks data integrity.
**Estimated Effort**: 10 days
**Impact Score**: 8/10
**Risk Reduction Score**: 9/10
**Dependencies**: SNDHS Phase 1 migrations applied
**Acceptance Criteria**: Tests for all SNDHS routes and models; flag toggling tests (enabled/disabled); backfill scenario tests; run in CI with SNDHS flags enabled
**Suggested Assignee**: Quality Engineering Lead

### MT-003: Implement property-based testing for domain logic

**Title**: Hypothesis-based testing for clinical calculations and state machines
**Description**: Add property-based tests using the Hypothesis library for critical domain logic: order state machine transitions, critical value calculations, reference range lookups, barcode generation algorithms.
**Motivation**: Example-based tests miss edge cases. Property-based tests explore the input space automatically and find bugs that manual test cases wouldn't discover.
**Estimated Effort**: 8 days
**Impact Score**: 7/10
**Risk Reduction Score**: 8/10
**Dependencies**: Hypothesis library install
**Acceptance Criteria**: Property-based tests for order state machine, critical value detection, reference range logic; > 1000 generated examples per test; no failures
**Suggested Assignee**: Quality Engineering Lead

### MT-004: Add performance budget for CI/CD

**Title**: Enforce latency budgets in deployment pipeline
**Description**: Integrate performance benchmarking into CI/CD. After staging deployment, run load tests, measure p95 latency, compare against budget. Block deployment if budget exceeded. Store historical data for trend analysis.
**Motivation**: Performance regressions must be caught before production. Current manual checks are insufficient for rapid release cadence.
**Estimated Effort**: 8 days
**Impact Score**: 7/10
**Risk Reduction Score**: 7/10
**Dependencies**: Performance regression test harness (ST-003)
**Acceptance Criteria**: CI runs performance benchmark after staging deploy; p95 latency measured for key endpoints; failure if budget exceeded; historical trend chart visible
**Suggested Assignee**: Platform Engineering

### MT-005: Implement RBAC audit dashboard

**Title**: Role and permission usage analytics
**Description**: Create a dashboard showing role assignment distribution, permission usage frequency, recently granted elevated privileges, and unused permission grants. Expose via admin API.
**Motivation**: RBAC drift is a security risk. Stale permissions, over-privileged roles, and unused access accumulate over time. Regular auditing prevents privilege creep.
**Estimated Effort**: 5 days
**Impact Score**: 6/10
**Risk Reduction Score**: 8/10
**Dependencies**: Audit log infrastructure
**Acceptance Criteria**: Dashboard shows role distribution, permission usage heatmap, stale privilege report; admin API for programmatic access; weekly report generated
**Suggested Assignee**: Security Team Lead

### MT-006: Implement database connection pool health monitoring

**Title**: Real-time DB pool utilization dashboard
**Description**: Add Prometheus metrics for database connection pool: active/idle/overflow connections, wait time, acquired/released rates. Add alerts for pool exhaustion, high wait times, connection leaks.
**Motivation**: Connection pool exhaustion is a common production issue. Real-time monitoring enables proactive intervention before users are impacted.
**Estimated Effort**: 4 days
**Impact Score**: 7/10
**Risk Reduction Score**: 8/10
**Dependencies**: Prometheus metrics infrastructure
**Acceptance Criteria**: Metrics for pool size, active/idle/overflow connections, connection wait time; alerts at 80%/90%/100% pool utilization; Grafana dashboard
**Suggested Assignee**: Platform Engineering

### MT-007: Add chaos engineering for circuit breaker scenarios

**Title**: Automated chaos tests for self-healing mechanisms
**Description**: Write chaos tests that simulate DB failures, Redis failures, network partitions, and slow queries. Verify circuit breaker opens correctly, degraded mode engages, and recovery completes within expected time.
**Motivation**: Self-healing mechanisms must be tested under controlled conditions. Chaos tests prove they work before production failures require them.
**Estimated Effort**: 8 days
**Impact Score**: 8/10
**Risk Reduction Score**: 9/10
**Dependencies**: Chaos test infrastructure (tests/chaos/)
**Acceptance Criteria**: Chaos tests for DB failure, Redis failure, slow query, network partition; circuit breaker opens within expected time; degraded mode engages; recovery completes; tests run in CI weekly
**Suggested Assignee**: Platform Engineering

### MT-008: Implement device bridge health monitoring

**Title**: Lab instrument integration health dashboard
**Description**: Add health monitoring for device bridge connections: connection status per instrument, message throughput, error rate, last successful communication. Alert on disconnection or sustained errors.
**Motivation**: Lab instrument connectivity is critical for lab operations. Unmonitored connection failures delay patient results.
**Estimated Effort**: 5 days
**Impact Score**: 7/10
**Risk Reduction Score**: 8/10
**Dependencies**: Device bridge in production
**Acceptance Criteria**: Dashboard shows per-instrument status, throughput, error rate; alerts on disconnection; message latency tracked; daily health report
**Suggested Assignee**: Device Bridge Team Lead

### MT-009: Implement feature flag deprecation process

**Title**: Feature flag lifecycle management
**Description**: Create process and tooling for feature flag deprecation: tracking flag age, usage metrics, code references. Automatically flag flags older than 6 months for cleanup. Enforce removal after 12 months.
**Motivation**: Stale feature flags accumulate as dead code paths, increasing complexity and test burden. Regular cleanup reduces cognitive load.
**Estimated Effort**: 4 days
**Impact Score**: 5/10
**Risk Reduction Score**: 4/10
**Dependencies**: Feature flag infrastructure
**Acceptance Criteria**: Flag inventory with age, usage metrics, code references; quarterly report of stale flags; automated flag cleanup reminders
**Suggested Assignee**: Backend Team Lead

### MT-010: Add localization testing framework

**Title**: Automated RTL and i18n testing for frontend
**Description**: Implement automated tests for Arabic localization: verify RTL layout, check for untranslated strings, validate number/date formatting. Integrate with Playwright or Cypress for visual regression testing.
**Motivation**: Arabic-first platform requires rigorous localization testing. Manual testing is insufficient as the frontend grows.
**Estimated Effort**: 10 days
**Impact Score**: 8/10
**Risk Reduction Score**: 7/10
**Dependencies**: Frontend E2E test framework
**Acceptance Criteria**: Automated RTL layout tests for all pages; untranslated string detection in CI; number/date format validation; visual regression comparison for Arabic vs English
**Suggested Assignee**: Product Engineering Lead

---

## Long-Term (3-12 months, 10 items)

### LT-001: Frontend consolidation

**Title**: Merge 3 frontends into unified architecture
**Description**: Consolidate `frontend/` (static PWA), `frontend-v2/` (React + Firebase), and `client/` (tRPC + React) into a single frontend application with consistent architecture, shared components, and unified deployment.
**Motivation**: Frontend fragmentation (TD-007) is the largest single source of technical debt. Consolidation reduces maintenance by 3x and ensures consistent UX.
**Estimated Effort**: 40 days
**Impact Score**: 7/10
**Risk Reduction Score**: 5/10
**Dependencies**: Frontend architecture decision, team availability
**Acceptance Criteria**: Single frontend application; all features from 3 existing frontends migrated; consistent UX patterns; unified deployment pipeline; old frontends decommissioned
**Suggested Assignee**: Product Engineering Lead

### LT-002: Implement database partitioning for audit_logs

**Title**: Partition audit_logs table by month
**Description**: Implement PostgreSQL partitioning for the `audit_logs` table by month. Create partition management automation (auto-create new partitions, detach old ones for archival). Migrate existing data.
**Motivation**: Audit logs will grow to millions of rows, causing slow queries and maintenance challenges. Partitioning by month enables efficient query pruning and data lifecycle management.
**Estimated Effort**: 12 days
**Impact Score**: 7/10
**Risk Reduction Score**: 6/10
**Dependencies**: Migration policy compliance
**Acceptance Criteria**: audit_logs partitioned by month; partition creation automated via cron/trigger; queries show partition pruning in EXPLAIN; migration of existing data complete; detach/archive procedure documented
**Suggested Assignee**: Backend Team Lead

### LT-003: Implement DICOM protocol support in device bridge

**Title**: Add DICOM medical imaging protocol support
**Description**: Implement DICOM protocol adapter for the device bridge. Support DICOM message reception, parsing, and forwarding to lab results pipeline. Add DICOM-specific test fixtures and simulator.
**Motivation**: Imaging and pathology labs use DICOM, not ASTM/HL7. Adding DICOM support expands the addressable lab market and provides a complete diagnostic data platform.
**Estimated Effort**: 20 days
**Impact Score**: 6/10
**Risk Reduction Score**: 3/10
**Dependencies**: Protocol abstraction layer (ST-009)
**Acceptance Criteria**: DICOM adapter implemented; supports SOP classes for lab results; end-to-end test with DICOM simulator; integration with lab results pipeline; DICOM-specific monitoring
**Suggested Assignee**: Device Bridge Team Lead

### LT-004: Implement blue-green deployment automation

**Title**: Fully automated zero-downtime deployments
**Description**: Complete the blue-green deployment workflow (`.github/workflows/blue-green-deploy.yml`) with automated traffic switching, health verification, canary analysis, and rollback on failure.
**Motivation**: Production deployments currently have a downtime window. Zero-downtime deployment enables faster release cadence and reduces deployment risk.
**Estimated Effort**: 15 days
**Impact Score**: 8/10
**Risk Reduction Score**: 8/10
**Dependencies**: Infrastructure automation
**Acceptance Criteria**: Zero-downtime deployment; automated blue-green switch; health verification before cutover; automated rollback on failure; deployment duration < 5 minutes
**Suggested Assignee**: Platform Engineering

### LT-005: Implement self-healing auto-repair for all components

**Title**: Extend auto-repair engine to cover caches, connections, and queues
**Description**: Expand the auto-repair engine (`backend/app/core/auto_repair.py`) beyond GC and pool recycle to include: Redis cache repair, connection pool drain detection, queue backlog recovery, and disk space management.
**Motivation**: Self-healing reduces on-call burden and improves platform reliability. Current engine only handles memory and DB connection recycling.
**Estimated Effort**: 15 days
**Impact Score**: 7/10
**Risk Reduction Score**: 8/10
**Dependencies**: Circuit breaker infrastructure
**Acceptance Criteria**: Auto-repair covers Redis (flush stuck keys, reconnect), connection pools (drain stale connections), queues (recover stuck events), disk (log rotation); all with circuit breaker coordination; metrics for repair actions
**Suggested Assignee**: Platform Engineering

### LT-006: API versioning strategy implementation

**Title**: Implement URL-based or header-based API versioning
**Description**: Design and implement API versioning strategy: choose between URL prefix (`/v1/`, `/v2/`), header (`Accept: application/vnd.gula.v2+json`), or query parameter. Implement backward compatibility layer for deprecated versions.
**Motivation**: Without versioning, breaking API changes are impossible without breaking existing clients. Versioning enables continuous API evolution.
**Estimated Effort**: 15 days
**Impact Score**: 6/10
**Risk Reduction Score**: 7/10
**Dependencies**: ADR on versioning strategy
**Acceptance Criteria**: Versioning strategy documented in ADR; versioned routes returning correct responses; version migration guide; deprecation policy; sunset process for old versions
**Suggested Assignee**: Backend Team Lead

### LT-007: Implement SNDHS Phase 2 readiness

**Title**: Prepare architecture for SNDHS Phase 2 requirements
**Description**: Based on SNDHS Phase 2 spec (not yet available), prepare the architecture for enhanced reporting, population health analytics, and cross-lab data aggregation. Likely requires data warehouse layer, analytics pipeline, and de-identification service.
**Motivation**: SNDHS expansion is a strategic priority. Early architectural preparation prevents rushed implementation when Phase 2 requirements are finalized.
**Estimated Effort**: 20 days (research + design)
**Impact Score**: 8/10
**Risk Reduction Score**: 5/10
**Dependencies**: SNDHS Phase 2 requirements document
**Acceptance Criteria**: Architecture design document; PoC for data warehouse pipeline; de-identification service prototype; ADR for analytics architecture
**Suggested Assignee**: Platform Engineering

### LT-008: Implement backup and disaster recovery automation

**Title**: Automated DR testing and recovery procedures
**Description**: Implement automated backup verification, restore testing, and disaster recovery drills. Define RPO/RTO targets, document recovery runbooks, automate recovery procedures where possible.
**Motivation**: Platform has `make backup` but no automated restore testing or DR drills. Undocumented recovery procedures cause extended downtime during real incidents.
**Estimated Effort**: 12 days
**Impact Score**: 8/10
**Risk Reduction Score**: 9/10
**Dependencies**: Infrastructure access
**Acceptance Criteria**: Documented RPO/RTO targets; automated backup verification (restore to test environment); quarterly DR drill with automated execution; recovery runbook documented; recovery time measured against targets
**Suggested Assignee**: Platform Engineering

### LT-009: Implement OTel-based distributed tracing

**Title**: Replace custom tracing with OpenTelemetry
**Description**: Integrate OpenTelemetry SDK for distributed tracing across all services. Replace custom `X-Request-ID` propagation with OTel context propagation. Export traces to Tempo or Jaeger.
**Motivation**: Custom tracing is limited in scope and integration capability. OTel provides standardized instrumentation, vendor-neutrality, and rich visualization.
**Estimated Effort**: 15 days
**Impact Score**: 6/10
**Risk Reduction Score**: 6/10
**Dependencies**: Observability infrastructure
**Acceptance Criteria**: OTel SDK integrated; traces captured for all API endpoints; context propagation to async tasks and downstream calls; traces visible in Jaeger/Tempo; no regression in request processing time
**Suggested Assignee**: Platform Engineering

### LT-010: Implement comprehensive security threat model

**Title**: Formal security threat modeling for all subsystems
**Description**: Conduct formal threat modeling using STRIDE methodology for each major subsystem: API gateway, backend, database, Redis, device bridge, frontend, SNDHS integration. Document threats, mitigations, and residual risks.
**Motivation**: Security is currently reactive (pentests, CVE scans). Proactive threat modeling identifies design-level vulnerabilities before they're exploited.
**Estimated Effort**: 10 days (analysis + documentation)
**Impact Score**: 8/10
**Risk Reduction Score**: 9/10
**Dependencies**: Security expertise
**Acceptance Criteria**: STRIDE analysis for each subsystem; threat register with mitigations; residual risk acceptance documentation; integration with security review process; annual threat model update cadence
**Suggested Assignee**: Security Team Lead

---

## Strategic (1+ years, 5 items)

### SG-001: Full microservice decomposition

**Title**: Decompose monolith into production microservices
**Description**: Extract business domains from the monolith into independent services: lab management, order processing, results management, patient management, notification, AI. Implement event-driven communication via message broker. Maintain backward compatibility during transition.
**Motivation**: Monolith is the current source of truth and will eventually limit scalability and team autonomy. Strategic decomposition aligns with the existing services/ directory structure.
**Estimated Effort**: 120 days (phased over 12 months)
**Impact Score**: 9/10
**Risk Reduction Score**: 6/10
**Dependencies**: All medium-term items, team growth, organizational readiness
**Acceptance Criteria**: First domain extracted and running independently; event-driven communication established; monolith delegates to microservice; no regression in API behavior; team ownership per service
**Suggested Assignee**: Platform Engineering + multiple teams

### SG-002: Financial Engine Phase B+ implementation

**Title**: Full financial engine with billing, invoicing, and payment processing
**Description**: Build on Financial Engine Phase A schema to implement complete financial features: lab billing, patient invoicing, insurance claims, payment processing, fraud detection, and financial reporting.
**Motivation**: Financial features are a key revenue driver for the platform. Phase A schema exists but cannot be activated without business logic.
**Estimated Effort**: 80 days
**Impact Score**: 9/10
**Risk Reduction Score**: 4/10
**Dependencies**: Financial Phase A schema, product requirements, regulatory approval
**Acceptance Criteria**: Billing engine implemented; invoice generation and delivery; payment gateway integration; insurance claim submission; fraud detection system; financial reporting dashboard
**Suggested Assignee**: Product Engineering Lead

### SG-003: AI-powered clinical decision support

**Title**: ML-assisted diagnosis suggestions and anomaly detection
**Description**: Build on `ai/` and `backend/app/ai/` foundations to implement: AI-assisted diagnosis suggestions based on lab results, anomaly detection in test patterns, predictive flagging for disease risk, and recommendation engine for follow-up tests.
**Motivation**: AI features differentiate the platform and provide clinical value beyond basic LIMS functionality. Predictive analytics can improve patient outcomes.
**Estimated Effort**: 100 days
**Impact Score**: 9/10
**Risk Reduction Score**: 7/10
**Dependencies**: ML infrastructure, clinical validation partners
**Acceptance Criteria**: AI diagnosis suggestions for top 20 test panels; anomaly detection in historical results; risk prediction for 5 conditions; clinician feedback loop; explainable AI (why suggestion was made)
**Suggested Assignee**: ML/AI Team Lead

### SG-004: National-scale health data exchange

**Title**: Interoperability with Ministry of Health and national health systems
**Description**: Implement full health data exchange standards: FHIR R4 APIs, national patient index integration, immunization registry, disease surveillance reporting, and Ministry of Health dashboard integration.
**Motivation**: National-scale interoperability is a long-term strategic goal and aligns with SNDHS roadmap. Enables GULA as the national lab data backbone.
**Estimated Effort**: 150 days
**Impact Score**: 10/10
**Risk Reduction Score**: 6/10
**Dependencies**: SNDHS Phase 2, government partnerships, FHIR capability
**Acceptance Criteria**: FHIR R4 API for patient, observation, and diagnostic report resources; Ministry of Health data exchange integration; disease surveillance automated reporting; national patient index matching
**Suggested Assignee**: Platform Engineering + Government Relations

### SG-005: Multi-region disaster recovery

**Title**: Active-active multi-region deployment
**Description**: Implement active-active deployment across two geographic regions (e.g., Baghdad + Erbil) with real-time database replication, global load balancing, and automatic failover. Target RPO < 1 minute, RTO < 5 minutes.
**Motivation**: National-scale clinical platform requires regional disaster tolerance. Single-region deployment is a single point of failure for critical healthcare infrastructure.
**Estimated Effort**: 90 days
**Impact Score**: 9/10
**Risk Reduction Score**: 10/10
**Dependencies**: Infrastructure automation, database replication capability, network connectivity between regions
**Acceptance Criteria**: Active-active deployment in 2 regions; sub-1-minute RPO; sub-5-minute RTO; automated failover testing monthly; cross-region latency < 20ms; data consistency verified after failover
**Suggested Assignee**: Platform Engineering + Infrastructure

---

## Backlog Management

### Prioritization Formula

```
Priority Score = (Impact × 2) + (Risk_Reduction × 1.5) + (Strategic_Alignment × 1) - (Effort_Days × 0.1)
```

### Priority Buckets

| Bucket | Timeframe | Total Effort | Items |
|--------|-----------|-------------|-------|
| Quick Wins | 1-2 days | 6.5 days | 10 |
| Short-Term | 1-2 weeks | 57 days | 10 |
| Medium-Term | 1-3 months | 72 days | 10 |
| Long-Term | 3-12 months | 164 days | 10 |
| Strategic | 1+ years | 540 days | 5 |
| **Total** | | **~320 days (active) + 540 days (strategic)** | **45** |

### Review Process

- **Weekly**: Top 5 quick wins and short-term items reviewed in standup
- **Monthly**: Sprint planning picks from top of backlog; update estimates
- **Quarterly**: Full backlog grooming; reprioritize based on product direction
- **Per-release**: Items that align with release scope pulled into sprint

### Definition of Ready

An improvement item is ready for sprint planning when:
1. Clear acceptance criteria
2. Effort estimated (within ±25%)
3. Dependencies identified and resolved
4. Assignee identified
5. Stakeholder validation (if user-facing)

### Definition of Done

An improvement item is complete when:
1. All acceptance criteria met
2. Code changes reviewed and merged
3. Tests written and passing
4. Documentation updated
5. Technical debt register updated (if relevant)
6. Stakeholder acceptance (if user-facing)

---

*This backlog is maintained by Platform Engineering. Monthly grooming required.*

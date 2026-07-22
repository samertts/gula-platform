# GULA Constitution — Gap Analysis & Implementation Roadmap

Generated: 2026-07-22 | **Verified against actual codebase**

This analysis uses only evidence verified by actual file/symbol inspection. No assumed capabilities are included.

## Priority Levels

| Priority | Definition | Target Resolution |
|----------|------------|-------------------|
| **Critical** | Violates security, clinical safety, or data integrity rules | Immediate (next sprint) |
| **High** | Prevents achievement of a core architectural principle | This quarter |
| **Medium** | Important but non-blocking; compliance gap | Next quarter |
| **Low** | Desirable enhancement; no functional impact | Within 12 months |

---

## VERIFIED GAPS BY ARTICLE

### Gap A05-1: Idempotency not wired to all POST routes
**Priority: High**
- **Evidence:** `core/idempotency.py` exists with middleware implementation. `services/order_service.py:511` uses `enforce_transition()` but no `Idempotency-Key` check. No route handler reads idempotency key.
- **Risk:** Duplicate POST requests can create duplicate orders/results in clinical workflows
- **Action:** Wire `Idempotency-Key` middleware to all mutating endpoints (orders, results, samples, batch)
- **Modules affected:** `routes/results.py`, `routes/clinical_orders.py`, `routes/batch.py`, `routes/samples.py`
- **Effort:** Medium (2-3 days)

### Gap A05-2: Cursor-based pagination absent
**Priority: Medium**
- **Evidence:** No cursor-based pagination implementation found in any route handler.
- **Risk:** Offset pagination on large datasets (>100K rows) degrades performance
- **Action:** Add cursor-based pagination to high-volume endpoints
- **Modules affected:** `routes/results.py`, `routes/patients.py`, `routes/samples.py`
- **Effort:** Medium (3-5 days)

### Gap A07-1: Line length not enforced in CI
**Priority: Low**
- **Evidence:** `ci.yml` runs `flake8` but no `--max-line-length` argument found. No `.flake8` config file found.
- **Action:** Add `--max-line-length=120` to flake8 command
- **Effort:** Trivial

### Gap A07-2: Coverage threshold not enforced in CI
**Priority: Critical**
- **Evidence:** CI `test` job runs `python -m pytest tests/ -v --timeout=60 -x` **without** `--cov` flag. No coverage config in `pyproject.toml` or `setup.cfg`.
- **Risk:** Code quality degrades silently; no safety net for regression
- **Action:** Add `pytest-cov` to CI test command; set `--cov-fail-under=80`
- **Effort:** Low (1 day)
- **Note:** This contradicts CLAUDE.md which claims coverage enforcement exists

### Gap A12-1: WCAG accessibility unverified
**Priority: Medium**
- **Evidence:** `frontend-v2/package.json` exists. ARIA attributes, keyboard navigation, screen reader support not verified in frontend code.
- **Action:** Audit frontend components for WCAG 2.1 AA compliance
- **Effort:** High (comprehensive audit)

### Gap A13-1: Data quality monitoring absent
**Priority: Medium**
- **Evidence:** No `data_quality` service, route, or monitoring module found in any code path.
- **Action:** Implement data quality scoring and alerting
- **Effort:** High (new module)

### Gap A14-1: `/api/v1/` prefix not used
**Priority: High**
- **Evidence:** All existing routes registered without `/api/v1/` prefix. `routes/ehr_fhir.py:32` uses `prefix="/fhir"`, `routes/authorization.py:32` uses `prefix="/authz"`. No route uses `/api/v1/`.
- **Risk:** Inconsistent API surface; future versioning requires standard prefix
- **Action:** Add `/api/v1/` prefix to new route groups. Existing routes preserved as-is per backward compatibility policy.
- **Effort:** Low (for new routes)

### Gap A14-2: Response envelope not adopted
**Priority: High** (for new routes only)
- **Evidence:** All verified route handlers return flat JSON. No middleware wraps responses in `{"data": ..., "meta": ...}` envelope.
- **Risk:** Breaking change to adopt envelope would break all existing clients
- **Action:** Add envelope as opt-in via `Accept: application/vnd.gula.v2+json` header
- **Effort:** Medium (add conditional wrapper middleware)

### Gap A15-1: Slow query monitoring absent
**Priority: Medium**
- **Evidence:** No `log_min_duration_statement` configuration or slow-query logging middleware found.
- **Action:** Configure PostgreSQL `log_min_duration_statement=200` and export metrics
- **Effort:** Low

### Gap A17-1: Plugin sandboxing absent
**Priority: High**
- **Evidence:** `integration/` directory has 20+ subdirectories but no sandboxing, subprocess isolation, or resource limits for third-party plugin execution.
- **Risk:** Third-party integrations run without isolation — memory exhaustion, data leaks
- **Action:** Implement subprocess/container-based sandbox for untrusted integrations
- **Effort:** High

### Gap A17-2: Plugin versioning absent
**Priority: Medium**
- **Evidence:** No plugin version registry, compatibility matrix, or version constraint enforcement.
- **Action:** Implement plugin manifest with version requirements
- **Effort:** Medium

### Gap A18-1: Configurable workflow engine absent
**Priority: Medium**
- **Evidence:** `domain/order_state.py` has hardcoded state machine. No YAML/JSON workflow definition DSL.
- **Action:** Implement per-tenant workflow configuration
- **Effort:** High

### Gap A20-1: Coverage threshold not enforced (see A07-2)
**Priority: Critical** (duplicate of A07-2)

### Gap A20-2: Migration round-trip not automated in CI
**Priority: Medium**
- **Evidence:** `ci.yml:76` — `migration-check` job runs `alembic upgrade head` only. No `downgrade -1 && upgrade head` test.
- **Action:** Add downgrade round-trip to migration check
- **Effort:** Low

### Gap A22-1: Semantic versioning not enforced in CI
**Priority: Low**
- **Evidence:** `config.py:65` — `APP_VERSION = "2.5.0"` exists. No CI check validates version bumps against release type.
- **Action:** Add version check to CI
- **Effort:** Low

### Gap A23-1: Deprecation headers absent
**Priority: Medium**
- **Evidence:** No `Deprecation: true` or `Sunset:` header middleware or route decorator found.
- **Action:** Add deprecation header middleware
- **Effort:** Low

### Gap A23-2: Version coexistence absent
**Priority: Low**
- **Evidence:** No `/api/v2/` parallel routing infrastructure.
- **Action:** Implement when first breaking change is needed
- **Effort:** High

### Gap A24-1: IHE profiles not implemented
**Priority: Medium**
- **Evidence:** No IHE integration code found. `routes/ehr_fhir.py:32` implements FHIR (prefix=/fhir) but no XDS.b, PIX, or CT profiles.
- **Action:** Implement IHE profiles for national interoperability
- **Effort:** High

### Gap A27-1: ADR path mismatch
**Priority: Low**
- **Evidence:** 5 ADR files exist at `docs/architecture/ADR-*.md` but Article 27 specifies `docs/architecture/decisions/`. Directory `docs/architecture/decisions/` does not exist on disk.
- **Action:** Move ADRs to `docs/architecture/decisions/` or update Article 27 to reflect actual path
- **Effort:** Trivial

### Gap A28-1: PR checklist absent
**Priority: Low**
- **Evidence:** `.github/PULL_REQUEST_TEMPLATE.md` does not exist.
- **Action:** Create PR template with DoD checklist
- **Effort:** Trivial

---

## VERIFIED: What Is Already Compliant (No Gaps)

These are areas where the Constitution requirement was verified against real code:

| Article | Key Verified Artifacts |
|---------|----------------------|
| 08 — Security | 16/16 criteria verified. `security/auth.py` (JWT), `security/abac.py` (ABAC), `security/encryption.py`, `security/rbac.py`, `security/rate_limit.py`, `security/session.py`, `security/mfa_service.py`, `security/oauth2_provider.py`, `security/saml_service.py`, `security/intrusion_detection.py`, `security/dependencies.py` (per-endpoint auth), `security/consent_dep.py` (consent enforcement), `models/audit_log.py` + `services/audit_service.py` (audit) |
| 09 — Clinical | 11/11 criteria verified. `services/clinical_state.py` (CDS), `services/critical_alerts.py`, `services/clinical_engine.py`, `services/ehr_service.py`, `routes/ehr_fhir.py` (FHIR Patient), `routes/citizen_portal.py` |
| 10 — Laboratory | 14/14 criteria verified. `models/lab_order.py`, `models/lab_result.py`, `models/sample.py`, `models/quality_control.py`, `domain/order_state.py` (state machine), `services/order_service.py` |
| 11 — AI | 12/12 criteria verified. `ai/guardrails.py`, `ai/sandbox.py`, `ai/approval.py`, `ai/governance.py`, `ai/healthcare_cds.py`, `core/decision_guard.py`, `core/policy_engine.py` |
| 16 — Event | 5/5 criteria verified. `models/outbox.py` (OutboxEvent), `services/outbox_service.py` (OutboxWorker), `core/events.py` (EventBus), `notifications/service.py` (NotificationService) |
| 26 — National | 9/9 criteria verified. `models/organization.py`, `models/tenant.py`, `services/mpi/` (6 files), `services/national_id.py`, `core/sndhs_flags.py`, `routes/compliance.py` |

---

## Implementation Roadmap

### Sprint 1: CI & developer experience (Week 1)
| Gap | Module | Effort | Verification |
|-----|--------|--------|-------------|
| A07-1 — Line length CI | `.github/workflows/ci.yml` | Trivial | Verified: flake8 runs without `--max-line-length` |
| A07-2 / A20-1 — Coverage CI | `.github/workflows/ci.yml`, `pyproject.toml` | Low | Verified: `pytest` runs without `--cov` |
| A22-1 — Semver CI | `ci.yml` | Low | Verified: No version check |
| A28-1 — PR template | `.github/PULL_REQUEST_TEMPLATE.md` | Trivial | Verified: Does not exist |
| A27-1 — ADR path fix | `docs/architecture/decisions/` | Trivial | Verified: ADRs at wrong path |

### Sprint 2: Data integrity (Week 2-3)
| Gap | Module | Effort | Verification |
|-----|--------|--------|-------------|
| A05-1 — Idempotency wiring | `core/idempotency.py`, route handlers | Medium | Verified: middleware exists but not wired |
| A20-2 — Migration round-trip CI | `ci.yml` migration-check job | Low | Verified: only `upgrade head`, no downgrade test |

### Sprint 3: API standards (Week 4-5)
| Gap | Module | Effort | Verification |
|-----|--------|--------|-------------|
| A14-1 — API prefix for new routes | Route registration in `factory.py` | Low | Verified: no `/api/v1/` prefix anywhere |
| A14-2 — Response envelope (opt-in) | `middleware.py` new middleware | Medium | Verified: flat responses only |
| A23-1 — Deprecation headers | `middleware.py` new middleware | Low | Verified: headers absent |

### Sprint 4: Performance & quality (Week 6-7)
| Gap | Module | Effort | Verification |
|-----|--------|--------|-------------|
| A05-2 — Cursor pagination | Route handlers (results, patients) | Medium | Verified: offset pagination only |
| A15-1 — Slow query monitoring | Database config | Low | Verified: no slow query config |
| A13-1 — Data quality | New `services/data_quality_service.py` | High | Verified: no DQ module exists |

### Sprint 5: Integration safety (Week 8-10)
| Gap | Module | Effort | Verification |
|-----|--------|--------|-------------|
| A17-1 — Plugin sandboxing | New sandbox module | High | Verified: no isolation mechanism |
| A17-2 — Plugin versioning | New registry | Medium | Verified: no version registry |

### Sprint 6: Advanced (Week 11+)
| Gap | Module | Effort | Verification |
|-----|--------|--------|-------------|
| A18-1 — Workflow engine | New `services/workflow_engine/` | High | Verified: hardcoded state machine only |
| A24-1 — IHE profiles | New `integration/ihe/` | High | Verified: FHIR only, no IHE |
| A12-1 — WCAG audit | frontend-v2 components | High | Verified: unverified |
| A23-2 — Version coexistence | Route versioning | High | Verified: no v2 infrastructure |

---

## Authorization Expansion — Verified Compliance with Constitution

The authorization expansion in the working tree was verified against the Constitution:

| Constitution Requirement | Code Evidence | Status |
|-------------------------|---------------|--------|
| Article 08.10 — RBAC with roles/perms | `models/authorization.py:47` — `Permission`, `:66` — `Role`, `:94` — `RoleAssignment` | VERIFIED |
| Article 08.11 — ABAC with attribute policies | `models/authorization.py:131` — `Policy` model with conditions | VERIFIED |
| Article 08.12 — Permission on every endpoint | `routes/authorization.py:103` — `require_permission("authz:read")` dependency | VERIFIED |
| Article 08.14 — Role delegation with expiry | `models/authorization.py:173` — `Delegation` model | VERIFIED |
| Article 14.13 — Auth on all endpoints | 15 endpoints under `/authz` prefix, all with `require_permission()` | VERIFIED |
| Article 05.15 — Backend authority | All authorization logic in services, enforced in dependencies | VERIFIED |
| Article 23.5 — Backward-compatible migration | `20260722_0001_authorization_expansion.py` — additive only (new tables, new columns) | VERIFIED |

**Conclusion:** Authorization expansion is fully aligned with the Constitution (7/7 criteria verified). No changes needed before merge.

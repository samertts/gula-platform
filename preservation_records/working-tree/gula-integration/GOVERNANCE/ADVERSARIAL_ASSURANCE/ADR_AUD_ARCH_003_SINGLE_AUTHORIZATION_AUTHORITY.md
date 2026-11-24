# ADR — AUD-ARCH-003: Single Canonical Authorization Authority

**Status:** ENGINEERING REMEDIATION IMPLEMENTED + TESTED — **OWNER RATIFICATION PENDING** for any
production claim (`owner_gated: true`, identity/security owner; touches RBAC/ABAC and the Shared
Core canonical registry). No production-readiness claim is made by this ADR.

**Repository:** `/home/samertts/workspace/projects/gula-integration` (uncommitted; see program
commit-block note)
**Date:** 2026-11-18
**Finding:** `AUD-ARCH-003` (HIGH / MEDIUM) — "Two mutually exclusive 'only authority' permission
engines coexist (health_core vs NIAM/shared RBAC)".

---

## Context

Two authorization engines claimed exclusivity:

1. `backend/app/health_core/authorization/engine.py` — docstring "The engine is the only authority
   for permissions." Synchronous, deny-by-default, exact role→permission map + grants/revocations
   over opaque `SYN-` synthetic identifiers. Instantiated only inside the non-activated Health Core
   slice (`guard.py:869`), reached only from the synthetic FHIR HTTP test router.
2. `backend/app/identity/services/authorization_service.py` (+ decision engine
   `authorization_decision.py`) — the cataloged RBAC + ABAC + workspace-scoped authority in
   `app/domain_platform/shared_core.py`, used by the main application authorization path.

The auditor's falsification held: the two are independent code paths with independent role/permission
maps and no delegation. Current production exposure was limited (the synthetic engine is confined
to a non-activated surface), but the architecture was ambiguous and unsafe to extend.

## Decision

**One canonical authority:** `backend/app/identity/services/authorization_service.py` (decision
engine `identity/services/authorization_decision.py`). The Health Core engine is explicitly
re-scoped as **SYNTHETIC ONLY** — it is not a platform-wide authority and must never be extended to
real identities or production routes.

This follows the finding's recommended remediation (option: "explicitly rename/scope the docstring
to 'synthetic Health Core only' and add a contract test proving decision equivalence"), which is the
lowest-blast-radius option that resolves the false exclusivity claim without disturbing synthetic
evidence. Full retirement/delegation of the synthetic engine was rejected as a larger change to
non-activated evidence with no production benefit.

## Implemented changes (engineering scope)

| # | Change | File |
|---|---|---|
| 1 | Docstring re-scoped to SYNTHETIC ONLY; names the canonical authority and the equivalence test | `backend/app/health_core/authorization/engine.py` |
| 2 | Shared Core catalog `authorization` entry now names THE single canonical authority and marks health_core synthetic-only | `backend/app/domain_platform/shared_core.py` |
| 3 | New differential equivalence test: a 5-situation corpus is fed through real evaluations in BOTH engines; verdicts must match; plus a scope/catalog assertion | `backend/tests/health_core/test_authorization_synthetic_scope.py` (7 tests) |

### Equivalence corpus (shared semantic verdict)

| Situation | Health Core verdict | Canonical verdict | Expected |
|---|---|---|---|
| authenticated principal with required permission, in scope | ALLOW | allow | allow |
| unauthenticated / inactive actor | DENY | deny | deny |
| authenticated but permission missing | DENY | deny | deny |
| cross-tenant request | DENY | deny | deny |
| explicit revocation / deny policy | DENY | deny | deny |

The test pins the *decision contract* — deny-by-default, authentication grants nothing, tenant
isolation, and explicit revocation/deny-policy override. It is a deterministic differential test on
a curated corpus, not a formal proof of full semantic equivalence: reason codes and internal policy
language intentionally differ between the synthetic and production engines. Any divergence in
either direction fails the build.

## Verification

- `tests/health_core/test_authorization_synthetic_scope.py` — **7 passed**.
- Neighbor suites (health_core authorization + domain_platform shared-core) — see remediation
  register for the consolidated run.

## Consequences / residual risk

- **Residual drift risk:** a differential corpus cannot cover every possible input. New
  authorization semantics added to either engine must be added to the corpus. Mitigated by the
  `test_corpus_covers_allow_and_all_core_deny_boundaries` guard against a vacuous/shrunk corpus.
- **Owner ratification required:** this ADR changes the documented authority in the Shared Core
  registry. No production claim (e.g. marking AUD-ARCH-003 `PRODUCTION READY`) is made until the
  identity/security owner ratifies. Status remains `IMPLEMENTED / TESTED`, owner-gated.
- **Reversible:** the three changes are documentation, a catalog description, and an additive test;
  all are independently revertible with no schema/data impact.

## Decision owner signature

**PENDING** — identity/security owner. Ratification is required only to convert the engineering
remediation into a production assurance claim; the engineering change itself does not activate any
functionality or alter runtime behavior.

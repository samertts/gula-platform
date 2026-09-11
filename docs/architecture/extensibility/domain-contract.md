# Domain module contract

**PROGRAM-EXT-001, Phase 4.** Normative.

A domain is a clinical or business area — pharmacy, nursing, blood bank,
radiology, LIMS, EMS. A capability is reusable across domains; a domain is not
reusable and does not try to be.

## 1. What every domain must expose

| # | Obligation | Where it is satisfied |
| --- | --- | --- |
| 1 | **Identity** — one package, one name, one owner | `app/<domain>/` |
| 2 | **Ownership** — a named team for every table it writes | capability descriptor `owner` |
| 3 | **Lifecycle** — a declared maturity | descriptor `maturity` |
| 4 | **Dependencies** — declared, not discovered by import | descriptor `dependencies` |
| 5 | **Public API** — versioned routes under `/api/v1/...` | `app/routes/` or `app/<domain>/routes.py` |
| 6 | **Events** — canonical envelope, versioned name | `app/kernel/event_bus/events.py::Event` |
| 7 | **Authorization** — server-side, per request, never a feature flag | `app/identity/` |
| 8 | **Audit** — every mutation, hash-chained | `CanonicalAuditService` |
| 9 | **Tenant boundary** — every patient-data query filters `lab_id` / `tenant_id` | the domain's own services |
| 10 | **Migrations** — new revision, idempotent, additive, reversible | `backend/migrations/versions/` |
| 11 | **Tests** — against migrated PostgreSQL, not `create_all()` | `backend/tests/` |
| 12 | **Observability** — health contribution and structured logs | `app/core/logging_config.py` |
| 13 | **Documentation** — one page, linked from the descriptor | `docs/<domain>/` |

## 2. The one rule that matters most

**A domain must not depend on another domain's internal implementation.**

Permitted, in order of preference:

1. a **CORE contract** — the kernel, identity, the canonical audit writer;
2. an **API contract** — a versioned HTTP route;
3. an **event contract** — subscribe to a published, versioned event.

Not permitted: importing another domain's `models/`, `repositories/`,
`infrastructure/`, `application/` or `domain/` package, or reading its tables
directly.

The reason is not taste. A domain that reads another's ORM rows is coupled to
that domain's *migration schedule*: the moment the other team renames a column,
a domain they have never heard of breaks. GULA has already lived this — NR-047
was an ORM that named columns another model owned, and it cost a working
authorization path.

## 3. Where this rule stands today

Not satisfied. Twenty-five imports cross domain internals, along six edges,
measured and tabulated in `core-boundary.md` §3.

So the guard is a **ledger**, not a gate: the six edges are recorded with their
counts, and `test_no_new_cross_domain_internal_dependency_appears` fails when a
new edge appears or an existing one grows. Existing debt is frozen and visible;
new debt is blocked.

This is deliberate. A guard that fails on its first run gets deleted, and then
there is no guard at all. A ledger that is honest about 25 is worth more than a
gate that claims 0.

## 4. Adding a domain

1. Create `app/<domain>/` with `models/`, `services/`, `routes.py`.
2. Declare a `CapabilityDescriptor` per capability the domain publishes.
3. Publish events with the canonical envelope; never let another domain read
   your tables.
4. Add migrations as new revisions — never edit an existing one.
5. Write tests against migrated PostgreSQL.
6. Run `backend/tests/test_extensibility_guards.py`.

The template in `extension-template.md` is this list as a file layout.

## 5. What a domain may assume from Core

* `get_db` yields a synchronous `sqlalchemy.orm.Session`. There is one engine
  and one pool. Do not create a second; do not annotate `AsyncSession` (see
  `docs/architecture/identity/nr-044-decision.md` for what that cost).
* Authentication and authorization are Identity's, and only Identity's.
* Audit is `CanonicalAuditService`. Do not write a second hash chain.
* Tenancy is enforced by the domain's own queries. Core provides the context;
  it cannot filter on your behalf.

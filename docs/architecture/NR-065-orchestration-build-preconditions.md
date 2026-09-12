# NR-065 — the fifteen orchestration tables may not be built as declared

**Status:** BLOCKED ON REPAIR, not on product intent. No table built, no endpoint
withdrawn, no frontend changed.
**Method:** AST over the two packages + the committed `evidence-created-tables.json`.
No repository-wide rescan.

## 1. What Unit 3 was asked to prove

The approved NR-059 decision gates schema creation on five checks: *prove every
proposed physical table is genuinely required by reachable behaviour; confirm
canonical ownership; confirm tenancy; confirm audit; confirm state-machine
semantics; confirm idempotency and concurrency requirements.*

NR-059 left one question open — whether national task and workflow
orchestration is a feature GULA ships — and correctly recorded that it is
product intent, not derivable from the repository. **That question is still
open and this document does not answer it.** What Unit 3 establishes is that
it is no longer the only blocker.

## 2. The checks, measured

| Check | Result |
| --- | --- |
| Required by reachable behaviour | **Yes.** 40 registered endpoints and two `frontend-v3` pages reach these tables (NR-059 §3-§4). |
| Canonical ownership | **Yes.** NR-051 proved `national/workflow_runtime` and `national/task_engine` are sole owners. |
| Tenancy | **1 of 15.** Only `national_workflow_executions` carries a tenant column. |
| Audit | **0 canonical calls** in either package. |
| State-machine semantics | Present — a workflow state machine and a saga engine exist. |
| Idempotency / concurrency | **Absent.** No idempotency key, no `with_for_update`, no compare-and-set on `version`. |

Two of six fail, and both failures are independent of product intent.

## 3. Tenancy

Fourteen of the fifteen tables have no column that scopes a row to a lab,
facility or governorate. `national_tasks` has 22 columns — `assigned_to`,
`assigned_by`, `created_by`, `queue_id`, `correlation_id` — and not one of them
says *whose*. The listing path
(`task_engine/infrastructure/repository.py::list`) filters on status, priority,
category, assignee, queue_id and a title `LIKE`, and on nothing else, because
there is nothing else to filter on.

The cause is visible in one line per model: all fifteen extend `BaseEntity`.
`app/national/base.py` defines four bases —

```
BaseEntity        timestamps, soft delete, optimistic lock
TenantEntity      + TenantMixin
AuditEntity       + AuditMixin
TenantAuditEntity + both
```

— and these fifteen use the only one with neither. `national_practitioners` uses
`AuditEntity`; the `cc_*` models use `TenantAuditEntity`. This was a choice
available at the time and not taken.

Built as declared, `GET /national/tasks` returns every tenant's tasks to any
caller authorized for the route. That is CLAUDE.md security invariant #1, at
national scale.

## 3.1 [Unit 6] The tenant column is vestigial, and the tenancy model is undecided

The earlier reading — "1 of 15 is tenanted" — was too generous.
`national_workflow_executions.tenant_id` exists, but `tenant_id` appears in
exactly six places across both packages: the column, a domain-entity field
defaulting to `None`, a service parameter defaulting to `None`, the value passed
through to the model, and two serialisation points. **No route supplies it.**
The routes derive `created_by` from `current_user.id` and stop there, so the
column is written NULL on every path that could write it.

So the surface is not partly tenanted. It is untenanted, with one column that
looks like tenancy and is not.

That turns tenancy from an omission into a **decision that has not been taken**,
and the two available answers disagree about what a national workflow is scoped
to:

| Candidate | Shape | What it would mean |
| --- | --- | --- |
| `TenantMixin.lab_id` | `INTEGER` → `labs.id` | a national workflow belongs to one laboratory |
| the existing `tenant_id` | `VARCHAR(100)`, nullable | some string tenant identifier — facility, governorate or organization |

Nothing in the repository prefers one. `labs` is the built tenant of the LIMS;
`niam_organizations` and `national_facilities` are both built and both plausible
for a *national* orchestration layer; and the only signal the package itself
carries is an optional string that nobody sets.

**This document does not choose.** Applying `TenantMixin` would assert that
national workflows are lab-scoped, on a national orchestration layer, against
the one contrary signal present — a consequential and hard-to-reverse data-model
decision with no evidence behind it. Recorded as the open question it is:

> What is the tenant of a national workflow execution or task — a laboratory, a
> facility, a governorate, or an organization?

Held mechanically: `test_the_one_tenant_column_is_still_never_populated` fails
the moment a route supplies `tenant_id`, because at that moment the question has
been answered and the answer belongs in this document rather than in a keyword
argument.

## 3.2 [Unit 7] Laboratory scope is eliminated, and the surface is larger than fifteen tables

§3.1 left four candidates and chose none. That was the right call from inside
`task_engine` and `workflow_runtime`, which is where it was made. Looked at from
the platform, one of the four is not a candidate at all.

### The scope vocabulary

Two enumerations decide what a role or a membership may be scoped **to**:

| Enum | Owner | Members |
| --- | --- | --- |
| `RoleScopeType` | `app/identity/models/authorization.py` | organization, facility, department, unit, workspace |
| `MembershipScopeType` | `app/identity/models/membership.py` | organization, facility, department, unit, workspace |

There is no `lab` member and no `governorate` member in either.

The consequence is not stylistic. A national artifact keyed by `lab_id` cannot be
named by any role assignment, so nothing can be granted over it and nothing can
be denied over it. Adopting `TenantMixin` on a national table would not give it
weak tenancy; it would give it tenancy the authorization model cannot read.

**The vocabulary is enforced, not decorative.**
`MembershipService._validate_context` looks the scope up in a mapping of exactly
those five members and raises `Unsupported membership scope` on a miss, so
`scope_type` — a `String(30)` the caller supplies — cannot become free text.
`AuthorizationServiceV2` takes an assignment's `scope_type` from the **role**,
never from the request. Every table behind this (`niam_role_assignments`,
`niam_memberships`, `niam_organizations`) is migration-backed.

**Organization is the mandatory root.** `niam_role_assignments.organization_id`
is `nullable=False`; `facility_id`, `department_id`, `unit_id` and `workspace_id`
are nullable narrowings beneath it. All five are ULID `String(26)` into `niam_*`
tables, where `TenantMixin.lab_id` is an `INTEGER` into `labs.id` — so the
laboratory option is also a type-level mismatch with the columns that express
scope.

So §3.1's table loses a row:

| Candidate | Status after Unit 7 |
| --- | --- |
| `TenantMixin.lab_id` | **eliminated** — unnameable by any role scope, and type-incompatible with the scope columns |
| governorate | **eliminated as a scope** — there is no governorate entity to point at. `niam_organizations.governorate` is a nullable `String(50)` *attribute* of an organization (with a `find_by_governorate` lookup beside it), so a governorate is a property of the scope root, not a level of it |
| organization root (`String(26)` → `niam_organizations`) | open |
| genuinely national (deliberately unscoped) | open |

### The question that remains

> Is national orchestration scoped at the organization root, or is it genuinely
> national and therefore deliberately unscoped?

That is still reserved under §44. Both surviving answers are defensible, and the
difference between them is jurisdictional rather than technical: whether a
ministry workflow belongs to the organization that started it or to the state.
Unit 7 narrows the decision; it does not take it.

### Blanket tenancy would be the opposite error

`app/national/ecosystem` is the counter-example, and it is the strongest one
available because it is **built**: six tables, all migration-backed, none
tenanted — `ecosystem_partners` and its credentials, certificates, rate limits,
audit logs and agreements. It is a registry of external partners, and an external
partner sits outside every tenant by definition. Giving those rows a tenant would
be a modelling error dressed as hardening.

That is why the guard forbids one specific adoption rather than requiring a
column.

### The surface, measured

NR-065 opened on fifteen tables in two packages. Across `app/national` the same
condition holds much more widely:

| Package | Tables | Untenanted | Built |
| --- | ---: | ---: | ---: |
| background_platform | 4 | 4 | 0 |
| document_platform | 6 | 6 | 0 |
| domain | 47 | 22 | 0 |
| ecosystem | 6 | 6 | **6** |
| observability | 8 | 8 | 0 |
| reference | 16 | 16 | 0 |
| rules_engine | 2 | 2 | 0 |
| scheduling_platform | 7 | 6 | 0 |
| search_platform | 2 | 0 | **2** |
| task_engine | 7 | 7 | 0 |
| workflow_runtime | 8 | 7 | 0 |
| **total** | **113** | **84** | **8** |

Seven packages are untenanted in full (background_platform, document_platform,
ecosystem, observability, reference, rules_engine, task_engine — 49 tables, six
of them built). Only eight of 113 national tables are built at all, which is why
this is a decision to take before building rather than a migration to write now.

### The one exception, declared rather than waived

Exactly two tables under `app/national` carry `lab_id`:
`national_search_saved_searches` and `national_search_results`. Both are built
and both filter on it correctly. What they scope is a user's own saved searches
and their results — a laboratory-local convenience that happens to live under
`app/national/`, not a national capability wearing lab tenancy. It is listed as
an allowed exception, and the guard requires it to stay built: an exception
granted to an unbuilt table protects nothing.

Held mechanically by `backend/tests/test_national_scope_vocabulary.py` (7 tests,
gated in `iam-hardening.yml`): the vocabulary may not gain a laboratory member,
an unsupported scope must still be refused at the service boundary, organization
must stay the mandatory root, and no further national table may adopt `lab_id`
or `TenantMixin`. Each was negative-proven by reintroducing the defect and
confirming the intended failure.

## 4. Audit

Neither package contains a call reaching the hash-chained audit log. That gap is
invisible at NR-062's package granularity — `app/national` counts as auditing
because `national/api/routes/interop.py` calls `log_action`, which is exactly
the lower bound NR-062 documented for itself. Measuring per subpackage exposes it.

`national_task_audit_logs` is **not** a counter-example. Its six columns are
`task_id`, `action`, `actor_id`, `previous_status`, `new_status`, `details`:
a status-transition log with no chain hash, no link to the previous entry and no
off-database anchor. It records what happened; it cannot prove the record was not
altered. It also has no tenant column.

## 5. Concurrency

`BaseEntity` supplies a `version` column through `OptimisticLockMixin`, and
`national_tasks` redeclares one. Nothing reads either on update:
`WorkflowExecutionRepository.save` loads by id, mutates the fields, and commits.
There is no idempotency key and no row lock anywhere in a package containing a
saga engine — so two concurrent step completions can both advance the same
execution.

## 6. The correction this forces

NR-059 §5 called shipping *"the cheapest of the NR-022-family decisions"* on the
grounds that ownership and implementation were already in place. Ownership and
implementation **are** in place. Tenancy and audit are not, and neither is
concurrency control. Building fifteen tables and fixing four frontend URLs would
not produce a working feature; it would produce a cross-tenant, unaudited
national task surface. That estimate was wrong and is corrected here.

## 7. What must happen first, whichever way §5 resolves

- **Not shipping** → retire both packages and both frontend pages. Nothing below
  applies and the National Core problem shrinks by fifteen tables.
- **Shipping** → in this order, before any migration:
  1. **Answer §3.1 first.** Re-basing on `TenantAuditEntity` picks `lab_id`
     (INTEGER, `labs.id`) by default, and that is the decision, not a detail.
     Then add the tenant column that answer implies.
  2. Add the tenant filter to every repository read path.
  3. Route mutations through `services/audit_service.log_action` so they reach
     the chain.
  4. Add an idempotency key to task creation and workflow triggering, and a
     compare-and-set or row lock to execution advance.
  5. Then one additive migration, verified on PostgreSQL in CI.

## 8. What is applied here

The precondition, additively and in tests only:
`backend/tests/test_orchestration_build_precondition.py` and, from Unit 7,
`backend/tests/test_national_scope_vocabulary.py`. No orchestration table
may be built while it lacks a tenant column; no package may have tables built
while it contains no canonical audit call; the untenanted ledger may shrink and
may not grow, and an entry that gains tenancy must be removed rather than left
behind.

Unit 7 adds no table and no column. It eliminates one candidate, records the
two that survive, and makes the elimination hold: the scope vocabulary may not
gain a laboratory member, an unsupported scope must still be refused at the
service boundary, organization must stay the mandatory root, and no further
national table may adopt `lab_id` or `TenantMixin`.

No runtime code changed. No table built. The 15 stay in the schema-fidelity
unbuilt ledger with their endpoint count stated (NR-058), so the state remains
visible either way.

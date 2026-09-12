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

## 3.3 [Unit 8] DECIDED — national orchestration is organization-rooted

§3.2 left two candidates and called the choice jurisdictional. It is not. They
are the same candidate, and one line of the bootstrap proves it.

### The evidence that closed it

`app/identity/bootstrap/seed.py::seed_platform_organization` creates

```python
NIAMOrganization(
    org_id="GULA-PLATFORM",
    name_en="GULA National Digital Health Platform",
    org_type="ministry",
    ...
)
```

**The ministry is a row in `niam_organizations`.** So the national level already
*is* an organization, and `RoleScopeType.organization` at that row already
expresses national scope. "Organization root" and "genuinely national" were
never rivals; the second is an instance of the first.

That removes the last reason to invent anything. A `national` scope member would
be a second spelling of `organization` at one particular row, and a nullable
"unscoped means national" convention would be a third. Two spellings of one
scope is how a query that filters on one silently misses the other.

### The decision

> **National workflow and task orchestration is scoped at the canonical
> organization root, using the authorization vocabulary unchanged. National work
> is organization scope at the ministry organization. Child rows carry no scope
> column and inherit through their parent. Cross-organization coordination is
> expressed by participants, never by widening the scope column.**

Concretely, when these tables are built:

| Table | Scope | Why |
| --- | --- | --- |
| `national_workflow_definitions` | `organization_id` **NOT NULL** + optional narrowings | a definition is owned; the ministry owns national ones |
| `national_workflow_executions` | inherits the definition's owner; records the **initiating** scope | who ran it is not who owns it (§E) |
| `national_tasks` | `organization_id` **NOT NULL** + optional `facility_id` | the unit of work someone is accountable for |
| `national_task_queues`, `national_task_sla_definitions` | `organization_id` **NOT NULL** | policy objects, owned like a definition |
| `national_workflow_templates` | `organization_id` **NOT NULL** | as above |
| `national_workflow_execution_steps`, `_approvals`, `_compensations`, `_timers` | **none** — inherit via `execution_id` | a scope column here duplicates the FK |
| `national_task_assignments`, `_escalations`, `_comments`, `_audit_logs` | **none** — inherit via `task_id` | as above |
| `national_saga_logs` | **none** — inherits via `saga_id` | note `saga_id` is `String(100)` and unconstrained; see §7 |

Nine of the fifteen take no scope column at all. That is the substance of the
decision as much as the root is: the earlier framing, "should these tables have
`tenant_id`", contained a false premise, because most of them are children.

### Why the alternatives were rejected

| Alternative | Rejected because |
| --- | --- |
| `TenantMixin.lab_id` on all fifteen | §3.2 — unnameable by any role scope, and `INTEGER` against ULID scope columns |
| a `national` scope member | the ministry is already an organization; a second spelling of one scope |
| nullable scope, "null means national" | makes the most privileged scope the default for a forgotten column |
| `tenant_id VARCHAR(100)` as it stands | no referent, no constraint, no route sets it (§3.1) |
| a single `organization_id` on **every** table, children included | duplicates the parent FK, and admits rows whose scope disagrees with their parent's |
| a single `organization_id` as the **only** scope on coordination rows | **disproved by the platform's own model** — see below |

### The cross-organization negative proof

`national_referrals` is the platform's existing cross-facility coordination
entity, and it is instructive precisely because of what it does **not** have:

```
referring_facility_id  -> national_facilities   (nullable)
receiving_facility_id  -> national_facilities   (nullable)
receiving_department_id-> national_departments  (nullable)
```

There is **no `organization_id` on `national_referrals` at all.** A referral is
scoped by the *pair* of facilities it connects, which may sit in different
organizations. So a single organization column cannot express coordination, and
any rule of the form "every national table must carry one organization_id" is
refuted by a built, shipped table in the same package family.

This is why the decision separates **ownership** from **participation** (§E of
the brief). The scope column answers "whose object is this?". Coordination
across organizations is expressed the way `national_referrals` already does it —
as explicit participant references — and never by relaxing the owner column.

### Scope must be server-derived, and there is already a pattern for it

`ClinicalAuthorizationContextService` resolves, fail-closed, for one legacy lab
user:

```
legacy_lab_user_id -> LegacyAccountLink(status=migrated)
                   -> Account + IdentityRecord (both active)
                   -> ClinicalScopeBridge active binding
                   -> (facility_resource_id, organization_resource_id,
                       tenant_id, scope_mapping_version)
```

with five distinct error types and no defaulting at any step. Its docstring is
explicit that it "does not add a facility to a token and does not authorize a
clinical operation by itself". That is the established shape: derive scope on the
server from a reviewed binding, or refuse.

Orchestration must use that, not a column the caller fills in. It also explains
the honest limit on implementing this today, recorded in §3.4.

## 3.4 [Unit 8] Why the decision is not yet implemented as columns

The decision above is settled. Writing it into the models is blocked behind
things that are worse than the thing it fixes, and all of them were found by the
caller trace this unit ran.

**Neither router performs any authorization.** `factory.py:695` and `:698`
register both routers, and neither `app/national/task_engine/api/routes.py` nor
`app/national/workflow_runtime/api/routes.py` contains a single
`require_permission`. Every endpoint is guarded by `get_current_user` alone. On
the day these tables are built, any authenticated principal — including a
laboratory technician with no national role — could create, execute, cancel,
reassign and delete national workflows and tasks, and list every one that exists.
A correct `organization_id` on a table behind an unauthenticated-in-effect
endpoint is a correctly-labelled open door.

This is an omission in these packages, not a habit of the platform. Every other
national route module declares `require_permission` — background_platform 2,
document_platform 2, observability 2, rules_engine 2, scheduling_platform 2,
search_platform 3, ecosystem 2 — which is both the evidence and the remediation
reference.

Writing that comparison as a guard immediately found a **third** unguarded
module the caller trace had not reached: `app/national/intelligence/routes.py`,
registered at `factory.py:786`, with endpoints including
`/intelligence/clinical/care-gaps/{patient_id}` and
`/intelligence/clinical/risk-score/{patient_id}`. It is recorded separately as
**NR-072** and at a much lower severity, because the whole
`app/national/intelligence` package performs **no database access at all** — no
`SessionLocal`, no `get_db`, no `.query(` anywhere in it. `patient_id` is echoed
rather than resolved, and `calculate_risk_score` builds its entire "patient" from
the `age` and `gender` query parameters. No patient data is read, so it is an
authorization gap on stateless compute rather than a disclosure. Stating it that
way is the point: the URL shape invites the louder reading, and the code does not
support it.

**`update_task` assigns from the request body.**

```python
for key, value in updates.items():
    if hasattr(task, key) and key not in ("id", "created_at", "version"):
        setattr(task, key, value)
```

`created_by`, `assigned_to`, `assigned_by`, `status` and `correlation_id` are all
writable. A scope column added to that entity would be writable too — the caller
would choose its own scope, which is worse than having no column.

**The actor comes from the client.** `POST /{task_id}/assign` passes
`data.get("assigned_by")` and `POST /{task_id}/escalate` passes
`data.get("escalated_to")`, while the same handlers hold an authenticated
`current_user` and use it for `created_by`.

**Canonical scope is not reachable from the authenticated principal.**
`get_current_user` returns `LabUser | User`. `LabUser` has no organization at all
— only `lab_id` and `province_id`. `User` has `organization_id`, but it points at
`organizations.id` (**INTEGER**), not `niam_organizations.id` (**ULID
`String(26)`**), which is what a role assignment names. The NIAM plane is reached
through `LegacyAccountLink` and the reviewed bridges, and neither router is on
that path. So the derivation the decision requires cannot run at these routes
today.

**There are no consumers.** Nothing outside the two packages creates a workflow
or a task. `app/platform/workflow.py` looks like a consumer and is not: it calls
`WorkflowRuntimeService()` with no arguments where the constructor takes eight
required repositories, so every method would raise `TypeError` — and the module
is imported by nothing, so its `PlatformRegistry.register("workflow", ...)` never
runs. `app/identity/governance` has its own unrelated `PolicyApprovalWorkflow`.

So the ordering is: authorization, then server-derived actor and scope, then
build the tables with the columns this section specifies. Adding the columns
first would be the least valuable of the three and would make the other two look
addressed.

Held mechanically by `test_orchestration_build_precondition.py`: no orchestration
table may be built while its router checks no permission, while `update_task`
assigns from the body, or while an actor identifier comes from the request body —
alongside the existing tenancy and audit preconditions. And by
`test_national_scope_vocabulary.py`: the ministry must remain an organization,
and no `national` member may be added to either scope enum.

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

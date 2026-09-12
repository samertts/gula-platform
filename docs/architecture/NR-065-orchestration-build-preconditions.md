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
  1. Re-base the fifteen on `TenantAuditEntity` (or `TenantEntity` where a row is
     genuinely not a mutation of record) and add the tenant column.
  2. Add the tenant filter to every repository read path.
  3. Route mutations through `services/audit_service.log_action` so they reach
     the chain.
  4. Add an idempotency key to task creation and workflow triggering, and a
     compare-and-set or row lock to execution advance.
  5. Then one additive migration, verified on PostgreSQL in CI.

## 8. What is applied here

The precondition, additively and in tests only:
`backend/tests/test_orchestration_build_precondition.py`. No orchestration table
may be built while it lacks a tenant column; no package may have tables built
while it contains no canonical audit call; the untenanted ledger may shrink and
may not grow, and an entry that gains tenancy must be removed rather than left
behind.

No runtime code changed. No table built. The 15 stay in the schema-fidelity
unbuilt ledger with their endpoint count stated (NR-058), so the state remains
visible either way.

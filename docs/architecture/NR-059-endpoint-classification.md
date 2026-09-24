# NR-059 — classifying the 42 endpoints before building anything

**Status:** DECISION-READY. No table built, no endpoint withdrawn, no frontend changed.
**Method:** cached ownership scan + committed `evidence-created-tables.json` + AST of
the two route modules. No repository-wide rescan.

## 1. The rule this phase exists to resist

42 endpoints reference 15 tables that no migration creates. The reflexive fix is
to write 15 `create_table` calls. That would be building schema to satisfy a
route list rather than a product, so every endpoint is classified first.

## 2. How they are registered (a correction worth recording)

`national_router` is **not** registered by `factory.py` — which is why
`/national/security/consent/check` does not exist (NR-060). But the task and
workflow routers **are** registered, directly and individually:

```
factory.py:695   from .national.workflow_runtime.api.routes import router as workflow_router
factory.py:698   from .national.task_engine.api.routes  import router as task_router
```

Both facts hold together. These 42 are live in the OpenAPI schema; the consent
enforcement stub is not.

## 3. Classification

51 handlers across the two modules, collapsing to 42 unique OpenAPI paths.

| Class | Count | Endpoints |
| --- | ---: | --- |
| **Canonical / live** | 2 | `/national/tasks/health`, `/national/workflows/health` — the only two handlers that touch no repository. They work today. |
| **Blocked dependency — real implementation, no schema** | ~40 | Every other handler. Each reaches a service → repository → one of the 15 unbuilt tables. |
| **Placeholder / fabricated** | 0 backend | See §4: the *callers* are malformed, not the handlers. |
| **Duplicate** | 0 | NR-051 established `national/workflow_runtime` as the sole owner of workflow. Nothing else implements it. |
| **Wrong owner** | 0 | Ownership is proven and correct. |
| **Safe to retire** | 0 outright | See §5 — retirement is a product decision, and there is a consumer. |
| **Requires genuine schema construction** | conditional | The 15 tables, *if* §5 resolves in favour of the feature. |

The ~40 are **not placeholders**. The packages contain domain entities, enums,
domain events, repository interfaces, SQLAlchemy implementations, a workflow
state machine and a saga engine. This is a complete implementation that was
never given a schema — which is a different failure from a stub, and calls for a
different remedy.

## 4. There is a consumer, and its calls are partly malformed

Two `frontend-v3` pages issue ten queries against these endpoints:

- `pages/national/workflow-runtime/NationalWorkflowRuntimeApiPage.tsx` — definitions,
  executions, steps, approvals, pending approvals, templates
- `pages/national/task-engine/NationalTaskEngineApiPage.tsx` — tasks, dashboard,
  comments, history

So these are **not dormant**: they are live pages calling live endpoints over
tables that cannot exist. On a migrated database each returns a server error.

Four of the ten are additionally malformed — `/national/workflows/executions//steps`,
`/executions//approvals`, `/national/tasks//comments`, `/tasks//history` — a
**double slash where a path parameter should be**. That is the NR-054
auto-generated-page signature: the `{id}` was interpolated as empty. Those four
would fail even against a working backend.

These pages are a **different class from NR-057** (which is calls resolving to no
registered route). These resolve to registered routes that cannot return data.

## 5. The decision, and why it is not mine to take

Ownership is proven (NR-051). A consumer exists. What is missing is evidence of
**product intent**, and it cannot be derived from the repository:

> Is national task and workflow orchestration a feature GULA is shipping, or
> scaffolding that was generated and never removed?

- **Shipping** → build the 15 tables in one migration, fix the four malformed
  frontend URLs, and the feature works. Ownership and implementation are already
  in place, so this is the cheapest of the NR-022-family decisions.
- **Not shipping** → retire both packages and both frontend pages. The 263-FK
  National Core problem shrinks by 15 tables.

What must **not** happen is the middle path: building 15 tables so that 42
endpoints stop erroring, without deciding whether anyone wants the feature. That
is schema built to satisfy a route list.

## 6. Recommended immediate action (not taken here)

Under NR-054's rule — *a route may only remain visible if its backend contract is
real and verified* — the two frontend pages should be hidden until §5 resolves.
That is a UX/API-surface change of exactly the kind NR-054 required an explicit
brief for, so it is recommended rather than applied.

The 15 tables stay declared in `test_schema_fidelity`'s unbuilt ledger with the
endpoint count stated (NR-058), so the state remains visible either way.

## 7. Status

**DECISION-READY.** Nothing built, nothing withdrawn. The classification stands
on the committed `create_table` evidence and a live OpenAPI schema.

# IA-058 — the platform advertised a workflow capability that could not be constructed

**Severity** P1 · **Confidence** CONFIRMED · **Reachability** advertised at
`GET /platform/capabilities` (admin-gated); the four operations are not
individually routed
**Fix status** FIXED — `c9f58874`, local commit on `claude/independent-audit-1`, not pushed
**Negative proof** NP-V / NP-W / NP-X, each restored byte-identically (sha256)

---

## The defect

All four methods of `app/platform/workflow.py` did this:

```python
service = WorkflowRuntimeService()
```

`WorkflowRuntimeService.__init__` has **eight required** repository parameters,
so every call raised:

```
TypeError: WorkflowRuntimeService.__init__() missing 8 required positional
arguments: 'definition_repo', 'execution_repo', 'step_repo', 'approval_repo',
'compensation_repo', 'timer_repo', 'saga_repo' and 'template_repo'
```

The module registers itself into `PlatformRegistry` **at import time**, so the
advertisement was live from startup even though nothing could run.

## What is and is not reachable

`app/platform/routes.py` exposes three endpoints, all behind
`require_permission("system:admin")`:

| Path | What it does |
|------|--------------|
| `GET /platform/health` | lists module names |
| `GET /platform/modules` | lists module names |
| `GET /platform/capabilities` | lists every registered capability |

**None of them invokes a service method.** So the live defect is not a 500 on a
served operation — it is `GET /platform/capabilities` stating that the platform
can start, cancel, status and list workflows when it cannot. The four methods
are latent: reachable only by a future caller resolving the module out of the
registry, which is exactly what the registry exists for.

Severity is P1 rather than P2 because an admin or an orchestrator reading that
listing to decide what the platform supports is being told something false.

## The family is closed

An AST scan of all 15 modules in `app/platform/`, resolving each imported name
and inspecting the real `__init__` signature:

```
zero-arg constructions of imported classes scanned: 7
constructions that must raise TypeError: 4
  app/platform/workflow.py:35  WorkflowRuntimeService() -> 8 required
  app/platform/workflow.py:46  WorkflowRuntimeService() -> 8 required
  app/platform/workflow.py:52  WorkflowRuntimeService() -> 8 required
  app/platform/workflow.py:67  WorkflowRuntimeService() -> 8 required
```

One module, one class, four sites. The scan is now a test, with the scanned
count asserted as a positive control so a scan gone blind fails rather than
passing.

## Why the repositories were NOT wired

This is the decision that matters, so the evidence is given in full.

### 1. `SagaLogRepository` has no implementation

`app/national/workflow_runtime/infrastructure/repository.py` defines seven:

```
SQLAlchemyWorkflowDefinitionRepository      SQLAlchemyWorkflowCompensationRepository
SQLAlchemyWorkflowExecutionRepository       SQLAlchemyWorkflowTimerRepository
SQLAlchemyWorkflowExecutionStepRepository   SQLAlchemyWorkflowTemplateRepository
SQLAlchemyWorkflowApprovalRepository
```

The eighth, `SagaLogRepository`, exists only as an ABC at
`domain/repository.py:141`.

**The subsystem's own router makes this plain.**
`app/national/workflow_runtime/api/routes.py::_get_service`:

```python
return WorkflowRuntimeService(
    definition_repo=SQLAlchemyWorkflowDefinitionRepository(),
    ...
    saga_repo=None,                      # ← against `saga_repo: SagaLogRepository`
    template_repo=SQLAlchemyWorkflowTemplateRepository(),
)
```

The parameter is annotated `SagaLogRepository`, not `SagaLogRepository | None`.
So the one working construction site in the codebase satisfies that argument
with a value its own type forbids. Copying that pattern into the platform
wrapper would propagate the hole, not close it.

> This also corrects something I had written earlier. The IA-057 narrative in
> `test_national_platform_runtime_truth.py` said "the router's own
> `_get_service()` passes eight repositories". It passes seven and a `None`.
> The correction is now in that file.

### 2. No migration creates any of the eight tables

Each table name was taken from the subsystem's ORM and checked individually
against `migrations/versions/` for a `create_table`:

| Table | Creating migrations |
|-------|--------------------|
| `national_workflow_definitions` | 0 |
| `national_workflow_executions` | 0 |
| `national_workflow_execution_steps` | 0 |
| `national_workflow_approvals` | 0 |
| `national_workflow_compensations` | 0 |
| `national_workflow_timers` | 0 |
| `national_workflow_templates` | 0 |
| `national_saga_logs` | 0 |

### The conclusion

Wiring seven of eight repositories would convert a `TypeError` into
`no such table: national_workflow_definitions` at the first query. **That is
not a repair — it is the same unavailability wearing a different exception.**
Making this capability work is build-out: one repository implementation plus one
migration. Neither is invented here.

## The repair

A single `UNAVAILABLE_REASON` string, raised by every entry point as
`WorkflowRuntimeUnavailable` and published by the registry, so the capability
listing and the runtime error cannot drift apart.

### What was deliberately not returned

```python
def get_status(self, execution_id: str) -> dict | None:
    raise self._unavailable("get_status")
    # Deliberately NOT `return None`. None is this method's documented
    # "no such execution" answer, so returning it here would report a
    # missing execution when the truth is that the subsystem cannot run.
```

Same for `get_tasks` and `[]`, which is indistinguishable from an execution
with no steps. Both would convert an outage into a successful empty result.

The real method bodies are preserved as comments under each raise: the mapping
from the runtime's return values to this façade's dict shape was correct — only
the construction was not — so whoever wires this does not have to reconstruct
it.

### Three further things the registry was getting wrong

| | Before | After |
|---|--------|-------|
| `register()` | no way to say a module cannot run | `available` / `unavailable_reason`, defaulting to available so existing registrations are unchanged; **refuses** `available=False` without a reason, because an unexplained outage in a capability listing cannot be acted on |
| `health()` | `dict.fromkeys(cls._modules, "registered")` — every module, unconditionally, including ones whose every entry point raised. True, but read as healthy | `"unavailable"` for those modules |
| `get_capabilities()` | `cap["module"] = name` mutated the **stored** dicts and returned references to registry state, so a caller editing a returned dict edited the registry | each entry is a copy, with a test |

## Negative proofs

The dangerous edit here is not a regression to `TypeError` — it is someone
making the suite green by returning an empty answer. So the proofs are aimed
there first.

| ID | Perturbation | Named tests that failed | Restored |
|----|-------------|-------------------------|----------|
| NP-V | `get_tasks` returns `[]` instead of raising — the fake success | `test_every_entry_point_raises_rather_than_returning_a_plausible_answer`, `test_get_status_does_not_answer_none_and_get_tasks_does_not_answer_empty` | sha256 OK |
| NP-W | register without `available=False` — the advertisement returns | 4 tests across both files, incl. `test_the_capability_listing_says_the_workflow_capability_is_unavailable` | sha256 OK |
| NP-X | delete the guard forbidding an unexplained outage | `test_an_unavailable_module_cannot_be_registered_without_a_reason` | sha256 OK |

One test's own ratchet caught a flaw in itself during this work:
`test_health_distinguishes_unavailable_from_registered` asserted that some
module still reads `"registered"`, and failed — because only `workflow` was
imported in that process, so the only value present was `"unavailable"`. The
assertion was right to demand both states and wrong to assume import order
would supply them; it now registers its own probe.

## Suite state

`tests/verification/` — **876 passed**, 150 skipped, 2 xfailed (875 before,
+8 new, −7 superseded from the flipped IA-057 tests). `py_compile` clean,
`flake8 --select=E9,F821,F811` clean.

## What remains open

The capability is **honestly unavailable**, not working. To make it work:

1. implement `SagaLogRepository` (or make `saga_repo` genuinely optional, and
   make the saga paths that need it fail closed) — and then fix
   `api/routes.py::_get_service`, which passes `None` today;
2. add a migration creating the eight tables;
3. wire the eight repositories into `WorkflowService` and delete the raises,
   restoring the preserved bodies.

Both (1) and (2) are new code and a new migration — CLAUDE.md puts schema
changes behind human approval. Recorded as the next step, not attempted.

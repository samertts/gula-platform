---
id: WF-INDEX
type: workflow
title: "Workflow Engine"
version: "1.0.0"
created: "2026-08-05"
status: verified
confidence: 95%
tags: [workflow, approval, retry, rollback, gula-kernel-ext-001]
---

# Workflow Engine

> Mission: GULA-KERNEL-EXT-001 — Phase 6
> Implementation: `scripts/kernel/ext/workflow.py`
> Machine-readable state: `workflows.json`

AI-operational workflows for missions: sequential and dependency-ordered
steps, approval gates, bounded retries, and cancel/rollback. Follows
`docs/constitution/18_WORKFLOW_CONSTITUTION.md` principles.

## Model

| Concept | Definition |
|---|---|
| WorkflowStep | id, kind (`task`/`approval`), description, handler, `requires`, `max_retries`, status |
| Workflow | id (WF-XXXXXX), name, steps, state, timestamps |
| State machine | pending → running → awaiting_approval → completed \| failed → rolled_back |
| WorkflowEngine | register, run, approve, cancel, workflows(state), snapshot, save |

## Properties (18_WORKFLOW_CONSTITUTION)

1. **Dependency ordering** — steps run only when their `requires` are
   completed; cycles are rejected at registration (reuses Kernel scheduler
   `find_cycle`).
2. **Approval gates** — an `approval` step halts the workflow in
   `awaiting_approval`; `approve()` resumes it.
3. **Bounded retries** — a task is retried up to `max_retries`; exhaustion
   fails the workflow (retry semantics mirror the Kernel recovery layer).
4. **Exceptions are first-class** — cancel/rollback via `cancel()`.
5. **State is persisted** — resumable; machine-readable snapshot.
6. **Emits events** — every transition publishes to the Phase 5 Event Bus
   (`workflow.<id>.completed`, `.awaiting_approval`, `.failed`).

## CLI

```bash
python scripts/kernel.py ext-workflow   # run demo workflow (with approval)
python scripts/kernel.py ext-check      # includes workflow completion gate
```

## Reuse

Composes `scripts/kernel/scheduler.py` (`find_cycle`), the Phase 5 Event
Bus (transition events), and Kernel recovery semantics. No scheduling or
event logic is duplicated.

## Related

- `workflows.json` — machine-readable workflow state
- `docs/constitution/18_WORKFLOW_CONSTITUTION.md` — workflow law
- Phase 5 Enterprise Event Bus — transition events

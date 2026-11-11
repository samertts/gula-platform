# IA-070 — six task-engine repositories reported writes they never made

**Severity** P1 · **Confidence** CONFIRMED · **Reachability** latent today, shielded
by the IA-059 TypeError — see "Why this was urgent anyway"
**Fix status** FIXED — `7e2de80c`, local commit on `claude/independent-audit-1`, not pushed
**Negative proof** NP-Y / NP-Z, each restored byte-identically (sha256)
**Supersedes** the repair IA-059 implied for its two task_engine entries

---

## How it was found

IA-059 recorded that `SQLAlchemyTaskAssignmentRepository` and
`SQLAlchemyTaskSLARepository` leave abstract methods unimplemented, so they
raise `TypeError` on instantiation. Reading the file to implement those methods
showed the rest of it.

## The defect

`app/national/task_engine/infrastructure/repository.py`, as committed:

```python
class SQLAlchemyTaskAuditLogRepository(TaskAuditLogRepository):
    async def save(self, log: Any) -> Any:
        return log                      # writes nothing, returns the entity
    async def find_by_task(self, task_id: str) -> list:
        return []
    ...
```

An AST pass over the file, classifying each class by whether any method
references `SessionLocal`/`session`/`query`/`execute`/`select`/`add`/`commit`:

| Class | Methods | DB-touching | Verdict |
|-------|---------|-------------|---------|
| `SQLAlchemyNationalTaskRepository` | 15 | 7 | **real** |
| `SQLAlchemyTaskQueueRepository` | 4 | 0 | stub |
| `SQLAlchemyTaskAssignmentRepository` | 5 | 0 | stub |
| `SQLAlchemyTaskEscalationRepository` | 4 | 0 | stub |
| `SQLAlchemyTaskSLARepository` | 4 | 0 | stub |
| `SQLAlchemyTaskCommentRepository` | 3 | 0 | stub |
| `SQLAlchemyTaskAuditLogRepository` | 4 | 0 | stub |

**6 of 7 classes, 24 methods, zero queries** — in classes named `SQLAlchemy*`.
The file does import SQLAlchemy and does use it, in the one real class, which is
what made the rest easy to miss.

`save()` returning its argument is the worst shape of the three: the caller
receives its own object back and has every reason to believe it was persisted.
`get()` returning `None` and finders returning `[]` are indistinguishable from
"no such row" and "no rows" — the normal, successful empty answers.

### The audit log

`SQLAlchemyTaskAuditLogRepository.save` discarded every entry and reported
success. CLAUDE.md security invariant 2 is "All mutations MUST write to the
audit log". Had the task engine been functional, every task mutation would have
been unaudited while the audit call returned normally.

## Why this was urgent anyway

Nothing reaches these today. All 29 routes in `api/routes.py` call
`_get_service()`, which constructs all seven repositories and raised:

```
TypeError: Can't instantiate abstract class SQLAlchemyTaskAssignmentRepository
without an implementation for abstract method 'find_by_assignee'
```

Measured directly, not inferred: `grep -c "@router\."` = 29,
`grep -c "_get_service()"` = 29, and calling `_get_service()` reproduces that
TypeError.

**So the two unconstructible classes were an accidental circuit breaker in
front of the other 24 silent methods.** The obvious repair for IA-059 — write
the three missing methods so the classes instantiate — would have unblocked
`_get_service()` and exposed every one of them, converting a loud failure into
silent data loss across the whole task engine, audit log included.

> An unconstructible class can be load-bearing. Check what its TypeError is
> holding back before making it constructible.

That lesson is now recorded in `test_repository_abc_conformance.py` for the two
IA-059 entries still open (`SQLResultRepository.list_by_patient_analyte` and
`DefaultLayoutDetector`), neither of which has been made constructible for that
reason.

## Why it was not repaired by writing real queries

All seven task_engine tables have **zero** creating migrations, each checked
individually against `migrations/versions/`:

```
national_tasks                 -> 0        national_task_sla_definitions -> 0
national_task_queues           -> 0        national_task_comments        -> 0
national_task_assignments      -> 0        national_task_audit_logs      -> 0
national_task_escalations      -> 0
```

Real SQLAlchemy here would produce `no such table: national_tasks`, not
persistence. Note this also means the one *real* repository cannot work either.

Making the task engine function is build-out: one migration plus six repository
implementations. None of it is invented here.

## The repair

Every method in the six classes raises `TaskEngineRepositoryUnavailable`,
naming the class, the method and one shared reason string. The three abstract
methods IA-059 flagged are implemented — as refusals — so:

* `_get_service()` now **succeeds**, and the 29 routes fail at the first
  repository call with an error that says what is actually wrong, instead of a
  constructor TypeError that says nothing actionable;
* the circuit breaker is no longer needed, because there is no longer anything
  behind it to shield;
* no future "make it constructible" change can expose a discard that no longer
  exists.

Constructibility is safe **only** because every method refuses. The test that
asserts construction says so explicitly, so the pair is not separated later.

### No `__getattr__` catch-all

The refusals list each contract method explicitly. A catch-all would answer a
method added to an ABC later with a refusal instead of letting it surface as a
normal `TypeError` at instantiation. A refusal must not become the thing that
hides a contract change. Asserted by a test.

## Negative proofs

The dangerous edit is not a regression to `TypeError` — it is someone making
something work by returning `[]`. Both proofs aim there.

| ID | Perturbation | Named tests that failed | Restored |
|----|-------------|-------------------------|----------|
| NP-Y | `SQLAlchemyTaskAuditLogRepository.save` returns its argument again | 4 tests across both files, incl. `test_the_audit_log_repository_does_not_report_a_write_it_did_not_make` and the AST ratchet | sha256 OK |
| NP-Z | add a `__getattr__` catch-all to `_UnavailableRepository` | `test_refusals_do_not_absorb_a_future_contract_change` | sha256 OK |

Both ratchets carry positive controls asserting they examined at least the 24
measured methods, so a walk or scan gone blind fails instead of passing
vacuously.

## Suite state

`tests/verification/` — **881 passed**, 150 skipped, 2 xfailed.
`py_compile` clean, `flake8 --select=E9,F821,F811` clean.

## What remains open

The task engine is **honestly unavailable**, not working. To make it work:

1. a migration creating the seven tables;
2. six real repository implementations;
3. delete the refusals.

(1) is a schema change, which CLAUDE.md puts behind human approval.

**Open question worth asking of the wider codebase:** this pattern — a class
named for a persistence technology that performs no persistence and returns
success-shaped values — is unlikely to be unique to `task_engine`. I have not
swept for it elsewhere. That sweep is the obvious next piece of work, and its
result should not be assumed either way: finding none would be as much a
measurement as finding more.

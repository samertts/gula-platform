# IA-071 — a served workflow write returned `success: true` and stored nothing

**Severity** P1 · **Confidence** CONFIRMED · **Reachability** **SERVED,
authenticated, live** — reproduced over HTTP
**Fix status** FIXED — local commit on `claude/independent-audit-1`, not pushed
**Found by** the platform-wide sweep IA-070 left open
**Corrects** IA-058's claim that this file "provides seven `SQLAlchemy*` repositories"

---

## Why this is the most serious of the four

IA-070 found the same pattern in `task_engine`, but there a `TypeError` at
construction shielded it — nothing could reach the stubs. **Here nothing
shields it.** `workflow_runtime`'s `_get_service()` has no missing abstract
methods, so it constructs, and the stubs are reachable through served routes.

Measured over HTTP as an authenticated admin, before the repair:

```
POST /national/workflows/templates
  -> 200 {"success":true,"id":"b4ebd8c9-4a67-440b-bb85-8173b19695a6"}

GET  /national/workflows/templates
  -> 200 {"items":[],"total":0}

GET  /national/workflows/approvals/pending
  -> 200 {"approvals":[]}
```

The write **reported success and minted an id the client could keep**, and
stored nothing. This is precisely the prohibited shape: a failure converted
into a fake success.

## The measurement

`app/national/workflow_runtime/infrastructure/repository.py`, classified by AST
on whether any method references the session/query/execute/select machinery:

| Class | Methods | DB-touching | Verdict |
|-------|---------|-------------|---------|
| `SQLAlchemyWorkflowDefinitionRepository` | 10 | 7 | **real** |
| `SQLAlchemyWorkflowExecutionRepository` | 9 | 6 | **real** |
| `SQLAlchemyWorkflowExecutionStepRepository` | 5 | 0 | stub |
| `SQLAlchemyWorkflowApprovalRepository` | 4 | 0 | stub |
| `SQLAlchemyWorkflowCompensationRepository` | 3 | 0 | stub |
| `SQLAlchemyWorkflowTimerRepository` | 4 | 0 | stub |
| `SQLAlchemyWorkflowTemplateRepository` | 4 | 0 | stub |

**2 real, 5 stubs, 20 fake methods.** Direct observation of the stub behaviour:

```
template.save({'id':'tpl-1'})  -> {'id': 'tpl-1'}   # returns the entity
template.delete('tpl-1')       -> True              # "deleted"
template.get('tpl-1')          -> None              # gone, right after "saving"
approval.save({'id':'ap-1'})   -> {'id': 'ap-1'}
approval.find_pending_for_user -> []                # whatever was approved
```

Two shapes deserve naming:

* **`delete` returning `True`.** A caller has no way to distinguish that from a
  real deletion. It is the hardest of these to notice.
* **`find_pending_for_user` returning `[]` unconditionally.** An approval can be
  recorded as saved and then never appear in the queue that governs it. In an
  approval workflow that is the whole point of the subsystem failing silently.

## Correction to IA-058

IA-058 stated that `infrastructure/repository.py` "provides seven
`SQLAlchemy*` repositories" and framed the absent `SagaLogRepository` as the
only gap. **Only two of the seven are real.**

IA-058's *conclusion* — do not wire these into `app/platform/workflow.py` —
holds and is strengthened. Its *reason* was wrong: I said wiring would produce
`no such table`. In fact five of the seven would have reported success and
persisted nothing, and only the two real ones would have failed honestly. The
trade would have been a loud failure for a silent one, which is worse than I
described. Both `IA-058_WORKFLOW_CAPABILITY.md` and the module docstring in
`app/platform/workflow.py` are corrected.

## How the sweep found it, including the sweep's own bug

IA-070 closed with an explicit open question: does the persistence-in-name-only
pattern exist elsewhere? The first sweep reported **15** hits. Most were false
positives from a case-insensitive `Orm` in the name pattern, which matches:

```
perfORMance   transfORM   platfORM
```

— so every `Performance*`, `Transform*` and `PlatformSubscriptionCreate` class
in the tree came back as a fake repository. Tightened to a case-sensitive,
anchored pattern, the sweep reports:

```
classes whose name claims persistence, scanned: 79
classes that perform none and return success-shaped values: 7
```

Of those 7, after reading each:

| Candidate | Verdict |
|-----------|---------|
| 5 × `workflow_runtime` repositories | **CONFIRMED** — this finding |
| `app/ai/system_optimizer.py::DBMetrics` | **VERIFIED_NEGATIVE** — a dataclass with computed `@property` methods deriving from its own fields; "DB" means database *metrics*, it claims no persistence |
| `app/health_data/streaming/sinks.py::PostgresSink` | **CONFIRMED, open** — see below |

## Still open: the streaming sinks

`PostgresSink.write` logs `"PostgresSink: writing %d records to %s"` and then
`return len(records)` — reporting the number of records written, having written
none. `ClickHouseSink.write` is identical (the name pattern missed it; reading
the file found it).

Not repaired in this commit, because I have not yet measured whether either
sink is reachable, and the fix may be to delete them rather than make them
refuse. Recorded rather than guessed at.

## The repair

The five stub classes raise `WorkflowRepositoryUnavailable`, naming the class,
the method and one shared reason. Not repaired by writing queries, for the same
reason as IA-070: none of the subsystem's eight tables has a creating migration
(each checked individually), so real SQLAlchemy would raise `no such table`.
That is honest too, but refusing says *why*, and reaching it does not require
guessing at column names.

The two real repositories are untouched, and a test asserts they still query
and were not converted to refusals by mistake.

### On the response code

The served routes now fail rather than returning `200 {"success":true}`. A 500
is not a good answer, and mapping these to 503 would be better — but a write
that reports success and stores nothing is strictly worse than a write that
fails loudly, so the ugly honest answer ships and the polish is recorded as
follow-up.

## Negative proofs

| ID | Perturbation | Named tests that failed | Restored |
|----|-------------|-------------------------|----------|
| NP-AA | `SQLAlchemyWorkflowTemplateRepository.delete` returns `True` again | `test_delete_does_not_report_a_deletion_it_did_not_perform`, the AST ratchet, the method walk | sha256 verified |
| NP-AB | `find_pending_for_user` returns `[]` again | `test_the_served_reads_do_not_answer_an_empty_list` and the walk | sha256 verified |

Both ratchets assert they examined at least the 20 measured methods, so a scan
gone blind fails rather than passing vacuously.

## Suite state

`tests/verification/` — **888 passed**, 150 skipped, 2 xfailed.
`py_compile` clean, `flake8 --select=E9,F821,F811` clean.

## What remains open

1. **The streaming sinks** above — measure reachability, then refuse or delete.
2. **Make the subsystem work**: a migration for the eight tables, plus five
   repository implementations and `SagaLogRepository`. Schema change, so gated.
3. **Map the refusals to 503** at the route layer rather than letting them 500.
4. **The sweep covered names.** A class named neutrally — `TemplateStore`,
   `ApprovalGateway` — with the same empty bodies would not have been caught by
   a name-based pattern. A behavioural sweep (a repository wired into a route
   whose methods never touch a session) would be stronger, and has not been
   done. Finding nothing there would be a measurement; assuming it is the right
   answer would not.

# IA-069 — the compatibility contract suite is in no executed test scope, and has rotted

**Severity** P2 · **Confidence** CONFIRMED · **Reachability** not served — CI/test-infrastructure defect
**Discovered** 2026-10-05, while repairing IA-061: the repair broke a consumer,
and the consumer turned out to have been broken already.
**Fix status** FIXED — the whole tree now runs: **33 passed, 6 skipped, 4 xfailed
(strict), 0 failed, 0 errors**. The four xfails are the real catalog drift, held
visible rather than silenced; see "The four things left failing on purpose".

---

## How it surfaced

IA-061 made `result_to_fhir`'s `patient_id` keyword-only and required. Grepping
for consumers before committing found one outside `backend/`:

```
contracts/compatibility/test_contract_fhir.py:164:  resource = result_to_fhir(FakeResult())
```

Running that file to check the break produced **two** failures, not one:

```
FAILED TestFHIRMapperOutput::test_result_mapper_produces_valid_fhir   ← mine
FAILED TestFHIRMapperOutput::test_order_mapper_produces_valid_fhir    ← not mine
E   TypeError: order_to_fhir_service_request() missing 1 required
    keyword-only argument: 'patient_id'
```

`order_to_fhir_service_request` was made keyword-only by **NR-219**, a repair
that landed before this cycle. Its call site in this file was never updated,
and nothing noticed.

## Why nothing noticed

```
$ cat backend/pytest.ini
[pytest]
testpaths = tests
```

CI runs `cd backend && pytest tests/`. `contracts/compatibility/` is outside
that path. No workflow references it:

```
$ grep -rn "contracts" .github/workflows/ | grep -v "contracts/sdk"
(nothing)
```

Every `contracts/` reference in the workflow tree points at `contracts/sdk/`
(the published client SDKs). The compatibility suite — the thing whose job is
to notice exactly this class of drift — has never run in CI.

**This is the finding.** The broken assertion is a symptom; a contract suite
that is not executed is not a contract.

## The rot, measured

Four independent drifts, all in code that only runs if someone runs it by hand:

| Site | Drifted against | Symptom |
|------|-----------------|---------|
| `test_contract_fhir.py` order mapper call | NR-219's keyword-only `patient_id` | `TypeError` |
| `test_contract_fhir.py` `FakeOrder` | `app.lims.models.Order.order_status` | `AttributeError` |
| `conftest.py::auth_token` | `create_token(data: JWTClaims)` — the keyword form has never existed | every dependent test errored at setup |
| `test_contract_fhir.py` `FakeResult` | `app.lims.models.Specimen` | see below — this one is the interesting failure |

### The fake that was richer than the model

`FakeResult` carried:

```python
class FakeSpecimen:
    class FakeOrder:
        patient_id = 1
    order = FakeOrder()
specimen = FakeSpecimen()
```

The real `Specimen` has `order_id` and **no** `order` relationship. The mapper
guarded on `hasattr(result.specimen, "order")`, so:

- in production the guard never passed → `Patient/unknown` on every Observation (IA-061);
- in this contract test the fake supplied the missing attribute → the guard
  passed → the test asserted valid FHIR and was satisfied.

So even if this suite *had* run, it would not have caught IA-061. A fake that
is richer than the model it stands for cannot hold the contract: it tests the
fake. This is a second-order finding and the more durable one — running the
suite is necessary but not sufficient.

## Repaired here

`test_contract_fhir.py` → **13 passed, 0 failed, 0 errors**.

- both mapper call sites pass a resolved `patient_id`, and additionally assert
  `subject.reference == f"Patient/{patient_id}"` and that `patient_id=None` raises;
- the nested `specimen.order.patient_id` fake is deleted, with a comment
  recording why it must not come back;
- `FakeOrder.order_status` added;
- `conftest.py::auth_token` passes a claims dict, with claim names matching
  `app.security.auth.build_token_payload`.

## The rest of the tree, classified and repaired

Running the whole suite initially gave **7 failed, 28 passed, 6 skipped, 1 error**.
Every one is now classified by measurement. Six were test defects; four were real
drift.

### Test defects, repaired

| Test | Defect | Repair |
|------|--------|--------|
| `test_contracts.py::TestReportGeneration::test_version_match` | `NameError: name 'datetime' is not defined` — the fixture that writes the report artifact errored at setup, so **the report this suite exists to produce was never written at all** | added `from datetime import datetime` |
| `test_contracts.py::_get_backend_routes` | a *second independent copy* of the same broken flat census | delegates to the one corrected walker in `test_contract_api`, so the two cannot drift apart |
| `test_contract_api.py::test_health_endpoints_public` | asserted 200 on `/health/ready` | asserts publicness (not 404, not 401/403); see below |
| `test_contracts.py::test_health_endpoints_reachable` | same assertion, duplicated | same repair |
| `test_contract_dto.py::test_known_enum_fields` | `pattern.strip("^$").split("|")` turned `^(android\|ios)$` into `{"(android", "ios)"}` and `^[MFmf]$` into `{"[MFmf]"}`, so the intersection was always empty and the test **failed on patterns that were correct** | `_pattern_alternatives()` reads the two shapes the catalog uses — alternation and character class — and says in its docstring that it is a reader for those two, not a regex engine |
| `test_contract_api.py::test_methods_match_catalog` | `assert len(mismatches) <= 3`, a magic tolerance hiding up to three real mismatches and naming none | the ledger names all 27 and ratchets both ways |

#### Why `/health/ready` returning 503 is not a defect

`ReadinessMiddleware` holds every non-whitelisted path at 503 until
`startup_guard` sets `system_ready`, and the guard cannot complete in a test app
with no migrated database. The 503 is the designed behaviour. The test conflated
*reachable without a credential* with *this deployment is ready*, so it could
only ever pass against a fully started stack — which, given the suite never ran,
nobody discovered. The repaired test asserts what its own name claims:
`/health` and `/health/live` must be 200 (liveness does not depend on readiness),
and the other three must be neither 404 nor 401/403.

### The artifact that dates the last real run

`contracts/compatibility/report.json` is tracked, and says:

```json
"generated_at": "2026-07-14T17:29:44",
"platform_version": "2.1.0",
"runner_version": "1.0.0",
{"test": "platform_version_match", "status": "PASS", "detail": "backend=2.1.0, catalog=2.1.0"}
"summary": {"total": 7, "passed": 7, "failed": 0, "passed_pct": 100.0}
```

So the last recorded state of this suite is **100% passing**, on 2026-07-14,
when the backend genuinely was 2.1.0 and the catalog genuinely did match. It has
been stale ever since, and because nothing ran it, the 100% stood unchallenged
for nearly three months. That artifact is the finding's own timeline.

**It was nearly destroyed in the course of fixing this.** Once the missing
`datetime` import let `TestReportGeneration` run, its `report_path` fixture --
pointing at that tracked file -- overwrote the 7-result 2.1.0 report with a
thinner 1-result one from a different producer. I restored it from git and
repointed the fixture:

- default is now a `tmp_path`, so running the suite cannot touch the artifact
  or dirty the working tree;
- `CONTRACT_REPORT_PATH` writes it somewhere real on purpose, which is what a
  CI job collecting the report should set — never back over the committed one.

Worth stating plainly: the repair for one defect briefly caused the deletion of
the evidence for another. The ordering that caught it was checking `git status`
and reading the diff before staging, rather than committing a green suite.

## The four things left failing on purpose

All four are the same underlying drift, in four projections. Each is
`@pytest.mark.xfail(strict=True)` with the reason inline — **strict**, so that
closing the gap makes the xfail itself fail and forces the markers and the
ledger to be updated together. A plain xfail would let a real fix pass silently.

| Test | What it measures |
|------|------------------|
| `test_platform_version_matches` | catalog declares `platform_version` **2.1.0**; `config.py` is at **2.5.0** |
| `TestReportGeneration::test_version_match` | the same mismatch, asserted again while writing the report |
| `test_all_catalog_endpoints_registered` | the (method, path) projection of the 254-path gap |
| `test_all_dto_schemas_have_backend_models` | 19 DTO schemas with no backend model: `orders_results/TestResult*`, all 9 `mpi/*`, all 5 `governance/*`, all 3 `tasks/*` |

The DTO failure corroborates rather than duplicates the path gap: the `/mpi/*`
endpoints those nine DTOs describe are themselves among the 254 unregistered
catalog paths. The catalog, its DTOs and its version all describe the 2.1.0
surface.

**I deliberately did not make the version test green by editing the version
string.** Relabelling the catalog 2.5.0 would assert it is current while 81% of
its paths do not exist — a worse falsehood than the mismatch it hides. The
mismatch is fixed by regenerating the catalog, which is a contract change.

## The measured gap

| | |
|---|---|
| catalog paths declared | **313** |
| paths the app registers | **1796** |
| catalog paths not registered | **254 (81%)** |
| method mismatches on the 59 that do match | **27** |

Recorded in `contracts/compatibility/KNOWN_CATALOG_GAP.json` and asserted by
`test_catalog_gap_matches_the_recorded_ledger`, which fails if the gap grows
**and** if it shrinks without the ledger being regenerated.

### Verified by sampling, not assumed

A 16-path random sample (seed 7) of the 254, probed over HTTP: all 16 absent.

**One of them taught a methodological lesson worth keeping.** `/insurance/claims`
answered **401**, which looks like proof it exists. It does not exist: the
request matched `/insurance/{insurance_id}` with `insurance_id="claims"`, and
that route's auth dependency produced the 401. The same trap caught
`/results/stats`, which answers 405 via `/results/{result_id}`.

> For this app, a non-404 response is **not** evidence that a documented path
> exists. Parameterised siblings swallow concrete segments. Only the resolved
> route census is decisive.

That is why the ledger is built from the census and the sample is corroboration,
not the other way round.

### Negative proofs

| ID | Perturbation | Named test that failed | Restored |
|----|-------------|------------------------|----------|
| NP-S | drop one entry from `unmatched_catalog_paths` | `test_catalog_gap_matches_the_recorded_ledger` (new gap) | sha256 OK |
| NP-T | add a bogus entry to `unmatched_catalog_paths` | same test (recorded gap no longer a gap) | sha256 OK |
| NP-U | revert `_get_registered_routes` to the flat `hasattr` walk | `test_the_route_census_is_not_inert` **and** both ledger tests | restored from copy, suite re-verified green |

NP-U is the one that matters most: it proves the positive control works. Without
`test_the_route_census_is_not_inert` — which pins both a plausible magnitude
(>1000 paths) and four certainly-registered paths — a collapsed census would
make every "not found" result here meaningless, which is exactly the state this
finding was discovered in.

## Superseded — the state at first measurement

Kept for the record, because the sequence matters: the classification below was
written before any of it was measured, and deliberately refused to guess.

> Running the whole suite gave **7 failed, 28 passed, 6 skipped, 1 error**.
> These are **UNCLASSIFIED pending measurement**. Each is one of two things and
> the distinction matters: a *stale test*, or a *real platform defect*. I have
> not yet measured which is which, and will not guess: a catalog assertion
> failing is not evidence that the endpoint is missing, and the reverse is
> equally untrue.

Measured outcome: **six stale tests, four real drift.** Both kinds were present,
so neither blanket assumption would have been right.

## Recommendation — now unblocked, still not applied

The original note recorded an ordering constraint:

> **Wiring the suite into CI before classifying the 7 remaining failures would
> turn CI red.** The 7 must be resolved first — each either fixed or explicitly
> `xfail`ed with a reason — and only then should the suite be gated.

**That constraint is now satisfied.** The suite is green (33 passed, 6 skipped,
4 strict xfails, 0 failures) and runs with no special `PYTHONPATH`:

```
ENV=test RUNTIME_MODE=test pytest contracts/compatibility/
```

What remains is adding it to an executed suite. Two options:

1. **`backend/pytest.ini`** — `testpaths = tests` would become
   `testpaths = tests ../contracts/compatibility`. Smallest change, but reaches
   outside `backend/`, and the suite needs the repo root importable.
2. **A CI step** — one `pytest contracts/compatibility/` in the test job.
   Cleaner separation, and the job already has the environment this suite needs.

I recommend (2). Neither is applied: CLAUDE.md puts `.github/workflows/` changes
behind human approval, and `pytest.ini` governs what CI executes, so changing it
is a CI change by another name. This is a one-line addition waiting on a
decision, not on more work.

**The warning that still stands:** gating this suite while it is red, or
silencing its findings to make it green, would both be worse than leaving it
unrun. The four strict xfails are the line between those two — they keep the
real drift failing-by-record, and they will break the moment someone closes the
gap without updating the ledger.

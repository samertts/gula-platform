# IA-069 — the compatibility contract suite is in no executed test scope, and has rotted

**Severity** P2 · **Confidence** CONFIRMED · **Reachability** not served — CI/test-infrastructure defect
**Discovered** 2026-10-05, while repairing IA-061: the repair broke a consumer,
and the consumer turned out to have been broken already.
**Fix status** PARTIALLY FIXED — `test_contract_fhir.py` green at 13/13; 7 failures
and 1 error remain in the rest of the tree, classified below but not yet repaired.

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

## Not repaired — the rest of the tree, classified

Running the whole suite (`ENV=test RUNTIME_MODE=test pytest contracts/compatibility/`)
gives **7 failed, 28 passed, 6 skipped, 1 error**:

```
ERROR  test_contracts.py::TestReportGeneration::test_version_match
FAILED test_contract_api.py::TestEndpointReachability::test_all_catalog_paths_registered
FAILED test_contract_api.py::TestEndpointReachability::test_health_endpoints_public
FAILED test_contract_dto.py::TestDTOEnumValues::test_known_enum_fields
FAILED test_contracts.py::TestModelMatching::test_all_dto_schemas_have_backend_models
FAILED test_contracts.py::TestAPIContract::test_all_catalog_endpoints_registered
FAILED test_contracts.py::TestAPIContract::test_platform_version_matches
FAILED test_contracts.py::TestAPIContract::test_health_endpoints_reachable
```

These are **UNCLASSIFIED pending measurement**. Each is one of two things and
the distinction matters:

- a *stale test* (the contract catalog has moved on and the assertion is wrong), or
- a *real platform defect* (a catalogued endpoint genuinely is not registered,
  a health endpoint genuinely is not public, the platform version genuinely
  does not match).

The second kind would be substantive — `test_health_endpoints_public` and
`test_all_catalog_paths_registered` in particular overlap with the route-census
work. I have not yet measured which is which, and will not guess: a catalog
assertion failing is not evidence that the endpoint is missing, and the
reverse is equally untrue.

## Recommendation (not applied — CI is gated)

Add `contracts/compatibility/` to an executed suite. CLAUDE.md puts
`.github/workflows/` changes behind human approval and the standing brief
forbids touching them, so this is recorded rather than done.

Note the ordering constraint: **wiring the suite into CI before classifying
the 7 remaining failures would turn CI red.** The 7 must be resolved first —
each either fixed or explicitly `xfail`ed with a reason — and only then should
the suite be gated. Gating it while it is red, or silencing the failures to
make it green, would both be worse than leaving it unrun and honest about it.

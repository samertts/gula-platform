# IA-061 — Adversarial Proof: the LIMS Observation names no patient

**Severity** P1 · **Confidence** CONFIRMED · **Reachability** served, authenticated, tenant-scoped
**Runtime proof** `backend/tests/verification/test_lims_result_fhir_http.py` (7 scenarios, HTTP)
**Negative proof** NP-I, restored byte-identically (sha256)
**Fix status** NOT APPLIED — decision gate below

---

## The trace

```
GET /lims/results/{id}/fhir           app/lims/routes.py:1453-1465
  -> Depends(get_current_user)        authenticated
  -> Result WHERE id AND lab_id       tenant-scoped on _lab_id(current_user)
  -> result_to_fhir(result)           app/lims/fhir_mappers.py:108  returned unchanged
       subject = Patient/{result.specimen.order.patient_id}
                 if hasattr(result, "specimen") and hasattr(result.specimen, "order")
                 else "unknown"
```

`Specimen` has `order_id` (FK to `lab_orders.id`) and **no `order` relationship**.
Measured: `hasattr(Specimen, "order") is False`. The only `order`-named
relationship in `app/lims/models.py` is `Order.original_order` (line 993).
The guard can never pass, so the `else` branch always runs.

## Phase 1 — seven scenarios, over HTTP

| # | Scenario | Status | `subject` |
|---|---|---|---|
| 1,2,7 | normal result, valid `order_id`, single Observation path | **200** | `{"reference": "unknown", "display": ""}` |
| 3 | `order_id = 999999` (no such `lab_orders` row) | **200** | `{"reference": "unknown", "display": ""}` — unchanged, because the mapper never reads the order |
| 4 | tenant B reads tenant A's result | **404** | — tenant isolation holds; 404 not 403, so no existence oracle |
| 4b | no credential | **401** | — |
| 5 | wrong-patient reference | — | not constructible: no patient id reaches the payload at all |
| 6 | bundle path `/lims/orders/{id}/fhir-bundle` | **200** | `subject` **absent** from all 3 entries (`ServiceRequest`, `Specimen`, `Observation`) — `routes.py:1021` pops it deliberately |

Classification of the outcome, asserted rather than described:

```
subject absent            False
subject null              False
malformed reference       True     <-- this one
correct Patient reference False
exception                 False
```

`valueQuantity` is correct and UCUM-coded
(`{"value": 5.4, "unit": "mmol/L", "system": "http://unitsofmeasure.org", "code": "mmol/L"}`),
so the payload is otherwise well-formed. Only the subject is wrong.

## The sibling endpoint proves the correct behaviour on identical data

Same order, same patient, same analyte, one request each
(`test_dual_result_store_divergence.py`):

```
/fhir/Observation/1        id='1'            subject={'reference': 'Patient/1', 'type': 'Patient'}
/lims/results/1/fhir       id='lims-obs-1'   subject={'reference': 'unknown',   'display': ''}
```

The core FHIR bridge resolves the patient correctly from the same row set.
This is not a question of what is possible — the platform already does it.

## Phase 2 — the intended contract is already established, twice, in the same file

| Site | Pattern |
|---|---|
| `app/lims/routes.py:952-962` (`/orders/{id}/fhir`) | `db.query(LabOrder.patient_id).filter(...)` → `order_to_fhir_service_request(lims_order, patient_id=patient_id)` |
| `app/lims/routes.py:995-1003` (bundle) | same resolution, same keyword-only hand-off |
| `app/lims/fhir_mappers.py:285` | `"subject": _fhir_reference(f"Patient/{patient_id}")` — the correct builder |

Measured: `Result`, `Specimen` and `Order` all carry `order_id`; **none carries
`patient_id`**. So resolution must go through `lab_orders.patient_id`, which is
exactly what both route sites already do. There are two patient-reference
builders in `fhir_mappers.py`: line 285 takes the id as a keyword-only
parameter and is correct; line 117 reaches for a relationship that does not
exist and is not.

**No relationship was invented to establish this.** The contract was read off
the existing code.

## The contradiction in the existing fix

The docstring of `order_to_fhir_service_request` — the fix applied after the
ServiceRequest subject was found publishing `Patient/{order_id}` — justifies
itself partly with:

> `result_to_fhir` in this same module already reaches the patient correctly
> through `specimen.order.patient_id`

**That assertion is false** and is pinned as a test. The ServiceRequest path
was repaired correctly; the Observation path beside it was assumed correct and
never measured. The docstring also records the discipline that would have
caught this: *"No default is the control: a call site that forgets the argument
fails loudly rather than silently publishing a wrong-patient reference."*
`result_to_fhir` has no such control — its fallback is silent.

## Impact

- **Security** none found. Authenticated, tenant-scoped, 404 on cross-tenant,
  401 unauthenticated. No PHI exposed, no wrong patient named — the reference
  points at nothing.
- **Clinical / data integrity** an Observation a consumer cannot file against
  a patient. A receiving system either rejects it or files it unattributed.
  Worse than a loud failure, because the payload otherwise validates.
- **Scope** one of two call sites. The bundle is unaffected by design.

## Decision gate — why this is not fixed here

Two mechanically obvious repairs:

1. **Add `Specimen.order`.** One line, makes the existing guard pass. But it
   adds an ORM relationship into a module whose own docstring says the
   foundation models remain untouched, and it would silently make the false
   docstring claim true without anyone revisiting it.
2. **Resolve in the route and pass keyword-only**, mirroring
   `order_to_fhir_service_request`: query `LabOrder.patient_id` via
   `Specimen.order_id`, make `patient_id` a required keyword argument of
   `result_to_fhir`, delete the `hasattr` fallback so a forgetful caller fails
   loudly.

(2) matches the established precedent and carries the fail-loud control. It
also changes a served FHIR response shape — `subject` becomes a real Patient
reference where clients currently receive `"unknown"` — which CLAUDE.md puts
behind human approval, and the brief for this cycle forbids changing FHIR
subject semantics. **Recommended, not applied.**

Prepared but withheld: the route-side resolution already exists verbatim at
`routes.py:952-958` and can be lifted into `result_fhir` without inventing
anything.

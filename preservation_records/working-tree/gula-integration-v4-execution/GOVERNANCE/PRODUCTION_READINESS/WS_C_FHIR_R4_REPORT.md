# Workstream C — Isolated FHIR R4 Adapter Report (F-03)

**Status:** development evidence only. `GOVERNANCE/FINAL_DECISION.md` remains **HOLD** (md5 `effdfeaf10234678d83b2668c4489552`); the MPI verdict remains **REJECT**. Nothing in this report is a release, clinical-safety, national-deployment or production-approval claim.

**Workspace:** `/home/samertts/workspace/projects/gula-integration` only. The protected repository `/home/samertts/workspace/projects/gula-platform` was not written to; its `git status --short` was empty at final verification.

## 1. Objective and outcome

F-03 required an actual, isolated FHIR R4 adapter for the completed synthetic Health Core slice: real serialisation/deserialisation, synthetic-only reference and identifier validation, and real `OperationOutcome` error mapping. This workstream implemented that adapter as a **pure in-process Python package**. It is deliberately not a FHIR server, not a client, not an HTTP boundary and not production activated.

The adapter round-trips nine frozen internal entity types through nine FHIR R4 resource shapes, fails closed on unsupported or malformed input, and maps every error code visible to this package to a valid R4 `OperationOutcome.issue.code`.

## 2. Files created (all uncommitted)

| Path | Lines | Purpose |
|---|---:|---|
| `backend/app/health_core/fhir/__init__.py` | 49 | Public exports and explicit non-compliance scope note |
| `backend/app/health_core/fhir/adapter.py` | 36 | `FhirR4Adapter.serialize/deserialize/round_trip/operation_outcome` facade |
| `backend/app/health_core/fhir/errors.py` | 160 | Adapter error classes, R4 issue-type set, `operation_outcome_from_error` |
| `backend/app/health_core/fhir/support.py` | 476 | Allow/deny lists, local synthetic URNs, extensions, strict reference/identifier validation helpers |
| `backend/app/health_core/fhir/serializers.py` | 404 | Nine real entity → FHIR R4 JSON serializers |
| `backend/app/health_core/fhir/deserializers.py` | 814 | Nine real FHIR R4 JSON → frozen entity deserializers |
| `backend/tests/health_core/test_fhir_roundtrip.py` | 410 | Nine field-equality round-trips, shape checks, explicit resource sets, service-emitted entities |
| `backend/tests/health_core/test_fhir_validation.py` | 262 | Negative reference, identifier, malformed, missing-field and profile/version/tenant tests |
| `backend/tests/health_core/test_fhir_operation_outcome.py` | 174 | Every mapped error code, R4 issue-code validity, diagnostics determinism, facade delegation |
| `GOVERNANCE/PRODUCTION_READINESS/WS_C_FHIR_R4_REPORT.md` | this file | Evidence, gaps and handoff |

No other path was created, edited, staged, committed, pushed, merged, rebased or cleaned by this workstream. `factory.py`, `main.py`, `GOVERNANCE/FINAL_DECISION.md`, MPI files, production `app/fhir/**`, schemas, migrations and DDL were read-only.

## 3. Requirement evidence

| Requirement | Status | Evidence |
|---|---|---|
| Work only in `gula-integration`; protected repo byte-untouched | PASS | `git status --short` in `gula-platform` returned no output |
| Keep HOLD / REJECT unchanged | PASS | `FINAL_DECISION.md` md5 unchanged; static guard `test_final_decision_and_protected_governance_file_hash_is_unchanged` passed; no MPI file written |
| No DDL, migration, schema, production DB or real patient data | PASS | No migration/DDL tokens in new source; all fixtures are `SYN-` opaque values; static guard passed |
| No commit/push/merge/rebase/PR/deploy/`git add`/`git reset`/`git clean` | PASS | No such command was executed |
| No production activation | PASS | No router, route, `include_router`, `factory.py` or `main.py` edit; static guard `test_no_fastapi_router_construction_or_route_decorators` and `test_factory_and_main_do_not_import_or_reference_health_core` passed |
| No new third-party dependency | PASS | Imports are stdlib plus already-installed Health Core modules; no packaging file changed |
| No placeholder / fake success / skipped tests | PASS | Static guards for empty bodies, `return True`, skips/xfails and assertion presence all passed |
| Explicit supported/unsupported resources | PASS | `SUPPORTED_FHIR_RESOURCE_TYPES` (9) and `UNSUPPORTED_FHIR_RESOURCE_TYPES` (28) in `support.py`; allow-list is authoritative |
| Frozen entity → FHIR R4 JSON dict | PASS | Nine serializer functions with `resourceType`, `id`, versioned synthetic `meta`, opaque `SYN-` identifiers and `Type/SYN-...` references |
| Deserialize only validated dicts | PASS | Nine deserializer functions; non-dict input raises `InvalidFhirResourceError`; all fields pass strict validators |
| Synthetic-only references/identifiers | PASS | Shared `reject_national_identifier` and `is_synthetic_id` used on every identifier/reference; cross-resource prefix mismatch rejected |
| Every visible error code → real `OperationOutcome` | PASS | 16 codes mapped; R4 issue-type set enforced; unknown future codes fall back to `processing` |
| Round-trip tests for every supported resource | PASS | Nine parametrized field-equality cases in `test_fhir_roundtrip.py` |
| Negative tests for invalid reference, real identifier, unsupported resource, malformed resource, missing field, every error code | PASS | `test_fhir_validation.py` and `test_fhir_operation_outcome.py` |

## 4. Supported and unsupported resources

### Supported (exact allow-list)

| Internal frozen entity | FHIR R4 resource | Notes |
|---|---|---|
| `Practitioner` | `Practitioner` | Role/qualification carried in local extensions |
| `Organization` | `Organization` | Active state preserved |
| `Facility` | `Location` | R4 has no `Facility` resource |
| `Encounter` | `Encounter` | Exact internal state in local extension, validated against FHIR status |
| `Diagnosis` | `Condition` | ICD code validation retained |
| `Observation` | `Observation` | UCUM-style quantity; synthetic local code system |
| `LabOrder` | `ServiceRequest` | Exact order state and idempotency key in local extensions |
| `Specimen` | `Specimen` | Barcode in synthetic local system; exact state in extension |
| `LabResult` | `DiagnosticReport` | Numeric value/range/amendments in local extensions; no separate Observation fabricated |

`Patient` is **not** a supported top-level resource: no `Patient` entity exists in the synthetic slice and no identity link is fabricated. It is accepted only as an opaque reference target `Patient/SYN-PAT-...` with a validated synthetic label and matching tenant.

### Documented deny-list

`UNSUPPORTED_FHIR_RESOURCE_TYPES` explicitly names 28 considered-but-rejected types: `Patient`, `MedicationRequest`, `MedicationStatement`, `AllergyIntolerance`, `Immunization`, `CarePlan`, `DocumentReference`, `Composition`, `Procedure`, `Bundle`, `Goal`, `Device`, `Provenance`, `Claim`, `Coverage`, `AuditEvent`, `Questionnaire`, `FamilyMemberHistory`, `RelatedPerson`, `Person`, `Group`, `SupplyRequest`, `NutritionOrder`, `RiskAssessment`, `ImagingStudy`, `Appointment`, `Schedule`, `CapabilityStatement`.

This tuple is documentation, not an exhaustive list of every FHIR R4 resource. The **allow-list is the authoritative gate**: any resource outside the nine supported types is rejected with a structured `UNSUPPORTED_FHIR_RESOURCE` error.

## 5. Synthetic identity and reference rules

- Identifier system: `urn:gula:synthetic:fhir:R4:identifier`.
- Barcode system: `urn:gula:synthetic:fhir:R4:barcode`.
- Local code systems: `urn:gula:synthetic:fhir:R4:CodeSystem/local` and `.../test`.
- Profiles: `urn:gula:synthetic:fhir:R4:StructureDefinition/synthetic-<Resource>`.
- Extensions: `urn:gula:synthetic:fhir:R4:extension/*`, including tenant, patient label, lifecycle state, idempotency key, cancellation, result value/range/criticality and amendment provenance.
- Versioning: `meta.versionId` is the local Health Core contract version; deserialization requires a positive integer and the exact profile.
- References must be exact relative `Type/SYN-...` strings. The validator rejects absolute URLs, extra path segments, extra `Reference` keys, digit-only values, real-looking values, malformed prefixes and type/prefix mismatches.
- Internal lifecycle states that collapse into one FHIR status are preserved by local extensions; deserialization verifies extension/status consistency instead of coercing state.

## 6. `OperationOutcome` mapping

The shared `FHIR_ISSUE_CODE_BY_ERROR_CODE` map was used as guidance. Two of its values are legacy shorthands that are **not** R4 issue-type codes (`forbidden`, `conflict`), so the adapter canonicalises them before emission. The shared contract itself was not modified.

| Error code | Emitted R4 issue code |
|---|---|
| `HEALTH_CORE_ERROR` | `processing` |
| `INVALID_SYNTHETIC_REFERENCE` | `invalid` |
| `UNKNOWN_PATIENT` | `not-found` |
| `TENANT_MISMATCH` | `denied` (guidance: `forbidden`) |
| `DUPLICATE_ENTITY` | `duplicate` (guidance: `conflict`) |
| `INVALID_STATE_TRANSITION` | `invariant` (guidance: `conflict`) |
| `FORBIDDEN_SYNTHETIC_OPERATION` | `denied` (guidance: `forbidden`) |
| `UNSUPPORTED_FHIR_RESOURCE` | `not-supported` |
| `INVALID_FHIR_RESOURCE` | `invalid` |
| `CLINICAL_VALIDATION_ERROR` | `invalid` |
| `UNKNOWN_CLINICAL_ENTITY` | `not-found` |
| `LAB_WORKFLOW_ERROR` | `processing` |
| `UNKNOWN_LAB_ENTITY` | `not-found` |
| `UNKNOWN_TEST_CODE` | `not-supported` |
| `INVALID_RESULT` | `invalid` |
| `INVALID_ACTOR` | `invalid` |

Every outcome contains exactly one issue with `severity` (`error` for statuses below 500, `fatal` at/above 500), a valid R4 `code`, and deterministic `diagnostics` containing the stable code, client-safe message and sorted structured details. No traceback, real-world identifier or fabricated issue code is emitted. An unrecognised future code falls back to `processing`.

## 7. Verification results

All commands were run from the integration workspace with `/tmp/opencode/mpi-venv/bin/python`.

### Focused FHIR adapter suite

```bash
cd /home/samertts/workspace/projects/gula-integration/backend
ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. \
  /tmp/opencode/mpi-venv/bin/python -m pytest tests/health_core/test_fhir*.py -q --tb=short
```

Result: **94 passed**, 1 pre-existing `StarletteDeprecationWarning`, 0 failed.

### Full Health Core suite

```bash
cd /home/samertts/workspace/projects/gula-integration/backend
ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. \
  /tmp/opencode/mpi-venv/bin/python -m pytest tests/health_core -q --tb=short
```

Result: **750 passed**, 1 pre-existing warning, 0 failed. This includes `test_sandbox_guards.py` (4 tests) and `test_quality_review_static.py` (18 tests), so the new package is covered by the existing import, router, DDL, secret, HOLD-md5, skip/xfail and assertion guards.

### Lint and typing

```bash
cd /home/samertts/workspace/projects/gula-integration
/tmp/opencode/mpi-venv/bin/python -m ruff check \
  backend/app/health_core/fhir backend/tests/health_core/test_fhir*.py
```

Result: `All checks passed!`

```bash
cd /home/samertts/workspace/projects/gula-integration
MYPYPATH=backend /tmp/opencode/mpi-venv/bin/python -m mypy \
  --config-file pyproject.toml backend/app/health_core/fhir
```

Result: **zero errors attributable to the new package** (6 source files checked). The command still exits 1 because of two pre-existing baseline errors in the read-only file `backend/app/domain/order_state.py` (lines 63 and 81, `no-untyped-def`). Those are outside the WS-C write boundary and are listed as a handoff item.

### Boundary checks

- `git status --short` in `gula-platform`: empty.
- `md5sum GOVERNANCE/FINAL_DECISION.md`: `effdfeaf10234678d83b2668c4489552`.
- Filtered `git status` in `gula-integration` shows only the new `backend/app/health_core/fhir/` package, the three new `test_fhir*.py` files and this report as WS-C deliverables. All remain **uncommitted**.
- No production `app/fhir/**` module is imported or modified by this package.

## 8. Defects found and corrected during implementation

1. `Observation.category` and `DiagnosticReport.category` are R4 CodeableConcept arrays; the deserializers initially treated them as a single CodeableConcept. Added a strict one-concept reader.
2. `deserialize_resource` called `.get()` before checking the input type; a list input raised `AttributeError`. It now raises structured `InvalidFhirResourceError`.
3. The diagnostic-report reference range is carried as decimal text in a local extension; bounds are now parsed as finite numbers instead of being passed as strings.
4. A service-emitted round-trip test used a generic idempotency-key prefix rejected by the real clinical services; keys now use each service's required `SYN-` prefix.
5. The missing-field test deleted `qualification` from an `Organization`; it now uses a `Practitioner` resource where that field exists.
6. The initial `OperationOutcome` mapping emitted legacy non-R4 codes from shared guidance; it now canonicalises to valid R4 values while preserving the documented guidance and not modifying the read-only contract.

No assertion was deleted or weakened to obtain green tests.

## 9. Conformance evidence and gaps

### Evidence (real, narrow)

- Actual FHIR R4 JSON resource dictionaries with correct `resourceType`, `id`, `meta`, identifiers, references and status/category/quantity shapes.
- Real bidirectional mapping for nine frozen internal entities with field equality after round-trip.
- Strict synthetic identity/reference validation using the shared Health Core helpers.
- Deterministic, valid R4 `OperationOutcome` for all 16 visible error codes.

### Gaps (not implemented, not claimed)

- No FHIR conformance statement or `CapabilityStatement`.
- No terminology server, national code-system binding or snomed/LOINC validation beyond local synthetic/ICD and UCUM shapes.
- No HTTP interaction, content negotiation, `application/fhir+json` response layer, status-code binding or request audit.
- No national profile binding and no real identifier support by design.
- No production activation, feature flag, router or service wiring.
- The shared `contracts/errors.py` guidance and national factory `_FHIR_ISSUE_CODES` still contain legacy shorthands; WS-C canonicalises locally but did not alter read-only files.

This is not a claim of full FHIR R4 compliance.

## 10. Handoff requests

1. **Do not activate** this package or relax HOLD/REJECT without explicit owner approval and a separate security/clinical-safety review.
2. Ask the platform owner to reconcile `FHIR_ISSUE_CODE_BY_ERROR_CODE` and `app/factory.py::_FHIR_ISSUE_CODES` with the R4 issue-type value set if a single canonical map is desired; WS-C did not modify either.
3. Ask the F-03 owner to review and accept the narrow conformance scope above, especially the `Patient`-as-reference-only decision and local extensions for lifecycle states.
4. If production integration is ever authorised, commission a separate workstream for HTTP boundary, terminology/national profiles, capability negotiation, security, audit and operational monitoring.
5. Assign the two pre-existing `backend/app/domain/order_state.py` mypy errors to their owning workstream; they are outside the WS-C boundary.

## 11. Final declaration

The F-03 adapter exists, is exercised by 94 focused and 750 Health Core tests, is lint-clean under the scoped ruff command, has no new-scope mypy errors, and makes no production or governance-state change. It remains **uncommitted development evidence** under an unchanged **HOLD / REJECT** decision.

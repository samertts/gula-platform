# WS-A — Authorization Enforcement — Development Evidence Report

| Field | Value |
|---|---|
| Workstream | A — Authorization Enforcement (synthetic Health Core slice) |
| Review finding closed | **F-02** — declared RBAC/ABAC boundaries were not enforced at runtime (`GOVERNANCE/ACCELERATION/QUALITY_ARCHITECTURE_REVIEW.md` §4) |
| Date | 2026-11-18 |
| Branch / HEAD | `integration/gula-unification-v1` @ `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0` — **unchanged** (no commit made) |
| State | Implemented and verified in the working tree; **uncommitted** |
| Governing decision | `GOVERNANCE/FINAL_DECISION.md` remains **HOLD** (md5 `effdfeaf10234678d83b2668c4489552`, unchanged); MPI verdict remains **REJECT** (unchanged) |
| Nature of this document | **Development evidence only.** It is not a clinical-readiness, release, safety, security-certification or production-approval claim. It does not lift the HOLD or change the MPI verdict. |

---

## 1. Scope and protection integrity

Every constraint was checked after implementation; all pass.

| Constraint | Verification | Result |
|---|---|---|
| Work only in `gula-integration` | All created/edited paths are under this repo | PASS |
| `gula-platform` byte-untouched | `git -C /home/samertts/workspace/projects/gula-platform status --short` → empty (0 changes) | PASS |
| `GOVERNANCE/FINAL_DECISION.md` unchanged | `md5sum` → `effdfeaf10234678d83b2668c4489552`; body still begins `HOLD — do not release to production` | PASS |
| MPI stays REJECT; MPI files untouched | Verdict documented in `MPI_FINAL_INDEPENDENT_AUDIT.md` and referenced unchanged in governance docs; no MPI file edited | PASS |
| No production activation | No change to `backend/app/factory.py` or `backend/app/main.py`; no FastAPI router or route added; static gate confirms neither file references `app.health_core` | PASS |
| No DDL / migrations / schema / production DB / real patient data / secrets | No migration or schema file touched; all identifiers opaque `SYN-`; no real data or credentials used | PASS |
| No new third-party dependency | None added | PASS |
| No commit / push / merge / rebase / PR / deploy / `git add` / `git reset` / `git clean` | Only read-only git commands used (`status`, `rev-parse`, `diff --cached`); staged area contains **none** of this workstream's files; HEAD unchanged | PASS |
| Exclusive write ownership respected | Only `backend/app/health_core/authorization/**`, `backend/tests/health_core/test_authorization*.py`, and this report were created/edited | PASS |

Toolchain: `/tmp/opencode/mpi-venv/bin/python` (CPython **3.12.13**), pytest 9.1.1, `ENV=test RUNTIME_MODE=test PYTHONPATH=.:.. PYTHONDONTWRITEBYTECODE=1`.

---

## 2. Files created (exact)

Production package — `backend/app/health_core/authorization/`:

| File | Role |
|---|---|
| `__init__.py` | Public exports of the authorization layer (23 symbols). |
| `models.py` | Frozen, synthetic-only value objects: `Principal`, `ResourceContext`, `Decision`, `PolicyId`, `AuthorizationDecision`, `Action`, `PUBLIC_DENIAL_REASON`. |
| `errors.py` | `AuthorizationDenied` — extends shared `ForbiddenSyntheticOperationError`; generic 403 body, internal decision kept off the wire. |
| `audit.py` | Frozen `AuditRecord`, append-only `AuthorizationAuditLog`, SHA-256 hash chain over canonical JSON, `verify_audit_chain()`. |
| `engine.py` | `AuthorizationEngine`: exact RBAC map, authoritative grants, revocation registry, ordered scope evaluation, audited decisions. |
| `guard.py` | `AuthorizedHealthCore` facade over real `ClinicalContext` + `LabWorkflowService`; `ResourceAttributeIndex`; `build_authorized_context()`. |

Adversarial tests — `backend/tests/health_core/`:

| File | Tests | Coverage |
|---|---|---|
| `test_authorization_engine.py` | 35 | Deny-by-default, no-policy, authentication-alone, RBAC exactness, forged inputs, grants/expiry, revocation scopes/expiry, tenant/org/facility/patient scoping, audit dimensions, uniform denials. |
| `test_authorization_audit.py` | 11 | Genesis link, pristine chain, frozen records, immutable snapshot, edited/replaced/removed/reordered records, no mutation surface, internal policy id recorded. |
| `test_authorization_guard.py` | 16 | End-to-end clinical+lab happy path, denial-before-delegation, hierarchy bypass, grants, revocation, tenant/org/facility/patient violations, caller-claim forgery prevention, unguarded-write invisibility, generic error body. |
| **Total** | **62** | (target was ≥ ~30) |

Report — `GOVERNANCE/PRODUCTION_READINESS/WS_A_AUTHORIZATION_REPORT.md` (this file).

---

## 3. Design summary

- **Authority.** `AuthorizationEngine` is the only permission authority. `Principal` deliberately has **no grants field** — grants and revocations can only come from the engine registry, so a caller cannot forge a grant by constructing a principal.
- **Exact RBAC, no hierarchy.** `ROLE_PERMISSIONS` is derived mechanically from `AUTHORIZATION_BOUNDARIES`: `viewer` = 11 reads, `clinician` = 7 clinical writes, `lab_technician` = 4 lab writes, `admin` = 0 permissions unless explicitly granted. Adding a second role never inherits unrelated permissions.
- **Rule order** (first match wins): unknown action / no policy → DENY; unauthenticated → DENY; cross-tenant → DENY; active revocation → DENY; missing permission → DENY; absent/out-of-scope organization → DENY; absent/out-of-scope facility → DENY; patient scope missing/mismatched → DENY; otherwise explicit ALLOW.
- **Generic denials.** Every public denial reason is the single constant `authorization denied for this operation`. The internal `PolicyId` is recorded in the audit record and on `AuthorizationDenied.decision`, but is never in the serialized error body (`code`, `message`, `details={}` only). Cross-tenant probes of an existing vs. a random id produce an identical reason and never look up the resource.
- **Resource-level evaluation.** Reads obtain tenant/org/facility/patient attributes only from `ResourceAttributeIndex`, which is populated exclusively by guarded writes. The facade has no read parameter for scope claims; unguarded direct-service writes are never indexed and are therefore denied on read.
- **Audit.** SHA-256 over `sort_keys`/compact/ASCII canonical JSON plus predecessor hash, chained from `SYN-GENESIS`. Records are frozen dataclasses; the log exposes only tuple snapshots and has no remove/clear/pop/update/insert surface. Verification detects edited fields, replaced hashes, removed records and reordered records.
- **Wiring.** `build_authorized_context(identity)` constructs `ClinicalContext(identity)`, `LabWorkflowService(identity=identity)` and `AuthorizationEngine()` behind the guard. Nothing registers a route or touches production startup.

---

## 4. Requirement coverage (all 10)

| # | Requirement | How enforced | Test evidence (representative) |
|---|---|---|---|
| 1 | Deny by default | Any action without a declared `AUTHORIZATION_BOUNDARIES` entry → `DENY_NO_POLICY`; no-role/no-grant principal denied on every operation | `test_unknown_injected_action_is_denied_with_no_policy`, `test_authentication_alone_never_creates_a_policy`, `test_authenticated_principal_with_no_role_or_grant_is_denied` |
| 2 | Tenant isolation | Exact `principal.tenant_id == resource.tenant_id` before any lookup; generic reason for existing and random ids | `test_cross_tenant_access_is_denied`, `test_cross_tenant_probe_cannot_discover_existence`, `test_cross_tenant_denial_reason_is_generic_and_discloses_nothing` |
| 3 | Organization / facility scoping | Absent attribute → `DENY_MISSING_ATTRIBUTE`; out-of-scope → `DENY_ORG_SCOPE` / `DENY_FACILITY_SCOPE` | `test_missing_organization_attribute_is_denied`, `test_out_of_scope_organization_is_denied`, `test_organization_scope_violation_prevents_facility_creation`, `test_facility_scope_violation_prevents_encounter_creation` |
| 4 | Practitioner RBAC + grants, no hierarchy escalation | Exact role map; grants are authoritative and principal-bound; admin holds nothing by default; second role does not inherit | `test_admin_role_does_not_implicitly_inherit_every_permission`, `test_adding_a_second_role_does_not_inherit_unrelated_permissions`, `test_grant_to_another_principal_does_not_apply`, `test_role_hierarchy_bypass_is_denied_on_lab_write`, `test_direct_grant_enables_write_without_role_escalation` |
| 5 | Patient-context restrictions | Patient-scoped actions (and any resource carrying a `patient_ref`) require an explicit matching `patient_scopes` member; wildcard rejected | `test_patient_scoped_action_denied_without_any_patient_scope`, `test_patient_scope_mismatch_is_denied`, `test_wildcard_patient_scope_is_not_representable`, `test_patient_scope_violation_prevents_observation_recording`, `test_patient_scope_violation_prevents_reading_another_patients_encounter` |
| 6 | Resource-level evaluation | Reads use `ResourceAttributeIndex` populated only by guarded writes; no caller scope parameters; unguarded writes invisible | `test_reads_use_authoritative_attributes_not_caller_claims`, `test_direct_service_write_is_not_indexed_and_cannot_be_read_via_guard`, `test_patient_attribute_on_non_patient_action_still_requires_scope` |
| 7 | Revocation registry with expiry | Principal / role / permission scopes; active revocations override grants regardless of timing; expired revocations stop applying; expired grants stop applying | `test_principal_revocation_overrides_an_existing_grant`, `test_principal_revocation_registered_before_grant_still_denies`, `test_permission_revocation_overrides_a_direct_grant`, `test_expired_revocation_no_longer_denies`, `test_expired_grant_no_longer_allows`, `test_revoked_principal_cannot_reuse_an_existing_grant` |
| 8 | Frozen hash-chained audit + verification | Frozen records, canonical JSON SHA-256 chain, tuple snapshots, no mutation API, full `verify()` | `test_pristine_chain_verifies`, `test_tampered_field_is_detected`, `test_replaced_hash_is_detected`, `test_removed_record_is_detected`, `test_reordered_records_are_detected`, `test_append_only_log_has_no_mutation_surface`, `test_every_guard_denial_is_audited_and_chain_stays_valid` |
| 9 | No implicit permissions from authentication | `authenticated=False` → `DENY_UNAUTHENTICATED` even with valid role and scopes; authentication alone never creates a policy | `test_unauthenticated_principal_denied_even_with_valid_role_and_scope`, `test_no_authentication_grants_zero_permissions_at_the_facade`, `test_unauthenticated_with_valid_role_and_scope_still_denied` |
| 10 | Generic, non-leaking denials | One public reason for all denial types; policy id only internal/audited; no existence or ownership disclosure | `test_all_denial_types_use_the_same_generic_public_reason`, `test_cross_tenant_denial_reason_is_generic_and_discloses_nothing`, `test_authorization_denied_public_error_body_is_generic` |

---

## 5. Verification commands and exact results

All commands executed from the working tree in its uncommitted state.

**Focused authorization suite (62 tests)**

```
cd /home/samertts/workspace/projects/gula-integration/backend
ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. \
  /tmp/opencode/mpi-venv/bin/python -m pytest tests/health_core/test_authorization*.py -q --tb=short
```
→ `62 passed, 1 warning in 0.72s` (warning is the pre-existing Starlette/TestClient `httpx` deprecation notice, unrelated to this workstream).

**Ruff**

```
cd /home/samertts/workspace/projects/gula-integration
/tmp/opencode/mpi-venv/bin/python -m ruff check \
  backend/app/health_core/authorization backend/tests/health_core/test_authorization*.py
```
→ `All checks passed!`

**Mypy**

```
cd /home/samertts/workspace/projects/gula-integration
MYPYPATH=backend /tmp/opencode/mpi-venv/bin/python -m mypy \
  --config-file pyproject.toml backend/app/health_core/authorization
```
→ `Found 2 errors in 1 file (checked 6 source files)`. Both errors are **pre-existing and outside this workstream's scope**: `backend/app/domain/order_state.py:63` and `:81` (`no-untyped-def`). **Zero errors are attributable to any file in `backend/app/health_core/authorization/`.**

**Static quality gate (no stubs / no literal fake-success returns)**

```
... python -m pytest tests/health_core/test_quality_review_static.py -q --tb=short
```
→ `18 passed, 1 warning in 3.58s`.

**Full synthetic Health Core suite**

```
... python -m pytest tests/health_core -q --tb=line
```
→ `3 failed, 550 passed, 1 warning in 6.89s` (553 collected).

The 3 failures are **pre-existing and unrelated to authorization**; each was confirmed to fail in isolation in a fresh process that does not collect any `test_authorization*.py` file:

| Failing test | Cause | Independence evidence |
|---|---|---|
| `test_client_integration_manifests.py::test_claiming_an_absent_or_partial_layer_implemented_fails_closed` | Test expects error code `IMPLEMENTATION_STATUS_MISMATCH`; implementation emits `LAYER_STATUS_MISMATCH` | Fails identically when that file alone is run; file contains no `authorization` reference |
| `test_reliability_audit.py::test_reordering_is_detected` | Test expects `OUT_OF_ORDER`/`BROKEN_LINK`; implementation reports `GENESIS_MISMATCH` | Fails identically in isolation; file contains no `authorization` reference |
| `test_reliability_performance.py::test_injected_deterministic_clock_produces_exact_durations` | Floating-point accumulation: `1.0000000000000009 != 1.0` | Fails identically when run alone; pure float arithmetic, no authorization involvement |

Two further manifest tests observed failing in an earlier full run (`test_tampered_observation_is_detected`, `test_unobserved_or_duplicate_platform_manifests_fail_closed`) pass in isolation and when the final suite was re-run — they are pre-existing order-dependent tests, again with no authorization import. None of these failures was modified, skipped, xfailed, or weakened; they are outside this workstream's write ownership and are handed off in §8.

**End-to-end smoke check (earlier in this workstream):** a guarded clinical+lab path (encounter → order → specimen → collect → receive → result → verification) completed with all decisions `ALLOW` and `verify() → AuditVerification(is_valid=True, errors=(), records_checked=11)`.

---

## 6. Defects found and fixed during verification

All fixes are in this workstream's own files; no test assertion was deleted, skipped, xfailed or weakened.

1. `test_patient_scoped_action_denied_without_any_patient_scope` used `Role.CLINICIAN`, which does not hold `ENCOUNTER_READ`; the engine correctly returned `DENY_MISSING_PERMISSION` before the patient-scope rule. Changed the fixture role to `Role.VIEWER` so the test actually exercises the patient-scope rule.
2. `test_organization_scope_violation_prevents_facility_creation` tried to register `OTHER_ORG` using a principal scoped only to `ORG`, so it was denied at registration. Added a dedicated `OTHER_ORG`-scoped `CLINICIAN` principal for the setup write, then attempted the facility creation with the original principal to exercise the intended `DENY_ORG_SCOPE`.
3. `test_every_guard_denial_is_audited_and_chain_stays_valid` assumed the audit log started empty, but `seed()` legitimately appends 3 ALLOW records. The test now captures a baseline count and asserts the 3 post-seed records are denials — same intent, accurate premise.
4. `test_denials_are_audited_with_their_internal_policy_id` used `ENCOUNTER_READ` without a patient scope, which correctly denies. Changed the first evaluation to `PRACTITIONER_READ`, a genuinely allowed non-patient read, preserving the ALLOW→DENY chain intent.
5. `_is_expired` used a literal `return True` for malformed expiries, which the repository's static quality gate classifies as a fake-success return. Replaced with a `datetime.min` fail-closed sentinel so the result is computed by the same comparison as well-formed expiries — identical behavior, no literal success return.
6. Ruff findings resolved: `SIM102` (combined patient-scope condition), `I001` (import order in `errors.py`), `F401` (unused `Permission` import), `RUF022` (sorted `__all__`), `UP040` (PEP 695 `type Action = ...`).

---

## 7. Limitations (explicit, not hidden)

- The engine, grants, revocations and audit log are **in-memory and process-local**. They are not persisted across restarts and are not shared across workers. This is appropriate for the synthetic slice only.
- The audit chain is **tamper-evident, not tamper-proof** against code running in the same process with direct access to the record list; there is no external append-only store or signature.
- Grants and revocations are seeded programmatically through the engine API. No management UI/API, approval workflow, or persistence is provided.
- Authorization is enforced only for callers that go through `AuthorizedHealthCore`. Code that calls the wrapped clinical/lab services directly bypasses it by design; the guard's attribute index simply has no record of such writes (covered by `test_direct_service_write_is_not_indexed_and_cannot_be_read_via_guard`).
- Only opaque `SYN-` identifiers are accepted; there is no real identity, NHID, tenant registry or national deployment integration, and none was bypassed.
- Evaluation is synchronous with no shared cross-thread state guarantees beyond each engine instance; no concurrency stress test is included in this workstream.
- **No production activation:** no route, router, factory/main change, DDL, migration, schema change or deployment change was made. This closes the *synthetic-slice* finding F-02 only; it does not authorize or implement activation of the national platform.

---

## 8. Handoff requests / next steps (owner decisions required)

1. **Independent review** of the F-02 closure: confirm the 62 adversarial tests and the rule order in §3 satisfy the reviewer, and record the disposition in `GOVERNANCE/ACCELERATION/`.
2. **No promotion.** Keep `GOVERNANCE/FINAL_DECISION.md` at **HOLD** (md5 `effdfeaf10234678d83b2668c4489552`) and the MPI verdict at **REJECT** until their own gates are met by their owners. This report does not change either.
3. **Production wiring is out of scope** and requires an explicit owner decision: persistence for grants/revocations and audit, external audit anchoring, and controlled integration into a request pipeline. Nothing in this workstream should be treated as an activation step.
4. **Baseline failures to triage (not this workstream):** the 3 pre-existing failures in §5 should be assigned to their respective client-integration, reliability-audit and reliability-performance owners. The order-dependent manifest failures should also be stabilized by their owner. They are unchanged by WS-A.
5. **Verification hygiene:** because this shared working tree contains concurrent uncommitted work from other workstreams, re-run the focused authorization command in §5 as the authoritative WS-A gate; the full-suite count may change as other work lands, but the WS-A scope is the 62 authorization tests plus the static gate.

---

**Bottom line:** Workstream A implements and verifies runtime RBAC/ABAC enforcement for the synthetic Health Core slice (62 adversarial tests pass; ruff clean; no new mypy errors; static quality gate passes). It closes F-02 for that slice only. It does **not** lift the HOLD, does **not** change the MPI REJECT verdict, and does **not** activate any production surface.

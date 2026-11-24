# Independent Verification — Team C — Tier B (GULA-MASTER-AUTH-2026-11-19 §5)

- **Report timestamp:** 2026-11-19T09:38:19Z
- **Verifier:** Independent Verification Team C — **fresh context**; no code in this scope was authored by this verifier.
- **Posture:** fail-closed / adversarial. The working tree was treated as read-only. No source, test, or config file was modified, staged, committed, pushed, or merged. Sibling repo `gula-platform` was not written to. No operational DB, Redis, patient data, or external network integration was used.
- **Repo / branch:** `gula-integration` @ `integration/gula-unification-v1`, HEAD `2206654d` (working tree: many uncommitted changes + staged renames; untouched by this review).
- **Pinned interpreter:** `/home/samertts/workspace/projects/gula-platform/backend/.venv/bin/python` (Python 3.12.13).
- **Scope:** B1 (PHI permission map), B2 (consent / break-glass), B3 (verified guardian / minor / NHID), B5 (delegation), plus the specific "drift fix" fact regarding `20261119_0002`.

> **No production, legal, clinical, or operational-readiness claim is made by this report.** `PRODUCTION READY` is explicitly not awarded. All findings are engineering-scope observations from code inspection and disposable SQLite fixtures.

---

## 1. Executive verdict

| Control | Verdict (exclusive vocabulary) | One-line basis |
|---|---|---|
| **B1** — centralized PHI permission map | **INDEPENDENTLY VERIFIED** (engineering scope) | Single policy map; canonical `phi_permission_conflict` enforcement confirmed; no second engine, no new role/permission catalog entries; 0 real bypasses found. **Integration residual risk** noted below (map emits keys absent from the seeded catalog → fail-closed denial in a real deployment). |
| **B2** — separate consent / break-glass, fail-closed | **INDEPENDENTLY VERIFIED** (engineering scope) | Header is intent-only; server-verified, subject-bound, active/unexpired/non-deactivated session required; forged/expired/deactivated/wrong-subject/other-actor/non-read all DENY; consent/break-glass separation confirmed. 0 real bypasses found. |
| **B3** — verified guardian / minor / NHID | **INDEPENDENTLY VERIFIED** (engineering scope) | Age server-derived from DOB; 90-day near-majority gate; canonical NID normalization/hash only, no NHID minted; twin-merge and authorized-verifier gates present; additive deny-only gate in `_relationship_allows`. 0 real bypasses found. |
| **B5** — delegation only into canonical authority | **BLOCKED** | **1 real escalation bypass** (narrow-delegation holder can re-delegate a role permission they do not themselves hold) + **not wired into production** (live route uses the legacy, ungoverned service writing a different table). Details in §4. |

**Result: 0 real bypasses in B1/B2/B3; 1 real bypass in B5. No control is awarded `PRODUCTION READY`.**

---

## 2. Exact commands and recorded output

### 2.1 Focused test command (as specified)

```
cd /home/samertts/workspace/projects/gula-integration/backend && ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. /home/samertts/workspace/projects/gula-platform/backend/.venv/bin/python -m pytest tests/unit/test_b4_cross_account_security.py tests/unit/test_b1_phi_permission_map.py tests/test_consent.py tests/unit/test_b3_verified_guardian.py tests/unit/test_b5_delegation.py tests/identity/test_authorization_phase7.py tests/identity/test_authorization_phase8.py tests/health_core/test_authorization_synthetic_scope.py tests/test_citizen_relationship_workflow.py tests/unit/test_nhid_readiness.py tests/unit/test_niam_step_up.py -q
```

Output (verbatim tail; exit code recorded explicitly):

```
============================= test session starts ==============================
platform linux -- Python 3.12.13, pytest-9.1.1, pluggy-1.6.0
rootdir: /home/samertts/workspace/projects/gula-integration/backend
configfile: pytest.ini
plugins: anyio-4.14.2, asyncio-1.4.0, Faker-40.36.0, xdist-3.8.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
collected 226 items

tests/unit/test_b4_cross_account_security.py ........................    [ 10%]
tests/unit/test_b1_phi_permission_map.py .............                   [ 16%]
tests/test_consent.py ..........................                         [ 27%]
tests/unit/test_b3_verified_guardian.py ................................ [ 42%]
.........                                                                [ 46%]
tests/unit/test_b5_delegation.py ..........................              [ 57%]
tests/identity/test_authorization_phase7.py .....                        [ 59%]
tests/identity/test_authorization_phase8.py ...................          [ 68%]
tests/health_core/test_authorization_synthetic_scope.py .......          [ 71%]
tests/test_citizen_relationship_workflow.py .....                        [ 73%]
tests/unit/test_nhid_readiness.py .......................                [ 83%]
tests/unit/test_niam_step_up.py .....................................    [100%]

=============================== warnings summary ===============================
../../gula-platform/backend/.venv/lib/python3.12/site-packages/fastapi/testclient.py:1
  /home/samertts/workspace/projects/gula-platform/backend/.venv/lib/python3.12/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
================== 226 passed, 1 warning in 171.14s (0:02:51) ==================
EXIT_CODE=0
```

Note: a green suite is **necessary but not sufficient**; the bypass in §4 is not covered by any of these 226 tests.

### 2.2 Ruff on the Tier B scope

```
cd /home/samertts/workspace/projects/gula-integration/backend && <pinned python> -m ruff check \
  app/identity/services/phi_permission_map.py app/security/break_glass_guard.py \
  app/security/consent_dep.py app/routes/authorization.py \
  app/identity/services/verified_guardian_guard.py app/identity/services/delegation_service.py \
  app/identity/services/authorization_service_v2.py app/identity/services/authorization_decision.py \
  app/identity/models/delegation.py app/identity/models/__init__.py \
  migrations/versions/20261119_0002_niam_delegations.py \
  tests/unit/test_b1_phi_permission_map.py tests/unit/test_b3_verified_guardian.py \
  tests/unit/test_b5_delegation.py tests/test_consent.py
```

Result:

```
All checks passed!
RUFF_EXIT=0
```

### 2.3 Adversarial probes (written to `/tmp/opencode/tierC_probe_*.py`, never to the repo)

- `/tmp/opencode/tierC_probe_metadata.py` — structural verification of the drift fix (§5). Exit 0.
- `/tmp/opencode/tierC_probe_b5_escalation.py` — reproduced the real B5 escalation (§4.1). Exit 0.
- `/tmp/opencode/tierC_probe_b5_transitive.py` — confirmed transitive-revocation residual risk (§6). Exit 0.

No disposable PG database was required: the drift-fix facts (§5) were verified deterministically from ORM metadata and the migration source (AST), and a real Alembic round-trip would not change the security conclusions. The `gula` operational DB was not touched.

---

## 3. Per-control independent findings

### B1 — centralized per-action PHI permission map — **INDEPENDENTLY VERIFIED**

Inspected `app/identity/services/phi_permission_map.py` and its enforcement site `app/identity/services/authorization_decision.py::_evaluate` (lines 286–295).

- One centralized policy table (`PhiAction`, `PHI_RESOURCE_TYPES`, `PHI_ACTIONS`, `resolve_phi_permission`); all 8 actions (`read/create/update/delete/export/print/share/administrative`) distinct; `administer` alias present.
- Unmapped action / non-PHI resource → `None` (map itself fails closed).
- Enforcement is exclusively in the canonical authority: for a PHI resource the map-derived key overrides/substitutes the caller key, and a caller-supplied conflicting key yields `AuthorizationReason.phi_permission_conflict` (line 292). Verified via my own reading and the committed parametrized escalation tests (`test_b1_phi_permission_map.py`).
- **No new authorization engine** and **no new role/permission catalog entries**: repository-wide search found no added role/permission seeds carrying PHI-style keys (`lab_result.*`, `patient_record.*`, …) — the only keys seeded remain the pre-existing `audit.*`, `security.incident.*`, `organization.*`, `compliance.*`, `patients.read`, `orders.read`, etc.
- 0 real bypasses found.

**Residual risk (not a bypass):** the map emits keys (e.g. `lab_result.read`, `patient_record.export`) that are **not present in the seeded `niam_permissions` catalog**. In a real deployment `_permission_exists()` (line 417–424) returns False and canonical PHI access is denied with `permission_unknown`. The B1 tests mock `_Db.scalar()` to always return a permission id, so this gap is invisible to them. Effect is fail-closed false-deny, not privilege grant — but it means B1's happy path is not functionally integrated with the real catalog.

### B2 — separate consent / break-glass, fail-closed — **INDEPENDENTLY VERIFIED**

Inspected `app/security/consent_dep.py`, `app/security/break_glass_guard.py`, `app/routes/authorization.py` activation/deactivation endpoints, and `tests/test_consent.py`.

- `X-Emergency-Access` is parsed only by `_emergency_header()` and is used **only** to choose the audit reason; access is granted only when `authorize_break_glass()` returns `allowed=True` based on a server-persisted `BreakGlassSession` (actor id, `status='active'`, `deactivated_at is None`, unexpired via `_as_utc`, sufficient justification, allowed category, and `session.patient_id ∈ resolve_subject_patient_ids(db, gpid)`).
- Adversarial cases all DENY (confirmed by committed tests + code reading): forged header with no session, ineligible role, expired session, deactivated row, `status != active`, too-short justification, invalid category, wrong-subject binding, another actor's session, non-`read:` scope.
- Consent and break-glass are separate: `test_break_glass_never_creates_consent` passes; break-glass never writes a `Consent` row and consent never activates break-glass.
- Iraqi legal categories are explicitly declared as **POLICY DEPENDENCIES** in `break_glass_guard.py` (§6, docstring lines 22–25, `ALLOWED_EMERGENCY_CATEGORIES`); no legal entitlement is fabricated from missing config.
- Activation route ownership checks prevent cross-actor deactivation (lines 456–459).
- 0 real bypasses found.

**Residual risk (not a bypass):** `BreakGlassActivateRequest.emergency_category` pattern (`clinical|technical|security|compliance|system_failure`) only intersects the guard's `ALLOWED_EMERGENCY_CATEGORIES` on `system_failure`; all other activation attempts through that route are rejected (403). Fail-closed, but functionally narrow.

### B3 — verified guardian / minor / NHID — **INDEPENDENTLY VERIFIED**

Inspected `app/identity/services/verified_guardian_guard.py`, canonical `CitizenRelationshipWorkflow` (`app/identity/services/citizen_relationship_service.py`, exercised via `tests/test_citizen_relationship_workflow.py` and B3 tests), and `AuthorizationDecisionService._relationship_allows` (lines 426–472).

- Age is derived server-side from `Citizen.date_of_birth` (`derive_age`, `age_transition`) — no client `is_minor` flag is consumed. Missing/future/implausible DOB fails closed.
- 90-day near-majority re-verification: `age_transition` marks age-17 within `REVERIFICATION_WINDOW_DAYS=90`; `evaluate_guardian_access` denies `near_majority` unless `reverified_at_transition=True`.
- NHID: only the canonical `normalize_national_id` / `hash_national_id` input contract is used; raw NID is never persisted (B3 test asserts raw NID absent from relationship metadata); no canonical NHID is minted.
- Twins-never-merged (`assert_no_twin_merge`) and authorized-verifier gate (`is_authorized_verifier_role`, workflow rejects `role='citizen'`) are present and tested.
- `guardian_relationship_permits` is invoked as an **additional** `continue` (deny-only) inside `_relationship_allows` before the pre-existing `relationship.allows(...)` check — it cannot grant authority a relationship did not already have. Scope wildcards (`*`) are rejected. Canonical `GuardianRulesService` is reused.
- 0 real bypasses found.

**Residual risk (not a bypass):** `guardian_relationship_permits` calls `evaluate_guardian_access` without passing `reverified_at_transition`, so it defaults to `False` — near-majority guardians are effectively always denied through the canonical adapter even after a legitimate re-verification (fail-closed false-deny). Where the re-verification flag is supplied in a real flow is not established by the code reviewed.

### B5 — delegation only into canonical authority — **BLOCKED**

Inspected `app/identity/models/delegation.py`, `app/identity/services/delegation_service.py`, `app/identity/services/authorization_service_v2.py`, `app/routes/authorization.py`, `app/services/authorization_service.py`, and the migration. See §4 for the real bypass and integration gap. Subset/scope/duration/depth(3)/self-delegation/audit/revocation are individually implemented and tested for the *simple* cases, but the "cannot escalate" invariant fails for re-delegation of a narrow grant, and the control is not wired to production.

---

## 4. Real bypasses (with concrete reproductions)

### 4.1 REAL BYPASS — B5 authority laundering via narrow-delegation re-delegation (escalation)

- **Severity:** HIGH (logic-level privilege escalation; current HTTP reachability is limited — see note).
- **Location:** `backend/app/identity/services/delegation_service.py`
  - Lines 185–206: `permission_keys` are validated only as a subset of the **role's active catalog** (`allowed_keys`), never against the **actor's own effective permissions**.
  - Lines 208–218 / 233–274: `_holding()` treats *any* active receipt of the role as "holding the role" (role-level), then grants a new delegation with `new_depth = depth + 1` without checking that the actor actually holds the specific `permission_keys` being delegated.
- **Reproduction** (`/tmp/opencode/tierC_probe_b5_escalation.py`, disposable SQLite, committed test fixtures reused verbatim):
  1. Create role R with permissions A=`lab_result.read`, B=`lab_result.export`, both active.
  2. Give actor X a **narrow** delegation of R containing only A (depth 1, active), and remove X's direct role assignment.
  3. Confirm `RolePermissionService.effective_permissions(X)` = `{lab_result.read}` — X **does not hold B**.
  4. Call `DelegationService.delegate_role(actor_id=X, delegate_account_id=Y, role_id=R, permission_keys=[B], duration_hours=24, reason="...")`.
- **Observed:** call **succeeds**; a depth-2 delegation of `lab_result.export` is created for Y; `RolePermissionService.effective_permissions(Y)` = `{lab_result.export}`.
- **Expected (fail-closed):** DENY — X cannot grant a permission it does not itself hold; "permission subset (cannot escalate)" requires the delegated set to be a subset of the actor's *effective* permissions, not merely of the role catalog.
- **Why not a fixture artifact:** the probe executes the real `DelegationService` and real `RolePermissionService` against real NIAM model metadata on SQLite; identical behavior follows on PostgreSQL. The narrowed-delegation state is first-class (the committed happy-path test itself creates a subset delegation).
- **Reachability note:** no production route currently calls this B5 `DelegationService` (see §4.2); the bypass is reachable from any internal caller / future route wiring. It nonetheless violates the stated invariant of the control itself.
- **Remediation:** in `delegate_role`, intersect `permission_keys` with the actor's own `effective_permissions(account_id=actor_id, organization_id=..., scope=...)` (and, for a delegation-based holding, with the received delegation's `permission_keys`) and reject any key not held; add a regression test for the narrow-delegate re-delegation case.

### 4.2 INTEGRATION GAP — B5 canonical delegation is not wired to production; live route uses the ungoverned legacy service

- **Severity:** HIGH (the invariant "delegation only into canonical authority" is not realized at the HTTP boundary).
- **Evidence:**
  - `backend/app/routes/authorization.py` lines 17–29 and 345–359: `POST /authz/delegations` imports and calls **`app.services.authorization_service.DelegationService.create_delegation`**, which writes the legacy `Delegation` model (integer user ids, table `delegations`) with **no** subset/scope/depth/self-delegation/role-holding/audit validation (see `app/services/authorization_service.py` lines 888–934).
  - `backend/app/identity/services/delegation_service.py::DelegationService` (the B5 service) is imported only by `tests/unit/test_b5_delegation.py` (and constants by `authorization_service_v2.py`). It is not referenced by any route or DI wiring.
  - The canonical consumer `RolePermissionService.effective_permissions()` (`authorization_service_v2.py` lines 246–268) reads **`niam_delegations`**, not the legacy `delegations` table. Therefore the live API's delegations are invisible to canonical authorization, and nothing in the running app writes the table that canonical authorization consumes.
- **Observed vs expected:** expected — the single canonical delegation path governs all delegation creation/audit/revocation and feeds `effective_permissions`; observed — two disconnected systems, the governed one dormant outside tests.
- **Remediation:** route `POST /authz/delegations` (and revoke/list) through the canonical B5 `DelegationService` with account-based ids; retire or explicitly gate the legacy service; add an end-to-end route test proving a created delegation changes `effective_permissions`.

Neither finding is a "synthetic-fixture artifact": both are properties of the production code paths, demonstrated with disposable data.

---

## 5. Specific new fact to verify — drift fix for `20261119_0002`

All three sub-claims verified independently (probe `/tmp/opencode/tierC_probe_metadata.py`, exit 0):

**(a) `niam_delegations` is now in `IdentityBase.metadata` — CONFIRMED.**
- `app/identity/models/__init__.py` line 41: `from .delegation import DelegationStatus, NiamDelegation`; `__all__` includes `NiamDelegation` (line 128) and `DelegationStatus` (line 93).
- Probe output: `niam_delegations in IdentityBase.metadata: True`; `NiamDelegation.__table__ name: niam_delegations`.

**(b) Migration creates/drops matching index names; no new drift beyond baseline uuid churn — CONFIRMED (with one documented baseline-level nuance).**
- ORM composite indexes: `ix_niam_delegations_delegate` (delegate_account_id, status) and `ix_niam_delegations_role` (role_id, status).
- Migration `20261119_0002` creates exactly those two composites (lines 74–85) and drops them symmetrically in `downgrade()` (lines 91–92). The single-column loop uses the identical tuple in both directions (`uuid, delegator_account_id, delegate_account_id, role_id, organization_id, facility_id, department_id, unit_id, workspace_id, expires_at, status`). No `remove_table`, no `alter_column`, and no drop of any pre-existing column; `upgrade()` is guarded by `_has_table` and `downgrade()` drops only this table.
- Nuance: the ORM declares `ix_niam_delegations_uuid` as a UNIQUE index (`unique=True, index=True` on the `uuid` column), while the migration creates a **non-unique** `ix_niam_delegations_uuid` plus a separate `uq_niam_delegations_uuid` unique constraint. I confirmed this is the **repo-wide baseline pattern**, not drift introduced by this fix: migration `20261119_0001` (and `20260814_0005`) use the identical "unique constraint + non-unique `ix_*_uuid` loop index" idiom. This falls within the "repo-wide generic VARCHAR/uuid index churn already at baseline" carve-out in the directive.

**(c) The fix introduced no security regression — CONFIRMED.**
- The fix is purely registration (adding the import + `__all__`) plus index-name renames in DDL. It changes no permission logic, no query predicate, and no authorization decision. Registration makes metadata reflect the already-existing table (it does not grant authority). `effective_permissions()` imports `NiamDelegation` directly from `app.identity.models.delegation`, so its behavior is independent of `__init__.py` registration. The 226-test suite is green with the fix in place.

---

## 6. Residual risks / hardening gaps (not classified as real bypasses)

1. **B1 catalog gap:** PHI map keys are absent from the seeded `niam_permissions` catalog → canonical PHI decisions deny with `permission_unknown` in a real deployment; B1's allow-path is validated only against a mocked DB. (Fail-closed; functional/integration defect.)
2. **B2 category pattern mismatch:** activation route allows categories the guard rejects (only `system_failure` overlaps) → most break-glass activations fail. (Fail-closed; functional defect.)
3. **B3 near-majority re-verification flag:** `guardian_relationship_permits` never supplies `reverified_at_transition`, so near-majority guardians are always denied via canonical auth even post re-verification. (Fail-closed; functional defect / unclear production re-verification flow.)
4. **B5 transitive revocation:** confirmed by `/tmp/opencode/tierC_probe_b5_transitive.py` — after revoking the delegator's own direct role assignment, the delegate **retains** the delegated permission (`effective_permissions` does not verify the delegator's current holding at enforcement time; `authorization_service_v2.py` lines 246–268). The directive's "revocation (immediate effect)" works for revoking the delegation itself, but upstream authority loss does not propagate. Recommend checking the delegator chain in `effective_permissions` or cascading revocation.
5. **B5 legacy surface:** the legacy `delegations` table/service remains reachable at `/authz/delegations` with no governance (see §4.2); treat as active attack surface until retired.
6. **Owner bypass provenance (B2 adjacent):** `consent_dep._is_owner` trusts `getattr(current_user, "citizen_ulid", None)`. The code comment states this is populated from a JWT claim "when the citizen portal authenticates them." I did not find the production code that sets this attribute in the reviewed paths; if any client-controlled path can set `citizen_ulid`, it would allow owner-bypass for arbitrary subjects. Flagged for follow-up verification (not confirmed here).

---

## 7. Scope / non-claims

- This is an **engineering-scope** independent verification only.
- **No PRODUCTION READY verdict is awarded** (and none is permitted under this engagement). Operational deployment, Ministry/legal ratification of Iraqi emergency categories, clinical safety sign-off, and production data/DR gates are **outside this scope** and are explicitly not claimed.
- Statuses above use only the permitted vocabulary: `IMPLEMENTED / TESTED / INTEGRATED / INDEPENDENTLY VERIFIED / PRODUCTION READY / BLOCKED / NOT IMPLEMENTED`.
- Verification was performed fresh-context and independently; no implementer claim was accepted without code/test evidence.
- Only this report file was written in the repository; no other repo file was modified.

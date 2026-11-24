# Final Report 07 — Consolidated Adversarial Review, Defect Register, Regression Inventory, Blocker Matrix & Demo

**Report ID:** PR-FINAL-07 · **Date:** 2026-11-18 · **Data class:** SYNTHETIC ONLY
**Governing decision:** HOLD / REJECT unchanged. This report is an evidence compilation, not a release claim.

## 1. Consolidated adversarial review

Two independent adversarial reviews were commissioned after the six workstreams landed. Both used different techniques from the builders and produced strict, reproducible scratch reproductions.

| Review | Source | Severity distribution | Disposition |
|---|---|---|---|
| Correctness | `ADVERSARIAL_REVIEW_CORRECTNESS.md` | 0 CRITICAL / **1 HIGH** / 3 MEDIUM / 1 LOW | All 5 fixed + re-verified |
| Security | `ADVERSARIAL_REVIEW_SECURITY.md` | 0 CRITICAL / 0 HIGH / 0 MEDIUM / **3 LOW** / **2 INFO** | All 5 fixed + re-verified |

**Total: 10 / 10 findings remediated, 0 deferred, 0 weakened assertions.** Every fix has a permanent strict repository regression test (§3).

### Exact findings and disposition

| ID | Sev | Finding (abridged) | Fix | Status |
|---|---|---|---|---|
| F-01 | HIGH | Event catalogue validation never enforced at emitters; real lifecycle events violated their own payload contract | `validate_domain_event()` in `_emit()` before append; real-context payloads for all six transitions | **CLOSED** |
| F-02 | MED | WAL tail truncation + re-checksum replayed silently | Authoritative `record_count`/`last_sequence` anchors sealed in envelope; replay rejects stale anchors | **CLOSED** |
| F-03 | MED | `AuditLog.verify()` self-referential; tail deletion invisible | Append-only head/count anchors; tail deletion → `COUNT_MISMATCH`; honest docstring | **CLOSED** |
| F-04 | MED | `validate_all_manifests()` ignored its `observations` argument | Resolve observation per platform; pass `observation=`; fail-closed once on missing | **CLOSED** |
| F-05 | LOW | `_check_key()` accepted any non-empty string | `require_synthetic_id(key, field="key")` | **CLOSED** |
| L-1 | LOW | Facade exposed unwrapped `clinical`/`lab` services (bypass) | Private `_clinical`/`_lab`; strict no-public-bypass test | **CLOSED** |
| L-2 | LOW | Engine tenant equality trusted caller tenant on indexed reads | Index authoritative for `tenant_id`; mismatched caller denied `DENY_TENANT` + audited | **CLOSED** |
| L-3 | LOW | Audit docstring overclaimed tamper detection | Exact limits documented; limitation tests added | **CLOSED** |
| I-1 | INFO | `is_synthetic_id` docstring overclaimed proof of generation | Docstring corrected to shape check; strict validators remain separate; regression added | **CLOSED** |
| I-2 | INFO | `OperationOutcome.diagnostics` echoed raw `details` | Allowlist + `html.escape(..., quote=True)`; identifier keys dropped | **CLOSED** |

**Note on the two "coherent forgery" limitations (F-03 / L-3):** these are deliberately NOT "fixed" by pretending to add security that does not exist. They are documented precisely and locked in by tests that assert the limitation (`ok is True` after a full consistent rehash). Upgrading them requires an external keyed/durable anchor — a persistence/owner decision. This is honest classification, not an open defect.

## 2. Defect register

| Defect | Raised by | Severity | Verification evidence | Classification |
|---|---|---|---|---|
| F-01 | Correctness review | HIGH | 40 focused event tests; full suite 773; `FINAL_02` | VERIFIED FIXED |
| F-02 | Correctness review | MEDIUM | 26 reliability tests; `FINAL_06` | VERIFIED FIXED |
| F-03 | Correctness review | MEDIUM | 26 reliability tests; limitation test-locked | VERIFIED FIXED (limit disclosed) |
| F-04 | Correctness review | MEDIUM | 30 client tests; `FINAL_05` | VERIFIED FIXED |
| F-05 | Correctness review | LOW | 26 reliability tests; `FINAL_06` | VERIFIED FIXED |
| L-1 | Security review | LOW | 68 authorization tests; `FINAL_01` | VERIFIED FIXED |
| L-2 | Security review | LOW | 68 authorization tests; `FINAL_01` | VERIFIED FIXED |
| L-3 | Security review | LOW | 68 authorization tests; limitation test-locked | VERIFIED FIXED (limit disclosed) |
| I-1 | Security review | INFO | 27 event-semantics tests; `FINAL_02` §4 | VERIFIED FIXED |
| I-2 | Security review | INFO | 25 FHIR tests; `FINAL_03` | VERIFIED FIXED |

Earlier-cycle defects (cross-module event conformance 20/21 failing, `NOTE_ADDED` aggregate drift, dual error/idempotency documentation gap) remain closed as recorded in `GOVERNANCE/ACCELERATION/ACCELERATED_EXECUTION_REPORT.md` §8.

## 3. Scratch → repository regression inventory

The adversarial reviewers wrote 8 scratch reproduction files under `/tmp/opencode/prodready/review_{correctness,security}/`. Every reproducible finding was converted into a permanent strict test in the repository; scratch files remain outside the repo and add no repository surface.

| Scratch reproduction | Finding | Permanent repository regression test(s) |
|---|---|---|
| `review_correctness/test_adversarial_events.py::test_real_admitted_event_violates_catalogue`, `::test_real_lifecycle_events_all_fail_catalogue` | F-01 | `tests/health_core/test_cross_module_conformance.py::test_every_encounter_lifecycle_transition_emits_a_catalogue_valid_event` |
| `review_correctness/test_adversarial_events.py::test_production_emitters_never_call_validate_domain_event` | F-01 | `tests/health_core/test_event_semantics.py::test_emit_validates_against_catalogue_before_appending_to_the_sink` |
| `review_correctness/test_adversarial_fhir_ci.py::test_validate_all_manifests_ignores_passed_observations` | F-04 | `tests/health_core/test_client_integration_manifests.py` — custom WEB observation produces `LAYER_STATUS_MISMATCH` / `ABSENT_PROJECT_WITH_PRESENT_LAYER`; missing observation → `NO_OBSERVATION_FOR_PLATFORM` once |
| `review_correctness/test_adversarial_reliability.py::test_wal_tail_truncation_replays_silently` | F-02 | `tests/health_core/test_reliability_durable.py` — re-sealed truncated WAL → `ChecksumMismatchError`; legitimate restart recovers all keys |
| `review_correctness/test_adversarial_reliability.py::test_wal_middle_record_drop_is_detected` | F-02 control | `tests/health_core/test_reliability_durable.py` — middle-drop control rejected |
| `review_correctness/test_adversarial_reliability.py::test_audit_log_verify_cannot_detect_tail_deletion` | F-03 | `tests/health_core/test_reliability_audit.py` — anchored tail deletion → `COUNT_MISMATCH` |
| `review_correctness/test_adversarial_reliability.py::test_store_accepts_non_synthetic_key` | F-05 | `tests/health_core/test_reliability_durable.py` — non-SYN key → `InvalidSyntheticReferenceError` |
| `review_security/test_adv_guard.py::test_direct_wrapped_service_bypass_succeeds_and_writes` | L-1 | `tests/health_core/test_authorization_guard.py` — `not hasattr(guard, "clinical"/"lab")`; guarded write+read still works |
| `review_security/test_adv_guard.py::test_cross_tenant_read_with_own_tenant_id_is_blocked_at_service_layer` | L-2 | `tests/health_core/test_authorization_guard.py` — `AuthorizationDenied`/`DENY_TENANT`, audit carries stored tenant, legitimate read ALLOWs |
| `review_security/test_adv_audit.py::test_delete_last_record_detected`, `::test_recompute_hash_with_consistent_rewrite_detected_only_with_anchor` | L-3 | `tests/health_core/test_authorization_audit.py` — honest limitation tests (`ok is True`) + first-deletion detection |
| `review_security/test_adv_fhir.py::test_operation_outcome_includes_details_verbatim_characterisation` | I-2 | `tests/health_core/test_fhir_operation_outcome.py` — sanitised diagnostics, allowlist + escaping tests |
| (docstring audit) | I-1 | `tests/health_core/test_event_semantics.py::test_is_synthetic_id_is_a_shape_check_and_strict_validation_is_separate` |

Scratch reproductions that found **no** defect (e.g. `test_adv_auth_engine.py`, `test_adv_client_term.py`, `test_adv_fhir.py` identifier/type checks, `test_operation_outcome_all_error_codes_are_r4`, `test_terminology_unverified_not_valid`) are covered by existing strict repository tests; no source change was made for them.

## 4. Blocker matrix (all residual blockers are owner-gated)

| # | Blocker | Classification | Owner / gate | Changed by this program? |
|---:|---|---|---|---|
| 1 | Release / activation (`FINAL_DECISION.md` HOLD, MPI REJECT) | **BLOCKED** | Platform owner | No — md5s unchanged |
| 2 | Patient Master Record + cross-identity Patient Timeline | **BLOCKED** | MP-001, ODR-001…004, D-020/D-021, MPI REJECT | No — not implemented |
| 3 | F-01 event validation promotion blocker | **CLOSED** (promotion still HOLD-gated) | Lead remediation | Fixed this cycle |
| 4 | F-02 runtime RBAC/ABAC promotion blocker | **CLOSED** | WS-A remediation | Fixed earlier + hardened L-1/L-2 |
| 5 | F-03 real FHIR adapter promotion blocker | **CLOSED (local adapter)**; wire endpoint **NOT IMPLEMENTED** | WS-C / owner for wire | Adapter verified; endpoint absent by design |
| 6 | Terminology official releases / LOINC check-digit | **PARTIALLY VERIFIED / NOT IMPLEMENTED** | Owner + licensed data | No |
| 7 | Client platforms (web/android/flutter/desktop/expo) | **BLOCKED**; iOS **NOT IMPLEMENTED** | Client owner / checkout | No client tree modified |
| 8 | Schema / migration / DDL | **BLOCKED** | Migration owner | No migration proposal created |
| 9 | Durable keyed audit / WAL anchor | **PARTIALLY VERIFIED** | Persistence owner | Limits documented + test-locked |
| 10 | Production route wiring (`factory.py`/`main.py`) | **NOT IMPLEMENTED** | Platform owner | 0 health_core references — unchanged |

## 5. Reproducible demonstration (synthetic, no production activation)

```bash
cd /home/samertts/workspace/projects/gula-integration/backend
ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. \
  /tmp/opencode/mpi-venv/bin/python /tmp/opencode/prodready/demo_production_readiness.py
```

The script exercises real code from all six workstreams with `SYN-` fixtures only: WS-A runtime authorization (deny/allow/revoke/audit), WS-B event semantics (legacy + explicit lifecycle), WS-C FHIR round-trip + OperationOutcome, WS-D terminology validation, WS-E fail-closed client manifests, WS-F WAL/restart/backup/restore/audit/idempotency/retry/observability. Every step asserts its expected outcome; the script exits non-zero on any defect.

**Expected final line:**
```
DEMONSTRATION VERDICT: ALL SIX WORKSTREAMS EXECUTED — ASSERTIONS PASSED
```

The demo lives in `/tmp` so it adds no repository file; the same behaviour is permanently covered by `tests/health_core/` (773 tests).

## 6. Final verification snapshot

```bash
bash /tmp/opencode/prodready/integration_gate.sh   # 773 passed; ruff clean; mypy 2 pre-existing baseline errors only
bash /tmp/opencode/prodready/verify_final.sh       # 24/24 PASS — governance, preservation and ownership intact
```
Integrity: integration HEAD `2827c1ff…` unchanged · platform HEAD `f478676b…` status 0 · HOLD `effdfeaf…` · REJECT `1a02c015…` / `ea3969d0…` · 0 deletions · 20 staged baseline entries unchanged · 0 new migration artifacts · 0 `health_core` references in `factory.py`/`main.py`.

**End of final report 07. End of the eight-report classified final set.**

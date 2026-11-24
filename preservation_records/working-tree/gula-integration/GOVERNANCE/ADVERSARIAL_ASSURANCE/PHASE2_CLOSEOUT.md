# Phase 2 Tier A Closeout — Privacy / Security Remediation

**Artifact class:** Formal closeout record
**Repository:** `gula-integration` — branch `integration/gula-unification-v1`
**Audited HEAD:** `2206654dc713ea2de8c564a3207dfe05fde23549`
**Date:** 2026-11-19
**Gate for Tier B:** SATISFIED at engineering scope — all six Tier A fixes independently verified
by fresh-context Team C; all three corrected residuals subsequently **VERIFIED CORRECTED** by
focused Team C re-verification (`INDEPENDENT_VERIFICATION_TEAM_C_PHASE2_REVERIFY.md`).

## 1. Verdict

**PHASE 2 TIER A CLOSED AT ENGINEERING SCOPE.** All six HIGH-severity findings are
`IMPLEMENTED / TESTED` and `INDEPENDENTLY VERIFIED` (engineering scope only) by fresh-context Team C
(`INDEPENDENT_VERIFICATION_TEAM_C_PHASE2.md`). **No `PRODUCTION READY` awarded.** Owner-gated
decisions (HOLD, MPI REJECT, MP-001, ODR-001…004, D-020/D-021, ADR-A…J, AUD-02/07/16,
AUD-API-002, AUD-ARCH-003) remain untouched.

| Finding | Fix | Targeted evidence | Team C verdict |
|---|---|---|---|
| AUD-SEC-007 — async actor lock filter | Shared strict predicate for sync + async | 4 passed | `INDEPENDENTLY VERIFIED` |
| AUD-API-001 — standards endpoint 500 | Real accessors only; no invented data | 5 passed | `INDEPENDENTLY VERIFIED` |
| AUD-PRV-001 — NID cross-facility PHI | Lab-scoped lookup + non-identifying marker | 6 passed | `INDEPENDENTLY VERIFIED` |
| AUD-SEC-004 — Bearer logout revocation | Shared Bearer-or-cookie extraction + independent revocation of all presented credentials | 5 passed (incl. e2e 401) | `INDEPENDENTLY VERIFIED` (R-SEC-004-A corrected) |
| AUD-PRV-003 — force_create bypass | Elevated permission + reason + audit + NID 409 | 10 passed | `INDEPENDENTLY VERIFIED` |
| AUD-CLIN-003 — critical flag persistence | Persist flags/status; clear stale flags on re-validation | 4 passed | `INDEPENDENTLY VERIFIED` (R-CLIN-003-A corrected) |

## 2. Adversarial outcome (honest disclosure)

Fresh-context Team C re-ran all 32 new tests (32 passed), the 87-test combined targeted+neighbor
regression, Ruff on 13 files, and devised ~25 new adversarial probes. All six fixes survived.

Team C **successfully falsified three engineering claims** — all in the integrator's recording,
not the fixes: (1) `phase_b_gate.py` was 4 PASS/2 FAIL (not 6/6); (2) `national_integration_verify.py`
was verdict FAIL; (3) the earlier `4945 passed` full-suite claim was stale because the registry was
edited after that run. Single root cause: a non-canonical status annotation in
`status_registry.json → adversarial_assurance.phase2_tier_a.status`. Corrected by using the exact
canonical value `INDEPENDENTLY VERIFIED` and moving the annotation to `basis`. Both gates re-run
**PASS, exit 0**; the 3 registry tests pass. Full disclosure: `TEST_EVIDENCE_INDEX.md` §11.5.

Team C's focused re-verification (`INDEPENDENT_VERIFICATION_TEAM_C_PHASE2_REVERIFY.md`) then
re-attempted falsification of all four residuals: **all VERIFIED CORRECTED, zero falsifications**.
R-SEC-004-A survived 4 new probes (invalid-cookie/valid-Bearer, refresh-in-Bearer,
expired-Bearer/valid-cookie, duplicate-JTI), each proving the real perm_version bump; R-CLIN-003-A
survived 3 new probes (high→normal, critical-low→normal, 3× re-validation idempotence) with
`OutboxEvent` counts unchanged. No new status award; `production_ready` remains 0.

## 3. Verification evidence

- **New adversarial tests:** 34 total (32 Tier A + 2 residual regressions).
- **Focused residual + registry run:** 40 passed (5 + 4 + 31).
- **Final-tree full regression:** **4947 passed, 27 skipped, 203 warnings in 536.93s (0:08:56), EXIT=0, 0 failed** — authoritative, executed after the registry was
  finalized. Prior engineering-tree `4945 passed` result explicitly superseded. No test deleted,
  skipped or weakened. Record: `TEST_EVIDENCE_INDEX.md` §11.3 (historical) and §11.5 (authoritative).
- **`scripts/phase_b_gate.py`:** 6/6 PASS, exit 0 (regression floor 780 passed).
- **`scripts/national_integration_verify.py`:** VERDICT PASS, exit 0 (expected advisory HEAD-drift WARN).
- **Ruff:** clean, exit 0, on all Phase 2 source/test files.

## 4. Residuals carried forward

- **R-SEC-004-A (medium) corrected + VERIFIED CORRECTED:** all presented credentials revoked
  independently; 4 new Team C probes passed; regression 5/5.
- **R-CLIN-003-A (low) corrected + VERIFIED CORRECTED:** stale critical/abnormal flags cleared on
  re-validation; previously emitted durable outbox events deliberately untouched; 3 new Team C
  probes passed; regression 4/4.
- **R-CLIN-003-B (low, pre-existing):** `flag` uses the first emitted flag, so
  `['high','critical_high']` persists `'high'` (FHIR `H`); identical in the create path — clinical
  owner awareness only, not introduced by this fix.
- **AUD-PRV-003:** exact same-lab NID collision returns 409 (MPI merge path); no DB-level unique
  constraint added. Pre-existing broken call at `backend/app/nhdw/services.py:40` untouched.
- Authoritative scope boundary: no operational DB/Redis, real government integration, licensed
  terminology datasets, clinical/regulatory validation, restore/PITR drill, or measured RPO/RTO;
  no commit/push/PR/merge/deploy.

## 5. Invariants

| Invariant | Status |
|---|---|
| Integration HEAD `2206654d…` unchanged | PASS |
| 20 staged entries, all `R100` under `archive/legacy/workflow_runtime/`, untouched | PASS |
| Protected MD5s (`effdfeaf…`, `1a02c015…`, `ea3969d0…`) byte-identical | PASS |
| Sibling `gula-platform` HEAD `f478676b…` unchanged (read-only) | PASS |
| All owner-gated decisions unchanged; AUD-SEC-008 not implemented | PASS |
| `production_ready_items == 0`, `production_ready_count == 0` | PASS |
| No commit / push / PR / merge / deploy / external integration | PASS |

## 6. Next step

Team C's focused re-verification verdicts are recorded (all VERIFIED CORRECTED; no falsification,
no PRODUCTION READY). Phase 2 Tier A is fully closed at engineering scope. Next: assess Tier B
strictly in the order defined by `PHASE_2_CANDIDATE_PLAN.md` — assessment only, no implementation
before gate decisions. Preliminary read-only assessment: AUD-SEC-006's
router-level defect is already resolved by Phase 1 AUD-SEC-001 (only an IDOR-style `account_id`
residual remains); AUD-PRV-002 and AUD-PRV-005 remain open; AUD-SEC-008 remains BLOCKED pending
owner ratification of AUD-ARCH-003. No Tier B implementation without those gates.

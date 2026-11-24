# Phase 1 Closeout — Critical Security / API / Architecture Remediation

**Artifact class:** Formal closeout record
**Repository:** `gula-integration` — branch `integration/gula-unification-v1`
**Audited HEAD:** `2206654dc713ea2de8c564a3207dfe05fde23549`
**Date:** 2026-11-19
**Gate for Phase 2:** SATISFIED — all five Phase 1 fixes independently verified or precisely blocked with owner dependencies documented.

## 1. Verdict

**PHASE 1 CLOSED at engineering scope.** All five CRITICAL/HIGH findings are
`IMPLEMENTED / TESTED` and `INDEPENDENTLY VERIFIED` (engineering scope only) by fresh-context Team C.
No `PRODUCTION READY` awarded. Owner-gated items remain owner-gated.

| Finding | Final verdict | Targeted evidence | Owner gate |
|---|---|---|---|
| AUD-SEC-001 — control-plane authz | `INDEPENDENTLY VERIFIED` | 14 passed | none (engineering) |
| AUD-SEC-002 — JWT account domain | `INDEPENDENTLY VERIFIED` | 18 passed | none (engineering) |
| AUD-SEC-003 — staged privileged login | `INDEPENDENTLY VERIFIED` | 13 passed (after falsification correction) | none (engineering) |
| AUD-API-002 — OAuth2 tokens usable | `INDEPENDENTLY VERIFIED` | 10 passed (after falsification correction) | **owner ratification for production claim** |
| AUD-ARCH-003 — single authz authority | `INDEPENDENTLY VERIFIED` | 7 passed | **owner ratification for production claim** |

## 2. Adversarial outcome (honest disclosure)

Fresh-context Team C **successfully falsified two defects** on the first pass
(`INDEPENDENT_VERIFICATION_TEAM_C_PHASE1.md`):
1. AUD-SEC-003 completion path crashed on `datetime.now(datetime.UTC)` (AttributeError) — a defect
   introduced by the integrator's own post-regression cosmetic cleanup, not the original fix.
2. AUD-API-002 legacy NULL-`account_kind` grants carried a bare `user_id` that
   `resolve_token_account_kind()` guessed into the USER family (cross-account collision).

Both were corrected, and fresh-context re-verification
(`INDEPENDENT_VERIFICATION_TEAM_C_PHASE1_REVERIFY.md`) confirms **both survived renewed
falsification with no new defect found**. Full disclosure in `PHASE1_FALSIFICATION_AND_FOLLOWUP.md`.

## 3. Verification evidence

- **Final-tree full regression:** `4913 passed, 27 skipped, 202 warnings, 0 failed, EXIT=0 (9m36s)`
  — prior 4851 + 62 tests (58 Phase 1 + 4 falsification-follow-up). Authoritative run in
  `TEST_EVIDENCE_INDEX.md` §10; the earlier 4909-pass run is explicitly superseded.
- **`scripts/phase_b_gate.py`:** 6/6 PASS (preservation, registry, focused, static, types, regression 780).
- **`scripts/national_integration_verify.py`:** PASS (expected advisory HEAD-drift WARN).
- **Ruff:** clean on all Phase 1 source/test files.
- No test deleted, skipped or weakened; warnings pre-existing and not suppressed.

## 4. Invariants (independently re-confirmed by integrator and Team C)

| Invariant | Status |
|---|---|
| Integration HEAD `2206654d…` unchanged | PASS |
| 20 staged entries, all `R100` under `archive/legacy/workflow_runtime/`, untouched | PASS |
| Protected MD5s (`FINAL_DECISION.md` `effdfeaf…`, MPI audits `1a02c015…`, `ea3969d0…`) intact | PASS |
| Sibling `gula-platform` HEAD `f478676b…` unchanged (read-only) | PASS |
| All 21 owner-gated decisions unchanged | PASS |
| `production_ready_items == 0`, `production_ready_count == 0` | PASS |
| No commit / push / PR / merge / deploy / external integration | PASS |

## 5. Residual items carried forward (not blockers for Phase 2)

- Owner ratification required for any production claim on AUD-API-002 and AUD-ARCH-003.
- Caller-supplied `*_by` attribution fields remain in some NIAM control-plane routes (AUD-SEC-001).
- Legacy tokens without `account_kind` derive domain from signed `lab_id` (AUD-SEC-002).
- Cross-worker MFA pending-JTI single-use depends on Redis (in-memory fallback otherwise) (AUD-SEC-003).
- No operational DB/Redis, real RP/OIDC flow, live RBAC catalog, or full engine-equivalence proof.

## 6. Phase 2 authorization

Phase 2 implementation may now begin per `PHASE_2_CANDIDATE_PLAN.md`, starting with Tier A:
AUD-SEC-007, AUD-API-001, AUD-PRV-001, AUD-SEC-004, AUD-PRV-003, AUD-CLIN-003.
Each finding follows the same falsification-first, adversarial-test, independent-verification protocol.
No status self-award; no production claim; no commit without an exact, owner-approved scope.

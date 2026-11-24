# Final Assurance Decision — Adversarial Assurance Cycle

**Repository:** `gula-integration` — branch `integration/gula-unification-v1`
**Audited HEAD:** `2206654dc713ea2de8c564a3207dfe05fde23549`
**Sibling repository:** `gula-platform` — READ-ONLY, pinned `f478676b6fc375338648dde46fbf076c015a3f91`
**Date:** 2026-11-18 (Phase 1 addendum 2026-11-19)
**Decision class:** Engineering assurance decision — **not** an owner/release decision

## Decision

**PROGRAM VERDICT: NOT ACCEPTED FOR PRODUCTION — HOLD unchanged.**

`production_ready_items == 0`. No finding, remediation or workstream has been awarded `PRODUCTION READY`. No owner-gated decision has been lifted or superseded.

## Basis

| Evidence | Result |
|---|---|
| Team A six-lane adversarial discovery | **81 findings** — CRITICAL 5 / HIGH 39 / MEDIUM 28 / LOW 9; all `DISCOVERED`; none awarded independent or production status (`FINDINGS_REGISTER.json`) |
| Locally applied engineering remediations | **9** — FK/NR-011, AUD-CLIN-001, AUD-MPI-001, AUD-SUP-001 (prior cycle) + **Phase 1: AUD-SEC-001/002/003, AUD-API-002, AUD-ARCH-003**; all `IMPLEMENTED` / `TESTED` (`REMEDIATION_REGISTER.json`) |
| Independent verification | Phase A rounds 1→2 (FAIL→PASS, 8 findings fixed), Phase B PASS (zero findings), Team C fresh-context review: **4/4 prior fixes `INDEPENDENTLY VERIFIED`**; Phase 1 first pass: **4 `INDEPENDENTLY VERIFIED`, 1 FALSIFIED (AUD-SEC-003)** + a legacy-domain residual (AUD-API-002); **re-verification: all 5 Phase 1 fixes `INDEPENDENTLY VERIFIED` at engineering scope, no new defect found** — see `INDEPENDENT_VERIFICATION_REPORT.md`, `INDEPENDENT_VERIFICATION_TEAM_C.md`, `INDEPENDENT_VERIFICATION_TEAM_C_PHASE1.md`, `INDEPENDENT_VERIFICATION_TEAM_C_PHASE1_REVERIFY.md` |
| Phase B authoritative gate | `scripts/phase_b_gate.py` — **6/6 PASS** (preservation, registry, focused, static, types, regression) |
| Registry integrity | `scripts/national_integration_verify.py` — **PASS** (expected advisory HEAD-drift WARN only) |
| Protected records | MD5s `effdfeaf…`, `1a02c015…`, `ea3969d0…` unchanged; both repository HEADs intact; 20 pre-existing staged `R100` renames preserved |
| Final full regression (complete working tree) | **Final corrected tree: 4913 passed, 27 skipped, 0 failed, EXIT=0 (9m36s)** (index §10) — prior cycle 4851 + 62 tests (58 Phase 1 + 4 legacy-domain falsification-follow-up). The earlier 4909-pass run is superseded (it preceded the falsified cosmetic edit). |
| Final test evidence | Indexed in `TEST_EVIDENCE_INDEX.md`; Phase 1 falsification history in `PHASE1_FALSIFICATION_AND_FOLLOWUP.md` |

**Independent-verification meaning:** every `INDEPENDENTLY VERIFIED` award above is a narrow, engineering-evidence verdict (static inspection + targeted synthetic tests + read-only checks). Team C explicitly awarded no `PRODUCTION READY`, touched no owner-gated decision, and performed no external, human, clinical or regulatory validation. At source-finding level all 81 Team A findings remain `DISCOVERED` — that marker is an audit-discovery label, never an assurance award. `FINDINGS_REGISTER.json` tracks `independently_verified_count` for remediated findings (now **5** — all Phase 1 fixes independently verified at engineering scope after re-verification); `production_ready_count` remains **0**.

## What changed in this cycle

1. **NR-011 / FK target integrity (engineering):** dangling FK retargeted to `niam_sessions.id`; missing `IdentityAuthorityRecord` ORM mirror added and registered; regression tests added. The previously disclosed broad-suite co-collection failure is resolved locally; its historical disclosure is retained, with a resolution addendum in reports `13`/`14` and `status_registry.json`.
2. **AUD-CLIN-001 (CRITICAL):** false `"alerted"` success replaced with a durable `CriticalResultDetected` outbox row and honest `notification_pending` response. **No clinician is contacted** — recipient, escalation and acknowledgement remain owner-gated (`BLOCKED`).
3. **AUD-MPI-001 (HIGH):** `nid_exact` is authoritative only when the stored citizen has `nid_verified=True`; unverified NID hashes force `pending_review` or probabilistic scoring and cannot reach the 1.0 short-circuit. NID provenance authority policy remains owner-gated (`BLOCKED`).
4. **AUD-SUP-001 (CRITICAL):** `pyproject.toml` transitive security floors aligned with `requirements.txt`; `uv.lock` regenerated (7 vulnerable pins raised); `uv lock --check` passes; new CI hard gate (`python-uv-lock-consistency`) and dependabot `uv` ecosystem entry added.
5. Assurance artifacts consolidated and written under `GOVERNANCE/ADVERSARIAL_ASSURANCE/`.

## Phase 1 addendum (2026-11-19) — critical security / API / architecture

Five further CRITICAL/HIGH findings were remediated at **engineering scope** with adversarial tests:
AUD-SEC-001 (NIAM control-plane authz, deny-by-default), AUD-SEC-002 (signed `account_kind`,
collision-safe resolution), AUD-SEC-003 (staged privileged login), AUD-API-002 (OAuth2 tokens usable +
legacy-domain fail-closed), AUD-ARCH-003 (single canonical authorization authority). Owner ratification
remains required for any production claim on the two owner-gated items (AUD-API-002, AUD-ARCH-003).

Fresh-context Team C **successfully falsified two defects**, both since corrected:
- AUD-SEC-003 completion path crashed with `datetime.now(datetime.UTC)` (`AttributeError`) — a defect
  introduced by the integrator's own post-regression cosmetic cleanup. Fixed; 13/13 local.
- AUD-API-002 legacy NULL-`account_kind` tokens carried a bare `user_id` that was *guessed* into the
  USER family. Fixed at the mint point; 4 new adversarial tests, 10/10 local.

Fresh-context re-verification (`INDEPENDENT_VERIFICATION_TEAM_C_PHASE1_REVERIFY.md`) confirms **both
corrected defects survived renewed falsification** — the exact `datetime.UTC` crash input no longer
raises, the three security-critical staged-login assertions remain intact (13/13), and a forced
NULL-domain grant with a LabUser/User ID collision mints no `user_id` and is rejected (10/10).
**No new defect found.** All five Phase 1 fixes are now `INDEPENDENTLY VERIFIED` at **engineering
scope**; AUD-API-002 and AUD-ARCH-003 remain **owner-gated** — this is not a production claim. All
invariants re-checked by Team C PASS. No `PRODUCTION READY` awarded; `production_ready_items == 0`.

## What did NOT change

- **HOLD**, **MPI REJECT**, **MP-001**, **ODR-001…004**, **D-020/D-021**, **ADR-A…J**, **AUD-02/07/16** — all immutable, byte-identical.
- T6 FHIR HTTP package remains under `backend/app/interoperability/fhir_http/`, **NON-activated**; WS-E guard preserved.
- No deployment, push, PR, merge, production DB access, external government integration or publication.
- No real patient data; synthetic data only.
- No `PRODUCTION READY` self-award; `INDEPENDENTLY VERIFIED` awards come only from independent Team C
  verdicts, never from the integrator. All 81 Team A findings retain `status = DISCOVERED`.

## Residual risks and required authorities

See `BLOCKED_ITEMS_AND_EXTERNAL_DEPENDENCIES.md`. The dominant residuals are:
- Phase 1 CRITICAL security findings locally remediated and independently verified at engineering
  scope; AUD-SEC-003 and AUD-API-002 corrected after falsification and survived re-verification —
  **still no production claim**; AUD-API-002 and AUD-ARCH-003 need owner ratification for any
  production claim;
- `AUD-DB-004` FK to an unmigrated table (ADR-A 284-table gap) — `BLOCKED`;
- OAuth2 token-type contract (`AUD-API-002`) — owner ratification required for any production claim;
- offline-first / SLO / durable-queue product decisions — owner-gated;
- no restore/PITR drill or measured RPO/RTO (`AUD-INF-002`) — `BLOCKED`;
- audited tree not reproducible from HEAD (`AUD-ARCH-002`, `AUD-SUP-003`) — commit/branch policy owner decision;
- clinical notification delivery policy — clinical owner decision.

## Commit status — BLOCKED by the provenance gap

The nine remediations and all assurance artifacts are **present and verified in the working tree but not committed**. This is a deliberate safety decision, not an omission:

- The tree contains **215 untracked files** and a large pre-existing modified surface (the documented `AUD-ARCH-002` / `AUD-SUP-003` provenance gap), which is owner-gated `BLOCKED`.
- Several files I had to modify carry **pre-existing uncommitted work** mixed with my edits:
  - `backend/app/services/mpi/resolver.py` contains pre-existing MPI audit-lifecycle/review-decision/merge-integrity work; it imports `backend/app/services/mpi/reliability.py`, which is untracked and absent from HEAD. Committing `resolver.py` alone would produce a broken import in a clean checkout.
  - `backend/app/lims/routes.py` contains pre-existing auth-dependency changes unrelated to `AUD-CLIN-001`.
  - `backend/tests/test_mpi_audit0416_integrity.py` is pre-existing untracked work; my edit is a minimal compatibility adjustment.
- The 20 pre-existing staged `R100` renames under `archive/legacy/workflow_runtime/` remain staged and untouched.

Creating a scoped commit would therefore either absorb owner-gated pre-existing work into my commit (misattribution) or create a commit that is broken from a clean checkout. Both are unacceptable. The correct status for local commits is `BLOCKED` pending the owner's decision on the commit/branch policy for the untracked surface (`AUD-ARCH-002` / `AUD-SUP-003`). No push, PR, merge or deploy was attempted.

## Final instruction

**STOP.** This cycle ends at an engineering assurance decision. Escalation of any owner-gated item requires a new, traceable, signed decision record from the named authority. Any production, clinical, regulatory or release claim requires human authority that was not exercised here.

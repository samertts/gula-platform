# Executive Audit Report — National Integration Adversarial Assurance Cycle

**Audience:** Program Director / named owners
**Repository:** `gula-integration` — branch `integration/gula-unification-v1`
**Audited HEAD:** `2206654dc713ea2de8c564a3207dfe05fde23549`
**Sibling:** `gula-platform` — READ-ONLY at `f478676b6fc375338648dde46fbf076c015a3f91`
**Date:** 2026-11-18 (Phase 1 addendum 2026-11-19)

## 1. Headline

The adversarial assurance cycle is complete at the **engineering** level. A six-lane, disjoint Team A audit produced **81 findings** (5 CRITICAL, 39 HIGH, 28 MEDIUM, 9 LOW). Nine of the most material defects have been remediated locally and verified at engineering scope (four in the prior cycle, five in Phase 1). The remaining findings are recorded with evidence, reproduction/falsification notes, owner-gate classification and status — none were silently closed.

**Phase 1 (2026-11-19):** five CRITICAL/HIGH security, API and architecture fixes were independently attacked by fresh-context Team C. **Two defects were successfully falsified** — the AUD-SEC-003 MFA-completion path crashed on an invalid `datetime.UTC` reference (defect introduced by the integrator's own post-regression cleanup), and a legacy OAuth2 NULL-domain token was *guessed* into the wrong account family. Both were corrected, locally re-tested, and then **survived fresh-context re-verification** — all five Phase 1 fixes are now `INDEPENDENTLY VERIFIED` at engineering scope, with no new defect found. See `PHASE1_FALSIFICATION_AND_FOLLOWUP.md` and `INDEPENDENT_VERIFICATION_TEAM_C_PHASE1_REVERIFY.md`.

**Program verdict: NOT ACCEPTED FOR PRODUCTION. HOLD unchanged. `production_ready_items == 0`.**

No owner-gated decision was lifted: HOLD, MPI REJECT, MP-001, ODR-001…004, D-020/D-021, ADR-A…J, AUD-02/07/16 remain byte-identical. No deployment, push, PR, merge, production DB or external government integration occurred.

## 2. What was found

| Area | Findings | Most material |
|---|---|---|
| Architecture / inventory (A1) | 9 | Audited tree not reproducible from HEAD (209+ untracked files); two mutually exclusive "only authority" permission engines coexist |
| Security / privacy (A2) | 14 | 3 CRITICAL: NIAM control planes accept any authenticated actor; JWT has no account-type discriminator with LabUser resolved first; privileged login checks MFA enrollment but issues full tokens without an MFA challenge |
| MPI / clinical (A3) | 6 | CRITICAL false-success critical-result alert; HIGH unverified-NID auto-claim; demographic-specific reference ranges and tenant scope gaps |
| Database / API (A4) | 15 | OAuth2 tokens use `type='oauth2_access'` but protected endpoints require `type='access'`; FK to unmigrated `national_encounters` (ADR-A 284-table gap); `/integration/standards` returns HTTP 500 |
| Performance / offline / frontend (A5) | 17 | 99.99% SLO computed from a hardcoded gauge; default conflict resolution is `LAST_WRITE_WINS`; no client-side offline data store |
| Supply / infra (A6) | 20 | Stale `uv.lock` with vulnerable transitive pins; unpinned microservice images; `validate-restore.sh` can return PASS when `pg_restore` fails; no measured RPO/RTO or PITR drill |

Full machine-readable detail: `FINDINGS_REGISTER.json`.

## 3. What was fixed

| Remediation | Finding | Change | Engineering status |
|---|---|---|---|
| FK target integrity / NR-011 | NR-011 (disclosed integration defect) | FK retargeted to `niam_sessions.id`; `IdentityAuthorityRecord` ORM mirror added + registered; regression tests | `IMPLEMENTED` / `TESTED` |
| Critical-result alert | AUD-CLIN-001 (CRITICAL) | Durable `CriticalResultDetected` outbox row; honest `notification_pending`, `clinician_notified=False`; route commits durable row | `IMPLEMENTED` / `TESTED` |
| Unverified NID gate | AUD-MPI-001 (HIGH) | `nid_exact` requires stored `nid_verified=True`; unverified hashes excluded from 1.0 short-circuit; pending_review on lock path | `IMPLEMENTED` / `TESTED` |
| Dependency lock integrity | AUD-SUP-001 (CRITICAL) | `pyproject.toml` floors aligned; `uv.lock` regenerated (7 pins raised); `uv lock --check` gate + `uv export`/`pip-audit` CI job; dependabot `uv` entry | `IMPLEMENTED` / `TESTED` |
| NIAM control-plane authz | AUD-SEC-001 (CRITICAL) | `require_niam_control_plane_authority()`; active elevated NIAM role; deny by default; 8 planes wired; 14 tests | `IMPLEMENTED` / `TESTED` |
| JWT account domain | AUD-SEC-002 (CRITICAL) | Signed `account_kind`; strict table-specific resolution; collision-safe legacy fallback; 18 tests | `IMPLEMENTED` / `TESTED` |
| Staged privileged login | AUD-SEC-003 (CRITICAL) | Credentials → scoped `mfa_pending` → real factor → full tokens; single-use JTI; 13 tests (after correcting a falsified completion-path crash) | `INDEPENDENTLY VERIFIED` (engineering scope) |
| OAuth2 tokens usable | AUD-API-002 (HIGH, owner-gated) | Canonical `type='access'` + user claims; persisted `account_kind`; legacy NULL-domain now fails closed at mint; 10 tests | `INDEPENDENTLY VERIFIED` (engineering scope); owner ratification pending for production claim |
| Single authz authority | AUD-ARCH-003 (HIGH, owner-gated) | health_core engine re-scoped SYNTHETIC ONLY; one canonical authority in Shared Core; 7-test differential equivalence; ADR | `IMPLEMENTED` / `TESTED` |

Detail and per-finding boundaries: `REMEDIATION_REGISTER.json`.

**Commit status:** these changes remain **uncommitted in the working tree**. Local commits are `BLOCKED` by the owner-gated provenance gap (`AUD-ARCH-002` / `AUD-SUP-003`): 215 untracked files and pre-existing uncommitted work are mixed into several files I had to modify (e.g. `resolver.py` imports the untracked `reliability.py`), so a scoped commit would either absorb owner-gated work or break from a clean checkout. See `FINAL_ASSURANCE_DECISION.md` §"Commit status".

## 4. Verification posture

- Phase A independent review: round 1 **FAIL** (8 findings) → round 2 **PASS** (all fixed on disk).
- Phase B independent review: **PASS**, zero findings.
- Team C fresh-context verification (prior cycle): **4/4 fixes `INDEPENDENTLY VERIFIED`**, engineering scope only. Recorded in `INDEPENDENT_VERIFICATION_TEAM_C.md`.
- Team C fresh-context verification (Phase 1): **4 INDEPENDENTLY VERIFIED, 1 FALSIFIED** (AUD-SEC-003), plus a legacy-domain residual in AUD-API-002 — recorded in `INDEPENDENT_VERIFICATION_TEAM_C_PHASE1.md`. Both corrected and re-verified: **all 5 Phase 1 fixes `INDEPENDENTLY VERIFIED` at engineering scope, no new defect found** — recorded in `INDEPENDENT_VERIFICATION_TEAM_C_PHASE1_REVERIFY.md`.
- `scripts/phase_b_gate.py`: **6/6 PASS**. `scripts/national_integration_verify.py`: **PASS** (re-run after the corrections).
- Full regression on the **final corrected tree**: **4913 passed, 27 skipped, 0 failed, EXIT=0 (9m36s)** — prior 4851 + 62 tests (58 Phase 1 + 4 falsification-follow-up). The earlier 4909-pass run is explicitly superseded (it preceded the falsified cosmetic cleanup). Recorded in `TEST_EVIDENCE_INDEX.md` §10.
- Protected MD5s and both repository HEADs verified unchanged; 20 pre-existing staged `R100` renames preserved.
- Full test evidence index: `TEST_EVIDENCE_INDEX.md`.

All independent verdicts are **engineering-evidence only** — narrow, scoped, and not production, clinical, regulatory or release claims. No `PRODUCTION READY` was awarded; `production_ready_items == 0`; the 81 source findings remain `DISCOVERED` at the finding level.

## 5. Why this is not production-ready

1. **Phase 1 CRITICAL/high findings are locally remediated and independently verified at engineering scope**, including the two corrected defects (AUD-SEC-003, AUD-API-002) which survived renewed falsification. No production claim is made. AUD-API-002 and AUD-ARCH-003 additionally require owner ratification.
2. **Clinical delivery is not real.** The critical-result alert is now durable and honest, but no clinician is contacted; recipient, escalation and acknowledgement policy is a clinical-owner decision.
3. **Authoritative terminology datasets** (licensed SNOMED CT, official LOINC/ICD/UCUM) are external dependencies, absent here.
4. **No operational DB, no restore/PITR drill, no measured RPO/RTO**; `AUD-INF-002` is `BLOCKED`.
5. **Provenance gap:** the audited tree is not reproducible from HEAD (large untracked surface), a commit/branch-policy owner decision (`AUD-ARCH-002`, `AUD-SUP-003`).
6. **Breaking changes require owner authority:** OAuth2 token-type contract (`AUD-API-002`) — engineering fix done, owner ratification pending for any production claim; DB constraint downgrades (`AUD-DB-003`).
7. **Offline-first and availability SLO claims contradict source defaults** and need product-owner decisions.

## 6. Recommended owner actions

1. Convene the identity/security owner to ratify the Phase 1 engineering outcomes (control-plane authorization, account-type discriminator, MFA challenge enforcement, single canonical authorization authority). Engineering-scope independent verification is complete; this does not substitute for owner ratification or any production claim.
2. Convene the clinical owner to define critical-result recipient/escalation/acknowledgement policy before any delivery claim is made.
3. Commission an operational-DB restore/PITR drill and measure RPO/RTO (`AUD-INF-002`, `AUD-INF-001`).
4. Decide the commit/branch policy for the large untracked surface so the audited tree becomes reproducible from HEAD (`AUD-ARCH-002` / `AUD-SUP-003`).
5. Decide the ADR-A 284-table migration package and the `national_encounters` FK (`AUD-DB-004`).
6. Decide the OAuth2 token-type contract (`AUD-API-002`) and DB constraint restoration (`AUD-DB-003`) as explicit breaking-change records.

Until these are signed, the correct status is **STOP — NOT ACCEPTED FOR PRODUCTION**.

## 7. Artifact index

| Artifact | Purpose |
|---|---|
| `FINDINGS_REGISTER.json` | Canonical consolidated 81-finding register |
| `REMEDIATION_REGISTER.json` | Nine local remediations, evidence and boundaries |
| `INDEPENDENT_VERIFICATION_REPORT.md` | Index of all independent verification events |
| `INDEPENDENT_VERIFICATION_TEAM_C.md` | Fresh-context remediation verification (prior cycle) |
| `INDEPENDENT_VERIFICATION_TEAM_C_PHASE1.md` | Fresh-context Phase 1 verification — includes two successful falsifications |
| `INDEPENDENT_VERIFICATION_TEAM_C_PHASE1_REVERIFY.md` | Re-verification of the two corrected defects — both survived, no new defect |
| `PHASE1_FALSIFICATION_AND_FOLLOWUP.md` | Falsification detail and integrator corrections |
| `PHASE_2_CANDIDATE_PLAN.md` | Gated Phase 2 candidate triage (no implementation authorised) |
| `TEST_EVIDENCE_INDEX.md` | Reproducible commands and observed results |
| `BLOCKED_ITEMS_AND_EXTERNAL_DEPENDENCIES.md` | Owner gates and external dependencies |
| `FINAL_ASSURANCE_DECISION.md` | Formal engineering assurance decision |
| `FINDINGS_A1…A6*.json` + Area reports | Source auditor artifacts (disjoint lanes) |

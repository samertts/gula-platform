# Independent Verification Report — Adversarial Assurance Cycle

**Artifact class:** Assurance index (no new status award)
**Repository:** `gula-integration` — branch `integration/gula-unification-v1`
**Audited HEAD:** `2206654dc713ea2de8c564a3207dfe05fde23549`
**Sibling repository:** `gula-platform` — READ-ONLY, pinned `f478676b6fc375338648dde46fbf076c015a3f91`

This report **indexes** independent verification already performed and points to the
primary records. It does not re-award status. Every verdict below is an
**independent engineering-evidence verdict only** — not a production, clinical,
regulatory or release claim.

## Vocabulary discipline

Only `IMPLEMENTED / TESTED / INTEGRATED / INDEPENDENTLY VERIFIED / PRODUCTION READY / BLOCKED / NOT IMPLEMENTED` are used as status words. `INDEPENDENTLY VERIFIED` appears only where a reviewer with no file ownership actually re-executed the evidence. `PRODUCTION READY` is awarded nowhere (`production_ready_items == 0`).

## Independent verification events

| # | Event | Reviewer (no file ownership) | Verdict | Scope | Primary record |
|---|---|---|---|---|---|
| 1 | Phase A round 1 | independent read-only subagent `ses_e102f590affeeLaDFoCeAgw8px` | **FAIL** — 8 findings (3 HIGH, 4 MEDIUM, 1 LOW) | Documents `00`–`14`, `status_registry.json`, validator + its tests | `GOVERNANCE/NATIONAL_INTEGRATION/ADVERSARIAL_REVIEW_RECORD.md` §Round 1 |
| 2 | Phase A round 2 | same independent subagent | **PASS** — all 8 findings confirmed genuinely fixed on disk | Same as #1 | `ADVERSARIAL_REVIEW_RECORD.md` §Round 2 |
| 3 | Phase B | independent read-only subagent `ses_e0ff9c922fferm5xYuovZPWVX4` | **PASS** — zero findings | Phase B evidence reports, T1/T3/T5/T6 modules, `phase_b_gate.py`, reports 13/14, registry | `ADVERSARIAL_REVIEW_RECORD.md` §Phase B |
| 4 | Team C remediation verification | fresh-context independent subagent `ses_e0fd6974fffemmtdI2xUZjG770` | **4/4 `INDEPENDENTLY VERIFIED`** — engineering scope only; could not falsify any of the four fixes | FK/NR-011, AUD-CLIN-001, AUD-MPI-001, AUD-SUP-001 | `GOVERNANCE/ADVERSARIAL_ASSURANCE/INDEPENDENT_VERIFICATION_TEAM_C.md` |
| 5 | Team C Phase 1 fresh-context verification | fresh-context independent subagent `ses_e0f8508f9ffeKVxWPB2aAsbK4m` | **4 `INDEPENDENTLY VERIFIED`, 1 FALSIFIED** — engineering scope only | AUD-SEC-001, AUD-SEC-002, AUD-SEC-003, AUD-API-002, AUD-ARCH-003 | `GOVERNANCE/ADVERSARIAL_ASSURANCE/INDEPENDENT_VERIFICATION_TEAM_C_PHASE1.md` |
| 6 | Team C Phase 1 **re-verification** of the two corrected defects | same fresh-context subagent | **both `INDEPENDENTLY VERIFIED`** — survived renewed falsification; no new defect found; engineering scope only | AUD-SEC-003, AUD-API-002 (legacy-domain residual) | `GOVERNANCE/ADVERSARIAL_ASSURANCE/INDEPENDENT_VERIFICATION_TEAM_C_PHASE1_REVERIFY.md` |

Team C's four verdicts, each narrowly scoped and with residuals recorded honestly:

| Fix | Verdict scope | Evidence re-executed | Residual limitations |
|---|---|---|---|
| FK target integrity (NR-011) | `INDEPENDENTLY VERIFIED` — static + targeted + co-collection + forced FK probe | 5/5 targeted; original co-collection 185 passed/4 pre-existing skips; 1174 FKs force-resolved on merged Alembic metadata, zero errors | No live PG/DDL; stale `SESSION_GOVERNANCE.md:114` table listing; pre-existing cross-metadata FKs resolve only via merge layer |
| `AUD-CLIN-001` | `INDEPENDENTLY VERIFIED` — static + 4 targeted + event/subscriber census | 4/4; no live `alerted` path; route commits only on `notification_pending`; no subscriber delivers `lims.result.critical` | Delivery/acknowledgement owner-gated → `BLOCKED`; SQLite only; no real worker run |
| `AUD-MPI-001` | `INDEPENDENTLY VERIFIED` — static + 13 targeted + synthetic bypass probes | 13/13; unverified NID → `probabilistic`/`pending_review`, never `nid_exact`; no production path sets `nid_verified=True` | Matcher 1.0 short-circuit persists but unreachable from resolver; fully concordant demographics still score 1.0 as `probabilistic`; no PG concurrency |
| `AUD-SUP-001` | `INDEPENDENTLY VERIFIED` — read-only `uv lock --check`/`uv export` + YAML parse | lock md5 unchanged, exit 0; frozen export exit 0 with all 7 pins meeting floors; CI hard gate + dependabot `uv` entry present | `pip-audit` not run (network prohibited); CI job not run on GitHub; pip+uv dependabot duplicate-PR risk |

Two of Team C's falsification probes initially raised a `NoReferencedTableError` for a *different* pre-existing cross-metadata FK (`niam_assignments → facilities`); this was an artifact of probing below NR-011's merge layer, not a defect — the real Alembic merged path resolved all 1174 FKs. Recorded honestly in the Team C report §1.

## Phase 1 fresh-context verdicts (event #5 / #6)

The adversarial model worked as designed: fresh-context Team C **successfully falsified two defects**, which is why `INDEPENDENTLY VERIFIED` was withheld from them until re-verification.

| Fix | First-pass verdict | Falsification / residual | Current status |
|---|---|---|---|
| AUD-SEC-001 (control-plane authz) | `INDEPENDENTLY VERIFIED` | none | `INDEPENDENTLY VERIFIED` (engineering scope) |
| AUD-SEC-002 (JWT account domain) | `INDEPENDENTLY VERIFIED` | none | `INDEPENDENTLY VERIFIED` (engineering scope) |
| AUD-SEC-003 (staged login) | **BLOCKED — FALSIFIED** | `datetime.now(datetime.UTC)` `AttributeError` after a correct MFA factor → 500, no tokens (11 passed / 2 FAILED) | defect corrected; **`INDEPENDENTLY VERIFIED`** (13 passed, survived renewed falsification) |
| AUD-API-002 (OAuth2 tokens) | `INDEPENDENTLY VERIFIED` (eng. scope, owner-gated) | legacy NULL-`account_kind` grant carried a bare `user_id` guessed into the USER family | residual corrected at mint point; **`INDEPENDENTLY VERIFIED`** (10 passed, survived renewed falsification; owner-gated) |
| AUD-ARCH-003 (single authority) | `INDEPENDENTLY VERIFIED` (eng. scope, owner-gated) | none beyond documented equivalence limits | `INDEPENDENTLY VERIFIED` (engineering scope) |

Both defects were corrected and locally re-tested (13/13 and 10/10), with full disclosure in `PHASE1_FALSIFICATION_AND_FOLLOWUP.md`. Fresh-context re-verification (event #6, `INDEPENDENT_VERIFICATION_TEAM_C_PHASE1_REVERIFY.md`) confirms both survived renewed falsification with **no new defect found**; the corrected behavior is now `INDEPENDENTLY VERIFIED` at engineering scope (all 5 Phase 1 fixes). Owner-gated items (AUD-API-002, AUD-ARCH-003) remain owner-gated; no `PRODUCTION READY` awarded.

## What the independent reviewers actually re-executed

**Phase A round 2** (`ADVERSARIAL_REVIEW_RECORD.md`):
- `test_national_integration_registry.py` → **31 passed**
- `test_nr011_metadata_discovery.py` → **14 passed**
- `tests/health_core` → **773 passed, 1 warning**
- `pytest tests/ --collect-only` → **4675 tests collected, 0 errors**
- `ruff check` on validator + test → clean
- `national_integration_verify.py --json` → **PASS, 0 errors, 0 warnings**
- 11 in-memory adversarial registry mutations → **all detected**

**Phase B** (same record):
- `scripts/phase_b_gate.py` → **exit 0, 6/6 PASS**
- Six focused suites → **235 passed** (31 + 14 + 106 + 19 + 14 + 51)
- Terminology contract/provenance → **103 passed**
- `pytest tests --collect-only -q` → **4865 collected, 0 errors**
- `tests/health_core` → **773 passed, 1 warning**
- Source-level review of T1 (Mod-10), T3 (durable queue), T5 (audit hash chain), T6 (non-activated FHIR HTTP) and DB evidence
- Reproduced the disclosed NR-011 co-collection failure (now resolved locally — see §below)

**Team A** (fresh, disjoint six-lane static audit): 81 findings, all `DISCOVERED`, none awarded independent or production status. Source artifacts: `FINDINGS_A1…A6*.json`, consolidated in `FINDINGS_REGISTER.json`.

## Resolution of the disclosed NR-011 failure

Phase B review reproduced: `NoReferencedTableError: niam_adaptive_mfa_sessions.session_id → niam_user_sessions.id` when `tests/identity` is co-collected. This was a real, disclosed, pre-existing defect — never suppressed. It has now been repaired locally by retargeting the FK to `niam_sessions.id` and adding the missing `IdentityAuthorityRecord` ORM mirror (see `REMEDIATION_REGISTER.json` → `REM-FK-001`). The historical disclosure is retained in `status_registry.json` and reports `13`/`14`; a resolution addendum was appended to each. Final regression evidence is indexed in `TEST_EVIDENCE_INDEX.md`.

## Assurance boundary

- No `PRODUCTION READY` award anywhere; `production_ready_items == 0`.
- Phase A and Phase B `INDEPENDENTLY VERIFIED` verdicts are scoped to their documented review boundaries and do **not** extend to post-Phase-B remediation work.
- Team C verdicts are engineering-only (static review + targeted synthetic tests); they do not constitute runtime, operational-DB, external, clinical or regulatory validation.
- Owner-gated decisions — HOLD, MPI REJECT, MP-001, ODR-001…004, D-020/D-021, ADR-A…J, AUD-02/07/16 — remain unchanged. No authority has supplied a superseding decision.
- No real patient data, external government integration, deployment or production DB was used.

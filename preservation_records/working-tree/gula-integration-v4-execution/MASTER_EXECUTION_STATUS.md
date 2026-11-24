# GULA Stable v1.0.0 — Master Execution Status

**Document:** `MASTER_EXECUTION_STATUS.md`
**Repository:** `gula-integration` — branch `integration/gula-unification-v1`
**Reviewed HEAD:** `2206654dc713ea2de8c564a3207dfe05fde23549`
**Sibling repository:** `gula-platform` HEAD `f478676b6fc375338648dde46fbf076c015a3f91` (read-only, untouched)
**Date / environment:** 2026-11-19 — Linux, Python 3.12.13, pinned interpreter
`/home/samertts/workspace/projects/gula-platform/backend/.venv/bin/python`,
`ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:..`, synthetic/disposable data only.

**Status vocabulary (exclusive):** `IMPLEMENTED / TESTED / INTEGRATED / INDEPENDENTLY VERIFIED /
PRODUCTION READY / BLOCKED / NOT IMPLEMENTED`. `PRODUCTION READY` is **not** awarded anywhere in
this document. `GULA Stable v1.0.0` is **not declared**.

> **GULA-AUDIT-COMPREHENSIVE-REVIEW — OD-001 ACCEPTED (additive, 2026-11-20):** The owner explicitly recorded “OD-001: ACCEPTED. The owner explicitly accepts the third independent SEC-015 F-01 review verdict (PASS) and authorizes recording OD-001 as ACCEPTED. This acceptance applies to the defined SEC-015/F-01 engineering scope only.” Reference: `GULA_SEC015_F01_INDEPENDENT_REVIEW_3_REPORT.md` (MD5 `329049ee6bed006901660e43b2d4b995`, 171 lines). This governance synchronization changes no criterion, no status award and no release decision. It does not accept `OD-002`…`OD-025`, authorize commit/merge/release/deploy, award `PRODUCTION READY`, or change **HOLD**. Stable v1.0.0 remains **NOT declared**; `production_ready_items = 0`.

---

## 1. Scope and invariants (re-checked this session, not assumed)

| Invariant | Expected | Observed | Result |
|---|---|---|---|
| Integration HEAD | `2206654d...` | `2206654dc713ea2de8c564a3207dfe05fde23549` | intact |
| Sibling HEAD (read-only) | `f478676b...` | `f478676b6fc375338648dde46fbf076c015a3f91` | intact |
| Staged `R100` renames under `archive/legacy/workflow_runtime/` | 20 | 20 | intact |
| `GOVERNANCE/FINAL_DECISION.md` MD5 | `effdfeaf10234678d83b2668c4489552` | identical | intact |
| `MPI_FINAL_INDEPENDENT_AUDIT.md` MD5 | `1a02c01563c93b07a7cdb92c0462bf36` | identical | intact |
| `MPI_INDEPENDENT_AUDIT_FINDINGS.md` MD5 | `ea3969d09aaf7b0b28a065838b44a594` | identical | intact |
| `status_registry.json → production_ready_items` | 0 | 0 | intact |
| Commits / push / PR / merge / deploy | none | none performed | intact |

Protected decisions (`HOLD`, `MPI REJECT`, `MP-001`, `ODR-001…004`, `D-020/D-021`, `ADR-A…J`,
`AUD-02/07/16`) were not modified. No operational DB/Redis, real patient data, government
integration, or external network integration was used.

## 2. Workstream status

| # | Workstream | Status | Authoritative evidence |
|---|---|---|---|
| 1 | **Phase 1** — AUD-SEC-001/002/003, AUD-API-002, AUD-ARCH-003 | `INDEPENDENTLY VERIFIED` (engineering scope) | `GOVERNANCE/ADVERSARIAL_ASSURANCE/PHASE1_CLOSEOUT.md`; final tree `4913 passed / 27 skipped / 0 failed` |
| 2 | **Phase 2 Tier A** — AUD-SEC-007, AUD-API-001, AUD-PRV-001, AUD-SEC-004, AUD-PRV-003, AUD-CLIN-003 | `INDEPENDENTLY VERIFIED` (engineering scope) | `GOVERNANCE/ADVERSARIAL_ASSURANCE/PHASE2_CLOSEOUT.md`; final tree `4947 passed / 27 skipped / 0 failed`; three falsified recording errors corrected and re-verified |
| 3 | **NIAM Step-up prerequisite** (bounded work item, before B4) | `INDEPENDENTLY VERIFIED` (engineering scope, by fresh-context Team C) | `INDEPENDENT_VERIFICATION_TEAM_C_STEP_UP.md` (57+ probes, 0 real bypasses); `NIAM_STEP_UP_SECURITY_REPORT.md`; 37 focused tests, final tree 4984/0, gates PASS |
| 4 | **B4** — cross-account security administration | `INDEPENDENTLY VERIFIED` (engineering scope) | Owner directive `GULA-MASTER-AUTH-2026-11-19` §4 authorized implementation. Server-side guard `app/identity/adaptive_auth/b4_guard.py` + hardened `routes.py` (self-only MFA, narrow master_admin/security_administrator RBAC, fresh step-up, fail-closed audit); 24 adversarial tests pass; Ruff clean; step-up + AUD-SEC-001 regressions 51/51 pass; OpenAPI unchanged (1815 paths). Fresh-context Team C verdict `INDEPENDENTLY VERIFIED` (engineering scope) — `GOVERNANCE/ADVERSARIAL_ASSURANCE/INDEPENDENT_VERIFICATION_TEAM_C_B4.md` (10 independent probes, all 8 audit fields persisted, 0 real bypasses; 4 residual risks R-1…R-4 recorded). `PRODUCTION READY` explicitly not awarded. Report: `B4_CROSS_ACCOUNT_SECURITY_REPORT.md`. |
| 5a | **B1** — centralized per-action PHI permission map | `INDEPENDENTLY VERIFIED` (engineering scope, fresh-context Team C, second pass) | Owner directive §5. `app/identity/services/phi_permission_map.py` — 8 distinct PHI actions (`read/create/update/delete/export/print/share/administrative`) + `administer` alias; integrated into canonical `AuthorizationDecisionService` via `AuthorizationReason.phi_permission_conflict`; no new engine. `tests/unit/test_b1_phi_permission_map.py` 13 passed; combined canonical authorization regressions 39/39, `EXIT=0`; Ruff clean. |
| 5b | **B2** — separate consent / break-glass, fail-closed | `INDEPENDENTLY VERIFIED` (engineering scope, fresh-context Team C) | Owner directive §5 (AUD-PRV-002). `app/security/break_glass_guard.py` verifies a persisted, active, unexpired, subject-bound `BreakGlassSession`; `X-Emergency-Access` downgraded to intent-only signal; `consent_dep.py` rewired; activation route (`routes/authorization.py`) validates role/category/justification/patient/duration and enforces deactivation ownership. Consent and break-glass remain separate. `tests/test_consent.py` 26 passed (forged-header bypass, expired/deactivated/wrong-subject/another-actor/non-read-scope, activation policy); combined with B1 39/39, `EXIT=0`; Ruff clean. Iraqi legal categories are documented policy dependencies. |
| 5c | **B3** — verified guardian/minor/NHID rules | `INDEPENDENTLY VERIFIED` (engineering scope, fresh-context Team C) | Owner directive §5 (AUD-PRV-005). New fail-closed policy layer `app/identity/services/verified_guardian_guard.py` (server-derived age, 90-day near-majority re-verification, canonical NID input contract only — **no canonical NHID minted**, twins-never-merged, authorized-verifier gate); additive `create_pending_guardian()` in canonical `CitizenRelationshipWorkflow`; extra guardian gate in canonical `AuthorizationDecisionService._relationship_allows` (an additive check, not a second engine). `tests/unit/test_b3_verified_guardian.py` 41 passed; canonical regressions 67/67 (`test_authorization_phase8`, `test_authorization_synthetic_scope`, `test_citizen_relationship_workflow`, `test_nhid_readiness`, `test_b1_phi_permission_map`); Ruff clean. Iraqi legal specifics remain documented policy dependencies. |
| 5d | **B5** — delegation into canonical authority | `INDEPENDENTLY VERIFIED` (engineering scope, fresh-context Team C re-verification `2026-11-19T10:35:28Z`; all 3 prior findings remediated, 0 real API bypasses); one residual defense-in-depth gap documented in §6 | Owner directive §5 (AUD-SEC-008). New NIAM-native, account-based `niam_delegations` model (`app/identity/models/delegation.py`), additive reversible migration `20261119_0002` (single head, 110 files), and `DelegationService` (`app/identity/services/delegation_service.py`) with verified permission subset, scope containment, duration cap, depth cap (3), self-delegation denial, and full audit. Wired into the **single canonical** `RolePermissionService.effective_permissions()` — no second engine, no new role/permission. `tests/unit/test_b5_delegation.py` 26 passed (grant/deny/depth/scope/expiry/revocation/authority-consumer); combined Tier B + canonical regressions 226/226, `EXIT=0`; Ruff clean; OpenAPI unchanged (1815 paths). |
| 6 | Phase 3 — national identity / trust | `TESTED` (pre-existing components), broader execution `BLOCKED` on owner-gated decisions and service integration evidence | MPI/identity reports in `GOVERNANCE/IDENTITY_REMEDIATION/`; no new government API claims. |
| 7 | Phase 4 — clinical critical alerts | `TESTED` (Tier A AUD-CLIN-003), full lifecycle failure drill `BLOCKED` (Redis/RabbitMQ runtime unavailable) | `GOVERNANCE/ADVERSARIAL_ASSURANCE/PHASE2_CLOSEOUT.md` §2 residual; no claim of delivery to practitioners. |
| 8 | Phase 5 — database / migrations / recovery | `TESTED` (step-up migration upgrade/downgrade on disposable SQLite), restore/PITR and RPO/RTO `BLOCKED` | `NIAM_STEP_UP_SECURITY_REPORT.md` §4; no DDL on operational DB. |
| 9 | Phase 6 — 18 services / frontend | Static inventory review `TESTED`; runtime service integration `BLOCKED` | Wave 3 ledger §12: 18-service inventory revalidated; frontend static gates freshly re-run (ledger §10). The **45 `care_continuum` `cc_*` tables now have migration coverage** via uncommitted revision `20261119_0003` (62-table FK closure, full-chain upgrade/downgrade/re-upgrade + synthetic constraint probes PASS, 8 regression tests; see `GOVERNANCE/EXECUTION_LEDGER.md` §16 and `DATABASE_MIGRATION_READINESS.md` §4 — migration `INDEPENDENTLY VERIFIED` at engineering scope by fresh-context Team C re-verification, 2026-11-19 — §7; `PRODUCTION READY` not awarded). `create_all` still masks schema gaps in tests and **0 audit writes** remain on the 74-op surface; no runtime/integration claim |
| 10 | Phase 7 — reproducibility / full regression | `TESTED` (full Python suite); clean-environment rebuild / Docker / CI `BLOCKED` (out of scope) | Full-suite logs in `/tmp/opencode/`; see §3. |
| 11 | Team C independent verification | Phase 1 + Phase 2 + step-up + B4 + **Tier B B1/B2/B3/B5** + **care-continuum migration `20261119_0003` P1 fix** `INDEPENDENTLY VERIFIED` (engineering scope) | Team C reports in `GOVERNANCE/ADVERSARIAL_ASSURANCE/`. Two fresh-context Tier B passes conflicted; the later, more adversarial pass (`INDEPENDENT_VERIFICATION_TEAM_C_TIER_B.md`) verified B1/B2/B3 but blocked B5 on a reproducible HIGH escalation bypass + HIGH integration gap. Fixes were implemented and a third fresh-context pass (`INDEPENDENT_VERIFICATION_TEAM_C_B5_REVERIFY.md`, `2026-11-19T10:35:28Z`) independently confirmed all three findings remediated with 0 real API-reachable bypasses, awarding B5 `INDEPENDENTLY VERIFIED`. Both earlier passes are retained honestly; no award was self-granted |
| 12 | Final acceptance / v1.0.0 declaration | `BLOCKED` | See `FINAL_ACCEPTANCE_REPORT.md` — 18 criteria not all satisfied. |

## 3. Full-suite evidence chain (honest, chronological)

| Run | Result | Coverage / note |
|---|---|---|
| Phase 1 final tree | `4913 passed, 27 skipped, 0 failed` | closeout `PHASE1_CLOSEOUT.md` |
| Phase 2 final tree | `4947 passed, 27 skipped, 0 failed` | closeout `PHASE2_CLOSEOUT.md` (authoritative after registry fix) |
| First run after initial step-up changes | `4973 passed, 27 skipped, 1 failed, EXIT=1` | sole failure = CPU-timing benchmark `test_cosine_similarity_throughput` (`1680/s < 2000/s`), unrelated to step-up; passed 3 isolation runs at `7796/s`, `3885/s`, `5992/s`; no threshold weakened |
| Clean re-run | **`4974 passed, 27 skipped, 203 warnings, EXIT=0 (17m09s)`** | `/tmp/opencode/step_up_full_suite_rerun.log`; confirms benchmark flake; contained the 27-test step-up file (before the 10 new adversarial cases) |
| Final step-up tree (account-state guard, concurrency/replay guard, DB unique constraint, 37 tests) | `4984 passed, 27 skipped, 203 warnings, EXIT=0 (15m04s)` | `/tmp/opencode/step_up_final_full_suite.log`; exactly `4974 + 10` new cases, zero failures |
| **Final Tier B tree** (B4 24 + B1 13 + B2 26 + B3 41 + B5 26 new tests) | **`5105 passed, 27 skipped, 203 warnings, EXIT=0 (12m03s)`** | `/tmp/opencode/final_tree_full_suite_tierB.log`; zero failures; supersedes `4984` for final-tree claims |
| **Post-fix final tree** (adds 6 B5-security + 6 drift-fix regressions) | **`5117 passed, 27 skipped, 203 warnings, EXIT=0 (13m12s)`** | `/tmp/opencode/final_tree_full_suite_b5_fixed.log`; authoritative result after all Tier B + B5 fixes, zero failures; `5117 = 5105 + 12`; superseded below |
| Final tree with care-continuum closure regression tests (**pre-P1-fix**) | `5124 passed, 28 skipped, 203 warnings, EXIT=0 (16m04s)` | `/tmp/opencode/final_tree_full_suite_cc_closure.log`; `5124 = 5117 + 7` static tests, `28 = 27 + 1` skipped opt-in DB lifecycle test. Superseded by the post-P1-fix run below |
| **Final tree after the Team C P1 `use_alter` FK fix** | **`5124 passed, 28 skipped, 203 warnings, EXIT=0 (15m32s)`** | `/tmp/opencode/final_tree_full_suite_p1_fixed.log`; authoritative current-tree result, zero failures; identical count to the pre-fix run because the fix changed migration DDL ops + strengthened existing test assertions (no test added/removed); the DB lifecycle test remains opt-in/skipped without its env var |

Count arithmetic is consistent throughout: pre-step-up `4947` + `27` initial step-up tests = `4974`
executed; `4973 passed + 1 failed` in the flaky run, `4974 passed` in the clean re-run; the final
Tier B tree adds `121` net passing tests over the `4984` step-up tree (`5105`), with no test deleted,
skipped, or weakened.

## 4. Blocking decisions requiring the owner

1. **B4 authorization — RESOLVED.** Owner directive `GULA-MASTER-AUTH-2026-11-19` §4 explicitly
   authorized the exact Self + Security Administration model and ratified the step-up bounds
   (30–3600 s, default 300). B4 is implemented, `TESTED`, and `INDEPENDENTLY VERIFIED` at engineering
   scope by fresh-context Team C (0 real bypasses; 4 residual risks R-1…R-4 recorded). No production
   claim.
2. **Tier B policies — AUTHORIZED (implementation in progress).** Owner directive §5 authorized
   break-glass/consent separation (`AUD-PRV-002`), minor/guardian verification (`AUD-PRV-005`),
   the per-action PHI permission map (`AUD-SEC-005`), and canonical-authority delegation
   (`AUD-SEC-008`). Jurisdiction-specific Iraqi legal rules remain policy dependencies; no legal
   entitlement is fabricated.
3. **Production claims** — `AUD-API-002`, `AUD-ARCH-003` owner ratification; clinical/regulatory
   validation; RPO/RTO measurement and restore/PITR drill; runtime service integration.
4. **Commit separation** — 391 working-tree entries at this check (126 modified,
   245 untracked, 20 renames) from mixed earlier phases; no commit was created because scope
   separation from the pre-existing surface has not been proven. Re-count before any commit.
5. **Registry vs closeout test count:** `GOVERNANCE/NATIONAL_INTEGRATION/status_registry.json:565,583`
   still records the superseded `4945 passed`; the authoritative final-tree result is `4947 passed`
   (`PHASE2_CLOSEOUT.md` §3, `TEST_EVIDENCE_INDEX.md` §11.5). This is a documented, intentional
   registry staleness — do not "fix" it by editing the registry without repeating the suite.

## 5. Next executable work (safe lane, no owner decision required)

1. **Done:** post-fix final-tree full-suite result recorded (§3 last row: `5117 passed / 0 failed`,
   `EXIT=0`) and reconciled with Team C's `INDEPENDENTLY VERIFIED` awards (zero real bypasses) for
   B4 and Tier B B1/B2/B3; B5 re-verification still pending.
2. No Team C defect was found; the one `ObjectDeletedError` was proven a synthetic-fixture artifact
   with no bypass. No re-verification cycle is required.
3. **B4 implemented, `TESTED`, and `INDEPENDENTLY VERIFIED`** (engineering scope) under the
   owner-authorized exact security model; fresh-context Team C awarded the verdict with 0 real
   bypasses. See `B4_CROSS_ACCOUNT_SECURITY_REPORT.md` and `INDEPENDENT_VERIFICATION_TEAM_C_B4.md`.
4. Tier B: B1, B2, B3 and B5 are all implemented and `TESTED` (226 combined targeted tests,
   Ruff clean, OpenAPI 1815 unchanged, single migration head). All controls reuse canonical
   primitives only; no new role, permission catalog entry, or authorization engine was introduced.
   **Two fresh-context Team C passes disagree:** the later, more adversarial pass
   (`INDEPENDENT_VERIFICATION_TEAM_C_TIER_B.md`) awarded `INDEPENDENTLY VERIFIED` (engineering scope)
   to **B1, B2 and B3** but marked **B5 `BLOCKED`** with a reproducible HIGH escalation bypass
   (narrow-delegation holder re-delegates a permission they do not hold) and a HIGH integration gap
   (live `POST /authz/delegations` uses the ungoverned legacy service; canonical table is never
   written by the app). The conservative verdict stands until both are fixed and re-verified.
   B4 residuals R-1…R-4 and Tier B residuals (category-enum drift, near-majority adapter signal,
   legacy audit sink, B1 catalog gap) are recorded for follow-up. **Resolved:** a third fresh-context
   Team C pass (`INDEPENDENT_VERIFICATION_TEAM_C_B5_REVERIFY.md`) re-verified all three B5 fixes and
   awarded B5 `INDEPENDENTLY VERIFIED` (engineering scope); transitive-revocation propagation is
   closed, and one new defense-in-depth residual (forged DB row) is recorded in §6.
5. Wave 2 (database integrity) is `TESTED` (ledger §8): single migration head, 22 migration-safety
   tests, additive/reversible B5 migration verified live on a disposable PG. Wave 3 static service
   inventory review is `TESTED` (ledger §12) but confirms a production blocker (45 `care_continuum`
   `cc_*` tables with no migration, `create_all` test masking, 0 audit writes), so runtime integration
   stays `BLOCKED`; Wave 4 frontend static gates are `TESTED` (ledger §10); Wave 5 offline durability
   is `TESTED` at static-suite scope (82 focused tests, ledger §13; device/network partition drill
   still `BLOCKED`). Wave 6 CI/reproducibility is `TESTED` (ledger §14): the Python 3.14→3.12
   drift in 4 workflows + 14 Dockerfiles was fixed (behavior-preserving, 0 residual executable
   pins, 32/32 workflows parse, `git diff --check` EXIT=0); a CI-policy gap — no `architecture-check`
   or brain hard gate in `gula-integration` — is recorded, not fixed. Wave 7 operational-resilience
   static inventory is `TESTED` (ledger §15: full health probe family, circuit-breaker/retry/
   bulkhead primitives, 45 K8s manifests + HPA/PDB and staged-rollback workflows; 1 PDB and no
   operational drill — restore/PITR, outage and partition drills remain `BLOCKED`). **The safe-lane
   evidence waves recorded in the ledger (2–7) are complete**, and the Team C independent-verdict
   gate (the B4 report's "Wave 8") is satisfied for B4 and all Tier B controls (B1/B2/B3/B5). Only
   the final acceptance/release gate and all owner/operational/legal/clinical decisions remain
   `BLOCKED`; no `PRODUCTION READY` or v1.0.0 claim.

**Current decision:** program remains in execution. Step-up prerequisite is `INDEPENDENTLY VERIFIED`
at engineering scope (`4984 passed / 0 failed` step-up tree; `5117 passed / 0 failed` post-fix final tree). B4 is authorized, implemented, `TESTED`
and `INDEPENDENTLY VERIFIED` (24 adversarial tests, 51 related regressions, Ruff clean, OpenAPI
unchanged, 10 independent Team C probes, 0 real bypasses). Tier B: B1 (PHI map) and B2
(consent/break-glass), B3 (verified guardian/minor) and B5 (scoped/revocable/deep-limited
delegation into the single canonical authority) are implemented and `TESTED` (226 combined
targeted tests, Ruff clean, OpenAPI 1815 unchanged, single migration head `20261119_0002`).
Post-fix final-tree full suite complete: **`5124 passed / 28 skipped / 0 failed, EXIT=0`**
(`/tmp/opencode/final_tree_full_suite_p1_fixed.log`, §3); supersedes the `5117` Tier B tree run for
final-tree claims (adds 7 care-continuum static regression tests + 1 skipped opt-in DB lifecycle
test; the P1 `use_alter` FK fix changed DDL ops and strengthened existing assertions, not test
counts). The later fresh-context Team C pass awarded `INDEPENDENTLY VERIFIED` (engineering scope) to
B1/B2/B3 but **blocked B5** on a reproducible escalation bypass and integration gap
(`GOVERNANCE/ADVERSARIAL_ASSURANCE/INDEPENDENT_VERIFICATION_TEAM_C_TIER_B.md` §4). A real Alembic
drift defect found after that run (unregistered `NiamDelegation` model +
mismatched migration index names) was fixed and locked down with 6 new regression tests
(`tests/unit/test_b5_migration_drift_regression.py`, 6 passed, Ruff clean), followed by 6 B5-security
regressions (`tests/unit/test_b5_security_regressions.py`). The `5117`-pass run is the authoritative
post-fix tree result. A third fresh-context Team C pass
(`GOVERNANCE/ADVERSARIAL_ASSURANCE/INDEPENDENT_VERIFICATION_TEAM_C_B5_REVERIFY.md`) independently
confirmed all three B5 findings remediated and awarded B5 `INDEPENDENTLY VERIFIED` (engineering
scope), with one defense-in-depth residual recorded in §6 — no self-award. No release, production,
or v1.0.0 claim is made; no `PRODUCTION READY` is awarded anywhere.

---

## 6. B5 independent-verification conflict and conservative disposition

Two fresh-context Team C passes were run against Tier B. The first reported B2/B3/B5 verified with
zero bypasses; the second (report timestamp `2026-11-19T09:38:19Z`, broader scope including B1 and
the drift-fix fact) reached the **opposite** conclusion for B5 with a reproducible probe. Both
results are retained honestly; the more severe, evidence-backed result governs:

| Finding | Severity | Evidence | Disposition |
|---|---|---|---|
| Authority laundering: an actor holding a narrow delegation of role R (only `lab_result.read`) can re-delegate `lab_result.export` from R's catalog, which they do not hold; canonical `effective_permissions()` then grants it | HIGH | report §4.1, probe `/tmp/opencode/tierC_probe_b5_escalation.py`; `delegation_service.py:185-218` validates only against role catalog | fix: verify requested keys against the actor's **effective** holding (direct assignment = full active role catalog; delegation-based holding = that delegation's own subset), deny/audit otherwise |
| Integration gap: live `POST /authz/delegations` uses legacy `app.services.authorization_service.DelegationService` writing the ungoverned `delegations` table; canonical `effective_permissions()` reads `niam_delegations`, which no app route writes | HIGH | report §4.2; `routes/authorization.py:345-359` | fix: route delegation lifecycle through the canonical B5 service / account-based IDs or fail the legacy surface closed |
| Transitive revocation: revoking the delegator's direct role assignment leaves the delegate's authority in force | MEDIUM residual | report §6 item 4, probe `/tmp/opencode/tierC_probe_b5_transitive.py` | fix in canonical consumer by validating the delegator chain at enforcement time |

**Remediation implemented 2026-11-19 (fail-closed, no self-award):** authority laundering fixed by
validating requested keys against the actor's effective holding; integration gap fixed by adding the
canonical account-based `/niam/delegations` API (writes the governed `niam_delegations` table) and
failing the legacy `/authz/delegations` surface closed (HTTP 410); transitive revocation fixed by
validating the full delegator chain at enforcement time. Six new regression tests
(`tests/unit/test_b5_security_regressions.py`), focused suite **238 passed, EXIT=0**, Ruff clean,
OpenAPI `1815 → 1817` (+2 intentional canonical routes). Full ledger evidence: execution ledger §11.

**Resolution (2026-11-19T10:35:28Z):** a third fresh-context Team C pass
(`GOVERNANCE/ADVERSARIAL_ASSURANCE/INDEPENDENT_VERIFICATION_TEAM_C_B5_REVERIFY.md`) independently
re-tested all three findings with adversarial probes: the exact prior escalation repro is DENIED,
the canonical route writes `niam_delegations` and changes `effective_permissions`, the legacy surface
returns HTTP 410 with no writes to either table, and the enforcement-time chain walk denies root /
intermediate revoke, expiry, deactivation, a forged cycle and depth tamper. Verdict: each finding and
**overall B5 = `INDEPENDENTLY VERIFIED`** (engineering scope), zero real API-reachable bypasses. The
implementer did not self-award this status.

**Residual defense-in-depth gap (re-verify report §6, novel probe 1):** a directly forged
`niam_delegations` row can carry an unheld key because the chain walk validates liveness but not
per-hop key attenuation at enforcement. It requires out-of-band write access to the canonical
delegation table (`delegation_service.py:270` is the only production writer), so it is not an
API-reachable bypass of findings 1–3. Recorded for follow-up (recommended: attest the parent key set
in the chain walk and intersect at enforcement); not accepted as production evidence.

---

## 7. Team C review of care-continuum closure migration `20261119_0003` — P1 found, fixed, `INDEPENDENTLY VERIFIED`

A fresh-context Team C review of the DB-critical migration (report
`/tmp/opencode/teamc_cc_review_report.md`) independently reproduced the full lifecycle on four
throwaway PostgreSQL databases and **verified** claims 1–4 (true 62-table missing set, additive /
reversible DDL, 24 enum types with exact ORM labels, full upgrade→downgrade→re-upgrade cycle). It
awarded `VERDICT: BLOCKED` on one reproducible defect:

| Finding | Severity | Evidence | Disposition |
|---|---|---|---|
| `national_encounters.referral_id → national_referrals.id` FK silently absent (ORM declares it with `use_alter=True`, which Alembic's `op.create_table()` skips without emitting `AddConstraint`); bogus `referral_id='NO-SUCH-REFERRAL'` was ACCEPTED on a live migrated DB | **P1** | Team C report §2: 302 declared FKs vs 301 live; `national_encounters` 7 declared vs 6 live; `fk_national_encounters_referral_present=false` | **Fixed**: explicit `op.create_foreign_key("fk_national_encounters_referral", ...)` added after both tables exist, plus a symmetric `op.drop_constraint(...)` before `national_referrals` is dropped in downgrade (the mutual FK cycle with `national_referrals.encounter_id → national_encounters.id` required the compensating ALTER). |
| Regression suite blind to the defect (checked one sample FK + a synthetic probe table, never total FK parity) | **P1 enabler** | Team C report §1 check H | **Fixed**: DB lifecycle test now asserts `live FK count == declared FK count (302)`, asserts the specific cycle-breaking FK exists, and rejects a bogus `referral_id` on a REAL migrated table. Static test asserts every `use_alter=True` FK has a compensating `create_foreign_key` + `drop_constraint`. |
| Enum guard checks only `pg_type.typname`, not labels/schema; downgrade unconditionally `DROP TYPE IF EXISTS` | P2 (latent) | Team C report §2; prior-head DB had 0 enums, so not triggered | Documented residual, not triggered in this chain; no scope change to a DB-critical migration. |
| 125 duplicate index column-sets (~20% of 619) inherited from ORM (`index=True` + explicit `Index`) | P2 | Team C report §1 check I | Documented residual; inherited from ORM metadata, not introduced by this revision. |

**Team C re-verification (fresh-context, 2026-11-19) — `INDEPENDENTLY VERIFIED` (engineering scope):**
report `/tmp/opencode/teamc_cc_reverify_report.md`; all checks A–G PASS: live FK parity 302 declared =
302 live; `fk_national_encounters_referral` present with `ondelete=SET NULL`; bogus `referral_id`
REJECTED, NULL/valid accepted, delete → SET NULL; `downgrade -1` + re-upgrade clean with 0
pre-existing objects lost; both idempotency guards verified; no duplicate constraint/index names.
Falsification proof: reverting the fix in a `/tmp` copy made the two new P1 guards fail (2 failed /
6 passed) — the tests are non-vacuous. Real files: 7 passed / 1 skipped without the URL, 8 passed
with it. No P0/P1 remains. This award was issued by fresh-context Team C, **not self-awarded**;
`PRODUCTION READY` is not awarded, no release claim, no commit. Two latent P2 residuals and one
informational P3 caveat (a database that applied an unreleased pre-fix draft of the same revision ID
cannot be retro-patched by the table-existence guard; no such DB exists) are documented in ledger
§16.1.

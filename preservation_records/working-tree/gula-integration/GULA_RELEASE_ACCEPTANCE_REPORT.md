# GULA RELEASE ACCEPTANCE REPORT (§11)

**Directive:** Supreme Autonomous Completion & National Release Directive — 2026-11-19
**Repository:** `gula-integration` only
**Status legend (exclusive):** `IMPLEMENTED` · `TESTED` · `INTEGRATED` · `INDEPENDENTLY VERIFIED` · `PRODUCTION READY` · `BLOCKED` · `NOT IMPLEMENTED`
**Release position:** **GULA Stable v1.0.0 is NOT declared.** This report is an evidence ledger, not a release certificate. Standing decision: **HOLD** (`GOVERNANCE/FINAL_DECISION.md:13,361`). No `PRODUCTION READY` awarded anywhere; `status_registry.json → production_ready_items = 0`.

> **GULA-OWNER-GATE-2026-11-20 (additive cross-reference):** Sections 1–5 are preserved verbatim; §6 adds the prepared (not approved) owner decisions `OD-001`…`OD-025` and current evidence. No criterion status or historical result changed. Exact scopes: `GULA_EXACT_APPROVAL_RESOURCE_REQUIREMENTS.md`. HOLD stands.

> **GULA-AUDIT-COMPREHENSIVE-REVIEW — OD-001 ACCEPTED (additive cross-reference, 2026-11-20):** The owner explicitly recorded “OD-001: ACCEPTED. The owner explicitly accepts the third independent SEC-015 F-01 review verdict (PASS) and authorizes recording OD-001 as ACCEPTED. This acceptance applies to the defined SEC-015/F-01 engineering scope only.” Reference: `GULA_SEC015_F01_INDEPENDENT_REVIEW_3_REPORT.md` (MD5 `329049ee6bed006901660e43b2d4b995`, 171 lines). This is a documentary acceptance record only: no criterion status, historical result, or release posture is changed. `GULA_OWNER_DECISION_REGISTER.md` §8 is authoritative for OD-001; `OD-002`…`OD-025` remain `BLOCKED`. **HOLD** stands; Stable v1.0.0 **NOT declared**; `PRODUCTION READY` **NOT authorized**; `production_ready_items = 0`.

---

## 1. The 18 final acceptance criteria (directive §9)

| # | Criterion | Status | Evidence / task | Affected files | Owner | Residual risks | Dependencies | Next decision |
|---:|---|---|---|---|---|---|---|---|
| 1 | All in-scope services classified complete or documented out of scope | `IMPLEMENTED` | `GULA_COMPONENT_INVENTORY.md` §4 | inventory file | Autonomous engineering | 0 E2E_VERIFIED; 3 NOT_IMPLEMENTED, 1 BLOCKED | ADR-C/D/G/I/J | owner scope approval |
| 2 | All core contracts compatible | `BLOCKED` | contract gate: 0 STABLE, 5 DRAFT, 11 BLOCKED, 3 NOT IMPLEMENTED | `contracts/*` | Architecture owner | incompatible contracts remain | ADR decisions | owner decision |
| 3 | All required migrations covered and tested | `BLOCKED` | care-continuum closure tested; platform 426 historical / 354 source-based-at-HEAD tables uncovered (`GULA_ORM_MIGRATION_COMPLETENESS_REPORT.md`); W-017 119/872 from artifacts, rerun `BLOCKED` (`GULA_W017_STRICT_GATE_REASSESSMENT.md`) | migration tree | Database owner | schema drift | ADR-A/B | no bulk migration without ownership |
| 4 | All sensitive-data paths protected | `BLOCKED` | SEC-001 audit mis-mapping `INDEPENDENTLY VERIFIED` (engineering scope) fixed & 50/50 calls corrected (`GULA_AUDIT_POSITIONAL_FIX_REPORT.md`); SEC-014 critical-alert audit bypass `INDEPENDENTLY VERIFIED` (engineering scope) fixed (`GULA_AUDIT_BYPASS_FIX_REPORT.md`); criterion stays `BLOCKED` because SEC-004 56 unguarded ops remain open | `GULA_SECURITY_AND_RISK_REGISTER.md` | Security lead | SEC-004 unguarded ops; SEC-001/SEC-014 commits gated by mixed provenance; SEC-015 fixed & `INDEPENDENTLY VERIFIED` (engineering scope) | SEC-004 review | remediate SEC-004; commit SEC-001/SEC-014 |
| 5 | All permissions tested | `TESTED` (scoped) | identity/authz probes; Team C awards | `backend/app/identity/*` | Engineering + Team C | B4/B5 residuals | fresh review for new changes | retain scoped awards |
| 6 | All core clinical journeys tested end-to-end | `BLOCKED` | 0 services E2E_VERIFIED; 7 journeys contract-envelope only | `NATIONAL_HEALTH_PLATFORM_COMPLETION_REPORT.md:90,232-238` | QA lead | no journey proof | runtime environment | execute E2E |
| 7 | Four client platforms buildable and testable | `IMPLEMENTED` (source) / `TESTED` (Web engineering) | Web 15 unit + 13 e2e specs; native source present | `frontend-v3`, `mobile/*`, `hospital_desktop` | Frontend owner | native builds not run | build environment | run native builds |
| 8 | Offline sync proven against failure/duplication/conflict | `BLOCKED` | durability NOT VERIFIED; ADR-J `BLOCKED` | `backend/app/integration/*` | Reliability owner | silent clinical conflict risk | ADR-J | owner decision + tests |
| 9 | Security and performance tests complete | `TESTED` (scoped) / `BLOCKED` (full matrix) | scoped adversarial + Team C; full SAST/DAST/load matrix not run | `GOVERNANCE/ADVERSARIAL_ASSURANCE/*` | QA/Security lead | unmeasured performance | operational resources | run full matrix |
| 10 | Restore and recovery tests proven | `NOT IMPLEMENTED` | `FINAL_ACCEPTANCE_REPORT.md:29,34` | `DATABASE_RECOVERY_REPORT.md` | DevOps owner | RPO/RTO unmeasured | authorised staging | prepare drill; never invent numbers |
| 11 | CI/CD reproducible | `BLOCKED` | 33 workflows present; no CI run this session | `.github/workflows/*` | DevOps owner | presence ≠ success | CI runner | execute clean build |
| 12 | Independent verification complete | `IMPLEMENTED` for named scopes; remainder `BLOCKED` | Team C awards incl. care-continuum migration; SEC-001 and SEC-014 fixes `INDEPENDENTLY VERIFIED` (engineering scope) by fresh-context reviewers | Team C reports / `GULA_AUDIT_POSITIONAL_FIX_REPORT.md` / `GULA_AUDIT_BYPASS_FIX_REPORT.md` | fresh-context Team C | self-award forbidden | fresh reviewer | retain; commission for remaining scopes |
| 13 | No open P0/P1 | `BLOCKED` | SEC-001 P1 engineering fix verified but commit gated; SEC-002 still declares P0/P1 findings not at zero | `GULA_SECURITY_AND_RISK_REGISTER.md` | Security lead | cannot reach RC | SEC-002 owner decision | do not claim; await D-020 |
| 14 | Operational/admin/maintenance docs complete | `IMPLEMENTED` (docs present) / `BLOCKED` (DR/runbook proof) | 685 docs; 77 reports; RC packet not assembled | `docs/*`, `reports/*` | Documentation owner | evidence gaps in runbooks | RC packet | assemble RC docs |
| 15 | No unknown-provenance changes in release | `BLOCKED` | 149 modified + 264 untracked paths, mixed provenance | whole worktree | Autonomous engineering | broad commit not authorised | exact-path provenance review | commit only exact new files |
| 16 | All required official approvals documented | `BLOCKED` | D-020/D-021, MP-001, ODR-001…004, ADR-C…J pending; no MoH/regulator/clinical evidence | `DECISION_REGISTRY.md`, `status_registry.json` | respective owners | no approval claimed | owner action | prepare packets; never fabricate |
| 17 | Installable release candidate exists | `BLOCKED` | no versioned RC packet | — | Release owner | — | criteria 1–16 | do not declare v1.0.0 |
| 18 | Final honest report delivered | `IMPLEMENTED` (this document set) | baseline, inventory, graph, plan, §11 files | root `.md` files | Autonomous engineering | must stay current | — | update after each fix |

---

## 2. Tally (current)

| Status | Count | Criteria |
|---|---:|---|
| `INDEPENDENTLY VERIFIED` | 0 | criterion 12 holds named-scope Team C awards only, not a whole-criterion award |
| `IMPLEMENTED` | 5 | 1, 7, 12, 14, 18 |
| `TESTED` | 2 (scoped) | 5, 9 |
| `INTEGRATED` | 0 | — |
| `BLOCKED` | 10 | 2, 3, 4, 6, 8, 11, 13, 15, 16, 17 |
| `NOT IMPLEMENTED` | 1 | 10 |

Primary status per criterion counted once; partial qualifications are stated in the table above rather than double-counted. Total = 18.

\* The separate programme tally in `FINAL_ACCEPTANCE_REPORT.md:41-46` counts 1 `INDEPENDENTLY VERIFIED` (criterion 5 there = Team C independent verification of critical fixes). The numbering differs between that document and the directive §9 list; both are preserved rather than silently merged. No `PRODUCTION READY` in either.

---

## 3. Authoritative evidence retained

| Item | Evidence | Status |
|---|---|---|
| Full suite (post-fix final tree) | `5124 passed / 28 skipped / 0 failed, EXIT=0 (15m32s)` — `/tmp/opencode/final_tree_full_suite_p1_fixed.log` | `TESTED` |
| Care-continuum DB lifecycle | `1 passed (188s)` — `/tmp/opencode/cc_regression_p1_fixed.log` | `TESTED` |
| Migration graph e2e | upgrade→downgrade→re-upgrade OK; 435→497→435→497 target tables | `TESTED` |
| Team C care-continuum re-verification | `INDEPENDENTLY VERIFIED` engineering scope; checks A–G PASS; falsification proof | `INDEPENDENTLY VERIFIED` |
| Team C identity/security awards | see `GULA_SECURITY_AND_RISK_REGISTER.md` §1 | `INDEPENDENTLY VERIFIED` (named scopes) |
| SEC-001 audit fix post-change full suite | `5134 passed / 28 skipped / 1 failed` — `/tmp/opencode/auditfix_full_suite.log`; sole failure is flaky CPU benchmark (isolated re-run 1 passed @ 7289 ops/s) | `TESTED` |
| SEC-001 audit fix independent review | `INDEPENDENTLY VERIFIED` (engineering scope), fresh-context reviewer, PASS on all 7 checks, 50/50 calls corrected — `GULA_AUDIT_POSITIONAL_FIX_REPORT.md` §5/§7 | `INDEPENDENTLY VERIFIED` |
| SEC-014 audit-bypass fix independent review | `INDEPENDENTLY VERIFIED` (engineering scope), fresh-context reviewer (session `ses_e0ad74e7affewsQeqX0OxMTMvS`), PASS on diff scope / semantic equivalence / chain placement / bypass AST scan / falsification; focused 3/3, related 161/161 — `GULA_AUDIT_BYPASS_FIX_REPORT.md` §5/§9 | `INDEPENDENTLY VERIFIED` |
| SEC-014 audit-bypass fix full suite | `5138 passed / 28 skipped / 0 failed, EXIT=0 (12m13s)` — `/tmp/opencode/auditfix_full_suite_clean.log`, no concurrent pytest; isolated benchmark reps 7/7 pass (min 5626/s vs 2000/s) | `TESTED` |

---

## 4. Non-claims

No Stable v1.0.0 declaration. No release candidate installed. No production deployment. No merge to main or protected branch. No owner / MoH / regulator / clinical / legal approval claimed. No `PRODUCTION READY` awarded. No CI PASS claimed (no CI run this session). No fabrication of test results.

---

## 5. Next decision

`BLOCKED` — the `AUDIT-POSITIONAL-001` and `AUDIT-BYPASS-001` fixes are `INDEPENDENTLY VERIFIED` (engineering scope) and cleared their criterion-4 sub-gates, but criterion 4 remains `BLOCKED` because SEC-004 (56 unguarded operations) is still open and both fixes remain uncommitted pending mixed-provenance sign-off (`lims/routes.py`, `routes/ai.py`). SEC-015 (SQLite chain linkage) is fixed and `INDEPENDENTLY VERIFIED` (engineering scope — pre-insert predecessor read + dialect-scoped transaction lock; fresh-context reviewer PASS; `GULA_SEC015_AUDIT_CHAIN_REMEDIATION_REPORT.md`), with commit `BLOCKED` (no-commit authority); production-PG path was never affected. Criteria 2, 3, 4, 6, 8, 10, 11, 13, 15, 16, 17 remain `BLOCKED`/`NOT IMPLEMENTED`. Release remains with the authorised owner.

---

## 6. Additive update — GULA-OWNER-GATE-2026-11-20 (owner decision packages)

**This section adds decision-package references and current evidence; it does not change any status above, any criterion, or any historical test result.** Sections 1–5 remain the authoritative 2026-11-19 record. Fresh baseline: branch `integration/gula-unification-v1`, HEAD `2206654dc713ea2de8c564a3207dfe05fde23549`; protected MD5s exact; 20 staged `R100` renames; sibling HEAD `f478676b6fc375338648dde46fbf076c015a3f91`; `git diff --check` exit 0; no commit/push/merge/PR/deploy.

### 6.1 Owner decisions prepared, none approved

| Decision ID | Subject | Recommendation | Status |
|---|---|---|---|
| `OD-001` | SEC-015 technical acceptance | Accept engineering evidence; keep commit `BLOCKED` | `BLOCKED` |
| `OD-002` | Provenance / exact-path commits (13 hunks, 4 workstreams) | Four separate scoped sign-offs; keep files `BLOCKED` | `BLOCKED` |
| `OD-003` | ADR-A database ownership (354 tables) | Domain registries + per-context reversible revisions + ship/no-ship | `BLOCKED` |
| `OD-004` | ADR-B reference-table ownership | Option B1, one ORM owner for `national_facilities` | `BLOCKED` |
| `OD-005` | W-017 strict gate authorization/resources | No re-run until trigger + A07/owner + harness + PG16 | `BLOCKED` |

Full twelve-field records, priority order and remaining decisions (`OD-006`…`OD-025`): `GULA_OWNER_DECISION_REGISTER.md`. A–D explanation/evidence/consequences/scope: `GULA_OWNER_DECISION_PACKAGE.md`. Exact approval text and resources: `GULA_EXACT_APPROVAL_RESOURCE_REQUIREMENTS.md`.

### 6.2 Current evidence recorded additively (historical results preserved)

| Item | Current evidence | Prior/historical evidence (retained) |
|---|---|---|
| SEC-015 focused suite | `13 passed` after LOW assertion fix (`sec015_green_lowfix.log`) | red `7 failed / 6 passed`; green `13 passed` |
| Related audit suites | `73 passed` (`sec015_related_audit.log`) | — |
| Disposable PG16 | `PG_VERIFY_RESULT=PASS` (`sec015_pg_verify.log`) | — |
| Full backend suite | `5151 passed / 28 skipped / 0 failed, EXIT=0` (`sec015_full_suite.log`) | `5138 / 28 / 0` (`auditfix_full_suite_clean.log`), `5124 / 28 / 0`, `5134 / 28 / 1` — none overwritten |
| Independent review | Fresh-context reviewer PASS (`ses_e0a984dadffemm3LClZf6oKOPo`), engineering scope only | prior SEC-001/SEC-014 awards retained |
| W-017 | Historical `753 passed / 119 failed / 0 skipped (872)` — **FAILED**, not re-run | 119 and 753 are the failure/pass fractions of one run, not two measurements |
| ORM matrix | 354 source-based discrepancy at HEAD; 51 tables on unregistered bases; 261/51/22/20 classification | 426/340/284 historical discrepancies retained and reconciled |

### 6.3 Status consequence

The criterion tally in §2 is **unchanged**: `INDEPENDENTLY VERIFIED` 0 whole-criterion awards, `IMPLEMENTED` 5, `TESTED` 2 (scoped), `INTEGRATED` 0, `BLOCKED` 10, `NOT IMPLEMENTED` 1. No acceptance, no commit, no deployment and no `PRODUCTION READY` is granted by this update. SEC-015 acceptance requires `OD-001`; commits require `OD-002`; migration work requires `OD-003`/`OD-004`; a W-017 re-run requires `OD-005`. Supporting assessments added: `GULA_DATABASE_OWNERSHIP_PROPOSAL.md`, `GULA_SERVICE_COVERAGE_REASSESSMENT.md` §5, `GULA_SECURITY_OPERATIONAL_READINESS_ASSESSMENT.md`.

Standing decision **HOLD**. Stable v1.0.0 **NOT declared**. `production_ready_items = 0`.

---

## 7. Additive SEC-015 REVIEW-2 synchronization — GULA-MASTER-COMPLETION-2026-11-20

Sections 1–6 and the criterion tally above are preserved unchanged. This section records the mandated verification of the second independent adversarial review only.

| Item | Record |
|---|---|
| Review located and verified | `GULA_SEC015_ADVERSARIAL_REVIEW_2_REPORT.md` (MD5 `f2b44ae6b23ffbbb3f65344aa2126134`), 285 lines, directive `GULA-SEC015-REVIEW-2`, dated 2026-11-20 |
| Verdict | **PASS WITH CONDITIONS** — no CRITICAL/HIGH; unresolved **MEDIUM F-01** |
| F-01 | PostgreSQL advisory-lock serialization holds only at `READ COMMITTED`; chain fork (`broken=[2]`) reproduced at `REPEATABLE READ` and `SERIALIZABLE`; no application isolation enforcement. Fresh 13/13 + 73/73 source-tied runs and disposable PG16 proofs recorded in Review-2 §10 |
| Criterion 4 / 12 impact | **None.** Review-2 does not award `INDEPENDENTLY VERIFIED`; criterion 4 and 12 statuses are unchanged. The prior engineering-scope award remains historical context only |
| OD-001 | **Still `BLOCKED`** — the review is not an acceptance and contains no owner approval text. Owner must decide F-01 explicitly; see `GULA_OWNER_DECISION_REGISTER.md` §6 |
| Prepared work | `GULA_SEC015_F01_REMEDIATION_PACKAGE.md` — R4 change prepared for explicit review, **not implemented**; no source/test change |
| Evidence caveat | `/tmp/opencode/sec015_*` raw logs removed by tmp cleanup; Review-2 §10.1 records them as historical, with fresh source-tied evidence substituted. Historical `5151 / 28 / 0` remains a prior result, not re-verified |
| Invariant | branch `integration/gula-unification-v1`, HEAD `2206654dc713ea2de8c564a3207dfe05fde23549`, 20 staged `R100` renames, staged MD5 `56c524d6ffe9872c3a3ac6eff8c8f203`, three protected MD5s exact, sibling HEAD `f478676b6fc375338648dde46fbf076c015a3f91`, `git diff --check` exit 0 |

Standing decision **HOLD**. Stable v1.0.0 **NOT declared**. `production_ready_items = 0`.

---

## 8. Additive F-01 fix evidence — `GULA-SEC015-F01-REMEDIATION` (2026-11-20)

Sections 1–7 and the criterion tally are unchanged. The owner authorized scoped implementation; the resulting fix is `IMPLEMENTED` + `TESTED` and remains **not** `INDEPENDENTLY VERIFIED`.

| Item | Record |
|---|---|
| Changed files | `backend/app/services/audit_service.py` MD5 `566d64a2f8aa5c898a2511e1bbe304bd`; new `backend/tests/unit/test_audit_chain_isolation_guard.py` MD5 `9ccfa3e92fac50c247f0e839ea180cc8` |
| Evidence | focused 13/13, related 73/73, disposable PG16 suite 12/12 (RC intact; RR/SER/raw-SET/AUTOCOMMIT/undeterminable rejected before write; concurrency, rollback, sequence, append-only triggers verified); logs `/tmp/opencode/f01_verify_*`, all exit 0 |
| Criterion 4 / 12 impact | **None.** No verification or production status awarded; prior historical results unchanged |
| OD-001 | **Still `BLOCKED`** — implementation authorization is not acceptance; fresh independent review required |
| Publication | no commit, push, PR, merge or deploy; HOLD stands; Stable v1.0.0 **NOT declared**; `production_ready_items = 0` |

Standing decision **HOLD**. Stable v1.0.0 **NOT declared**. `production_ready_items = 0`.

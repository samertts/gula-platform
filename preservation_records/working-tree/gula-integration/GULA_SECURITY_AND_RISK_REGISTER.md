# GULA SECURITY AND RISK REGISTER (§11)

**Directive:** Supreme Autonomous Completion & National Release Directive — 2026-11-19
**Repository:** `gula-integration` only
**Status legend (exclusive):** `IMPLEMENTED` · `TESTED` · `INTEGRATED` · `INDEPENDENTLY VERIFIED` · `PRODUCTION READY` · `BLOCKED` · `NOT IMPLEMENTED`
**Security certification:** `GOVERNANCE/FINAL_DECISION.md:46` — **NOT CERTIFIED**. This register is engineering evidence, not a security certificate.

> **GULA-OWNER-GATE-2026-11-20 (additive cross-reference):** No finding is reclassified. SEC-015 technical acceptance is prepared (`OD-001`) and its evidence is recorded in `GULA_SEC015_AUDIT_CHAIN_REMEDIATION_REPORT.md`; commits remain `BLOCKED` (`OD-002`). Updated posture assessment: `GULA_SECURITY_OPERATIONAL_READINESS_ASSESSMENT.md`. D-020/SEC-004 remain `BLOCKED`. No security certificate, no `PRODUCTION READY`; HOLD stands.

---

## 1. Open findings and risks

| ID | Finding / risk | Severity | Owner | Status | Affected files | Tests / evidence | Residual risk | Dependencies | Next decision |
|---|---|---|---|---|---|---|---|---|---|
| SEC-001 | Audit `log_action` positional-argument regression: 50 call sites mis-map arguments after commit `aae20c89` inserted `lab_id` before `details`; entity IDs land in `resource_type`, lab IDs in `user_role`, detail strings in `lab_id` | **P1** | Autonomous engineering + fresh-context independent reviewer | `INDEPENDENTLY VERIFIED` (engineering scope); commit `BLOCKED` | `backend/app/nhdw/{services,offline}.py`, `backend/app/nursing/{coordination,medication,services}.py`, `backend/app/lims/{services,routes}.py`, `backend/app/services/hospital_service.py` | `GULA_AUDIT_POSITIONAL_FIX_REPORT.md`; 50/50 calls converted to keywords; reviewer PASS on all 7 checks; focused 11/11; related 38/38; full suite 5134/28/1 (flaky benchmark, isolated re-run passed) | fix verified; commit gated by mixed provenance in `lims/routes.py`; 2 pre-existing LIMS/hospital observations recorded, not introduced | provenance sign-off on `lims/routes.py` before exact-path commit | commit fix after sign-off; do not claim security certification |
| SEC-014 | **AUDIT-BYPASS-001:** `routes/ai.py::_emit_critical_alert` constructed `AuditLog` directly (blame 2026-07-04, predating the chain), writing critical-result alerts with NULL `chain_hash` — OUTSIDE the tamper-evident chain (verify skips NULL rows). Distinct from SEC-001 (canonical writer was bypassed, not mis-called). | **P1** | Autonomous engineering + fresh-context independent reviewer | `INDEPENDENTLY VERIFIED` (engineering scope); commit `BLOCKED` | `backend/app/routes/ai.py`, `backend/tests/unit/test_audit_bypass_regression.py` | `GULA_AUDIT_BYPASS_FIX_REPORT.md`; routed through canonical `log_action`; fresh-context reviewer verdict `INDEPENDENTLY VERIFIED (engineering scope)`; focused 3/3 (75.12s); related 161/161; zero direct `AuditLog(...)` in any route module | commit gated by mixed provenance (`require_ai_operator` changes in `routes/ai.py`); SEC-015 chain linkage now fixed & `INDEPENDENTLY VERIFIED` (engineering scope) | provenance sign-off on `routes/ai.py` | commit after sign-off; do not claim security certification |
| SEC-015 | SQLite multi-row audit chain linkage: non-PostgreSQL `log_action` branch read `_get_last_chain_hash` AFTER the row was flushed, so the just-inserted NULL-hash row became its own predecessor and every row chained to genesis; `verify_audit_chain` reported tampered on multi-row SQLite. **Production PostgreSQL path was correct.** Root cause: commit `2cdc5479` FIXED the ordering but `f0b021bd3` regressed it. Timestamp canonicalization (`_canonical_audit_timestamp`, `2fb4fd11`) was already correct at HEAD. | **P2** (test-env artifact; prod path correct) | Autonomous engineering + fresh-context independent reviewer | `INDEPENDENTLY VERIFIED` (engineering scope); commit `BLOCKED` (no-commit authority) | `backend/app/services/audit_service.py`, `backend/tests/unit/test_audit_chain_integrity.py` (new), `backend/tests/test_compliance_integrity.py:58-77` | `GULA_SEC015_AUDIT_CHAIN_REMEDIATION_REPORT.md`; reviewer verdict PASS (`ses_e0a984dadffemm3LClZf6oKOPo`); pre-insert predecessor read both dialects; PG advisory xact lock + SQLite write reservation; focused 13/13; related 73/73; disposable PG16 PASS; hash re-stitching workaround removed | PG advisory lock assumes READ COMMITTED (documented); pre-commit anchor write (pre-existing, not introduced); SQLite multi-process not supported | no commit authority; ARCH/DB owner ADR still optional | record full-suite result; do not claim security certification or production readiness |
| SEC-002 | Critical security findings not at zero | P0/P1 (declared) | Security lead | `BLOCKED` | `FINAL_ACCEPTANCE_REPORT.md:20` | `FINAL_DECISION.md:46` NOT CERTIFIED | release criterion 1 unmet | D-020 owner decision | do not claim security certification |
| SEC-003 | High findings unmitigated / risk-accepted | High | Security lead | `BLOCKED` | `FINAL_ACCEPTANCE_REPORT.md:21` | — | release criterion 2 unmet | D-020 | owner decision |
| SEC-004 | 56 live OpenAPI operations without declared security (documented 2026-11-17) | High | Engineering | `BLOCKED` | `GOVERNANCE/NATIONAL_SERVICE_INVENTORY.md`; `contracts/export/openapi.json` | inventory scan | critical path may lack Authorisation/Audit | per-route review | classify each as public-by-design or remediate |
| SEC-005 | B4 residuals R-1…R-4; B5 forged-DB-row defence-in-depth gap; end-point residuals R-01…R-11 | Medium | Engineering + Team C | `IMPLEMENTED` (documented residuals) | `GOVERNANCE/ADVERSARIAL_ASSURANCE/*` | `MASTER_EXECUTION_STATUS.md:41,193-198`; `FINAL_DECISION.md:166` | residual bypass surface | owner acceptance | document in RC known limitations |
| SEC-006 | Identity impersonation / privilege escalation / replay / cross-tenant / enumeration / merge abuse probes | High | prior engineering + Team C | `TESTED` / `INDEPENDENTLY VERIFIED` (named scopes) | `backend/app/identity/*` | 13/13, 57+, 10 probes | no full programme-wide attack matrix | fresh-context review for new changes | keep awards; re-test only on change |
| SEC-007 | Secrets / PHI in code or logs | High | Autonomous engineering | `IMPLEMENTED` for scoped files (none found in new work) | new root files + audit fix scope | secret/PHI scan to run before any commit | untracked tree may contain unknown material | commit-time scan | scan exact staged paths before commit |
| SEC-008 | Real patient data in tests | High | Autonomous engineering | `IMPLEMENTED` (none used) | all test work | synthetic data only | — | — | maintain |
| SEC-009 | Production DDL / `alembic stamp` / `create_all()` masking | High | Autonomous engineering | `IMPLEMENTED` (none performed) | `backend/migrations/*` | disposable PG only | program-wide schema gap remains (SEC-010) | — | maintain |
| SEC-010 | Schema drift: W-017 strict gate 753 passed/119 failed (same 872-test run); 426 historical / 354 source-based-at-HEAD unmigrated ORM tables; `DocIntelBase`/`InsBase` unregistered | High | Database owner | `BLOCKED` | `backend/migrations/env.py`, `ins_*`, doc-intel tables | `FINAL_DECISION.md:348-352`; `NATIONAL_HEALTH_PLATFORM_COMPLETION_REPORT.md:18,238`; `GULA_ORM_MIGRATION_COMPLETENESS_REPORT.md` (354 at HEAD, 51 tables on unregistered bases, single head); `GULA_W017_STRICT_GATE_REASSESSMENT.md` (rerun `BLOCKED`) | silent schema gaps hidden by `create_all()` in tests | ADR-A/B owner decision | no bulk migration without ownership analysis |
| SEC-011 | Insurance surface: 84 unserved endpoints, 30 unmigrated `ins_*` tables | High | Program Director | `BLOCKED` | `backend/app/insurance/*` | `GULA_COMPONENT_INVENTORY.md` §4 #16 | incomplete service exposed as if complete | ADR-G/I | out-of-scope proposal documented |
| SEC-012 | Government / regulator / licensed-terminology integrations assumed | High | Autonomous engineering | `BLOCKED` | `backend/app/{fhir,integration,interoperability}/*` | no documented authority/credential | false integration claim | documented approval | use documented interfaces only |
| SEC-013 | CI security gates present but not executed this session | Medium | DevOps | `BLOCKED` | 33 workflows | workflow inspection | workflow presence ≠ passing gate | CI runner | execute when authorised |
| ARC-001 | Circular-import coupling in `backend/app` (pre-existing) | Medium | Architecture owner | measurement + runtime-impact `TESTED`; remediation `BLOCKED` | `backend/app/kernel/*` (5 hard import-time cycles) + lazy-mitigated cycles in `core`, `security`, `middleware`, `national/background_platform` | read-only AST + Tarjan SCC over 2,045 modules (2026-11-19): 5 hard cycles, all in `app.kernel`; see `GULA_DEPENDENCY_GRAPH.md` §4. Runtime impact: 10/10 import-order permutations PASS; `create_app()` PASS (125 routes); kernel CLI import PASS; `alembic heads` PASS (single head) — no observed failure, so kernel NOT restructured for static score | maintainability / import-order fragility; no security exploit claimed | ADR-F topology decision (owner-gated) | prepare for ADR-F; do not rewire without approval |

---

## 2. Hard rules demonstrated this session

| Rule | Status | Evidence |
|---|---|---|
| No production DB/Redis connection | `IMPLEMENTED` | only disposable PG used for care-continuum lifecycle; no Redis access |
| No destructive migration | `IMPLEMENTED` | additive/reversible migration only; upgrade/downgrade/re-upgrade on disposable DB |
| No deletion of failing tests | `IMPLEMENTED` | none deleted |
| No reduction of security/coverage standards | `IMPLEMENTED` | none reduced |
| No `PRODUCTION READY` self-award | `IMPLEMENTED` | no award in any new file |
| No fabricated approval / release / deployment | `IMPLEMENTED` | none claimed |

---

## 3. Release-quality policy (targets, not achieved claims)

No open P0/P1 at RC; no privilege escalation; no silent data loss; no duplicate confirmed health identity; no unauthorised PHI disclosure; no critical API path without Authorisation **and** Audit; no untested migration; no exposed secret; no test deleted to hide failure; no unmeasured performance figure; no unproven integration claim. Every item above is `BLOCKED` unless a specific row states `TESTED` / `INDEPENDENTLY VERIFIED` with evidence.

---

## 4. Next decision

`BLOCKED` — SEC-001 is fixed, tested (`11/11` focused, `38/38` related, full suite `5134/28/1` with the sole failure an isolated-confirmed flaky CPU benchmark) and `INDEPENDENTLY VERIFIED` (engineering scope) by a fresh-context reviewer — this is evidence that the identified audit-column mis-mapping is corrected, **not** a claim that the whole audit trail is certified. SEC-001's commit remains `BLOCKED` by mixed provenance in `backend/app/lims/routes.py`. SEC-014 (AUDIT-BYPASS-001) is fixed, tested (`3/3` focused, `161/161` related, full suite `5138/28/0, EXIT=0 (12m13s)`) and `INDEPENDENTLY VERIFIED` (engineering scope); commit `BLOCKED` by mixed provenance in `routes/ai.py`. SEC-015 (SQLite chain linkage) is fixed (pre-insert predecessor read + dialect-scoped transaction lock) and `INDEPENDENTLY VERIFIED` (engineering scope) by a fresh-context reviewer — see `GULA_SEC015_AUDIT_CHAIN_REMEDIATION_REPORT.md`; commit `BLOCKED` (no-commit authority), production-PG path was never affected. SEC-002/003/004/010/011/012/013 remain open. Security certification stays with the security lead / Program Director (D-020); this register certifies nothing.

---

## 5. Open risks — 2026-11-20 checkpoint (ordered by severity)

This section is additive. It does not change §1–§4 and awards no acceptance or production status.
HOLD = TRUE; `production_ready_items = 0`; Stable v1.0.0 NOT DECLARED; PRODUCTION READY NOT AUTHORIZED.

| # | Severity | Risk / finding | Evidence verified this checkpoint | Disposition |
|---|---|---|---|---|
| 1 | **HIGH** | Publicly exposed DeepSeek API key — `ROTATION UNVERIFIED` | `DEEPSEEK_API_KEY` (`sk-` shape) committed 2026-03-08 in `d2863c35…`, ancestor of `origin/main`; absent at HEAD; only generic runbook, no dated provider revocation/replacement record | Owner must revoke at provider, issue least-privilege replacement, update secret store/consumers, review usage/billing, record key ID + date. No history rewrite. `AUDIT_EXECUTION_RECORDS/ENV_INCIDENT_REVIEW.md` |
| 2 | **HIGH** | Mixed provenance blocks safe preservation | 20 staged `R100` (MD5 `56c524d6…`), 162 modified, 664 untracked (3 checkpoint documents added) | No commit/push/PR; owner scope separation required first |
| 3 | **HIGH** | F02/F03 decision packets are **not decision-ready** (independent verdict FAIL) | Packets cite uncommitted working-tree state; HEAD has different code; decisive RED tests declare SQLite although the guard is PostgreSQL-only; 1 CRITICAL + 2 HIGH (F02), 1 CRITICAL + 6 HIGH (F03) | Return to preparation, rewrite against explicit baseline, re-review. No implementation. `AUDIT_EXECUTION_RECORDS/PACKET_REVIEW_2026-11-20.md` |
| 4 | **MEDIUM** | P-02 fail-closed availability impact on clinical path is unquantified | Re-raising from `_emit_critical_alert` reaches `/ai/interpret` before interpretation; packet understates it | Owner must accept the endpoint-level trade-off explicitly after packet correction |
| 5 | **MEDIUM** | P-03 actor attribution, secret-access boundary, DB session and exactly-once claims unverified | HEAD takes actor from request body; `access_audit_log()` has zero callers; no DB dependency; no dedupe parameter | Must be resolved in the rewritten packet; no implementation |
| 6 | **MEDIUM** | Audit-completion pressure: 16 AUD-F findings remain open | F01/F04 engineering-closed only; 6/29 ≈ 20.7% independently reviewed is not completion | Do not claim audit completion; all five statuses kept separate |
| 7 | **MEDIUM** | Pre-review residuals on accepted-engineering packages | P-15 fail-closed trade-off; P-13 retry/double-charge idempotency; P-16 F6/F7/F9; P-01 advisory `previous_hash`; P-04 L1/L2/INFO | Retained as open acceptance conditions; P-04 code frozen after review |
| 8 | **LOW** | P-04 residual: count/verify TOCTOU and session creation outside mapped-error boundary | `AUDIT_EXECUTION_RECORDS/P-04_AFTER.md` | Future acceptance only; no post-review edit without a new review cycle |
| 9 | **LOW** | P-13/P-15 original fail-closed and idempotency owner trade-offs not signed | Scorecard §2.1 | Owner decision outstanding |
| 10 | **INFO** | PR #307 OPEN and untouched; backup branch preserved at committed HEAD | `gh pr view 307`; `git ls-remote` | No action; do not modify |

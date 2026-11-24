# Execution Ledger

**Program:** GULA Stable v1.0.0 Unification + GLOSI Master Registry
**Date:** 2026-11-16
**Branch:** `integration/gula-unification-v1`
**State:** All changes uncommitted. No production database, main worktree, or Platform-Core was modified.

Status vocabulary: `PASS` / `FAIL` / `BLOCKED` / `NOT RUN` / `UNKNOWN` / `PARTIAL`.

## 1. GULA unification

| ID | Scope | Key files | Result | Tests / evidence | Status |
|---|---|---|---|---|---|
| GULA-001 | NR-010 downgrade repairs and round trip | `20260716_0004`, `20260716_0003`, `20260324_0010`, `20260324_0009`, `20260324_0006` | Fresh PG16 `upgrade head` → `downgrade base` → `upgrade head` PASS; 433 tables; 3 reference tables intentionally remain | `/tmp/opencode/nr010_*.log`; `DATABASE_COMPATIBILITY_REPORT.md` §9 | PASS |
| GULA-002 | Canonical workflow integration (CR-1) | `app/workflows/*`, `identity/api/router.py`, `factory.py`, archived runtime | Single `/workflows` mount; 7 paths / 8 operations; boot 125 routes; auth 401; DB bridge works | 10/10 `test_identity_workflows_canonical.py` | PASS |
| GULA-003 | Search service promotion | `app/capabilities/search_service/*`, document-intelligence wiring | Canonical search/indexer/semantic services; old namespace vacated | Validator/scaffold: 1 PASS, 1 environment-only fail (kernel not initialized) | PARTIAL |
| GULA-004 | National document PDF promotion | `capabilities/document_management/pdf_generator.py`, national route/service | Canonical `shared/pdf` adapter; OpenAPI pinned | 13/13 `test_document_platform_pdf.py` | PASS |
| GULA-005 | Domain Platform + governance engine | `app/domain_platform/*`, `scripts/domains/*`, migration, 16 routes | 11/11 domains certified; isolation PASS | 71/71 `test_domain_platform.py` | PASS |
| GULA-006 | Professional registry | `app/identity/professional_registry/*` | Verify-only privilege activation; 7 routes; audit actions unioned | 12/12 `test_niam_professional_registry.py` | PASS |
| GULA-007 | Communication experience + providers | `app/communication/*`, shared providers, model, router | Ported; local circuit breaker superset adopted; `signxml` installed | 198/198 communication tests | PASS |
| GULA-008 | Full backend suite stabilization | `tests/test_niam_v2.py`, `tests/test_document_intelligence.py`, `app/blood_bank/domain/state_machine.py` | Fixed 3 stale workflow imports and 1 missing `verified -> in_progress` transition | `3135 passed, 27 skipped, 0 failed`; 577.65s; exit 0; `/tmp/opencode/full_suite_integration_2.log` | PASS |
| GULA-009 | Existing-database upgrade rehearsal (MIG-EXISTING) | — | Only empty disposable PG16 databases exercised; no supported prior snapshot rehearsal | — | NOT VERIFIED |
| GULA-010 | Local service extractions (9 services) | `app/services/{lab,sample,dashboard,quality_control,metrics,mobile,admin,test_result,stats}_service.py`; route modules `dashboard.py`, `stats.py`, `metrics.py`, `mobile.py`, `quality_control.py` | **5 of 9 routes delegate** (`dashboard` 28 LOC, `stats` 88, `quality_control` 130, `metrics` 343, `mobile` 426) and re-export the names tests import (`evaluate_westgard`, `_role_ar`, `_get_permissions`); route↔service shadowing fixed (`stats.py` called itself recursively); metrics fail-closed without a bearer token. **4 of 9 are NOT wired**: `admin.py` (1 037 LOC), `test_results.py` (731), `labs.py` (231), `samples.py` (217) still hold the original inline logic while `admin_service` / `test_result_service` / `lab_service` / `sample_service` are imported by no route — verified byte-identical for `admin_service.toggle_lab` vs `routes/admin.py:toggle_lab` | `test_system_improvements.py` 113 passed; full suite 3,313 passed / 0 failed; `grep -q <service> <route>` matrix → 5 YES / 4 NO | **PARTIAL** |
| GULA-011 | Preserved local tests/gates reconciliation | `tests/unit/*`, ported service tests, `frontend-v3/src/**/*.test.tsx` | All collected suites pass. One stale frontend assertion repaired: `MobileBottomNav` accessible name became `More` in `f2ae0c7e` (WCAG 2.5.3, matches visible label) while the test still expected `Open all sections` | Backend full suite 3,313 passed / 0 failed; vitest 16 files / 56 tests passed | PASS |
| GULA-012 | Frontend merge per CR-2 | `frontend-v3/*`, `config/nginx/conf.d/api.conf` (read), `.github/workflows/frontend-pwa.yml` (read) | Contract audited against the **runtime** spec (1,807 paths): 825/926 unique calls resolve (89.1 %, was 86.5 %). `/api` single-strip convention aligned (Vite rewrite added, Vercel left preserving `/api`), NIAM double prefix repaired (60 paths), 3 dead wrappers removed, axios/follow-redirects bumped to 0 advisories. 101 remaining gaps classified (7 categories) with no page rewritten | `typecheck`/`lint`/`test`(56)/`build`/`npm audit` all EXIT 0; 5 governance scripts EXIT 0; `GOVERNANCE/FRONTEND_INTEGRATION_REPORT.md` | PASS |
| GULA-013 | Security review (authn/authz) | `GOVERNANCE/SECURITY_REVIEW_REPORT.md`; `backend/app/control_plane/routes.py`, `app/identity/api/router.py`, `app/{governance,lifecycle_platform,pilot_platform,certification,contracts}/*`, `app/security/{redis_client,csrf,auth}.py` | **NOT CERTIFIED.** Route walk: 2,132 endpoints, 1,974 guarded (92.6 %), 158 unguarded → **91 real gaps** (governance 28, lifecycle 18, pilot-platform 14, certification 9, contracts 9, niam 8, `/api/ai` 3, lims 2); 67 unguarded hits proven to be public-by-design or in-body-guarded. Blocking: **S-01** control plane has authentication but no authorization (any `citizen` token can rewrite global config, poison the policy store, deploy releases); **S-02** deploy actor/approver taken from the request body (`master_admin` spoof); **S-03** NIAM persons/sessions/devices unguarded; **S-04** anonymous release approval + go/no-go gate writes; **S-05** `POST /governance/audit-events` forges `actor_id`; **S-06** Redis loss silently downgrades revocation/rate-limit/idempotency to per-worker memory. Verified sound: JWT alg pinning + separate refresh secret, `httpOnly`+`SameSite=Strict` cookies, fail-closed CSRF, SHA-256+HMAC audit chain, global rate limiting, no tracked secrets, edge HMAC, fail-closed webhooks. Frontend deps audit-clean | 40/40 runtime probes passed (`/tmp/opencode/security_probe3.log`) + 10/10 supplementary control-plane reads (`/tmp/opencode/security_probe_cp.log`); 1,974/2,132 guarded; `npm audit --omit=dev` → 0 | PARTIAL — findings closed by GULA-015, review pending |
| GULA-014 | Release candidate | — | Not started | — | NOT STARTED |
| GULA-015 | Security remediation S-01…S-12 (authorized by Program Director) | `app/control_plane/routes.py`, `app/identity/api/access.py`, `app/security/platform_access.py`, `app/governance/routes/governance_routes.py`, `app/security/{redis_client,auth,dependencies,rate_limit}.py`, `app/routes/{ai,ai_telemetry,verification}.py`, `app/lims/routes.py`, `app/config.py`, `app/services/{mobile_service,order_service}.py`, `app/routes/{login,mobile,citizen_portal,demo}.py` + 6 new regression test files | **All 12 findings closed in the working tree (uncommitted, awaiting independent review).** Re-derived route walk: 2 133 endpoints / **2 066 guarded** / 67 unguarded, and those 67 are exactly the public-by-design set → **0 residual authz gaps** (was 91) *(walk numbers superseded by the reconstructed walker in GULA-016: 2 064 guarded / 69 unguarded — heuristic delta explained in `PUBLIC_ENDPOINT_REGISTER.md` §2)*. Distinct policy modules: control-plane (S-01/S-02 two-person release), NIAM registry reader/writer (S-03), national governance reader/writer (S-04/S-08/S-10/S-11), `security_store()` fail-closed boundary (S-06), HTTPS-derived secure cookies (S-07), AI-operator read gate (S-09), LIMS authentication (S-12). No endpoint regressed to unguarded | `test_control_plane_authorization` 21, `test_niam_registry_authorization` 21, `test_national_governance_authorization` 29, `test_governance_audit_authorization` 11, `test_governance_anonymous_access` 8, `test_security_store_policy` 12, `test_ai_platform_authorization` 8, `test_lims_quality_authorization` 5; adjacent regression runs: security/config 55 + 126 passed, governance 222 passed, AI/LIMS 114 passed; full suite re-run in §3; walk + classification in `/tmp/opencode/remediation/` | **PARTIAL** (code complete, unreviewed/uncommitted) |
| GULA-016 | Independent post-remediation verification: S-13 + kill-switch fail-closed + 69-endpoint review (Program Director items 4–7) | `app/routes/verification.py` (S-13), `app/core/kill_switch.py` (fail-closed), `tests/test_professional_verification_authorization.py` (new), `tests/test_kill_switch_fail_closed.py` (new), stale mock targets in `tests/test_{stress,comprehensive}.py`, `GOVERNANCE/PUBLIC_ENDPOINT_REGISTER.md` (new) | **S-13 found and fixed:** self-service verification could activate a `doctor` account without licence approval (CWE-863) — now `SELF_VERIFIABLE_ROLES=("citizen",)`, professional activation only via `PUT /admin/doctors/{id}/approve`. **Kill-switch fail-open closed:** unreadable shared state ⇒ ACTIVE in production/staging (CRITICAL log, `shared_state_readable`), dev/test unchanged; policy-engine proof that autonomous actions are blocked. **All 69 unguarded endpoints independently reviewed** (handler-by-handler): 0 confidential-data exposures, 0 unauthenticated state changes; 11 residuals R-01…R-11 documented and left **open**. Stale `test_comprehensive.py:654` mock target corrected to `redis_client.cache` (S-06 moved the singleton); original test intent unchanged. Frontend re-verified (typecheck/lint/vitest 56/build/audit all 0) | `test_professional_verification_authorization` 7, `test_kill_switch_fail_closed` 9 (+ `test_control_layer` 64 combined), adjacent auth suites 44, `test_stress.py`+`test_comprehensive.py` 124, **full suite 3 447 passed / 0 failed / 27 skipped, exit 0, 731.46 s**; walk 2 133/2 064/69 → `classify_unguarded.py` exit 0 (69/69, 0 residual); register §1–§6 | **PARTIAL** (complete, unreviewed/uncommitted; residuals open) |
| GULA-017 | W1 strict-schema functional validation (migration-only DB, evidence-only gate) | External harness `/tmp/opencode/strict-w1/` (strict conftest, 53 byte-identical modules); disposable clone `gula_w1_strict_20261117` (rev `20261114_0006`, 433 tables); no repo file changed | **FAIL.** **753 passed / 119 failed / 0 skipped** (273.09 s) vs **872 passed / 0 failed** (297.98 s) for the identical modules under the SQLite `create_all()` control → all 119 failures are schema-induced. Classification: 43 column drift, 33 missing table, 20 runtime guard, 4 append-only trigger, 4 cascade, 4 id-assumption, 4 harness path, 4 assertions, 2 type overflow, 1 FK. Schema gap: 756 ORM (per-base) / 416 present / **340 missing** tables; **82 tables / 664 columns** missing. Fingerprint identical before/after → zero DDL. NR-011 refined by probes A/B/C to a **two-part** fix | `logs/strict_suite_20261117_063054.log`, `logs/strict_run2.xml`, `logs/baseline_sqlite.xml`, `remediation/w1/{strict_classification,schema_gap_strict,schema_drift_strict,run1_vs_run2_nodes}.json`, `ALEMBIC_PROBE_EVIDENCE.md`; `DATABASE_COMPATIBILITY_REPORT.md` §11, `PHASE_C_DATABASE_REHEARSAL_REPORT.md` §13 | **FAIL — evidence appended** (no fix attempted; ADR-A/ADR-B boundary) |

## 2. GLOSI Master Registry

| ID | Phase | Deliverables | Verification | Status |
|---|---|---|---|---|
| GLOSI-001 | Phase 0 — Discovery | Repository baseline, existing-research inventory, integration constraints | Read-only inspection; no prior registry | PASS |
| GLOSI-002 | Phase 1 — Governance | Governing docs, 100-point framework, schema, integration/security/license policy | Documents reviewed for internal consistency | PASS |
| GLOSI-003 | Phase 2 — Registry | 16-record registry, deterministic builder, validator/exporter, 20 tests, 16 proposed decision records | Validator PASS; tests 20/20; canonical export byte-identical; ruff 0 | PASS |
| GLOSI-004 | Phase 3 — Initial research B1 | 16 source-verified projects (OpenELIS, SENAITE, OpenMRS, Bahmni, DHIS2, SORMAS, OpenHIE, OpenHIM, HAPI FHIR, OCL, Keycloak, OpenBao, OpenTelemetry, Prometheus, CouchDB, Automerge) | 16/16 repository metadata verified; evidence snapshot hashes 46 files | PARTIAL |
| GLOSI-005 | Phase 4 — Quality assurance | Structural, scoring, decision gate, export, history, link checks | Automated PASS; human security/legal review NOT RUN | PARTIAL |
| GLOSI-006 | Phase 5 — Program initiation | Reports 0–5, opportunities, next batches, stop conditions | Reports published; no project approved | PASS |

## 3. Commands and exit codes

| Command | Exit |
|---|---|
| `python3 GLOSI/tools/glosi_registry.py validate GLOSI/REGISTRY/registry.json` | 0 |
| `python3 -m unittest discover -s GLOSI/tests -v` | 0 (20 tests) |
| `ruff check GLOSI/tools GLOSI/tests` | 0 |
| `pytest tests/ -q` (integration backend — **pre-remediation baseline**) | 0 (3,313 passed, 27 skipped; `/tmp/opencode/full_suite_3.log`, 758 s) |
| `pytest tests/test_niam.py tests/test_niam_v2.py tests/test_niam_professional_registry.py tests/test_governance.py tests/test_db_adaptive.py tests/test_device_trust.py tests/identity -q` | 0 (416 passed, 4 skipped) |
| `npm ci` (frontend-v3) | 0 (609 packages, reproducible from lockfile) |
| `npm run typecheck` | 0 |
| `npm run lint` (`--max-warnings 0`) | 0 |
| `npm test` (vitest) | 0 (16 files / 56 tests) |
| `npm run build` | 0 (2.90 s; PWA precache 146) |
| `npm audit --omit=dev` | 0 (0 vulnerabilities) |
| `node scripts/verify-integration-boundary.mjs` | 0 |
| `node scripts/verify-frontend-unification.mjs` | 0 |
| `node scripts/verify-contract-governance.mjs` | 0 |
| `node scripts/data-source-inventory.mjs` | 0 (94 surfaces) |
| `node scripts/verify-data-source-governance.mjs` | 0 |
| `python /tmp/opencode/audit_auth_coverage.py` (live route walk) | 0 (2,132 endpoints / 1,974 guarded / 158 unguarded; `/tmp/opencode/auth_coverage.json`) |
| `pytest tests/test_security_probe_tmp.py` (40 runtime probes, temporary file, since removed) | 0 (40 passed, 271.89 s; `/tmp/opencode/security_probe3.log`) |
| `pytest tests/test_security_probe_cp_tmp.py` (10 control-plane reads, temporary file, since removed) | 0 (10 passed, 151.07 s; `/tmp/opencode/security_probe_cp.log`) |
| `python /tmp/opencode/remediation/audit_auth_coverage_after.py` (post-remediation walk, **reconstructed** after tmp cleanup) | 0 (2,133 endpoints / 2,064 guarded / **69 unguarded = public-by-design only**; `/tmp/opencode/remediation/auth_coverage_after.json`) |
| `python /tmp/opencode/remediation/classify_unguarded.py` | 0 (69/69 partitioned into 11 categories, **0 residual gaps**; `unguarded_classification.json`) |
| `pytest tests/test_control_plane_authorization.py tests/test_niam_registry_authorization.py tests/test_national_governance_authorization.py tests/test_governance_audit_authorization.py tests/test_governance_anonymous_access.py tests/test_security_store_policy.py tests/test_ai_platform_authorization.py tests/test_lims_quality_authorization.py` | 0 (all pass; per-file counts in GULA-015) |
| `pytest tests/test_professional_verification_authorization.py` (S-13) | 0 (**7 passed**, 77.39 s) |
| `pytest tests/test_security_demo_contract.py tests/test_routes_register.py tests/test_login_protection.py tests/test_identity_authentication_security.py tests/test_public_demo_security.py` (adjacent auth regression) | 0 (**44 passed**, 92.38 s) |
| `pytest tests/test_kill_switch_fail_closed.py tests/test_control_layer.py` | 0 (**64 passed**; 9 are the new fail-closed tests) |
| `pytest tests/ -q` (full tree, **post S-13 + kill-switch + stale-mock fix**) | 0 (**3 447 passed, 27 skipped, 0 failed, 731.46 s**; `/tmp/opencode/remediation/full_suite_final_post_s13.log`) |
| `pip-audit -r requirements-lock.txt --no-deps --disable-pip` (backend runtime deps) | 1 (**55 known vulnerabilities in 6 packages** — pillow 42, pyasn1 4, urllib3 3, joserfc 2, dnspython 2, certifi 2; `/tmp/opencode/remediation/pip_audit_backend.log`) |

### 3.1 Phase 1 — dependency remediation (2026-11-17)

| Command | Exit |
|---|---|
| `pip` wheel download path (2 attempts, PID 72597 attempt 2 **TERMINATED**) | **2 / BLOCKED** — network throttling (~13–33 kB/s), `ReadTimeoutError`. Recorded as **BLOCKED by network throttling**, *not* a resolution failure. Artifacts preserved |
| `uv 0.11.26 pip compile requirements.txt … --python-platform linux --python-version 3.12` (same manifests, same PyPI, same interpreter 3.12.13, metadata-only) | **0** — **72 pins**, byte-identically reproducible across two runs (`/tmp/opencode/remediation/uv_compile_*.txt`) |
| `pip-audit` on the **freshly resolved** set (metadata-only, no wheel download) | **0 — "No known vulnerabilities found"** |
| `pip-audit` on the **lock** after raising the six floors | **0 — "No known vulnerabilities found"** |
| `pip-audit` on the **installed** set in the isolated audit venv | **0** |
| Dependency compatibility suite (behaviour-only, 33 tests) — old set vs new set | **0 / 0** (**33 passed** both) |
| Targeted remediation suite (225 tests) | **0** (**225 passed**) |
| `pytest tests/ -q` (full tree, **after dependency upgrades**) | **0** (**3 480 passed, 27 skipped, 0 failed, 506.93 s**) vs 3 447 pre-upgrade baseline (+33 = the new compat tests; 0 regressions) |

### 3.2 Phase C — existing-database rehearsal (2026-11-17, disposable clones only)

| Command | Exit |
|---|---|
| `CREATE DATABASE gula_unify_rehearsal_20261117_085724 TEMPLATE gula_unify_scratch` (rev `20260815_0022`, 405 tables, 51 rows) | 0 |
| `alembic upgrade head` on that clone (**20 revisions**, 3 branches, 2 merges) | **0** (17 s; rev `20261114_0006`; **433** tables) |
| Business-data reconciliation (per-table `count(*)` + `md5(string_agg(row::text))`) | **0** — 50 rows identical (`niam_roles` 7, `niam_permissions` 20, `niam_role_permissions` 23); only `alembic_version` differs (by design) |
| `docker exec gula-postgres pg_dump --schema-only` (host `pg_dump` 14 **cannot** dump a v16 server — first attempt exit 1, 0-byte output retained) | 0 for all three dumps (prior / upgraded / fresh) |
| `diff` upgraded vs fresh-build schema (restrict tokens normalised) | **43 lines = exactly 1 divergence** (`pharmacy_drug_catalog.id` legacy sequence default → **NR-012**); no table/column/type/index/constraint difference |
| Schema fingerprint (`schema_fingerprint.sql`) fresh build vs `downgrade base` → `upgrade head` | **identical** — both `3b2d9499d019503bf1ff5644f713cd5f272705f544862d8022887a516f973568` (0 diff lines) |
| `alembic downgrade 20260815_0022` (partial/block rewind, on a separate clone) | **0 — but NOT a clean reversal**: **2** `alembic_version` rows + **7** residual tables (`blood_bank_*` ×6 + `clinical_command_receipts`), 412 tables instead of 405 |
| `alembic downgrade base` (full teardown, second clone) | **0** (25 s; 0 version rows; **4** residual tables = `alembic_version` + `facilities`/`organizations`/`national_facilities`) |
| `alembic upgrade head` after teardown | **0** (81 s; rev `20261114_0006`; 433 tables; fingerprint identical to fresh build) |
| `alembic check` | **1** (9 s) — `NoReferencedTableError: ehr_allergies.encounter_id → national_encounters` → **NR-011** |

### 3.3 Strict-schema functional validation — W1 gate (2026-11-17, disposable clone only)

Harness lives **outside** the repository (`/tmp/opencode/strict-w1/`): strict conftest (PostgreSQL,
asserted revision/table count, savepoint isolation, **no DDL**), `pytest.ini`, and **53**
byte-identical test modules (sha256 manifest re-verified). Clone `gula_w1_strict_20261117` from
`gula_unify_full` (rev `20261114_0006`, 433 tables).

| Command | Exit |
|---|---|
| Schema fingerprint of the strict clone **before** the runs (`schema_fingerprint.sql`) | `3b2d9499d019503bf1ff5644f713cd5f272705f544862d8022887a516f973568` (1 118 041 B) |
| Strict suite #1: `STRICT_DATABASE_URL=<clone> pytest tests -q` (872 tests) | **1** — **753 passed / 119 failed / 0 skipped**, 273.09 s (`logs/strict_suite_20261117_063054.log`) |
| Strict suite #2 repeatability: same clone, `--junitxml` | **1** — **750 / 122**, 281.35 s (`logs/strict_run2_20261117_063054.log`; junit 281.198 s); **119/119** reproduced, +3 self-poisoned audit-chain assertions |
| SQLite control: same 53 modules, repository conftest (`create_all`) | **0** — **872 passed / 0 failed**, 297.98 s (`logs/baseline_sqlite.xml`) |
| Schema fingerprint **after** both runs and the drift probe | `3b2d9499…6f973568` — **identical** → zero DDL executed |
| Failure classification (run #1, 119) | 43 `MIGRATION_COLUMN_DRIFT`, 33 `MIGRATION_MISSING_TABLE`, 20 `RUNTIME_GUARD`, 4 `AUDIT_APPEND_ONLY_TRIGGER`, 4 `CASCADE_FAILURE`, 4 `ID_SEQUENCE_ASSUMPTION`, 4 `HARNESS_PATH_ARTEFACT`, 4 `OTHER`, 2 `PG_TYPE_OVERFLOW`, 1 `FK_ENFORCEMENT` |
| ORM ↔ migrated schema comparison | 433 DB tables; 756 ORM (per-base) / 416 present / **340 missing**; **82 tables / 664 columns** missing; 85 extra-column tables; 4 type-risk tables |
| NR-011 probe **A** (pristine `env.py`, repo copy untouched) | **1** — `NoReferencedTableError` (unresolved FK varies across runs) |
| NR-011 probe **B** (`import app.national.domain` only) | **1** — error **moves** to `national_patients` (cross-metadata FKs unresolvable) |
| NR-011 probe **C** (7 omitted bases + merged `MetaData`) | **1** — no `NoReferencedTableError`; `FAILED: New upgrade operations detected` (284 distinct missing tables) → real ADR-A diff |
| NR-011 supporting isolation checks (`EHRBase` FK resolution, `configure_mappers`) | confirmed cross-metadata FKs; `configure_mappers()` still needs `app.services.mpi.models` |

## 4. Open blockers

1. `MIG-EXISTING` remains **PARTIAL / NOT MET**. Phase C (2026-11-17) proved the forward upgrade and the full-teardown rollback on a disposable clone of the prior snapshot `20260815_0022` (405→433 tables, 0 rows lost, checksum-identical business data, byte-identical fingerprint after round trip). Outstanding: (a) ADR-B table ownership, (b) rollback procedure must be a recorded decision — `downgrade 20260815_0022` is a silent partial reversal (exit 0, 2 version rows, 7 residual tables), (c) the only snapshot holds 51 rows, so production-like data is unproven, (d) **NR-011** blocks `alembic check`.
2. Three downgrade-residual reference tables remain ownership-ambiguous (`facilities`, `organizations`, `national_facilities`) → ADR-B.
2a. **NR-011 (P0, new):** `alembic check`/autogenerate **cannot run** — `ehr_allergies.encounter_id → national_encounters` is missing from metadata (`migrations/env.py:38` imports only `app.national.base`; table exists in no migration and no migrated DB). This is the mechanical reason the **426-table** ORM gap (407/833 migrated, 18/40 contexts covered) cannot be closed by autogenerate → ADR-A prerequisite. **Root cause corrected (W1, 2026-11-17):** an import-only fix moves the error to `national_patients` because all four `ehr_allergies` FKs are cross-metadata; a merged `MetaData` is also required (see §3.3 probe C and `UNIFICATION_BLOCKERS.md` §3A/§5 item 9).
2b. **NR-012 (P2, new):** upgrading a real `0022` DB preserves `DEFAULT nextval('pharmacy_drug_catalog_id_seq')` on `pharmacy_drug_catalog.id` after `20260815_0023` converts it to `varchar(26)`. 2-line structural delta; not an upgrade defect; documented debt.
3. Remaining preserved backend gates are unaudited beyond the full suite (mypy 71 scoped pre-existing errors; ruff 35 pre-existing findings in `app/routes/`).
4. **F-01 (P0, deployment) — FIXED, awaiting review:** `.github/workflows/frontend-pwa.yml` built with an origin-only `VITE_API_BASE_URL`, which bypassed the gateway's `/api/` route and could not reach any root backend route. Changed to `https://api.gula-platform.org/api` (one line). Docker production build was already correct (unset → client default `/api`).
5. **Frontend contract drift (P1/P2):** 101 unresolved calls classified — 21 malformed (`//`), 20 missing path params, 15 namespace drift, 14 feature-flag-off (financial), 10 no counterpart (8 placeholder capability pages), 9 extra segment, 4 retired surface; plus 28 verb mismatches (15 in dead `ehrApi`/`resultsApi`). See `GOVERNANCE/FRONTEND_INTEGRATION_REPORT.md` §4–§5.
6. Mypy remains unclean for ported modules (71 scoped pre-existing errors).
7. GLOSI has no human security/legal/technical review and no approved project.
8. No commit has been created; commit review and Program Director approval are required.
9. **Security (P0) — S-01/S-02, control plane: REMEDIATED in the working tree (uncommitted, unreviewed).** Reads are `master_admin`/`ministry_admin`; writes are `master_admin`; deploy requires a prior `APPROVED` release and a distinct approver derived from the token; body `user`/`approve_first`/`approved_by`/`deployed_by` are rejected `400`. Evidence: `test_control_plane_authorization.py` 21/21.
10. **Security (P0) — S-03, NIAM identity store: REMEDIATED in the working tree (uncommitted, unreviewed).** `persons`/`sessions` require a registry reader; `devices` and the person-create / session-terminate writes require the registry writer; `auth`/`accounts` unchanged (`accounts` still `410`). Evidence: `test_niam_registry_authorization.py` 21/21.
11. **Security (P0) — S-04/S-05, national surfaces: REMEDIATED in the working tree (uncommitted, unreviewed).** Lifecycle/pilot-platform/certification/contracts use one shared policy (read ⇒ operational allow-list with `citizen` denied, write ⇒ `master_admin`); `/governance/audit-events` is authenticated and the actor is server-derived (forged `actor_id` ⇒ `403`, nothing persisted). Evidence: `test_national_governance_authorization.py` 29/29, `test_governance_audit_authorization.py` 11/11.
12. **Security (P1) — S-06, degraded-mode downgrade: REMEDIATED in the working tree (uncommitted, unreviewed).** `security_store()` fails closed for revocation / rate-limit / idempotency / verification when the store is process-local in production/staging without `ALLOW_DEGRADED_REDIS=true`; `get_current_user` and the rate limiter surface `503`. Evidence: `test_security_store_policy.py` 12/12. **Kill-switch residual resolved this cycle:** `app/core/kill_switch.py` `_read_shared_state()`/`_evaluate()` treat unreadable shared state as **ACTIVE** in production/staging (CRITICAL log, `shared_state_readable:false` in `status()`), so a Redis outage can no longer silently disable an emergency stop; dev/test keep fail-open. Evidence: `test_kill_switch_fail_closed.py` 9/9 (incl. policy-engine proof that autonomous actions are blocked). Residual **R-06** (operators/alerting must honour `shared_state_readable=false`) stays open.
13. **Security (P1) — 91 unguarded endpoints: REMEDIATED in the working tree (uncommitted, unreviewed).** S-07 (HTTPS-derived `Secure` cookies via one helper), S-08 (24 confidential governance reads + 3 anonymous worker writes), S-09 (AI internals ⇒ AI-operator gate), S-10/S-11 (covered by S-04) and S-12 (LIMS indicators ⇒ authenticated). Re-derived walk: **2 133 endpoints / 2 064 guarded / 69 unguarded = public-by-design only, 0 real gaps** (69 = the documented 67 + `POST /oauth2/token` + `POST /auth/refresh`, both reviewed and credential-validating — see register §2). Evidence: regression files in GULA-015 + **`GOVERNANCE/PUBLIC_ENDPOINT_REGISTER.md`** (per-endpoint handler/control/residual for all 69; 91 → 0 closure map; residuals **R-01…R-11** open).
14. **Security (HIGH) — S-13, self-service verification of professional accounts: REMEDIATED in this cycle (uncommitted, unreviewed).** `/auth/verification/{request,confirm}` now only resolves `SELF_VERIFIABLE_ROLES = ("citizen",)`; a self-declared doctor can no longer self-verify past licence approval (`PUT /admin/doctors/{id}/approve` remains the only activation path). Evidence: `test_professional_verification_authorization.py` 7/7 + adjacent 44 passed. Residual **R-07** (unverified doctor rows persist) open.
15. **Backend Python dependency advisories: REMEDIATED — criterion 11 MET (2026-11-17).** The 55 advisories in 6 runtime packages (`pillow` 42, `pyasn1` 4, `urllib3` 3, `joserfc` 2, `dnspython` 2, `certifi` 2) were each raised to the minimum fix version (`pillow==13.0.0`, `joserfc==1.7.6`, `certifi==2026.10.18`, `dnspython==2.9.2`, `pyasn1==0.6.5`, `urllib3==2.8.0`, plus `idna==3.20`), with security **floors** recorded in `requirements.txt`. Lock audit, fresh-resolution audit (`uv pip compile`, 72 pins, reproducible) and installed-set audit are **all exit 0 — "No known vulnerabilities found"**; 33/33 behaviour-only compat tests pass on both old and new sets; full suite 3 480 passed / 27 skipped / 0 failed (+33 vs the 3 447 baseline, 0 regressions). Evidence: `GOVERNANCE/DEPENDENCY_VULNERABILITY_REPORT.md` §6.1, `DEP-AUDIT-BACKEND` **VERIFIED**, `/SECURITY_REMEDIATION_REPORT.md` addendum A1–A3. Method disclosure: two `pip` wheel-download attempts failed **only** at the network layer (throttling) and are recorded as **BLOCKED**, not as a resolution failure.
16. **Open residuals from the endpoint review (R-01…R-11)** are catalogued in `GOVERNANCE/PUBLIC_ENDPOINT_REGISTER.md` §5 — health-probe diagnostics disclosure, `/health/kernel` `str(e)`, docs-gate gaps (staging + `/docs/oauth2-redirect`), password-reset coverage/delivery, kill-switch operator semantics, S-07 account-state residual, OAuth introspect/revoke client-auth conformance, `ENABLE_PUBLIC_PATIENT_HISTORY`, `/setup/status`, `/metrics/prom` env dependence. **No finding is recorded as fully closed while its residual is open.**
17. **Human security review and Program Director sign-off are still required** before any of the above can be considered closed; nothing is committed and no certification is claimed.
18. **W1 strict-schema gate: FAILED (evidence appended, no fix attempted).** Against a disposable PG16 clone built only by Alembic, the 53-module / 872-test set is **753 passed / 119 failed** (run #1) vs **872/872** under the SQLite `create_all()` control → 100 % of failures are schema-induced. 19 modules carry failures; 34 pass fully. Four P0 patient-workflow modules fail (ICU/LIMS 6/7, emergency surgery 2/4, pharmacy/radiology 1/3, pharmacy POS 0/3). Findings registered as **W1-*** in `UNIFICATION_BLOCKERS.md` §3A; detail in `DATABASE_COMPATIBILITY_REPORT.md` §11 and `PHASE_C_DATABASE_REHEARSAL_REPORT.md` §13.
19. **W1 — ORM/migration completeness (P0):** **340** ORM table slots absent from the migrated schema and **82 tables missing 664 ORM columns** (W1-baseline figures); `national_encounters`, `ehr_conditions`, `exam_code` appeared in no migration at that baseline. Root cause of 76 direct + 4 cascade failures. Closure requires ADR-A (schema change), not test edits. **Partial closure since:** the 62-table care-continuum + FK-dependency closure (incl. `national_encounters`) is now covered by the independently verified revision `20261119_0003` (§16); the broader backlog and ADR-A ownership decisions remain open and these W1 counts have not been recomputed.
20. **W1 — test isolation defect (P1, not patched):** the repository `client` fixture binds `SessionLocal` to the engine rather than the savepoint connection, so writes commit outside the rollback boundary (12 `audit_logs` rows, ids 65–191). This made strict run #2 report 3 extra audit-chain failures. Fix belongs in the integration repo's fixture; production code untouched.
21. **W1 — coverage hole (P1):** referrals and `care_continuum` have **no functional tests** (referrals only a static route-guard string; `care_continuum` only in `tests/conftest.py`), and hospital coverage is a single module. Those workflows are **NOT VERIFIED**, not "passing".
22. **NR-011 — root cause corrected and RESOLVED IN CODE (status corrected 2026-11-19, fresh Wave 0 verification):** the historical two-part root cause (register the 7 omitted declarative bases + merge cross-metadata FKs into one `MetaData`) is now implemented in `migrations/env.py` — all 17 bases registered, `app.national.domain` imported, single merged `MetaData`; cross-metadata `ehr_allergies → national_patients` FKs resolve. Evidence: `pytest tests/unit/test_nr011_metadata_discovery.py tests/unit/test_fk_target_integrity.py -q` → **19 passed, EXIT=0** (fresh re-run this session: NR-011 module 14 passed; see `GOVERNANCE/WAVE_0_BASELINE.md` §2 and `DATABASE_MIGRATION_READINESS.md` §1). The remaining ADR-A scope is the unmigrated-table backlog, **not NR-011 itself**; no ADR-A approval is claimed.
23. **W1 — secondary defects proven, not fixed:** `disk_free_bytes` migrated as `integer` (2 `NumericValueOutOfRange` failures); 20/20 `test_edge_platform` cases blocked by `RuntimeIsolationError` against the migrated schema; 4 audit-tamper tests hit the append-only trigger; 4 source-inspection tests are external-harness path artefacts (classified, not skipped).

## 5. NIAM Step-Up Authentication — bounded prerequisite (2026-11-19, HEAD `2206654d…`)

| ID | Scope | Key files | Result | Evidence | Status |
|---|---|---|---|---|---|
| STEP-01 | Functional step-up prerequisite for B4 | `app/identity/services/step_up_service.py`, `app/identity/models/step_up.py`, `app/identity/api/{auth,step_up}.py`, `app/config.py`, `20261119_0001` migration | Self-only own-account MFA evidence, server-bound, fail-closed, 300s owner-approved freshness; no role/authority created | `NIAM_STEP_UP_SECURITY_REPORT.md` §3; `NIAM_STEP_UP_PREREQUISITE.md` | `IMPLEMENTED / TESTED / INTEGRATED` (engineering) |
| STEP-02 | Adversarial suite (37 tests) | `backend/tests/unit/test_niam_step_up.py` | 37 passed / 1 warning, `EXIT=0`; covers 299/300/301, skew, replay, session/token/account/factor substitution, suspended/locked accounts, concurrency, DB constraint, migration up/down | focused pytest log in `NIAM_STEP_UP_SECURITY_REPORT.md` §5 | `TESTED` |
| STEP-03 | Failures found and genuinely repaired | same scope | blank config accepted → fail-closed; `is_active`-only principal check → full account-state guard; racy replay check → DB unique constraint + `IntegrityError`→`StepUpDenied`; missing import / tz mismatch fixed | §5 of the security report | `TESTED` |
| STEP-04 | Regressions + gates | — | earlier 374 passed/4 skipped (file list not retained); **retained-log targeted re-run 170 passed/0 skipped `EXIT=0`** (12 files); `phase_b_gate.py` 6/6 `EXIT=0`; `national_integration_verify.py` VERDICT PASS `EXIT=0` | `/tmp/opencode/step_up_targeted_final.log`; `NIAM_STEP_UP_PREREQUISITE.md` §7 | `TESTED` |
| STEP-05 | Full-suite chain | — | first run `4973 passed/1 failed` (CPU-timing benchmark flake `1680/s<2000/s`, unrelated; 3 isolation runs pass); clean re-run `4974 passed/27 skipped/EXIT=0` (17m09s); **final current tree `4984 passed/27 skipped/203 warnings/EXIT=0` (15m04s), 0 failed** | `/tmp/opencode/step_up_{full_suite,full_suite_rerun,final_full_suite}.log` | `TESTED` |
| STEP-06 | Team C independent verification | `GOVERNANCE/ADVERSARIAL_ASSURANCE/INDEPENDENT_VERIFICATION_TEAM_C_STEP_UP.md` | fresh-context review 2026-11-19T06:14Z→06:35Z: 37/37 focused, Ruff clean, 57+ probes / 0 real bypasses, all invariants held; `INDEPENDENTLY VERIFIED` at engineering scope, `PRODUCTION READY` not awarded | Team C report §1/§2/§7 | `INDEPENDENTLY VERIFIED` |
| STEP-07 | B4 wiring | `backend/app/identity/adaptive_auth/routes.py` | **Historical status at step-up closeout:** not modified, owner approval pending. **Superseded by §6 below** — owner directive `GULA-MASTER-AUTH-2026-11-19` §4 subsequently authorized and the work was implemented. | — | `BLOCKED` (superseded) |

Invariants reconfirmed: both HEADs pinned, 20 staged R100 renames intact, all three protected MD5s
identical, `production_ready_items == 0`, no commit/push/PR/merge/deploy, no operational DB/Redis.
No `PRODUCTION READY` awarded. No test deleted, skipped, or weakened.

---

## 6. B4 — Cross-account security administration (2026-11-19, owner directive §4)

Owner directive `GULA-MASTER-AUTH-2026-11-19` §4 explicitly authorized B4 with an exact security
model. Prior `BLOCKED` gates are resolved. No new role, permission, MFA or authorization engine was
introduced; all decisions reuse canonical NIAM primitives.

| ID | Scope | Key files | Result | Evidence | Status |
|---|---|---|---|---|---|
| B4-01 | Server-side policy guard | `backend/app/identity/adaptive_auth/b4_guard.py` | Actor + target + session re-read server-side; narrow `master_admin`/`security_administrator` subset of the canonical RBAC catalog with active/unexpired/unrevoked checks; fresh step-up via `StepUpService.assert_fresh`; fail-closed audit via `AuditService` | `B4_CROSS_ACCOUNT_SECURITY_REPORT.md` §3 | `IMPLEMENTED / TESTED` |
| B4-02 | HTTP surface hardening | `backend/app/identity/adaptive_auth/routes.py` | All 9 account-scoped routes bind actor + guard; client `account_id`/`mfa_id`/`session_id` demoted to untrusted lookup hints; MFA challenge/verify self-only; AUD-SEC-001 router guard retained | `B4_CROSS_ACCOUNT_SECURITY_REPORT.md` §4 | `IMPLEMENTED / TESTED` |
| B4-03 | Adversarial suite | `backend/tests/unit/test_b4_cross_account_security.py` | 24 passed / 1 warning, `EXIT=0` (35.46 s): role narrowing, weak control-plane role denial, expired/revoked assignments, missing/expired step-up, session/account substitution, suspended admin, MFA self-only, audit completeness, structural route binding, OpenAPI stability | focused pytest run this session | `TESTED` |
| B4-04 | Regressions + static gates | — | step-up + AUD-SEC-001 regressions `51 passed / 1 warning, EXIT=0 (187.42 s)`; Ruff `All checks passed!`; `app.main.app` OpenAPI 1815 paths unchanged | this session | `TESTED` |
| B4-05 | Independent verification | `GOVERNANCE/ADVERSARIAL_ASSURANCE/INDEPENDENT_VERIFICATION_TEAM_C_B4.md` | fresh-context Team C awarded `INDEPENDENTLY VERIFIED` (engineering scope): 24/24 + 51/51 regressions + Ruff clean + OpenAPI 1815 unchanged + 10 independent adversarial probes, 0 real bypasses, all 8 directive audit fields persisted; 4 residual risks R-1…R-4 recorded; `PRODUCTION READY` explicitly not awarded | `INDEPENDENT_VERIFICATION_TEAM_C_B4.md` §2/§7 | `INDEPENDENTLY VERIFIED` (engineering scope) |

Invariants reconfirmed after B4: both HEADs pinned, 20 staged R100 renames intact, three protected
MD5s identical, `production_ready_items == 0`, no commit/push/PR/merge/deploy, no operational
DB/Redis. No `PRODUCTION READY` awarded. No test deleted, skipped, or weakened.

---

## 7. Tier B — authorized security controls (2026-11-19, owner directive §5)

Owner directive `GULA-MASTER-AUTH-2026-11-19` §5 authorized B1/B2/B3/B5 within explicit fail-closed
boundaries. No new role catalog, permission engine, MFA engine, or audit store was introduced; all
controls reuse canonical primitives. Jurisdiction-specific Iraqi legal rules remain documented
policy dependencies — no legal/clinical entitlement is fabricated.

| ID | Scope | Key files | Result | Evidence | Status |
|---|---|---|---|---|---|
| B1-01 | Centralized per-action PHI permission map | `backend/app/identity/services/phi_permission_map.py` | 8 distinct PHI actions (`read/create/update/delete/export/print/share/administrative`) + `administer` alias; broad/substitute PHI keys denied via `AuthorizationReason.phi_permission_conflict` in canonical `AuthorizationDecisionService` | `tests/unit/test_b1_phi_permission_map.py` (13 passed) | `IMPLEMENTED / TESTED` |
| B1-02 | Canonical authorization regressions | — | B1 map + `test_authorization_phase8.py` + `test_authorization_synthetic_scope.py` combined `39 passed / EXIT=0`; Ruff clean | focused pytest run this session | `TESTED` |
| B2-01 | Server-verified break-glass guard | `backend/app/security/break_glass_guard.py` | Active/unexpired/non-deactivated `BreakGlassSession`, actor ownership, eligible clinical role, read-only scope, MPI subject scoping (`Citizen.canonical(strict=True)` + `IdentityClaim`); `X-Emergency-Access` downgraded to intent-only signal; consent/break-glass kept separate; fail-closed reason codes | `tests/test_consent.py` | `IMPLEMENTED / TESTED` |
| B2-02 | Consent dependency + activation route rewiring | `backend/app/security/consent_dep.py`, `backend/app/routes/authorization.py` | Use-time verification replaces client-header bypass; activation validates role/category/justification/patient/duration (`MAX_BREAK_GLASS_MINUTES=240`) and deactivation enforces ownership | `tests/test_consent.py` (forged-header, expired, deactivated, wrong-subject, another-actor, non-read-scope, activation policy) | `IMPLEMENTED / TESTED` |
| B2-03 | Consent suite + combined regressions | — | `tests/test_consent.py` 26 passed; combined with B1 `39 passed / EXIT=0`; Ruff clean | focused pytest run this session | `TESTED` |
| B3-01 | Fail-closed verified-guardian policy layer | `backend/app/identity/services/verified_guardian_guard.py` | Server-derived age (never client `is_minor`); near-majority 90-day re-verification; canonical NID input contract only (no canonical NHID minted — `NHID_CANONICALIZATION_READINESS.md` remains `BLOCKED`); twins-never-merged; authorized-verifier gate (no subject self-assertion); canonical `GuardianRulesService` action table; fail-closed reason codes | `tests/unit/test_b3_verified_guardian.py` (41 passed) | `IMPLEMENTED / TESTED` |
| B3-02 | Canonical workflow + authorization wiring | `backend/app/identity/services/citizen_relationship_service.py`, `backend/app/identity/services/authorization_decision.py` | Additive `create_pending_guardian()` (verifier role, minor subject, NID digest only, twin collision denial, audit); additive guardian gate in `_relationship_allows` subject to verified relationship + scope + rule table — other relationship types unchanged | canonical regressions 67 passed | `IMPLEMENTED / TESTED` |
| B5-01 | Canonical NIAM delegation model + additive migration | `backend/app/identity/models/delegation.py`, `backend/migrations/versions/20261119_0002_niam_delegations.py` | Account-based IDs + canonical role IDs; verified permission subset; scope/facility/department/unit/workspace; depth 1..3 DB CHECK + policy cap; expiry/revocation provenance; single migration head (`20261119_0002`, 110 files); upgrade creates table only, downgrade drops it only; no data migration | migration head probe + structural tests | `IMPLEMENTED / TESTED` |
| B5-02 | Delegation validation + audit | `backend/app/identity/services/delegation_service.py` | Self-delegation, no-holding-authority, inactive account/role, unknown permission, scope-exceeds-authority, duration cap (1..720 h), depth cap and reason validation all fail closed; `delegation_granted/revoked/denied` audit via canonical `AuditService` | `tests/unit/test_b5_delegation.py` (26 passed) | `IMPLEMENTED / TESTED` |
| B5-03 | Single-canonical-authority consumer | `backend/app/identity/services/authorization_service_v2.py` | `effective_permissions()` unions only verified, active, in-force, in-scope, depth-capped delegation rows with direct role permissions; no parallel engine; health_core synthetic engine remains synthetic-only | `tests/unit/test_b5_delegation.py` + `test_authorization_phase7/8.py` + `test_authorization_synthetic_scope.py` | `IMPLEMENTED / TESTED` |
| T-B-04 | Combined Tier B + canonical regressions | — | B4 24 + B1 13 + B2 26 + B3 41 + B5 26 + phase7 5 + phase8 19 + synthetic 7 + workflow 5 + NHID 23 + step-up 37 = **226 passed / 0 failed, EXIT=0**; Ruff clean on all changed scopes; OpenAPI 1815 paths unchanged; single migration head | focused pytest run this session | `TESTED` |
| T-B-05 | Final Tier B tree full suite | `/tmp/opencode/final_tree_full_suite_tierB.log` | `ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. <pinned py> -m pytest tests/ -q` → **5105 passed, 27 skipped, 203 warnings, EXIT=0 (12m03s)**, 0 failed; supersedes the 4984 step-up-tree run for final-tree claims; no test deleted/skipped/weakened; warnings are pre-existing deprecations | full-suite run this session | `TESTED` |
| T-B-06 | B5 migration live round-trip on disposable PG | `/tmp/opencode/b5_migration_{upgrade,downgrade,reupgrade}.log` | Throwaway DB `gula_b5_migration_verify` on local dev PG `172.18.0.2:5432` (same disposable pattern as NR-011). `alembic upgrade head` **EXIT=0** → head `20261119_0002`, `niam_delegations` with all 23 columns and `ck_niam_delegations_depth = CHECK(depth>=1 AND depth<=3)`; `alembic downgrade -1` **EXIT=0** → head `20261119_0001`, table count 0; `alembic upgrade head` again **EXIT=0** → head `20261119_0002`, table count 1; throwaway DB **dropped** (count 0). No operational/production DB touched; no data migrated | migration round-trip this session | `TESTED` |
| T-B-07 | B5 Alembic drift defect found and fixed | `/tmp/opencode/b5_drift_check_{before,after}.log`, `/tmp/opencode/b5_final_check.log` | Real defect: `NiamDelegation` was absent from `app/identity/models/__init__.py`, so `niam_delegations` was missing from `IdentityBase.metadata` and `alembic check` emitted a **new `remove_table` drift** (before fix: `niam_delegations_in_identity_metadata=False`, `('remove_table','niam_delegations')` present, 123 token hits). Fix: registered `NiamDelegation`/`DelegationStatus` in the package import and `__all__`; renamed migration composite indexes to match the ORM (`ix_niam_delegations_delegate`, `ix_niam_delegations_role`). After fix on a fresh disposable DB: metadata probe **True**, `remove_table` count **0**, only the repo-wide generic `uuid` VARCHAR/String index churn remains (same noise as baseline tables). Ruff clean; no source behavior change | drift probe + fix + re-probe this session | `TESTED` |
| T-B-08 | Post-alignment live migration round-trip | `/tmp/opencode/b5_indexalign_{upgrade,downgrade,reupgrade}.log` | Fresh throwaway DB `gula_b5_indexalign_verify`: `alembic upgrade head` **EXIT=0** with both realigned composite indexes present (`ix_niam_delegations_delegate`, `ix_niam_delegations_role`); `alembic downgrade -1` **EXIT=0** → table count 0 (new index names drop cleanly); `alembic upgrade head` **EXIT=0** → head `20261119_0002`, table count 1; throwaway DB **dropped** (count 0). Confirms the post-fix `downgrade()` is reversible | migration round-trip after index alignment | `TESTED` |
| T-B-09 | Drift-fix regression guard | `backend/tests/unit/test_b5_migration_drift_regression.py` | 6 new pure tests (no DB): metadata registration, package export, model↔migration composite-index parity, named depth CHECK parity, 23-column parity, additive/reversible migration structure. `ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. <pinned py> -m pytest tests/unit/test_b5_migration_drift_regression.py -q` → **6 passed, 1 warning, EXIT=0**; Ruff clean. Locks in the T-B-07 fix so a recurrence fails fast | focused pytest this session | `TESTED` |
| T-B-10 | Final-tree full suite after B5 security fixes | `/tmp/opencode/final_tree_full_suite_b5_fixed.log` | Same command as T-B-05 on the post-fix tree → **`5117 passed, 27 skipped, 203 warnings, EXIT=0 (13m12s)`**, zero failures. `5117 = 5105 + 12` (the 6 B5-security regressions + 6 drift-fix regressions); no test deleted, skipped, or weakened; warnings are pre-existing deprecations. Supersedes T-B-05 for final-tree claims | full-suite run after all B5 fixes | `TESTED` |

Tier B invariants reconfirmed: no new authorization engine, no destructive migration, disposable data
only, both HEADs pinned, 20 staged R100 renames intact, three protected MD5s identical,
`production_ready_items == 0`, no commit/push/PR/merge/deploy, no operational DB/Redis. No
`PRODUCTION READY` awarded. No test deleted, skipped, or weakened. Final Tier B tree full suite
rerun complete (`5105 passed / 27 skipped / 0 failed, EXIT=0`, row T-B-05); post-fix final-tree
full suite complete (`5117 passed / 27 skipped / 0 failed, EXIT=0`, row T-B-10) and authoritative
for final-tree claims. Fresh-context Team C verification of B2/B3/B5 is recorded in §10; B5
re-verification after the fixes is pending.

**`status_registry.json` raw-substring reconciliation (exact, this session).** A naive substring scan of
`GOVERNANCE/NATIONAL_INTEGRATION/status_registry.json` reports `"PRODUCTION READY"` × 7 and
`"production_ready"` × 4. A deterministic structural walk of the parsed JSON proves these are NOT
status assignments: exact string-value assignments of `"PRODUCTION READY"` = **0**; the four fields
named `production_ready*` are `$.production_ready_items`, `$.phase_b.production_ready_items`,
`$.adversarial_assurance.findings_register.production_ready` and
`$.adversarial_assurance.remediation_register.production_ready`, all **0** (nonzero count fields = 0).
The raw hits are the vocabulary definition (`status_vocabulary[11]`), count-field *names*, negation
strings ("No `PRODUCTION READY` awarded", "NOT PRODUCTION READY", "never PRODUCTION READY"), and the
`critical_path` line "production readiness (BLOCKED)". Invariant `production_ready_items == 0`
therefore holds; no workstream, finding, remediation, or phase is promoted to production ready.

## 8. Wave 2 — database integrity (2026-11-19, safe lane)

| ID | Control | Evidence | Result | Verification | Status |
|---|---|---|---|---|---|
| W2-01 | Migration graph integrity | Alembic `ScriptDirectory` probe | single head `20261119_0002` (`head_count=1`), single base `20250322_0000`, 110 revisions, `b5_down_revision=20261119_0001`, `b5_is_head=True`; 4 pre-existing merge revisions (`20260908_0001`, `20260819_0001`, `20260815_0015`, `20260815_0003`) are intentional branch merges, not fork drift | deterministic Alembic probe this session | `TESTED` |
| W2-02 | Migration safety tests | `tests/migrations/test_migration_graph_integrity.py`, `tests/test_migrations.py`, `tests/test_migration_resilience.py` | `ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. <pinned py> -m pytest <3 files> -q` → **22 passed, 1 warning, EXIT=0** (6.76s) | focused pytest after the B5 drift fix | `TESTED` |
| W2-03 | No fake stamps / `create_all()` masking in B5 migration | structural inspection of `20261119_0002_niam_delegations.py` + `migrations/env.py` | B5 migration contains no `stamp`, no `create_all`, no `op.alter_column`, no `op.add_column`; creates only `niam_delegations`, drops only that table on downgrade. `env.py` explicitly documents `create_all()` only for the SQLite test conftest, never for migration application | source inspection + regression test T-B-09 | `TESTED` |

Wave 2 conclusion: migration graph is linear-to-head with only intentional pre-existing merge nodes;
the B5 addition is additive and reversible in both structure and live execution (rows T-B-06/T-B-08).
Repo-wide `alembic check` churn remains a documented pre-existing baseline condition and is **not**
claimed resolved; the new `niam_delegations` table contributes no new destructive drift after T-B-07.
Operational restore/PITR/RPO/RTO drills remain `BLOCKED` (operational resources prohibited).

## 9. Fresh-context Team C — Tier B independent verification (2026-11-19)

| ID | Control | Evidence | Result | Verdict | Status |
|---|---|---|---|---|---|
| TC-B-00 | B1 — centralized PHI permission map | `GOVERNANCE/ADVERSARIAL_ASSURANCE/INDEPENDENT_VERIFICATION_TEAM_C_TIER_B.md` (later pass, broader scope) | canonical `phi_permission_conflict` enforcement; no second engine/catalog entries | 0 real bypasses | `INDEPENDENTLY VERIFIED` (engineering scope) |
| TC-B-01 | B2 — consent / break-glass | `GOVERNANCE/ADVERSARIAL_ASSURANCE/INDEPENDENT_VERIFICATION_TEAM_C_TIER_B.md` | source trace; implementer consent suite re-run; forged/expired/deactivated/wrong-subject/non-read all DENY | 0 real bypasses | `INDEPENDENTLY VERIFIED` (engineering scope) |
| TC-B-02 | B3 — verified guardian / minor / NHID | same report | 22/22 fresh adversarial probes; source trace | 0 real bypasses | `INDEPENDENTLY VERIFIED` (engineering scope) |
| TC-B-03 | B5 — delegation into canonical authority (prior pass) | same report (later, more adversarial pass) | reproducible HIGH authority-laundering bypass (§4.1, `/tmp/opencode/tierC_probe_b5_escalation.py`) + HIGH integration gap (§4.2) + MEDIUM transitive-revocation residual (§6.4) | **2 real HIGH findings** (superseded by TC-B-06 after fixes) | `BLOCKED` (historical; resolved) |
| TC-B-04 | Implementer suite + Ruff re-execution by Team C | report §3 rows 1–2 | `93 passed, 1 warning, EXIT=0` (17.31s); Ruff on 9 Tier B source files `All checks passed!`, EXIT=0 | independently re-run | `TESTED` |
| TC-B-05 | Non-mutation attestation | report §2 item 8, §3 rows 7–8 | HEAD `2206654d…` unchanged; branch `integration/gula-unification-v1`; 20 R100 renames intact; `FINAL_DECISION.md` MD5 `effdfeaf…` unchanged; no commit/push/merge/reset; report was the only repo file the verifier edited | verified | `IMPLEMENTED` |
| TC-B-06 | B5 fix re-verification (third fresh-context pass) | `GOVERNANCE/ADVERSARIAL_ASSURANCE/INDEPENDENT_VERIFICATION_TEAM_C_B5_REVERIFY.md` (timestamp `2026-11-19T10:35:28Z`) | focused suite **238 passed, EXIT=0**; Ruff on all changed scopes clean; `git diff --check` EXIT=0; independent probes: exact escalation repro now DENIED, mixed/depth-2/scope-widen/cross-catalog all fail closed + audited, canonical HTTP route writes `niam_delegations` and changes `effective_permissions`, legacy 410 with no writes, chain walk denies root/intermediate revoke + expiry + deactivation + cycle + depth tamper | **0 real API-reachable bypasses**; 1 defense-in-depth residual (forged DB row, requires out-of-band table write) | **`INDEPENDENTLY VERIFIED`** (engineering scope, overall B5) |

**Conflicting passes:** an earlier fresh-context Tier B verification reported B2/B3/B5 verified with
0 bypasses; the later, broader and more adversarial pass (timestamp `2026-11-19T09:38:19Z`) verified
B1/B2/B3 but found the two HIGH B5 findings above. Both results are retained; the more severe
evidence-backed result governed while the fixes were pending. **Resolved (TC-B-06):** a third
fresh-context pass (timestamp `2026-11-19T10:35:28Z`) independently confirmed all three findings
remediated with 0 real API-reachable bypasses and awarded overall B5 `INDEPENDENTLY VERIFIED` at
engineering scope. `PRODUCTION READY` was not awarded. Residuals: B1 seeded-catalog gap, B2
category-pattern mismatch, B3 near-majority adapter flag, B3 legacy audit sink, B5 forged-DB-row
defense-in-depth gap, and B4 R-1…R-4.

## 10. Wave 4 — frontend static gates (2026-11-19, fresh run)

All commands from `/home/samertts/workspace/projects/gula-integration/frontend-v3`, Node v24.18.0.

| ID | Check | Evidence | Result | Status |
|---|---|---|---|---|
| W4-01 | TypeScript typecheck | `npm run typecheck` → `/tmp/opencode/wave4_typecheck.log` | `tsc --noEmit`, **EXIT=0**, zero errors | `TESTED` |
| W4-02 | ESLint | `npm run lint` → `/tmp/opencode/wave4_lint.log` | `eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0`, **EXIT=0**, zero warnings | `TESTED` |
| W4-03 | Frontend unit tests | `npm run test` → `/tmp/opencode/wave4_vitest.log` | Vitest 4.1.10: **16 files / 56 tests passed, EXIT=0** (69.88s) | `TESTED` |
| W4-04 | Unification gate | `npm run verify:unification` → `/tmp/opencode/wave4_verify_unification.log` | **EXIT=0** — bridge, scoped reads and transition document consistent | `TESTED` |
| W4-05 | Contract governance gate | `npm run verify:contracts` → `/tmp/opencode/wave4_verify_contracts.log` | **EXIT=0** — patient/order contracts, scoped permissions, facility context, governance refs | `TESTED` |
| W4-06 | Integration-boundary gate | `npm run verify:integration-boundary` → `/tmp/opencode/wave4_verify_boundary.log` | **EXIT=0** — direct REST boundary, canonical clinical gateway, server tRPC bridge, no secrets | `TESTED` |
| W4-07 | Data-source governance gate | `npm run verify:data-sources` → `/tmp/opencode/wave4_verify_datasources.log` | **EXIT=0** — 94 surfaces explicitly classified; clinical reads governed; visible writes classified and centrally blocked | `TESTED` |
| W4-08 | Audit-artifact gate | `npm run verify:audit-artifacts` → `/tmp/opencode/wave4_verify_auditartifacts.log` | **EXIT=0** — 309 backend paths, 92 frontend entries, 7 domains, gateway/delegation/integration decisions verified | `TESTED` |

These are static/build-time gates only; no runtime browser or service-integration claim is made.
No verifier script created or modified repository files (re-checked with `git status --short`).

## 11. B5 remediation of Team C HIGH findings (2026-11-19 — independently re-verified)

The later Team C pass (`INDEPENDENT_VERIFICATION_TEAM_C_TIER_B.md` §4) found two HIGH B5 defects and
one MEDIUM residual. All three were fixed with regression tests and then independently re-verified
by a third fresh-context Team C pass (`INDEPENDENT_VERIFICATION_TEAM_C_B5_REVERIFY.md`,
row TC-B-06), which awarded overall B5 `INDEPENDENTLY VERIFIED` at engineering scope with 0 real
API-reachable bypasses. **The implementer did not self-award that status.**

| ID | Finding | Fix | Evidence | Status |
|---|---|---|---|---|
| B5-F1 | Authority laundering (HIGH) | `delegation_service.py::delegate_role` now verifies requested permission keys against the actor's **effective holding** (direct assignment = full active role catalog; delegation-based holding = that delegation's own subset), not just the role catalog. Deny + audit with reason `permission_exceeds_holding_authority` | `tests/unit/test_b5_security_regressions.py::test_narrow_delegate_cannot_redelegate_unheld_permission`; the probe actor holding only `lab_result.read` can no longer grant `lab_result.export`; independently re-verified (TC-B-06, exact repro now DENIED) | `INDEPENDENTLY VERIFIED` (engineering scope) |
| B5-F2 | Integration gap (HIGH) | New canonical account-based API `app/identity/api/delegations.py` mounted at `/niam/delegations` (grant/list/revoke), backed by the ONE B5 `DelegationService` on `AsyncSession`; legacy `/authz/delegations` handlers failed closed with HTTP 410 pointing to the canonical surface | `test_canonical_route_writes_governed_table_and_changes_effective_permissions` (HTTP e2e: POST writes `niam_delegations`, canonical `effective_permissions()` changes, revoke removes it); `test_legacy_delegation_surface_fails_closed`; `test_canonical_route_registered_on_real_app`; independently re-verified (TC-B-06, real-app HTTP + 410 no-write) | `INDEPENDENTLY VERIFIED` (engineering scope) |
| B5-F3 | Transitive revocation (MEDIUM) | `authorization_service_v2.py::_delegation_chain_valid` walks the delegator chain at enforcement time; any broken link, cycle, missing parent or depth violation fails closed | `test_revoking_delegator_direct_role_revokes_delegate_authority`, `test_multi_hop_chain_still_grants_while_live`; independently re-verified (TC-B-06, revoke/expiry/deactivation/cycle/depth tamper) | `INDEPENDENTLY VERIFIED` (engineering scope) |

Supporting evidence:
- Focused Tier B + canonical suite (incl. 12 new regressions): **238 passed, 1 warning, EXIT=0** (102.51s).
- Pre-fix post-drift full tree: `5105 passed / 27 skipped / 0 failed, EXIT=0` (`/tmp/opencode/final_tree_full_suite_tierB_postfix.log`, 17m22s).
- Ruff clean on all 8 changed source/test scopes. Compile clean.
- OpenAPI paths `1815 → 1817` (+2 intentional: `/niam/delegations`, `/niam/delegations/{delegation_id}/revoke`); no existing contract changed; legacy paths retained but 410.
- Preserved: 3 protected MD5s, 20 staged R100 renames, `git diff --check` exit 0.
- Final-tree full suite after the fixes: **5117 passed / 27 skipped / 0 failed, EXIT=0 (13m12s)**
  (`/tmp/opencode/final_tree_full_suite_b5_fixed.log`, row T-B-10); `5117 = 5105 + 12` new regressions.
- **Re-verification complete (TC-B-06):** focused suite 238 passed / EXIT=0, Ruff clean,
  `git diff --check` EXIT=0; third fresh-context Team C pass awarded overall B5
  `INDEPENDENTLY VERIFIED` (engineering scope), 0 real API-reachable bypasses.
- **Residual (defense-in-depth, not a bypass):** a directly forged `niam_delegations` row can carry
  an unheld key at enforcement (re-verify report §6 novel probe 1). Requires out-of-band write to the
  canonical table (single production writer), so it is not API-reachable; recommended follow-up is
  to attest the parent key set in the chain walk and intersect at enforcement.
- **Next gate:** Waves 3/5/6/7 evidence and Team C triage of recorded residuals; no `PRODUCTION READY`
  or v1.0.0 claim.

---

## 12. Wave 3 — service-integration inventory review (2026-11-19, static evidence)

Read-only review against the current tree; no runtime service integration, production DB, Redis or
external network was used. Probe: `/tmp/opencode/wave3_service_integration_probe.py` →
`/tmp/opencode/wave3_service_integration_probe.log`.

| ID | Check | Evidence | Result | Status |
|---|---|---|---|---|
| W3-01 | Authoritative API surface | `ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. <pinned py>` → `from app.main import app; app.openapi()` | **`1817 paths / 2130 operations`**, `/niam/delegations` present; consistent with the post-B5 contract count | `TESTED` |
| W3-02 | 18-service inventory revalidation | `GOVERNANCE/NATIONAL_SERVICE_INVENTORY.md` §3 (18 target services) re-read against current tree | Headline unchanged: 4 effectively complete (laboratory, pharmacy, radiology, emergency), 9 real-but-partial, 3 signal-only (dental, rehabilitation, mental-health analytics) | `TESTED` (static) |
| W3-03 | `care_continuum` migration coverage | probe: 45 `cc_*` model tables vs `create_table('cc_*')` across 110 migrations | **45 model tables, 0 covering migrations** (the 4 `cc_*` hits are command-centre `cc_emergency_declarations` / `cc_resource_requests`, a different namespace). Confirms the inventory's dominant cross-service defect still exists on the current tree | `TESTED` (defect confirmed) |
| W3-04 | Test-masking mechanism | probe: `tests/conftest.py` contains `create_all(` → **True** | Missing `cc_*` schema is synthesised in tests, so CI is green while a fresh `alembic upgrade head` would not create these tables. Same root-cause pattern as the hospital-family finding | `TESTED` (defect confirmed) |
| W3-05 | `care_continuum` auth / audit signals | probe: route `get_current_user` × **75**, route audit × **0**, service audit × **0** | Authentication + lab scoping present; **no audit-log writes** on this 74-operation surface | `TESTED` (defect confirmed) |

**Wave 3 conclusion:** the static inventory review is complete (`TESTED`), but the review **confirms
an unresolved production blocker**: 45 `care_continuum` tables have no migration, tests mask the gap
with `create_all`, and the surface writes no audit log. Runtime end-to-end service integration and a
45-table additive migration are **NOT attempted** — migration work is owner-gated (criterion 9
`BLOCKED` on NR-011/ADR-A) and the no-operational-resources constraint forbids live service drills.
Criterion 12 therefore remains `BLOCKED` (review done, integration not proven), not awarded.
No `PRODUCTION READY` and no release claim.

---

## 13. Wave 5 — offline durability (2026-11-19, focused static suite)

Safe-lane focused run; disposable SQLite only, no Redis/DB/network, no repo file written by the run.
Command: `ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. <pinned py> -m pytest
tests/test_offline_sync.py tests/test_offline_conflict_synthetic.py
tests/health_core/test_integration_offline.py tests/health_core/test_reliability_conflicts.py
tests/test_certification_engine_synthetic.py -q` → `/tmp/opencode/wave5_offline_focused.log`.

| ID | Check | Evidence | Result | Status |
|---|---|---|---|---|
| W5-01 | Focused offline-durability suite | 5 test files, 82 collected | **82 passed, 1 warning, EXIT=0 (1.60s)** | `TESTED` |
| W5-02 | Sync idempotency / replay / integrity | `test_offline_sync.py` (20): duplicate receive, signature rejection, vector clock, replay-based recovery, multi-node no-data-loss, conflict quarantine preserves both versions | pass | `TESTED` |
| W5-03 | Deterministic conflict disposition + full accounting | `test_offline_conflict_synthetic.py` (11) + `test_reliability_conflicts.py` (9): no silent clinical overwrite, order-independent resolution, one hash-chained audit record per candidate, tampered-chain detection, missing disposition fails accounting, candidate digest mismatch rejected | pass | `TESTED` |
| W5-04 | Offline integration surface + certification | `test_integration_offline.py` (12) + `test_certification_engine_synthetic.py` (30) | pass | `TESTED` |

**Documented limitation (not a bypass):** `app/services/offline_sync_service.py:21-25` explicitly
states the dictionary-merge is **not a CRDT** (no per-field registers, tombstones or deterministic
actor tie-break) and convergence/idempotence cannot be proven at that layer; the design instead
quarantines conflicting versions for human workflow. The separate `health_core/reliability/
sync_conflicts.py` provides deterministic, hash-chained accounting. Offline durability is `TESTED`
at static-suite scope; a real device/network partition drill remains `BLOCKED` under the
no-operational-resources constraint. Criterion 11 (full clinical-alert outage drill) is unchanged.

---

## 14. Wave 6 — CI / reproducibility (2026-11-19, config-only fix)

A real reproducibility drift was found and fixed: the repository's documented fixed target is
**Python 3.12** (`requires-python = ">=3.12"` in `backend/pyproject.toml`; pinned venv 3.12.13), yet
4 CI workflows and 14 Dockerfiles still pinned **3.14**. Behavior-preserving string-only change to
the version pins; no source, test, dependency set, or operational resource touched. No commit made.

| ID | Check | Evidence | Result | Status |
|---|---|---|---|---|
| W6-01 | Workflow Python pins | `foundation-gate.yml:19`, `formatting.yml:21`, `quality-gate.yml:20` `python-version: "3.14"→"3.12"`; `constitution-compliance.yml:17` `PYTHON_VERSION: "3.14"→"3.12"` | 4 workflows aligned | `TESTED` |
| W6-02 | Dockerfile base images | 14 Dockerfiles `FROM python:3.14-slim→3.12-slim` (9 `services/*`, `docker/`, `platform/`, `nhop-platform/`, `backend/` ×2 stages, root `Dockerfile` ×2 stages) | 16 `FROM` lines aligned across 14 files | `TESTED` |
| W6-03 | Residual 3.14 scan | `grep -rn "3\.14" .github/workflows/ --include="*.yml"` + `grep -rn "3\.14" --include="Dockerfile*" .` + repo-wide `python-version:`/`FROM python:` scan | **0 matches** (`grep_exit=1`); "NONE" on repo-wide executable-pin scan | `TESTED` |
| W6-04 | Workflow parseability | `yaml.safe_load` over all `.github/workflows/*.yml` | **32 files, 32 parse OK, 0 fail**, EXIT=0 | `TESTED` |
| W6-05 | Hygiene + invariants | `git diff --check`; HEAD; R100 count; protected MD5s | `DIFF_CHECK_EXIT=0`; HEAD `2206654d…`; **20 R100 renames**; MD5s `effdfeaf…`/`1a02c015…`/`ea3969d0…` all unchanged | `TESTED` |

**Provenance note:** `services/lab/Dockerfile` carried a pre-existing orthogonal uncommitted change
(`joserfc` → `"joserfc>=1.7.6"`, line 5) before this wave. The Wave 6 edit touched **only its line 1**
`FROM` image; both changes are preserved verbatim and documented here. Establish exact per-hunk
provenance before any commit.

**Wave 6 gap (recorded, not fixed):** `gula-integration` CI does **not** expose `architecture-check`
or brain (`brain`/`brain-check`) as hard gates (verified by workflow text scan: both absent), unlike
the sibling `gula-platform` where they are wired into `ai-governance.yml`. `validate`, `ruff`,
`typecheck`, `eslint`, `pytest` gates are present. Adding those two hard gates is deferred: it is a
CI-policy change outside the auth directive's core scope and would require a fresh validation baseline
before CI enforcement; recorded here as a reproducibility/governance gap, not awarded. No
`PRODUCTION READY` or release claim.

---

## 15. Wave 7 — operational resilience (2026-11-19, static evidence only)

Read-only inventory of resilience controls in code/config. **No operational drill, deployment,
restore, PITR/RPO/RTO exercise, outage simulation or external integration was performed** — those
remain `BLOCKED` under the no-operational-resources constraint. Presence of a control is `TESTED` at
static-inventory scope only; it is not proof of operational behavior.

| ID | Check | Evidence | Result | Status |
|---|---|---|---|---|
| W7-01 | Health / readiness / liveness probe surface | `app.main.app.openapi()` filtered paths | Full probe family present: `/health`, `/health/live`, `/health/ready`, `/health/deep`, `/health/kernel`, `/health/status`, plus `/metrics` and per-domain health endpoints (73 health/ready/metrics-matched paths total) | `TESTED` (static) |
| W7-02 | Resilience primitives | source scan | `CircuitBreaker` + `CircuitBreakerManager` (`app/kernel/gateway/circuit_breaker.py`); `RetryExecutor` + `RetryStatus` + `RetryOutcome` (`app/health_core/reliability/retry.py`); `RetryQueue` (`app/kernel/event_bus/retry_queue.py`); `job_retry`, `health_routing` present | `TESTED` (static) |
| W7-03 | Deployment / rollback topology | `.github/workflows/` + K8s manifests | Rollback & staged-deploy workflows present: `auto-rollback.yml`, `rollback.yml`, `blue-green-deploy.yml`, `canary-deploy.yml`, `deploy.yml`, `preview-deploy.yml`. 45 K8s YAML manifests; 17 with `livenessProbe`/`readinessProbe`/`startupProbe`; 9 `HorizontalPodAutoscaler`; 1 `PodDisruptionBudget` | `TESTED` (static) |

**Honest gaps:** only **1** `PodDisruptionBudget` across 45 K8s manifests (voluntary-disruption
protection is not broadly applied); resilience primitives are present in source but **not exercised
by any operational drill in this engagement**; restore/PITR, clinical-alert full-outage and
device/network-partition drills remain `BLOCKED`. The already-recorded Wave 5 offline limitation
(non-CRDT merge, quarantine-by-design) governs the durability claim. No release, `PRODUCTION READY`,
or v1.0.0 claim.

---

## 16. Wave 2 (continuation) — care-continuum FK-closure migration `20261119_0003` (2026-11-19)

New uncommitted artifacts (both currently untracked; **no commit/push/PR made**):
`backend/migrations/versions/20261119_0003_care_continuum_closure.py` and
`backend/tests/migrations/test_care_continuum_closure_migration.py`.

**Problem confirmed from live code state (not assumed):** 45 `cc_*` ORM tables (1,706 columns,
249 FKs, 467 indexes; 1,016-line router + 1,084-line service) had ZERO migration coverage. Their
FKs reach `national_*` tables, so a cc-only migration would leave dangling FK targets on a fresh
install.

**True missing set derived from ACTUAL DB state** (fresh disposable PG upgraded to prior head
`20261119_0002`, then inspected; static migration scans are unreliable because earlier migrations
use variable-named `create_table`): transitive FK closure = 63 tables (45 `cc_*` + 18 `national_*`);
`national_facilities` already exists from `20260813_0004` → excluded. **True missing = 62 tables
(45 `cc_*` + 17 `national_*`).** DDL was generated by Alembic autogenerate from the exact 63-table
closure metadata then the `national_facilities` create/drop ops were filtered out at the structured-op
level (so all FKs still resolve). No hand-written column lists.

| ID | Check | Evidence | Result | Status |
|---|---|---|---|---|
| W2C-01 | Migration graph | `ScriptDirectory`: single head `20261119_0003`, `down_revision=20261119_0002`; file compiles | PASS | `TESTED` |
| W2C-02 | DDL shape | 62 `create_table`, 62 `drop_table`, 619 `create_index`, 619 `drop_index`, 0 `national_facilities` create/drop | PASS | `TESTED` |
| W2C-03 | Full-chain lifecycle (authoritative) | Fresh `upgrade head` → `downgrade -1` → re-`upgrade head` on unique disposable PG16 DB: `AFTER_UPGRADE total=497 target_cc=45 target_national=17`; `AFTER_DOWNGRADE total=435 target_cc=0 target_national=0`; `AFTER_REUPGRADE total=497 target_cc=45 target_national=17`; `RESULT=OK`, EXIT=0. Reproduced 4× (incl. post-Ruff-quote-fix) | PASS | `TESTED` |
| W2C-04 | Enum DDL root cause + fix | Generic `sa.Enum(create_type=False)` silently drops the PG-only kwarg (PG impl defaults `create_type=True`, emits `CREATE TYPE` → prior `type "gender" already exists` on re-upgrade). Fixed by rendering `postgresql.ENUM(..., create_type=False)` and managing the 24 shared types with idempotent `CREATE TYPE`/`DROP TYPE IF EXISTS`. 44 enum columns, 24 types, labels match ORM exactly | PASS | `TESTED` |
| W2C-05 | Regression tests | `pytest tests/migrations/test_care_continuum_closure_migration.py -q` → **7 passed, 1 skipped (DB opt-in), EXIT=0**; with `GULA_CC_MIGRATION_ADMIN_DB_URL` set → **8 passed, EXIT=0** (full-chain + synthetic FK/UNIQUE/ENUM constraints on throwaway DB) | PASS | `TESTED` |
| W2C-06 | Static parity guards | derive closure from the same merged 17-base metadata as `env.py`; assert exact table set, op counts, enum names+labels, idempotency guard, no facility recreation, every `cc_*` ORM table covered | PASS | `TESTED` |
| W2C-07 | Hygiene | Ruff clean on both files (0 errors; generated single→double quote normalization applied); `py_compile` OK; trailing-ws/tabs/CR = 0; `git diff --no-index --check /dev/null <file>` produced 0 bytes of whitespace-error output on both files (rc=1 is the expected "files differ" result for a new file, not a hygiene failure); secret/PHI scan clean (only schema column/index names matched) | PASS | `TESTED` |

**Status discipline:** the first fresh-context Team C adversarial review
(`/tmp/opencode/teamc_cc_review_report.md`) returned `VERDICT: BLOCKED` on one reproducible **P1**
data-integrity defect (below); it independently verified claims 1–4 on four throwaway DBs. The defect
was fixed, and a **second fresh-context Team C re-verification** (report
`/tmp/opencode/teamc_cc_reverify_report.md`) awarded **`VERDICT: INDEPENDENTLY VERIFIED`**
(engineering scope), with all checks A–G PASS and a falsification proof (reverting the fix in a
`/tmp` copy made the two new P1 guards fail: 2 failed / 6 passed). The award was issued by Team C,
**not self-awarded**. No `PRODUCTION READY` or release claim. No operational DB, no real patient
data, no `create_all()`, no fake stamp, no destructive migration. HEAD and the 20 staged `R100`
renames were unchanged by this work. A commit remains gated on exact per-file provenance across the
pre-existing 149 modified / 598 untracked paths.

### 16.1 Team C P1 finding and fix (2026-11-19, same session)

| ID | Check | Evidence | Result | Status |
|---|---|---|---|---|
| W2C-08 | Team C independent review | Fresh-context review on 4 disposable PG DBs: claims 1–4 VERIFIED (62 missing tables, additive/reversible DDL, 24 correct enum types, full lifecycle). Claim 5 REFUTED IN PART: one declared FK absent | P1 found | `TESTED` |
| W2C-09 | P1 defect — `use_alter=True` FK silently omitted | `national_encounters.referral_id → national_referrals.id` declared with `use_alter=True` (mutual FK cycle). Alembic `create_table()` emits only `CreateTable`, which skips such FKs; no `AddConstraint`. Live DB: 301 vs 302 declared FKs; bogus `referral_id` accepted | CONFIRMED | `TESTED` |
| W2C-10 | P1 fix | Added explicit `op.create_foreign_key("fk_national_encounters_referral", ..., ondelete="SET NULL")` after both tables exist, plus symmetric `op.drop_constraint(...)` before `national_referrals` is dropped. Regression: static guard (every `use_alter=True` FK needs a compensating create+drop), live FK-count parity (302), specific FK presence, and bogus-`referral_id` rejection on a REAL migrated table | fix applied | `TESTED` |
| W2C-11 | Post-fix local verification | `py_compile` OK; Ruff clean on both files; static tests `7 passed, 1 skipped`; DB lifecycle with `GULA_CC_MIGRATION_ADMIN_DB_URL` → **1 passed (188s), EXIT=0** (FK parity 302, specific FK present, bogus referral rejected, downgrade/re-upgrade clean); authoritative full-chain e2e → `AFTER_UPGRADE 497/45/17`, `AFTER_DOWNGRADE 435/0/0`, `AFTER_REUPGRADE 497/45/17`, `RESULT=OK`, EXIT=0; cross-test regression set **54 passed, 1 skipped**; post-fix full suite **5124 passed / 28 skipped / EXIT=0** | PASS | `TESTED` |
| W2C-12 | Fresh-context Team C re-verification of the P1 fix | Report `/tmp/opencode/teamc_cc_reverify_report.md`, `VERDICT: INDEPENDENTLY VERIFIED` (engineering scope). A: live FK parity **302 declared = 302 live** + specific FK `ondelete=SET NULL`, bogus referral REJECTED, NULL/valid accepted, delete→SET NULL; B/C: `downgrade -1` + re-upgrade clean, 0 pre-existing objects lost, 0 enums survive downgrade; D: no duplicate constraint/index names, both idempotency guards verified; E: both P2s remain latent; F: reverting the fix in a `/tmp` copy → **2 failed / 6 passed** on the exact two new P1 guards (non-vacuous); G: real files 7 passed/1 skipped without URL, 8 passed with URL. No P0/P1 remains | **INDEPENDENTLY VERIFIED** (engineering scope, issued by Team C) | `INDEPENDENTLY VERIFIED` |

**Team C P2 residuals (documented, not triggered in this chain):** (a) enum DO blocks guard only
`pg_type.typname`, not labels/schema, and downgrade drops types unconditionally — prior head had 0
enums, so no present impact; (b) ~123–125 duplicate index column-sets inherited from ORM metadata
(`index=True` + explicit `Index`), ~20% write amplification, not introduced by this revision.

**Final status (W2C-12):** revision `20261119_0003` and its regression test are
**`INDEPENDENTLY VERIFIED`** at engineering scope — the award was issued by a fresh-context Team C
re-verification, not self-awarded. No P0/P1 remains. `PRODUCTION READY` and any release/v1.0.0 claim
remain unawarded. Informational P3 caveat: the table-existence idempotency guard cannot retro-apply
the FK fix to a database that already applied an unreleased pre-fix draft of the same revision ID;
no such database exists in this environment.

**Git/provenance invariants re-verified after all §16 edits (exact `md5sum`, not abbreviated):**

| Protected object | Expected | Actual | Result |
|---|---|---|---|
| `GOVERNANCE/FINAL_DECISION.md` | `effdfeaf10234678d83b2668c4489552` | `effdfeaf10234678d83b2668c4489552` | PASS |
| `GOVERNANCE/IDENTITY_REMEDIATION/MPI_FINAL_INDEPENDENT_AUDIT.md` | `1a02c01563c93b07a7cdb92c0462bf36` | `1a02c01563c93b07a7cdb92c0462bf36` | PASS |
| `GOVERNANCE/IDENTITY_REMEDIATION/MPI_INDEPENDENT_AUDIT_FINDINGS.md` | `ea3969d09aaf7b0b28a065838b44a594` | `ea3969d09aaf7b0b28a065838b44a594` | PASS |
| `gula-integration` HEAD | `2206654dc713ea2de8c564a3207dfe05fde23549` | `2206654dc713ea2de8c564a3207dfe05fde23549` | PASS |
| sibling `gula-platform` HEAD | `f478676b6fc375338648dde46fbf076c015a3f91` | `f478676b6fc375338648dde46fbf076c015a3f91` | PASS |
| staged `R100` renames | 20 | 20 | PASS |

No commit, push, PR, staging operation, history rewrite or protected-decision change was performed.

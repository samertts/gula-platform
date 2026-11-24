# GECS — BLOCKER REGISTRY

**Purpose (canonical):** every blocker with its type, root cause, exit criteria and current status.
Canonical detail remains in `GOVERNANCE/UNIFICATION_BLOCKERS.md` (imported rows keep their source
IDs) and the reports referenced per row. **Priority by: patient safety → data integrity → security →
release impact.** Type: `approval` (needs a named human decision) · `technical` (code/schema) ·
`evidence` (a fact has not been measured/verified) · `external`.
**Created:** 2026-11-17 · Severity P0–P4 (P0 blocks convergence/release; P1 blocks subsystem
certification; P2 tracked debt).

## A. Approval blockers (cannot be cleared by any amount of code work)

| ID | Description | Sev | Type | Root cause | Affected phases | Dependencies | Required approval | Resolution plan | Exit criteria | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| B-001 | NR-011 two-part `env.py` fix not approved | P0 | approval | autonomous authority boundary (W1_CHECKPOINT §8) | W1-GATE, MIG-EXISTING | D-003 | Architecture | present probes A/B/C + package §A6 for decision | written approval of D-003 | **CLEARED — 2026-11-17** (owner approval recorded, DECISION_REGISTRY §A1; row retained) |
| B-002 | ADR-A migration strategy not approved | P0 | approval | schema change requires Program Director/Architecture | MIG-EXISTING, all release gates | B-001 | Program Director / Architecture | decision package §A11 matrix reviewed | written approval of D-001 | **CLEARED — 2026-11-17** (owner approval recorded, DECISION_REGISTRY §A1; row retained) |
| B-003 | ADR-B table ownership not approved | P0 | approval | dropping/owning possibly pre-existing tables is destructive | DB-READINESS (criterion 5) | D-002 | Program Director / Architecture + Database owner | package §A5 contract reviewed | owner recorded + exclusion asserted | **CLEARED — 2026-11-17** (owner approval recorded; ownership *record* itself = W-038, still open) |
| B-004 | Rollback policy not recorded as a decision | P1 | approval | runbook choice, not a code change | RECOVERY, RELEASE | D-004 | Database / Operations owner | package §A7 + Phase C T3/T4 evidence reviewed | runbook approved; partial downgrade prohibition accepted | **CLEARED — 2026-11-17** (policy approved; drill/RPO-RTO still open as B-016 → W-034) |
| B-005 | Human security review + Program Director sign-off absent (criterion 7) | P0 | approval | remediation exists but is uncommitted/unreviewed | SECURITY-PRIVACY, RELEASE | W-015, W-016 | Security lead + Program Director | review report **and** remediation diff; accept/reject R-01…R-11 | criterion 7 MET with signatures | **OPEN — PENDING_APPROVAL** |
| B-006 | No commit authorization — all work uncommitted | P0 | approval | Program Director review required before any commit | all | B-005 (security) + PD | Program Director | review change-set; explicit commit instruction | authorized commit exists | **OPEN — PENDING_APPROVAL** (no commit/push/merge/PR permitted) |

## B. Technical blockers

| ID | Description | Sev | Type | Root cause | Affected phases | Dependencies | Required approval | Resolution plan | Exit criteria | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| B-007 | W1 strict-schema gate **FAILED** — 119/872 (19 of 53 modules) | P0 | technical | schema gaps (F-001, F-002) + NR-011 | W1-GATE, RELEASE | B-001, B-002 | none beyond D-001/D-003 | ADR-A contexts → strict rerun twice | **872/872**, fingerprint delta = approved migrations only | **OPEN — FAILED (evidence complete, fix blocked)** |
| B-008 | 340 ORM tables absent from migrated schema | P0 | technical | tables exist in no migration; autogenerate unusable | MIG-EXISTING | B-001, B-002 | D-001, D-002 | waves W-026…W-030 by bounded context | per-wave strict subset green; 0 unexplained missing | **OPEN — proven** |
| B-009 | 82 tables / 664 columns drift (70 insert-breaking) | P0 | technical | migrations never added ORM columns | MIG-EXISTING | B-002 | D-001 | reviewed additive migrations (W-029 first) | drift 0 on shipping surfaces; strict drift failures 0 | **OPEN — proven** |
| B-010 | Partial downgrade falsely succeeds (2 version rows + 7 residual tables, 412≠405) | P0 | technical | branch topology below target revision | RECOVERY, CI | B-004 | D-004 | prohibit in runbook; add CI state assertion (W-037) | no workflow uses partial downgrade; CI asserts state | **OPEN — proven (unsafe)** |
| B-011 | `app.main` import-time AI-registry defect (`:caps::jsonb`) | P1 | technical | syntax defect in registry sync | PLATFORM | none | separate ticket (W-042) | reproduce → fix → regression test | registry syncs; import clean | **OPEN — proven** |
| B-012 | 20 edge-platform runtime-guard failures on migrated schema | P1 | technical | guard/schema conflict unadjudicated | W1-GATE | none | adjudication (W-035) | decide guard-vs-schema without weakening guard | written disposition; failures classified not counted as migration fixes | **OPEN — proven** |
| B-013 | Test-isolation leak (`SessionLocal` on engine; 12 `audit_logs` rows) | P1 | technical (test-only) | fixture connection binding | QA-HYGIENE, W1-GATE repeatability | category-B authorization | QA Lead (test change) | fix fixture binding (W-031) | two consecutive clean strict runs | **OPEN — proven, not patched** |
| B-014 | Type overflow (`disk_free_bytes` integer; 4 type-risk columns) | P1 | technical | migration type choices | MIG-EXISTING | B-002 | D-001 | widen in reviewed migration (W-036) | 2 overflow failures green; types reconciled | **OPEN — proven** |
| B-015 | No shipping/non-shipping register — 340 absent tables have live app refs | P0 | technical/governance | register never created | RELEASE | B-002 | D-001 | create register (W-025), enforce in CI | every gated surface named; CI can fail on ungated enablement | **OPEN — risk (X-01)** |
| B-022 | Two declarative bases unregistered with Alembic → autogenerate blind spot (F-085) | P1 | technical/evidence | `DocIntelBase` (21 classes) + `InsBase` (30 classes) omitted from `env.py:134-151` `target_metadata` (E-063); 19 runtime bases on disk vs 17 registered | MIG-EXISTING, DB-READINESS | B-008, B-009 | D-001 wave / Database owner | register both bases in a category-D change with fresh-clone autogenerate + strict-subset verification; do not auto-apply removals | 19/19 bases registered; autogenerate sees the 51 mapped classes; no operational DDL | **OPEN — new CC-010 finding; NOT remediated** (no `env.py` edit; NR-011 delta stays `+49/-0`) |

## C. Evidence blockers (facts not yet measured or verified)

| ID | Description | Sev | Type | Root cause | Affected phases | Dependencies | Required approval | Resolution plan | Exit criteria | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| B-016 | RPO / RTO **unmeasured** — no drill produced a figure | P1 | evidence | restore/PITR drills never run here | RECOVERY | B-004 | D-004 | execute restore + PITR drills (W-034) | measured values recorded, or "unmeasured" formally retained | **OPEN — missing evidence** |
| B-017 | No production-like snapshot (only 51 rows available) | P1 | evidence | only prior snapshot is tiny | DB-READINESS (criterion 5c) | external data | Database owner | obtain production-like snapshot → rehearsal (W-039) | rehearsal on realistic volume with checksums | **OPEN — external dependency** |
| B-018 | Coverage holes: referrals, `care_continuum` untested; hospital = 1 module | P1 | evidence | tests never written | PATIENT-WORKFLOW, QA | B-002 (strict context) + QA authorization | QA Lead | add functional tests (W-032) | tests exist and pass on migration-built schema | **OPEN — documented (F-007)** |
| B-019 | Tenant/authorization isolation untested against migration-only DB | P1 | evidence | no isolation test exists for that schema | IDENTITY-AUTHZ, PATIENT-DATA | B-002 | Security + QA | dedicated isolation tests post-approval | isolation tests pass; `tenant_id` semantics decided | **OPEN — investigate (F-027)** |
| B-020 | GLOSI: no human security/legal/technical review | P2 | evidence | human review never scheduled | GLOSI | none | GLOSI owner | human review (W-022) | review recorded | **OPEN — not run (F-059)** |
| B-021 | No retained PR-run evidence for the baseline commit (`CI-RUN-EVIDENCE`) | P2 | evidence | Actions logs not retained | CI | none | — | retain job logs per commit | logs exist for baseline | **OPEN — UNKNOWN (source: blockers §1)** |

## D. Imported canonical blockers (source IDs preserved — status as recorded, never rewritten)

| Source ID | Sev | Type | Summary | Status (as recorded) | GECS link |
|---|---|---|---|---|---|
| NR-003 | P0 | technical | Pharmacy PK type divergence `Integer` vs `String(26)` FKs | **FIXED (identity) — uncommitted** | D-015, B-006 |
| NR-006 | P1 | technical | `national_facilities` mapped by two ORM packages | **OPEN** | F-014, D-002, B-003 |
| NR-007 | P1 | technical | Entity-agnostic clinical state machine | **OPEN** | not in GECS scope yet |
| NR-009 | P0 | technical | FK to non-migrated `hospital_operation_theaters` | **FIXED (conditional FK) — uncommitted** | D-016, B-006 |
| NR-010 / NR-010-RESIDUAL | P0/P1 | technical | Downgrade defects repaired; 3 residual tables remain unowned | **FIXED — uncommitted**; residual **OPEN** | D-017, F-013, B-003 |
| NR-011 | P0 | technical | `alembic check` aborts (see B-001 for approval half) | **OPEN — root cause corrected** | F-010, D-003 |
| NR-012 | P2 | technical | Legacy sequence default after type change | **OPEN — documented debt** | F-011 |
| CI-RUN-EVIDENCE | P1 | evidence | No retained PR-run evidence | **UNKNOWN** | B-021 |
| AUDIT-COVERAGE | P1 | evidence | Most risk categories not audited | **NOT AUDITED** | B-019-adjacent |
| SECURITY-PRIVACY | P1 | approval | Privacy/consent/tenant/audit/recovery posture not independently verified | **PARTIAL — NOT CERTIFIED** | B-005, D-020 |
| CR-1 | P1 | technical | Dual workflow runtimes | **EXECUTED — VERIFIED (uncommitted)** | D-013 |
| CR-2 | P1 | approval | Authoritative web client | **DECIDED — frontend-v3 primary** | D-014 |
| CR-3 | P1 | approval | Local `security/` toolkit vs in-app security (158 standalone files) | **DOCUMENTED / NOT CERTIFIED** — human review of carry-forward controls required | B-005-adjacent |
| WEB-SURFACE | P1 | technical | `frontend-v3` ownership | **PARTIAL** (resolves with CR-2) | D-014 |
| MIG-TAIL | P2 | technical | Six forward migrations unexercised | **RESOLVED (uncommitted)** | W-001 |
| CODE-MERGE | P0 | technical | Backend module merge incomplete | **DONE (uncommitted) — release blocked by security** | W-002…W-010, B-005 |
| NR-006-dupe | P1 | technical | 4 of 9 service routes still inline (2,216 LOC) | **PARTIAL (uncommitted)** | F-061, W-040 |
| SEC-AUTHZ / SEC-NIAM / SEC-NATIONAL | P0 | security | Control-plane / NIAM / national-surface authorization gaps | **REMEDIATED — uncommitted, unreviewed** | F-031…F-035, B-005 |
| SEC-REDIS / SEC-COOKIE / SEC-UNGUARDED / SEC-SELFVERIFY | P1 | security | Redis degradation, cookies, 91 endpoints, self-verification | **REMEDIATED — uncommitted, unreviewed** | F-036…F-043, B-005 |
| SEC-RESIDUALS | P2 | security | 11 endpoint-review residuals | **OPEN — documented** | F-044…F-054 |
| DEP-AUDIT-BACKEND | P1 | technical | 55 dependency advisories; pip wheel path network-blocked | **VERIFIED (0 advisories)**; wheel path **BLOCKED by throttling** | F-055, F-056 |
| LINT-MYPY-PORTED | P2 | technical | ruff 35 / mypy 71 scoped pre-existing | **OPEN — tracked** | F-058 |
| W1-* (9 rows) | P0–P2 | technical | Strict-schema findings | **OPEN** (as recorded §3A) | F-001…F-009 |
| MIG-EXISTING | P0 | evidence | Criterion 5 not met (4 sub-conditions) | **PARTIAL — NOT MET** | F-016, B-017, B-003, B-004, B-001 |

**Counts:** 36 blockers — 6 approval (B-001…B-006; **B-001…B-004 CLEARED 2026-11-17 by owner
approval of D-001…D-004**, rows retained), 9 technical (B-007…B-015), 6 evidence
(B-016…B-021), 15 imported canonical rows (source IDs preserved, 4 already FIXED/RESOLVED but
uncommitted). **Open P0:** B-005, B-006, B-007, B-008, B-009, B-010, B-015.
*Historical note:* the line "No blocker is closed by GECS" held for the GECS-foundation phase;
closure of B-001…B-004 happened only via the 2026-11-17 owner approval record, with exit criteria
named per row.*

## E. Phase 3–8 cross-references (additive — NO blocker opened or closed)

| Blocker | New findings/evidence now indexed | Status effect |
|---|---|---|
| B-005 (security sign-off) | `DECISION_REGISTRY.md` §D authorization/tenant/audit evidence (E-046/E-047); W-033 | **OPEN** — test evidence is not human sign-off |
| B-007 (strict gate) | E-046…E-052 (740 targeted passes) | **OPEN / FAILED** — different corpus; 119/872 unchanged; no rerun |
| B-010 (unsafe rollback) | F-012 referenced in engine verification §5 (recovery untouched) | **OPEN** — no rollback work performed |
| B-015 (shipping register) | F-071 dormant scaffold, F-068 unmounted national CDS route | **OPEN** — neither surface was enabled or registered |
| B-016 / B-017 (evidence gaps) | Phase 3 made 0 runtime/production claims (0/39 engines verified) | **OPEN** — RPO/RTO and production-like snapshot still absent |
| B-018 (coverage holes) | F-066/F-067/F-070/F-072 recorded as new missing-evidence findings; W-044/W-045 PENDING_APPROVAL | **OPEN** — no test added; F-007 unchanged |
| B-019 (tenant isolation) | E-046 `test_tenant_isolation_matrix` 21 (synthetic harness only) | **OPEN** — migration-built schema isolation still untested |
| D-012 / G-10 (offline) | F-069 first-wins `CRDT_MERGE`, F-028 in-memory queue (E-046) | **OPEN** — W-047 PENDING; R-OFF-1 unsatisfied |

**Counts unchanged:** 36 blockers (B-001…B-004 CLEARED with rows retained; open P0 list as above).
Phase 3–8 recorded evidence against blockers; it did **not** close, downgrade or raise any blocker.

---

## E. CC-010 addition (append-only — 2026-11-17)

- **B-022 added** (technical/evidence, P1): unregistered `DocIntelBase`/`InsBase` (F-085, E-063).
  This is the **only** blocker created by the post-stabilization completion program. It records a
  source-verified Alembic blind spot; it does **not** assert an application defect and was **not**
  remediated (no `env.py` edit; NR-011 delta remains `+49/-0`).
- **No blocker closed, downgraded or re-scoped.** B-005/B-007/B-016/B-017 etc. retain their status;
  W-017 strict gate stays **FAILED 119/872** (E-001), D-020/D-021 stay `PENDING_APPROVAL`.
- **Count clarification (does not rewrite the historical line above):** canonical GECS blocker IDs
  are now **B-001…B-022 (22 rows)**; the earlier "36" counted the imported source-ID rows of §D
  together with the GECS B-IDs. Imported source-ID rows remain source-labelled and are never renumbered.

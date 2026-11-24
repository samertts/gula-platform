# APPROVAL MATRIX — PROGRAM-GULA-PARALLEL-001

**Status:** PROPOSED — no approval has been granted by this document
**Date:** 2026-11-19
**Scope:** all approval gates needed to move from planning to Wave C execution
**Related:** `POST_WAVE_B_EXECUTION_PLAN.md`, `P0_CONTAINMENT_PLAN.md`, `ISOLATION_OPTIONS.md`, `TEST_BASELINE_PLAN.md`

> Every gate below is **ungranted**. "Proposed owner" is the role the orchestrator
> recommends; the actual approver must be named by the user. No fix proceeds without
> its gate recorded as APPROVED. Categories overlap; the primary gate is listed first.

---

## 1. User decisions (highest priority — blocks everything else)

| ID | Decision required | Proposed authority | Evidence | On approval | On denial |
|---|---|---|---|---|---|
| U-01 | Release the three patch files for isolated replication/commit | USER | `git status`: two ` M`, one `??`; Appendix A of execution plan | Option D/E testing can begin | Patch stays unverified; certification halted |
| U-02 | Choose isolation option (D recommended, E acceptable, B baseline-only) | USER + ORCH | `ISOLATION_OPTIONS.md` §3 | Environment established | No remediation environment |
| U-03 | Accept severity reassessment (A02-001, A06-001 → P1; 6 P0s kept) | USER | Execution plan §2 | Backlog rebaselined | Findings remain as originally typed; plan revised |
| U-04 | Confirm certification halt on A06-001 + A06-002 despite A06-001 downgrade | USER + CLIN | Standing instruction | Halt retained | Halt would be lifted — **not recommended** |
| U-05 | Authorize 36-test execution in isolated clone; confirm no DB/service/prod ops | USER + ORCH | `TEST_BASELINE_PLAN.md` §3–4 | Baseline produced | Patch stays NOT VERIFIED |
| U-06 | Authorize A08-R001 containment notice + guard **design** (no edit/move of original) | USER + ORCH | `P0_CONTAINMENT_PLAN.md §1`; `deploy.sh:173` | DO-NOT-RUN notice issued | Script remains an unmitigated landmine |
| U-07 | Name SEC / CLIN / DB-API / ARCH / CI owners for §5 batches | USER | Execution plan §5 | Gates can be sought | All remediation remains blocked |
| U-08 | Decide A01 architecture: open ADRs now or defer | USER + ARCH | A01-001…019 | Structural work scoped | A01 deferred to separate program |

---

## 2. Per-domain approval gates

### 2.1 Clinical safety & workflows (A03 + A05-001…005)
| Gate | Findings | Proposed approver | Status | Required before |
|---|---|---|---|---|
| CLIN-C01 | A05-001 critical-result delivery policy | Clinical owner | UNGRANTED | Any delivery-worker design |
| CLIN-C02 | A05-002 QC gate semantics | Clinical owner | UNGRANTED | Any auto-validation change |
| CLIN-C03 | A03-003 approval separation | Clinical owner + SEC | UNGRANTED | Pharmacy page/API change |
| CLIN-C04 | A03-001/002/009/012 synthetic-as-live rules | Clinical owner | UNGRANTED | Page-local changes |
| CLIN-C05 | A05-003/004/006 clinical semantics | Clinical owner | UNGRANTED | Correction/AI/capability fixes |
| SEC-C03 | A03-005/007/013 RBAC/PHI | SEC owner | UNGRANTED | Workspace/PHI changes |
| DB-API-C03 | A03-004/006/008 contracts | DB-API owner | UNGRANTED | Endpoint contract changes |

### 2.2 Offline synchronization & event delivery (A06)
| Gate | Findings | Proposed approver | Status | Required before |
|---|---|---|---|---|
| USER-O01 | A06-002 patch release | USER | UNGRANTED | Any patch replication/adoption |
| CLIN-O01 | A06-002 clinical merge semantics | Clinical owner | UNGRANTED | Adoption of quarantine |
| CLIN-O02 | A06-001 certification criteria | Clinical owner + A09 | UNGRANTED | Lifting certification halt |
| SEC-O01 | A06-009 signature, A06-016 replay integrity | SEC owner | UNGRANTED | Security changes |
| DB-API-O01 | A06-003/013/014/017/018/020 outbox & idempotency | DB-API owner | UNGRANTED | Persistence/outbox changes |
| ARCH-O01 | A06-004/005/007/012 architecture | ARCH owner | UNGRANTED | Structural offline changes |
| ORCH-O01 | Certification halt release (only after both A06-001/002 verified) | ORCH + USER | UNGRANTED | Any certification claim |

### 2.3 Security & identity (A04)
| Gate | Findings | Proposed approver | Status | Required before |
|---|---|---|---|---|
| SEC-I01 | A04-001/002/003 NIAM controls | SEC owner | UNGRANTED | Any auth route change |
| SEC-I02 | A04-004/005/006/008 OAuth2/password/scope | SEC owner | UNGRANTED | OAuth2 or policy change |
| SEC-I03 | A04-007/009 token-in-query, bcrypt perf | SEC owner | UNGRANTED | Contract/perf change |
| USER-I02 | A04-002 file is USER ` M` | USER | UNGRANTED | Editing that file |
| DB-API-I01 | A04-009 migration-linked change | DB-API owner | UNGRANTED | Schema change |

### 2.4 FHIR & database integrity (A05-006…008 + A07)
| Gate | Findings | Proposed approver | Status | Required before |
|---|---|---|---|---|
| CLIN-F01 | A05-007 transaction atomicity | Clinical/interop owner | UNGRANTED | Any `/fhir` change |
| DB-API-F01 | A05-007, A07-014, A07-015/016 | DB-API owner | UNGRANTED | Any DB/migration/schema change |
| USER-F01 | A07-015/016 untracked migrations | USER | UNGRANTED | Any migration work |
| DB-API-F02 | A07-001 tenant typing, A07-008 OpenAPI, A07-009/011/017 contracts | DB-API owner | UNGRANTED | Contract changes |
| SEC-F02 | A07-001 cross-domain principal | SEC owner | UNGRANTED | Auth typing change |
| ORCH-F01 | No-DB-execution rule confirmation | ORCH | UNGRANTED | Any DB-touching test |

### 2.5 frontend-v3 design system & UX (A02)
| Gate | Findings | Proposed approver | Status | Required before |
|---|---|---|---|---|
| VIS-D01 | A02-001 token aliases | Design/visual reviewer | UNGRANTED | Token change |
| A11Y-D01 | A02-002/004/006/007 a11y | Accessibility reviewer | UNGRANTED | Contrast/semantics changes |
| A03-D01 | A02-013/017 consumer coordination | A03 owner | UNGRANTED | Shared-component API change |
| USER-D01 | A02-020 `vite.config.ts` is USER-owned | USER | UNGRANTED | Theme colour change |

### 2.6 DevOps & reliability (A08)
| Gate | Findings | Proposed approver | Status | Required before |
|---|---|---|---|---|
| ORCH-R01 | A08-R001 containment | ORCH + USER | UNGRANTED | Any script/workflow action |
| CI-R01 | A08-001/002/R002…R006 pipeline & deploy | CI/release owner | UNGRANTED | Workflow changes |
| SEC-R01 | A08-R003…R007/R007 rollback/canary safety | SEC owner | UNGRANTED | Deploy safety changes |
| COST-R01 | A08-004 (replace commercial `safety`), R009/R013/R014 | COST owner (Free First) | UNGRANTED | Tooling/cloud decisions |
| DATA-R01 | A08-R008/R009/R015 backup/DR claims | Data owner | UNGRANTED | DR documentation changes |

### 2.7 Testing & CI quality gates (A09)
| Gate | Findings | Proposed approver | Status | Required before |
|---|---|---|---|---|
| USER-Q01 | A09-001/002 USER-owned files | USER | UNGRANTED | Editing those files |
| CI-Q01 | A09-002/003/011 gate wiring | CI owner | UNGRANTED | CI config changes |
| A09-Q02 | A09-005/008/009/012 assertion fixes | A09 owner (assigned) | UNGRANTED | Test changes |
| A02-Q01 | A09-010 contrast re-enable | A02 reviewer | UNGRANTED | Re-enabling axe contrast rule |

### 2.8 Architecture & structural (A01)
| Gate | Findings | Proposed approver | Status | Required before |
|---|---|---|---|---|
| ARCH-A01 | A01-001…004, 012…019 structural decisions | ARCH owner | UNGRANTED | Any structural change |
| ARCH-A02 | A01-005…009, 011 service/cycles/gate catalog | ARCH + DB-API + CI | UNGRANTED | Composition/gate changes |
| CLIN-A02 | A01-016 FHIR consolidation | Clinical owner | UNGRANTED | FHIR implementation consolidation |

---

## 3. Standing prohibitions (independent of approvals)

- No merge, cherry-pick, rebase, force-push, reset, clean, forced checkout, stash operation, worktree create/delete, branch delete, or history rewrite.
- No migration execution against any database; no production deploy; no service start.
- No paid dependency without a documented cost exception (Free First / Open Source First / Self-Hosted First / No Vendor Lock-In).
- No new agents without explicit user authorization.
- No claim of "verified" without machine-readable artifacts from an isolated execution.

---

## 4. Minimum approval set to begin any remediation

1. U-01, U-02, U-05 (patch release, isolation, test authorization).
2. U-06 (A08-R001 containment) and U-07 (named owners).
3. Domain gate for the specific batch being started (§2).
4. For offline work: CLIN-O01/CLIN-O02 and the certification-halt confirmation U-04.

Until these are recorded, Wave C remains **BLOCKED**, 175 findings remain `Discovered`, and the register stays **Fixed 0 / Verified 0**.

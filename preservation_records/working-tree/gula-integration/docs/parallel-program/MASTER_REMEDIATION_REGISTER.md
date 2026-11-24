# MASTER REMEDIATION REGISTER — PROGRAM-GULA-PARALLEL-001

**Wave:** B (Consolidation) — **COMPLETE**
**Orchestrator:** Principal Engineering Orchestrator (this session)
**Date:** 2026-11-19
**Source:** 9 Wave A agent reports (A01–A09), all read-only
**Status:** All fixes **BLOCKED** — Wave C **NOT AUTHORIZED** (see §11)

> Every issue below retains its **source agent finding ID** as the canonical key
> (globally unique by construction). Each finding was accepted only after confirming
> it carries: file path, technical evidence, root cause, severity, and a verification
> method. The orchestrator independently re-verified all 8 P0 findings with read-only
> git/grep checks — see §4.

---

## 1. Consolidation method

1. Collected all 24 agent report files (9 agents; 3 wrote 3 files, 6 wrote 2).
2. Parsed each report's own severity table and detailed finding sections.
3. Cross-checked reported counts against actual finding IDs and severity labels.
   - One inconsistency found and corrected by A01: summary said 18/P2=10, detail held
     19 IDs/P2=11. **Authoritative A01 count = 19 (P0:0/P1:4/P2:11/P3:4).**
4. Independently verified all 8 P0 findings against the working tree (§4).
5. Deduplicated by root cause + evidence + fix (§6).
6. Mapped cross-domain dependencies (§7) and conflicting/overlapping recommendations (§8).
7. Assigned approval category and proposed ownership to every issue (§9, §10).

---

## 2. Source audit summary (Wave A)

| Agent | Domain | Files reviewed (reported) | Findings | P0 | P1 | P2 | P3 | Reports |
|---|---|---|---|---|---|---|---|---|
| A01 | Repository & Architecture | 51 top-level dirs; full repo inventory | 19 | 0 | 4 | 11 | 4 | ARCHITECTURE_AUDIT.md, REPOSITORY_DEPENDENCY_MAP.md |
| A02 | Frontend Design System | 70 | 21 | 1 | 6 | 10 | 4 | DESIGN_SYSTEM_AUDIT.md, DESIGN_SYSTEM_REMEDIATION.md |
| A03 | Frontend Clinical Workflows | 97 pages / 13,771 lines | 16 | 1 | 10 | 4 | 1 | CLINICAL_WORKFLOW_AUDIT.md, CLINICAL_WORKFLOW_REMEDIATION.md |
| A04 | Security & Identity | ~55 + 145-secret scan | 14 | 0 | 3 | 6 | 5 | SECURITY_AUDIT.md, SECURITY_REMEDIATION_PLAN.md |
| A05 | Clinical Data & Interoperability | ~70 | 8 | 3 | 3 | 2 | 0 | CLINICAL_WORKFLOW_AUDIT.md, INTEROPERABILITY_AUDIT.md |
| A06 | Offline & Distributed | ~50 + repo-wide searches | 22 | 2 | 8 | 9 | 3 | OFFLINE_AUDIT.md, SYNCHRONIZATION_AUDIT.md |
| A07 | Backend, API & Database | ~45 deep + 63 routes + 109 migrations | 20 | 0 | 3 | 8 | 9 | BACKEND_AUDIT.md, API_CONTRACT_AUDIT.md, DATABASE_MIGRATION_AUDIT.md |
| A08 | DevOps, Performance, Reliability | ~120 / 32 workflows | 42 | 1 | 7 | 21 | 13 | DEVOPS_AUDIT.md, PERFORMANCE_AUDIT.md, RELIABILITY_AUDIT.md |
| A09 | Testing & QA | ~120 | 15 | 0 | 4 | 8 | 3 | QA_AUDIT.md, REGRESSION_TEST_PLAN.md, TEST_RESULTS.md |
| **TOTAL** | | **~700 file inspections** | **177** | **8** | **48** | **79** | **42** | 24 reports |

**Deduplicated totals:** 2 confirmed duplicate pairs merged (§6) → **175 unique issues**:
P0 **8**, P1 **47**, P2 **78**, P3 **42**. (Additional strongly-related clusters are flagged
in §7/§8 but retained as distinct issues because they have different root causes or fixes.)

---

## 3. P0/P1/P2/P3 counts

| Severity | Raw | After dedup | Disposition |
|---|---|---|---|
| **P0** | 8 | 8 | All 8 halt their component; no ad-hoc fixes permitted |
| **P1** | 48 | 47 | Approval-gated; none safe-independent |
| **P2** | 79 | 78 | Mostly approval-gated; small safe-independent subset |
| **P3** | 42 | 42 | Housekeeping; several safe-independent candidates |
| **Total** | 177 | 175 | 0 fixed, 0 verified |

---

## 4. P0 findings — evidence-backed (orchestrator independently re-verified)

| ID | Title | Key evidence (path:line) | Root cause | Independent verification | Approval |
|---|---|---|---|---|---|
| **A02-001** | Split token architecture; shipped primitives use never-generated utilities | `main.tsx:4` imports only `styles/index.css`; `bg-surface`/`border-outline`/`text-on-surface` defined in dead `src/index.css` (4 hits), used in `ui/Modal.tsx`, `Skeleton.tsx`, `EmptyState.tsx` | Two token vocabularies; active vs dead stylesheet | ✅ confirmed: active CSS 0 hits, dead CSS 4 hits, 3 consumers found | A02 + A03 coordination; visual |
| **A03-003** | Pharmacy substitution request + approval in one click on real API path | `PharmacyPosPanel.tsx:52-70` mutationFn calls `createSubstitutionRequest` then `approveSubstitution(request.id)`; `:59` hardcoded reason; `:158` button `طلب واعتماد`; `routes/index.tsx:222-223` | Request/approval collapsed into one client mutation; no distinct approval step/identity | ✅ evidence path:line confirmed present | Clinical + security approval |
| **A05-001** | Critical-result alerts queued but no clinician delivery/acknowledgement path | `lims/workflows.py:227-247,270-289,303-318`; `routes.py:2213-2229`; test asserts `notification_pending`/`clinician_notified is False` | Honest intent half implemented; no recipient policy or delivery worker | ✅ evidence reviewed; test pins honest state | Clinical owner + A07/A09 |
| **A05-002** | Auto-validation omits documented QC gate; invoked without patient/delta context | `lims/workflows.py:32-41` (5 checks documented) vs `:61-166` (no QC branch); `services.py:252-259` omits 4 context inputs; `routes.py:1346-1349` release accepts `auto_validated` | Documented fail-closed QC step never implemented; weak caller context | ✅ evidence reviewed | Clinical owner + A07/A09 |
| **A05-007** | FHIR `transaction` bundles not atomic; partial writes committed | `routes/ehr_fhir.py:1446-1497` per-entry loop; `:1498-1499` catches HTTPException per entry; `:1505-1507` single `db.commit()`, no rollback | Batch and transaction semantics conflated | ✅ confirmed: per-entry except + single commit, file CLEAN | Interop owner + A07 + A09 |
| **A06-001** | Offline reconnect simulation marks SYNCED after local hash only | `gula_offline_simulation_test.py` self-referential; guide claims "100% integrity / 0% loss" | No server/ack/idempotency; success claim circular | ✅ evidence reviewed | Clinical + QA evidence owner |
| **A06-002** | Unsafe first-seen-wins `CRDT_MERGE` in committed HEAD; safe fix only in uncommitted user work | `HEAD:offline_sync_service.py:19,176` has `CRDT_MERGE`; working tree `:20-25,200,238` has `CONFLICT_QUARANTINE` | Silent clinical overwrite; fix never committed | ✅ confirmed via `git show HEAD:` vs working tree | **USER RELEASE** + clinical + git decision |
| **A08-R001** | `emergency-recover.sh` would irreversibly destroy protected user work | `emergency-recover.sh:34` stale branch; `:71` `checkout -B`; `:76` `reset --hard`; `:81` `clean -fd`; branch absent from all 16 branches | Field-repair script left executable; no dirty-tree guard | ✅ confirmed: commands present, stale branch absent | Orchestrator + user release; **DO NOT RUN** |

**P0 rule applied:** all related work is halted. No ad-hoc remedy. A06-002 and A08-R001
additionally require explicit user release of protected work.

---

## 5. Full issue register (accepted findings)

Legend — **Safe?** = safe-fix possible in principle; **Approval**: `none` / `ARCH` / `CLIN` /
`SEC` / `DB-API` / `CI` / `USER`; **Status**: all `Discovered` at Wave B close.
Evidence is in the cited agent report at the given finding ID; all include path:line,
root cause and verification method.

### A01 — Architecture (19)
| ID | Sev | Title | Safe? | Approval | Proposed owner |
|---|---|---|---|---|---|
| A01-001 | P1 | Multiple frontend app trees outside canonical surface/workspace | No | ARCH | ORCH + A01 review |
| A01-002 | P1 | Root demo runtime duplicates backend/frontend entry points | No | ARCH + CI | ORCH |
| A01-003 | P1 | `packages/uap` declared single runtime, zero production consumers | No | ARCH | ORCH + domain owners |
| A01-004 | P1 | `platform/` parallel 636-file platform, no CI/deploy wiring | No | ARCH | ORCH; **Platform-Core: NO ACTION** |
| A01-005 | P2 | 7 `services/` stubs with direct SQL + deprecated lifespan | No | DB-API + CI | ORCH |
| A01-006 | P2 | 11 package-level import cycles despite "no cycles" invariant | No | ARCH | A01 review only |
| A01-007 | P2 | `factory.py` 91-registration single composition root | No | ARCH + SEC | A01/A04 review only |
| A01-008 | P2 | Untracked `health_core` parallel domain not wired to production | No | USER + ARCH | ORCH + user |
| A01-009 | P2 | Route→ORM imports persist despite cleanup claim | No | CLIN + DB-API | A07 review |
| A01-010 | P3 | `services/shared/` copies of canonical `shared/` modules | Conditional | ARCH + clean-file | ORCH |
| A01-011 | P2 | Frontend unification gate checks stale string catalog | Conditional | CI + clean-file | A08/A01 |
| A01-012 | P2 | 11 manifests / 9 lockfiles / 4 TS majors | No | ARCH | ORCH |
| A01-013 | P2 | Parallel apps couple to cloud SDKs/MySQL without ADR | No | ARCH + COST | ORCH (vendor coupling, not paid) |
| A01-014 | P3 | Architecture docs stale vs current tree | Yes (docs) | ARCH | ORCH |
| A01-015 | P2 | Multiple workflow/event engines; dormant scaffold + unmounted router | No | CLIN + SEC | A01/A04 review |
| A01-016 | P2 | Five FHIR implementations despite ADR-011 canonical | No | CLIN | A05 review |
| A01-017 | P3 | Two CI-active mobile stacks, no canonical client | No | ARCH + CI | ORCH |
| A01-018 | P3 | Four AI implementation trees, no canonical owner | No | CLIN + Local-AI policy | ORCH |
| A01-019 | P2 | `shared/` wide fan-in, no versioning/boundary gate | No | ARCH | ORCH |

### A02 — Design System (21)
| ID | Sev | Title | Safe? | Approval | Proposed owner |
|---|---|---|---|---|---|
| A02-001 | **P0** | Split token architecture (see §4) | Conditional | ARCH(design) | A02 + A03 |
| A02-002 | P1 | Light-theme contrast failures (3.82:1, 3.76:1, 1.22:1) | Yes | none (a11y-improving) | A02 |
| A02-003 | P1 | Flash of wrong theme; no pre-paint bootstrap | Yes | CI/HTML shell | A02 + A08 |
| A02-004 | P1 | Duplicate overlays; `Modal` no dialog semantics/focus trap | Yes | none (additive a11y) | A02 |
| A02-005 | P1 | Tajawal downloaded but never applied | Yes (CSS) / CDN needs A08 | HTML/CDN | A02 + A08 |
| A02-006 | P1 | Form errors not programmatically associated (`aria-invalid`/`describedby`) | Yes | none | A02 |
| A02-007 | P1 | `DataTable` sort/rows keyboard-inaccessible + hardcoded Arabic | Partial | none for a11y; translation for strings | A02 |
| A02-008 | P2 | Hardcoded colours bypass token layer | Conditional | visual review | A02 |
| A02-009 | P2 | RTL/LTR mirroring inconsistent; physical properties | Yes | RTL review (5 locales) | A02 |
| A02-010 | P2 | Wrong-direction flash for LTR locales | Yes | HTML shell | A02 |
| A02-011 | P2 | i18n resource/usage gaps (ku/tk/syr) | Yes | translation owner | A02 |
| A02-012 | P2 | Accessibility preference token coverage incomplete | Yes | a11y | A02 |
| A02-013 | P2 | Fragmented Loading/Error/Empty primitives | Conditional | API change (A03 imports) | A02 + A03 |
| A02-014 | P2 | `lib/utils.ts` hardcodes colours, Arabic, `ar-IQ` | Conditional | visual/i18n | A02 |
| A02-015 | P2 | Two competing focus-ring languages; Button class in dead CSS | Yes | visual | A02 |
| A02-016 | P3 | No-op animation utility classes | Yes | none | A02 |
| A02-017 | P2 | vitest-axe minimal; `color-contrast` disabled (dup → A09-010) | Yes | A09 review | A02 + A09 |
| A02-018 | P2 | Dead CSS files with conflicting tokens/stale template | Yes (after C-01) | deletion review | A02 |
| A02-019 | P3 | No central typography/line-height/breakpoint scale | Yes | visual | A02 |
| A02-020 | P3 | Browser/PWA theme colours disagree with tokens | Partial | USER (vite.config.ts) | A02 + user |
| A02-021 | P3 | Mobile shell breakpoint/grid edge cases | Yes | visual | A02 |

### A03 — Frontend Clinical Workflows (16)
| ID | Sev | Title | Safe? | Approval | Proposed owner |
|---|---|---|---|---|---|
| A03-001 | P1 | Synthetic patient registry presented as operational | Partial | CLIN + USER rule | A03 + A05 |
| A03-002 | P1 | Synthetic lab results/critical alert as operational workflow | Partial | CLIN | A03 + A05 |
| A03-003 | **P0** | Pharmacy substitution same-click approval (see §4) | UI boundary only | CLIN + SEC | A03 + A04/A07 |
| A03-004 | P1 | Real sale from fabricated encounter/payment IDs | Partial | DB-API + governance | A03 + A07 |
| A03-005 | P1 | Governed reads vs direct REST clinical pages | No | SEC + CLIN | A04/A05 review |
| A03-006 | P1 | FHIR Explorer substitutes Patient lookup for 10 types | Partial | CLIN + DB-API | A03 + A05/A07 |
| A03-007 | P1 | FHIR detail pages read arbitrary IDs, no workspace context | Partial | CLIN + SEC | A03 + A04 |
| A03-008 | P1 | Admin citizen page calls non-`/me` endpoints | Partial | DB-API | A03 + A07 |
| A03-009 | P1 | Live-capable workspaces retain synthetic data on load failure | Yes (page-local) | CLIN (live-mode rule) | A03 |
| A03-010 | P1 | API-stub pages render placeholder schemas | Yes (visibility) | none | A03 |
| A03-011 | P2 | Generated stubs ignore query errors → failed reads look empty | Yes | none | A03 |
| A03-012 | P1 | Data-quality POST inside `useQuery`; retry creates another check | Yes (page-local) | CLIN (mutation semantics) | A03 + A07 |
| A03-013 | P2 | Golden-record table displays raw `national_id` | Partial | SEC (PHI masking) | A03 + A04 |
| A03-014 | P2 | AI platform raw JSON output, no advisory/provenance boundary | Partial | CLIN | A03 + A05 |
| A03-015 | P2 | Clinical/audit action buttons inert | Yes (explanatory state) | none | A03 |
| A03-016 | P3 | Governance tabs/tier action hardcoded empty/dead controls | Yes | none | A03 |

### A04 — Security & Identity (14)
| ID | Sev | Title | Safe? | Approval | Proposed owner |
|---|---|---|---|---|---|
| A04-001 | P1 | NIAM step-up dependency defined but enforced on no route | Yes (reuse existing) | SEC | A04 + ORCH |
| A04-002 | P1 | Unauthenticated logout terminates arbitrary sessions (file is USER `M`) | Yes | SEC + USER | A04 + user |
| A04-003 | P1 | Terminated-session tokens still accepted on NIAM routes | Yes | SEC | A04 + ORCH |
| A04-004 | P2 | Self-service OAuth2 client registration, arbitrary redirects/scopes | No | SEC | A04 + ORCH |
| A04-005 | P2 | OAuth2 introspection/revocation unauthenticated | Yes | SEC | A04 |
| A04-006 | P2 | Password reset/change bypass complexity policy | Yes (shared validator) | SEC | A04 |
| A04-007 | P2 | NIAM refresh token accepted as query parameter | Partial | SEC + FE contract | A04 + A03 |
| A04-008 | P2 | Scope matching treats any authorization as national-scope | Yes | SEC | A04 |
| A04-009 | P2 | Reset-token verify does full-table bcrypt per attempt | Conditional | SEC + migration | A04 + A07 |
| A04-010 | P3 | No committed live secrets; key in gitignored `.env` (informational) | N/A | none | ORCH (verify ignore) |
| A04-011 | P3 | Weak default DB password in maintenance/dev fallback | Yes | SEC | A04 + A08 |
| A04-012 | P3 | Reverse-proxy headers trusted from any private peer | Yes | SEC + topology | A04 + A08 |
| A04-013 | P3 | Audit anchor write failures logged only, no fail-closed alert | Yes | SEC + observability | A04 + A08 |
| A04-014 | P3 | `get_current_identity` omits perm-version consistency check | Yes | SEC | A04 + A07 |

### A05 — Clinical Data & Interoperability (8)
| ID | Sev | Title | Safe? | Approval | Proposed owner |
|---|---|---|---|---|---|
| A05-001 | **P0** | No critical-result delivery/ack path (see §4) | No | CLIN | Clinical owner + A07/A09 |
| A05-002 | **P0** | Auto-validation omits QC gate (see §4) | No | CLIN | Clinical owner + A07/A09 |
| A05-003 | P1 | Correction helper records but doesn't update corrected value | No | CLIN + DB-API | A05 review → A07 |
| A05-004 | P1 | AI eval declares safety metrics it doesn't compute; silent retrieval failure | No | CLIN (AI) | A05 review + A09 |
| A05-005 | P2 | Terminology coverage partial; synthetic validators ≠ conformance | N/A (disclosure) | CLIN + COST | ORCH + terminology owner |
| A05-006 | P1 | FHIR CapabilityStatement overclaims resources/interactions/security | Yes (metadata truth) | CLIN + A07 | A05 review → A07 |
| A05-007 | **P0** | FHIR transaction bundles non-atomic (see §4) | No | CLIN + DB-API | Interop owner + A07 + A09 |
| A05-008 | P2 | MPI PostgreSQL concurrency controls not proven in checkout | Yes (test harness) | DB-API | A07 + A09 |

### A06 — Offline & Distributed (22)
| ID | Sev | Title | Safe? | Approval | Proposed owner |
|---|---|---|---|---|---|
| A06-001 | **P0** | Offline sim fakes sync success (see §4) | No | CLIN + QA | Clinical + A09 |
| A06-002 | **P0** | Unsafe CRDT_MERGE in HEAD; fix only in user work (see §4) | No | USER + CLIN + git | ORCH + user |
| A06-003 | P1 | No durable offline queue in production path | No | ARCH + DB-API | A07 + ORCH |
| A06-004 | P1 | PWA no offline mutation queue; `offline.html` unwired; substring gate | No | ARCH + CI + USER | A02/A03/A08/A09 |
| A06-005 | P1 | Hybrid router cloud/LAN branches empty stubs | No | ARCH | A01/A07 |
| A06-006 | P1 | NHDW LWW by string compare; batch-wide conflict status | No | CLIN + DB-API | A05/A07 |
| A06-007 | P1 | Large doc-to-code gap on sovereign offline protocol | N/A (governance) | ARCH | ORCH |
| A06-008 | P2 | Edge agent no offline result backlog; server-controlled timing | No | SEC + DB-API | A04/A08 |
| A06-009 | P2 | "Digital signature" unkeyed digest; non-constant-time compare | No | SEC | A04 |
| A06-010 | P2 | Redis-only degradation may never clear | Yes | reliability | A08 |
| A06-011 | P3 | Two unrelated `OfflineSyncEngine` classes | Conditional | API clarity | A01/A07 |
| A06-012 | P1 | Four event stacks, no authoritative store; non-durable | No | ARCH | ORCH + A07 |
| A06-013 | P1 | Outbox marks handlers `done` on failure/0 handlers | No | DB-API + CLIN | A07 + A09 |
| A06-014 | P1 | `publish()` bypasses outbox/inbox/retry/DLQ it constructs | No | DB-API | A07 |
| A06-015 | P2 | Async handlers fire-and-forget from sync publish | No | ARCH + reliability | A07/A08 |
| A06-016 | P2 | Replay orders by client timestamp string; no payload integrity | No | CLIN + SEC | A05/A09 |
| A06-017 | P2 | Retry queue never advances count; `processing` can strand | No | DB-API | A07 |
| A06-018 | P2 | `reconcile_incoming()` reports but never applies; LWW trusts client time | No | CLIN + DB-API | A05/A07 |
| A06-019 | P2 | No CRDT/Merkle implementation; vector clocks in one prototype | N/A (research) | none | ORCH (correct claims) |
| A06-020 | P2 | Fragmented idempotency; offline ops lack Idempotency-Key | No | CLIN + DB-API | A05/A07 |
| A06-021 | P3 | Outbox cleanup mixes naive/aware datetimes | Yes | none | A07/A08 |
| A06-022 | P3 | Recovery PARALLEL/BATCHED replay can violate ordering | No | DB-API | A07 |

### A07 — Backend, API & Database (20)
| ID | Sev | Title | Safe? | Approval | Proposed owner |
|---|---|---|---|---|---|
| A07-001 | P1 | `get_current_user` return type unsound; `lab_id` nullable/cross-domain | No | SEC | A04 + A07 |
| A07-002 | P2 | Validation asymmetry; phone normalized for check, stored raw | Partial | DB-API | A07 plan + A09 tests |
| A07-003 | P2 | N+1 query in pending-labs list | Yes (shape unchanged) | clean-file | A07 |
| A07-004 | P3 | ContextVars set in threadpool may not reach event loop | Yes | observability | A07 + A08 |
| A07-005 | P3 | `create_app(override_mode)` mutates global env without restore | Yes | none | A07 + A09 |
| A07-006 | P3 | Read-replica fallback silent | Yes (metric) | DB-API if header | A08 (metric) |
| A07-007 | P3 | Phantom `__all__` entry (`Appointment`) | Yes | clean-file | A07 |
| A07-008 | P1 | OpenAPI artifact empty stub, stale version 2.1.0 vs 2.5.0 | Yes (regenerate) | DB-API (version) | A07 + A09 |
| A07-009 | P2 | API versioning claimed but inconsistent; no deprecation path | No | DB-API + ARCH | A07 + A01/A08 |
| A07-010 | P2 | `/contracts/schemas/*` broken by invalid import | Yes | none | A07 |
| A07-011 | P2 | Legacy error `detail` flattened, drops `message_ar`/code | No | DB-API | A07 + A03 |
| A07-012 | P3 | Two modules both claim canonical error envelope | Conditional | DB-API | A07 |
| A07-013 | P3 | Compatibility helper unwired to any route | Conditional | DB-API | A07 |
| A07-014 | P1 | `patients.lab_id` ON DELETE CASCADE destroys data | No | DB-API + CLIN | A07 + A05 (forward migration) |
| A07-015 | P2 | 8 untracked migrations gate current head | No | USER + DB-API | ORCH + user |
| A07-016 | P2 | Several untracked migrations not idempotent | No | USER + DB-API | ORCH + user |
| A07-017 | P2 | ORM metadata drift (widened columns still narrow in models) | No | DB-API | A07 |
| A07-018 | P3 | Deprecated SQLAlchemy table-existence API (speculative) | Conditional | DB-API | A07 (verify pinned version) |
| A07-019 | P3 | PostgreSQL major version inconsistency (16 vs 17) | N/A (docs) | DB-API | ORCH |
| A07-020 | P3 | Backup/restore scripted but no automated CI verification | Conditional | CI | A08 |

### A08 — DevOps, Performance, Reliability (42)
| ID | Sev | Title | Safe? | Approval | Proposed owner |
|---|---|---|---|---|---|
| A08-R001 | **P0** | `emergency-recover.sh` destroys protected work (see §4) | Guard only | USER + ORCH | ORCH (quarantine) |
| A08-001 | P1 | Backend Docker build context mismatch → CI/nightly expected fail | Yes | CI | A08 |
| A08-002 | P1 | Python 3.12 CI vs 3.14 prod images | Yes | CI | A08 + A07 |
| A08-R002 | P1 | Blue-green trigger names nonexistent workflow | Conditional | CI + release owner | A08 + ORCH |
| A08-R003 | P1 | Blue-green failure can restore bad slot; health failure only warning | No | CI + SEC | A08 + A04 |
| A08-R004 | P1 | Canary monitor never evaluates health; promotion unconditional | No | CI + SEC | A08 + A04 |
| A08-R005 | P1 | Auto-rollback verification can never succeed; manual-only | No | CI + SEC | A08 + A04 |
| A08-R006 | P1 | Deploy/rollback swallow failures with `|| true` | No | CI + SEC | A08 + A04 |
| A08-003 | P2 | Duplicate CodeQL workflows | Yes | CI | A08 |
| A08-004 | P2 | Commercial `safety` CLI in CI violates Free First | Yes (pip-audit) | COST + SEC | A08 + A04 |
| A08-005 | P2 | Image pinning gate accepts mutable tags | Yes | CI | A08 |
| A08-006 | P2 | Legacy compose inconsistent/unhardened | No | CI | A08 |
| A08-007 | P2 | Full-stack compose: Vault dev-mode, public MinIO metrics | No | SEC + topology | A08 + A04 |
| A08-008 | P2 | Floating action tags in bundle workflow | Yes | CI | A08 |
| A08-009 | P2 | Frontend governance gates unwired; pnpm vs npm (**dup → A09-011**) | Conditional | CI + USER | A08 + user |
| A08-010 | P2 | Makefile gates non-blocking even in "strict" | Yes | CI | A08 |
| A08-011 | P2 | `preview-deploy.yml` no-op, suppresses install failures | Yes | CI | A08 |
| A08-012 | P2 | No test-coverage gate in CI (overlaps A09-007) | Conditional | CI + USER | A08 + A09 |
| A08-013 | P2 | Two Pages workflows deploy on every main push | Yes | CI | A08 |
| A08-P001 | P2 | SLO perf gate fails open, unwired | Conditional | CI | A08 |
| A08-P002 | P2 | Nightly Locust threshold cannot fail job | Yes | CI | A08 |
| A08-P003 | P2 | k8s memory limit vs worker concurrency | Conditional | infra | A08 |
| A08-P004 | P2 | Horizontal scaling can exceed PostgreSQL max_connections | No | DB-API + infra | A07/A08 |
| A08-R007 | P2 | No metrics-driven rollback | No | CI + SEC | A08 + A04 |
| A08-R008 | P2 | Three backup paths; one verified; no restore drill | Conditional | CI + data owner | A08 |
| A08-R009 | P2 | DR docs recommend paid SaaS; unverified RTO/RPO/encryption | N/A (docs) | COST + data owner | A08 + ORCH |
| A08-R010 | P2 | `make restore` advertised but missing | Yes | CI | A08 |
| A08-R011 | P2 | HA claims vs single points of failure | No | infra | A08 |
| A08-R012 | P2 | k8s `:latest` image; readiness probes liveness endpoint | Yes | CI | A08 |
| A08-014 | P3 | Node.js version drift | Yes | CI | A08 |
| A08-015 | P3 | Prometheus scrapes non-existent exporters | Yes | observability | A08 |
| A08-016 | P3 | Service/container hardening gaps | Conditional | SEC | A08 + A04 |
| A08-017 | P3 | Workflow inventory 32 vs brief's 30 | N/A (docs) | none | ORCH |
| A08-018 | P3 | Metrics-token placeholder has no ignore rule | Yes | none | A08 |
| A08-P005 | P3 | Bundle budget uncompressed + fragile asset filter | Yes | CI | A08 |
| A08-P006 | P3 | Unbounded `.all()` in list endpoints | Conditional | DB-API | A07/A08 |
| A08-P007 | P3 | Redis eviction policy differs between stacks | Yes | infra | A08 |
| A08-P008 | P3 | PgBouncer pool wait-time no observability | Yes | observability | A08 |
| A08-P009 | P3 | Perf test entry points not reusable | Yes | none | A08 |
| A08-R013 | P3 | Terraform state on commercial cloud; no versioning | No | COST + infra | A08 |
| A08-R014 | P3 | Rollback coupled to Vercel SaaS; preview no-op | No | COST + CI | A08 |
| A08-R015 | P3 | Fragmented/stale DR documentation | Yes (docs) | data owner | A08 |

### A09 — Testing & QA (15)
| ID | Sev | Title | Safe? | Approval | Proposed owner |
|---|---|---|---|---|---|
| A09-001 | P1 | Production secret-guard test is no-op (`assert True`), file USER `M` | Yes | USER + SEC | user release → A09 + A04 |
| A09-002 | P1 | `--passWithNoTests` → CI can pass with zero tests | Yes | USER + CI | user + A08 |
| A09-003 | P1 | Test workflows not triggered on integration branch | Yes | CI | A08 + ORCH |
| A09-004 | P1 | 119 migration-gate failures claimed, no raw artifact | N/A (evidence gap) | ORCH | ORCH (request artifacts) |
| A09-005 | P2 | `or True` unfalsifiable assertions (one USER file) | Yes | clean-file / USER | A09 |
| A09-006 | P2 | Intermittent cross-suite failure (order dependence) | Conditional | none | A09 |
| A09-007 | P2 | Coverage gate declared but non-functional (overlaps A08-012) | Conditional | USER + CI | user + A08 |
| A09-008 | P2 | Two E2E specs hardcode `/usr/bin/chromium` | Yes | none (A09 assignment) | A09 |
| A09-009 | P2 | E2E single-browser, single-device | Yes | CI | A09 + A08 |
| A09-010 | P2 | Axe coverage narrow; `color-contrast` disabled (**dup → A02-017**) | Yes | A02 review | A09 + A02 |
| A09-011 | P2 | Six verify gates + `check` never run in CI (**dup → A08-009**) | No | CI + USER | A08 + user |
| A09-012 | P3 | Placeholder/smoke assertions in clean tracked tests | Yes | none | A09 |
| A09-013 | P3 | Env-gated skips can mask regressions | Yes | QA process | A09 |
| A09-014 | P2 | 116 untracked test files outside committed CI coverage | N/A (user work) | USER | ORCH |
| A09-015 | P3 | Historical test counts inconsistent/unaccompanied | N/A (docs) | none | ORCH |

---

## 6. Deduplication

| Merged issue | Duplicate pair | Basis | Resulting canonical issue |
|---|---|---|---|
| DEDUP-01 | **A08-009** ↔ **A09-011** | Same root cause (frontend `verify:*` + `check` gates never invoked in CI), same evidence (`frontend-v3/package.json:14-21`, 0 workflow matches), same fix | Keep both IDs cross-referenced; counted once (P2) |
| DEDUP-02 | **A02-017** ↔ **A09-010** | Same two a11y test files with `color-contrast` disabled (`PageComponents.a11y.test.tsx`, `WorkspaceSelector.a11y.test.tsx`), overlapping fix | Keep both IDs cross-referenced; counted once (P2) |

**Strongly related but NOT merged** (distinct root cause/fix; tracked in §7/§8):
A08-012 ↔ A09-007 (coverage gate: CI-wiring vs missing provider);
A01-016 ↔ A05-006/007 (FHIR duplication vs capability overclaim vs atomicity);
A07-001 ↔ A04-014 (auth principal typing vs perm-version check);
A09-003 ↔ A08 CI trigger findings; A01-012 ↔ A08-009/A08-014 (manifest/version sprawl).

---

## 7. Cross-domain dependencies

| Dependency | Issues | Reason |
|---|---|---|
| A02 shared components before A03 pages | A02-001,013 ↔ A03-009,010,015 | Pages consume shared primitives/tokens; A02 must stabilise first |
| A09 tests depend on fixed behavior | A09-004,006,008 ↔ A02/A03/A05/A07/A08 | Regression oracles need corrected behavior; independent characterization tests may be written earlier |
| A04 SEC gate on auth issues | A04-001,002,003,005,006 ↔ A07-001, A03-005/007, A03-013 | Auth/RBAC/PHI changes need security approval |
| A05 CLIN gate on clinical issues | A05-001,002,003,006,007 ↔ A03-001,002,009,012,014; A06-001,002,006,016,018; A07-014 | Clinical logic/safety decisions |
| A07 DB-API gate on contracts/DB | A07-014,015,016 ↔ A05-003,007,008; A06-013,017,018,020; A08-P004; A03-004 | Schema/migration/contract changes forbidden without approval |
| A08 CI gate on verification | A08-009/011/012 ↔ A09-002,003,011; A01-011 | Gate wiring is CI semantics + often USER-owned files |
| P0 blockers | A02-001, A03-003, A05-001/002/007, A06-001/002, A08-R001 | Halt all related work until resolved or formally downgraded |
| USER release gate | A06-002, A08-R001, A04-002, A07-015/016, A09-001/002, A02-020, A08-009 | Files are pre-existing user work |

---

## 8. Conflicting / overlapping recommendations

| ID | Conflict | Resolution |
|---|---|---|
| CF-01 | A02-017 recommends re-enabling `color-contrast`; A09-010 notes re-enabling may expose real design defects and requests A02 sign-off | Not a true contradiction — sequencing. A02 must fix token contrast (A02-002/015) **before** contrast rule is re-enabled. Wave C order: A02 first, then A09. |
| CF-02 | A08-004 wants to replace commercial `safety` with free `pip-audit`; A08's own scope request defers to A04 | Align: A04 owns security-tool approval; both agree on Free First. No conflict, joint ownership. |
| CF-03 | A08-009 attributes gate unwiring to `pnpm` vs `npm`; A09-011 attributes it to gates simply never being wired | Both true and complementary — fix = change script manager AND wire CI. Merged under DEDUP-01. |
| CF-04 | A01-016 says consolidate to one FHIR implementation (ADR-011); A05 findings require preserving clinical exchange behavior during any change | Consolidation is ARCH/CLIN gated; no action in this program. A05 review first. |
| CF-05 | A04 report says "no committed live secret"; A04-010 flags a real-looking key in gitignored `.env` | Not contradictory: tracked vs untracked. ORCH to verify `.gitignore` coverage (A04-010). |
| CF-06 | Program brief claims "30 workflows"; A08 verified 32; A08-017 reports the mismatch | Use verified count (32). Historical figure stale (consistent with CR-003 pattern). |

---

## 9. Approval categorization (deduplicated, 175 issues)

| Category | Count | Description |
|---|---|---|
| **Safe independent** (no behavioral/scope approval needed; clean-file check still required) | ~24 | A02-002/004/006/007(partial)/016/019/021; A03-010/011/015/016; A07-003/005/007/010; A08-003/005/008/010/011/013/018/P002/R010; A09-005/008/012/013 (subject to clean-file) |
| **Architectural approval** | ~30 | All A01 structural issues; A06-003/004/005/007/012/014; A01-016; dedup gating |
| **Clinical approval** | ~22 | A03-001/002/003/009/012/014; A05 all; A06-001/002/006/016/018/020; A07-014 |
| **Security approval** | ~24 | A04 all P1/P2 + several P3; A03-005/007/013; A06-009; A08-R003/004/005/006/007/R007; A07-001 |
| **Database/API approval** | ~35 | A07 most; A05-003/007/008; A06-013/017/018/020/022; A03-004/006/008; A08-P004/P006 |
| **CI/DevOps approval** | ~26 | A08 CI findings; A09-002/003/011; A01-011; A02-003/005 |
| **USER release required** | ~14 | A06-002, A08-R001, A04-002, A07-015/016, A09-001/002/014, A02-020, A08-009, A03-001, plus user-modified clinical files |
| **Informational / no-fix / research** | ~10 | A04-010, A05-005, A06-019, A08-017/R009, A09-004/014/015, A01-014(P3 doc) |

> Categories overlap (one issue may need USER + SEC + CLIN). Counts are indicative
> by primary gate; exact per-issue gates are in §5. No issue is simultaneously
> "safe independent" and blocked by a P0.

---

## 10. Prioritized remediation backlog

**Ordering:** P0 halt items first (but all require approval/release), then P1 security,
then P1 clinical, then P1 backend/architecture, then P2/P3 safe-independent candidates
that become eligible once isolation is resolved. Nothing below is authorized yet.

| Rank | Issue(s) | Severity | Gate | Rationale |
|---|---|---|---|---|
| 1 | A08-R001 | P0 | USER + ORCH | Quarantine `emergency-recover.sh` (guard-only fix; DO NOT RUN). Highest destructive risk. |
| 2 | A06-002 | P0 | USER + CLIN | Resolve committed unsafe merge; needs user release of uncommitted fix. |
| 3 | A05-007, A05-001, A05-002 | P0 | CLIN + DB-API | Clinical record integrity, critical-result delivery, QC gate. |
| 4 | A03-003 | P0 | CLIN + SEC | Pharmacy substitution same-click approval on real API path. |
| 5 | A06-001 | P0 | CLIN + QA | Offline sync false-success claim. |
| 6 | A02-001 | P0 | design + A03 | Split tokens; unblocks the entire visual remediation batch. |
| 7 | A04-001,002,003 | P1 | SEC | Half-wired NIAM security controls (step-up, logout, token binding). |
| 8 | A07-001, A07-014 | P1 | SEC / DB-API | Tenant-type soundness and destructive cascade. |
| 9 | A07-008 | P1 | DB-API | Empty OpenAPI artifact breaks generated clients. |
| 10 | A03 P1 clinical UI batch | P1 | CLIN | Synthetic-as-live, fabricated identifiers, FHIR Explorer, data-quality mutation. |
| 11 | A08-001,002,R002–R006 | P1 | CI + SEC | Pipeline cannot work correctly; deploy/rollback unsafe. |
| 12 | A05-003/004/006, A01-001..004 | P1 | CLIN / ARCH | Correction semantics, AI eval honesty, capability overclaim, duplicate app trees. |
| 13 | DEDUP-01 (A08-009/A09-011), A09-002/003 | P2 | CI + USER | Verification gates unwired; CI can pass with zero tests. |
| 14 | Remaining P2 (per §5) | P2 | varied | Batches by gate after P0/P1 cleared. |
| 15 | Safe-independent P3 (per §9) | P3 | clean-file check | Elective housekeeping only after isolation resolved. |

---

## 11. Wave C authorization — BLOCKED (exact blockers)

Wave C **does not start**. All 175 issues are `Discovered`, `Fixed = 0`, `Verified = 0`.

| # | Blocker | Evidence |
|---|---|---|
| 1 | **Working tree insufficiently isolated** (explicit instruction) | 378+ changed paths of user work; remediation in-place risks corruption |
| 2 | **8 open P0 findings** | §4 — each halts its component |
| 3 | **Clean-clone isolation incomplete** | `/tmp/opencode/gula-isolation-eval` from HEAD `2206654d` is clean but lacks all user work and `node_modules`; cannot be trusted as sole base |
| 4 | **USER release not given** for protected files | A06-002 fix, A08-R001, A04-002, untracked migrations, USER-owned manifests |
| 5 | **No independent approvals** for SEC/CLIN/DB-API/ARCH changes | §9 categorization is proposed, not approved |
| 6 | **No gate baseline** | A09: 0 machine-readable test artifacts; all historical pass/fail = CLAIM-UNVERIFIED |

**Expected verification gates when Wave C is eventually authorized** (from discovered scripts,
run package-locally; never assume across projects):
`frontend-v3/`: `pnpm typecheck`, `pnpm test`, `pnpm verify:unification`, `pnpm verify:contracts`,
`pnpm verify:integration-boundary`, `pnpm generate:data-source-inventory`, `pnpm verify:data-sources`,
`pnpm generate:route-gate`, `pnpm verify:audit-artifacts`, `pnpm build`, `pnpm check:bundle`,
`pnpm test:e2e`, `pnpm check`. Backend: `pytest` (335 test files), `make ci`, migration graph
integrity (static only — **no DB execution**). Gate results to be recorded with exit codes in
`INTEGRATION_LOG.md`.

---

## 12. Status counts (actual register states)

| Metric | Count |
|---|---|
| Discovered | 175 |
| Fixed | 0 |
| Verified | 0 |
| Blocked (P0 halt or USER release) | 8 P0 + ~14 USER-gated (overlap) |
| Approval Required (SEC/CLIN/DB-API/ARCH/CI) | ~140 |
| Safe Independent (eligible pending isolation+clean-file) | ~24 |

**Completion percentages:** 0% fixed, 0% verified. These are computed from actual register
states; no estimated progress is claimed.

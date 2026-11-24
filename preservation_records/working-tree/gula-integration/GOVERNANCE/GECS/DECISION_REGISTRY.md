# GECS — DECISION REGISTRY

**Purpose (canonical):** every decision the programme depends on, with its **unchanged** approval
status. This file is canonical for *decision status*; option analysis lives in
`GOVERNANCE/ADR_DECISION_REQUEST.md`, `GOVERNANCE/ARCHITECTURE_DECISION_PACKAGE_W1.md` and
`GOVERNANCE/FINAL_DECISION.md` (referenced, never copied).
**Created:** 2026-11-17 · **Rule:** only explicitly named authorities may approve. **A recommendation,
an analysis task, or a user saying "continue general analysis" is never approval.**

Status vocabulary for decisions: `PENDING_APPROVAL` (nothing implemented) · `DECIDED` (recorded,
implementation pending) · `VERIFIED` (decided **and** evidenced) · `SUPERSEDED`.

## A. The four W1 decisions — ALL NOT APPROVED (approval boundary)

| ID | Decision | Status | Options considered | Recommended option | Evidence | Decision authority | Required approvals | Implementation dependencies | Reversibility | Acceptance criteria |
|---|---|---|---|---|---|---|---|---|---|---|
| D-001 | **ADR-A** — migration strategy for the unmigrated ORM tables | **APPROVED — project owner, 2026-11-17** (was PENDING_APPROVAL) | A incremental-by-bounded-context; A1+A3 (original); A2 single bulk baseline; A4 deploy-time `create_all()`; B centralised baseline; C hybrid | **Option A** (incremental per bounded context) + shipping/non-shipping register; A2 and A4 rejected (A4 empirically rejected by the 872/0 control); C only as an explicitly accepted emergency subset | package §4, §A3, §A4; E-001…E-016; E-004 (control) | Program Director / Architecture | written approval of ADR-A row in `ADR_DECISION_REQUEST.md` | D-003 (NR-011) first; D-002 for duplicate/unresolved tables | high — each context revision independently revertible; feature flags revertible | 8 numbered criteria in package §4.4 (fresh-clone upgrade, strict subset green per wave, register enforced, fingerprint delta = approved migrations only, no test edits, repeatability, downgrade per revision, no renumbering) |
| D-002 | **ADR-B** — ownership of `facilities` / `organizations` / `national_facilities` (+ `insurance_coverages`, duplicate models) | **APPROVED — project owner, 2026-11-17** (was PENDING_APPROVAL) | B1 single `Base` owner + downgrade exclusion; B1 corrected (measured: all three are migration-created, never dropped); B2/B3 rejected; B4 master-data service; B5 federated | **B1 corrected**: single authoritative owner + asserted downgrade exclusion; retire/re-point 28-col duplicate `Facility`; extend ruling to 7 `duplicate` + 2 `unresolved_ownership` tables before their migration | package §5, §A5; E-014 (6-col vs 28-col); E-024 §6 (4 residuals) | Program Director / Architecture | ADR-B row approval + Database owner sign-off (FINAL_DECISION §9) | data-provenance survey for long-lived deployments | high for the record; **irreversible if a table is dropped** — drop prohibited without new ADR | 7 numbered criteria in package §5.4 (owner recorded, exclusion asserted, no drop, loser retired with provenance, `org_type` drift resolved, tests assert single owner, criterion 5 sub-condition (a) closed) |
| D-003 | **NR-011** — Alembic metadata completeness fix | **APPROVED — project owner, 2026-11-17** (was PENDING_APPROVAL) | N1 two-part fix (register 7 bases + national domain **and** merged `MetaData`); N2 import-only (rejected by probe B — error merely moves); N3 include_object strategy; N4 external metadata mirror | **N1 two-part fix**, implemented only in `backend/migrations/env.py` + a regression test, **zero DDL** | E-017 (probes A/B/C exit 1/1/1; C = real 284-table diff); package §A6 | Architecture | ADR/NR-011 approval before any `env.py` edit | none (first step of the chain) | single-file revert; no DB object created → no data rollback needed | 7 numbered criteria in package §A6.7 (alembic check no FK error, 17 bases registered, probe-C reproduced, fingerprint unchanged, 70 removal findings triaged, single head, no new import-time secret) |
| D-004 | **Rollback policy** | **APPROVED — project owner, 2026-11-17** (was PENDING_APPROVAL) | snapshot restore; `downgrade base` + `upgrade head`; partial downgrade to a revision; CI exit-code steps as proof | **snapshot restore (once drilled) or `downgrade base` + `upgrade head`**; partial downgrade **prohibited**; no RPO/RTO claim without measurement | E-024 §5–§6 (partial unsafe; full teardown verified 25 s/81 s, 433 tables, identical fingerprint); package §A7 | Database / Operations owner | recorded runbook decision + Database owner sign-off | D-004 needed before W-034 drill and W-039 rehearsal | full path verified reversible; partial path measured unsafe | 5 numbered criteria in package §7.3; drill evidence before any recovery claim |

**Boundary statement:** preparing this table is not approval. D-001…D-004 were approved only by the
explicit written record below (2026-11-17). **D-005…D-012 (ADR-C…ADR-J), D-020 and D-021 remain
PENDING — this approval does not extend to them.** `FINAL_DECISION.md` stays **HOLD**.

### §A1 — Approval record (2026-11-17, project owner)

**Approval source:** explicit owner approval in the OpenCode task *"GULA — GECS Approval Activation
& Controlled Execution"* §1 (this task) — not inferred, not delegated to the security or clinical
reviewer. **Approval date:** 2026-11-17 · **Branch at approval:** `integration/gula-unification-v1`
@ `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0` · Recorded in
`ARCHITECTURE_DECISION_PACKAGE_W1.md` §A11 and in this registry.

| ID / ADR ref | Exact approved decision | Scope | Constraints | Risks accepted | Required evidence (before closure) | Related work | Reversal conditions |
|---|---|---|---|---|---|---|---|
| **D-001 / ADR-A** | Incremental migration by **bounded context (Option A)** + explicit shipping/non-shipping register; A2 bulk baseline and A4 `create_all()` rejected; hybrid C only as an explicitly accepted emergency subset | future migration revisions for the 340 absent tables + 82/664 drift, in 5 waves | register must exist and be CI-enforceable; no test edits to obtain passes; no renumbering; per-revision downgrade; zero DDL outside an approved revision | partial waves leave mixed schema states; register omissions → ungated surfaces | package §4.4 criteria 1–8; fresh-clone upgrade PASS; per-wave strict subset green; fingerprint delta = approved migrations only | W-025, W-026…W-030, W-036; F-001, F-002, F-019 | new evidence materially changing option risk/reversibility; any destructive autogenerate finding triaged as unaccepted |
| **D-002 / ADR-B** | **B1 corrected**: single authoritative `Base` owner + asserted downgrade exclusion for `facilities`/`organizations`/`national_facilities`; retire/re-point the 28-col duplicate `Facility`; extend ruling to 7 duplicate + 2 unresolved tables **before** their migration | ownership of reference/master tables; documentation + enforcing test | **no table may be dropped** without a new ADR; archive/retire with provenance; data-provenance survey for long-lived deployments | wrong owner → runtime failure on 22 missing columns; drop = irreversible data loss | package §5.4 criteria 1–7; owner recorded; exclusion asserted; tests assert single owner; criterion 5 sub-condition (a) | W-038, W-030; F-013, F-014, F-016 | provenance survey showing a different authoritative source; any evidence of a pre-existing external consumer |
| **D-003 / NR-011** | **N1 two-part fix**: register the 7 omitted bases + national domain models **and** deterministically merge into one `MetaData`; import-only (N2) rejected by probe B | **`backend/migrations/env.py` only** + regression test | zero DDL; zero DB change; fingerprint unchanged `3b2d9499…`; single head; no new import-time secret; no circular imports; if a second file becomes essential → stop and request separate approval | metadata merge could alter autogenerate scope → 70 removal findings must be triaged, never auto-applied | 7 criteria package §A6.7; `alembic check` completes without `NoReferencedTableError`; regression test proves discovery of all registered bases | W-024; F-010, F-002 | discovery regression; autogenerate proposes unaccepted drops; any DDL or migration-history change observed |
| **D-004 / Rollback** | **Snapshot restore (once drilled)** or `downgrade base` + `upgrade head`; **partial downgrade prohibited**; no RPO/RTO claim without measurement | rollback runbook + CI assertions + recovery drills | never treat exit-0 as state equivalence; no published RPO/RTO number until measured; drills only on disposable clones | false sense of recovery readiness until drilled | package §7.3 criteria; one documented drill with table-count/fingerprint comparison; runbook records the prohibition | W-034, W-037, W-039; F-012, F-017, F-018 | drill failure; new evidence that the full-teardown path is unsafe |

**Not approved by this record:** D-020 (human security review), D-021 (clinical safety sign-off),
ADR-C…ADR-J, Platform-Core restructuring, any architecture change outside the four decisions,
any irreversible action. **If actual evidence conflicts with any approved decision: stop that
part, record the conflict — do not force the decision.**

## B. Imported architecture decisions ADR-C…ADR-J (canonical: `ADR_DECISION_REQUEST.md` — all PENDING, unchanged)

| ID | Decision | Status | Recommended option | Evidence | Decision authority | Required approvals | Implementation dependencies | Reversibility | Acceptance criteria |
|---|---|---|---|---|---|---|---|---|---|
| D-005 | ADR-C — `care_continuum`: cross-cutting host vs decomposed services | **PENDING_APPROVAL** | C1 (host) | `ADR_DECISION_REQUEST.md` §ADR-C | Program Director / Architecture | contract 07 owner | D-001 (tables must exist) | medium | contract 07 satisfied; no cross-domain import cycle |
| D-006 | ADR-D — audit coverage / replacement for blanket `system:admin` | **PENDING_APPROVAL** | D2 + D1 | `ADR_DECISION_REQUEST.md` §ADR-D | Security lead | conditions 7, 10 owners | W-033 security review | medium | no blanket admin attribution; audit chain tests green |
| D-007 | ADR-E — public token/phone access model | **PENDING_APPROVAL** | E1 | `ADR_DECISION_REQUEST.md` §ADR-E | Program Director | contract 04 owner | D-012 (offline) | medium | contract 04 + J4 satisfied |
| D-008 | ADR-F — lab duplication (`lab_service` vs inline `routes/labs.py`) | **PENDING_APPROVAL** | F1 per route | `ADR_DECISION_REQUEST.md` §ADR-F | Architecture | condition 9 owner | W-040 | medium — one route at a time | condition 9; OpenAPI unchanged per route |
| D-009 | ADR-G — insurance provisioning (5 live ops vs 84 unserved endpoints) | **PENDING_APPROVAL** | G2 (or G1 after contract) | `ADR_DECISION_REQUEST.md` §ADR-G | Program Director | contracts 05/06 owners | D-011 | medium | contracts 05/06 satisfied |
| D-010 | ADR-H — Shared Core boundary | **PENDING_APPROVAL** | H1 (CI-enforced) | `ADR_DECISION_REQUEST.md` §ADR-H | Architecture | all contracts | architecture gate wiring | high | CI enforces the boundary; no new reimplementation |
| D-011 | ADR-I — register or archive the unserved insurance API | **PENDING_APPROVAL** | I1 (archive) | `ADR_DECISION_REQUEST.md` §ADR-I | Architecture | follows ADR-G | D-009 | high — archive-first, reversible by move | unserved endpoints either served or archived with provenance |
| D-012 | ADR-J — offline durability (durable queue vs in-memory) | **PENDING_APPROVAL** | J1 (durable queue) | `ADR_DECISION_REQUEST.md` §ADR-J; F-028 (in-memory confirmed) | Architecture | offline-first claim owner | D-007 | medium | restart loses no queued work; or feature verifiably gated off |

## C. Programme decisions already taken (imported with original status — never re-decided)

| ID | Decision | Status | Evidence | Decision authority | Notes / dependencies | Acceptance criteria |
|---|---|---|---|---|---|---|
| D-013 | CR-1 — keep local `backend/app/workflows`; archive remote broken runtime | **VERIFIED** (DECIDED + EXECUTED, uncommitted) | E-025; `test_identity_workflows_canonical.py` 10/10; DCR §9.8 | Program Director | commit blocked by B-006 | single mount, auth 401, DB bridge — met |
| D-014 | CR-2 — `frontend-v3` authoritative; `apps/*` secondary/demo | **VERIFIED** (DECIDED) | E-035; `FRONTEND_INTEGRATION_REPORT.md` | Program Director | WEB-SURFACE resolved with it | frontend gates exit 0 — met |
| D-015 | NR-003 — pharmacy PK identity fix (`Integer` → `String(26)` alignment) | **VERIFIED** (DECIDED + IMPLEMENTED, uncommitted) | DCR §9; fresh PG16 through `20260815_0023` | Migration Owner | needs commit review (B-006) | fresh upgrade PASS — met |
| D-016 | NR-009 — conditional FK for `hospital_operation_theaters` | **VERIFIED** (DECIDED + IMPLEMENTED, uncommitted) | DCR §9.4; fresh `upgrade head` PASS | Migration Owner | needs commit review | 433 tables, head `20261114_0006` — met |
| D-017 | NR-010 — six downgrade defects across five revisions repaired | **VERIFIED** (AUTHORISED + FIXED, uncommitted) | E-038; DCR §9.5 | DBA | NOT a clean-schema certification; 3 residual tables → D-002 | round trip PASS — met |
| D-018 | W1 gate method — validate only against a disposable migration-built clone with byte-identical test copies outside the repo; **no test/fixture/migration/production edit to obtain a pass** | **VERIFIED** (DECIDED + EXECUTED) | E-018 §2, E-016 manifest, E-015 fingerprint | QA Lead / Program Director | result FAILED (W-017) but the method decision stands; never rerun without trigger | zero DDL proven by fingerprint — met |
| D-019 | Release decision — **HOLD** (`FINAL_DECISION.md`) | **VERIFIED** (recorded, unchanged) | E-022 md5 `effdfeaf…`, HOLD at lines 13 and 361 | Program Director | criteria 5, 7, 8, 9 NOT MET | HOLD intact — met (re-verified 2026-11-17) |
| D-020 | Security verdict — **reviewed, NOT CERTIFIED** (S-01…S-12 remediated in tree, uncommitted/unreviewed; S-13 found in independent pass) | **PENDING_APPROVAL** | E-027, E-029, E-022 §9 | Security lead + Program Director | W-033; criterion 7 NOT MET | human sign-off on report **and** remediation diff |
| D-021 | Clinical safety posture — `test_clinical_safety` 33/33 PASS, `test_patient_card` 15/15, `test_clinical_command_guard_p0` 5/5 under strict schema; **but 4 P0 workflow modules fail and referrals/`care_continuum` are untested** → no clinical safety certification exists | **PENDING_APPROVAL — no approval record exists** | E-024 §13.4; F-003, F-007 | Clinical Safety Owner (risk owner per package §8 X-09) | certification impossible until F-003/F-007 closed | all P0 workflow modules green + coverage holes filled |
| D-022 | GECS adoption — lightweight Markdown-only execution control under `GOVERNANCE/GECS/` (10 files, no database/dashboard/dependency) | **VERIFIED** (DECIDED + EXECUTED, documentation-only) | `GECS_CHECKPOINT.md` (this phase) | this phase's mandate | category-A change only (`CHANGE_CONTROL.md` CC-001) | registries created + read-only audit PASS |

**Counts:** 23 decisions — 4 W1 (**APPROVED by project owner 2026-11-17**, §A1 record), 8 ADR-C…J
(all PENDING — unchanged), 10 programme (PENDING_APPROVAL 2, VERIFIED 8), 1 executive authorization
(**D-023 DECIDED 2026-11-17**, §E, CC-007). D-020 and D-021 remain PENDING_APPROVAL; the D-023
authorization grants engineering work only and changed neither of them nor the HOLD.

---

## D. Phase 5 evidence refresh for D-020 / D-021 (additive — status unchanged, CC-006)

Evidence lists only. **Neither decision is closed, upgraded or attributed to a reviewer.**
Authentication is **not** authorization: passing an `is_authenticated` check does not establish a
authorization decision. Test passes below are isolated synthetic results (E-046 205, E-047 291),
not runtime, migration-schema, security-sign-off or clinical-certification evidence.

| Required check | D-020 evidence now indexed (security) | D-021 evidence now indexed (clinical safety) | Gap that keeps both PENDING |
|---|---|---|---|
| Authorization | E-027/E-029/E-033 (route walk 2,133/2,064/69, residuals R-01…R-11); E-047 `test_ai_platform_authorization` 4, governance audit 6, national governance 19, NIAM registry 14, runtime isolation 8 | E-046 `test_lims_quality_authorization` 3; E-050 workflow auth paths | Human security review/sign-off absent (B-005); no clinical-safety approval record exists |
| Tenant isolation | E-046 `test_tenant_isolation_matrix` 21, `test_lims_tenant_isolation` 5, `test_tenants` (kernel) | E-048/050 workflow isolation on synthetic harness only | Isolation on the **migration-built schema** untested (F-027/B-019); `tenant_id` semantics undecided |
| Patient data protection | E-047 NIAM registry authorization 14; E-027 redaction; Phase 3 used synthetic data only — no patient data introduced | F-067 (MDM matcher/merge unverified); inventory §9.1 audit gaps | No production-like data rehearsal (B-017); D-021 coverage holes F-003/F-007 open |
| Audit completeness | E-047 `test_governance_audit_authorization` 6, `test_national_governance_authorization` 19; E-046 idempotency 11 | Inventory §9.1 — 7 services without immutable audit writes; ENG-C07 audit engine | Append-only trigger behavior on migrated schema unverified (F-008); fixture leak (F-005) unpatched |
| AI output safety | E-047 AI platform authorization 4; E-046 `test_ai_guardrails` 27; E-047 `test_ai_evaluation` 8 | E-047 `test_ai_integration` 22 (CDS cases) — synthetic; F-068 national CDS 9 permissive fail-open paths | No clinical-safety sign-off; F-068 unresolved; no fail-safe decision recorded |
| Human override | E-046/047 AI sandbox approval/guardrail flow tests; E-027 kill-switch evidence (9/9) | E-050 national workflow unit tests (9) only | No clinical override procedure or evidence; workflow P0 modules still fail strict (F-003) |
| Fail-safe behavior | E-046 `tests/kernel/test_circuit_breaker` 4, `test_runtime_isolation` 8; E-027 kill-switch fail-closed 9/9 | F-068 (permissive exceptions), F-069 (`CRDT_MERGE` first-wins), F-012 (unsafe partial downgrade) | Fail-safe semantics undecided for CDS and offline conflict resolution; rollback still unsafe |

**Status line (unchanged):** D-020 = **PENDING_APPROVAL** — Security lead + Program Director;
D-021 = **PENDING_APPROVAL — no approval record exists** — Clinical Safety Owner.
New supporting findings: F-066…F-072 (detail in `GOVERNANCE/AUTONOMOUS_ENGINES_FINDINGS.md`).
This refresh records evidence and gaps; it does **not** certify either decision, fix any finding,
close a blocker, or lift the HOLD in `FINAL_DECISION.md`.

---

## E. D-023 — Executive authorization for remediation & stabilization (additive — CC-007)

**This decision records an EXECUTION MANDATE, not a release or clinical/security certification.**
It does not close, upgrade or attribute D-020 or D-021 to any reviewer.

| Field | Record |
|---|---|
| ID | **D-023** (executive authorization; independent of D-001…D-022) |
| Decision | Project owner granted **full executive delegation** for post-GECS remediation & stabilization (task *"GULA — NATIONAL PLATFORM STABILIZATION & AUTONOMOUS CAPABILITY REMEDIATION"*, 2026-11-17), adopting F-066…F-072 for treatment. Branch at authorization `integration/gula-unification-v1` @ `2827c1ff…`. Baseline checkpoint: `GECS_CHECKPOINT.md` §9. |
| Status | **DECIDED — execution COMPLETE**: all 15 phases A–O delivered (W-049…W-063). A–G + J/K VERIFIED with independent evidence E-053…E-061 (194 synthetic tests / 0 failed; 3 real defects FIXED); H/I/L/M/N assessments delivered (PARTIAL / BLOCKED). Final report `NATIONAL_PLATFORM_STABILIZATION_REPORT.md` maps all 17 acceptance criteria to evidence; final integrity PASS. This decision authorizes **engineering evidence only** — D-020/D-021 still PENDING and `FINAL_DECISION.md` remains HOLD. |
| Decision authority | Project owner (explicit written delegation). Source quoted in `GECS_CHECKPOINT.md` §9.1. |
| Tasks authorized | F-066 rules/policy/expression tests; F-067 MDM + patient matching fix; F-068 conservative documented CDS fail-safe; F-069 reliable/tested `CRDT_MERGE` replacement or honest alternative; F-070 Lab Device Gateway fix+tests; F-072 Certification engine tests; proven security fixes; rules/policy, engine integration/de-dup, 18-service interlink, 7 patient journeys, reliability/performance, backup/DR, schema/migration readiness; new files/tests/helpers where necessary. |
| Boundaries (owner §0.2/§22) | No bypass of clinical safety; no patient-data risk; no disabling Authorization / Tenant Isolation / Audit; no real patient data in tests; no hidden failing tests; no unproven production readiness; no irreversible operations; no undocumented out-of-scope change. Conservative fail-safe default where a specialist clinical decision is needed, with human escalation and no hidden failure. |
| Conservative clinical policy (owner §0.2/§4) | On CDS evaluation failure: use `UNAVAILABLE`/`INDETERMINATE`; stop the affected recommendation; preserve original data; show a clear message to the specialist; write an Audit event; do NOT block emergency care; no independent diagnosis or treatment change without an approved path; new clinical behavior remains disabled by default until documented and reviewed. |
| Rollback policy (owner §19 / D-004) | Each change limited, documented, testable, reversible, contract-compatible, regression-tested. Before each set: checkpoint + diff + affected files + impact + rollback method. On failure: do not hide it; revert safely if possible; retain evidence; record a Finding; move to the next independent task. No partial downgrade; no destructive git; no `alembic stamp`; no DDL on operational DB. |
| Required tests | MDM synthetic matrix (identical/different names, order/spelling/Arabic-EN/typos/missing/DOB/phone/conflicting/multi-source/uncertain/unauthorized merge/unmerge); CDS valid/invalid/missing/type/value/dependency/timeout/partial/malformed/override/audit/fail-safe/emergency; offline two-node/multi-node/out-of-order/duplicate/partition/concurrent/reconnect/replay/crash/idempotency/conflict/convergence/no-loss; lab gateway synthetic ASTM/HL7/duplicate/sequence/mapping/invalid/critical/retry; rules/policy precedence/invalid/circular/conflict/version/audit; certification criteria/expiry/renewal/revocation/role-separation. No skip/xfail to hide failure; no full strict-suite rerun without documented trigger; historical numbers E-001 `753/119`, E-003 `872/0`, control `750/122` retained. |
| Required evidence | Per-remediation record: root cause · fix · tests (before/after) · risks · rollback · E-ID log · status (VERIFIED/PARTIAL/BLOCKED/FAILED/NOT VERIFIED). Unique F/E/W IDs; no duplicate Finding; no VERIFIED without evidence. Final `GOVERNANCE/NATIONAL_PLATFORM_STABILIZATION_REPORT.md`. |
| Independent professional responsibilities (NOT replaced by owner approval) | **D-020** human security review + Program Director sign-off (B-005/W-033); **D-021** Clinical Safety Owner sign-off (F-003/F-007 coverage holes); national release still requires met release criteria, a professional security review and clinical testing. Owner approval authorizes engineering work only; it is **not** clinical certification, security certification, or production readiness. |
| Acceptance boundary | Owner §20 criteria are engineering evidence, **not** a safety/production claim. Automated test success alone does not prove clinical safety or production readiness. `FINAL_DECISION.md` remains **HOLD** until all real release criteria are met. |

---

## F. CC-010 post-stabilization completion program — NO new decision/approval (additive, 2026-11-17)

**No D-ID is created by CC-010.** This section records that the post-stabilization national-completion
program was an **owner engineering mandate** (category A + narrow B) and **did not** decide, approve,
reopen or change any decision. It is an accountability note, not a decision record.

- **Decisions untouched:** D-001…D-004 (APPROVED), D-005…D-012 (ADR-C…ADR-J, PENDING), D-013…D-022,
  D-023 (DECIDED — execution COMPLETE), **D-020 and D-021 still `PENDING_APPROVAL`**. No decision
  status changed; no approval inferred from the completion report.
- **Authority boundary reaffirmed:** the owner's engineering authorization covers the reference-only
  capability registry, ownership/integration/test matrices and GECS/report documentation. It is
  **not** a human security review (D-020/B-005/W-033), **not** a Clinical Safety Owner sign-off
  (D-021/F-003/F-007), **not** an ADR-C…ADR-J approval, and **not** a release decision.
- **New finding only:** F-085 (unregistered `DocIntelBase`/`InsBase`, E-063) is **OPEN** and needs
  category-D/D-001 wave treatment; **no** approval to register the bases was granted here and the
  `backend/migrations/env.py` NR-011 delta stays `+49/-0`.
- **Release position:** `FINAL_DECISION.md` **HOLD** unchanged; W-017 strict gate **FAILED 119/872**
  (E-001) unchanged; ENG-A12 dormant; ENG-B09 unmounted; 0 commits. **HOLD must not become GO on
  the strength of `NATIONAL_HEALTH_PLATFORM_COMPLETION_REPORT.md`.**

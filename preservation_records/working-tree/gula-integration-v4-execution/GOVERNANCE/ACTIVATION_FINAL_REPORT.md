# GECS APPROVAL ACTIVATION — FINAL REPORT (Phases 0–8)

**Repository:** `/home/samertts/workspace/projects/gula-integration`
**Branch / HEAD:** `integration/gula-unification-v1` @ `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0` (unchanged)
**Date:** 2026-11-17 · **Category:** A (documentation-only, append-only) · **Records:** CC-005 / CC-006
**Verdict of `GOVERNANCE/FINAL_DECISION.md`:** **HOLD — do not release** (md5 `effdfeaf10234678d83b2668c4489552`, lines 13 and 361, unchanged).
**D-020 (security):** PENDING_APPROVAL. **D-021 (clinical safety):** PENDING_APPROVAL — no approval record exists.
**Commits / pushes / merges / PRs / deploys:** **none**. **Code, migration, test, fixture, conftest, DB:** **unchanged**.

---

## 1. What was authorized and what was actually done

The project owner approved D-001 (ADR-A), D-002 (ADR-B), D-003 (NR-011) and D-004 (rollback) on
2026-11-17, recorded in `DECISION_REGISTRY.md` §A1, package §A11/§A11.1 and `ACTIVATION_BASELINE.md` §6.
That approval is limited to those four decisions; it does **not** approve D-020, D-021,
ADR-C…ADR-J, code changes other than the narrowly scoped NR-011 `env.py` fix, or release.

| Phase | Work | Status |
|---|---|---|
| 0 | Integrity snapshot (HEAD, branch, git delta, md5s, HOLD) | VERIFIED — `GECS_CHECKPOINT.md` §1–§4 |
| 1 | Record D-001…D-004 approvals; clear B-001…B-004 with rows retained | EXECUTED (CC-003); G-01 MET |
| 2 | NR-011 metadata discovery (`env.py` +49 lines, 1 new test file) | EXECUTED (CC-004) — 10/10 criteria MET; E-041…E-045 |
| 3 | Bounded autonomous-engine audit + isolated synthetic verification | EXECUTED (CC-005) — 5 artifacts; E-046…E-052 |
| 4 | Additive 18-service / J1–J7 re-verification | EXECUTED (CC-006) — no verdict upgraded |
| 5 | D-020 / D-021 evidence-only refresh | EXECUTED — both remain PENDING |
| 6 | Targeted tests only (7 bounded batches, existing tests) | EXECUTED — 740 passed / 0 failed |
| 7 | Full GECS registry / count / checkpoint sync | EXECUTED — 72 findings / 52 evidence / 48 work / 22 decisions |
| 8 | This final report | EXECUTED — HOLD unchanged |

## 2. Autonomous engines — found, tested, effective, disabled, unverifiable

**39 engines inventoried** (A workflow/rules 12 · B AI/FHIR/data 12 · C security/offline 9 ·
D lab/ops 6) in `GOVERNANCE/AUTONOMOUS_ENGINES_INVENTORY.md`.

| Classification | Count | Meaning in this audit |
|---|---:|---|
| `INTEGRATION_VERIFIED` | 9 | Isolated synthetic TestClient / DB-fixture tests passed here (E-046/047/052) — **not** runtime or production |
| `UNIT_VERIFIED` | 15 | Isolated synthetic unit tests passed here, incl. four engines promoted by E-052 (A09, A11, B12, D03) |
| `PARTIAL_VERIFIED` | 2 | ENG-A01 workflow (E-048/050) and ENG-C05 offline conflict (E-046) — only named paths exercised |
| `SOURCE_PRESENT` | 11 | Source and entry points read; **no executed test** for that component |
| `DORMANT` | 1 | ENG-A12 generated `capabilities/workflow_engine` scaffold — zero external references, trivial tests (F-071) |
| `UNVERIFIABLE` | 1 | ENG-B09 national CDS engine — permissive fail-open paths, no suite, route unmounted (F-068) |
| `RUNTIME_VERIFIED` | **0** | No booted-app run was performed or authorized |
| `PRODUCTION_VERIFIED` | **0** | No production evidence exists |

**"Effective" — precise statement.** 24 engines have *passing isolated synthetic evidence* in this
audit (9 integration + 15 unit). This is **not** a claim that they are runtime-effective,
migration-compatible, clinically safe or production-ready. The strict W1 gate remains FAILED
(119/872, E-001); the 740 targeted passes are a **different corpus** on a SQLite harness.

**Disabled / unverifiable / not activated:** ENG-A12 (dormant scaffold, never wire it), ENG-B09
(national CDS — do not enable, do not refactor; clinical decision pending D-021), ENG-A07/A08/A10
(rules/policy/expression — wired but untested), ENG-B07 (MDM), ENG-B08 (streaming), ENG-B11 (search),
ENG-C01/C08/C09 (rate limiter / device gateway / national security rules), ENG-D06 (certification).

**Verification detail:** `AUTONOMOUS_ENGINES_VERIFICATION.md` (per-engine mapping + 8-dimension
matrix), `AUTONOMOUS_ENGINES_DEPENDENCY_MAP.md` (entry points, consumers, blast radius),
`AUTONOMOUS_ENGINES_FINDINGS.md` and `AUTONOMOUS_ENGINES_REMEDIATION_PLAN.md`.

## 3. Repairs — what was and was not applied

**Code repairs applied: 0.** No engine source, route, worker, test, fixture, conftest, migration,
`env.py`, schema, operational DB, `gula-platform` or Platform-Core file was changed in Phases 3–8.
No engine was enabled, mounted, restarted, refactored, or created. No clinical behavior,
authentication or authorization behavior was altered.

**Documentation repairs delivered (all reversible by deletion / row removal):**
- 5 new engine artifacts (inventory, verification, findings, remediation plan, dependency map).
- `NATIONAL_SERVICE_INVENTORY.md` §16 (additive NR-011 tooling supersession + Phase 3 cross-references).
- `NATIONAL_SERVICE_CONTRACTS.md` §11 (additive J1–J7 re-verification).
- `DECISION_REGISTRY.md` §D (evidence-only D-020/D-021 refresh).
- 7 findings, 7 evidence records, 6 work items, 2 change records and cross-references in GECS.

The only prior code change in the whole activation remains the Phase 2 NR-011 `env.py` +49 lines
(E-041), which must not be re-edited without new defect evidence.

## 4. Targeted evidence (Phase 6)

Single approved command form: `ENV=test PYTHONPATH=.. <gula-platform venv>/python -m pytest -q
--no-header -p no:cacheprovider <existing test files>`.

| E-ID | Scope | Result |
|---|---|---|
| E-046 | kernel/event/offline/AI-guardrail/FHIR-hardening/QC/metrics/idempotency (20 files) | 205 passed / 0 failed |
| E-047 | AI/FHIR/outbox/observability/authorization (15 files) | 291 passed / 0 failed |
| E-048 | canonical + P0 workflows (6 files) | 65 passed / 0 failed |
| E-049 | kernel cron / locks / priority / worker pool | 11 passed / 0 failed |
| E-050 | national workflows | 9 passed / 0 failed |
| E-051 | FHIR / synthetic HL7 ORU→FHIR | 4 passed / 0 failed |
| E-052 | control layer / task queue / test result / document intelligence | 155 passed / 0 failed |

**Aggregate: 740 passed / 0 failed / 0 skipped, 7 batches, all exit 0.** No BLOCKED batch: every
approved command ran and passed with the available environment. Warnings are pre-existing
dependency deprecations and are recorded, not suppressed. **No new test was written in Phase 6;
no existing test edited.** Duplicate-prevention rule applies: E-041…E-045 (NR-011) were not re-run
without new evidence.

## 5. The 18 national services

All 18 rows and their original verdicts in `GOVERNANCE/NATIONAL_SERVICE_INVENTORY.md` §3 are
retained verbatim (including the §15.1 insurance correction). Phase 4 re-check (§16) confirmed:

- Readiness was **not** derived from API/model existence: `IMPLEMENTED` still requires migrations +
  authentication + audit writes + dedicated tests.
- The §15.4 "NR-011 blocks `alembic check`" statement is **additively superseded** by E-042/E-045:
  discovery now completes without `NoReferencedTableError`. This is a tooling correction only — it
  does not close the 407-table migration gap or upgrade any service verdict.
- Migration gap (407/833 across 40 contexts), audit gaps (7 services without immutable audit writes),
  and strict-schema failures (E-001) are **unchanged**.
- Interactions with engine evidence: workflow/FHIR/CDS/offline/lab cross-references are recorded in
  §16.2, but no service was activated and no verdict changed.

## 6. Tested journeys (J1–J7)

`NATIONAL_SERVICE_CONTRACTS.md` §11 re-verified all seven patient journeys additively; **none is
marked testable, ready or certified**:

| Journey | Synthetic evidence only | Blocker retained |
|---|---|---|
| J1 Primary→Lab→Pharmacy→Follow-up | workflow E-048/050 | `cc_*` 0 % unmigrated; no audit; F-003/F-007 |
| J2 Emergency→Hospital→Radiology→Lab→Discharge | FHIR/R4 E-047; HL7 E-051 | hospital 13 uncovered tables; radiology 94.4 % |
| J3 Maternal→Lab→Pharmacy→Referral | citizen-relationship workflow 5 (E-048) | referral coverage hole F-007 |
| J4 Chronic→Primary→Lab→Medication→Follow-up | CDS synthetic E-047 | `cc_chronic_disease` 0 %; F-068 national CDS unverifiable |
| J5 Immunization→Patient record→Surveillance | none | `cc_*` 0 %; 0 audit; 0 tests |
| J6 Blood request→Compatibility→Transfusion | LIMS authorization 8 (E-046) | no immutable audit; admin-only gate |
| J7 Referral→Receiving facility→Feedback | canonical workflow unit tests | referral feedback unproven on migrated schema |

Contract primitives remain: authentication stable; authorization / tenancy / audit / offline
UNSTABLE or NOT SATISFIED. R-OFF-1 is unsatisfied (in-memory queue F-028 + first-wins `CRDT_MERGE`
F-069). R-AUTH-1 / R-ERR-1 / R-IDEM-1 are not closed by test passes.

## 7. New findings (F-066…F-072)

| ID | Finding | Sev | Status |
|---|---|---|---|
| F-066 | rules/policy/expression engines wired but no dedicated tests | P2 | OPEN — PENDING_APPROVAL (cat B) |
| F-067 | MDM service/matching no dedicated behavioral test | P2 | OPEN — PENDING_APPROVAL (cat B) |
| F-068 | National CDS: 9 permissive fail-open paths, no suite, route unmounted | P1 | OPEN — PENDING_APPROVAL (D-021 + cat C) |
| F-069 | `CRDT_MERGE` is first-seen-key-wins, not a CRDT | P2 | OPEN — PENDING_APPROVAL (D-012 + cat C) |
| F-070 | Lab device gateway no direct test | P2 | OPEN — PENDING_APPROVAL (cat B) |
| F-071 | Generated workflow scaffold dormant with trivial tests | P3 | VERIFIED (classification only) — no code action |
| F-072 | Certification engine untested; output not release evidence | P2 | OPEN — PENDING_APPROVAL (cat B) |

Duplicate-prevention outcome and non-duplication proofs are in `AUTONOMOUS_ENGINES_FINDINGS.md` §1/§4.
**No finding was closed, downgraded or merged by this report.**

## 8. Open blockers and pending approvals

**Still open:** B-005 (human security review), B-006 (commit review), B-007 (strict W1 gate:
119/872 FAILED and workflow P0 failures F-003), B-008…B-010, B-015, plus evidence gaps B-016/B-017
(RPO/RTO unmeasured; no production-like snapshot). W-031 (fixture leak), W-032 (coverage tests),
W-033 (security sign-off) remain PENDING_APPROVAL. W-017 (strict gate) is unchanged — no rerun trigger.

**Approvals needed (requested, not self-granted):**
1. **QA Lead (category B):** bounded synthetic tests for F-066, F-067, F-070, F-072 only; no existing
   test/fixture/conftest edited; new files reversible; new E-IDs.
2. **Clinical Safety Owner + Program Director (D-021, category C):** decide fail-safe semantics for the
   nine permissive CDS paths and whether the CDS route is shipping (F-068). No behavior change before sign-off.
3. **Architecture + Clinical Safety (D-012/category C):** decide whether `CRDT_MERGE` is a real
   convergence feature or a mislabeled first-wins strategy (F-069, linked to F-028).
4. **Security lead + Program Director (D-020 / W-033 / B-005):** human security review of the
   S-01…S-13 diff and R-01…R-11 acceptance.

No approval is attributed to a security or clinical reviewer in this report. Test passes are not approval.

## 9. Risks

- **Release/readiness conflation:** 740 targeted passes on SQLite could be misread as strict-gate,
  runtime or production verification. Mitigated by the fixed status taxonomy and explicit non-claims;
  W-017 remains FAILED.
- **Clinical safety:** F-068 fail-open CDS paths and F-069 offline merge semantics are unresolved;
  no CDS route enablement or behavior change is permitted before D-021/D-012.
- **Patient identity/data:** MDM matching (F-067) and audit-on-migrated-schema (F-008) are unverified;
  no production-like rehearsal (B-017).
- **Offline-first claim:** in-memory queue (F-028) + first-wins merge (F-069) → R-OFF-1 unsatisfied.
- **Traceability:** evidence logs live in volatile `/tmp` (declared lapse F-060); registries record
  paths and results but do not copy results.
- **Process:** category-B/C work must not be inferred from category-A documentation; HOLD must not flip.

## 10. Next step

Present the four approval requests in §8 to their named authorities. Until they are granted:
keep FINAL_DECISION at **HOLD**, keep D-020/D-021 PENDING, keep ENG-A12 dormant and ENG-B09
unmounted, do not rerun the strict suite (no trigger), do not commit any of the uncommitted
documentation, and do not touch the operational DB, `gula-platform` or Platform-Core. If QA
authorization is granted, execute W-044/W-045/W-047 as new, reversible test files with new E-IDs;
if D-021 is granted, execute W-046 with a recorded fail-safe decision first.

## 11. Integrity attestations (final)

- `FINAL_DECISION.md` md5 `effdfeaf10234678d83b2668c4489552` — unchanged; HOLD at lines 13 and 361.
- HEAD `2827c1ff…` and branch `integration/gula-unification-v1` — unchanged; **0 commits**.
- No code / migration / DDL / test / fixture / conftest change in Phases 3–8; no operational DB access;
  no `gula-platform` or Platform-Core modification.
- All changes are uncommitted documentation under `GOVERNANCE/`, append-only; prior history retained.
- **Production Ready and Clinical Safety Certified are NOT claimed.** No runtime or production
  verification exists (0/39 engines). FINAL_DECISION remains **HOLD**.

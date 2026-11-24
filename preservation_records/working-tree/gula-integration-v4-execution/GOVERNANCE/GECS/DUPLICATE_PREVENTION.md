# GECS — DUPLICATE PREVENTION

**Purpose (canonical):** the mandatory pre-execution protocol that stops repeated investigations,
duplicate tasks and needless re-runs. **No work starts before this checklist is completed and its
outcome recorded.**
**Created:** 2026-11-17

## 1. Mandatory pre-execution protocol

Before starting **any** task, in order:

1. Search `WORK_REGISTRY.md` for the scope (title, scope text, parent phase, dependencies).
2. Search `FINDINGS_REGISTRY.md` for the problem statement (description, source IDs, aliases).
3. Search `EVIDENCE_REGISTRY.md` for an existing result that already answers the question.
4. Check whether the work was completed previously (status `VERIFIED` / `FAILED` / `SUPERSEDED`).
5. Check whether relevant source files changed since that evidence (git status / mtimes — read-only).
6. Check whether the prior result is still valid (same inputs, same scope, same environment).
7. Identify exactly what evidence is missing.

## 2. Choose exactly one outcome (record it before executing)

| Outcome | When | What you do |
|---|---|---|
| **REUSE_EXISTING_EVIDENCE** | the question is already answered and inputs unchanged | cite the E-ID; execute nothing |
| **CONTINUE_EXISTING_WORK** | a non-`VERIFIED` item already covers the scope and is still valid | resume that Work ID; append evidence |
| **REOPEN_WITH_NEW_EVIDENCE** | predecessor `VERIFIED` but new evidence / changed files / failed acceptance / new dependency exists | record reason + impact assessment on the existing ID first; only then continue |
| **CREATE_NEW_TASK** | genuinely new scope, no predecessor covers it | create a new Work ID with all 11 required fields |
| **BLOCKED_PENDING_APPROVAL** | scope needs a decision/authorization that does not exist | record against the blocker/decision ID; execute nothing |

**Hard rules**
- Do not create a new task if an existing item covers the same scope (merge or link instead).
- Do not rerun a completed test without a documented trigger (new evidence, changed files,
  failed acceptance criterion, newly discovered dependency — record which).
- Do not repeat repository-wide scans without a demonstrated need written down first.
- Findings merge **only after** proving identical root cause; original IDs and history are preserved
  (see `FINDINGS_REGISTRY.md` merge/linked lists).
- `FAILED` results are evidence, not invitations to re-run: W-017 (strict gate) stays FAILED until
  D-001/D-003 approvals exist — rerunning now would produce the same 119 failures.

## 3. Worked resolutions (recorded at GECS creation)

| Proposed action | Search result | Outcome chosen | Why |
|---|---|---|---|
| "Re-derive the 340-table missing inventory" | E-008/E-012/E-013 exist, fingerprint unchanged | **REUSE_EXISTING_EVIDENCE** | inputs unchanged; measurement complete |
| "Re-run the strict 872-test suite to see current state" | W-017 = FAILED with E-001…E-007; no approval changed | **BLOCKED_PENDING_APPROVAL** | no trigger; same schema → same result |
| "Re-run the full backend suite" | E-031 (3,480/0) current; no code changed in this phase | **REUSE_EXISTING_EVIDENCE** | suite rerun prohibited without trigger |
| "Investigate the fixture leak again" | F-005 + W-031 exist, root cause proven | **CONTINUE_EXISTING_WORK** (awaiting category-B approval) | fix authorized separately |
| "Fix `app.main` import defect" | F-021 + W-042 exist | **CONTINUE_EXISTING_WORK** when authorized | separate ticket, not ADR scope |
| "Re-scan security endpoints" | E-033/E-029 current (2,133/2,064/69) | **REUSE_EXISTING_EVIDENCE** | walk exists; new walk only if routes change |
| "Re-run `pip-audit`" | E-032 three audits exit 0 | **REUSE_EXISTING_EVIDENCE** | re-scan only on dependency change |
| "Create a task per missing table (340 tasks)" | E-012 groups them into 8 bounded contexts | **CREATE_NEW_TASK ×5 waves (W-026…W-030)** | mandate: group by bounded context, never 340 tasks |
| "Adopt RPO 1hr / RTO 4hr from prior report" | F-018 flags it as unverified claim | **BLOCKED_PENDING_APPROVAL** (D-004, W-034) | no measurement exists here |

## 4. Audit hook

The control-system audit (`GECS_CHECKPOINT.md` §4) verifies that every new Work/Finding ID has a
unique predecessor search recorded in this protocol's spirit: no duplicate IDs, no reopened item
without reason, no evidence re-run without trigger.

## 5. Worked resolutions — Phase 3–8 (additive)

| Proposed action | Search result | Outcome chosen | Why |
|---|---|---|---|
| "Re-run failed engine-discovery subagents" | four earlier subagents stopped at free-usage limit; no reusable artifacts | **REUSE_EXISTING_EVIDENCE** (do not rerun) | no prior work to repeat; bounded source discovery done directly |
| "Audit engines from the 18-service inventory" | W-003/W-007/W-040/041/W-042 cover different scopes; no engine-audit item | **CREATE_NEW_TASK (W-043)** | genuinely new scope; 5 artifacts + E-046…E-052 |
| "Count the generated `workflow_engine` scaffold as workflow verification" | ENG-A01 `app/workflows/engine.py` is canonical; scaffold has 0 external refs + 3 trivial tests | **REUSE_EXISTING_EVIDENCE** + classify `DORMANT` (F-071) | never cite trivial generated tests as canonical verification |
| "Treat E-052 as closing F-066/F-067/F-068/F-070/F-072" | E-051 exercised control-layer policy, task queue, test-result and document intelligence, not the gapped engines | **REUSE_EXISTING_EVIDENCE** — gaps stay OPEN | E-052 promoted A09/A11/B12/D03 only; no finding closed |
| "Re-run NR-011 acceptance tests (E-041…E-045)" | 14 new regression tests pass; no changed engine source or new defect evidence | **REUSE_EXISTING_EVIDENCE** | duplicate rule; no trigger |
| "Re-run the 872-test strict gate after 740 targeted passes" | W-017 FAILED (E-001); 740 passes are a different SQLite corpus | **BLOCKED / REUSE_EXISTING_EVIDENCE** | no trigger; different schema and test set |
| "Close D-020/D-021 on the strength of authorization test passes" | `DECISION_REGISTRY.md` §D shows human sign-off absent | **BLOCKED_PENDING_APPROVAL** | authentication ≠ authorization; tests ≠ clinical/security certification |
| "Add tests for F-066/F-067/F-070/F-072 now" | category B not authorized; W-031/W-032 already pending approval | **BLOCKED_PENDING_APPROVAL** (W-044/W-045) | request QA authorization; no campaign started |
| "Change CDS fail-open paths / `CRDT_MERGE` in Phase 3" | clinical/outline behavior change needs D-021 / D-012 | **BLOCKED_PENDING_APPROVAL** (W-046/W-047) | never change clinical or offline behavior without named authority |

**Outcome recorded for Phase 3:** `CREATE_NEW_TASK` (W-043) + `CREATE_NEW_FINDINGS` (F-066…F-072),
with `BLOCKED_PENDING_APPROVAL` for category-B/C repairs. No failed subagent was rerun, no existing
test was re-executed without trigger, and no duplicate finding was created (proof in
`AUTONOMOUS_ENGINES_FINDINGS.md` §1/§4).

## 6. Worked resolutions — D-023 remediation (additive, 2026-11-17)

Rows 71–72 above (`BLOCKED_PENDING_APPROVAL` for F-066/F-067/F-070/F-072 tests and CDS/`CRDT_MERGE`
behavior) are **superseded in scope only** by D-023 (owner executive delegation, CC-007/CC-008).
The blocks were real at Phase 3; the owner has now authorized bounded category-B/C remediation.
No earlier row is rewritten.

| Proposed action | Search result | Outcome chosen | Why |
|---|---|---|---|
| "Add synthetic tests for F-066/F-067/F-068/F-070/F-072" | Phase 3 rows 71–72 BLOCKED; D-023 now grants B/C for bounded scope | **`CONTINUE_EXISTING_WORK` → W-049…W-055 (E-053…E-059)** | authorization changed (D-023); findings adopted, not duplicated |
| "Fix 15-of-16 broken rules-runtime operators" | discovered during E-058, no existing finding | **`CREATE_NEW_FINDING` F-077 + bounded fix** | real defect (AttributeError on every non-eq rule), regression-tested |
| "Fix missing-field→0 false-normal in rules-runtime" | discovered during E-058, no existing finding | **`CREATE_NEW_FINDING` F-078 + bounded fix** | clinical fail-safe; conservative no-match, evidence preserved |
| "Make certification route stop returning 500" | discovered during E-059, no existing finding | **`CREATE_NEW_FINDING` F-079 + bounded fix** | idempotent in-root absolute path; traversal still rejected |
| "Build a real CRDT for offline sync" | F-069/F-028; full CRDT needs schema redesign (out of bounded scope) | **`CREATE_NEW_TASK`-defer / honest alternative** | `CONFLICT_QUARANTINE` label + conflict preservation; no unproven CRDT claim; crash durability stays NOT VERIFIED |
| "Mount/enable national CDS route or ENG-A12/ENG-B09" | D-021/D-012 PENDING; standing prohibition | **`BLOCKED_PENDING_APPROVAL`** | new clinical behavior stays disabled by default; owner approval ≠ clinical certification |
| "Close D-020 on the Phase G merge fix" | `DECISION_REGISTRY.md` §D: human sign-off absent | **`BLOCKED_PENDING_APPROVAL`** | engineering fix ≠ human security review (B-005/W-033) |
| "Publish RPO/RTO from Phase N assessment" | F-018 flags unverified; no measurement | **`BLOCKED_PENDING_APPROVAL`** | no measured value; numbers must not be published as measured |

**Outcome recorded for D-023:** 7 remediation tasks VERIFIED (W-049…W-055) with 7 independent
E-IDs; 9 new findings (F-073…F-081) of which 3 are FIXED defects and 6 are recorded residuals;
no failed test hidden or skipped; no existing test rerun without trigger; strict suite not rerun.

---

## CC-010 duplicate-prevention record (append-only — 2026-11-17)

Pre-execution search protocol applied to every proposed action in the post-stabilization completion
program. No earlier row is rewritten.

| Proposed action | Search result | Outcome chosen | Why |
|---|---|---|---|
| "Build a National Capability Registry / engine index" | Phase H assessment (W-056) already recommended GO-FOR-DESIGN reference-only; 39 engines already inventoried (`AUTONOMOUS_ENGINES_INVENTORY.md`) | **`CONTINUE_EXISTING_WORK` → W-064/W-072/W-079, reference-only index** | no new engine; re-use the inventoried 39 with their recorded statuses; executing registry explicitly NO-GO |
| "Create a new orchestration/dispatch engine for the registry" | ENG-A01…A06 + ENG-A12 (dormant) already cover workflow/rules/decision; D-021/standing prohibition | **`BLOCKED_PENDING_APPROVAL`** | would duplicate existing engines, create a SPOF, and activate dormant surface; outside CC-010 category A+B |
| "Mount/enable ENG-B09 national CDS or ENG-A12" | D-021 PENDING; F-068/F-071; standing prohibition | **`BLOCKED_PENDING_APPROVAL`** | owner engineering mandate ≠ clinical certification; new clinical behavior disabled by default |
| "Register the two unregistered declarative bases in `env.py`" | New source observation (E-063): `DocIntelBase`/`InsBase` absent from `target_metadata`; NR-011 already approved (D-003/CC-004) | **`CREATE_NEW_FINDING` F-085 + defer to category-D/D-001 wave** | real metadata blind spot, but changing `env.py` needs approval + fresh-clone autogenerate; NR-011 delta must stay `+49/-0` here |
| "Re-run MDM / CDS / offline / gateway / certification suites" | E-053…E-061 already VERIFIED; no changed source in those areas | **`DO_NOT_REPEAT`** | a VERIFIED item is never repeated without a documented trigger (new evidence, changed files, failed criterion, new dependency) — none exists |
| "Re-run the 872-test strict suite to prove completion" | E-001 753/119 FAILED; no documented trigger | **`BLOCKED_PENDING_APPROVAL`** | no trigger; a pass must not be obtained by weakening a gate; historical numbers immutable |
| "Close F-073…F-084 as part of completion" | residuals explicitly carried OPEN by D-023 final report | **`DO_NOT_CLOSE`** | no finding was closed by CC-010; closure requires verified acceptance evidence and the named professional authority |

**Outcome recorded for CC-010:** 1 new finding (F-085, E-063) + 1 new blocker (B-022), 3 new
evidence IDs (E-062/063/064), 17 new work items (W-064…W-080), 1 new change record (CC-010), **no**
new decision, **no** decision status change, no repeated VERIFIED work, no strict-suite rerun, no
dormant activation, no gate closure, no HOLD change.

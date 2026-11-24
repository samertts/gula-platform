# AUTONOMOUS ENGINES FINDINGS — Phase 3 (new, non-duplicate findings)

**Repository / HEAD:** `gula-integration` · `integration/gula-unification-v1` @ `2827c1ff…` (unchanged)
**Date:** 2026-11-17 · **Category:** A (documentation-only) · **Change record:** CC-005
**Canonical status owner:** `GOVERNANCE/GECS/FINDINGS_REGISTRY.md` (this file is the detail report;
the registry rows are added in Phase 7 sync). **No finding below is closed by this document.**

---

## 1. Duplicate-prevention outcome (mandatory protocol, §1–§2 of `DUPLICATE_PREVENTION.md`)

| Step | Result |
|---|---|
| Search `WORK_REGISTRY` for "engine audit / workflow / rules / CDS / MDM / offline conflict / certification" | Existing W-003 (search promotion), W-007 (communication), W-040/041 (wiring/drift), W-042 (AI-registry defect) cover **different scopes**; no engine-audit item exists → new W-043 |
| Search `FINDINGS_REGISTRY` for the seven problem statements | F-007 (coverage holes: referrals/care_continuum/hospital), F-028 (in-memory offline queue), F-043 (professional activation CWE-863), F-058 (lint/type debt), F-065 (NR-011 5 zero-table bases), F-021 (AI-registry defect) found. **None has the same root cause** as F-066…F-072 — see §4 |
| Search `EVIDENCE_REGISTRY` | No engine verification record existed (E-001…E-045 cover schema, security, frontend, NR-011). New E-046…E-052 created |
| Completed previously? | No — Phase 3 engine discovery/execution was new (four earlier subagents stopped at the free-usage limit; their work is not redone here) |
| Source files changed since prior evidence? | Only `backend/migrations/env.py` (NR-011, E-041); engine sources unchanged — re-scan unnecessary but file existence/LOC measured fresh |
| Prior result valid? | Yes for E-041…E-045; **not reused for engine verification** (different question) |
| Missing evidence | Engine entry points, dependency graph, existing-test mapping, isolated synthetic execution → this report + E-046…E-052 |

**Outcome chosen:** `CREATE_NEW_TASK` (W-043) + `CREATE_NEW_FINDINGS` (F-066…F-072).
No subagent was rerun; no prior work was repeated.

## 2. New findings summary

| ID | Title | Type | Sev | Affected engines | Status | Closure requires |
|---|---|---|---|---|---|---|
| F-066 | Kernel/national rules-policy engines are wired but have no dedicated tests | missing-evidence | P2 | ENG-A07, ENG-A08, ENG-A10 | **OPEN — PENDING_APPROVAL** (category B) | dedicated tests added under QA authorization and passing in isolation; no behavior change |
| F-067 | MDM service/matching has no dedicated behavioral test | missing-evidence | P2 | ENG-B07 | **OPEN — PENDING_APPROVAL** (category B) | MDM unit tests (exact/fuzzy/probabilistic, dedup decisions) exist and pass |
| F-068 | National CDS engine: 9 permissive swallowed-exception paths + no dedicated suite; route not mounted by factory | risk (clinical) / missing-evidence | P1 | ENG-B09 | **OPEN — PENDING_APPROVAL** (D-021 + category C) | clinical-safety review of failure semantics; fail-closed decision; dedicated tests; route exposure decision — **no behavior change without clinical approval** |
| F-069 | `CRDT_MERGE` conflict resolution is first-seen-key-wins, not a CRDT | confirmed-defect (semantics/claim) | P2 | ENG-C05 | **OPEN — PENDING_APPROVAL** (D-012 + category C) | either real CRDT with convergence tests, or rename/gate as non-CRDT; clinical/offline behavior change needs separate approval |
| F-070 | Lab device gateway has no direct test | missing-evidence | P2 | ENG-C08 | **OPEN — PENDING_APPROVAL** (category B) | gateway unit tests (HL7 parsing/analyzer mapping/error paths) exist and pass |
| F-071 | Generated `capabilities/workflow_engine` scaffold is dormant with trivial tests | confirmed-architectural (classification) | P3 | ENG-A12 | **VERIFIED (classification) — no code action** | not a defect to fix; keep dormant; never count its 3 trivial tests as canonical-workflow verification |
| F-072 | Certification engine has no dedicated tests; its output must not be read as production readiness | missing-evidence | P2 | ENG-D06 | **OPEN — PENDING_APPROVAL** (category B) | dimension tests + explicit disclaimer enforced in docs; certification output never used as release evidence |

## 3. Finding detail

### F-066 — rules/policy/expression engines lack dedicated tests
- **Evidence:** source read — `app/kernel/rules_runtime.py` (299 LOC), `app/kernel/policy_runtime.py`
  (220 LOC), `app/national/rules_engine/domain/expression_engine.py` (200 LOC). Wiring confirmed at
  `app/kernel/runtime_routes.py`, `app/kernel/runtime_integration.py`, `app/factory.py:692`.
  Symbol search over `tests/**/test_*.py` found no dedicated module; none of the seven executed
  batches (E-046…E-052) included them. E-052 exercised control-layer policy/risk (ENG-A09), not
  `rules_runtime` / `policy_runtime` / the national expression engine.
- **Root cause:** these engines were added as infrastructure wiring without an accompanying test
  module; this is a coverage gap, **not** a reproduced defect.
- **Impact:** rule evaluation, policy decisions and expression semantics are `SOURCE_PRESENT` only;
  no PASS may be claimed for them. They are not part of the W1 872-test corpus, so W-017 is unchanged.
- **Resolution proposed (not executed):** add focused tests under explicit category-B QA authorization;
  keep behavior unchanged; record as new evidence with a new E-ID.
- **Acceptance:** tests exist, pass in isolation, and are mapped to these three engines; no existing
  test edited; no rule/policy logic changed.
- **Related / distinct:** F-058 (general lint/type debt — different), F-007 (workflow coverage holes
  in referrals/care_continuum/hospital — different modules). W-031/W-032 are the existing approval
  vehicles for test additions; do not open a duplicate QA campaign.

### F-067 — MDM has no dedicated behavioral test
- **Evidence:** `app/health_data/mdm/service.py` (132) and `matching.py` (318) expose
  `MDMService`, `ExactMatcher`, `FuzzyMatcher`, `ProbabilisticMatcher`; no `tests/**` module
  references these symbols behaviorally (E-045 references the module path only for metadata import).
- **Impact:** patient identity deduplication/matching behavior is unverified. It touches patient data
  handling, so any test addition must use synthetic records and must not be read as D-020/D-021 sign-off.
- **Resolution proposed (not executed):** synthetic unit tests for matcher thresholds, tie-breaks and
  merge/no-merge decisions under category-B authorization.
- **Related / distinct:** F-033 (NIAM persons/sessions/devices authz — different), F-027 (tenant
  isolation on migration schema — different), D-021 (clinical sign-off — still PENDING).

### F-068 — national CDS engine permissive failures, no suite, unmounted route
- **Evidence:** `app/national/services/cds_engine.py` (983 LOC) has `except (ValueError, TypeError):
  pass` / permissive defaults at lines 635, 669, 679, 689, 699, 756, 769, 782, 798 (e.g. condition
  comparison failure returns `True`, allowing a rule to pass). No dedicated test module found.
  `app/national/api/routes/cds.py` mounts CDS endpoints into `national_router`
  (`app/national/api/routes/__init__.py:22`), but `app/factory.py` was read and does **not** mount that
  aggregator in the observed wiring (it includes individual national sub-routers instead).
- **Root cause:** defensive coding uses fail-open defaults; no test suite pinned the intended
  fail-safe semantics. Exposure status is separately unverified — no claim of a live endpoint is made.
- **Impact:** if activated, malformed clinical inputs could yield permissive CDS output. This is a
  **clinical-safety-sensitive finding**, not something to silently "fix" in this governance phase.
- **Resolution proposed (not executed):** clinical-safety review (D-021 authority) decides fail-closed
  semantics; only then add tests and change behavior under category C. Route mount decision needs
  the same approval. Until then: **do not enable, do not refactor, do not claim safe**.
- **Related / distinct:** F-043 (professional activation CWE-863 — authentication/authorization,
  different root cause), B-005/D-020 (security sign-off — different authority), D-021 (clinical).
  This finding is **new** and does not duplicate any of them.

### F-069 — `CRDT_MERGE` is not a CRDT
- **Evidence:** `app/services/offline_sync_service.py:176-182` — for each of the two conflicting
  operations it copies `k → v` only `if k not in merged`, i.e. **first-seen key wins**. There is no
  conflict-free replicated data type, no tombstone, no commutative/associative/idempotent merge proof.
  `test_offline_sync.py` (20 passed, E-046) covers `LAST_WRITE_WINS`, `TIMESTAMP_MERGE`, `MANUAL`
  but not this branch. `app/certification/dimensions/offline.py:35` still lists CRDT as an option,
  so the label could be mistaken for a real convergence guarantee.
- **Root cause:** enum value named `CRDT_MERGE` was implemented as a first-wins dictionary merge.
- **Impact:** misleading capability claim; if used for clinical/offline data, divergent replicas may
  not converge. Distinct from **F-028**, which is about the in-memory queue losing work on restart —
  this finding is about merge semantics.
- **Resolution proposed (not executed):** either implement a real CRDT with convergence tests, or
  rename/gate the value so it cannot be mistaken for a CRDT — **only after** D-012 (ADR-J) and any
  clinical/offline behavior approval; category C.
- **Acceptance:** documented decision + tests proving convergence (if implemented) or proof the
  branch is non-shipping with an accurate label.

### F-070 — lab device gateway has no direct test
- **Evidence:** `app/gateways/lab_device_gateway.py` (219 LOC) read; symbol search over `tests/**`
  found no direct module. HL7 conversion itself is tested (`test_fhir_interoperability.py`, E-051)
  but that exercises `app/capabilities/fhir_interoperability/hl7.py`, not the gateway.
- **Impact:** analyzer/device ingress mapping and error paths are `SOURCE_PRESENT` only.
- **Resolution proposed (not executed):** synthetic gateway tests (category B) — parser outputs,
  instrument mapping, malformed-message handling. No production device connection.

### F-071 — dormant generated workflow scaffold (classification finding, VERIFIED)
- **Evidence:** `grep -rln "capabilities.workflow_engine" app/**/*.py` returns only files inside
  `app/capabilities/workflow_engine/`; its `tests/test_unit.py` (2) and `test_integration.py` (1)
  assert only `success=True` / `validate=True`. The real workflow engine is `app/workflows/engine.py`
  (ENG-A01, E-048/050).
- **Classification:** `DORMANT` — source exists, no external consumers, not the canonical engine.
- **Impact:** risk of mistaking trivial generated tests for workflow verification. No defect to repair.
- **Action:** none; keep dormant, do not activate, do not cite as evidence for G-08. **VERIFIED as
  classification** (source/reference scan), not as functional verification.

### F-072 — certification engine untested; readiness claims must not use its output
- **Evidence:** `app/certification/engine.py` (117) and `app/certification/dimensions/offline.py`
  (204) read; no dedicated test module found. Offline dimension text lists candidate strategies
  without measuring them.
- **Impact:** a certification report produced by this engine is not evidence of production
  readiness, migration compatibility or clinical safety. `FINAL_DECISION.md` stays HOLD.
- **Resolution proposed (not executed):** dimension tests under category-B authorization + an
  explicit scope disclaimer next to any generated certification artifact.

## 4. Cross-references — no duplication

| Existing finding | Why the new finding is **not** a duplicate |
|---|---|
| F-065 (NR-011: 5 of 17 bases contribute 0 tables) | Schema-discovery gap in `env.py`; none of F-066…F-072 concerns metadata discovery. F-065 stays open and is **referenced, not re-recorded** |
| F-028 (offline queue in memory) | Durability/restart loss; F-069 is merge semantics (`CRDT_MERGE`). Linked, not merged |
| F-007 (coverage holes: referrals/care_continuum/hospital) | Different modules; F-066/067/070/072 cover rules, MDM, device gateway, certification |
| F-043 (CWE-863 professional activation) | Authentication/authorization defect; F-068 is clinical decision output on malformed input |
| F-021 (`app.main` `:caps::jsonb` registry defect) | Concrete import-time SQL syntax defect; no overlap with engine findings |
| F-058 (lint/type debt), F-063 (`create_all()` control) | Quality/control-role findings; different root causes |
| D-020 / D-021 | Approval decisions, not findings; neither is advanced or closed by these findings |

**Counts after Phase 3 detail (registry sync occurs in Phase 7):** 7 new findings F-066…F-072
(6 OPEN PENDING_APPROVAL · 1 VERIFIED classification). Findings total 65 → **72**.
No finding is closed here; no severity is downgraded; no historical row is rewritten.

**E-052 effect on findings:** the seventh batch (155 passed / 0 failed) promoted ENG-A09, ENG-A11,
ENG-B12 and ENG-D03 from `SOURCE_PRESENT` to `UNIT_VERIFIED`, but did **not** exercise any engine
gapped by F-066 (rules/policy/expression), F-067 (MDM), F-068 (national CDS), F-070 (device gateway)
or F-072 (certification). All seven findings therefore keep their status and severity unchanged.

# National Integration Program — MASTER EXECUTION PLAN

**Program:** GULA National Integration & Governance Remediation Program
**Document:** 00 — Master Execution Plan
**Date:** 2026-11-18
**Primary repository:** `/home/samertts/workspace/projects/gula-integration`
**Branch:** `integration/gula-unification-v1` · **HEAD (baseline):** `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0`
**Secondary repository:** `/home/samertts/workspace/projects/gula-platform` (read-only baseline; HEAD `f478676b6fc375338648dde46fbf076c015a3f91`, clean)
**Data class:** SYNTHETIC ONLY. No real patient data, no national identifiers, no production DB, no network, no external publication, no deployment.

---

## 1. Authority and boundaries

This plan records engineering evidence and decision-package preparation under the executing engagement directive. **Nothing here supersedes, lifts or reinterprets the repository's recorded `HOLD` / `REJECT` verdicts** — those remain in full force in their original files (md5s below), and this program claims **no** owner signature:

| Authorized (engineering evidence only) | Not authorized (never performed) |
|---|---|
| Local commits on a dedicated working branch after validation | Push, publish, PR, protected-branch merge, public release |
| Synthetic-safe engineering evidence and decision-package preparation for MPI REJECT, MP-001, ODR-001…004, D-020/D-021, ADR-A…J — verdicts unchanged | Inventing legal / clinical / regulatory / government-owner approval |
| Disposable local DB migrations for rehearsal | Any operational/production DB or live infrastructure access |
| Superseding **decision packages** that leave original history intact | Falsifying, rewriting or deleting original governance history |
| Parallel agents on disjoint file ownership | Deleting tests, weakening assertions, hiding failures, counting skips as passes |

**Original governance records are immutable evidence.** `GOVERNANCE/FINAL_DECISION.md` (HOLD, md5 `effdfeaf10234678d83b2668c4489552`), `GOVERNANCE/IDENTITY_REMEDIATION/MPI_FINAL_INDEPENDENT_AUDIT.md` (REJECT, md5 `1a02c01563c93b07a7cdb92c0462bf36`) and `MPI_INDEPENDENT_AUDIT_FINDINGS.md` (md5 `ea3969d09aaf7b0b28a065838b44a594`) are **not edited**. Every evidence-status change is recorded in a new, traceable record under this directory; **owner verdicts are never superseded by this program**.

## 2. Status vocabulary (mandatory, no synonyms)

`IMPLEMENTED` · `TESTED` · `INTEGRATED` · `INDEPENDENTLY VERIFIED` · `PRODUCTION READY` · `BLOCKED` · `NOT IMPLEMENTED`

- `INDEPENDENTLY VERIFIED` requires a reviewer with no file ownership in the change.
- `PRODUCTION READY` requires human security/legal/clinical sign-off and owner release decision — **cannot be self-awarded by this program**.
- `BLOCKED` always names the missing authority and the decision package that carries it.
- `NOT IMPLEMENTED` is used honestly where a platform or dataset is absent (e.g. iOS Xcode project, licensed SNOMED CT).

## 3. Program structure — phases and workstreams

### Phases

| Phase | Name | Exit criterion | Status |
|---|---|---|---|
| **A** | Baseline, survey and planning | Evidence-based baseline, 15 documents + registry, dependency graph, critical path | `IMPLEMENTED` (this document set) |
| **B** | Authorized engineering remediation | Each workstream change has focused tests; no baseline regression | `NOT IMPLEMENTED` |
| **C** | Integration and cross-workstream evidence | Full regression green; OpenAPI/contract diff where applicable; integration tests | `NOT IMPLEMENTED` |
| **D** | Adversarial review and decision packages | Independent review per change; external-authority packages complete | `NOT IMPLEMENTED` |
| **E** | Final acceptance | Scorecard + `14_FINAL_ACCEPTANCE_REPORT.md`; STOP before deployment | `NOT IMPLEMENTED` |

### Workstreams (WS-01 … WS-07) — disjoint file ownership

| WS | Name | Primary surface (integration repo) | Survey doc |
|---|---|---|---|
| **WS-01** | Identity & MPI | `backend/app/identity/`, `backend/app/services/mpi/`, `backend/app/health_core/identity/` | `06` |
| **WS-02** | Security & audit | `backend/app/security/`, `backend/app/audit/`, `backend/app/health_core/authorization/` | `07` |
| **WS-03** | FHIR R4 interoperability | `backend/app/health_core/fhir/`, `backend/app/capabilities/fhir_interoperability/`, `backend/app/national/fhir/`, `backend/app/fhir/` | `08` |
| **WS-04** | Terminology | `backend/app/health_core/terminology/`, `backend/app/national/reference/` | `09` |
| **WS-05** | Reliability & offline-first | `backend/app/health_core/reliability/`, offline sync engine | `10` |
| **WS-06** | Client integration | `backend/app/health_core/client_integration/`, frontend contracts | `11` |
| **WS-07** | National domains & journeys | `backend/app/domain_platform/`, national service inventory | `12` |

Workstream charters, file ownership, acceptance criteria and dependency edges are in `03_WORKSTREAM_CHARTERS.md`; the machine-readable graph is in `02_DEPENDENCY_GRAPH_AND_CRITICAL_PATH.md` and `status_registry.json`.

## 4. Verified baseline (single source of truth for Phase A)

| Evidence | Result | Status |
|---|---|---|
| Health Core synthetic gate | **773 passed, 1 warning, 0 failed / 0 skipped / 0 errors** (13.41 s re-run with complete toolchain; count independently re-run by the reviewer — see review record) | `TESTED` |
| Ruff / MyPy | Ruff clean on Health Core scope; MyPy 0 issues in 75 source files (complete toolchain — see `01`) | `TESTED` |
| Preservation gate (prior cycle) | 24/24 PASS — governance, preservation and ownership intact (carried prior-cycle evidence) | `TESTED` |
| Reproducible six-workstream demo (prior cycle) | All assertions passed (carried prior-cycle evidence) | `TESTED` |
| MPI final independent audit | **REJECT** — 13 PASS + 1 documented PASS, 3 open (AUD-02 HIGH, AUD-07 MED, AUD-16 INFO) | `BLOCKED` (owner-gated) |
| Unification release decision | **HOLD** — 11 exit criteria, 5/7/8/9 NOT MET | `BLOCKED` (owner-gated) |
| ADR-A … ADR-J | All `PENDING` in `GOVERNANCE/ADR_DECISION_REQUEST.md` | `BLOCKED` (owner-gated) |
| NR-011 prerequisite engineering | `TESTED` — 14/14 regressions + disposable-PG `alembic check` with 0 metadata aborts | `TESTED` |
| 426 unmigrated ORM tables | strict-schema gap; ADR-A decision prerequisite | `BLOCKED` |

**Toolchain note (environment recovery):** the prior `/tmp/opencode/{mpi-venv,prodready}` artifacts were removed by an environment reset before this phase. The complete equivalent toolchain was recovered from `/home/samertts/workspace/projects/gula-platform/backend/.venv` (Python 3.12.13, pytest 9.1.1, ruff 0.16.0, mypy 2.3.0, alembic 1.18.5, `signxml` present). The 773-test gate was re-executed, **Ruff passed**, **MyPy passed on 75 files**, and full-suite collection succeeded (4675 tests, 0 errors). See `01_PHASE_A_BASELINE.md` §2.

## 5. Critical path (summary)

`NR-011 fix — **TESTED** this program (14/14 regressions + disposable-PG `alembic check` with 0 metadata aborts)` → `ADR-A decision` → `context-by-context migrations` → `MIG-EXISTING closure` → `HOLD lifting` → `production readiness`.
`MP-001 (DB UNIQUE)` → `AUD-02 closure` → `MPI ACCEPT` → `national identity platform`.
All external-authority items (Iraqi legal/clinical/government approvals, licensed SNOMED CT, iOS platform) are **decision packages only** in this program.

## 6. Quality gates (every change)

1. Focused test suite for the changed module(s) — must pass before integration.
2. Full Health Core gate (773 baseline) at each milestone — no test deleted, skipped or weakened.
3. Contract/OpenAPI diff where routes or schemas change — must be byte-stable unless a documented correction.
4. Ruff + MyPy on changed scope (restored toolchain).
5. Independent adversarial review before any workstream is marked `INDEPENDENTLY VERIFIED`.
6. Preservation gate: HEADs, protected md5s, 0 deletions, no protected-repo writes.

## 7. Deliverable index

`00` master plan · `01` baseline · `02` dependency graph/critical path · `03` workstream charters · `04` governance remediation plan · `05` decision packages · `06`–`12` seven workstream surveys · `13` integration test & verification · `14` final acceptance · `status_registry.json` (machine-readable).

---

**End state of this program is explicitly NOT production deployment.** Phase E ends with a STOP for Program Director acceptance.

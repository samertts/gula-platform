# REPOSITORY RISK MATRIX

**Program:** PROGRAM-REPO-01 v1.0 — Repository Engineering & Open Source Excellence
**Phase:** 2.5-C / F — Repository Risk Matrix (ANALYSIS ONLY — no mutations)
**Date:** 2026-08-08
**Status:** DRAFT — risk scores are evidence-driven from REPOSITORY_DEPENDENCY_GRAPH.md edges.

**Scale:** LOW · MEDIUM · HIGH · CRITICAL
**Risk axes:** Move (M) · Rename (R) · Delete (D) · Archive (A) · Break CI · Break Workflows (Wf) ·
Break Scripts (Sc) · Break Docs (Doc) · Break Release Pipeline (Rel)
**Overall = worst-of-per-axis** (conservative; a single CRITICAL axis makes the dir CRITICAL to touch).

---

## 1. Directory Risk Matrix

| Directory | Classification | M | R | D | A | CI | Wf | Sc | Doc | Rel | OVERALL | Constraint edges |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `backend/` | ACTIVE | CRITICAL | CRITICAL | CRITICAL | CRITICAL | CRITICAL | CRITICAL | HIGH | MEDIUM | CRITICAL | **CRITICAL** | E-06 (compose), E-01 (shared), Makefile, CI |
| `shared/` | SHARED | CRITICAL | CRITICAL | CRITICAL | CRITICAL | HIGH | MEDIUM | CRITICAL | MEDIUM | HIGH | **CRITICAL** | E-01 (67 imports), E-02 |
| `governance/` (top-level) | ACTIVE | HIGH | HIGH | CRITICAL | HIGH | MEDIUM | LOW | HIGH | MEDIUM | MEDIUM | **CRITICAL** | E-16 (backend imports it) |
| `frontend-v3/` | ACTIVE | MEDIUM | MEDIUM | HIGH | MEDIUM | HIGH | HIGH | MEDIUM | LOW | MEDIUM | **HIGH** | E-09 (generator+zero-drift), ci.yml, vitest |
| `services/` | ACTIVE | HIGH | HIGH | CRITICAL | HIGH | HIGH | MEDIUM | MEDIUM | LOW | HIGH | **CRITICAL** | E-06 (compose contexts), 9 Dockerfiles |
| `scripts/` | TOOLING | HIGH | HIGH | HIGH | HIGH | HIGH | HIGH | CRITICAL | MEDIUM | HIGH | **CRITICAL** | Makefile(63), workflows, AGENTS.md |
| `contracts/` | ACTIVE | MEDIUM | MEDIUM | HIGH | MEDIUM | MEDIUM | MEDIUM | MEDIUM | LOW | MEDIUM | **MEDIUM** | E-12 sdk-publish |
| `mobile/` | ACTIVE | LOW | LOW | HIGH | LOW | HIGH | HIGH | LOW | LOW | HIGH | **HIGH** | E-13 3 workflows |
| `server/` | ACTIVE | MEDIUM | MEDIUM | HIGH | MEDIUM | HIGH | MEDIUM | LOW | LOW | MEDIUM | **HIGH** | E-10 root Dockerfile + package.json |
| `data/` | ACTIVE | MEDIUM | MEDIUM | HIGH | MEDIUM | LOW | LOW | MEDIUM | LOW | MEDIUM | **MEDIUM** | deployment SQL |
| `docs/` | ACTIVE_DOC | LOW | LOW | MEDIUM | LOW | LOW | LOW | MEDIUM | HIGH | LOW | **MEDIUM** | E-11 link targets |
| `security/` | ACTIVE_INFRA | MEDIUM | MEDIUM | HIGH | MEDIUM | LOW | LOW | MEDIUM | LOW | LOW | **MEDIUM** | policies referenced |
| `config/` | ACTIVE_INFRA | MEDIUM | MEDIUM | HIGH | MEDIUM | MEDIUM | LOW | MEDIUM | LOW | MEDIUM | **MEDIUM** | E-14 compose/scripts |
| `terraform/` | ACTIVE_INFRA | LOW | LOW | MEDIUM | LOW | LOW | LOW | LOW | LOW | MEDIUM | **LOW** | image-name only (E-15) |
| `k8s/` | ACTIVE_INFRA | LOW | LOW | MEDIUM | LOW | LOW | LOW | LOW | LOW | MEDIUM | **LOW** | image-name only (E-15) |
| `helm/` | ACTIVE_INFRA | LOW | LOW | MEDIUM | LOW | LOW | LOW | LOW | LOW | MEDIUM | **MEDIUM** | E-04 `frontend-v2` image edge |
| `docker/` | ACTIVE_INFRA | MEDIUM | MEDIUM | HIGH | MEDIUM | MEDIUM | MEDIUM | LOW | LOW | MEDIUM | **MEDIUM** | build path |
| `cloudflare/` | ACTIVE_INFRA | LOW | LOW | LOW | LOW | LOW | LOW | LOW | LOW | LOW | **LOW** | none |
| `.ai/` | TOOLING | LOW | LOW | HIGH | LOW | MEDIUM | MEDIUM | MEDIUM | MEDIUM | LOW | **MEDIUM** | gate baselines |
| `.github/` | TOOLING | LOW | LOW | CRITICAL | LOW | CRITICAL | CRITICAL | MEDIUM | MEDIUM | HIGH | **CRITICAL** | E-03 (workflows) |
| `frontend-v2/` | LEGACY | **HIGH** | MEDIUM | HIGH | **HIGH** | **CRITICAL** | **CRITICAL** | MEDIUM | LOW | MEDIUM | **CRITICAL** | E-03 frontend-pwa builds it; E-04 helm image |
| `frontend/` | LEGACY | LOW | LOW | MEDIUM | LOW | LOW | LOW | LOW | LOW | LOW | **LOW** | no workflow edge (14 static files) |
| `nhop-platform/` | LEGACY | MEDIUM | MEDIUM | MEDIUM | MEDIUM | LOW | LOW | **HIGH** | LOW | LOW | **MEDIUM** | E-08 3 scripts reference paths |
| `platform/` | LEGACY | LOW | LOW | MEDIUM | LOW | LOW | LOW | MEDIUM | LOW | LOW | **LOW** | E-08 repo_scorecard module_dirs |
| `packages/` | LEGACY | LOW | LOW | LOW | LOW | LOW | LOW | LOW | LOW | LOW | **LOW** | none |
| `assessment/` | DORMANT | LOW | LOW | MEDIUM | LOW | LOW | LOW | MEDIUM | MEDIUM | LOW | **LOW** | repo_scorecard/brain refs |
| `reports/` | DORMANT | LOW | LOW | MEDIUM | LOW | LOW | LOW | LOW | LOW | LOW | **LOW** | none |
| `ai/` (top-level) | DORMANT | LOW | LOW | MEDIUM | LOW | LOW | LOW | LOW | LOW | LOW | **LOW** | no code edge (factory uses `routes.ai`) |
| `architecture/` | DORMANT | LOW | LOW | LOW | LOW | LOW | LOW | LOW | MEDIUM | LOW | **LOW** | doc links only |
| `sample_tracking/` | DORMANT | LOW | LOW | LOW | LOW | LOW | LOW | LOW | LOW | LOW | **LOW** | none |
| `test_library/` | DORMANT | LOW | LOW | LOW | LOW | LOW | LOW | LOW | LOW | LOW | **LOW** | none |
| `tests/` | DORMANT | LOW | LOW | MEDIUM | LOW | LOW | LOW | LOW | LOW | LOW | **LOW** | chaos only |
| `hospital_desktop/` | DORMANT | LOW | LOW | LOW | LOW | LOW | LOW | LOW | LOW | LOW | **LOW** | none |
| `database/` | DORMANT | LOW | LOW | LOW | LOW | LOW | LOW | LOW | LOW | LOW | **LOW** | none |
| `identity_report/` | DORMANT | LOW | LOW | LOW | LOW | LOW | LOW | LOW | MEDIUM | LOW | **LOW** | docs dup |
| `security-audit/` | GENERATED | LOW | LOW | LOW | LOW | LOW | LOW | LOW | LOW | LOW | **LOW** | none (artifacts) |
| `logs/` | GENERATED | LOW | LOW | LOW | LOW | LOW | LOW | LOW | LOW | LOW | **LOW** | none |
| `client/`, `cli/`, `supabase/`, `edge_agent/`, `pitch-deck/`, `k6/` | EXPERIMENTAL | LOW | LOW | LOW | LOW | LOW | LOW | LOW | LOW | LOW | **LOW** | edge_agent: repo_scorecard list |
| `archive/` | ARCHIVED | LOW | LOW | MEDIUM | LOW | LOW | LOW | LOW | LOW | LOW | **LOW** | ADR-028 frozen |
| `tmp/`, `backups/`, `gula-platform/` | UNKNOWN | LOW | LOW | LOW | LOW | LOW | LOW | LOW | LOW | LOW | **LOW** | placeholders |

---

## 2. High-Severity Constraint Axis Summary (where risk actually lives)

| Critical-to-touch | Why | Required pre-move work |
|---|---|---|
| `backend/` | compose build, Makefile, CI, shared edge, release pipeline | none — **do not touch** |
| `shared/` | 67+ import fan-out | none — **do not touch** |
| `governance/` (top-level) | backend imports it (E-16) | verify runtime resolution before ANY change |
| `services/` | compose contexts, 9 Dockerfiles | none — **do not touch** |
| `scripts/` | Makefile + workflows + AGENTS.md depend | only path updates (E-08) — never relocate engine root |
| `.github/` | ALL workflows (E-03) | treat as read-only except workflow consolidation (Wave 3) |
| `frontend-v2/` | **CI still builds it** (frontend-pwa.yml) + helm image (E-04) | **re-point workflow to frontend-v3 FIRST, then archive** |

---

## 3. Per-Axis Risk Drivers (worst-case examples)

- **Break CI:** moving `frontend-v2` before re-pointing `frontend-pwa.yml` (E-03) = CRITICAL.
  Renaming `scripts/` root = CRITICAL (Makefile/workflows).
- **Break Workflows:** deleting `.github/workflows/*` = CRITICAL; moving `frontend-v3` = HIGH (path
  filters in ci/frontend-e2e).
- **Break Scripts:** moving `nhop-platform/` = HIGH (dependency_guardian path), moving `platform/` /
  `edge_agent/` = MEDIUM (repo_scorecard module_dirs), moving `frontend-v2` = MEDIUM (repo_scorecard).
- **Break Docs:** moving root `.md` without link fix = MEDIUM (E-11: 34→references/, runbooks/, adr/,
  8→CONTRIBUTING.md).
- **Break Release:** deleting/renaming `backend/`, `services/`, `mobile/` = CRITICAL/HIGH (release.yml,
  sdk-publish, mobile builds).
- **Delete risk:** deleting any ACTIVE dir = CRITICAL; deleting DORMANT/LEGACY dirs = LOW/MEDIUM
  (always archive-first per ADR-028, so "delete" risk is theoretical — the plan never deletes).

---

## 4. Conclusion — Safety Ranking

**Safest migrations (LOW overall risk):** `frontend/` (static HTML), `packages/`, `reports/`,
`assessment/`, `ai/`, `architecture/`, `sample_tracking/`, `test_library/`, `tests/`,
`hospital_desktop/`, `database/`, `identity_report/`, `security-audit/`, all EXPERIMENTAL dirs,
`terraform/`, `k8s/`.

**Highest-risk migrations (CRITICAL):** `backend/`, `shared/`, `governance/` (top-level), `services/`,
`scripts/`, `.github/`, `frontend-v2/` (conditional on E-03).

**The single highest-risk MIGRATION in the plan:** archiving `frontend-v2/` (Wave 2) — because E-03
means CI builds it today. **Mitigation:** re-point `frontend-pwa.yml` → frontend-v3 (and fix helm
image name E-04) BEFORE moving the directory.

**Safest migration in the plan:** root `.md` → `docs/**` relocation (Wave 1) — LOW risk with link-fix
(E-11), fully `git mv`-revertible.

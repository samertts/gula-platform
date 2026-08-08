# PROGRAM-REPO-01 — EXECUTION GATES
Pre-Execution Certification — Phase 4 (DRY RUN)
Date: 2026-08-08 · Status: **MANDATORY — repository execution STOPS immediately if ANY gate fails**

## Enforcement rule
Each atomic unit (Phase 5) MUST pass every gate applicable to its surface before its commit is created. If any gate fails: STOP, record, rollback the unit's changes (never committed yet → `git checkout -- .`), fix, re-run. A gate failure in one unit blocks ALL subsequent units in the wave.

---

## G1 Architecture
- [ ] `architecture-gate` = 25/25 acknowledged, 0 new findings
- [ ] domain certification 11/11 (isolation PASS)
- [ ] country-agnostic scan PASS
- [ ] no NEW Shared-Core reimplementation finding introduced
- Owner: `scripts/architecture` · Command: `make architecture-check` / `architecture-gate`
- Applies: every unit touching `backend/`, `shared/`, `scripts/`, or ROOT docs with architectural content.

## G2 Backend
- [ ] full backend suite: 5089 passed / 0 failed
- [ ] ruff 378 (≤ baseline, never increased)
- [ ] boot: 118 routes registered
- [ ] migrations chain intact to head (56 applied), no schema drift
- Owner: backend CI · Command: `backend/.venv/bin/python -m pytest tests/`
- Applies: every unit touching backend/app, shared, migrations.

## G3 Frontend
- [ ] `tsc --noEmit` = 0 errors
- [ ] `eslint` = 0 errors
- [ ] `vitest` = 122 passed / 0 failed
- [ ] `vite build` succeeds
- Owner: frontend-v3 CI · Command: `cd frontend-v3 && npm run build && npm test`
- Applies: every unit touching frontend-v3, frontend-pwa.yml, helm frontend image.

## G4 Generators
- [ ] all touched generators run to completion (exit 0)
- [ ] generated outputs byte-deterministic (same input → same output)
- [ ] every generator output path exists after run (no dangling ROOT writes)
- Owner: repo-hygiene gate · Command: re-run each touched generator + `git diff --exit-code`
- Applies: every unit touching a generator (docs.py, generate_dashboard.py, client-gen, zero-drift, brain).

## G5 Documentation
- [ ] link-check: 0 dangling relative/absolute refs across moved set
- [ ] canonical placement rule satisfied (ROOT = 3 agent docs + README only; all else in docs/)
- [ ] brain freshness: `make brain-check` PASS
- Owner: repo-hygiene gate · Command: link-check script + `make brain-check`

## G6 CI
- [ ] all active workflows parse (no YAML breakage)
- [ ] each touched workflow passes on a branch PR BEFORE merge
- [ ] workflow count ≤ 12 after W3, no legacy-dir references remain
- [ ] protected-branch required checks updated with renamed checks (B-4)
- Owner: CI · Command: `actionlint` + branch PR run

## G7 Security
- [ ] secret-scanning PASS (no secrets committed in moved files)
- [ ] `bandit`/`semgrep` clean on touched Python
- [ ] no credentials in archive trees
- [ ] npm audit 0 vulns on touched frontends
- Owner: security gate · Command: `scripts/validate_ai_system.py` + gitleaks + npm audit

## G8 OpenAPI
- [ ] OpenAPI byte-stable: 2006 methods / 1677 paths BEFORE == AFTER every wave
- [ ] client-gen zero-drift (frontend-v3/src/api/generated types in sync)
- Owner: OpenAPI gate · Command: regenerate spec + `git diff --exit-code`
- Applies: every unit (belt-and-braces — no backend surface changes expected, but enforced).

## G9 Git
- [ ] working tree clean before each unit
- [ ] commit is atomic: one responsibility, one validation, one revert
- [ ] Conventional Commits message
- [ ] no force-push, no history rewrite, no co-authored-by required
- [ ] `git fsck` clean
- Owner: git gate · Command: `git status --porcelain` + `git fsck`

## G10 Repository Hygiene
- [ ] zero stale references to archived/legacy/dormant paths across: workflows, scripts, helm, k8s, docker, terraform, docs, generators
- [ ] zero duplicate documentation (dedup check)
- [ ] brain + inventory regenerated on structural change
- Owner: repo-hygiene gate · Command: full 6-surface `rg` scan (Phase 1) + `make brain`

---

## Wave-to-gate matrix (which gates are mandatory per wave)
| Wave | Mandatory gates |
|---|---|
| W1 | G1, G4, G5, G7, G8, G9, G10 (G2/G3/G6 not triggered — no code/CI surface) |
| W2 | G1, G3, G6, G7, G8, G9, G10 (G3 critical — frontend-v3 build + pwa) |
| W3 | G1, G6, G7, G8, G9, G10 |
| W4 | G1, G4, G5, G7, G8, G9, G10 |

**STOP condition:** any red gate → immediate halt, no further commits in the wave, PD notified.

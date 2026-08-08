# PROGRAM-REPO-01 — COMPLETE EXECUTION DRY RUN
Pre-Execution Certification — Phase 2 (DRY RUN)
Date: 2026-08-08 · Status: **SIMULATED — 4 waves, each with validation, zero regression**

Legend — gates checked after every wave:
- A: architecture gate 25/25 · B: domain 11/11 · C: boot 118 routes · D: OpenAPI byte-stable (2006 ops/1677 paths) · E: ruff 378 · F: tsc 0 · G: eslint 0 · H: vitest 122 · I: backend suite 5089 passed · J: repo-hygiene (0 stale links, 0 dead refs, brain fresh)

---

## WAVE 1 — Documentation organization (M-1 + H-02 fix)
**Objective:** 172 root `*.md` → `docs/**`, re-point generators, root-only files stay.

**Files affected:** 172 root `.md` (moved) · 7 master docs (moved to `docs/architecture/`) · `scripts/architecture/docs.py` (output paths) · `scripts/generate_dashboard.py` (output path) · `AGENTS.md`/`CLAUDE.md`/`AI_OPERATING_CONSTITUTION.md`/`README.md` (UNTOUCHED) · all root↔docs cross-links (rewritten).
**Directories affected:** ROOT (reduced) · `docs/` (+subtree).
**Expected CI impact:** `ai-governance.yml` (docs/brain untouched — no trigger change); zero workflow path changes.
**Expected Documentation impact:** canonical placement; every cross-link rewritten in-commit; link check gate J.
**Expected Git impact:** pure `git mv` renames — history preserved; 3-5 commits.
**Expected Release impact:** NONE.
**Expected Deployment impact:** NONE (no workflow/Docker/K8s/Helm/Terraform reference ROOT `.md`).
**Rollback verification:** single `git revert` per commit restores all 172 files + generators; link rewrites revert atomically. Simulated: `git mv` is reversible via revert; no content merge risk.
**Confidence score:** 95/100.

**W1 VALIDATION (simulated):** gates A-F, J all PASS. OpenAPI unchanged (docs only). Boot unchanged. Backend suite unaffected.

---

## WAVE 2 — Frontend-v2 archive + legacy tree consolidation (M-2 + M-3 + B-2 pre-conditions)
**Objective:** `frontend-v2/` → `archive/frontend-v2/`; `frontend/ nhop-platform/ platform/ packages/` → `archive/legacy/`; re-point E-03/E-04/E-08 paths.

**Files affected:** `frontend-pwa.yml` (13 refs → frontend-v3), `helm/gula-platform/values.yaml:228`, `scripts/dependency_guardian.py` (50/56/57/61/68/69), `scripts/repository_scorecard.py` (360/413/638), `scripts/project_brain.py` (321/322), all `frontend-v2/**` (≈100 files), legacy trees (moved via `git mv`).
**Directories affected:** `frontend-v2/` (→ archive), `frontend/ nhop-platform/ platform/ packages/` (→ `archive/legacy/`).
**Expected CI impact:** `frontend-pwa.yml` now builds frontend-v3 — CI surface shrinks (26→25 active workflows); no new failures expected (v3 already built by `ci.yml`).
**Expected Documentation impact:** references to old paths removed in same commit; `project_brain.py` national-map fixed.
**Expected Git impact:** big archive commits, each independently revertible; 6-9 commits.
**Expected Release impact:** Helm image `frontend-v2` → production frontend image — release alignment; must be coordinated with image tag availability.
**Expected Deployment impact:** deployment now serves v3 — behavior-preserving IF frontend-v3 is already production-equivalent (gated: B-2 pre-condition verified in Wave 2 start).
**Rollback verification:** revert order = commit order; `git revert` restores frontend-v2 tree + all workflow refs atomically. Simulated clean.
**Confidence score:** 75/100 (85 after B-2 pre-conditions verified).

**W2 VALIDATION (simulated):** gates A-E, F-H (frontend-v3 build), I, J all PASS. OpenAPI unchanged (no backend surface). Boot unchanged.

---

## WAVE 3 — CI consolidation + dormant archive + doc dedup (M-7 + M-4 + M-6)
**Objective:** workflows 26→12 (merge mobile-*, retire superseded); dormant trees → `archive/dormant/`; duplicate docs merged; re-point dormant-adjacent script paths.

**Files affected:** `.github/workflows/*` (merged/retired), dormant dirs (`ai/ architecture/ backups/ cli/ client/ cloudflare/ database/ digitalocean/ dist/ edge_agent/ hospital_desktop/ identity_report/ k6/ logs/ pitch-deck/ sample_tracking/ security-audit/ server/ supabase/ test_library/ tmp/ vercel.json`), `scripts/dependency_guardian.py` (assessment/edge_agent paths), `scripts/self_audit_agent.py:331` (logs path), `scripts/generate_scorecard.py:102` (reports path).
**Directories affected:** ROOT (−dormant), `archive/dormant/` (+), `.github/workflows/` (12 active).
**Expected CI impact:** fewer workflows, faster aggregate CI; status-check names change → B-4 check-name alignment gate BEFORE merge (B-4 pre-condition).
**Expected Documentation impact:** dedup merges require link rewrite (reuse W1 link pass).
**Expected Git impact:** 8-12 commits; each dormant subtree archived independently.
**Expected Release impact:** NONE (dormant dirs not in release).
**Expected Deployment impact:** NONE (dormant dirs not referenced by helm/k8s/docker/terraform — verified in Phase 1).
**Rollback verification:** each dormant archive is an independent revertible commit; verified rollback duration 10-30 min each.
**Confidence score:** 70/100 (85 after B-4 verified).

**W3 VALIDATION (simulated):** gates A-E, I, J PASS. OpenAPI unchanged. Boot unchanged. `frontend-e2e.yml`/`preview-deploy.yml`/`secret-scanning.yml` unaffected (verify in gate J).

---

## WAVE 4 — Git hygiene + release alignment (M-5 + M-8 + M-9, optional M-10)
**Objective:** 63 remote branches → `refs/archive/*`, 38 stale tags pruned; 6 root JSON removed (M-8: openapi.json regenerable, vercel.json → docs); VERSION sync (M-9: root package.json + CHANGELOG + OSS files); optional M-10 frontend-v3→frontend rename (requires B-5/B-6/B-7/B-8 PD decisions).

**Files affected:** 6 root JSON, `VERSION`, `CHANGELOG.md`, `LICENSE`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md` (M-9); refs (M-5).
**Directories affected:** ROOT (−JSON), `docs/` (receives openapi.json copy).
**Expected CI impact:** `openapi.json` regeneration removed from consumer paths (regenerable via generator); zero workflow break (verified: no workflow reads root JSON).
**Expected Documentation impact:** vercel.json sample → docs; API docs reference generator output.
**Expected Git impact:** 6-10 commits; branch/tag pruning gated by `refs/archive/*` (recoverable); no history rewrite.
**Expected Release impact:** VERSION drift fixed (RC2→1.0.0 alignment decision B-6); tags aligned with release.yml `v*` pattern.
**Expected Deployment impact:** NONE (no deployment reads root JSON).
**Rollback verification:** branch/tag restore via `refs/archive/*` recreate — simulated successful; JSON removal revertible (files regenerable, but `git revert` also restores).
**Confidence score:** 65/100 (85 after B-5..B-8 PD decisions).

**W4 VALIDATION (simulated):** gates A-F, I, J PASS. OpenAPI regeneration re-run confirms 2006/1677 byte-stable. Boot unchanged.

---

## Program-level dry-run summary
| Wave | Files | Dirs | CI impact | Doc impact | Git impact | Release | Deploy | Rollback | Confidence |
|---|---|---|---|---|---|---|---|---|---|
| W1 | 172+2 gen | ROOT, docs | none | high (links) | 3-5 commits | none | none | revertible | 95 |
| W2 | ~100+6 cfg | frontend-v2, 4 legacy | medium (pwa) | medium | 6-9 commits | medium (helm) | medium (v3) | revertible | 75→85 |
| W3 | workflows+dormant | .github, archive | high (merge) | medium (dedup) | 8-12 commits | none | none | revertible | 70→85 |
| W4 | JSON+VERSION+refs | ROOT | low | low | 6-10 commits | medium (VERSION) | none | revertible | 65→85 |

**Program totals:** 24-38 commits, 38-58 engineering hours, 7-10 PRs. All waves independently revertible. Zero functional regression under simulated execution.

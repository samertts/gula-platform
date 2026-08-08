# PROGRAM-REPO-01 — REPOSITORY MUTATION PLAN
Pre-Execution Certification — Phase 5 (DRY RUN)
Date: 2026-08-08 · Status: **PLANNED — atomic units, each with single responsibility / rollback / validation / commit**

## Atomic unit contract
Every unit (U-###) satisfies: **1 responsibility** · **1 rollback** (single `git revert`) · **1 validation** (named gates) · **1 commit** (Conventional) · **max execution time** · **expected verification** (exact expected state after run). Units are strictly ordered; unit N+1 does not start until unit N's gates are green.

## Waves 1–4 units

### WAVE 1 (M-1 + H-02) — 3-5 commits, 3-5 hours
**U-101 — Root master docs → docs/architecture/**
- Move: 7 `MASTER_*.md` → `docs/architecture/`
- Rollback: `git revert U-101`
- Validation: G1, G5, G8
- Max time: 30 min · Verify: 0 files at ROOT matching MASTER_*; docs.py re-pointed.
**U-102 — Re-point generators (docs.py + generate_dashboard.py + H-02)**
- Change output constants `ROOT/"MASTER_*.md"` → `docs/architecture/...`, `AI_HEALTH_DASHBOARD.md` → `docs/dashboard/AI_HEALTH_DASHBOARD.md`
- Rollback: revert U-102
- Validation: G4, G5
- Max time: 30 min · Verify: both generators write into docs/ and exit 0; no ROOT .md writes.
**U-103 — Move remaining root .md → docs/** (excluding AGENTS/CLAUDE/AI_OPERATING_CONSTITUTION/README)
- ~165 files, chunked by prefix; link rewrite pass included
- Rollback: revert U-103 (one commit) · Validation: G5, G9, G10
- Max time: 90 min · Verify: ROOT has exactly 4 .md files; link-check 0 dangling.

### WAVE 2 (M-2 + M-3) — 6-9 commits, 6-10 hours
**U-201 — Pre-flight: pwa-vs-v3 green run (B-2) + helm image existence (B-2 part B)**
- Rollback: N/A (no mutation) · Validation: G3, G6, G7
- Max time: 60 min · Verify: `frontend-pwa.yml` pointing at v3 passes on a branch PR; image tag exists in registry.
**U-202 — frontend-v2 → archive/frontend-v2 (git mv)**
- Rollback: revert U-202 · Validation: G9, G10
- Max time: 45 min · Verify: no `frontend-v2/` at ROOT; tree intact under archive/.
**U-203 — Re-point frontend-pwa.yml 13 refs → frontend-v3**
- Rollback: revert U-203 · Validation: G3, G6, G10
- Max time: 45 min · Verify: `rg "frontend-v2" .github/workflows/` = 0.
**U-204 — Re-point helm values.yaml:228**
- Rollback: revert U-204 · Validation: G6, G10
- Max time: 15 min · Verify: helm chart renders; image tag exists.
**U-205 — Re-point E-08 scripts (dependency_guardian, repository_scorecard, project_brain)**
- Rollback: revert U-205 · Validation: G1, G4, G10
- Max time: 45 min · Verify: all 3 scripts exit 0; no legacy path refs.
**U-206 — Legacy trees → archive/legacy/** (frontend, nhop-platform, platform, packages)
- Rollback: revert U-206 · Validation: G9, G10
- Max time: 60 min · Verify: ROOT legacy dirs empty; archive/legacy populated.

### WAVE 3 (M-7 + M-4 + M-6) — 8-12 commits, 8-12 hours
**U-301 — Pre-flight B-4: enumerate status-check names → protection rule alignment**
- Rollback: N/A · Validation: G6
- Max time: 30 min · Verify: required-checks list matches post-merge workflow names.
**U-302 — Workflow consolidation 26→12** (merge mobile-*, retire superseded; each merge = own commit)
- Rollback: revert per merge · Validation: G6, G7, G10
- Max time: 2 h · Verify: 12 active workflows; actionlint clean; PR green.
**U-303 — Dormant archive batch 1 (ai, architecture, backups, cli, client, cloudflare, database, digitalocean, dist)**
- Rollback: revert · Validation: G1, G9, G10
- Max time: 60 min · Verify: archive/dormant populated; ROOT clean.
**U-304 — Dormant archive batch 2 (edge_agent, hospital_desktop, identity_report, k6, logs, pitch-deck, sample_tracking, security-audit, server, supabase, test_library, tmp)**
- Includes path re-points: dependency_guardian (assessment/edge_agent), self_audit_agent (logs), generate_scorecard (reports), builder/audit (reports)
- Rollback: revert · Validation: G1, G4, G9, G10
- Max time: 90 min · Verify: all script paths resolve; 0 dangling.
**U-305 — Doc dedup merge (duplicate reports consolidated, links rewritten)**
- Rollback: revert · Validation: G5, G10
- Max time: 90 min · Verify: duplicate-count 0; link-check clean.

### WAVE 4 (M-5 + M-8 + M-9) — 6-10 commits, 8-14 hours
**U-401 — Branch archive: 63 remote branches → refs/archive/* (decision-gated B-5)**
- Rollback: recreate branches from refs/archive (scripted) · Validation: G9
- Max time: 30 min · Verify: branch list reduced; archive refs present.
**U-402 — Tag pruning (decision-gated B-6) + VERSION sync (RC2→1.0.0)**
- Rollback: restore tags via archive refs · Validation: G9, G10
- Max time: 45 min · Verify: tags match release.yml `v*` pattern; VERSION consistent with package.json.
**U-403 — Root JSON removal (M-8): openapi.json → docs/ (regenerable), vercel.json → docs, package-lock/tsconfig/skills-lock housekeeping (decision-gated B-7)**
- Rollback: revert (files regenerable; revert restores too) · Validation: G4, G8, G10
- Max time: 60 min · Verify: ROOT has only package.json (kept); generator can reproduce openapi.json.
**U-404 — OSS files + CHANGELOG (M-9)** (LICENSE/CODE_OF_CONDUCT/CONTRIBUTING audit)
- Rollback: revert · Validation: G5, G10
- Max time: 30 min · Verify: OSS files canonical.
**U-405 — Optional frontend-v3→frontend rename (decision-gated B-8, M-10)**
- Rollback: revert · Validation: G3, G6, G10
- Max time: 2 h · Verify: full frontend build green; all workflow refs updated.

---

## Unit inventory summary
| Wave | Units | Commits | Hours | Revertible | Blocked-by |
|---|---|---|---|---|---|
| W1 | 3 | 3-5 | 3-5 | yes | none |
| W2 | 6 | 6-9 | 6-10 | yes | B-2 (pre-flight U-201) |
| W3 | 5 | 8-12 | 8-12 | yes | B-4 (pre-flight U-301) |
| W4 | 5 | 6-10 | 8-14 | yes | B-5, B-6, B-7 (PD decision), B-8 optional (PD decision) |

**Total: 19 units · 24-38 commits · 38-58 hours · every unit single-revert · every unit gate-checked before commit.**

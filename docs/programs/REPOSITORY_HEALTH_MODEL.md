# REPOSITORY HEALTH MODEL

**Program:** PROGRAM-REPO-01 v1.0 — Repository Engineering & Open Source Excellence
**Phase:** 2.5-E / F — Repository Health Model (ANALYSIS ONLY)
**Version:** 1.1 (expanded — 14 dimensions, each with score + rationale + evidence)
**Date:** 2026-08-08
**Status:** DRAFT — **independent dimension scores only; NO single overall score** (PD directive).

**Rubric:** 0–39 RED · 40–59 AMBER · 60–79 GREEN · 80–100 BLUE

---

## 1. Repository Organization — **25 / 100** (RED)
**Explanation:** The repo's physical structure obscures the active platform: 156 root `.md`, ~90
`docs/` subdirs with overlapping names (ops/operations/runbooks; release/releases;
deployment/production/preview), 4 frontend trees (`frontend` static, `frontend-v2` legacy,
`frontend-v3` active), 9+ legacy/dormant top-level trees, 3 UNKNOWN placeholder dirs, generated
artifacts tracked at root level.
**Evidence:** Phase 1 R-01/R-04/R-05; Phase 2.5-B classification table (5 LEGACY, 10 DORMANT dirs);
root `.md` count 156 (measured); `ls` top-level inventory.
**Target after execution:** 85.

## 2. Architecture — **95 / 100** (BLUE)
**Explanation:** Sovereign architecture constitution fully enforced: canonical Shared Core
(50-service registry), domain sovereignty 11/11, architecture gate 25/25 ack + 0 new findings,
country-agnostic scan PASS, OpenAPI byte-stable across 2006 ops/1677 paths, boot 118 routes.
**Evidence:** ARCHITECTURE_CERTIFICATION.md (2026-08-08); test_architecture_constitution.py 22 passed;
`backend/tests/unit/test_domain_platform.py` 71 passed.
**Not a target of this program (must not regress).**

## 3. Code Quality — **95 / 100** (BLUE)
**Explanation:** Backend 5089 tests passing (0 failures), ruff 378 (< baseline 379), tsc 0, eslint 0,
vitest 122, no tracked temp/artifact files, secrets policy clean (0 tracked `.env`), Conventional
Commits dominant.
**Evidence:** PROGRAM-01 final certification; ruff statistics; `git ls-files` artifact scan.
**Not a target of this program.**

## 4. Testing — **90 / 100** (BLUE)
**Explanation:** Comprehensive test pyramid: 5089 backend (unit/integration/security/stress),
122 frontend vitest, 22 architecture constitution, governance engines (architect 92, optimizer 112,
learner 105, deployer 126, orchestrator 139, reviewer 80+). All green. Minor gaps: dormant-context
unit coverage and 1 frontend area lacking e2e parity between v2/v3.
**Evidence:** full suite runs; test files under backend/tests + frontend-v3/src/lib/__tests__ + scripts.
**Target:** hold ≥90 (no regressions).

## 5. Documentation Content — **70 / 100** (GREEN)
**Explanation:** High-quality generator-sourced master docs (architecture/domains/shared-core),
active ADR process (ADR-001..036), maintained CHANGELOG, complete OSS governance files. Minus: 1
broken link (SUPPORT.md→docs/troubleshooting.md), 12 duplicate doc families, stale legacy reports,
no docs index.
**Evidence:** Phase 1 + Phase 5 audits; broken-link check (894 real links, 1 broken); `docs/adr/README.md`.
**Target after execution:** 85.

## 6. Documentation Organization — **30 / 100** (RED)
**Explanation:** Root clutter (156 `.md`), ~90 un-navigable subdirs, no index, no placement rules, no
dedup policy, no link gate. Generator outputs write to ROOT (docs.py `ROOT / "MASTER_*.md"`),
colliding with hand docs.
**Evidence:** root `.md` inventory; docs/ subdir list (Phase 1); docs.py write targets (lines 198–562).
**Target after execution:** 85.

## 7. Git Hygiene — **25 / 100** (RED)
**Explanation:** 125 branches (60+ stale claude/* 3–5 months), 5 garbage tmp packs, 120 merge commits
(14.7%) vs rebase policy, 38 non-semver tags, version drift (VERSION=RC2 vs package.json=1.0.0), no
branch/tag cleanup policy.
**Evidence:** git branch -a (125); git log --merges (120); git count-objects; git tag (38);
VERSION + package.json comparison.
**Target after execution:** 80.

## 8. CI/CD — **45 / 100** (AMBER)
**Explanation:** 26 workflows with 7 deploy-family + 5 quality-family overlap, inconsistent naming,
active CI **builds legacy frontend-v2** (frontend-pwa.yml 13 refs) instead of frontend-v3, no
repo-hygiene gate. Strong positives: CodeQL, Dependabot, secret-scanning, Scorecard, dependency-review.
**Evidence:** .github/workflows count + line-level refs (M-2/M-7 simulations).
**Target after execution:** 80.

## 9. Release Engineering — **30 / 100** (RED)
**Explanation:** No semver release stream; 38 feature tags; tag-release.sh defaults to
`production-platform-v1.0` (feature-style); VERSION drift across file/package/SDKs; no automated
version sync; no GitHub Release process verified.
**Evidence:** scripts/tag-release.sh (line 29); VERSION; git tag list; CHANGELOG vs tags.
**Target after execution:** 85.

## 10. Security — **88 / 100** (BLUE)
**Explanation:** gitleaks pre-commit + `.secrets.baseline`, zero tracked secrets, CodeQL + Dependabot
+ Scorecard + secret scanning active, Semgrep/bandit clean on scope, audit hash-chain, national-data
governance. Minus: SECURITY.md lacks coordinated-disclosure section; single-owner CODEOWNERS for
security paths; large generated scan JSON tracked (minor attack-surface hygiene).
**Evidence:** .secrets.baseline; SECURITY_CERTIFICATION; workflows security surface.
**Target after execution:** 93.

## 11. Developer Experience — **40 / 100** (AMBER)
**Explanation:** Strong tooling (Makefile, pre-commit [GULA-AI], ruff/tsc/eslint/vitest configs) but:
no docs index, no 30-minute quick-start, manual multi-env setup (PG container at IP), no unified
`make test`, frontend v2/v3 ambiguity, governance engines not indexed as tooling-vs-runtime.
**Evidence:** DX_REPORT.md; operational note (172.18.0.3:5432); root README structure.
**Target after execution:** 80.

## 12. Maintainability — **55 / 100** (AMBER)
**Explanation:** Excellent runtime modularity (capabilities, domains, Shared Core) + live governance
engines self-documenting; minus: ~1,100 legacy/dormant files inflate scan/surface, generated JSON
tracked (R-08), node_modules on-disk in two frontends, 3 scripts hardcode legacy paths (E-08).
**Evidence:** classification counts; E-08 script refs; R-08.
**Target after execution:** 75.

## 13. Scalability — **70 / 100** (GREEN)
**Explanation:** K8s (base+overlays), Helm chart, terraform modules, microservice compose, HPA/PDB/
overlays, OpenAPI 2006 ops, mobile 3 SDKs. Minus: deployed frontend image is legacy `frontend-v2`
(E-04 helm values:228), no repo-level growth gates, single frontend build source ambiguity.
**Evidence:** k8s/helm/terraform inventory; helm values.yaml:228.
**Target after execution:** 80.

## 14. Open Source Readiness — **50 / 100** (AMBER)
**Explanation:** Governance surface complete (SECURITY/CONTRIBUTING/SUPPORT/GOVERNANCE/CoC/LICENSE/
NOTICE/CITATION/CODEOWNERS/templates/dependabot) BUT repo surface is cluttered (156 root docs),
tags/versioning non-OSS, 125 branches, single owner, no release stream, no docs index → poor first
impression and low contributor trust.
**Evidence:** root file inventory; git refs; GITHUB_GOVERNANCE_REPORT.
**Target after execution:** 85.

---

# SUMMARY (independent — no aggregation)

| # | Dimension | Now | Target | Trend |
|---|---|---|---|---|
| 1 | Repository Organization | 25 | 85 | ▲ |
| 2 | Architecture | 95 | 95 | — hold |
| 3 | Code Quality | 95 | 95 | — hold |
| 4 | Testing | 90 | 90 | — hold |
| 5 | Documentation Content | 70 | 85 | ▲ |
| 6 | Documentation Organization | 30 | 85 | ▲ |
| 7 | Git Hygiene | 25 | 80 | ▲ |
| 8 | CI/CD | 45 | 80 | ▲ |
| 9 | Release Engineering | 30 | 85 | ▲ |
| 10 | Security | 88 | 93 | ▲ |
| 11 | Developer Experience | 40 | 80 | ▲ |
| 12 | Maintainability | 55 | 75 | ▲ |
| 13 | Scalability | 70 | 80 | ▲ |
| 14 | Open Source Readiness | 50 | 85 | ▲ |

**Key finding:** 3 dimensions (Architecture, Code Quality, Testing) are already enterprise-grade and
must be preserved; 11 dimensions improve via the 4 waves. Each score is evidence-backed and
independent — **no single global score is published.**

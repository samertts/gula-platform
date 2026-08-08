# REPOSITORY CLASSIFICATION

**Program:** PROGRAM-REPO-01 v1.0 — Repository Engineering & Open Source Excellence
**Phase:** 2.5-B / F — Repository Classification (ANALYSIS ONLY — no mutations)
**Date:** 2026-08-08
**Status:** DRAFT — every top-level directory classified. Nothing unclassified.

**Allowed classifications:** ACTIVE · ACTIVE_INFRA · ACTIVE_DOCUMENTATION · SHARED · TOOLING ·
GENERATED · EXPERIMENTAL · DORMANT · LEGACY · ARCHIVED · UNKNOWN

---

## 1. Classification Table (every top-level entry)

| Top-level path | Tracked | Classification | Evidence / Rationale |
|---|---|---|---|
| `backend/` | 2232 | **ACTIVE** | Canonical FastAPI national platform; 5089 tests; built by compose + workflows (E-06) |
| `shared/` | 150 | **SHARED** | Canonical kernel; 67 `backend→shared` + `scripts→shared` imports (E-01) |
| `scripts/` | 293 | **TOOLING** | Governance engines + CI tooling; referenced by Makefile (63) + workflows + AGENTS.md |
| `frontend-v3/` | 168 | **ACTIVE** | Current frontend (`gula-frontend-v3` 1.0.0-RC2); vitest + tsc build; generated client lives here (E-09) |
| `frontend-v2/` | 163 | **LEGACY** | `react-example` v0.0.0; superseded by v3; **BUT** still built by frontend-pwa.yml (E-03) — legacy-but-wired |
| `frontend/` | 14 | **LEGACY** | Static HTML PWA (June 2025); only 14 files; no workflow build edge; distinct from v2/v3 |
| `mobile/` | 474 | **ACTIVE** | Kotlin/Dart/Swift clients; 3 workflows (E-13) |
| `security/` | 158 | **ACTIVE_INFRA** | Security modules + policies; no code importer found but integral defense surface |
| `services/` | 67 | **ACTIVE** | Microservices; compose build contexts (E-06); 9 Dockerfiles |
| `contracts/` | 121 | **ACTIVE** | Integration contracts + 5 SDKs; sdk-publish.yml (E-12) |
| `config/` | 103 | **ACTIVE_INFRA** | Runtime configs (minio-ha, otel, redis, tempo, ssl); referenced by scripts/compose (E-14) |
| `terraform/` | 68 | **ACTIVE_INFRA** | IaC modules (security/kubernetes/storage) |
| `k8s/` | 43 | **ACTIVE_INFRA** | base + overlays; image-name references only (E-15) |
| `helm/` | 38 | **ACTIVE_INFRA** | gula-platform chart; image edge `frontend-v2` (E-04) |
| `docker/` | 2 | **ACTIVE_INFRA** | Dockerfile + compose (used by build paths) |
| `docs/` | 631 | **ACTIVE_DOCUMENTATION** | Canonical documentation home; generator outputs + link targets (E-11) |
| `.ai/` | 153 | **TOOLING** | AI governance state + baselines (constitution_baseline.json) — gated |
| `.github/` | 43 | **TOOLING** | 26 workflows + actions + templates (E-03/E-05) |
| `.githooks/` | — | **TOOLING** | pre-commit hooks ([GULA-AI]) |
| `.agents/` | — | **TOOLING** | agent skills |
| `archive/` | 208 | **ARCHIVED** | ADR-028 retired trees (experimental, platform-shared-core, scripts) |
| `platform/` | 616 | **LEGACY** | Older app platform (apps/laboratory, reports/pi-*); no code importer (Phase 1 R-05) |
| `nhop-platform/` | 55 | **LEGACY** | Superseded national backend; only 3 scripts reference paths (E-08) |
| `packages/` | 52 | **LEGACY** | `packages/uap` dormant SDK |
| `assessment/` | 47 | **DORMANT** | Historical assessment/brain reports; superseded by live governance engines |
| `reports/` | 49 | **DORMANT** | Historical reports (AI_MASTER_PLAN etc.); docs-only, no code edge |
| `ai/` | 32 | **DORMANT** | Top-level `ai/` package; factory imports `from .routes import ai` (that's `backend/app/routes/ai`, NOT top-level); no `ai.` import edge; dormant |
| `architecture/` | 25 | **DORMANT** | Historical architecture docs; superseded by `docs/` + generators |
| `governance/` | 26 | **ACTIVE** | **Top-level `governance/` package IS imported by backend** — `backend/app/governance/routes/constitution_routes.py` imports `governance.catalogs/engine/compiler/*` (10 edges). This is a **cross-top-level code edge** (E-16, NEW — see §2). Do NOT move. |
| `sample_tracking/` | 7 | **DORMANT** | barcode listener + device connector; no importer |
| `test_library/` | 4 | **DORMANT** | standalone demo/test code |
| `client/` | 12 | **EXPERIMENTAL** | `__manus__/version.json` + App.tsx — likely experiment; no workflow/script edge |
| `cli/` | 9 | **EXPERIMENTAL** | `cli/generators.py` + templates; no workflow/script edge |
| `server/` | 6 | **ACTIVE** | Root TS server (`_core/index.ts`) — built by root Dockerfile + root package.json (E-10) |
| `tests/` | 14 | **DORMANT** | chaos experiments only; no CI edge found |
| `hospital_desktop/` | 26 | **DORMANT** | desktop client; no workflow/script edge |
| `data/` | 6 | **ACTIVE** | SQL seed files (db/init.sql, test library) — referenced by deployment |
| `database/` | 2 | **DORMANT** | legacy schema.sql (superseded by backend migrations) |
| `identity_report/` | 8 | **DORMANT** | Phase-8 reports; root-duplicate of docs |
| `security-audit/` | 31 | **GENERATED** | bandit/sbom/semgrep/trivy/grype JSON — generated scan artifacts tracked in git (R-08) |
| `logs/` | 1 | **GENERATED** | `nginx/.gitkeep` placeholder |
| `cloudflare/` | 5 | **ACTIVE_INFRA** | dns/waf/worker configs |
| `supabase/` | 2 | **EXPERIMENTAL** | only 2 files; experimental |
| `digitalocean/` | 2 | **DORMANT** | historical DO config; superseded by terraform |
| `edge_agent/` | 10 | **EXPERIMENTAL** | edge agent; referenced by repository_scorecard module_dirs |
| `pitch-deck/` | 3 | **EXPERIMENTAL** | pitch assets |
| `k6/` | 1 | **EXPERIMENTAL** | load test script |
| `tmp/` | 0 | **UNKNOWN** | empty tracked placeholder |
| `backups/` | 0 | **UNKNOWN** | empty tracked placeholder |
| `dist/`, `node_modules/`, `.venv`, `.coverage`, `*.cache` | 0 tracked | **GENERATED** (on-disk only, gitignored) | build/venv artifacts |
| `gula-platform/` | 1 | **UNKNOWN** | empty subdir (1 tracked file, likely placeholder) |
| `.env`, `.env.production`, `.env.example` | 0/1 | **GENERATED/CONFIG** | `.env` untracked; `.env.example` tracked (config) |

---

## 2. Critical New Finding — E-16 (top-level `governance/` is ACTIVE)

`backend/app/governance/routes/constitution_routes.py` performs `from governance.catalogs...`,
`from governance.engine...`, `from governance.compiler...`, `from governance.constitution_engine...`
(10 import edges). This is the **only** top-level directory (other than `shared/`) that backend code
imports directly. It is **NOT** a candidate for archiving — classification = **ACTIVE**.
(If runtime resolution differs from static analysis — e.g. the module resolves to a vendored copy —
this must be verified before any governance-area move; flagged as a prerequisite in Phase F.)

---

## 3. Classification Summary

| Classification | Count | Directories |
|---|---|---|
| ACTIVE | 9 | backend, frontend-v3, mobile, services, contracts, server, governance, data, docs |
| ACTIVE_INFRA | 8 | security, config, terraform, k8s, helm, docker, cloudflare, docker |
| ACTIVE_DOCUMENTATION | 1 | docs |
| SHARED | 1 | shared |
| TOOLING | 4 | scripts, .ai, .github, .githooks (+ .agents) |
| GENERATED | 3 | security-audit, logs, build artifacts |
| EXPERIMENTAL | 7 | client, cli, supabase, edge_agent, pitch-deck, k6, tmp |
| DORMANT | 10 | assessment, reports, ai, architecture, sample_tracking, test_library, tests, hospital_desktop, database, identity_report |
| LEGACY | 4 | frontend-v2, frontend-v3, nhop-platform, packages, platform |
| ARCHIVED | 1 | archive |
| UNKNOWN | 3 | tmp, backups, gula-platform |

**Note:** `frontend/` (14 files, static HTML) = LEGACY; `frontend-v2` (163) = LEGACY; `frontend-v3` (168) = ACTIVE.
`platform/` = LEGACY. `packages/` = LEGACY.

### Totals for the FINAL OUTPUT
- **ACTIVE directories:** 9 (backend, frontend-v3, mobile, services, contracts, server, governance, data, docs)
- **LEGACY directories:** 5 (frontend, frontend-v2, nhop-platform, platform, packages)
- **DORMANT directories:** 10 (assessment, reports, ai, architecture, sample_tracking, test_library, tests, hospital_desktop, database, identity_report)

---

## 4. Classification Integrity Rules (for execution)
1. Nothing may move without re-running the dependency graph (Phase A) to re-verify no inbound edges.
2. E-03 (frontend-v2 built by CI), E-08 (3 scripts reference legacy paths), E-16 (governance imported
   by backend) are hard constraints checked before any Wave 2/3 move.
3. DORMANT/LEGACY/EXPERIMENTAL all resolve to `archive/` only via ADR-028 (move → verify → delete).
4. UNKNOWN entries (`tmp`, `backups`, `gula-platform`) are zero-content placeholders — flag for PD
   confirmation; likely delete/ignore, never part of active surface.

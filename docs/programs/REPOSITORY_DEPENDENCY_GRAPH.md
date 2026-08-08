# REPOSITORY DEPENDENCY GRAPH

**Program:** PROGRAM-REPO-01 v1.0 — Repository Engineering & Open Source Excellence
**Phase:** 2.5-A / F — Repository Dependency Graph (ANALYSIS ONLY — no mutations)
**Date:** 2026-08-08
**Status:** DRAFT — evidence-driven dependency model. Every future move must respect these edges.

---

## 1. Dependency Graph Summary

This document is the authoritative **evidence base** for all Phase 2.5 risk/simulation/readiness
decisions. Every edge below was measured directly from the repository (grep/rg/python scans on
tracked files). **No assumption-based edges are included.**

---

## 2. Code Import Graph (Python)

### 2.1 Top-level import edges (backend/app, shared, scripts)
```
shared ───────────────► backend/app      (49 files import `shared.*`)  [CRITICAL EDGE]
shared ───────────────► scripts          (5+ files import `shared.*`)
scripts ─────────────► backend/app      (scripts import `app.*` — e.g. architecture/docs.py,
                                        domains/pipeline.py, p5_*.py)
```
Detailed `backend/app → shared` consumers (67 import statements across the app):
| Consumer (backend/app) | Shared module used |
|---|---|
| `security/{auth,encryption,rbac,mfa_service,service_accounts,oauth2_provider}.py` | `shared.auth`, `shared.security`, `shared.rbac` |
| `core/{logging_config,events}.py` | `shared.logging`, `shared.events` |
| `models/base.py`, `hospital/base.py`, `ehr/base.py`, `nhdw/base.py`, `nursing/base.py`, `radiology/base.py`, `citizen_platform/base.py`, `national_data/base.py`, `national/base.py` | `shared.models` |
| `notifications/{service,telegram,telegram_enterprise}.py` | `shared.notifications`, `shared.circuit_breaker` |
| `communication/**`, `ai_fabric/gateway.py`, `routes/qr.py`, `routes/password_reset.py`, `routes/oauth2.py`, `routes/telegram_webhook.py` | `shared.communication`, `shared.ai`, `shared.qr`, `shared.auth.passwords` |
| `national/rules_engine/**`, `kernel/rules_runtime.py` | `shared.rules_engine` |
| `identity/services/authorization_service.py`, `services/authorization_service.py` | `shared.rbac.permissions` |
| `control_plane/audit.py` | `shared.audit` |
| `citizen_platform/identity.py` (encrypt/decrypt), `citizen_platform/laboratory.py` | `shared.security.encryption`, `shared.pdf` |

**Implication:** `shared/` is the canonical kernel — it has the highest fan-out of any directory.
`shared/` itself imports only stdlib + 3rd-party libs (reportlab, redis, boto3, joserfc, etc.) plus
internal `shared.*` modules (30 self-imports). **No top-level directory imports `shared/`'s parent or siblings.**

### 2.2 Internal top-level edges (backend/app → app.*)
`app` self-imports (990) cover the internal modular structure (routes→services→models→security,
capabilities, identity, national, domain_platform). These are intra-backend edges — unaffected by
any Phase 2.5 move (backend/app stays put).

### 2.3 TypeScript/TSX edges (frontend-v3)
- `frontend-v3/src/api/generated/types.ts` — **AUTO-GENERATED** by `scripts/generate_frontend_client.py`
  (header: "Generated from backend/ models"). **Hard dependency: backend models → generated client.**
  Zero-drift enforced by `scripts/zero_drift_engine.py`.
- No references from `frontend-v3` to `frontend-v2` or `frontend-v3` → `frontend-v2` (verified: none).
- `frontend-v2` is a standalone Vite app (`react-example` v0.0.0) — **no code depends on it**.

### 2.4 Mobile edges
- `mobile/` (Kotlin/Dart/Swift) has no imports back into the repo (standalone clients; consume APIs).
- No repo code imports `mobile/`.

---

## 3. File Reference Graph (non-code)

### 3.1 GitHub Actions workflows (26) — directory references by count
| Workflow | Dirs referenced |
|---|---|
| mobile-flutter-desktop.yml (26) | mobile/** |
| mobile-android.yml (20) | mobile/** |
| mobile-ios.yml (13) | mobile/** |
| nightly.yml (15) | backend, mobile, scripts, docs |
| sdk-publish.yml (14) | contracts/sdk/** |
| frontend-pwa.yml (12) | **frontend-v2/** AND **frontend-v3/** |
| ai-governance.yml (12) | backend, scripts, shared |
| release.yml (10) | root, Makefile, backend |
| ci.yml (8) | backend, frontend-v3, scripts, shared |
| formatting.yml (6) | backend, frontend-v3 |
| constitution-compliance.yml (6) | backend, scripts, .github |
| ai-governance-enforcement.yml (6) | backend, scripts |
| frontend-e2e.yml (5) | frontend-v2, frontend-v3 |
| secret-scanning.yml (3) | all |
| build-images.yml (3) | **build: ./backend** |
| deploy.yml (2) | backend, frontend |
| preview-deploy.yml (1) | frontend |
| foundation-gate.yml (1) | backend |

**Critical edges:**
- `frontend-pwa.yml` builds **frontend-v2** (`working-directory: frontend-v2`, cache
  `frontend-v2/package-lock.json`, artifact `frontend-v2/build/`) — the ACTIVE CI pipeline builds the
  LEGACY frontend. This is a **must-address edge** for any frontend-v2 move/archive.
- `frontend-e2e.yml` triggers on **both** frontend-v2 and frontend-v3.
- `build-images.yml` context = `./backend` only.
- `helm/gula-platform/values.yaml:228` — `repository: frontend-v2` (image name in the Helm chart).

### 3.2 Docker / Compose
| Edge | Target |
|---|---|
| docker-compose.yml:104, 223 | build context `./backend` |
| docker-compose.full.yml:720 | build `./backend` |
| docker-compose.full.yml:314–700 | build context `./services` (ai/lab/patient/order/result/sample/notification/autonomous_manager Dockerfiles) |
| Dockerfile (root) | copies `package.json`, `.` — builds the ROOT TS app (`server/_core/index.ts`), NOT frontend-v2/v3 |
| docker/Dockerfile | separate build |
| services/*/Dockerfile (9) | self-contained per-service builds |
| nhop-platform/Dockerfile, platform/Dockerfile | legacy images (no compose reference) |

### 3.3 Terraform / Kubernetes / Helm
- `terraform/` (57 `.tf`) — infrastructure modules (security, kubernetes, storage, backend.tf).
- `k8s/base` (31) + `k8s/overlays` (12) — Deployments reference **image names only** (`redis:7-alpine`, `nginx:1.28-alpine`, `ghcr.io/samertts/gula-platform/svc-lab:latest`, etc.) — **no repo-relative path edges**.
- `helm/gula-platform/` (38) — templates for backend/frontend/microservices/redis/postgres; the
  **frontend image name edge = `frontend-v2`** (values.yaml:228).

### 3.4 Shell scripts
| Script | Edge |
|---|---|
| scripts/tag-release.sh | `Makefile`, `backend/` (root check), git tags |
| scripts/setup-https.sh | `config/ssl/` |
| scripts/emergency-fix.sh, server-setup.sh, rotate-secrets.sh, repair-droplet.sh, diagnose*.sh, setup-deployment.sh, nginx-ensure.sh, pitr-recover.sh, digitalocean-manage.sh | server-side ops (paths mostly on remote host) |
| deploy.sh, emergency-recover.sh, setup-production.sh | root-level: `backend/`, docker |
| .github/scripts/{auto-rollback,blue-green-deploy,canary-deploy}.sh | deploy pipeline (containers by name) |
| scripts/generate-sbom.sh, auto_heal.sh, bootstrap_environment.sh | root + backend |

### 3.5 Makefile
`Makefile` references `backend/` (32), `scripts/` (63), `docs/` (16), `frontend` (1).
**Edge:** `make` targets run governance engines in `scripts/` and tests in `backend/`.

---

## 4. Documentation Reference Graph (Markdown)

### 4.1 Link targets to top-level (all tracked `.md`, node_modules excluded)
| Target | Inbound links | Source areas |
|---|---|---|
| `references/` | 34 | contracts, docs |
| `CONTRIBUTING.md` | 8 | multiple |
| `NATIONAL_DEPLOYMENT_CHECKLIST.md` | 7 | national docs |
| `CODE_OF_CONDUCT.md` | 6 | multiple |
| `runbooks/` | 6 | docs |
| `LICENSE`, `ARCHITECTURE.md`, `adr/` | 5 each | multiple |
| `GOVERNANCE.md`, `CLAUDE.md`, `CHANGELOG.md`, `SECURITY.md`, `ROADMAP.md`, `engineering/` | 4 each | multiple |
| `README.md`, `NOTICE`, `docs/` | 2–3 | multiple |

### 4.2 Measured link integrity (Phase 5, re-verified for this graph)
- **Tracked-file broken links: 1** — `SUPPORT.md → docs/troubleshooting.md` (target absent).
- `node_modules` under frontend-v2/frontend-v3 are on-disk only (**untracked**) — their broken README
  links are NOT repo edges (excluded; they belong to third-party packages).

### 4.3 Generator-sourced docs (regenerated, not hand-edited)
| Doc | Generator |
|---|---|
| MASTER_ARCHITECTURE_v2, SHARED_CORE_REGISTRY, DOMAIN_*, WORKSPACE_ARCHITECTURE, DIGITAL_TRUST_PLATFORM, MASTER_REMAINING_WORK, ARCHITECTURE_CONSTITUTION/CERTIFICATION | `scripts/architecture/docs.py` + `report.py` |
| AGENTS.md (62 KB) | `scripts/project_brain.py` |
| PROJECT_BRAIN.md + brain_index.json | `scripts/project_brain.py` |
| TECH docs baselines | `scripts/architecture/*`, `scripts/domains/*` |
| frontend client `types.ts` | `scripts/generate_frontend_client.py` (+ zero_drift_engine.py) |

---

## 5. Package-Manager Graph

| Manifest | Location | Consumers |
|---|---|---|
| `backend/pyproject.toml` (requires-python ≥3.12, 26 deps) | backend/ | backend Docker, CI, Makefile |
| root `package.json` (gula-platform 1.0.0; TS server `server/_core`) | root | root Dockerfile, root build |
| `frontend-v2/package.json` (react-example 0.0.0) | frontend-v2/ | frontend-pwa.yml (builds v2) |
| `frontend-v3/package.json` (gula-frontend-v3 1.0.0-RC2) | frontend-v3/ | ci.yml, frontend-e2e, vitest |
| `mobile/` Gradle/pubspec/Package.swift | mobile/ | mobile-{android,ios,flutter} workflows |
| `pnpm-workspace.yaml` | root | (workspace config present) |
| `contracts/sdk/{cli,dart,kotlin,python,typescript}` | contracts/sdk | sdk-publish.yml |
| `shared/` (stdlib+3rd-party only, no own manifest) | shared/ | backend, scripts |

---

## 6. Generator / SDK / Report Edges

| Generator | Output | Consumers of output |
|---|---|---|
| scripts/generate_frontend_client.py | frontend-v3/src/api/generated/types.ts | frontend-v3 source, zero_drift gate |
| scripts/zero_drift_engine.py | zero-drift registry check | CI (ai-governance), frontend build |
| scripts/architecture/docs.py + report.py | 9 master docs | docs, AGENTS.md, gate |
| scripts/project_brain.py | AGENTS.md, PROJECT_BRAIN.md, brain_index.json | Makefile brain, brain freshness gate |
| scripts/domains/**, architecture/** | governance reports/state | .ai/core, CI |
| contracts/sdk generators | SDK packages | sdk-publish.yml |
| `reports/` (49 tracked) | historical reports | docs only (no code edge) |
| `security-audit/*.json` (bandit/sbom/semgrep/trivy/grype, ~8 MB) | generated scan output | **tracked in git (R-08)** — no code consumer |

---

## 7. Edge Inventory (everything that constrains moves)

| # | Edge | Severity | Move constraint |
|---|---|---|---|
| E-01 | `backend/app` → `shared/` (67 imports) | CRITICAL | Never move/rename `shared/` content used by app |
| E-02 | `scripts/` → `shared/` + `backend/app` (app.* imports) | HIGH | Scripts reference canonical paths |
| E-03 | `frontend-pwa.yml` builds **frontend-v2** | CRITICAL | Archiving/moving frontend-v2 REQUIRES re-pointing this workflow to frontend-v3 (or delete workflow) — else CI breaks |
| E-04 | `helm values.yaml:228` image `frontend-v2` | MEDIUM | Renaming frontend dirs must update chart image name or the deployed image becomes stale |
| E-05 | `frontend-e2e.yml` triggers on frontend-v2+v3 | MEDIUM | Path filters must be updated if v2 archived |
| E-06 | docker-compose build `./backend`, `./services` | HIGH | Never move backend/ or services/ build contexts |
| E-07 | Makefile → backend(32)/scripts(63)/docs(16) | HIGH | Keep canonical `scripts/` + `backend/` paths |
| E-08 | `scripts/{dependency_guardian,repository_scorecard,project_brain}.py` reference `frontend-v2`, `nhop-platform`, `platform`, `services`, `edge_agent` paths | HIGH | Archiving legacy dirs REQUIRES updating these 3 scripts |
| E-09 | `generate_frontend_client.py` + zero_drift → frontend-v3 types | HIGH | Renaming frontend-v3 must update generator output path + zero-drift registry |
| E-10 | Root `Dockerfile` builds root `server/_core/index.ts` (NOT v2/v3) | MEDIUM | Root build independent; docs must clarify |
| E-11 | `docs/` + root `.md` link each other (34→references/, runbooks/, adr/) | MEDIUM | Root `.md` moves must update cross-links OR use relative-safe moves |
| E-12 | `contracts/sdk/**` published by sdk-publish.yml | MEDIUM | Keep contracts/ path stable |
| E-13 | `mobile/**` workflows (3) reference mobile paths | LOW | Keep mobile/ stable |
| E-14 | `config/ssl`, `config/minio-ha`, etc. referenced by scripts/compose | MEDIUM | Keep config/ stable |
| E-15 | `terraform/`, `k8s/`, `helm/` reference image NAMES only (not repo paths) | LOW | Moves of these dirs break nothing in repo code; only tooling call-sites |

---

## 8. Conclusions for Migration Planning

1. **`shared/`, `backend/`, `scripts/`, `services/`, `config/`, `contracts/`, `mobile/` are load-bearing paths** — no moves.
2. **The three "untouchable without a plan" surfaces:** `frontend-v2` (E-03 CI build), legacy dirs
   referenced by 3 scripts (E-08), and `docs/`↔root links (E-11).
3. **Root `.md` moves are safe IF** either (a) moved with all their inbound links (E-11: fix the 1
   broken link + re-point the 8 cross-links), or (b) kept canonical as the generator outputs (they
   regenerate to whatever path the generator says — so the generator must be updated too, E-08-style).
4. **`frontend-v3 → frontend/` rename (Wave 4 optional)** touches E-04/E-05/E-09 — the HIGHEST-risk
   single move, correctly flagged as optional.
5. All moves must use `git mv` (history preserved) and be individually revertible (ADR-028).

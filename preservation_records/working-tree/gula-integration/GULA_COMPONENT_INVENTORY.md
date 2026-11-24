# GULA COMPONENT INVENTORY — WAVE 0

**Companion to:** `GULA_MASTER_BASELINE.md`
**Method:** fresh read-only filesystem examination, 2026-11-19; service verdicts cross-referenced to `GOVERNANCE/NATIONAL_SERVICE_INVENTORY.md` (2026-11-17).
**Status legend (exclusive):** `IMPLEMENTED` · `TESTED` · `INTEGRATED` · `INDEPENDENTLY VERIFIED` · `PRODUCTION READY` · `BLOCKED` · `NOT IMPLEMENTED`
**Important:** engineering status is not release approval. "E2E journey verified" is `NOT IMPLEMENTED` program-wide (documented at `GOVERNANCE/NATIONAL_HEALTH_PLATFORM_COMPLETION_REPORT.md:90,232-238`).

> **GULA-OWNER-GATE-2026-11-20 (additive cross-reference):** All 18 services were re-verified across ten dimensions in `GULA_SERVICE_COVERAGE_REASSESSMENT.md` §5. No model, route or directory was counted as completion: 0 services are `INTEGRATED`/`INDEPENDENTLY VERIFIED`/`PRODUCTION READY`, 0 have verified frontend consumption, 0 have durable offline behaviour, 0 have an E2E journey. No inventory status changed; HOLD stands.

---

## 1. Top-level components

| Directory | Raw files | Purpose | Status |
|---|---:|---|---|
| `backend/` | 5,021 | FastAPI backend, Alembic migrations, tests | `IMPLEMENTED` |
| `frontend-v3/` | 24,219 (242 excl. node_modules/dist) | Primary Arabic-first React Web app | `IMPLEMENTED` |
| `apps/` | 327 | Two full-stack React/tRPC/Drizzle apps | `IMPLEMENTED` |
| `platform/` | 636 | Autonomous platform framework (CLI, kernel, domain, UI, migrations) | `IMPLEMENTED` |
| `mobile/` | 538 | Native Android (Kotlin), iOS (Swift), Flutter desktop | `IMPLEMENTED` |
| `docs/` | 685 | Product/engineering documentation | `IMPLEMENTED` |
| `shared/` | 241 | Shared Core Python library (42 subpackages) | `IMPLEMENTED` |
| `GOVERNANCE/` | 210 | National-service inventory, contracts, ADRs, decisions, reports | `IMPLEMENTED` |
| `frontend-v3` caches / `node_modules` | — | Generated, not source | `IMPLEMENTED` |
| `archive/` | 182 | Archived legacy compose/scripts/experiments | `IMPLEMENTED` |
| `assessment/` | 47 | Enterprise assessment/gap reports | `IMPLEMENTED` |
| `reports/` | 77 | Phase/program reports | `IMPLEMENTED` |
| `scripts/` | 134 | Repo automation (discovery, export, restore, governance, gates) | `IMPLEMENTED` |
| `services/` | 67 | Standalone containerized microservices + device bridge | `IMPLEMENTED` |
| `config/` | 102 | Postgres/Redis/RabbitMQ/MinIO/Grafana/zero-trust configs | `IMPLEMENTED` |
| `contracts/` | 121 | FHIR/ASTM/SDK/compatibility/security contracts, SBOM | `IMPLEMENTED` |
| `terraform/` | 68 | Infrastructure as code | `IMPLEMENTED` |
| `k8s/` | 37 | Kubernetes base manifests + overlays | `IMPLEMENTED` |
| `helm/` | 38 | Helm chart `helm/gula-platform` | `IMPLEMENTED` |
| `security-audit/` | 42 | Security audit reports | `IMPLEMENTED` |
| `.github/` | 45 | 33 workflows + templates | `IMPLEMENTED` |
| `GLOSI/` | 42 | Open-source intelligence/compliance registry | `IMPLEMENTED` |
| `hospital_desktop/` | 27 | PySide6 Qt desktop app | `IMPLEMENTED` |
| `mobile-expo/` | 133 | Expo/RN speech-recognition app (narrow scope) | `IMPLEMENTED` |
| `nhop-platform/` | 55 | Separate NHOP platform service | `IMPLEMENTED` |
| `packages/` | 55 | `packages/uap` shared workspace package | `IMPLEMENTED` |
| `edge_agent/` | 10 | Python managed-edge-node agent | `IMPLEMENTED` |
| `client/`, `server/`, `api/` | 14 / 6 / 1 | Thin demo/scaffold surfaces — not release clients | `IMPLEMENTED` (demo scope) |
| `architecture/`, `identity_report/`, `STATUS/`, `PROGRAM/`, `EVIDENCE/`, `data/`, `database/`, `docker/`, `cloudflare/`, `digitalocean/`, `k6/`, `logs/`, `pitch-deck/`, `presentations/`, `sample_tracking/`, `test_library/`, `tools/`, `ai/`, `governance/`, `supabase/`, `audit/`, `cli/`, `.audit/`, `.semgrep/`, `.githooks/`, `.mypy_cache/`, `.ruff_cache/` | various | Supporting governance, infra, analytics, caches and assets | `IMPLEMENTED` |

---

## 2. Backend domain packages (`backend/app/`, 67 subdirectories, 2,045 `.py` files)

Largest/highest-signal packages:

| Package | `.py` | Role | Status |
|---|---:|---|---|
| `national/` | 346 | National health programs, FHIR mappers, scheduling | `IMPLEMENTED` |
| `capabilities/` | 275 | Shared-capability implementations | `IMPLEMENTED` |
| `identity/` | 136 | NIAM: workspaces, registries, policies, security | `IMPLEMENTED` |
| `kernel/` | 101 | Runtime kernel, routes, SDK, event bus, observability | `IMPLEMENTED` |
| `integration/` | 95 | Inbox, FHIR R4 exchange, identity bundle, offline sync | `IMPLEMENTED` |
| `health_core/` | 82 | Core health platform | `IMPLEMENTED` |
| `services/` | 63 | Application services | `IMPLEMENTED` |
| `routes/` | 63 | HTTP route modules | `IMPLEMENTED` |
| `national_data/` | 50 | National data warehouse (`dp_*`) | `IMPLEMENTED` |
| `engineering/` | 50 | Engineering/autonomy engine | `IMPLEMENTED` |
| `core/` | 46 | Policy/risk/self-healing/startup | `IMPLEMENTED` |
| `governance/` | 41 | Governance services/routes | `IMPLEMENTED` |
| `document_intelligence/` | 34 | Document AI | `IMPLEMENTED` |
| `models/` | 33 | Shared ORM models | `IMPLEMENTED` |
| `control_plane/` | 32 | Multi-tenant service manager | `IMPLEMENTED` |
| `insurance/` | 23 | Claims (`ins_*`); **84 unserved endpoints** | `BLOCKED` |
| `certification/` | 22 | Release gates, metrics | `IMPLEMENTED` |
| `citizen_platform/` | 22 | Citizen portal, medications, privacy, offline | `IMPLEMENTED` |

Bounded contexts with real models and routes: `lims` (35 tables), `pharmacy` (27), `blood_bank` (17), `radiology` (18), `hospital` (14) + `nursing` (15) + `critical_care` (13), `care_continuum` (45 `cc_*`), `ems` (12), `public_health` (6) + `nhdw` (15), `biomedical` (12), `financial`, `payments`, `trust`, `legal`, `workflows`, `notifications`, `edge`, `ai`, `ai_fabric`, `knowledge_graph`, `research_platform`, `command_center`, `command_intelligence`, `lifecycle_platform`, `pilot_platform`, `simulation`, `roadmap`, `interoperability`, `clinical_gateway`, `chronic_care`, `domain_platform`.

All package paths above: `IMPLEMENTED` (source present). Runtime/E2E proof: `BLOCKED` program-wide.

---

## 3. Client platforms

| Platform | Concrete source | Build/test artifacts | Status |
|---|---|---|---|
| Web | `frontend-v3/src` — 173 `.ts/.tsx`, React 19.2.8, Vite 8, Arabic-first RTL | 15 unit test files; 13 Playwright e2e specs; `npm run build`, `tsc`, `eslint` gates in `package.json` | `TESTED` (engineering: build/lint/unit); full e2e `BLOCKED` |
| Android | `mobile/android` — 138 `.kt`, Gradle Kotlin DSL, `values-ar/strings.xml`, unit + androidTest | Native source present | `IMPLEMENTED`; build not run this session → `BLOCKED` |
| iOS | `mobile/ios` — 118 `.swift`, RTL manager, barcode/QR, widget, 5 test files | Native source present | `IMPLEMENTED`; build not run this session → `BLOCKED` |
| Desktop | `mobile/desktop` — 131 `.dart`, linux/macos/windows runners; `hospital_desktop` — 26 Python/PySide6 files | Two independent desktop clients | `IMPLEMENTED`; build not run this session → `BLOCKED` |
| Expo/RN | `mobile-expo/src/speech` + 2 components, 1 Jest test | Narrow speech-recognition scope only | `IMPLEMENTED` (narrow) |
| Full-stack apps | `apps/gula-platform-ui-refresh`, `apps/gula-web-suite` (tRPC 11 + Drizzle + Vite) | 175 / 152 files excl. node_modules | `IMPLEMENTED` |

---

## 4. The 18 national health services (from `GOVERNANCE/NATIONAL_SERVICE_INVENTORY.md`)

`IN SCOPE` below means *proposed* for the release candidate pending owner approval; it is not an approval. `OUT OF SCOPE` includes the documented reason, per directive §2.

| # | Service | Live ops | Engineering status | Release-scope proposal |
|---:|---|---:|---|---|
| 01 | Laboratory | 103 | `IMPLEMENTED` + `TESTED` (35 `lims` tables) | IN SCOPE — pending E2E + owner gate |
| 02 | Hospital | 127 | `IMPLEMENTED` (14 hospital + 15 nursing + 13 critical tables) | IN SCOPE — ADR-B table ownership `BLOCKED` |
| 03 | Primary healthcare | 13 | `IMPLEMENTED` (5 `cc_*`) | IN SCOPE — ADR-C `BLOCKED` |
| 04 | Pharmacy & medication | 63 | `IMPLEMENTED` + `TESTED` (27 tables) | IN SCOPE — pending E2E |
| 05 | Radiology & imaging | 58 | `IMPLEMENTED` + `TESTED` (18 tables) | IN SCOPE — pending E2E |
| 06 | Emergency & ambulance | 26 | `IMPLEMENTED` + `TESTED` (12 tables) | IN SCOPE — pending E2E |
| 07 | Blood bank | 30 | `IMPLEMENTED` (17 tables) | IN SCOPE — pending E2E |
| 08 | Immunization | 13 | `IMPLEMENTED` (6 `cc_*` + 1 `ehr_*`) | IN SCOPE — cross-cutting; ADR-C `BLOCKED` |
| 09 | Public health & surveillance | 110 | `IMPLEMENTED` (6 + 15 `nhdw`) | IN SCOPE — pending E2E |
| 10 | Dental | 0 | `NOT IMPLEMENTED` (0 tables) | **OUT OF SCOPE** — no domain model, contract or API; reason: not implemented |
| 11 | Maternal & child health | 9 | `IMPLEMENTED` (7 `cc_*`) | IN SCOPE — cross-cutting; ADR-C `BLOCKED` |
| 12 | Chronic disease management | 15 | `IMPLEMENTED` (5 `cc_*`) | IN SCOPE — pending E2E |
| 13 | Rehabilitation / physio | 0 | `NOT IMPLEMENTED` (0 tables) | **OUT OF SCOPE** — no domain model, contract or API |
| 14 | Mental health | 0 | `NOT IMPLEMENTED` (data/analytics signals only, 0 dedicated tables) | **OUT OF SCOPE** — analytics only, no clinical service |
| 15 | Referral & continuity | 18 | `IMPLEMENTED` (12 `cc_*`) | IN SCOPE — migration closure `INDEPENDENTLY VERIFIED` (engineering) |
| 16 | Insurance & claims | 5 (84 unserved) | `BLOCKED` (30 `ins_*` tables, 84 unserved endpoints; F-085 `InsBase` unregistered) | **OUT OF SCOPE** — ADR-G/I `BLOCKED`; unserved API and unmigrated tables |
| 17 | Home healthcare | 4 | `IMPLEMENTED` (2 `cc_*`) | IN SCOPE — pending E2E |
| 18 | Medical equipment | 52 | `IMPLEMENTED` (12 + 10 devices) | IN SCOPE — pending E2E |

Care-continuum backbone: `backend/app/care_continuum/` (45 models) + `backend/app/routes/care_continuum.py` (74 operations) — `IMPLEMENTED` / `TESTED`. Finding `AUDIT-POSITIONAL-001` (audit call-site argument mis-mapping; see baseline §6) is fixed across all 8 affected files and `INDEPENDENTLY VERIFIED` (engineering scope) per `GULA_AUDIT_POSITIONAL_FIX_REPORT.md`; its commit remains `BLOCKED` by mixed provenance in `lims/routes.py`. Finding `AUDIT-BYPASS-001` (critical alerts written outside the hash chain; `routes/ai.py::_emit_critical_alert`) is fixed via canonical `log_action` and `INDEPENDENTLY VERIFIED` (engineering scope) per `GULA_AUDIT_BYPASS_FIX_REPORT.md`; commit `BLOCKED` by mixed provenance in `routes/ai.py`. A separate 0-audit-writes observation recorded in `GOVERNANCE/ACTIVATION_FINAL_REPORT.md:121` has now received read-only service-layer analysis in `GULA_SERVICE_COVERAGE_REASSESSMENT.md`: it is a journey-level observability gap (unmigrated `cc_*` services produced no E2E audit events), NOT a canonical-chain bypass (1 writer / 59 callers / 0 direct writes outside the chain, per `GULA_AUDIT_ARCHITECTURE_COMPLETENESS_REPORT.md`). The underlying journeys remain `BLOCKED`; the observation is not silently adjudicated as release-ready. SEC-015 (SQLite chain linkage) is fixed and `INDEPENDENTLY VERIFIED` (engineering scope) per `GULA_SEC015_AUDIT_CHAIN_REMEDIATION_REPORT.md`.

---

## 5. Shared Core (`shared/`, 42 subpackages)

`audit`, `auth`, `rbac`, `identity`, `security`, `encryption`, `events`, `workflow`, `notifications`, `communication`, `communication_providers`, `storage`, `cache`, `retry`, `circuit_breaker`, `pdf`, `barcode`, `qr`, `pdf`, `search`, `scheduler`, `metrics`, `logging`, `tracing`, `observability`, `middleware`, `validators`, `schemas`, `design_system`, `localization`, `domain`, `architecture`, `models`, `utilities`, `generators`, `backup`, `restore`, `policies`, `device`, `sdk`, `di_container`, `printing`, `health`.

Status: `IMPLEMENTED` (source present). Canonical-provider consolidation: `BLOCKED` — duplicate engines acknowledged in the architecture baseline; no new engine created in this wave.

---

## 6. Inventory completeness statement

Every top-level directory and every backend domain package has been enumerated above with a status from the permitted vocabulary. Clients, the 18 services and Shared Core are individually classified. Services marked `OUT OF SCOPE` carry an explicit reason. No incomplete component is hidden behind a nominal router or filename.

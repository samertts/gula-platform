# GULA — Current Repository State

**Document class:** AUTHORITATIVE snapshot (read-only discovery)
**Date:** 2026-08-11
**Audit type:** DISCOVER → VERIFY → AUDIT → CLASSIFY → MAP → PLAN → STOP
**Method:** Evidence-based inspection of the repository at HEAD `f735a7a1` on
branch `remediate-security-001`. Every claim below was verified against source
code, git history, or executed tooling — not inferred from documentation.

---

## 1. Repository & Git State

| Item | Value |
|---|---|
| Path | `/home/samertts/workspace/projects/gula-platform` |
| Branch | `remediate-security-001` |
| HEAD | `f735a7a1` (chore(devx): sync AI skills governance foundation) |
| Remote | `origin` → `ssh://git@ssh.github.com:443/samertts/gula-platform.git` |
| Remote HEAD (main) | `c4894c00` (Merge PR #120) — fetched; **main is ahead of this branch's lineage** |
| Local ↔ remote sync | Branch in sync with `origin/remediate-security-001` |
| Working tree | Clean |
| Staged changes | None |
| Unstaged changes | None |
| Untracked files | None |
| Stash | `stash@{0}` (modified `security/modules/container/__init__.py` — WIP, preserved untouched); `stash@{1}` (older FHIR routes WIP) |
| Worktrees | `gula-demo-preview` (f6772ee6), `gula-showcase-security` (60988833), `gula-wave-b` (77a964d0) |
| Tags | `v1.0.0-RC1`, `v1.0.0-RC2`, `v2.1.0-engineering-factory` (no `v1.0.0`) |
| Local branches | 10 (incl. `main`, `remediate-security-001`, `feature/demo-preview-access`, `wave-b/B1-abac-route-enforcement`) |
| Remote branches | `main`, `remediate-security-001`, `feature/demo-preview-access`, `wave-b/B1-abac-route-enforcement`, plus **concurrent sessions**: `manus/admin-workspace-20260811`, `security-hardening-demo-alignment`, `wave0-audit-hardening-20260811` |
| git fsck | Clean (dangling objects only, no corruption) |

### Concurrent-session work detected (PROTECTED — not touched)
- `origin/manus/admin-workspace-20260811` (9c558e7b — "add protected administration workspace") — separate session, not merged.
- `origin/security-hardening-demo-alignment` (69035da5 — "harden auth and add isolated demo flow") — separate session.
- `origin/wave0-audit-hardening-20260811` (6b234260) — separate session.
- Local branch `main` is NOT checked out; remote `main` has advanced independently.

### Git history summary (recent)
- `f735a7a1` — AI skills governance sync (this commit)
- `60988833` — merge `feature/demo-preview-access` (isolated read-only demo v0.1)
- `8444f039` → `dcd32500` — Wave A of the successor program: ABAC authorization foundation, organization facility hierarchy, authority boundaries, audit integrity verification, identity lifecycle hardening, professional authorization, Wave A certification.
- `71a8e9ee` — ADR-037: `PROGRAM_NEXT_PHASE_PLAN.md` declared authoritative successor program.
- `b09d0328` — PROGRAM-REPO-01 Wave 4 certified complete.
- `505bd48f`/`891cf02c` — legacy trees archived to `archive/legacy/` + `archive/frontend-v2`.

---

## 2. Governance Authority Hierarchy

Established from repository evidence (ADR-037, PROGRAM_NEXT_PHASE_PLAN.md,
AGENTS.md, AI_OPERATING_CONSTITUTION.md):

```
AUTHORITATIVE (execution-binding)
├── AI_OPERATING_CONSTITUTION.md (supreme)
├── AGENTS.md (workspace-anchored summary + enforcement)
├── docs/programs/PROGRAM_NEXT_PHASE_PLAN.md (successor program, PD-approved via ADR-037)
├── docs/adr/ADR-028..037 (structural migration, canonical providers, kernel domains, program authority)
├── docs/constitution/33_STRUCTURAL_MIGRATION_CONSTITUTION.md
├── docs/constitution/32_AI_EXECUTION_CONSTITUTION.md
└── .github/workflows/ai-governance.yml, architecture gate (hard CI)

CURRENT (referenced operating docs)
├── PROGRAM_01_FINAL_CERTIFICATION.md, WAVE_1..4_EXECUTION_REPORT.md, WAVE_A_EXECUTION_REPORT.md
├── SHARED_CORE_REGISTRY, ARCHITECTURE_CERTIFICATION.md, TECHNICAL_DEBT_REGISTER.md
├── docs/adr/ADR-001..036 (historical decisions)

HISTORICAL
├── PROGRAM-REPO-01 wave reports (certified, immutable)
├── 41 constitutional documents (docs/constitution/)
└── ARCHITECTURE_DECISIONS.md, OPERATIONS_DECISIONS.md

PROPOSED / EXPERIMENTAL
├── GULA_TARGET_ARCHITECTURE.md, GULA_MASTER_EXECUTION_PLAN.md, GULA_MASTER_GAP_MATRIX.md (this program set)
├── k8s/ overlays, terraform/, helm/, services/ microservice stubs
└── mobile/desktop (Flutter 2.1.0), mobile/ios (unbuildable scaffold)
```

**Program status:** PROGRAM-REPO-01 certified complete (architecture locked,
25/25 acknowledged findings, domain isolation 11/11). Successor program
(`PROGRAM_NEXT_PHASE_PLAN`) approved via ADR-037. **Wave A is COMPLETE and
CERTIFIED** (2026-08-10). **Wave B is NOT authorized** — the branch
`wave-b/B1-abac-route-enforcement` (77a964d0) exists but is unmerged; the
execution report states "STOP — do not start Wave B."

---

## 3. Application Ecosystem — Actual State

| Surface | Path | Framework | State (verified) |
|---|---|---|---|
| **Web (active)** | `frontend-v3/` | React 19.2 + react-router 8.3 + Vite 8 + TanStack Query 5 | **REAL / production-grade surface** — 45+ page areas, real API auth, MFA flow, i18n (ar/en, RTL), PWA with service worker |
| **Android** | `mobile/android/` | Kotlin 2.1.20, AGP 8.13.2, Compose, Hilt, Room, Retrofit | **REAL / buildable** — single `:app`, `io.gula.android`, minSdk 26 / target 35, encrypted prefs, cert pinning, offline sync queue |
| **iOS** | `mobile/ios/` | SwiftUI + Core Data | **UNBUILDABLE** — `Gula.xcodeproj/` is EMPTY (no `project.pbxproj`, no workspace, no scheme); Core Data model missing; 107 Swift sources tracked but no build system |
| **Desktop** | `mobile/desktop/` | Flutter 2.1.0 (drift, riverpod) | **PARTIAL** — real feature surface, but `database.g.dart` is a placeholder (drift generated code missing → DB/offline path cannot compile) and lab device discovery is a stub |
| **Store metadata** | `mobile/store/` + `fastlane` | — | Terms/privacy/listing for App Store + Google Play exist; secrets are env-driven; fastlane team IDs are placeholders |
| **Root experimental app** | `server/` + `client/` | Node 24, express 5, tRPC 11, React 19 | **EXPERIMENTAL** — root Dockerfile targets it; `dist/` gitignored |

### Divergent API domains (inconsistency finding)
- Frontend v3: `VITE_API_BASE_URL` (default `/api`, dev `http://localhost:8000`)
- Android: `https://api.gulaplatform.com/api/v1/` (AuthInterceptor.kt:87)
- Desktop: `https://api.gula-platform.com/api/v1` (main.dart)
- iOS: `https://api.gula.iq` (APIClient.swift) — **three distinct production domains; must be unified**

---

## 4. Backend — Actual State

**Entry:** `backend/app/main.py` → `factory.py` `create_app()` (8 runtime modes).
**Route surface (verified by booting in openapi mode):** **1,643 unique paths /
1,959 HTTP operations** across 82 router registration points. Top prefixes:
`/niam` 221, `/national` 126, `/governance` 71, `/clinical` 66, `/nursing` 61,
`/api` 56, `/lims` 55, `/ehr` 53, `/nhdw` 51, `/radiology` 49.

### Identity / Authentication / Authorization — REAL, dual-track
- **NIAM** (`backend/app/identity/`): 26 subpackages. 10 canonical IdentityTypes,
  bcrypt password login (`POST /niam/auth/login`), JWT pair (15 min / 7 days,
  jti, Redis blacklist), **MFA real** (TOTP + WebAuthn/FIDO2 + backup codes),
  OAuth2/OIDC + SAML endpoints, adaptive-auth risk engine, certificate/federation
  support.
- **Authorization:** RBAC `RoleAssignment`→`RolePermission` with license-gating
  (professional roles require verified `ProfessionalLicense`); ABAC `PolicyService`
  (targets + conditions: governorate, time-of-day, deny-overrides); workspace-scoped
  `check_permission` (permissions never cross workspaces); break-glass sessions;
  every decision logged to `AuthorizationAudit`.
- **Legacy lab auth** (`security/dependencies.py`): `get_current_user`,
  `require_permission`, `require_role`, `require_service_account` — enforced on
  **522 `require_permission` + 595 `get_current_user` + 14 `require_role`** call sites.
- **Both paths are enforced server-side.** Frontend authorization is NOT trusted
  as authority.

### Domain module reality (evidence-based classification)
| Module | Class | Evidence |
|---|---|---|
| `national/` | **REAL** | 330 files, ~39,700 LOC — rules/task/notification/document/scheduling/search engines, observability, FHIR mappers, ABAC/break-glass |
| `ehr/` | **REAL** | 15 files, service 1,389 LOC, 53 routes |
| `fhir/` | **REAL** | R4 server at `routes/ehr_fhir.py` (1,557 LOC, 25 decorators), mappers in `national/fhir/`, CapabilityStatement 4.0.1, SMART-on-FHIR |
| `interoperability/` | **STUB** | 7 files, 572 LOC — framework only, **zero importers** |
| `hospital/` | **PARTIAL** | models in-module; routes/services outside |
| `ems/`, `blood_bank/`, `pharmacy/`, `radiology/`, `public_health/`, `care_continuum/`, `citizen_platform/`, `nursing/`, `critical_care/`, `insurance/`, `financial/`, `mpi/`, `nhdw/`, `health_data/`, `research_platform/`, `command_center/`, `lifecycle_platform/`, `pilot_platform/` | **REAL** | actual routes/services/models verified |
| `clinical/`, `national_data/` | **PARTIAL** | models in-module, live logic in routes/services |
| `legal/` | **STUB** | 2 files, 11 lines — `record_consent()` returns dict, no DB/routes |
| `optimization/` + `approvals/`, `constraints/`, `policies/`, `rules/`, `validation/`, `forms/`, `dependencies/` | **EMPTY** | placeholder dirs, 0 files |

### Interoperability — REAL (where it matters)
- **FHIR R4:** real read/search/create/update/delete + batch/transaction + bundle;
  13 resource types; protected by `require_permission`.
- **HL7 v2:** ORU^R01 parser (`lims/integration/hl7.py`), `integration/standards/hl7.py`,
  `HL7Gateway` — receive endpoint `/lims/integration/hl7/receive`.
- **DICOM/PACS:** `radiology/pacs.py` (DICOMStorageService, SHA-256 checksums,
  archive tiers), RIS connector, LIS connector + full LIMS module (55 `/lims` paths).
- **Integration platform:** `IntegrationPlatform().initialize(app)` registers 5
  connectors at boot (laboratory, pharmacy, primary_care, radiology, vaccination);
  ESB module with dead-letter queue, idempotency, priority.

### Audit — REAL, tamper-evident
- Legacy: `audit_logs` table with `chain_hash` (SHA-256 of prev+entry), HMAC-anchored
  monthly anchor files on disk, `audit_log()` decorator.
- NIAM: `niam_audit_entries` with `entry_hash`+`previous_hash`, `verify_chain_integrity()`.
- Tests: `test_audit_chain_integrity.py` (9), `test_audit_service.py`, etc.

### AI — REAL framework, stub-by-default
- `ai_fabric/gateway.py`: 8 providers (OpenAI, Anthropic, Gemini, **Ollama local**,
  Azure, vLLM, OpenRouter, DeepSeek). Local AI engine probes GPUs with CPU fallback.
- **Without API keys → stub mode** (`generate()` returns `""`). Observed at boot.
- RAG (`ai/rag_pipeline.py`) + pgvector vector store; knowledge graph; CDS;
  **AI approval workflow** (`routes/ai.py`: suggest→approve→execute, doctor-gated).
- **Evaluation harness** (`ai_fabric/evaluation.py`): RAG suite + clinical suite, tested.

### Offline — implemented but weakest link
- `OfflineSyncEngine` (in-memory vector clocks/conflict detection), `SyncService`
  (in-memory), `StoreForwardEngine`+`ConflictResolver` (integration layer), and
  **`nhdw/offline.py` — the only DB-persisted sync** (OfflineChange table, sync batches).
- **No unified offline-first gateway across domains.** Citizen offline queue exists
  but uses in-memory sync. This is the biggest gap vs the "offline-first" claim.

### Event bus — REAL, production-shaped
- `kernel/event_bus/`: publish/subscribe, **Outbox + Inbox patterns**, RetryQueue,
  DeadLetterQueue, EventReplay, SnapshotEngine, RecoveryEngine, EventVersioning.
- ESB routes + dead-letter + idempotency + priority in `integration/esb/`.

### Tests
- **280 Python files / 257 test files / ~4,623 test functions / 58,330 LOC** of tests.
- Full suite recorded at **5,089 passed / 0 failed** (598 s, PostgreSQL 16).
- Frontend: 16 vitest files (122 tests) + 8 Playwright e2e specs. tsc 0, eslint 0.

---

## 5. Data & Migrations

- **57 Alembic migrations** in `backend/migrations/versions/` — single linear chain,
  applied to head; migration-check gate in CI.
- PostgreSQL 16 primary + replica (WAL) + pgbouncer; Redis + replica + sentinel;
  RabbitMQ; Kafka; ClickHouse; MinIO; Vault; Keycloak; Ollama — in `docker-compose.full.yml` (48 services).
- MySQL/NoSQL: none — PostgreSQL is the system of record.
- Health ID / MPI: real matcher/resolver/blocking in `mpi/` (1,378 LOC).
- DR: **live-tested** (2026-08-06) — backup → drop → restore round-trip on PG16,
  WAL→S3, RPO ≈ 1 min (documented in DISASTER_RECOVERY_REPORT.md).

---

## 6. Security Posture (verified findings)

### Strengths
- Server-side authorization enforced at scale; dual auth tracks both real.
- MFA (TOTP + WebAuthn), OAuth2/OIDC, SAML, adaptive auth, session blacklist.
- No tracked secrets — only `.env.example` placeholders; `.secrets.baseline` clean
  (CI enforces zero findings); pre-commit runs ruff + mypy + detect-secrets + gitleaks.
- Strict env validation (`config.py` fails closed in production without required vars).
- Security headers (CSP/HSTS/X-Frame-Options), CORS allowlist, rate limits on QR/edge/telegram.

### Findings (verified, non-destructive)
| # | Severity | Finding | Evidence |
|---|---|---|---|
| S1 | **HIGH** | `GET /api/ai/operations` and `GET /api/ai/providers` have **no auth dependency**; `/providers` actively probes Ollama `/api/tags` and returns `base_url`, model inventory, cost, fallback chain | `backend/app/routes/ai.py:337,346` |
| S2 | MEDIUM | `GET /insurance/{insurance_id}` has only `get_current_user` — no lab/ownership scoping (IDOR candidate). Mitigated: STUB mode default, trust level NON_CRITICAL | `backend/app/routes/insurance.py` |
| S3 | LOW | `POST /oauth2/revoke` unauthenticated (RFC 7009-style); `/token` does proper client auth | `backend/app/routes/oauth2.py:201` |
| S4 | MEDIUM | **Frontend RBAC is client-side only** — `src/permissions/index.ts` + `RoleGuard.tsx` read `user.role` stored in localStorage (`AuthContext.tsx:21,35`); editing localStorage self-grants UI privileges (server remains authoritative) | `frontend-v3/src/components/auth/RoleGuard.tsx:20` |
| S5 | MEDIUM | `docker-compose.full.yml` services lack `security_opt` (no-no-new-privileges) | compose file |
| S6 | MEDIUM | K8s ingress has no authn on control surface (no oauth2-proxy/basic-auth); secrets via `external-vault` annotation only | `k8s/base/gateway/ingress.yaml` |
| S7 | LOW | `build-images.yml` duplicate `push:` key silently drops the main-branch push trigger | workflow file |
| S8 | LOW | `frontend-pwa.yml` references `frontend-v3/lighthouse.config.json` which does not exist → Lighthouse job fails | workflow:135 |
| S9 | LOW | `mobile-ios.yml` uses `Gula.xcworkspace` in 6 steps; workspace does not exist → iOS CI cannot build | workflow |

### Legal / compliance gaps
- **No Privacy Policy or Terms of Service pages in the web frontend** (79 pages scanned, none found).
- Store metadata (Play/App Store) contains terms + privacy docs; fastlane metadata has privacy_url.
- Backend has data-privacy modules (informational only).

---

## 7. CI/CD — 26 workflows

All YAML-valid. Verified working: `ci.yml` (6 jobs: syntax/data-preservation/migration/lint/test/security), `quality-gate.yml`, `secret-scanning.yml`, `codeql`, `dependency-review`, `scorecard`, `deploy.yml` (SSH + cosign + health-check + rollback), `blue-green-deploy.yml`, `auto-rollback.yml`, `canary-deploy.yml`, `nightly.yml`, `release.yml`, `formatting.yml`, `frontend-pwa.yml` (except S8), `mobile-android.yml`, `mobile-flutter-desktop.yml`, `ai-governance.yml` (architecture gate hard).

Defects: S7 (duplicate push), S8 (missing lighthouse config), S9 (iOS workspace), C4 (unpinned actions in `ai-governance-enforcement.yml`).

---

## 8. Known Risks (top-level, detailed register in GULA_RISK_REGISTER.md)

1. iOS app unbuildable (empty Xcode project) despite store metadata + CI.
2. Desktop drift DB layer broken (`database.g.dart` placeholder).
3. AI admin endpoints unauthenticated (S1).
4. Frontend client-side authorization (S4) — UX-only, but must never become authority.
5. Offline sync not unified / not DB-persisted except nhdw.
6. `interoperability/` framework has zero importers (advertised but unused).
7. `legal/` consent is a stub.
8. Three divergent API base domains across clients.
9. Main branch has advanced independently; concurrent sessions active.
10. No web legal pages (privacy/terms) before store production release.
11. Root experimental app (server/client) + root Dockerfile ambiguity.
12. Wave B branch unmerged; next authorization gated on PD approval.

---

## 9. What Is / Is Not Verified

### Genuinely complete (evidence-backed)
- Wave A of successor program (identity hardening + immutable audit + ABAC foundation) — certified.
- NIAM identity/auth/MFA/RBAC/ABAC/workspaces — implemented and enforced server-side.
- FHIR R4 server, HL7 v2 receive, DICOM/PACS/RIS/LIS — real usable endpoints.
- Immutable hash-chained audit (DB + HMAC anchors) + verification service.
- Event bus with outbox/inbox/DLQ/replay/recovery.
- Full backend suite green (5,089); frontend 122 vitest; tsc/eslint clean.
- DR drill executed (PG16 backup/drop/restore, RPO≈1 min).

### Partial / broken
- iOS (unbuildable), Desktop (drift gen missing), offline sync (not unified),
  interoperability framework (unwired), legal consent (stub), frontend legal pages (missing).

### Protected from modification
- All concurrent-session branches/worktrees/stash untouched.
- No `reset --hard`, `clean -fd`, force-push, rebase, or branch deletion performed.

---

*This snapshot is intentionally non-normative about *next steps* — the execution
sequencing, target architecture, and gap remediation priorities are defined in
the companion documents: `GULA_MASTER_GAP_MATRIX.md`, `GULA_TARGET_ARCHITECTURE.md`,
`GULA_APPLICATION_ECOSYSTEM.md`, `GULA_MASTER_EXECUTION_PLAN.md`,
`GULA_RISK_REGISTER.md`, `GULA_DEPENDENCY_GRAPH.md`.*

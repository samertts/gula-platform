# GULA — Target Architecture

**Document class:** PROPOSED (target-state blueprint, not yet implemented)
**Date:** 2026-08-11
**Basis:** Verified current state (GULA_CURRENT_REPOSITORY_STATE.md) + national
platform constitution + `PROGRAM_NEXT_PHASE_PLAN.md` dependency layers.

---

## 1. Architecture Principles (target invariants)

1. **ONE GULA CORE** — one backend, one database of record, one identity.
2. **ONE GULA ACCOUNT / ONE IDENTITY** — NIAM is the single identity source; profile is separated from identity.
3. **ONE AUTHORIZATION MODEL** — RBAC + ABAC combined; server-side authoritative; frontend never trusts itself.
4. **ONE APPLICATION PER PLATFORM** — Web, Android, iOS, (Desktop where justified). All domains reachable via Workspaces + permissions; no citizen/doctor/lab/ministry separate apps.
5. **MULTIPLE WORKSPACES** — Citizen, Clinical, Laboratory, Radiology, Pharmacy, Hospital, Emergency/EMS, Blood Bank, Public Health, Workforce, Employee Services, Facility Operations, Directorate, Ministry/National Control Plane, Research, Administration, External/Partner.
6. **NATIONAL SCALE** — Ministry → Directorate → Hospital → Lab hierarchy as an organizational graph; governorate/tenant isolation via ABAC attributes.
7. **OFFLINE-FIRST** — every field-facing module has encrypted local state, durable queues, idempotency, conflict resolution, reconciliation, audit.
8. **CLINICAL SAFETY** — human verification mandatory at defined points; AI never the silent final decision maker.
9. **ARABIC-FIRST** — RTL, i18n ar/en, Arabic terminology.
10. **IMMUTABLE AUDIT** — hash-chained, append-only, HMAC-anchored; Purpose-of-Use + Minimum Necessary Disclosure enforced at the server.

---

## 2. Application Architecture

```
┌────────────────────────── Web (frontend-v3) ─────────────────────────┐
│ React 19 + router 8 · PWA · i18n ar/en RTL · workspaces in shell    │
├────────────────────────── Android (io.gula.android) ─────────────────┤
│ Compose · Room offline · encrypted prefs · pinning · sync queue     │
├────────────────────────── iOS (io.gula.ios) ─────────────────────────┤
│ SwiftUI · Core Data · Keychain · BGTask sync  (must be rebuilt)     │
├────────────────────────── Desktop (optional, Flutter) ───────────────┤
│ LIMS for Windows/Linux/macOS · drift · device/analyzer integration  │
└──────────────────────────────┬───────────────────────────────────────┘
                               │ HTTPS (one canonical API domain)
                               ▼
┌────────────────────────── ONE GULA CORE (backend) ───────────────────┐
│ factory.py · middleware · authn/authz dependencies · routers        │
│ NIAM (identity) · workspaces · RBAC/ABAC · audit · event bus        │
│ domain modules (ehr, lims, radiology, pharmacy, hospital, ems,      │
│ blood_bank, public_health, mpi, nhdw, national, research, ...)      │
│ interoperability: FHIR R4 · HL7 v2 · DICOM/PACS · RIS · LIS         │
└──────┬──────────────┬──────────────┬─────────────────────────────────┘
       ▼              ▼              ▼
   PostgreSQL 16    Redis 7       Object storage / MinIO
   (system of       (cache,        (DICOM, documents,
    record + WAL)    blacklist,      backups)
                     queues)
```

---

## 3. Backend Architecture (target)

- **Monolith-first with explicit seams.** Keep the single deployable (1,643
  paths today) and enforce domain isolation (Domain Platform 11/11 gate, hard CI).
  The `services/*` microservice stubs are NOT production; microservice extraction
  happens only when a bounded context proves it needs independent scaling.
- **Factory** registers routers; a **router registry** documents every prefix;
  growth is governed by the architecture gate (no new Shared Core reimplementations).
- **Canonical providers** (ADR-029/030/031/032/033/034/035/036) remain the single
  source for shared capabilities (audit, notifications, search, PDF, rules,
  workflows). `interoperability/` framework must be **wired into the canonical
  integration surface or retired** (currently zero importers).
- **Middleware:** CORS allowlist, security headers, request ID, concurrency limit,
  degraded mode, OTLP tracing, rate limiting, body-size limits.

---

## 4. Identity & Authorization Architecture (target)

```
ONE IDENTITY (NIAM)
  Person → Account → IdentityType (11) → Profile (separate)
  Devices · Sessions · Consents · Entitlements
       │
  Organization graph: Ministry → Directorate → Hospital → Lab → Unit
       │
  RBAC: RoleAssignment → RolePermission (license-gated where professional)
  ABAC: PolicyService (resource/action/roles/user_types + attributes:
        governorate, time-of-day, purpose-of-use)
       │
  Workspace: exactly ONE active per context; permissions never cross workspaces
       │
  Enforcement: server-side dependencies (get_current_user / require_permission
               / get_current_identity) on every route; MFA-required flags;
               break-glass with audit
       │
  Audit: every authz decision → AuthorizationAudit; hash chain + anchors
```

- **Frontend authorization is presentation-only.** `RoleGuard`/permissions may
  shape the UI, but the server re-validates everything. No self-grant path.
- **Purpose-of-Use + Minimum Necessary Disclosure** become real modules
  (Wave D) built on the consent primitives (which today are only an 11-line stub).

---

## 5. Data Architecture (target)

- **PostgreSQL 16** = system of record; single linear Alembic chain (57 today),
  additive-only migrations, backwards-compatible forever.
- **Schemas by domain** with strict ownership (Domain Platform isolation).
- **Identifiers:** Health ID via MPI (matcher/resolver/blocking); national ID
  handled country-agnostically with hashed storage.
- **Hot/archive/retention:** tiered storage; DICOM archive tiers; legal hold +
  retention policies on the data governance layer (partially present in `health_data`).
- **Data quality/lineage:** `health_data` data lake + governance/lineage +
  event store provide provenance; expand to clinical streams.
- **Partitioning/concurrency:** partitioned tables for audit/sync/orders at scale;
  pgbouncer + connection budget; index coverage for high-frequency queries.
- **Offline (target):** one DB-backed sync engine (vector clocks + CRDT + idempotency
  + reconciliation) usable by every domain — replaces today's in-memory mix.

---

## 6. Security Architecture (target)

- **DENY BY DEFAULT · LEAST PRIVILEGE · FAIL CLOSED · SERVER-SIDE AUTHORIZATION.**
- Auth: password (bcrypt) + MFA (TOTP/WebAuthn) + OAuth2/OIDC + SAML; session
  blacklist; device trust; adaptive auth risk engine.
- Secrets: external Vault (K8s `external-vault` annotation) or env-injected at
  deploy; no secrets in repo; gitleaks + detect-secrets baseline gates.
- Rate limiting: per-identity + per-IP + per-workspace budgets; abuse prevention
  on public endpoints (QR, telegram webhook, OAuth).
- Every route authenticated by default; explicit allowlist only for provably
  public endpoints (health, OAuth discovery, signed-token QR).
- **P0 fixes required before release:** AI admin endpoints auth (S1); insurance
  IDOR scoping (S2); compose `security_opt` (S5); ingress control-plane authn (S6).
- SBOM + dependency review (HIGH-blocking) already in CI; keep current.

---

## 7. Event Architecture (target)

- **One event bus** (`kernel/event_bus/`): publish/subscribe, transactional
  **Outbox** + **Inbox**, RetryQueue, DeadLetterQueue, EventReplay, Snapshots,
  RecoveryEngine, versioning. Already built; keep as the single backbone.
- ESB gateway (`integration/esb/`) provides routing + idempotency + priority.
- Domain events flow through the bus; integration connectors (laboratory,
  pharmacy, primary care, radiology, vaccination) publish/consume via the bus.

---

## 8. Integration Architecture (target)

| Standard | Target | Current |
|---|---|---|
| FHIR R4 | Full read/search + create/update + batch/transaction + terminology | **REAL** (ehr_fhir, 13 resources) |
| HL7 v2.x | ORU^R01 receive + ACK; outbound gateway | **REAL** (lims/integration, gateway) |
| DICOM / PACS | Storage + retrieval + MPPS + archive tiers | **REAL** (radiology/pacs) |
| RIS | connectors + ORM/ORU builders | **REAL** (connectors/ris) |
| LIS | analyzer receive + simulator | **REAL** (lims module) |
| Terminology | FHIR TerminologyService; CLSI/LOINC mapping | PARTIAL → expand |
| Analyzers | LIS receive; desktop device discovery | PARTIAL (desktop stub) |

---

## 9. Offline Architecture (target)

Classified by capability:
- ONLINE_ONLY: ministry control plane, national analytics.
- OFFLINE_ALLOWED: laboratory workflows (results capture, QC).
- OFFLINE_LIMITED: clinical read/update with reconciliation.
- EMERGENCY_OFFLINE: field triage, blood bank, EMS (write-forward).

Requirements per offline surface: encrypted local state (SQLCipher/IndexedDB/
Room/Keychain), durable operation queue, idempotent API keys, vector-clock conflict
resolution, reconciliation service, audit of every offline→online merge.

---

## 10. AI Architecture (target)

- **Local-first:** Ollama / vLLM preferred (Local AI First constitution); cloud
  providers (Gemini/OpenAI/Anthropic) behind keys, stub mode by default.
- **Governance:** approval workflow (suggest→approve→execute, human-gated),
  evaluation harness (RAG + clinical suites), guardrails, sandbox, versioned
  prompts, provenance, audit, kill switch, rollback.
- **Classification:** SAFE TO EXPAND (rules, terminology, data extraction);
  REQUIRES HARDENING (CDS alerts, clinical analysis); EXPERIMENTAL (RAG over
  clinical data, knowledge graph); **NEVER silently clinical** (AI output is
  always advisory; human decision-maker retains authority).
- AI admin endpoints must be authenticated (P0 fix).

---

## 11. Observability & Disaster Recovery (target)

- Health tiers `/health`, `/health/ready`, `/health/deep`; Prometheus metrics
  (role-gated), OTLP/HTTP tracing (vendor-neutral), JSON logs, SLO alerts,
  Alertmanager, dashboards. Already real; keep + expand.
- DR: nightly pg_dump + WAL→S3 (RPO≈1 min, verified 2026-08-06); restore drill
  quarterly; document RTO (<4 h target); encrypted off-site copies.

---

## 12. Delivery Waves (target, dependency-ordered)

Detailed in `GULA_MASTER_EXECUTION_PLAN.md`. Summary: Wave 0 recovery →
Wave 1 state+gap (this set) → Wave 2 architecture reconciliation →
Wave 3 identity/account/org/authz → Wave 4 app shell + workspaces →
Waves 5–9 clinical domains + engines → Wave 10 integration hub → Wave 11
offline/DR → Wave 12 national control plane → Wave 13 AI → Wave 14
entitlements → Wave 15 security/scale certification → Waves 16–17 pilot +
production expansion.

---

## 13. Constraints & Deferrals

- **Wave B of the successor program is NOT authorized** (needs PD approval; branch `wave-b/B1-abac-route-enforcement` unmerged).
- **National data flow is legally gated** — no national data sharing without Iraq legal/governance sign-off.
- **v1.0.0 tag / GitHub release deferred** (ADR-037 §8).
- **B-8 (frontend-v3 rename) deferred.**
- **No new fragmented applications.** All domains via workspaces in the four platform apps.
- **No vendor lock-in** — every component replaceable (PostgreSQL/Redis/MinIO/self-hosted AI).

---

*This document describes the TARGET. It is explicitly not a claim that the
current repository implements all of it. See `GULA_MASTER_GAP_MATRIX.md` for
the verified delta.*

# GULA — Dependency Graph

**Document class:** AUTHORITATIVE dependency map (current + target)
**Date:** 2026-08-11
**Basis:** Verified at HEAD `f735a7a1`; companion to GULA_MASTER_EXECUTION_PLAN.md.

---

## 1. Current Dependency Layers

```
┌ L0 ── Infra ──────────────────────────────────────────────┐
│ PostgreSQL 16 (system of record) · Redis 7 · MinIO/object │
│ storage · Docker Compose · k8s base + overlays · helm     │
└────────────┬──────────────────────────────────────────────┘
             ▼
┌ L1 ── ONE GULA CORE (backend) ──────────────────────────────┐
│ factory.py · middleware (CORS, headers, request ID,         │
│ concurrency, degraded, OTLP, rate limit, body limit)        │
│ 82 routers → 1,643 paths · 57-migration chain               │
│ kernel (event bus/outbox/inbox/DLQ/replay/recovery)         │
│ shared (audit, notifications, search, PDF, rules, workflows)│
└─────┬─────────┬──────────┬──────────┬───────────────────────┘
      ▼         ▼          ▼          ▼
┌ L2 ── Identity ──┐ ┌ L2 ── Clinical ──────┐ ┌ L2 ── Interop ────┐
│ NIAM (identity,   │ │ ehr · lims ·        │ │ FHIR R4 · HL7 v2  │
│ workspaces, RBAC, │ │ radiology/ris/pacs  │ │ DICOM · RIS · LIS │
│ ABAC, MFA, OAuth, │ │ pharmacy · hospital │ │ interoperability/ │
│ sessions, audit)  │ │ ems · blood_bank ·  │ │ (ZERO importers)  │
│                   │ │ public_health · mpi │ │                   │
│                   │ │ nhdw · national ·   │ │                   │
│                   │ │ research            │ │                   │
└───────────────────┘ └─────────────────────┘ └───────────────────┘
      ┌───────────────────────┴────────────────────────┐
      ▼                                                  ▼
┌ L3 ── Clients ──────────────────────────────────────────────┐
│ frontend-v3 (React 19 / PWA) · Android (Compose/Room) ·     │
│ iOS (BROKEN) · Desktop Flutter (drift gen missing) ·        │
│ root experimental server+client (Node/tRPC)                 │
└─────────────────────────────────────────────────────────────┘
```

## 2. Key Dependency Rules (target)

1. **Clients depend on the API contract only** — never on internal backend modules.
2. **Domains depend on the Shared Core (canonical providers)** — never on other
   domains' internals (Domain Platform isolation, hard gate).
3. **Backend depends on `shared/` (mountable, read-only in container)**.
4. **One canonical API base domain** (currently 3 divergent — M-08, P1).
5. **Interoperability standards** (FHIR/HL7/DICOM/RIS/LIS) exposed via the
   canonical integration surface; `interoperability/` must be wired or retired.

## 3. Concrete Dependencies (verified highlights)

| From | To | Nature | Status |
|---|---|---|---|
| All clients | `/api/*` (backend) | HTTP contract | REAL (3 base domains — fix) |
| backend | PostgreSQL 16 | system of record | REAL |
| backend | Redis 7 | cache/queues/blacklist | REAL |
| backend | `shared/` | code module mount | REAL (container) |
| domain modules | `kernel/event_bus` | outbox/inbox/DLQ | REAL |
| domain modules | `shared/` providers | audit/notifications/search/pdf/rules/workflows | REAL (canonical) |
| AI providers | Ollama (local) + cloud keys | inference | REAL (stub default; S1 leak) |
| Desktop | drift codegen | DB layer | **BROKEN** (placeholder) |
| iOS | Xcode project/Core Data | build system | **BROKEN** (empty) |
| deploy pipeline | SSH target + cosign + health | rollout | REAL |
| DR | S3/WAL | backup/restore | REAL (RPO≈1 min) |

## 4. Dependency Risks

| Risk | Link |
|---|---|
| Circular module imports prevented by Domain Platform isolation | G1 (architecture gate) |
| `services/*` microservice stubs imply independence they do not have | N-04/P3 |
| Root Dockerfile targets experimental app — deployment ambiguity | R-14 |
| 3 API base domains → client drift / config errors | R-05 |
| Drift codegen placeholder → desktop offline claims invalid | R-04 |
| iOS missing build system → store metadata claims invalid | R-01 |

## 5. Suggested Refactor Priorities (dependency-ordered)

1. Unify API base domain (M-08) — unblocks all clients.
2. Wire or retire `interoperability/` (B-06) — resolves false advertising.
3. Decide iOS (D-1) and Desktop (D-2) — resolves R-01/R-04.
4. Build consent primitives on `legal/` (B-12) — unblocks Wave 3 + Purpose-of-Use.
5. Reconcile root experimental app (D-4) — removes deployment ambiguity.

---

*Graph reflects the verified current state; the target adds nothing new at L0/L1.
Companion: `GULA_TARGET_ARCHITECTURE.md`, `GULA_MASTER_EXECUTION_PLAN.md`.*

# PROGRAM NEXT-PHASE PLAN — Identity, Authorization, Clinical Safety
**Status:** PLANNING ONLY — no implementation, no code, no migrations, no APIs, no UI
**Authority:** Approved by the Program Director as the authoritative successor
program to PROGRAM-REPO-01 (ADR-037, 2026-08-10). Wave A is NOT authorized by
this plan; each wave requires separate Program Director authorization.
**Date:** 2026-08-09
**Prerequisite:** PROGRAM-REPO-01 certified complete

> This document defines the architecture and dependency plan for the next
> program. It explicitly does **not** modify clinical behavior, create database
> migrations, create APIs, create UI, or start any implementation. The modules
> below are planned as the strategic national-safety platform direction.

---

## 1. Program Goal

Transition the GULA platform from repository/release readiness toward a
**national clinical-safety and identity-governed platform**, preserving the
permanent platform constitution (FHIR R4, HL7, ISO 15189, CAP, CLSI,
multi-tenancy, RBAC/ABAC, immutable audit, offline-first, Arabic-first,
ministry hierarchy, event bus, national compatibility).

## 2. Planned Capability Modules (18)

| # | Module | Core Deliverable (planned) |
|---|---|---|
| 1 | Identity & Account Management | Unified national identity lifecycle on top of NIAM IdentityType (11 canonical types) + citizen registry |
| 2 | RBAC / ABAC | Policy-driven authorization: roles (RBAC) + attributes (ABAC) combined engine |
| 3 | Citizen Account | Self-service citizen portal account bound to citizen registry |
| 4 | Professional Workspaces | Workspace platform extended to professional practice contexts |
| 5 | Organization / Facility hierarchy | Ministry → Directorate → Hospital → Lab hierarchy as an organizational graph |
| 6 | National professional authorization | Verify() privilege-activation expanded to national professional licensing |
| 7 | Ministry / Syndicate authority separation | Distinct authority scopes for MoH vs professional syndicates (zero cross-administration) |
| 8 | Immutable Audit | Hash-chained, append-only audit extended to national level |
| 9 | Purpose-of-Use access | Consent + purpose-bound access to patient data |
| 10 | Minimum Necessary Disclosure | Data-minimization engine for disclosure of patient records |
| 11 | Clinical Safety Alerts | Alert engine for high-risk clinical events |
| 12 | Infection Prevention & Control | Infection surveillance and IPC module |
| 13 | Occupational Exposure / Needlestick | Staff exposure incident capture |
| 14 | PEP workflow | Post-exposure prophylaxis protocol workflow |
| 15 | Incident Management | Clinical incident capture + investigation workflow |
| 16 | CAPA | Corrective & preventive action lifecycle |
| 17 | IPC Training / Competency | Training records + competency assessment |
| 18 | National safety dashboards | National aggregate safety reporting |

## 3. Dependency Graph (topological order)

```
Layer 0  Identity & Account Management  ──────────┐
         Immutable Audit                          │
         ─────────────────────────────────────────┘
Layer 1  RBAC / ABAC
         Citizen Account
         Professional Workspaces
         Organization / Facility hierarchy
Layer 2  National professional authorization
         Ministry / Syndicate authority separation
Layer 3  Purpose-of-Use access
         Minimum Necessary Disclosure
Layer 4  Clinical Safety Alerts
Layer 5  Infection Prevention & Control
         Occupational Exposure / Needlestick
Layer 6  PEP workflow
         Incident Management
Layer 7  CAPA
Layer 8  IPC Training / Competency
Layer 9  National safety dashboards
```

No module in a higher layer can start before its dependencies are certified.

## 4. Prerequisite Analysis

| Prerequisite | Current state | Required before |
|---|---|---|
| **Identity** | NIAM IdentityType 11 canonical types; workspaces; citizen registry; professional registry; sessions; org guard | Layers 0–3 |
| **Authorization** | RoleAssignments, permission checks, professional verify(), workspace check_permission, domain guard | Layers 1–4 |
| **Audit** | 29 PROGRAM-STABLE-003 audit actions + 25 PRO-01 baseline; hash-chain design | Layer 0 and every module (audit events per module) |
| **Clinical data** | FHIR R4 models, EHR domain, samples/results/QC, national workflows | Layers 4–6 |
| **FHIR** | FHIR R4 resources, ehr_fhir, HL7 adapters | Layers 4–6 |
| **Notifications** | canonical notification service + queue; event bus (in-process) | Layer 4 onward (alerts) |
| **Offline** | offline-first sync, offline-gate (PWA sw + IndexedDB + degraded mode) | Layers 4–6 (field IPC) |
| **Security/privacy** | encryption engine, session security, coordinated disclosure, security module | all layers; Purpose-of-Use/Minimum Necessary require consent + minimization primitives |
| **Legal/governance (Iraq)** | — | Required before any national data sharing: |

### 4.1 Iraq legal & governance dependencies (to be confirmed with stakeholders)

- Health data protection law / personal data protection law provisions
- MoH licensing and authorization flows (laboratory + professional)
- Syndicate (medical/technical) statutory authority boundaries
- National identifier usage rules and purpose constraints
- Ministry data-sharing agreements and audit disclosure rules
- Clinical governance / ISO 15189 accreditation requirements
- Notification/consent norms for occupational exposure (labor law)

**These are dependencies, not blockers for planning** — design must assume them
and expose configuration points, but implementation of national data flow is
gated on stakeholder sign-off.

## 5. Implementation Waves (planned, in order)

| Wave | Scope | Exit criteria (acceptance) |
|---|---|---|
| A | Identity hardening + Immutable Audit complete | Full identity lifecycle; audit chain verifiable; 0 auth findings |
| B | RBAC/ABAC engine + hierarchy model | Policy engine tests; organization graph certified; domain 11/11 preserved |
| C | Professional authorization + authority separation | Privilege activation national-scale; ministry/syndicate zero cross-admin |
| D | Purpose-of-Use + Minimum Necessary Disclosure | Consent model; disclosure minimization tests |
| E | Clinical Safety Alerts + IPC | Alert engine live; IPC surveillance data model |
| F | Occupational exposure + PEP + Incident + CAPA | Workflows live with FHIR representations |
| G | IPC Training/Competency + National dashboards | Competency records; national aggregate reporting |

## 6. Risk & Rollback

| Risk | Mitigation | Rollback |
|---|---|---|
| National data-sharing legal exposure | Gate on Iraq legal sign-off; country-agnostic core with national config | Feature-flag off; no data shipped |
| Clinical-safety alert false positives | Alert engine behind activation flag; simulation/validation harness | Disable module flag |
| ABAC complexity | Incremental: RBAC first, ABAC attributes additive | Revert policy commit |
| Scope creep beyond constitution | Every ADR; domain isolation; architecture gate hard | `git revert` per commit |
| Concurrent-session interference | Commit isolation protocol (as PROGRAM-REPO-01) | per-commit revert |

## 7. Acceptance Criteria (program-level)

1. All modules certified against Architecture Constitution gate (0 new findings)
   and Domain Platform (11/11).
2. Identity/authorization/audit prerequisites proven before clinical modules.
3. Full backend suite green (5089+ baseline) after every wave; ruff baseline
   preserved; tsc/eslint/vitest green.
4. Offline-first and Arabic-first preserved for field-facing modules.
5. Immutable audit hash-chain verifiable end-to-end.
6. No national data-sharing without Iraq legal/governance sign-off.
7. Production readiness declared only by Program Director, never by program
   completion alone.

---

**This document is planning only. Approved as the authoritative successor
program (ADR-037). Await Program Director authorization before any
next-program execution.**

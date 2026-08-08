# Architecture Constitution — GULA National Healthcare Platform

> **PROGRAM-ALPHA, Phase 7.** Permanent architectural gates. Every Pull Request
> that touches application code MUST pass the `architecture-check` gate in CI.
> A PR **automatically fails** if it introduces any violation of the rules below.
>
> **PROGRAM-01 FINAL CLOSURE — ARCHITECTURE LOCKED.** Baseline frozen at
> **25 acknowledged findings** (19 Domain-Owned, 1 Strategic
> Exception, 3 kernel-domain register, 2 False Positive) + **2 resolved**
> (encryption) = **0 actionable**. The gate now fails on ANY new or re-grown
> finding. See `PROGRAM_01_FINAL_CERTIFICATION.md`.

## 1. Preamble

GULA is a sovereign national healthcare platform. Its architecture is protected
by a permanent constitution that no feature, module, or bounded context may
weaken. The constitution is enforced deterministically by
`scripts/architecture/` and the Domain Platform Framework
(`backend/app/domain_platform`). Acknowledged legacy debt is tracked in
`.ai/core/architecture/constitution_baseline.json` and must be migrated — never grown.

## 2. The Ten Commandments

1. **Never duplicate infrastructure.** Every reusable service exists exactly
   once, in its canonical provider, and is consumed through Shared Core.
2. **Never duplicate business logic.** Domains own their business logic; shared
   logic lives only in Shared Core.
3. **Never create another identity implementation.** NIAM
   (`backend/app/identity`) is the only identity platform.
4. **Never create another notification system.** The platform notification
   core is the only delivery system.
5. **Never create another audit system.** The immutable audit core is the only
   audit log.
6. **Never create another barcode/QR engine.** `shared/barcode` + `shared/qr`
   are the only engines.
7. **Never break Shared Core.** Domains consume Shared Core; they never
   reimplement or fork it.
8. **Never break Domain Sovereignty.** Every Domain owns its entities, logic,
   policies, validation, reports, events, UI and APIs — and nothing else.
9. **Never break Workspace isolation.** Permissions never cross workspaces;
   a workspace never renders another workspace's UI.
10. **Never break Country-Agnostic design.** Country-specific behaviour lives
    only in the national layer, never hard-coded in a Domain.

## 3. Shared Core — single authoritative registry

Every Shared Core service maps to exactly ONE provider. The registry is
`SHARED_CORE_CATALOG` in `backend/app/domain_platform/shared_core.py`
(**16 guarded capabilities**).

| Rule | What is prohibited | Canonical provider(s) |
|---|---|---|
| `identity` | A new identity/authentication implementation outside the NIAM identity platform. | canonical: `backend/app/identity, shared/identity, backend/app/security` |
| `authentication` | A new password/JWT/MFA/SSO implementation outside shared/auth + NIAM. | canonical: `backend/app/identity, backend/app/security, shared/auth` |
| `authorization` | A new RBAC/ABAC permission implementation outside the platform. | canonical: `backend/app/identity, backend/app/security, shared/rbac` |
| `notifications` | A new notification delivery system outside the platform notification core. | canonical: `backend/app/notifications, shared/notifications, shared/communication, shared/communication_providers` |
| `audit` | A new audit-log implementation outside the platform audit core. | canonical: `shared/audit, backend/app/identity/models/audit.py, backend/app/identity/services/audit_service.py, backend/app/services/audit_service.py, backend/app/audit` |
| `workflow_engine` | A new workflow engine outside the platform workflow core. | canonical: `shared/workflow, backend/app/workflows, backend/app/capabilities/workflow_engine` |
| `rule_engine` | A new business-rules engine outside the platform rules core. | canonical: `shared/rules_engine, backend/app/rules` |
| `barcode_engine` | A new barcode generator/decoder outside shared/barcode. | canonical: `shared/barcode` |
| `qr_engine` | A new QR generator/decoder outside shared/qr. | canonical: `shared/qr` |
| `search_engine` | A new search implementation outside the platform search core. | canonical: `shared/search.py, backend/app/capabilities/search_service` |
| `encryption` | A new encryption/crypto implementation outside shared/security. | canonical: `shared/security, backend/app/security` |
| `cache` | A new cache backend outside shared/cache. | canonical: `shared/cache` |
| `events` | A new event bus outside shared/events. | canonical: `shared/events` |
| `dependency_injection` | A new DI container outside shared/di_container. | canonical: `shared/di_container` |
| `scheduler` | A new scheduler outside shared/scheduler. | canonical: `shared/scheduler.py` |
| `document_engine` | A new document/PDF engine outside the platform document core. | canonical: `backend/app/capabilities/document_management, shared/pdf` |

## 4. Enforcement gates

| Gate | Mechanism | Failure mode |
|---|---|---|
| Shared Core scan | `architecture-scan` — regex signal scan of `backend/app` + `shared` | Any finding not in the acknowledged baseline fails the PR |
| Domain certification | `domain-certify` — 9 checks per Domain (isolation, sovereignty, contracts, backward-compat) | Any Domain not 100% certified fails the PR |
| Workspace binding | Domain Platform `WorkspaceBindingRegistry` | Cross-workspace UI binding fails the PR |
| Country-agnostic | `architecture-country` — national markers outside the national layer | Any marker fails the PR |
| CI hard gate | `architecture-check` in `ai-governance.yml` | Exit code != 0 blocks merge |

## 5. Acknowledged legacy debt

The following Shared Core capabilities already contain legacy reimplementation
candidates. They are tracked for migration and are **blocked from growing**:
new files matching a rule fail the gate, even while legacy files remain.

- **acknowledged findings:** 25 across 11 rule(s)
  (`audit, authorization, barcode_engine, dependency_injection, document_engine, events, identity, notifications, qr_engine, scheduler, search_engine`)

See `MASTER_REMAINING_WORK.md` for the migration plan for each item.

## 6. Amendments

Amending the constitution requires: an ADR, a documented engineering rationale,
a negative-impact analysis, and explicit human approval. This document is
re-generated by `architecture-constitution`.

_Generated 2026-08-08 by scripts/architecture._

# GULA Platform — Roadmap

**Last updated:** 2026-07-24

---

## Project Status

The GULA Platform is currently in **active production use** with a stable feature
set covering laboratory management, EHR, security, and identity. The project has
completed its core platform foundation and is expanding into national-scale
healthcare modules.

## Completed Milestones

### Foundation (v1.0 - v2.1)
- ✅ Core LIMS: orders, specimens, results, quality control
- ✅ Multi-tier SaaS subscription model
- ✅ RBAC with 9 roles and granular permissions
- ✅ JWT authentication with token rotation
- ✅ Docker Compose deployment with PostgreSQL + Redis
- ✅ Arabic-first UI with full RTL support
- ✅ Lab instrument integration (ASTM/HL7)
- ✅ Offline-capable architecture

### National Platform (v2.2 - v2.3)
- ✅ National EHR Platform with FHIR R4
- ✅ National Health Data Platform and Analytics
- ✅ National Citizen Super App (mobile + PWA)
- ✅ National Doctor Clinical Workspace
- ✅ National Laboratory Desktop Professional
- ✅ Hospital Desktop Workspace (NHDW)
- ✅ Nursing & Care Coordination Platform
- ✅ Pharmacy Information Platform (NPIP)
- ✅ Radiology Information System & PACS (NRISP)
- ✅ Health Intelligence & AI Platform

### Engineering & Quality (v2.1+)
- ✅ Engineering Factory automation (code generation, CLI tools)
- ✅ Capability-driven development framework
- ✅ Quality gates, architecture compliance, scorecard
- ✅ Comprehensive CI/CD (18 GitHub Actions workflows)
- ✅ Security auditing (SAST, DAST, dependency scanning)
- ✅ Chaos engineering and resilience testing

### Constitution & Governance
- ✅ Platform Constitution (PROGRAM-CONSTITUTION-001)
- ✅ National Trust, Compliance & Privacy Platform
- ✅ Autonomous Platform Factory
- ✅ Free-First, Open-Source-First, Self-Hosted-First policies

## Current Focus

### Authorization Expansion (In Progress)

The authorization system is being expanded to support national-scale
identity and access management. See the detailed plan below.

## Near-Term Roadmap (Next 3 months)

| Priority | Area | Description |
|----------|------|-------------|
| P0 | Authorization | Role-based access expansion (1,284 permissions, 171 roles) |
| P0 | Frontend Auth | Backend-driven menus, routes, and component security |
| P0 | Offline Sync | Production-ready offline synchronization engine |
| P1 | Field Security | Field-level data masking and access control |
| P1 | Role Preview | Role simulation and visual certification |
| P1 | CI/CD Hardening | Reproducible builds, signed releases, SBOM automation |
| P2 | Performance | Query optimization, caching layer enhancements |
| P2 | Documentation | API reference, user guides, deployment cookbook |

## Medium-Term Roadmap (3-12 months)

| Area | Description |
|------|-------------|
| Multi-Region | Active-active deployment across governorates |
| Telemedicine | Integrated video consultation platform |
| Blood Bank | National blood bank management system |
| Emergency | Emergency department information system |
| Research | Clinical research data platform |
| Open Source | Community building, contributor documentation, governance maturity |

## Long-Term Vision

- National-scale health information exchange across Iraq
- AI-powered clinical decision support at point of care
- Interoperability with international health information systems
- Full FHIR R4 compliance across all clinical domains
- Community-driven open-source governance model

---

The remainder of this document details the **Authorization Expansion** roadmap,
which is the current active workstream.

---

# GULA Platform — Authorization Expansion Roadmap

**Version:** 1.0.0

---

## Overview

This roadmap outlines the phased implementation of the national-scale identity and authorization system. All phases build on the existing platform without removing any current functionality.

---

## Phase A: Foundation (Weeks 1-2)

### A.1 Backend Data Models

| Model | Priority | Description |
|-------|----------|-------------|
| `UserType` | P0 | 64 user type definitions |
| `Role` | P0 | 171 role definitions with hierarchy |
| `Permission` | P0 | 1,284 permission definitions |
| `RoleAssignment` | P0 | User-role-organization scoped assignments |
| `RoleGroup` | P1 | Role grouping and templates |
| `Policy` | P1 | ABAC policy model |
| `FieldSecurity` | P1 | Field-level security definitions |
| `Tenant` | P0 | Multi-tenant hierarchy model |
| `Identity` | P0 | 18 identity types unified model |
| `Delegation` | P1 | Delegation records |
| `BreakGlassSession` | P1 | Emergency access sessions |
| `AuthorizationAudit` | P0 | Authorization decision log |

### A.2 Backend Service Layer

| Service | Priority | Description |
|---------|----------|-------------|
| `PermissionService` | P0 | Permission resolution and checking |
| `RoleService` | P0 | Role management and inheritance |
| `RBACService` | P0 | RBAC evaluation engine |
| `ABACService` | P1 | ABAC attribute collection and policy evaluation |
| `IdentityService` | P0 | Identity registration and verification |
| `TenantService` | P0 | Tenant context and isolation |
| `FieldSecurityService` | P1 | Field-level access evaluation |
| `DelegationService` | P1 | Delegation management |
| `BreakGlassService` | P1 | Emergency access management |
| `AuthorizationAuditService` | P0 | Audit logging |
| `PolicyService` | P1 | Policy lifecycle management |

---

## Phase B: Authorization APIs (Weeks 3-4)

### B.1 Core Endpoints

| Endpoint | Priority | Description |
|----------|----------|-------------|
| `POST /authz/check` | P0 | Single permission check |
| `POST /authz/check-batch` | P0 | Batch permission check |
| `GET /authz/permissions` | P0 | Get user permissions |
| `GET /authz/roles` | P0 | List roles |
| `GET /authz/roles/:id` | P0 | Get role with permissions |
| `GET /authz/menus` | P0 | Dynamic menu tree |
| `GET /authz/routes` | P0 | Allowed routes |
| `GET /authz/field-security/:resource` | P1 | Field security for resource |
| `GET /authz/widgets` | P1 | Dashboard widgets |
| `GET /authz/actions` | P1 | Allowed actions |
| `GET /authz/me` | P0 | Full authorization context |
| `POST /authz/break-glass` | P1 | Emergency access |
| `GET /authz/delegations` | P1 | User delegations |

### B.2 Admin Endpoints

| Endpoint | Priority | Description |
|----------|----------|-------------|
| CRUD `/rbac/roles` | P0 | Role management |
| CRUD `/rbac/permissions` | P0 | Permission management |
| CRUD `/rbac/assignments` | P0 | Role assignment |
| CRUD `/rbac/groups` | P1 | Role group management |
| CRUD `/policies` | P1 | Policy management |
| GET `/policies/:id/simulate` | P1 | Policy simulation |
| CRUD `/tenants` | P1 | Tenant management |
| CRUD `/identities` | P1 | Identity management |

---

## Phase C: Frontend Authorization Engine (Weeks 5-6)

### C.1 Core Modules

| Module | Priority | Description |
|--------|----------|-------------|
| `AuthzProvider` | P0 | React context for authorization |
| `usePermission` | P0 | Hook: check permission |
| `usePermissions` | P0 | Hook: list user permissions |
| `useRoles` | P0 | Hook: get user roles |
| `useMenus` | P0 | Hook: get dynamic menu tree |
| `useRoutes` | P0 | Hook: get allowed routes |
| `useFieldSecurity` | P1 | Hook: get field security |
| `useActions` | P1 | Hook: get allowed actions |
| `useWidgets` | P1 | Hook: get dashboard widgets |
| `useAuthorizationContext` | P0 | Hook: get full authz context |

### C.2 Components

| Component | Priority | Description |
|-----------|----------|-------------|
| `<RequirePermission>` | P0 | Conditional render by permission |
| `<RequireRole>` | P0 | Conditional render by role |
| `<ProtectedField>` | P1 | Field-level security component |
| `<ProtectedAction>` | P1 | Action security component |
| `<DynamicMenu>` | P0 | Backend-driven menu |
| `<DynamicRouter>` | P0 | Backend-driven routing |
| `<DynamicDashboard>` | P1 | Backend-driven dashboard |
| `<RolePreviewBanner>` | P1 | Role preview mode banner |
| `<FieldSecurity>` | P1 | Field-level rendering component |

### C.3 Demo Users (Phase 18+19)

| Artifact | Priority | Description |
|----------|----------|-------------|
| Demo user accounts | P2 | Account for every role with realistic data |
| Demo patient records | P2 | 100+ patients with complete clinical records |
| Demo data factory | P2 | Script to generate internally consistent demo data |
| Demo scripts | P2 | Database seeding scripts |

---

## Phase D: UI Profiles & Dashboards (Weeks 7-8)

### D.1 Role-Specific UIs

| Profile | Priority | Users |
|---------|----------|-------|
| Citizen Dashboard | P2 | Citizens, Patients, Guardians |
| Doctor Dashboard | P1 | Physicians, Specialists, Consultants |
| Lab Dashboard | P1 | Lab technicians, Pathologists, Microbiologists |
| Hospital Dashboard | P1 | Hospital directors, Medical directors |
| Ministry Dashboard | P1 | Ministry directors, Governorate directors |
| Auditor Dashboard | P2 | Auditors, Compliance officers |
| Admin Dashboard | P1 | System administrators |
| Emergency Dashboard | P2 | Emergency physicians, Paramedics |
| Blood Bank Dashboard | P2 | Blood bank staff |
| Radiology Dashboard | P2 | Radiologists, Technicians |
| Research Dashboard | P2 | Researchers, Trial coordinators |

### D.2 Dynamic Menu Engine (Phase 13)

| Feature | Priority | Description |
|---------|----------|-------------|
| Backend menu API | P0 | GET /authz/menus returns menu tree |
| Menu caching | P1 | Cache menu tree with role-based invalidation |
| Menu filtering | P0 | Remove inaccessible items |
| Menu ordering | P1 | Configurable per-role ordering |
| Menu search | P2 | Global menu search |

### D.3 Dynamic Routing (Phase 14)

| Feature | Priority | Description |
|---------|----------|-------------|
| Backend routes API | P0 | GET /authz/routes returns allowed routes |
| Route filtering | P0 | Block navigation to unauthorized routes |
| Route redirect | P0 | Redirect to fallback on unauthorized |
| Lazy route registration | P0 | Register routes from backend data |

---

## Phase E: Component & Field Security (Weeks 9-10)

### E.1 Component Security

| Feature | Priority | Description |
|---------|----------|-------------|
| `<ProtectedButton>` | P1 | Button with permission check |
| `<ProtectedTable>` | P1 | Table with column-level security |
| `<ProtectedTab>` | P1 | Tab visibility by permission |
| `<ProtectedDialog>` | P1 | Dialog access control |
| `<ProtectedAction>` | P1 | Action visibility |

### E.2 Field-Level Security

| Feature | Priority | Description |
|---------|----------|-------------|
| Backend field security API | P1 | GET /authz/field-security/:type |
| `<ProtectedField>` renderer | P1 | Hidden/readonly/masked/editable |
| Masking component | P1 | Phone, national ID, email masking |
| Encrypted field handling | P2 | Decrypt on authorized access |
| Dynamic form builder | P2 | Form rendered from field security |

---

## Phase F: Role Preview & Certification (Weeks 11-12)

### F.1 Role Preview Mode

| Feature | Priority | Description |
|---------|----------|-------------|
| Preview API | P1 | GET /authz/preview/:roleId |
| Preview context | P1 | Override user context with role |
| Preview banner | P1 | "ROLE PREVIEW MODE" indicator |
| Preview restrictions | P1 | No mutations in preview mode |
| Preview exit | P1 | Return to normal mode |

### F.2 Visual Certification (Phase 20)

| Feature | Priority | Description |
|---------|----------|-------------|
| Role certification script | P1 | Automated permission audit per role |
| Visible/hidden page report | P1 | Per-role page accessibility |
| Allowed/denied API report | P1 | Per-role API accessibility |
| Role_visual_certification.md | P1 | Generated report |

### F.3 Auth Synchronization (Phase 21)

| Feature | Priority | Description |
|---------|----------|-------------|
| Sync script | P1 | Backend → Frontend auth artifact sync |
| Build-time check | P1 | Fail build if auth metadata inconsistent |
| Auth_sync_report.md | P1 | Generated sync report |
| Frontend_backend_parity_report.md | P1 | Generated parity report |
| Permission_coverage_report.md | P1 | Generated coverage report |

---

## Timeline Summary

```
Week 1-2:  [████████░░] Phase A — Backend models + services
Week 3-4:  [████████░░] Phase B — Authorization APIs
Week 5-6:  [████████░░] Phase C — Frontend auth engine
Week 7-8:  [████░░░░░░] Phase D — UI profiles + dynamic menus/routing
Week 9-10: [████░░░░░░] Phase E — Component + field security
Week 11-12:[████░░░░░░] Phase F — Role preview + certification + sync
```

## Dependencies

- Phase A: No external dependencies
- Phase B: Depends on Phase A (models)
- Phase C: Depends on Phase B (APIs)
- Phase D: Depends on Phase C (auth engine)
- Phase E: Depends on Phase C (auth hooks)
- Phase F: Depends on Phase A-F (all prior phases)

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Performance of real-time ABAC | Medium | High | Cache policies, batch attribute collection |
| Migration of existing users | Medium | High | Backward-compatible API, progressive rollout |
| Frontend-backend synchronization lag | Low | Medium | Build-time validation, CI fail on mismatch |
| Complexity of 1,284 permissions | Low | Medium | Automated generation, hierarchical structure |

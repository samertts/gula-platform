# NIAM — National Identity & Access Management Platform Architecture

## Overview

NIAM (NIAM Is Access Management) is the sovereign identity provider for the entire GULA National Digital Health Platform. It is a **completely independent domain** from the laboratory module — it manages who people are, how they authenticate, what they are authorized to do, and tracks every identity-related event with an immutable audit trail.

NIAM replaces the tightly-coupled `Lab`/`LabUser` authentication model with a generalized, healthcare-enterprise-grade identity system that covers citizens, government workforce, private workforce, machines, and external federated identities.

---

## Domain Model

```
                    ┌─────────────────────────────────────────────────────────────┐
                    │                     PERSON                                   │
                    │  (the natural person — exists once, globally)                │
                    │  given_name, family_name, birth_date, nationality,           │
                    │  national_id_hash, health_id, phone, email, ...              │
                    └────────────┬────────────────────────────────────────────────┘
                                 │
                    ┌────────────▼────────────────────────────────────────────────┐
                    │                     IDENTITY                                │
                    │  (verifiable claims about a person in a specific context)    │
                    │  identity_type: citizen | government_workforce | private     │
                    │                enterprise | machine | guest | temporary      │
                    │  status, verified_at, issued_by_organization, expires_at     │
                    └────────────┬────────────────────────────────────────────────┘
                                 │
                    ┌────────────▼────────────────────────────────────────────────┐
                    │                     ACCOUNT                                  │
                    │  (login credentials — the authentication principal)          │
                    │  account_type: human | machine | service | system            │
                    │  email, phone, username, password_hash, mfa_*, locked_*      │
                    └────────────┬────────────────────────────────────────────────┘
                                 │
              ┌──────────────────┼──────────────────────┐
              ▼                  ▼                       ▼
    ┌─────────────────┐ ┌──────────────┐ ┌──────────────────────┐
    │   CREDENTIAL     │ │   SESSION    │ │      DEVICE          │
    │ password,passkey,│ │ token_jti,   │ │ fingerprint,trusted, │
    │ fido2, api_key,  │ │ refresh_jti, │ │ public_key, os,      │
    │ certificate,...  │ │ ip, expires  │ │ browser, manufacturer │
    └─────────────────┘ └──────────────┘ └──────────────────────┘

                    ┌─────────────────────────────────────────────────────────────┐
                    │                 ORGANIZATION                                 │
                    │  (healthcare org hierarchy node)                             │
                    │  ministry → directorate → hospital/phc/lab → department     │
                    │  org_type, parent_org_id, governorate, accreditation        │
                    └────────────┬────────────────────────────────────────────────┘
                                 │
                    ┌────────────▼────────────────────────────────────────────────┐
                    │                  EMPLOYMENT                                  │
                    │  (person works at an organization)                           │
                    │  employee_id, position, department, start_date, end_date,   │
                    │  supervisor, primary_employment, contract_type, transfers   │
                    └────────────┬────────────────────────────────────────────────┘
                                 │
                    ┌────────────▼────────────────────────────────────────────────┐
                    │                 ASSIGNMENT                                   │
                    │  (person assigned to role/position at org/facility/dept)     │
                    │  role_id, assignment_type, facility_id, department_id,       │
                    │  is_primary, is_temporary, is_emergency, delegated           │
                    └─────────────────────────────────────────────────────────────┘

                    ┌─────────────────────────────────────────────────────────────┐
                    │              ADDITIONAL DOMAINS                              │
                    │                                                              │
                    │  PROFESSIONAL_LICENSE — medical/lab/pharmacy licenses        │
                    │  MACHINE_IDENTITY        — non-human device/host identity    │
                    │  ENTERPRISE_ACCOUNT  — org-level API/OAuth2 credentials      │
                    │  POLICY                       — ABAC policy definitions      │
                    │  AUDIT_ENTRY         — immutable identity event log          │
                    └─────────────────────────────────────────────────────────────┘
```

---

## Layer Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            API LAYER                                     │
│  FastAPI routers under /niam prefix                                      │
│  ├── /niam/persons/     ── Person CRUD                                   │
│  ├── /niam/accounts/   ── Account management (lock/unlock)              │
│  ├── /niam/auth/        ── Login, refresh, logout                        │
│  ├── /niam/sessions/    ── Session listing and termination               │
│  ├── /niam/devices/     ── Device registration and trust                 │
│  └── /niam/health       ── NIAM health check                             │
├─────────────────────────────────────────────────────────────────────────┤
│                           SERVICE LAYER                                   │
│  Business logic, orchestration, security enforcement                      │
│  ├── PersonService         ── Person CRUD, search, deactivation          │
│  ├── IdentityService       ── Identity issuance, verification, revoke    │
│  ├── AccountService        ── Account creation, auth, lockout, password  │
│  ├── AuthenticationService ── Login flow, session create, refresh, logout│
│  ├── SessionService        ── Session lifecycle, activity tracking       │
│  ├── DeviceService         ── Device registration, trust, revocation     │
│  ├── AuthorizationService  ── Permission checks, assignment queries      │
│  └── AuditService          ── Event recording, audit trail               │
├─────────────────────────────────────────────────────────────────────────┤
│                         REPOSITORY LAYER                                   │
│  Data access with soft-delete filtering and domain-specific queries        │
│  ├── PersonRepository      ├── AccountRepository                          │
│  ├── IdentityRepository    ├── SessionRepository                          │
│  ├── OrganizationRepository├── DeviceRepository                           │
│  ├── EmploymentRepository  ├── AssignmentRepository                       │
│  └── Base: IdentityRepositoryBase[T] — CRUD, soft delete, uuid lookup    │
├─────────────────────────────────────────────────────────────────────────┤
│                         MODEL LAYER                                        │
│  15 SQLAlchemy ORM models mapped to niam_* tables                         │
│  ├── Person                ├── Account                  ├── UserSession  │
│  ├── IdentityRecord        ├── NIAMOrganization         ├── Device       │
│  ├── Employment            ├── Assignment               ├── Credential   │
│  ├── IdentityPolicy        ├── IdentityAuditEntry       ├── MachineIdentity
│  ├── EnterpriseAccount     └── ProfessionalLicense                        │
│  └── Base: IdentityBaseEntity — ULID pk, timestamps, to_dict             │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow: Authentication

```
Client                     API Gateway              NIAM Auth Service
  │                            │                          │
  │  POST /niam/auth/login     │                          │
  │  {login, password}         │                          │
  │ ─────────────────────────► │ ────────────────────────► │
  │                            │                          │
  │                            │    AccountService.authenticate()
  │                            │    ├── find by email/username
  │                            │    ├── check lockout status
  │                            │    ├── verify_password(bcrypt)
  │                            │    ├── increment failed attempts
  │                            │    └── lock if threshold exceeded
  │                            │                          │
  │                            │    _create_session()
  │                            │    ├── generate access JWT (15m)
  │                            │    ├── generate refresh JWT (7d)
  │                            │    ├── create UserSession row
  │                            │    └── return tokens       │
  │                            │                          │
  │  {access_token,            │                          │
  │   refresh_token,           │                          │
  │   session_uuid}            │                          │
  │ ◄───────────────────────── │ ◄──────────────────────── │
```

---

## Separation of Concerns: Person vs Identity vs Account vs Employment vs Assignment

| Concept | Purpose | Example | Can Exist Without |
|---------|---------|---------|-------------------|
| **Person** | The actual human being. Exists once in the system. | Dr. Ali Al-Mansour | Everything |
| **Identity** | A verifiable claim about a person in a specific role/context. A person can have multiple identities. | Dr. Ali as "citizen", Dr. Ali as "government_workforce" at MoH | Person |
| **Account** | Login credentials for authentication. Tied to one identity. | alimansour@example.com with password | Person → Identity |
| **Employment** | An organization employs a person. One person can have multiple employments. | Dr. Ali works at Baghdad Teaching Hospital | Person + Organization |
| **Assignment** | A person is assigned to a specific role/position at an org/facility/dept. | Dr. Ali assigned as "Lab Director" at Baghdad Teaching Hospital, Hematology Dept | Person + Employment + Organization |

### Why This Separation?

In the old bootstrap system (`Lab`/`LabUser`), a user was always "a user of a specific lab". This created problems:

- A doctor who works at two labs had to have two accounts
- A citizen who is not a lab user had no identity representation
- Machine identities (instruments, servers) had no model
- Employment history and role assignments were not tracked
- Professional licensing was disconnected from the user record

NIAM decouples all these concerns so that:

1. **Person** = the immutable natural person record
2. **Identity** = what claims we verify about them (citizenship, employment, etc.)
3. **Account** = how they log in (separate from who they are)
4. **Employment** = their work relationships (multi-org supported)
5. **Assignment** = what roles they hold (temporal, delegated, emergency)

---

## Comparison: Old Bootstrap vs NIAM

| Capability | Old Bootstrap (Lab/LabUser) | NIAM |
|---|---|---|
| Authentication scope | Per-lab | Global (platform-wide) |
| Citizen identity | No model | `Person` + `IdentityRecord` (citizen type) |
| Multi-org user | Impossible (1 user = 1 lab) | `Employment` (N employments per person) |
| Role management | Fixed `role` column | `Assignment` engine (any role, any scope) |
| Professional licenses | Not tracked | `ProfessionalLicense` with board cert, CME |
| Device management | None | `Device` with fingerprint, trust, risk |
| Session management | None | `UserSession` with JTI, refresh, location |
| Audit trail | None | `IdentityAuditEntry` with 35+ action types |
| Policy/ABAC | None | `IdentityPolicy` engine with conditions |
| MFA support | None | `Credential` + `mfa_*` fields on Account |
| Machine identities | None | `MachineIdentity` with cert, heartbeat |
| Enterprise accounts | None | `EnterpriseAccount` with API keys, OAuth2 |
| Organization hierarchy | Single flat `Lab` | `NIAMOrganization` with parent/child tree |
| Password policies | None | Lockout, expiry, min length, history |
| Soft delete | No | `IdentitySoftDeleteEntity` base |
| UUID primary keys | Integer | ULID (26-char, sortable) |

---

## Package Structure

```
backend/app/identity/
├── __init__.py                  # Exports identity_router
├── base.py                     # IdentityBase, IdentityBaseEntity, IdentitySoftDeleteEntity
├── events.py                   # Event bus subscriptions
├── bootstrap/
│   └── seed.py                 # Seed data (ministry orgs, admin accounts)
├── api/
│   ├── __init__.py
│   ├── router.py               # Main /niam router, includes sub-routers
│   ├── persons.py              # /niam/persons/ endpoints
│   ├── accounts.py             # /niam/accounts/ endpoints
│   ├── auth.py                 # /niam/auth/login, /refresh, /logout
│   ├── sessions.py             # /niam/sessions/ endpoints
│   └── devices.py              # /niam/devices/ endpoints
├── models/
│   ├── __init__.py             # Exports all 15 models
│   ├── person.py               # Person (niam_persons)
│   ├── identity.py             # IdentityRecord, IdentityType (niam_identities)
│   ├── account.py              # Account, AccountType, AccountStatus (niam_accounts)
│   ├── niam_organization.py    # NIAMOrganization (niam_organizations)
│   ├── enterprise_account.py   # EnterpriseAccount (niam_enterprise_accounts)
│   ├── employment.py           # Employment, EmploymentStatus (niam_employments)
│   ├── assignment.py           # Assignment, AssignmentStatus (niam_assignments)
│   ├── license.py              # ProfessionalLicense, LicenseStatus (niam_licenses)
│   ├── credential.py           # Credential, CredentialType (niam_credentials)
│   ├── session.py              # UserSession (niam_sessions)
│   ├── device.py               # Device (niam_devices)
│   ├── machine_identity.py     # MachineIdentity (niam_machine_identities)
│   ├── policy.py               # IdentityPolicy (niam_policies)
│   └── audit.py                # IdentityAuditEntry, AuditAction (niam_audit_entries)
├── services/
│   ├── __init__.py             # Exports all 8 services
│   ├── person_service.py       # Person CRUD
│   ├── identity_service.py     # Identity lifecycle
│   ├── account_service.py      # Account management + authentication
│   ├── authentication_service.py # Login, session, token creation
│   ├── session_service.py      # Session lifecycle
│   ├── device_service.py       # Device registration and trust
│   ├── authorization_service.py # Permission checks
│   └── audit_service.py        # Audit event recording
└── repositories/
    ├── __init__.py             # Exports all 8 repos
    ├── base.py                 # IdentityRepositoryBase[T] (generic CRUD)
    ├── person_repository.py    # Person queries (by NID, health ID, phone, email)
    ├── identity_repository.py  # Identity queries (by person, type)
    ├── organization_repository.py # Org queries (by type, governorate, children)
    ├── account_repository.py   # Account queries (by email, username, phone)
    ├── employment_repository.py # Employment queries (by person, org)
    ├── assignment_repository.py # Assignment queries (by person, org, employment)
    ├── session_repository.py   # Session queries + termination
    └── device_repository.py    # Device queries (by fingerprint, person, account)
```

---

## Key Architectural Decisions

1. **Separate declarative base** — `identity.base.IdentityBase` is a completely separate SQLAlchemy `declarative_base()` from the main app's `Base`. NIAM tables live alongside but are not coupled to the lab schema.

2. **ULID primary keys** — 26-character uppercase hex IDs derived from UUID4 (no dashes). Sortable, URL-safe, no auto-increment coordination.

3. **Soft delete everywhere** — `IdentitySoftDeleteEntity` provides `is_deleted`, `deleted_at`, `soft_delete()`, and `restore()`. All queries filter `is_active=True` by default at the repository level.

4. **Async everywhere** — All services and repositories accept `AsyncSession` and use `await` for all database operations.

5. **Independent from lab module** — No imports from `app.models.lab`, `app.models.lab_user`, or any lab-specific code. NIAM is designed to be the identity provider for any current or future GULA sub-system.

6. **Reuses app.security.auth** — Password hashing (bcrypt), JWT creation, and token verification use the existing `app.security.auth` module to maintain consistency across the platform.

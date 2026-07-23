# NIAM — Implementation Guide

## Package Structure

```
backend/app/identity/
├── __init__.py                  # identity_router export
├── base.py                     # IdentityBase (declarative_base), IdentityBaseEntity,
│                               # IdentitySoftDeleteEntity, _ulid()
├── events.py                   # Event bus subscriptions (identity.verified, etc.)
├── bootstrap/
│   └── seed.py                 # Seed data for ministry orgs and admin accounts
├── api/                        # FastAPI route handlers
│   ├── __init__.py
│   ├── router.py               # Main /niam prefix router
│   ├── persons.py              # POST/GET /niam/persons/
│   ├── accounts.py             # POST /niam/accounts/, lock/unlock
│   ├── auth.py                 # POST /niam/auth/login, /refresh, /logout
│   ├── sessions.py             # GET /niam/sessions/, POST terminate
│   └── devices.py              # POST /niam/devices/register, trust, revoke
├── models/                     # SQLAlchemy ORM models (15 files)
│   ├── __init__.py
│   ├── person.py
│   ├── identity.py
│   ├── account.py
│   ├── niam_organization.py
│   ├── enterprise_account.py
│   ├── employment.py
│   ├── assignment.py
│   ├── license.py
│   ├── credential.py
│   ├── session.py
│   ├── device.py
│   ├── machine_identity.py
│   ├── policy.py
│   └── audit.py
├── services/                   # Business logic layer (9 service classes)
│   ├── __init__.py
│   ├── person_service.py
│   ├── identity_service.py
│   ├── account_service.py
│   ├── authentication_service.py
│   ├── session_service.py
│   ├── device_service.py
│   ├── authorization_service.py
│   └── audit_service.py
└── repositories/               # Data access layer (9 repository classes)
    ├── __init__.py
    ├── base.py
    ├── person_repository.py
    ├── identity_repository.py
    ├── organization_repository.py
    ├── account_repository.py
    ├── employment_repository.py
    ├── assignment_repository.py
    ├── session_repository.py
    └── device_repository.py
```

## Dependencies

| Dependency | Usage |
|---|---|
| `uuid` (stdlib) | UUID generation for `uuid` column on all models |
| `datetime` (stdlib) | Timestamps, expiry, lockout calculations |
| `sqlalchemy` | ORM models, async session, query building |
| `fastapi` + `APIRouter` | Route definitions, dependency injection |
| `pydantic.BaseModel` | Request/response schemas for API endpoints |
| `app.database.get_db` | AsyncSession dependency injection |
| `app.security.auth` | `hash_password`, `verify_password`, `create_token`, `create_refresh_token` |
| `app._compat.UTC` | Timezone-aware UTC singleton |
| `app._compat.StrEnum` | Python 3.11+ StrEnum with backward compat |

## Key Classes

### Base Layer (`base.py`)

| Class | Description |
|---|---|
| `IdentityBase` | SQLAlchemy `declarative_base()` — completely separate from main app's Base |
| `IdentityBaseEntity` | Abstract base with `id` (ULID), `created_at`, `updated_at`, `to_dict()`, `__repr__()` |
| `IdentitySoftDeleteEntity` | Extends IdentityBaseEntity with `is_deleted`, `deleted_at`, `soft_delete()`, `restore()` |

### Repository Base (`repositories/base.py`)

| Class | Description |
|---|---|
| `IdentityRepositoryBase[T]` | Generic CRUD with `create`, `get_by_id`, `get_by_uuid`, `soft_delete`, `hard_delete`, `list_all`, `count`. All queries filter `is_active=True` by default. |

## Model Files (15)

| # | File | Class | Table | StrEnums |
|---|---|---|---|---|
| 1 | `person.py` | `Person` | `niam_persons` | — |
| 2 | `identity.py` | `IdentityRecord` | `niam_identities` | `IdentityType` (8 values) |
| 3 | `account.py` | `Account` | `niam_accounts` | `AccountType` (4), `AccountStatus` (5) |
| 4 | `niam_organization.py` | `NIAMOrganization` | `niam_organizations` | — (uses `ORG_TYPES` list of 19 values) |
| 5 | `enterprise_account.py` | `EnterpriseAccount` | `niam_enterprise_accounts` | — |
| 6 | `employment.py` | `Employment` | `niam_employments` | `EmploymentStatus` (6) |
| 7 | `assignment.py` | `Assignment` | `niam_assignments` | `AssignmentStatus` (4) |
| 8 | `license.py` | `ProfessionalLicense` | `niam_licenses` | `LicenseStatus` (5) |
| 9 | `credential.py` | `Credential` | `niam_credentials` | `CredentialType` (12) |
| 10 | `session.py` | `UserSession` | `niam_sessions` | — |
| 11 | `device.py` | `Device` | `niam_devices` | — |
| 12 | `machine_identity.py` | `MachineIdentity` | `niam_machine_identities` | — |
| 13 | `policy.py` | `IdentityPolicy` | `niam_policies` | — |
| 14 | `audit.py` | `IdentityAuditEntry` | `niam_audit_entries` | `AuditAction` (38 values) |
| 15 | — | *(14 models listed; `__init__.py` re-exports all 14)* | | |

## Repository Files (9)

| # | File | Class | Model |
|---|---|---|---|
| 1 | `base.py` | `IdentityRepositoryBase[T]` | Generic |
| 2 | `person_repository.py` | `PersonRepository` | `Person` |
| 3 | `identity_repository.py` | `IdentityRepository` | `IdentityRecord` |
| 4 | `organization_repository.py` | `OrganizationRepository` | `NIAMOrganization` |
| 5 | `account_repository.py` | `AccountRepository` | `Account` |
| 6 | `employment_repository.py` | `EmploymentRepository` | `Employment` |
| 7 | `assignment_repository.py` | `AssignmentRepository` | `Assignment` |
| 8 | `session_repository.py` | `SessionRepository` | `UserSession` |
| 9 | `device_repository.py` | `DeviceRepository` | `Device` |

## Service Files (9)

| # | File | Class | Key Methods |
|---|---|---|---|
| 1 | `person_service.py` | `PersonService` | `create_person`, `get_person`, `get_person_by_uuid`, `find_by_health_id`, `find_by_phone`, `find_by_email`, `deactivate_person`, `update_person` |
| 2 | `identity_service.py` | `IdentityService` | `create_identity`, `get_identity`, `verify_identity`, `revoke_identity` |
| 3 | `account_service.py` | `AccountService` | `create_account`, `authenticate`, `get_account`, `find_by_email`, `change_password`, `lock_account`, `unlock_account` |
| 4 | `authentication_service.py` | `AuthenticationService` | `login`, `_create_session`, `refresh_session`, `logout`, `logout_all_sessions` |
| 5 | `session_service.py` | `SessionService` | `get_session`, `get_active_sessions`, `update_activity`, `terminate`, `terminate_all` |
| 6 | `device_service.py` | `DeviceService` | `register_device`, `trust_device`, `revoke_device` |
| 7 | `authorization_service.py` | `AuthorizationService` | `has_permission`, `get_assignments_for_person`, `get_assignments_for_organization` |
| 8 | `audit_service.py` | `AuditService` | `record`, `record_event` |

## ULID Generation

```python
def _ulid() -> str:
    return str(uuid.uuid4()).replace("-", "").upper()[:26]
```

All primary keys use this 26-character uppercase hex string. It is URL-safe, sortable (by creation time prefix), and requires no sequence coordination.

## Soft Delete Pattern

All models inherit from `IdentityBaseEntity` (or `IdentitySoftDeleteEntity`). The repository base class automatically adds `.where(model.is_active.is_(True))` to all `get_by_id`, `get_by_uuid`, `list_all`, and `count` queries. The `soft_delete` method sets `is_active=False` rather than deleting the row.

## Security Constants

Defined in `account_service.py`:

| Constant | Value | Purpose |
|---|---|---|
| `PASSWORD_MIN_LENGTH` | 12 | Minimum password characters |
| `ACCOUNT_LOCKOUT_THRESHOLD` | 5 | Failed attempts before lockout |
| `ACCOUNT_LOCKOUT_DURATION_MINUTES` | 30 | Lockout duration |
| `PASSWORD_EXPIRY_DAYS` | 90 | Password validity period |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 15 | JWT access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | 7 | Refresh token lifetime |

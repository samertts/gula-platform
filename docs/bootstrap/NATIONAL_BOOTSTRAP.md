# GULA Platform — National Bootstrap Engine

**Version:** 1.0 | **Last Updated:** 2026-07-23

## Overview

The National Bootstrap Engine transforms the platform's initializer from a
single `master_admin` creator into an enterprise-grade bootstrapper that seeds
the entire national health hierarchy: Ministry of Health, governorate health
directorates, facilities, roles, permissions, admin accounts, subscriptions,
and optional demo data.

## Architecture

```
backend/app/core/bootstrap/
├── __init__.py          # Exports, BootstrapContext, bootstrap sequence
├── config.py            # Bootstrap-specific env var loading
├── models.py            # Type definitions (RoleDef, PermissionDef, etc.)
├── master_admin.py      # ensure_master_admin() — backward compatible
├── organizations.py     # Generic organization seeder
├── ministry.py          # Ministry of Health seed
├── directorates.py      # 19 Iraqi governorate health directorates
├── facilities.py        # Platform facilities + generic facility seeder
├── laboratories.py      # Laboratory type definitions
├── departments.py       # 16 standard lab departments
├── roles.py             # 19 enterprise roles with permissions
├── permissions.py       # 80+ permissions across 20 domains
├── users.py             # 6 national admin accounts
├── subscriptions.py     # 4 subscription tiers (starter/national)
├── demo_data.py         # Deterministic demo data generator
├── validation.py        # Bootstrap validation engine
└── bootstrap.py         # Main orchestrator
```

## Design Principles

### Idempotency
Every module checks for existing records before creating new ones. Running the
bootstrap multiple times on the same database is safe — it will never create
duplicates.

### Backward Compatibility
- `ensure_master_admin()` in `backend/app/core/seeds.py` is preserved unchanged
- All existing re-exports from `admin.py` and `tiers.py` remain
- `startup_guard.py` calls both old and new bootstrap steps

### Clean Architecture
Each module is independently executable with its own `db: Session` parameter.
Modules can be called individually or through the orchestrator.

### Security
- Passwords come ONLY from environment variables — never hardcoded
- Support password hash override (pre-hashed passwords via env vars)
- All passwords hashed with bcrypt via `shared/auth/passwords.py`
- National IDs hashed with HMAC-SHA256

## Bootstrap Sequence

| Step | Module | Description | Config Gate |
|------|--------|-------------|-------------|
| 1 | master_admin | Create or verify platform super-admin | `ENABLE_BOOTSTRAP` |
| 2 | permissions | Seed 80+ permissions across 20 domains | `ENABLE_BOOTSTRAP` |
| 3 | roles | Create 19 enterprise roles | `ENABLE_BOOTSTRAP` |
| 4 | ministry | Create Ministry of Health organization | `ENABLE_NATIONAL_BOOTSTRAP` |
| 5 | directorates | Create 19 health directorates | `ENABLE_NATIONAL_BOOTSTRAP` |
| 6 | facilities | Create 9 platform facilities | `ENABLE_NATIONAL_BOOTSTRAP` |
| 7 | laboratories | Create 9 laboratory type definitions | `ENABLE_NATIONAL_BOOTSTRAP` |
| 8 | departments | Create 16 standard lab departments | `ENABLE_BOOTSTRAP` |
| 9 | users | Create 6 national admin accounts | `ENABLE_BOOTSTRAP` |
| 10 | subscriptions | Create starter subscriptions for all labs | `ENABLE_BOOTSTRAP` |
| 11 | demo_data | Generate demo patients/orders/results | `ENABLE_DEMO_DATA` |

## Seeded Entities

### Organizations
- Ministry of Health (national level)
- 19 Governorate Health Directorates (Baghdad, Basra, Nineveh, etc.)

### Platform Facilities (9)
| Facility | Type |
|----------|------|
| GULA Platform Laboratory | laboratory |
| GULA Platform Blood Bank | blood_bank |
| GULA Platform Public Health Lab | public_health_lab |
| GULA Platform Forensic Laboratory | forensic_lab |
| GULA Platform Reference Laboratory | reference_lab |
| GULA Platform Research Laboratory | research_lab |

### Laboratory Types (9)
Public Health Laboratory, Blood Bank, Forensic Medicine Laboratory,
Reference Laboratory, Research Laboratory, Training Center,
Hospital Laboratory, PHC Laboratory, Private Laboratory

### Departments (16)
Clinical Chemistry, Hematology, Microbiology, Parasitology, Serology,
Immunology, Urinalysis, Coagulation, Endocrinology, Molecular Biology,
Genetics, Toxicology, Histopathology, Cytopathology, Phlebotomy,
Quality Assurance

## Seeded Roles (19)

| Role | Level | Scope | Description |
|------|-------|-------|-------------|
| master_admin | 100 | global | Platform super-administrator |
| ministry_admin | 90 | ministry | Ministry-level administrator |
| organization_admin | 80 | organization | Organization-level administrator |
| directorate_admin | 70 | directorate | Health directorate administrator |
| auditor | 70 | global | System auditor (MFA required) |
| security_officer | 70 | global | Security officer (MFA required) |
| hospital_admin | 60 | hospital | Hospital administrator |
| phc_admin | 55 | phc | PHC center administrator |
| lab_manager | 50 | lab | Laboratory manager |
| quality_manager | 45 | lab | Quality control manager |
| lab_supervisor | 45 | lab | Lab supervisor |
| pathologist | 40 | lab | Pathologist (MFA required) |
| doctor | 35 | any | Medical doctor |
| technician | 30 | lab | Lab technician |
| nurse | 25 | facility | Nurse |
| receptionist | 20 | facility | Receptionist |
| cashier | 20 | facility | Cashier |
| api_client | 5 | api | Machine-to-machine client |
| patient | 10 | self | Patient self-service |

## Seeded Permissions (80+)

Permissions across 20 domains:

| Domain | Permissions |
|--------|-------------|
| identity | read, create, update, delete, verify |
| patients | read, create, update, delete, merge, export |
| orders | read, create, update, cancel, delete, batch |
| samples | read, create, update, destroy, transfer |
| results | read, create, update, verify, delete, release |
| billing | read, create, update, void, refund, read_reports |
| inventory | read, create, update, adjust |
| facilities | read, create, update, deactivate |
| users | read, create, update, deactivate, delete, change_role |
| organizations | read, create, update, deactivate |
| analytics | read, create_report, export |
| ai | access, interpret, manage_models, configure |
| audit | read, export, view_sensitive, rotate_keys |
| administration | system_config, manage_tiers, view_health, manage_backup |
| fhir | read, write, search, bulk_export |
| interoperability | read, configure, manage_devices |
| reporting | read, create, schedule, export_pdf |
| notifications | read, send, configure |
| configuration | read, update, manage_features |
| security | read_policy, update_policy, manage_mfa, view_logs, manage_api_keys, break_glass, manage_rate_limits, incident_response |

## Configuration

See [BOOTSTRAP_CONFIGURATION.md](BOOTSTRAP_CONFIGURATION.md) for all environment
variables and [BOOTSTRAP_WORKFLOW.md](BOOTSTRAP_WORKFLOW.md) for execution flow.

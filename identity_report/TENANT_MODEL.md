# GULA Identity Platform — Tenant Model

> Generated: 2026-07-23T11:23:43.297306+00:00
> Program: PROGRAM-IDENTITY-ENTERPRISE-001

## Tenant Hierarchy

GULA supports a multi-level hierarchical tenant model:

```
Ministry (National)
├── Governorate / Province
│   ├── Health Directorate
│   │   ├── Hospital
│   │   │   ├── Department
│   │   │   └── Laboratory
│   │   ├── Primary Health Center (PHC)
│   │   │   └── Department
│   │   └── Research Center
│   └── Private Facility
│       └── Laboratory
└── External Partner
```

## Tenant Model Components

### Tenant Table

| Column | Type | Description |
|--------|------|-------------|
| `tenant_id` | String | Unique identifier |
| `name_en` / `name_ar` | String | Bilingual naming |
| `domain` | String | Optional domain binding |
| `tenant_type` | String | Type (governorate, ministry, hospital, etc.) |
| `parent_tenant_id` | FK → Tenant | Self-referential hierarchy |
| `is_active` | Boolean | Activation flag |
| `max_users` | Integer | Capacity limit |
| `feature_flags` | JSON | Per-tenant feature matrix |
| `settings` | JSON | Per-tenant configuration |

### Organization Table

| Column | Type | Description |
|--------|------|-------------|
| `organization_id` | Integer | Primary key |
| `name` | String | Organization name |
| `parent_org_id` | FK → Organization | Self-referential hierarchy |
| `tenant_id` | FK → Tenant | Tenant membership |
| `org_type` | String | Type (directorate, hospital, phc, etc.) |

### User → Tenant Linkage

The `User` model carries 5 hierarchy fields:

| Field | Level |
|-------|-------|
| `tenant_id` | National → Governorate |
| `governorate_id` | Governorate |
| `directorate_id` | Health Directorate |
| `facility_id` | Facility (Hospital/PHC/Lab) |
| `department_id` | Department |

## Tenant Isolation Enforcement

1. **`require_own_lab()`** — All patient-data queries filter by `lab_id = current_user.lab_id`.
   Platform roles (master_admin, ministry_admin, province_admin) bypass this check.

2. **Lab active check** — `get_current_user()` verifies the lab is active on every request.

3. **`can_manage_user()`** — `province_admin` is scoped to their province.

4. **Subscription tier limits** — Per-lab resource limits (max_patients, max_staff, etc.).

5. **Per-tenant feature flags** — Feature availability controlled per tenant.

## Tenant Types

| Type | Description | Model Support |
|------|-------------|---------------|
| `governorate` | Iraqi governorate (18) | `tenant_type` in Tenant model |
| `ministry` | Ministry of Health | Inferred from role hierarchy |
| `hospital` | Hospital facility | Organization → Facility chain |
| `laboratory` | Medical laboratory | Organization → Facility chain |
| `phc` | Primary Health Center | Organization → Facility chain |
| `research_center` | Research institution | Organization type |
| `private_facility` | Private sector | Organization type |
| `external_partner` | External integration partner | Organization type |

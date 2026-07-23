# GULA Identity Platform — Permission Catalog

> Generated: 2026-07-23T11:23:43.297007+00:00
> Program: PROGRAM-IDENTITY-ENTERPRISE-001

## Extended Permission Model (16 permissions)

| Permission | Domain | Description |
|------------|--------|-------------|
| `patients:read` | Patients | View patient records |
| `patients:write` | Patients | Create/update patient records |
| `patients:delete` | Patients | Delete patient records |
| `orders:read` | Orders | View lab orders |
| `orders:write` | Orders | Create/update lab orders |
| `results:read` | Results | View lab results |
| `results:write` | Results | Enter/update lab results |
| `staff:manage` | Staff | Manage lab staff (assign roles, deactivate) |
| `lab:read` | Lab | View lab configuration |
| `lab:manage` | Lab | Manage lab configuration |
| `dashboard:read` | Dashboard | View dashboard/analytics |
| `audit:read` | Audit | View audit logs |
| `platform:manage_labs` | Platform | Manage labs across platform |
| `platform:manage_users` | Platform | Manage users across platform |
| `platform:view_stats` | Platform | View platform statistics |
| `system:admin` | System | System-level administration |

## Permission by Role

| Role | Permissions |
|------|------------|
| `master_admin` | All 0 permissions |
| `ministry_admin` | patients:read, orders:read, results:read, lab:read, dashboard:read, audit:read, platform:manage_labs, platform:manage_users, platform:view_stats |
| `province_admin` | patients:read, orders:read, results:read, lab:read, dashboard:read, audit:read, platform:manage_labs, platform:manage_users, platform:view_stats |
| `admin` / `lab_admin` | patients:read/write/delete, orders:read/write, results:read/write, staff:manage, lab:read/manage, dashboard:read, audit:read, platform:manage_users |
| `doctor` | patients:read, orders:read, results:read, dashboard:read |
| `staff` / `lab_staff` | patients:read/write, orders:read/write, results:read/write, lab:read, dashboard:read |
| `technician` | orders:read/write, results:read/write, lab:read, dashboard:read |
| `citizen` | (none — citizen data access is gated by consent, not role-based permissions) |

## Database-Backed Permission Model

The `permissions` table stores granular permission definitions with:

| Field | Description |
|-------|-------------|
| `permission_id` | Unique permission identifier |
| `name_en` / `name_ar` | Bilingual name |
| `domain` | Functional domain (patients, orders, results, etc.) |
| `resource` | Target resource type |
| `action` | CRUD action |
| `risk_level` | low / medium / high / critical |
| `is_sensitive` | Flag for sensitive permissions |
| `requires_mfa` | MFA required for this permission |
| `requires_justification` | Justification required |
| `is_audited` | Whether access is audited |

## Legacy Enum Permissions (13)

| Enum | Permission |
|------|-----------|
| `READ_PATIENTS` | `read:patients` |
| `WRITE_PATIENTS` | `write:patients` |
| `READ_ORDERS` | `read:orders` |
| `WRITE_ORDERS` | `write:orders` |
| `READ_RESULTS` | `read:results` |
| `WRITE_RESULTS` | `write:results` |
| `READ_SAMPLES` | `read:samples` |
| `WRITE_SAMPLES` | `write:samples` |
| `MANAGE_USERS` | `manage:users` |
| `MANAGE_LABS` | `manage:labs` |
| `VIEW_AUDIT` | `view:audit` |
| `MANAGE_SYSTEM` | `manage:system` |
| `VIEW_ANALYTICS` | `view:analytics` |

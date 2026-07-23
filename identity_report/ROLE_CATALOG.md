# GULA Identity Platform — Role Catalog

> Generated: 2026-07-23T11:23:43.295922+00:00
> Program: PROGRAM-IDENTITY-ENTERPRISE-001

## Role Hierarchy

GULA uses a hierarchical role model with numeric levels. Higher-level
roles can manage lower-level roles. Platform-level roles (master_admin,
ministry_admin, province_admin) have cross-lab access.

| Role | Level | Scope | Description |
|------|-------|-------|-------------|
| `master_admin` | 100 | National | Full system access, all tenants, all labs |
| `ministry_admin` | 90 | Ministry | Ministry-wide administration, stats, audit |
| `province_admin` | 80 | Province | Province/governorate scoped administration |
| `admin` / `lab_admin` | 50 | Lab | Lab administration (staff, patients, orders, results) |
| `doctor` | 40 | Lab | Read patient/order/result data, create orders |
| `staff` / `lab_staff` | 20 | Lab | Lab operations (patients, orders, results) |
| `technician` | 20 | Lab | Instrument results entry and management |
| `citizen` | 10 | Self | View own results only |

## Enum-Based Role Catalog (Legacy API)

| Enum | String Value |
|------|-------------|
| `SUPER_ADMIN` | `super_admin` |
| `LAB_ADMIN` | `lab_admin` |
| `LAB_TECH` | `lab_tech` |
| `DOCTOR` | `doctor` |
| `PATHOLOGIST` | `pathologist` |
| `NURSE` | `nurse` |
| `RECEPTIONIST` | `receptionist` |
| `CITIZEN` | `citizen` |
| `MINISTRY` | `ministry` |
| `RESEARCHER` | `researcher` |

## Role Management Rules

- Roles are managed hierarchically: a role can only manage lower-level roles.
- `master_admin` can only be managed by another `master_admin`.
- `province_admin` is scoped to their province — cannot manage users in other provinces.
- Platform roles (`master_admin`, `ministry_admin`, `province_admin`) bypass lab-scoped access control.
- Lab roles (`admin` through `citizen`) are strictly scoped to their lab.
- All roles are defined in `backend/app/models/authorization.py` with DB-backed `Role` model.
- Role groups enable template-based role assignment (e.g., "Lab Technician" group).

## Role Assignment Model

| Field | Description |
|-------|-------------|
| `user_id` | FK to User |
| `role_id` | FK to Role |
| `organization_id` | Scoped to organization |
| `facility_id` | Scoped to facility |
| `department_id` | Scoped to department |
| `assigned_by` | Who assigned |
| `expires_at` | Optional time-bound assignment |
| `is_primary` | Primary role flag |
| `is_delegated` | Flag for delegated roles |
| `status` | active / inactive |

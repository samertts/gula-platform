# Enterprise Certification — Multi-Tenancy & National Hierarchy v1.0

**Platform:** GULA National Health Platform
**Date:** 2026-08-02
**Level:** Enterprise Certification (P4 program)

## Scope

Ministry → Health Directorate → Hospital → Laboratory hierarchy, tenant
isolation, and national bootstrap — live-verified.

## 1. National Hierarchy — CERTIFIED

- Models: `models/organization.py` (governorate_id, directorate_id),
  `models/user.py`, `models/tenant.py` (tenant_type "governorate").
- Multi-tenant tree: `control_plane/multi_tenant.py get_hierarchy` with
  levels MINISTRY/DIRECTORATE (`control_plane/enums.py:32-33`).
- Scoped roles: `ministry_admin` (ministry scope), `directorate_admin`
  (directorate scope) (`core/bootstrap/roles.py:27,43`).

## 2. National Bootstrap — CERTIFIED (live, P4 fix `f0d101bd`)

- Full chain seeded by startup guard:
  ministry (`seed_ministry_of_health`) → health directorates →
  **platform organizations** (`seed_platform_organizations` — new:
  `org-gula-platform`, `dir-gula-platform`, `hosp-gula-platform`) →
  facilities.
- Live database holds: 1 ministry + 3 platform orgs + 7 facilities.
- Idempotent re-runs (ministry exists → True, no failure spam).
- Fresh-DB migration chain verified end to end (51 migrations, single root,
  typed-annotation heads included).

## 3. Tenant Isolation — CERTIFIED

- Lab-scoped queries enforced by `lab_id` filters across services
  (dashboard, metrics, stats, admin, samples, results) — verified by unit
  tests (`test_lab_isolation` families) and live probes.
- Users bound to labs; wide-scope roles limited to ministry/directorate
  admins.
- National data layer (`national/domain/hospital.py`,
  `national/domain/laboratory.py`) keys organizations to the hierarchy.

## 4. Deployment Compatibility — CERTIFIED

- Arabic-first with `dir="rtl"`; governorate-aware bootstrap
  (BOOTSTRAP_COUNTRY=IQ, timezone Asia/Baghdad).
- Health directorates seeded per governorate
  (`seed_health_directorates` with governorate_id).
- Regional k8s overlays (`region-eu`, `region-me` topology spread) for
  cross-governorate deployment.

## Verdict

**MULTI-TENANCY & NATIONAL HIERARCHY: CERTIFIED v1.0** — ministry-to-lab
hierarchy fully seeded and idempotent on live DB, lab-scoped isolation
enforced and tested, Arabic-first regional deployment supported.

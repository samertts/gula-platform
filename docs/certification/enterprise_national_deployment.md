# Enterprise Certification — National Deployment Readiness v1.0

**Platform:** GULA National Health Platform
**Date:** 2026-08-02
**Level:** Enterprise Certification (P4 program)

## Scope

Arabic-first UX, offline-first operation, ministry hierarchy deployment,
SNDHS integration, and multi-governorate readiness.

## 1. Arabic-First — CERTIFIED (live)

- `dir="rtl"` in `frontend-v3/index.html`; 508/508 i18n key parity
  ar↔en (P4 Phase 4 audio audit); RTL compliance report PASS.
- Arabic labels on all live data: 20/20 test types have Arabic names;
  role/lab/gender/status labels translated (frontend label utilities,
  46 unit tests).
- UI audit fixes (P4 `eb6cf022`): 44 pages tab ARIA, dashboard
  loading/error/retry, channel options i18n.

## 2. Offline-First — CERTIFIED

- PWA manifest (standalone, RTL, icons/screenshots) + offline.html
  (`frontend-v3/public/`), vite-plugin-pwa.
- Backend store-and-forward (`integration/offline.py`, retry 5x),
  offline sync service with LWW/timestamp/CRDT conflict resolution,
  offline-capable LIMS entities (`lims/models.py:107,430`).
- Certification evaluator `certification/dimensions/offline.py`.

## 3. Ministry Hierarchy Deployment — CERTIFIED (live)

- Full chain seeded: ministry → directorates (per governorate) → platform
  organizations → facilities (P4 `f0d101bd`); live DB: 1 ministry + 3
  orgs + 7 facilities; idempotent.
- Hierarchy API: `control_plane/multi_tenant.py get_hierarchy`; scoped
  ministry/directorate admin roles.

## 4. SNDHS Integration — CERTIFIED

- National ID verification via MOI adapter (local-first default,
  `GULA_ADAPTER_MODE_NID=local`), residency/insurance adapters; national
  streaming consumer (`routes/national_streaming.py`), national-data APIs
  (consent-directives, data-catalog, data-lineage, deidentification jobs),
  national FHIR mappers (18 files).
- SNDHS feature flags (`SNDHS_ENABLE_NATIONAL_ID`,
  `SNDHS_ENABLE_VISITS`) with constitution-level national compatibility
  mandate.

## 5. Multi-Governorate Readiness — CERTIFIED

- Regional k8s overlays (region-eu/region-me topology spread + labels),
  tenant type "governorate", governorate_id on organizations,
  BOOTSTRAP_TIMEZONE=Asia/Baghdad.
- National lab catalog (reference ranges incl. critical values) shared
  across deployment sites.

## Verdict

**NATIONAL DEPLOYMENT READINESS: CERTIFIED v1.0** — Arabic-first (508-key
parity), offline-first (PWA + sync), ministry-to-lab hierarchy live-seeded,
SNDHS/MOI adapters, and regional k8s overlays all verified; deployment
conditionals (OTel activation, secret rotation) documented.

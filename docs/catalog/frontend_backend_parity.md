# Frontend ↔ Backend Parity

> PROGRAM-02, against PROGRAM-01 backend catalog (1986 routes).

## 1. FE→BE call resolution

- Frontend makes **567** API calls across 57 groups.
- **549** of 567 resolve to registered backend routes (96.8%).
- **18** target `/financial/*` — backend module dormant, NOT registered in factory.py (all fail at runtime).

## 2. BE→FE coverage

- Backend: **553** routes consumed by frontend (27.8% of 1986).
- **1431** routes have no frontend consumer (dormant bounded contexts: niam 198, national 191, governance 78, lims 67, nursing 65, nhdw 61, radiology 57, pharmacy 55, document-intelligence 50, research 49, ai 42, care-continuum 32, intelligence 30, integration 28, authz 27, ems 26, roadmap 22, biomedical 21, control-plane 21, critical-care 20, blood-bank 19, lifecycle 19, public-health 19, api 17, citizen-platform 17, …).

## 3. Workflow parity

| Backend workflow | FE pages | UI status |
|---|---|---|
| Order creation + results | orders, results (read-only lists) | INTERRUPTED — no create/validate/cancel forms |
| Sample workflow | samples (read-only list) | INTERRUPTED — no registration/transitions |
| Analyzer device ingestion | — | MISSING |
| Result verification / locking | results | INTERRUPTED — no verify actions |
| Public result delivery | — | MISSING |
| QC Westgard | qc (list only) | INTERRUPTED — no data entry |
| Referral workflow | — | MISSING |
| EHR care continuum | ehr (misnamed lab timeline) | MISSING |
| Care continuum community | — | MISSING |
| Identity & registration | login, admin pending-labs | INTERRUPTED — no registration forms |
| Login / MFA | login, security | INTERRUPTED — no login MFA challenge |
| Consent workflow | — | MISSING |
| Claims / insurance | — | MISSING |
| FHIR export / import | fhir (read-only) | INTERRUPTED — no write UI |
| Streaming ingestion | — | MISSING |
| MPI | — | MISSING |
| Identity governance | niam/* (different module) | MISSING |
| Hospital hierarchy | hospital (partial CRUD) | INTERRUPTED — no bed/OT/equipment UI |
| Offline sync / edge | edge (fleet mgmt) | INTERRUPTED — no sync UI |
| Clinical intelligence | ai, ai-platform (read-only) | INTERRUPTED — no release gating UI |
| National notifications | national page (read-only) | INTERRUPTED — no send/template UI |
| Workflow runtime | workflow-runtime (GET-only) | INTERRUPTED — no execution controls |
| Capabilities workflow_engine (stub) | workflow-engine (GET-only) | INTERRUPTED |

**Workflow parity: 0/22 complete in UI, 12/22 interrupted, 10/22 missing.**

## 4. Role coverage

| Role | Landing | Accessible pages | Issues |
|---|---|---|---|
| master_admin | /dashboard | all | none |
| ministry_admin | /dashboard | dashboard, patients, orders, results, admin/*, national/*, hospital, labs, compliance, stats, settings | menu-route drift: qc/alerts/ai/tiers/patient-card/identity/capabilities menus visible but denied |
| province_admin | /dashboard | same as ministry_admin | same drift |
| admin | /dashboard | all adminRoles + national/* + capabilities + samples | national-data menu visible but route denied; dead add-buttons |
| lab_admin | /dashboard | same as admin | same |
| doctor | /dashboard | patients, orders, results, alerts, qc, stats, ai, tiers, patient-card, identity, capabilities, labs, notifications | samples menu visible but route denied; national menus denied |
| staff | /dashboard | staffRoles + labRoles routes | national-data/hospital/security menus denied |
| lab_staff | /dashboard | same as staff minus patients | national/hospital menus denied |
| technician | /dashboard | only 6 pages (dashboard, orders, results, notifications, settings, profile) | ~30 menu items dead — worst experience |
| citizen | /dashboard (lab KPIs!) | dashboard, notifications, settings, profile | wrong landing content; no citizen portal |
| receptionist | — | — | dead role in routes/menus |

# Backend API Inventory — Phase-02B

Date: 2026-07-24

## Overview
FastAPI 0.139.2 backend with SQLAlchemy ORM. The backend defines ~56 route files, 30+ SQLAlchemy models,
and Pydantic DTOs for every endpoint. Auth uses JWT with access + refresh token rotation and Redis blacklisting.

## Route Summary

| Module | Prefix | Endpoints |
|---|---|---|
| `routes/login.py` | `/login`, `/logout` | 2 |
| `routes/mobile.py` | `/auth/refresh`, `/auth/change-password` | 2 |
| `routes/password_reset.py` | `/auth/forgot-password`, `/auth/reset-password`, `/auth/change-password` | 3 |
| `routes/dashboard.py` | `/greeting`, `/dashboard` | 2 |
| `routes/patients.py` | `/patients` | CRUD + family/children |
| `routes/orders.py` | `/orders`, `/test-profiles` | CRUD + validate/cancel/intelligence |
| `routes/results.py` | `/test-results` | CRUD + verify/validate + citizen endpoints |
| `routes/samples.py` | `/samples` | CRUD |
| `routes/labs.py` | `/labs/me` | get/update + employees CRUD |
| `routes/admin.py` | `/admin/*` | stats, labs, users, doctors, citizens, audit-logs, kill-switch |
| `routes/qr.py` | `/qr/*`, `/qr-medical/*` | get |
| `routes/patient_history.py` | `/patient-history`, `/history` | get |
| `routes/clinical.py` | `/analyze` | 1 |
| `routes/notifications.py` | `/notify/send`, `/notify/history` | 2 |
| `routes/alerts.py` | `/alerts` | list + stats |
| `routes/qc.py` | `/qc` | CRUD + summary + batch |
| `routes/national_identity.py` | `/national-id/verify` | 1 |
| `routes/id_scan.py` | `/id-scan/scan` | 1 |
| `routes/identity.py` | `/identity/link`, `/identity/lookup` | 2 |
| `routes/patient_card.py` | `/patient-card` | get + qr + scan + history + print |
| `routes/device.py` | `/device/results` | 1 |
| `routes/batch.py` | `/batch/orders` | 1 |
| `routes/tiers.py` | `/tiers` | list + my + upgrade + admin |
| `routes/public.py` | `/r/{token}` | get + pdf |
| `routes/ai_v1.py` | `/api/ai/*` | suggest, pending, approve, reject, execute, analyze, interpret, chat, etc. |
| `routes/ai_v2.py` | `/api/ai/v2/*` | search, index, RAG, knowledge-graph, agents, orchestrate, sessions, CDS, governance, security, metrics |
| `routes/ai_telemetry.py` | `/api/ai/interactions`, etc. | log + feedback + stats |
| `routes/health.py` | `/health`, `/health/ready`, `/health/deep`, `/health/status` | 4 |
| `routes/metrics.py` | `/metrics`, `/metrics/prom` | 2 |
| `routes/stats.py` | `/stats/*` | trends + summary + turnaround |
| `routes/setup.py` | `/setup/status` | 1 |
| `routes/compliance.py` | `/compliance/*`, `/compliance/fhir/*` | FHIR + DHIS2 + audit + security |
| `routes/mfa.py` | `/mfa/*` | TOTP + WebAuthn + devices |
| `routes/service_accounts.py` | `/service-accounts` | CRUD + revoke + rotate |
| `routes/canonical_patient.py` | `/api/v1/canonical-patients` | CRUD + merge + link |
| `routes/ehr.py` | `/ehr/*` | clinical-notes, allergies, medications, care-plans, conditions, etc. |
| `routes/ehr_fhir.py` | `/fhir/*` | FHIR R4 read/search on all resources |
| `routes/care_continuum.py` | `/care-continuum/*` | encounters, referrals, care-journeys, vaccinations, etc. |
| `routes/clinical_full.py` | `/clinical/*` | terminology, knowledge, guidelines, pathways, formularies, etc. |
| `identity/api/auth.py` | `/auth/login`, `/auth/refresh`, `/auth/logout` | NIAM auth |

## Key Auth Schemas

### Login (routes/login.py, line 162)
```python
{
    "token": str,
    "refresh_token": str,
    "token_type": "Bearer",
    "user": {"id", "name", "email", "role", "lab_id", "lab_name"}
}
```

### Refresh (routes/mobile.py, line 158)
```python
{
    "token": str,
    "refresh_token": str,
}
```
Body: `{"refresh_token": str}` — also accepts httpOnly cookie.

### NIAM Login (identity/api/auth.py)
```python
class LoginResponse:
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    session_uuid: str
    account_uuid: str
```

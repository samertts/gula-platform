# API Contract Certification Report

**Date:** 2026-07-22
**Module:** GULA Platform Backend (FastAPI)

## Overview

| Metric | Value |
|--------|-------|
| Route files | 54 |
| Total decorated endpoints | 583 |
| API client modules | 57 |
| Typed API calls | 585/585 (100%) |
| OpenAPI spec | Available (requires Docker) |

## Endpoint Distribution (Top 10)

| Module | Endpoints |
|--------|-----------|
| EHR | 85 |
| Care Continuum | 74 |
| Clinical | 65 |
| Hospital | 39 |
| National Data | 34 |
| AI Platform | 23 |
| Admin | 22 |
| AI v1 | 17 |
| FHIR / Compliance | 13 |
| Edge | 20 |

## HTTP Method Distribution

| Method | Count |
|--------|-------|
| GET | ~280 |
| POST | ~200 |
| PUT | ~70 |
| PATCH | ~15 |
| DELETE | ~18 |

## Authentication

- All endpoints require JWT via `Bearer` header
- Login/Register endpoints use rate limiting (10 req/min)
- Refresh tokens use Redis blacklist for revocation
- OAuth2 provider available for third-party integration

## Authorization

- RBAC with 9 roles (master_admin → citizen)
- ABAC for lab-level tenant isolation
- Feature flags gate enterprise features
- Subscription limits enforce tier boundaries

## Pagination

- Standard params: `skip` (int), `limit` (int, default 20-100)
- Response wrapper: `{ total: number; items/results: T[] }`

## Error Schema

```json
{
  "detail": "Human-readable error message",
  "detail_ar": "رسالة الخطأ بالعربية"
}
```

HTTP status codes: 200, 201, 400, 401, 403, 404, 409, 413, 422, 429, 500, 503

## Security Headers

All responses include: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy, Permissions-Policy, Cross-Origin-Opener-Policy, Content-Security-Policy, Strict-Transport-Security (production), Cache-Control

## Status: PASS ✅

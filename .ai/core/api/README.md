# API Engineering Memory

**Mission:** GAIOS-MASTER-001
**Created:** 2026-08-04
**Status:** Active

---

## Purpose

Bridge to API design knowledge. The GULA Platform exposes REST
and FHIR APIs.

---

## API Types

| Type | Framework | Purpose |
|---|---|---|
| REST API | FastAPI | Primary API |
| FHIR API | FastAPI + FHIR | Healthcare interoperability |

---

## Design Patterns

- **Versioning:** URL path versioning
- **Pagination:** Cursor-based
- **Authentication:** JWT + Refresh tokens
- **Authorization:** RBAC + ABAC
- **Validation:** Pydantic models
- **Documentation:** OpenAPI (auto-generated)

---

## Key Endpoints

| Module | Route Prefix | Purpose |
|---|---|---|
| Lab | `/api/v1/labs/` | Lab management |
| Sample | `/api/v1/samples/` | Sample management |
| Test Results | `/api/v1/test-results/` | Result management |
| Quality Control | `/api/v1/quality-control/` | QC management |
| Dashboard | `/api/v1/dashboard/` | Dashboard data |
| Stats | `/api/v1/stats/` | Statistics |
| Admin | `/api/v1/admin/` | Administration |
| Mobile | `/api/v1/mobile/` | Mobile API |
| Metrics | `/metrics` | Prometheus metrics |

---

## FHIR Endpoints

| Resource | Endpoint |
|---|---|
| Patient | `/fhir/Patient/` |
| Observation | `/fhir/Observation/` |
| DiagnosticReport | `/fhir/DiagnosticReport/` |

---

## Related Knowledge

- `.ai/core/backend/` — Backend architecture
- `.ai/core/capabilities/` — API capabilities
- `docs/adr/` — API decisions

---

## References

- `backend/app/routes/` — Route implementations
- `docs/architecture/` — Architecture documentation
- ADR-011 (FHIR Strategy)

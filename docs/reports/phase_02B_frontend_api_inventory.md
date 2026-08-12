# Frontend API Layer Inventory — Phase-02B

Date: 2026-07-24

## Structure

```
frontend-v3/src/
  api/
    client.ts          — Axios singleton with refresh interceptor (1 instance)
    endpoints.ts       — ~700 lines, ~40 endpoint groups, ~200 API calls
    generated/         — Auto-generated client (not actively used)
  types/
    api.ts             — Auth types (LoginRequest, LoginResponse, JwtPayload, ApiResponse, PaginatedResponse)
    backend.ts         — Comprehensive types derived from backend models (570 lines, ~50 interfaces)
    models.ts          — Frontend domain model types (358 lines, ~35 interfaces)
    index.ts           — Barrel: re-exports api.ts + models.ts
  hooks/
    useApi.ts          — React Query wrappers around endpoints.ts
```

## Endpoint Groups (endpoints.ts)

| Group | Methods | Typed Returns | Record<unk> Returns |
|---|---|---|---|
| authApi | 7 | LoginResponse | 6 |
| setupApi | 1 | typed | 0 |
| dashboardApi | 2 | typed | 0 |
| patientsApi | 6 | Patient | 4 |
| ordersApi | 7 | LabOrder | 5 |
| resultsApi | 8 | LabResult | 4 |
| samplesApi | 4 | Sample | 2 |
| labsApi | 5 | Lab, LabEmployee | 3 |
| adminApi | 20 | Lab, User, AuditLog | 14 |
| criticalAlertsApi | 2 | CriticalAlert | 1 |
| qcApi | 4 | QualityControl | 3 |
| tiersApi | 8 | SubscriptionTier, SubscriptionInfo | 5 |
| aiApi | 14 | AIInterpretation, AIChatResponse, AIProviderStatus | 11 |
| aiPlatformApi | 24 | none | 24 |
| ehrApi | 42 | none | 42 |
| ehrFhirApi | 20 | none | 20 |
| careContinuumApi | 38 | none | 38 |
| clinicalFullApi | 38 | none | 38 |
| remaining | ~30 | few | most |

Approximately 75% of endpoints return `Record<string, unknown>` instead of typed DTOs.

## Types (types/)

### api.ts (48 lines)
- ApiResponse, PaginatedResponse, LoginRequest, LoginResponse, UserInfo, JwtPayload
- LoginResponse matches routes/login.py response shape

### models.ts (358 lines)
- User, Lab, Patient, LabOrder, LabResult, Sample, TestType, TestProfile
- AuditLog, NotificationRecord, CriticalAlert, QualityControl
- DashboardData, AbnormalResult, RecentOrder
- SubscriptionTier, SubscriptionInfo
- TrendData, TrendPoint, FlagDistribution, StatsSummary
- HealthStatus, DeepHealth
- AIInterpretation, AIChatResponse, AIProviderStatus
- TurnaroundTime, PatientCard, LabEmployee, FhirPatient

### backend.ts (570 lines)
- UserRole, Permission, ROLE_LEVELS (comprehensive union types)
- Core domain types (Patient, LabOrder, LabResult, Sample, Lab) — different optionality vs models.ts
- EHR types (EHRNote, EHRCondition, EHRMedication, etc.)
- Request DTOs (CreatePatientRequest, CreateOrderRequest, etc.)
- EdgeDevice, EdgeTask, Claim, Organization, Facility, LabSubscription, etc.
- PaginatedResponse (different shape than api.ts)

## Type Duplication

Types duplicated between api.ts and backend.ts:
- JwtPayload, LoginRequest, LoginResponse, PaginatedResponse

Types duplicated between models.ts and backend.ts:
- Lab, Patient, LabOrder, LabResult, Sample, TestType, AuditLog, CriticalAlert, QualityControl, PatientCard, StatsSummary, TurnaroundTime

All duplicates have slightly different field sets and optionality.

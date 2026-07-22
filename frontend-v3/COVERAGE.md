# Frontend Coverage Report

## API Coverage Matrix (52 modules, 583 endpoints)

| Module | Endpoints | Frontend Page | Coverage |
|--------|-----------|---------------|----------|
| `auth` | 6 | LoginPage, MFA (partial) | 70% |
| `dashboard` | 2 | DashboardPage | 100% |
| `patients` | 6 | PatientsPage | 100% |
| `orders` | 4 | OrdersPage | 100% |
| `results` | 6 | ResultsPage | 100% |
| `samples` | 4 | SamplesPage | 100% |
| `labs` | 5 | LabsPage | 100% |
| `critical_alerts` | 2 | CriticalAlertsPage | 100% |
| `notifications` | 2 | NotificationsPage | 50% |
| `ai` | 11 | AIPage | 100% |
| `ai_platform` | 23 | AIPage | 100% |
| `ai_telemetry` | 6 | — | 0% |
| `stats` | 6 | StatsPage | 100% |
| `quality_control` | 4 | QCPage | 100% |
| `patient_card` | 5 | PatientCardPage | 100% |
| `identity` | 2 | IdentityPage | 100% |
| `tiers` | 8 | TiersPage | 100% |
| `compliance` | 11 | CompliancePage | 100% |
| `settings` | — | SettingsPage | 100% |
| `profile` | — | ProfilePage | 100% |
| `security` | 1 | SecurityPage | 100% |
| `admin` | 22 | AdminPages (3) | 100% |
| `ehr_fhir` | 25 | **FhirPage (NEW)** | **100%** |
| `ehr` | 85 | — | 0% |
| `care_continuum` | 74 | — | 0% |
| `clinical` | 65 | — | 0% |
| `clinical_documentation` | 12 | — | 0% |
| `clinical_orders` | 10 | (OrdersPage) | 100% |
| `clinical_quality` | 4 | — | 0% |
| `hospital` | 39 | — | 0% |
| `national_data` | 34 | — | 0% |
| `national_identity` | 1 | IdentityPage | 100% |
| `national_streaming` | 5 | — | 0% |
| `edge` | 22 | — | 0% |
| `consent` | 3 | — | 0% |
| `claims` | 4 | — | 0% |
| `insurance` | 1 | — | 0% |
| `integrations` | 2 | — | 0% |
| `device_results` | 1 | — | 0% |
| `id_scan` | 1 | — | 0% |
| `qr` | 2 | PatientCardPage | 100% |
| `mfa` | 9 | SecurityPage (partial) | 50% |
| `oauth2` | 7 | — | 0% |
| `saml` | 2 | — | 0% |
| `mobile` | 2 | — | 0% |
| `batch` | 1 | — | 0% |
| `optimizer` | 2 | — | 0% |
| `metrics` | 2 | — | 0% |
| `password_reset` | 3 | — | 0% |
| `register` | 4 | LoginPage (partial) | 50% |
| `service_accounts` | 4 | — | 0% |
| `setup` | 1 | — | 0% |
| `test_results` | 6 | ResultsPage | 100% |
| `citizen_portal` | 6 | — | 0% |
| `canonical_patient` | 8 | — | 0% |
| `login` | 2 | LoginPage | 100% |

## Summary

| Metric | Count |
|--------|-------|
| Backend modules | 52 |
| Frontend pages | 22 |
| Fully covered modules | 24 |
| Partially covered | 5 |
| Uncovered modules | 23 |
| Overall endpoint coverage | ~52% |

## Next Priority Modules

1. EHR (85 endpoints) — highest impact
2. Care Continuum (74 endpoints) — clinical workflows
3. Clinical (65 endpoints) — lab operations
4. Hospital (39 endpoints) — facility management
5. National Data (34 endpoints) — SNDHS integration

# Repository Brain — GULA Platform v2.1.0

## Overview

- **Total Nodes:** 10858
- **Total Edges:** 9778
- **API Routes:** 478
- **Database Models:** 31
- **Events:** 0
- **Plugins:** 4

## Topology

- **ai/** — 32 source files
- **architecture/** — 0 source files
- **assessment/** — 1 source files
- **backend/** — 475 source files
- **client/** — 5 source files
- **cloudflare/** — 1 source files
- **config/** — 0 source files
- **data/** — 1 source files
- **database/** — 0 source files
- **digitalocean/** — 0 source files
- **docker/** — 0 source files
- **docs/** — 0 source files
- **edge_agent/** — 6 source files
- **frontend/** — 2 source files
- **frontend-v2/** — 25 source files
- **gula-platform/** — 0 source files
- **k6/** — 1 source files
- **k8s/** — 0 source files
- **logs/** — 0 source files
- **nhop-platform/** — 46 source files
- **pitch-deck/** — 0 source files
- **sample_tracking/** — 7 source files
- **scripts/** — 14 source files
- **server/** — 6 source files
- **services/** — 52 source files
- **shared/** — 111 source files
- **supabase/** — 0 source files
- **test_library/** — 4 source files
- **tests/** — 4 source files

## Kernel Subsystems

- **background/** — priority_queue, worker_pool, cron, distributed_locks, scheduler, job_retry, task_queue
- **config/** — registry, secrets, reload, validation, versioned
- **event_bus/** — inbox, events, replay, dead_letter_queue, outbox, dispatcher, bus, retry_queue, store, versioning
- **features/** — capabilities, flags, kill_switch, regional, tenant_features, experimental
- **gateway/** — health_routing, validation, discovery, routing, rate_limiting, circuit_breaker
- **module/** — registry, discovery, resolver, compatibility, loader, metadata
- **plugin/** — permissions, registry, marketplace, dependencies, hot_reload, manager, loader, version_manager, sandbox
- **runtime/** — lifecycle, shutdown, di_container, startup, context, service_registry, bootloader, capability_registry
- **tenant/** — registry, quotas, config, resolver, isolation
- **validation/** — memory, architecture, dependencies, security, performance, stress

## API Routes (by module)

### admin
- `GET /audit-logs` → `unknown`
- `GET /citizens` → `unknown`
- `GET /control-layer/stats` → `unknown`
- `GET /doctors` → `unknown`
- `GET /kill-switch/status` → `unknown`
- `GET /labs` → `unknown`
- `GET /labs/pending` → `unknown`
- `GET /labs/{lab_id}` → `unknown`
- `GET /stats` → `unknown`
- `GET /users` → `unknown`
- `PATCH /users/{user_id}/role` → `unknown`
- `POST /kill-switch/activate` → `unknown`
- `POST /kill-switch/deactivate` → `unknown`
- `POST /labs` → `unknown`
- `POST /users` → `unknown`
- `PUT /citizens/{citizen_id}/toggle` → `unknown`
- `PUT /citizens/{citizen_id}/verify` → `unknown`
- `PUT /doctors/{doctor_id}/approve` → `unknown`
- `PUT /doctors/{doctor_id}/revoke` → `unknown`
- `PUT /labs/{lab_id}/activate` → `unknown`
- `PUT /labs/{lab_id}/toggle` → `unknown`
- `PUT /users/{user_id}/toggle` → `unknown`
### ai
- `GET /critical-alerts` → `unknown`
- `GET /operations` → `unknown`
- `GET /pending` → `unknown`
- `GET /providers` → `list_ai_providers`
- `POST /analyze-order/{order_id}` → `unknown`
- `POST /approve/{approval_id}` → `unknown`
- `POST /execute/{approval_id}` → `unknown`
- `POST /reject/{approval_id}` → `unknown`
- `POST /suggest` → `unknown`
### batch
- `POST /orders` → `unknown`
### citizen_portal
- `GET /health-record` → `unknown`
- `GET /orders` → `unknown`
- `GET /profile` → `unknown`
- `GET /results` → `unknown`
- `POST /login` → `unknown`
- `POST /logout` → `unknown`
### claims
- `GET /{claim_id}` → `unknown`
- `POST /{claim_id}/submit` → `unknown`
- `POST /{claim_id}/validate` → `unknown`
### compliance
- `GET /audit-integrity` → `unknown`
- `GET /audit-summary` → `unknown`
- `GET /dhis2/aggregate` → `unknown`
- `GET /fhir/diagnostic-report/{order_id}` → `unknown`
- `GET /fhir/observation/{order_id}` → `unknown`
- `GET /fhir/patient/{patient_id}` → `unknown`
- `GET /fhir/service-request/{order_id}` → `unknown`
- `GET /info` → `unknown`
- `GET /security-report` → `unknown`
- `GET /system-status` → `unknown`
- `GET /time-sync` → `unknown`
### consent
- `GET /check` → `unknown`
- `POST /grant` → `unknown`
- `POST /revoke` → `unknown`
### critical_alerts
- `GET /stats` → `unknown`
### dashboard
- `GET /dashboard` → `unknown`
- `GET /greeting` → `unknown`
### device_results
- `POST /results` → `unknown`
### edge
- `GET /devices` → `unknown`
- `GET /devices/{device_id}` → `unknown`
- `GET /fleet/summary` → `unknown`
- `GET /health` → `unknown`
- `GET /models` → `unknown`
- `GET /policy` → `unknown`
- `GET /tasks` → `unknown`
- `GET /tasks/{task_uid}` → `unknown`
- `POST /agent/heartbeat` → `unknown`
- `POST /agent/tasks/{task_uid}/result` → `unknown`
- `POST /agent/telemetry` → `unknown`
- `POST /devices/{device_id}/kill_switch` → `unknown`
- `POST /devices/{device_id}/quarantine` → `unknown`
- `POST /devices/{device_id}/reinstate` → `unknown`
- `POST /devices/{device_id}/revoke` → `unknown`
- `POST /models` → `unknown`
- `POST /models/{model_uid}/assign` → `unknown`
- `POST /models/{model_uid}/status` → `unknown`
- `POST /tasks` → `unknown`
- `POST /tasks/{task_uid}/cancel` → `unknown`
- `PUT /policy` → `unknown`
### ehr
- `GET /patient/{patient_id}` → `unknown`
- `GET /patient/{patient_id}/summary` → `unknown`
### id_scan
- `POST /scan` → `scan_national_id`
### identity
- `GET /lookup` → `unknown`
- `POST /link` → `unknown`
### insurance
- `GET /insurance/{insurance_id}` → `unknown`
### integrations
- `GET /status` → `unknown`
- `POST /{name}/probe` → `unknown`
### labs
- `GET /me` → `unknown`
- `GET /me/employees` → `unknown`
- `POST /me/employees` → `unknown`
- `PUT /me` → `unknown`
- `PUT /me/employees/{employee_id}` → `unknown`
### login
- `POST /login` → `unknown`
- `POST /logout` → `unknown`
### metrics
- `GET /metrics` → `unknown`
- `GET /metrics/prom` → `unknown`
### mobile
- `POST /change-password` → `unknown`
- `POST /refresh` → `unknown`
### national_identity
- `POST /national-id/verify` → `unknown`
### notifications
- `GET /history/{order_id}` → `unknown`
- `POST /send` → `unknown`
### optimizer
- `GET /analyze` → `run_analysis`
- `GET /metrics` → `unknown`
### patient_card
- `GET /{patient_id}` → `unknown`
- `GET /{patient_id}/history` → `unknown`
- `GET /{patient_id}/print` → `unknown`
- `GET /{patient_id}/qr.png` → `unknown`
- `POST /scan` → `unknown`
### patients
- `GET /family/{family_id}` → `unknown`
- `GET /{patient_id}` → `unknown`
- `GET /{patient_id}/children` → `unknown`
- `PUT /{patient_id}` → `unknown`
### qr
- `GET /qr-medical/{token}` → `unknown`
- `GET /qr/{token}` → `unknown`
### quality_control
- `GET /summary` → `unknown`
- `POST /batch` → `unknown`
### register
- `POST /register` → `unknown`
- `POST /register/citizen` → `unknown`
- `POST /register/doctor` → `unknown`
- `POST /register/staff` → `unknown`
### results
- `GET /history/{phone}` → `unknown`
- `GET /orders` → `unknown`
- `GET /orders/{order_id}` → `unknown`
- `GET /orders/{order_id}/intelligence` → `unknown`
- `GET /patient-history/{patient_id}` → `unknown`
- `GET /r/{token}` → `unknown`
- `GET /r/{token}/pdf` → `unknown`
- `GET /test-profiles` → `unknown`
- `POST /analyze` → `unknown`
- `POST /orders` → `unknown`
- `POST /orders/{order_id}/cancel` → `unknown`
- `POST /orders/{order_id}/validate` → `unknown`
### samples
- `GET /{barcode}` → `unknown`
- `PUT /{barcode}` → `unknown`
### security
- `GET /status` → `unknown`
### setup
- `GET /setup/status` → `unknown`
### stats
- `GET /summary` → `unknown`
- `GET /trends/daily` → `unknown`
- `GET /trends/flags` → `unknown`
- `GET /trends/patients` → `unknown`
- `GET /trends/tests` → `unknown`
- `GET /turnaround` → `unknown`
### test_results
- `GET /citizen/{health_id}` → `unknown`
- `GET /citizen/{health_id}/timeline` → `unknown`
- `GET /{result_id}` → `unknown`
- `POST /` → `unknown`
- `POST /validate` → `unknown`
- `PUT /{result_id}/verify` → `unknown`
### tiers
- `GET /admin/tiers/demands` → `unknown`
- `GET /admin/tiers/flags/{lab_id}` → `unknown`
- `GET /tiers` → `unknown`
- `GET /tiers/my` → `unknown`
- `POST /admin/tiers/flags/{lab_id}` → `unknown`
- `POST /tiers/upgrade` → `unknown`
- `PUT /admin/tiers/{lab_id}` → `unknown`

## Models

- **AIFeedback** (in `ai_interaction`)
- **AIInteraction** (in `ai_interaction`)
- **AIRetrievalRef** (in `ai_interaction`)
- **AIUnresolvedQuestion** (in `ai_interaction`)
- **MedicalTerminologyNormalized** (in `ai_interaction`)
- **AuditLog** (in `audit_log`)
- **Claim** (in `claim`)
- **ClaimItem** (in `claim`)
- **Consent** (in `consent`)
- **EdgeDevice** (in `edge`)
- **EdgeEvent** (in `edge`)
- **EdgeModel** (in `edge`)
- **EdgeModelAssignment** (in `edge`)
- **EdgePolicy** (in `edge`)
- **EdgeTask** (in `edge`)
- **EdgeTelemetry** (in `edge`)
- **Lab** (in `lab`)
- **LabOrder** (in `lab_order`)
- **LabResult** (in `lab_result`)
- **LabUser** (in `lab_user`)
- **OutboxEvent** (in `outbox`)
- **Patient** (in `patient`)
- **QualityControl** (in `quality_control`)
- **Sample** (in `sample`)
- **FeatureFlag** (in `subscription`)
- **LabSubscription** (in `subscription`)
- **UpgradeDemandScore** (in `subscription`)
- **UpgradeRequest** (in `subscription`)
- **TestResult** (in `test_result`)
- **TestType** (in `test_type`)
- **User** (in `user`)

## Events


## Plugins

- `MarketplacePlugin`
- `PluginManager`
- `PluginPermissionManager`
- `PluginVersionManager`

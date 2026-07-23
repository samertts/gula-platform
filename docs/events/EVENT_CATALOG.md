# GULA Platform — Event Catalog

**Version:** 1.0 | **Last Updated:** 2026-07-23

## Table of Contents

1. [Event Architecture](#1-event-architecture)
2. [Event Envelope](#2-event-envelope)
3. [Event Catalog](#3-event-catalog)
   - [Patient Domain](#31-patient-domain)
   - [Order Domain](#32-order-domain)
   - [Result Domain](#33-result-domain)
   - [Sample / Specimen Domain](#34-sample--specimen-domain)
   - [Notification Domain](#35-notification-domain)
   - [Audit Domain](#36-audit-domain)
   - [National / Citizen Domain](#37-national--citizen-domain)
   - [LIMS Domain](#38-lims-domain)
   - [SNDHS Domain](#39-sndhs-domain)
   - [AI / Data Platform Domain](#310-ai--data-platform-domain)
   - [System Domain](#311-system-domain)
   - [Financial / Claims Domain](#312-financial--claims-domain)
   - [Interoperability Domain](#313-interoperability-domain)
4. [Retry and Error Handling](#4-retry-and-error-handling)
5. [Idempotency](#5-idempotency)
6. [Related Documents](#6-related-documents)

---

## 1. Event Architecture

The GULA Platform uses a **Transactional Outbox Pattern** as its primary event delivery mechanism, with a complementary **in-process EventBus** for synchronous dispatch within the monolith process.

### Core Components

| Component | Location | Role |
|-----------|----------|------|
| `OutboxEvent` model | `backend/app/models/outbox.py:29` | Database table `outbox_events` storing pending events |
| `emit_to_outbox()` | `backend/app/services/outbox_service.py:51` | Writes event inside the business DB transaction |
| `OutboxWorker` | `backend/app/services/outbox_service.py:82` | Background poller: batches of 50 every 10s |
| `EventBus` | `shared/events/bus.py:11` | In-process publish/subscribe dispatcher |
| `events` singleton | `backend/app/core/events.py:16` | Canonical EventBus instance, re-exported to all backend code |
| `NationalDomainEvent` | `backend/app/national/events/base.py:11` | Base dataclass for national-domain events |
| `LIMSEvent` | `backend/app/lims/events.py:15` | Base dataclass for LIMS-domain events |

### Delivery Flow

```
Business Operation
    │
    ├── DB transaction start
    │   ├── Write business data (patients, orders, etc.)
    │   ├── Call emit_to_outbox() → INSERT into outbox_events (status=pending)
    │   └── DB commit (event committed atomically with business data)
    │
    └── OutboxWorker (polls every 10s, batches of 50)
        ├── SELECT pending/failed events WHERE attempts < MAX_ATTEMPTS
        ├── FOR UPDATE SKIP LOCKED (safe for multiple workers)
        ├── status → "processing"
        ├── events.emit() → in-process handlers run
        ├── On success → status = "done", processed_at = now
        └── On failure → attempts++, if >= MAX_ATTEMPTS → status = "failed"
```

### Guarantees

- **At-least-once delivery**: if the app crashes between business commit and worker dispatch, the event stays `pending` and is picked up next cycle.
- **Transactional atomicity**: event is written inside the same DB transaction as the business data; rollback removes both.
- **No broker dependency**: events queue in PostgreSQL; no RabbitMQ/Kafka required for core operations.
- **Auto-purge**: events older than 30 days with status `done` or `failed` are deleted by `purge_old_events()` (runs every 24h).

### Status Lifecycle

```
pending → processing → done
            ↓
          failed  (retried up to MAX_ATTEMPTS=5 times)
```

### Background Loops (defined in `backend/app/main.py`)

| Loop | Interval | Purpose |
|------|----------|---------|
| `OutboxWorker.background_loop()` | 10s | Poll and dispatch pending outbox events |
| `RecoveryWorker.background_loop()` | 10–30s | Probe failed circuit breakers, restore connectivity |
| `RepairEngine.background_loop()` | 30s | Auto-repair: memory GC, pool recycle, Redis reconnect |
| `_health_alert_loop()` | 60s | System health scoring (GREEN/YELLOW/RED) and alert webhooks |
| `_adaptive_concurrency_loop()` | 60s | Adjust `_MAX_CONCURRENT` based on DB latency |

---

## 2. Event Envelope

### In-Process EventBus Envelope

The `events.emit()` call passes a plain `dict` payload with no fixed envelope. The caller is responsible for including correlation identifiers.

### Outbox Database Schema

| Column | Type | Description |
|--------|------|-------------|
| `id` | `Integer PK` | Auto-increment event ID |
| `event_type` | `String(100)` | Dot-separated event type (e.g. `order.created`) |
| `aggregate_type` | `String(100)` | Domain aggregate name (e.g. `order`, `result`, `Patient`) |
| `aggregate_id` | `Integer` | ID of the aggregate instance |
| `payload` | `Text` | JSON-serialised event data |
| `status` | `String(20)` | `pending` / `processing` / `done` / `failed` |
| `attempts` | `Integer` | Delivery attempt count (default 0) |
| `last_error` | `Text` | Error message from last failed attempt (truncated to 500 chars) |
| `created_at` | `DateTime` | When the event was created |
| `processed_at` | `DateTime` | When the event was successfully processed |

### SNDHS NATS Event Envelope (future microservices topology)

Defined in `docs/sndhs/07-events.md`. Not yet deployed; shown for reference:

```json
{
  "id": "01J...",
  "specversion": "1.0",
  "type": "clin.order.created.v1",
  "source": "/rsn/BG/clinical/order-service",
  "time": "2026-05-05T12:34:56.789Z",
  "datacontenttype": "application/json",
  "schema_version": 1,
  "correlation_id": "01J...",
  "causation_id": "01J...",
  "region_id": "BG",
  "data": { "...": "..." },
  "signature": "ed25519:..."
}
```

### National Domain Event Envelope

```python
@dataclass
class NationalDomainEvent:
    event_type: str
    aggregate_id: str
    aggregate_type: str
    payload: dict
    timestamp: str          # ISO 8601, auto-set on creation
    correlation_id: str
    causation_id: str
    version: int = 1
```

### LIMS Domain Event Envelope

```python
@dataclass
class LIMSEvent:
    event_type: str
    aggregate_id: str
    aggregate_type: str
    lab_id: int | None
    user_id: int | None
    payload: dict
    timestamp: str          # ISO 8601, auto-set on creation
```

---

## 3. Event Catalog

### 3.1 Patient Domain

Events emitted by `patient_service.py`, `mpi/` (Master Patient Index), and `patient_card.py`.

| Event Type | Producer | Consumer(s) | Payload Summary | Version | Retry Policy | Idempotency Key |
|---|---|---|---|---|---|---|
| `patient.created` | `patient_service.py`, routes | Audit, Notification, MPI, SNDHS sync | `patient_id`, `lab_id`, `full_name`, `phone` | 1 | MAX_ATTEMPTS=5 | `patient_id` |
| `patient.updated` | `patient_service.py`, routes | Audit, MPI, SNDHS sync | `patient_id`, `lab_id`, `changed_fields` | 1 | MAX_ATTEMPTS=5 | `patient_id` |
| `patient.merged` | `mpi/resolver.py` | Audit, Notification, SNDHS sync | `survivor_patient_id`, `merged_patient_id`, `lab_id` | 1 | MAX_ATTEMPTS=5 | `survivor_patient_id` |
| `patient.deleted` | `patient_service.py`, routes | Audit, MPI, Edge sync | `patient_id`, `lab_id`, `soft_delete` | 1 | MAX_ATTEMPTS=5 | `patient_id` |
| `national.patient.registered` | `national/workflows/patient_registration.py` | Citizen registry, NHOP | `citizen_id`, `health_number`, `facility_id` | 1 | MAX_ATTEMPTS=5 | `citizen_id` |
| `national.patient.merged` | MPI across national domains | National audit, SNDHS | `survivor_id`, `merged_id` | 1 | MAX_ATTEMPTS=5 | `survivor_id` |
| `national.patient.guardian_assigned` | Patient service | Notification, EHR | `patient_id`, `guardian_id` | 1 | MAX_ATTEMPTS=5 | `patient_id` |
| `data_platform.golden_record.created` | `data_platform_service.py` | MDM, NHOP | `golden_record_id`, `patient_id`, `citizen_id`, `confidence_score` | 1 | MAX_ATTEMPTS=5 | `golden_record_id` |

### 3.2 Order Domain

Events emitted by `order_service.py` and `routes/test_results.py`. The order lifecycle state machine is defined in `domain/order_state.py`.

**Lab order lifecycle:** `REQUESTED → COLLECTED → RECEIVED → IN_PROGRESS → COMPLETED → VERIFIED`

| Event Type | Producer | Consumer(s) | Payload Summary | Version | Retry Policy | Idempotency Key |
|---|---|---|---|---|---|---|
| `order.created` | `order_service.py:292` | Notification, Audit, SNDHS, Stats | `order_id`, `patient_id`, `lab_id`, `created_by`, `result_count` | 1 | MAX_ATTEMPTS=5 | `order_id` |
| `order.validated` | `order_service.py:543` | Audit, Notification, SNDHS | `order_id`, `patient_id`, `lab_id`, `validated_by` | 1 | MAX_ATTEMPTS=5 | `order_id` |
| `order.cancelled` | `order_service.py:586` | Audit, Notification, SNDHS, Stats | `order_id`, `patient_id`, `cancelled_by` | 1 | MAX_ATTEMPTS=5 | `order_id` |
| `order.collected` | Sample routes, device bridge | LIMS, Notification, SNDHS | `order_id`, `patient_id`, `collected_by`, `timestamp` | 1 | MAX_ATTEMPTS=5 | `order_id` |
| `order.received` | Lab intake routes | LIMS, Notification | `order_id`, `received_by`, `timestamp` | 1 | MAX_ATTEMPTS=5 | `order_id` |
| `order.in_progress` | Result entry routes | Audit, Status dashboard | `order_id`, `test_name`, `started_by` | 1 | MAX_ATTEMPTS=5 | `order_id` |
| `order.completed` | Result routes | Notification, Patient card, SNDHS | `order_id`, `completed_by`, `result_count` | 1 | MAX_ATTEMPTS=5 | `order_id` |
| `order.verified` | Verification routes | Notification (patient/citizen portal) | `order_id`, `verified_by`, `verified_at` | 1 | MAX_ATTEMPTS=5 | `order_id` |

### 3.3 Result Domain

Events emitted by `order_service.py`, `test_results.py`, and `critical_alerts.py`.

| Event Type | Producer | Consumer(s) | Payload Summary | Version | Retry Policy | Idempotency Key |
|---|---|---|---|---|---|---|
| `result.recorded` | `order_service.py` (create_result), routes | Audit, Interpretation engine, Patient card | `result_id`, `order_id`, `test_name`, `value`, `flag` | 1 | MAX_ATTEMPTS=5 | `result_id` |
| `result.updated` | Result amendment routes | Audit, Interpretation engine, SNDHS | `result_id`, `order_id`, `previous_value`, `new_value`, `amended_by` | 1 | MAX_ATTEMPTS=5 | `result_id` |
| `result.validated` | Validation routes | Audit, Notification, AI analysis | `result_id`, `order_id`, `validated_by`, `validated_at` | 1 | MAX_ATTEMPTS=5 | `result_id` |
| `result.critical` | `order_service.py:304`, `test_results.py:393` | Critical alerts, Notification (SMS/push), Audit | `order_id`, `result_id`, `patient_id`, `patient_name`, `patient_phone`, `test_name`, `value`, `lab_id` | 1 | MAX_ATTEMPTS=5 | `result_id` |

### 3.4 Sample / Specimen Domain

Events defined in `lims/events.py` for the specimen lifecycle and in `shared/events/constants.py` for core sample events.

| Event Type | Producer | Consumer(s) | Payload Summary | Version | Retry Policy | Idempotency Key |
|---|---|---|---|---|---|---|
| `sample.collected` | Lab intake routes, device bridge | LIMS, Notification, Order state machine | `sample_id`, `order_id`, `patient_id`, `collected_by`, `timestamp` | 1 | MAX_ATTEMPTS=5 | `sample_id` |
| `sample.received` | Lab intake routes | LIMS, Notification | `sample_id`, `order_id`, `received_by`, `condition` | 1 | MAX_ATTEMPTS=5 | `sample_id` |
| `sample.rejected` | Sample validation | Notification, Order state machine, Audit | `sample_id`, `order_id`, `reason`, `rejected_by` | 1 | MAX_ATTEMPTS=5 | `sample_id` |

**LIMS specimen events** (defined in `backend/app/lims/events.py:28-71`):

| Event Type | Description |
|---|---|
| `lims.specimen.ordered` | Specimen request created |
| `lims.specimen.registered` | Specimen registered in system |
| `lims.specimen.collected` | Specimen physically collected |
| `lims.specimen.transporting` | Specimen in transit to lab |
| `lims.specimen.received` | Specimen arrived at lab |
| `lims.specimen.accepted` | Specimen passed quality check |
| `lims.specimen.rejected` | Specimen failed quality check |
| `lims.specimen.aliquoted` | Specimen split into aliquots |
| `lims.specimen.analysis_started` | Analysis begun on instrument |
| `lims.specimen.analyzed` | Raw result obtained |
| `lims.specimen.verified` | Result verified by technologist |
| `lims.specimen.validated` | Result validated by lab director |
| `lims.specimen.released` | Result released to ordering clinician |
| `lims.specimen.archived` | Specimen moved to long-term storage |
| `lims.specimen.disposed` | Specimen destroyed per retention policy |

### 3.5 Notification Domain

The `NotificationService` (`backend/app/notifications/service.py:23`) consumes events and sends via channels. It maintains its own circuit breaker (threshold=10, recovery=30s).

| Event Type | Producer | Consumer(s) | Payload Summary | Version | Retry Policy | Idempotency Key |
|---|---|---|---|---|---|---|
| `notification.sent` | `NotificationService.send()` | Audit log | `channel`, `recipient`, `template_id`, `notification_id` | 1 | Circuit breaker (10 failures → open 30s) | `notification_id` |
| `notification.delivered` | Delivery callback (SMS/email/push provider) | Audit log, Stats | `notification_id`, `channel`, `delivered_at` | 1 | MAX_ATTEMPTS=5 | `notification_id` |
| `notification.failed` | `NotificationService.send()` | Audit log, Alerting | `notification_id`, `channel`, `error` | 1 | MAX_ATTEMPTS=5 | `notification_id` |

### 3.6 Audit Domain

| Event Type | Producer | Consumer(s) | Payload Summary | Version | Retry Policy | Idempotency Key |
|---|---|---|---|---|---|---|
| `audit.entry.created` | `audit_service.py` (log_action) | Audit hash chain, SNDHS compliance, NHOP | `action`, `resource_type`, `resource_id`, `user_id`, `chain_hash`, `anchor_hmac` | 1 | MAX_ATTEMPTS=5 | `audit_entry_id` |

The audit service (`backend/app/services/audit_service.py`) writes SHA-256 hash-chained entries to the `audit_log` table. Every mutation across the platform calls `log_action()` which creates an entry with `chain_hash = SHA-256(previous_chain_hash + this_record_data)`. Anchor HMAC checkpoints are written every 100 entries.

### 3.7 National / Citizen Domain

Events defined in `backend/app/national/events/` and emitted by `citizen_service.py` and `family_service.py`.

| Event Type | Producer | Consumer(s) | Payload Summary | Version | Retry Policy | Idempotency Key |
|---|---|---|---|---|---|---|
| `national.citizen.created` | `citizen_service.py:30` | NHOP, SNDHS, Patient registry | `citizen_id`, `health_number`, `full_name`, `national_id_hash` | 1 | MAX_ATTEMPTS=5 | `citizen_id` |
| `national.citizen.updated` | `citizen_service.py:49` | NHOP, SNDHS | `citizen_id`, `changed_fields` | 1 | MAX_ATTEMPTS=5 | `citizen_id` |
| `national.citizen.verified` | Identity verification workflow | Audit, NHOP | `citizen_id`, `verification_method` | 1 | MAX_ATTEMPTS=5 | `citizen_id` |
| `national.citizen.merged` | MPI merge workflow | NHOP, SNDHS, Audit | `survivor_id`, `merged_id` | 1 | MAX_ATTEMPTS=5 | `survivor_id` |
| `national.citizen.deceased` | Death registration workflow | NHOP, SNDHS, Patient status | `citizen_id`, `date_of_death`, `cause_code` | 1 | MAX_ATTEMPTS=5 | `citizen_id` |
| `national.health_number.assigned` | `citizen_service.py:31` | Patient card, NHOP | `citizen_id`, `health_number` | 1 | MAX_ATTEMPTS=5 | `citizen_id` |
| `national.family.created` | `family_service.py:13` | NHOP, SNDHS | `family_id`, `head_citizen_id`, `members` | 1 | MAX_ATTEMPTS=5 | `family_id` |
| `national.family.member_added` | `family_service.py:18` | NHOP | `family_id`, `member_id` | 1 | MAX_ATTEMPTS=5 | `family_id`+`member_id` |
| `national.family.member_removed` | `family_service.py:22` | NHOP | `family_id`, `member_id` | 1 | MAX_ATTEMPTS=5 | `family_id`+`member_id` |

### 3.8 LIMS Domain

Events defined in `backend/app/lims/events.py` for the full Laboratory Information Management System lifecycle.

**LIMS Order Events:**

| Event Type | Description |
|---|---|
| `lims.order.accessioned` | Order registered in LIMS |
| `lims.order.completed` | All results for order finalised |
| `lims.order.validated` | Order validated by lab director |
| `lims.order.released` | Results released to clinician |
| `lims.order.cancelled` | Order cancelled |
| `lims.order.corrected` | Order corrected post-release |

**LIMS Result Events:**

| Event Type | Description |
|---|---|
| `lims.result.created` | Individual result row created |
| `lims.result.updated` | Result amended |
| `lims.result.auto_validated` | Result passed auto-validation rules |
| `lims.result.validated` | Result manually validated |
| `lims.result.flagged` | Result flagged for review |
| `lims.result.critical` | Critical value detected |
| `lims.result.delta_check_failed` | Delta check threshold exceeded |

**LIMS Quality Control Events:**

| Event Type | Description |
|---|---|
| `lims.qc.iqc_run` | Internal quality control run completed |
| `lims.qc.iqc_out_of_control` | IQC outside acceptable range |
| `lims.qc.eqa_submitted` | External quality assessment submitted |
| `lims.qc.eqa_result_received` | EQA result received |
| `lims.qc.calibration_performed` | Instrument calibration performed |
| `lims.qc.calibration_failed` | Instrument calibration failed |

**LIMS Instrument Events:**

| Event Type | Description |
|---|---|
| `lims.instrument.online` | Instrument connected and ready |
| `lims.instrument.offline` | Instrument disconnected |
| `lims.instrument.error` | Instrument error condition |
| `lims.instrument.maintenance_due` | Scheduled maintenance due |
| `lims.instrument.maintenance_performed` | Maintenance completed |

**LIMS Inventory Events:**

| Event Type | Description |
|---|---|
| `lims.inventory.reagent_low` | Reagent stock below threshold |
| `lims.inventory.lot_expiring` | Lot approaching expiry |
| `lims.inventory.lot_expired` | Lot expired |

**LIMS Report Events:**

| Event Type | Description |
|---|---|
| `lims.report.generated` | Report document generated |
| `lims.report.finalized` | Report finalised and signed |
| `lims.report.corrected` | Report corrected post-finalisation |

### 3.9 SNDHS Domain

SNDHS-lite integration sync events. The full SNDHS event topology (NATS JetStream) is documented in `docs/sndhs/07-events.md` for the future microservices architecture.

| Event Type | Producer | Consumer(s) | Payload Summary | Version | Retry Policy | Idempotency Key |
|---|---|---|---|---|---|---|
| `sndhs.sync.triggered` | SNDHS backfill script, order/patient routes | SNDHS bridge, NHOP | `sync_id`, `table`, `last_pk`, `batch_size` | 1 | MAX_ATTEMPTS=5 | `sync_id` |
| `sndhs.sync.completed` | SNDHS bridge | Audit, NHOP | `sync_id`, `records_synced`, `duration_ms` | 1 | MAX_ATTEMPTS=5 | `sync_id` |
| `sndhs.sync.failed` | SNDHS bridge | Alerting, Audit | `sync_id`, `error`, `failed_records` | 1 | MAX_ATTEMPTS=5 | `sync_id` |

### 3.10 AI / Data Platform Domain

Events related to AI analysis, clinical intelligence, and the national data platform.

| Event Type | Producer | Consumer(s) | Payload Summary | Version | Retry Policy | Idempotency Key |
|---|---|---|---|---|---|---|
| `ai.analysis.requested` | Result routes, clinical engine | AI inference service, NHOP | `analysis_id`, `result_ids`, `analysis_type`, `patient_id` | 1 | MAX_ATTEMPTS=5 | `analysis_id` |
| `ai.analysis.completed` | AI inference service | Notification, Patient card, Clinical intelligence | `analysis_id`, `result_ids`, `findings`, `confidence` | 1 | MAX_ATTEMPTS=5 | `analysis_id` |
| `ai.analysis.failed` | AI inference service | Alerting, Audit | `analysis_id`, `error`, `result_ids` | 1 | MAX_ATTEMPTS=5 | `analysis_id` |

### 3.11 System Domain

Events related to platform health, self-healing, and infrastructure. These are logged but may not all be emitted as formal EventBus events — they are monitored via `_health_alert_loop()` and repair engine logs.

| Event Type | Producer | Consumer(s) | Payload Summary | Version | Retry Policy | Idempotency Key |
|---|---|---|---|---|---|---|
| `system.degraded.entered` | `self_healing.py` health monitor | Alerting webhook (Telegram/Discord/Slack), Metrics | `level` (L1/L2/L3), `reason`, `circuit_states` | 1 | No retry (fire-and-forget alert) | None |
| `system.degraded.exited` | `RecoveryWorker`, `RepairEngine` | Alerting webhook, Metrics | `level`, `duration_degraded_seconds` | 1 | No retry | None |
| `system.healing.action.taken` | `auto_repair.py` (RepairEngine) | Audit log, Metrics | `action_name`, `success`, `details`, `rss_mb` | 1 | No retry (idempotent action) | `action_name`+`timestamp` |

**Auto-repair actions** (defined in `backend/app/core/auto_repair.py:104-171`):

| Action Name | Condition | Effect |
|---|---|---|
| `memory_gc` | RSS > 600 MB (warn) or 900 MB (critical) | `gc.collect(2)`, dispose idle DB connections |
| `circuit_probe` | DB circuit breaker stuck OPEN | Force-probe DB connection; reset if successful |
| `pool_recycle` | DB pool exhaustion detected | `engine.dispose(close=False)` |
| `redis_reconnect` | Redis circuit breaker OPEN | Force `cache.ping()`, reset circuit if successful |
| `outbox_backlog` | Outbox queue > 200 pending | Log warning (not yet auto-escalated) |

### 3.12 Financial / Claims Domain

| Event Type | Producer | Consumer(s) | Payload Summary | Version | Retry Policy | Idempotency Key |
|---|---|---|---|---|---|---|
| `claim_submitted` | `claims_service.py:188` | Financial engine, Audit, Insurance gateway | `claim_id`, `lab_id`, `patient_id`, `order_id`, `total_amount`, `items` | 1 | MAX_ATTEMPTS=5 | `claim_id` |

### 3.13 Interoperability Domain

Events for FHIR, HL7, and CDC streaming via `backend/app/routes/national_streaming.py`.

| Event Type | Producer | Consumer(s) | Payload Summary | Version | Retry Policy | Idempotency Key |
|---|---|---|---|---|---|---|
| `fhir.<resource_type>.<event>` | `national_streaming.py:77` | NHOP, external FHIR subscribers | `resource_type`, `resource_id`, `subscription_id`, `resource` | 1 | MAX_ATTEMPTS=5 | `resource_type`+`resource_id`+`event` |
| `hl7.<message_type>` | `national_streaming.py:120` | NHOP, SNDHS, device bridge | `message_type`, `message_control_id`, `parsed_segments`, `source_device` | 1 | MAX_ATTEMPTS=5 | `message_control_id` |

### Workflow Events (from `docs/national/WORKFLOW_CATALOG.md`)

These are logical events emitted by the workflow engine during state machine transitions:

| Workflow | Events Emitted |
|---|---|
| Patient Registration | `PatientRegistered`, `HealthNumberAssigned`, `IdentityVerified` |
| Referral | `ReferralCreated`, `ReferralSent`, `ReferralAccepted`, `ReferralRejected`, `ReferralCompleted`, `ReferralCancelled` |
| Discharge | `DischargePlanned`, `DischargeSummaryCompleted`, `PatientDischarged`, `DischargeCancelled` |
| Transfer | `TransferOrdered`, `TransferInProgress`, `TransferCompleted`, `TransferCancelled` |
| Medication | Emitted via order state machine transitions |

---

## 4. Retry and Error Handling

### Outbox Retry Policy

| Parameter | Value | Source |
|-----------|-------|--------|
| `MAX_ATTEMPTS` | 5 | `backend/app/models/outbox.py:26` |
| `_BATCH_SIZE` | 50 events/cycle | `backend/app/services/outbox_service.py:44` |
| `_POLL_SECS` | 10 seconds | `backend/app/services/outbox_service.py:45` |
| Failure handling | `attempts++`, `last_error` set to exception message (truncated to 500 chars) | `outbox_service.py:134` |
| Status after MAX_ATTEMPTS | `failed` (permanent) | `outbox_service.py:136` |
| Dead-event cleanup | Auto-purge after 30 days via `purge_old_events()` in 24h cycle | `outbox_service.py:206` |
| Concurrency safety | `FOR UPDATE SKIP LOCKED` for multi-worker safety | `outbox_service.py:106` |

### Dead Letter / Permanent Failure

When an event exhausts `MAX_ATTEMPTS=5`:
1. Status is set to `failed` permanently
2. A critical log is emitted: `[OUTBOX] PERMANENTLY FAILED event_type=... id=... after 5 attempts`
3. The event remains in the database for 30 days (for forensic investigation)
4. After 30 days, `purge_old_events()` deletes it
5. No automatic re-queue — human investigation required
6. Ops alerting should monitor for `failed` event count > 0 in Prometheus

### Notification Circuit Breaker

The `NotificationService` (`backend/app/notifications/service.py:25`) maintains a separate circuit breaker to protect against downstream notification provider failures:
- **Failure threshold:** 10 consecutive failures
- **Recovery timeout:** 30 seconds
- **State:** CLOSED → OPEN → HALF_OPEN → CLOSED

### Self-Healing Circuit Breakers

Defined in `backend/app/core/self_healing.py:50`:
- DB circuit breaker: threshold=3 failures, recovery timeout=30s
- Redis circuit breaker: threshold=3 failures, recovery timeout=30s
- Degradation levels: NONE → L1_CACHE_HEAVY → L2_READ_ONLY → L3_CRITICAL_ONLY

---

## 5. Idempotency

### Outbox-Level Idempotency

The outbox pattern inherently provides idempotency at the persistence layer:
- Events are written inside the business transaction — if the same business operation is attempted twice, the second attempt will fail at the business logic level (e.g., unique constraint, optimistic lock on `version` column, idempotency key).
- The `OutboxWorker` uses `FOR UPDATE SKIP LOCKED` — events are locked while being processed, preventing double-dispatch.

### Handler-Level Idempotency

Event handlers must be idempotent because the outbox delivers at-least-once. Idempotency strategies in the codebase:

| Strategy | Used By | Implementation |
|---|---|---|
| Dedup by event `id` | SNDHS NATS consumers (planned) | Redis bloom filter + exact set, 24h window |
| Dedup by `aggregate_id + event_type` | Notification handlers | Check if notification already sent for this aggregate |
| Dedup by `correlation_id` | NHOP sync, SNDHS bridge | Idempotency key passed through causation chain |
| Optimistic locking | `LabResult` mutations | `version` column checked on every update |
| Status guards | Order state machine | `enforce_transition()` rejects invalid state transitions |

### Event ID Correlation Chain

```
Business Request (Idempotency-Key header)
    │
    ▼
order.created event (correlation_id = Idempotency-Key)
    │
    ├── result.recorded event (causation_id = order.created.id, correlation_id = same)
    │
    └── notification.sent event (causation_id = result.recorded.id, correlation_id = same)
```

---

## 6. Related Documents

| Document | Description |
|---|---|
| `docs/decisions/ARCHITECTURE_DECISIONS.md` (AD-ARC-007) | Event-driven architecture via outbox pattern — decision record |
| `docs/sndhs/07-events.md` | SNDHS NATS JetStream event topology, envelope, domain catalogue |
| `docs/national/WORKFLOW_CATALOG.md` | National workflow state machines and their emitted events |
| `backend/app/services/outbox_service.py` | Outbox worker implementation (writer, poller, purger) |
| `backend/app/models/outbox.py` | `OutboxEvent` ORM model and `MAX_ATTEMPTS` constant |
| `shared/events/bus.py` | In-process EventBus implementation |
| `shared/events/constants.py` | Canonical event type string constants |
| `backend/app/core/events.py` | Backend re-export of EventBus and constants |
| `backend/app/national/events/base.py` | `NationalDomainEvent` base dataclass |
| `backend/app/lims/events.py` | LIMS domain event definitions (40+ event types) |
| `backend/app/national/events/citizen_events.py` | Citizen domain event types |
| `backend/app/national/events/patient_events.py` | National patient event types |
| `backend/app/core/self_healing.py` | Circuit breaker, degraded mode, recovery worker |
| `backend/app/core/auto_repair.py` | Auto-repair engine with 5 repair actions |
| `backend/app/core/startup_guard.py` | `system_ready` flag and startup validation |
| `backend/app/notifications/service.py` | Notification service with circuit breaker |
| `backend/app/services/order_service.py` | Order/result event producers |
| `backend/app/services/critical_alerts.py` | Critical value thresholds and detection |
| `backend/app/services/audit_service.py` | Hash-chained audit logging |
| `backend/app/routes/national_streaming.py` | FHIR/HL7/CDC event streaming endpoints |
| `backend/app/services/data_platform_service.py` | Data platform event recording and MDM |
| `backend/app/services/claims_service.py` | Claims submission with outbox |
| `scripts/sndhs_phase1_backfill.py` | SNDHS Phase 1 data backfill (sync trigger) |

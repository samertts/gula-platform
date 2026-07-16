# National Radiology Information System Platform (NRISP) — Architecture

**Platform:** NRISP — National Radiology Information System Platform
**Mission:** 028
**Status:** Planned
**Version:** 0.1.0

---

## 1. Overview

The National Radiology Information System Platform (NRISP) provides comprehensive radiology workflow management for Iraqi healthcare facilities. It covers the full imaging lifecycle: order entry, modality worklist management, exam acquisition tracking, DICOM storage and retrieval, structured reporting, PACS archive management, device integration, and AI-powered imaging analysis. NRISP is designed to operate as both a standalone RIS and as an integrated component of the broader GULA healthcare platform.

### 1.1 Key Objectives

- Deliver a complete Radiology Information System (RIS) with exam scheduling, documentation, and reporting
- Provide native DICOM storage with FHIR mapping layer for interoperability with EHR
- Implement three-tier PACS architecture (hot/warm/cold storage) for cost-effective image management
- Support modality worklist (MWL) and Modality Performed Procedure Step (MPPS) via DICOM standards
- Enable structured radiology reporting with standard templates (RSNA, Iraqi national templates)
- Integrate AI imaging models through an abstraction layer (not hardwired to any specific AI provider)
- Provide web-based image viewer with streaming, thumbnails, and DICOM-to-PNG conversion
- Support IHE integration profiles for cross-enterprise document sharing
- Manage imaging devices, maintenance schedules, and modality connectivity
- Enable offline-capable exam documentation for remote/rural facilities

### 1.2 Scope

| Area | In Scope | Out of Scope |
|------|----------|--------------|
| RIS | Order management, scheduling, exam documentation, reporting | Billing/claims radiology coding |
| PACS | DICOM storage, query/retrieve, archive tiers, routing | Vendor-neutral archive (VNA) |
| DICOM | Storage SCP, Query/Retrieve SCU/SCP, MWL, MPPS | DICOM structured reporting (SR) |
| Imaging viewer | Web viewer, streaming, annotations, measurements | 3D reconstruction, advanced post-processing |
| AI | Model registry, inference pipeline, triage notifications | Model training, data labeling |
| Device integration | Modality connectivity, worklist, MPPS handler | Modality configuration management |
| Reporting | Structured templates, voice dictation integration, sign-off | Speech recognition engine |
| IHE | Scheduled Workflow (SWF), Patient Information Reconciliation (PIR) | Cross-document, XDS-I |

---

## 2. System Context

```
+------------------------------------------------------------------+
|              National Radiology Information System Platform        |
+------------------------------------------------------------------+
|                                                                     |
|  +------------------+  +------------------+  +------------------+  |
|  | Exam Workflow    |  | Reporting        |  | Image Viewer     |  |
|  | (Order →         |  | (Structured      |  | (Web-based,      |  |
|  |  Schedule →      |  |  Reports,        |  |  Streaming,      |  |
|  |  Perform →       |  |  Templates,      |  |  Annotations,    |  |
|  |  Report →        |  |  Sign-off)       |  |  DICOM→PNG)      |  |
|  |  Archive)        |  |                  |  |                  |  |
|  +------------------+  +------------------+  +------------------+  |
|                                                                     |
|  +------------------+  +------------------+  +------------------+  |
|  | Device           |  | AI Imaging       |  | PACS Archive     |  |
|  | Integration      |  | (Model Registry, |  | (Hot/Warm/Cold   |  |
|  | (MWL, MPPS,      |  |  Triage, Quality |  |  Storage Tiers,  |  |
|  |  DICOM SCP/SCU)  |  |  Detection)      |  |  Auto-Routing)   |  |
|  +------------------+  +------------------+  +------------------+  |
+---------------------------+---------------------------------------+
                            |
+---------------------------+---------------------------------------+
|                      Radiology Service Layer                        |
|                                                                     |
|  +------------------+  +------------------+  +------------------+  |
|  | RadiologyService |  | PACSService      |  | DeviceIntegration- | |
|  | (Workflow,       |  | (Storage,        |  | Service (MWL,    | |
|  |  Reporting,      |  |  Query/Retrieve, |  |  MPPS, DICOM     | |
|  |  Scheduling)     |  |  Archive Tiers)  |  |  SCP/SCU)        | |
|  +------------------+  +------------------+  +------------------+  |
|                                                                     |
|  +------------------+  +------------------+  +------------------+  |
|  | AIService        |  | ViewerService    |  | Sync Engine      |  |
|  | (Model Registry, |  | (Streaming,      |  | (Offline         |  |
|  |  Inference,      |  |  Conversion,     |  |  Support)        |  |
|  |  Triage)         |  |  Annotations)    |  |                  |  |
|  +------------------+  +------------------+  +------------------+  |
+---------------------------+---------------------------------------+
                            |
+---------------------------+---------------------------------------+
|                         DICOM Network                                |
|                                                                     |
|  +------------------+  +------------------+  +------------------+  |
|  | CT Scanner       |  | MRI Scanner      |  | X-Ray / US      |  |
|  | (DICOM MWL SCU   |  | (DICOM MWL SCU   |  | (DICOM MWL SCU  |  |
|  |  + MPPS SCU)     |  |  + MPPS SCU)     |  |  + MPPS SCU)    |  |
|  +------------------+  +------------------+  +------------------+  |
+------------------------------------------------------------------+
|                                                                     |
|  +-------------------------------------------------------------+   |
|  |  PostgreSQL 16 (Radiology Tables + EHR Integration)           |   |
|  |  Redis 7 (Cache, Worklist, Real-time Status)                  |   |
|  |  File System / S3 (Hot Tier DICOM)                            |   |
|  |  S3 / Glacier (Warm/Cold Tier DICOM Archive)                 |   |
|  +-------------------------------------------------------------+   |
+------------------------------------------------------------------+
```

---

## 3. Module Structure

### 3.1 Backend Module (`backend/app/radiology/`)

```
backend/app/radiology/
├── __init__.py
├── base.py                      # RADIOLOGYBase declarative base
├── models/
│   ├── __init__.py
│   ├── imaging_order.py          # Radiology order from EHR
│   ├── exam_schedule.py          # Scheduled exam slots
│   ├── exam_performed.py         # Completed exam record
│   ├── modality.py               # Imaging modality definitions
│   ├── modality_worklist.py      # DICOM MWL entries
│   ├── modality_mpps.py          # Modality Performed Procedure Step
│   ├── dicom_study.py            # DICOM study-level metadata
│   ├── dicom_series.py           # DICOM series-level metadata
│   ├── dicom_instance.py         # DICOM instance-level metadata
│   ├── storage_tier.py           # Hot/warm/cold storage configuration
│   ├── archive_rule.py           # Auto-archive routing rules
│   ├── radiology_report.py       # Structured radiology report
│   ├── report_template.py        # Report templates
│   ├── radiology_device.py       # Imaging device registry
│   ├── device_maintenance.py     # Device maintenance schedule
│   ├── ai_model.py               # AI model registry
│   ├── ai_inference.py           # AI inference record
│   ├── ai_triage.py              # AI triage alert
│   └── pacs_archive.py           # PACS archive location
├── services/
│   ├── __init__.py
│   ├── radiology_service.py      # Core RIS business logic
│   ├── pacs_service.py           # DICOM storage and archive
│   ├── device_integration_service.py # DICOM modality integration
│   ├── ai_service.py             # AI imaging abstraction layer
│   └── viewer_service.py         # Image viewer and conversion
└── routes/
    ├── __init__.py
    ├── exams.py                  # Exam workflow endpoints
    ├── reports.py                # Report endpoints
    ├── pacs.py                   # PACS/DICOM endpoints
    ├── devices.py                # Device management endpoints
    ├── ai.py                     # AI imaging endpoints
    ├── viewer.py                 # Image viewer endpoints
    ├── modalities.py             # Modality MWL/MPPS endpoints
    └── archive.py                # Archive management endpoints
```

---

## 4. Core Entities (18 Models)

### 4.1 Workflow (3)

| Entity | Table | Purpose | Key Fields |
|--------|-------|---------|------------|
| `ImagingOrder` | `radiology_imaging_orders` | Radiology order from EHR/referral | patient_id, orderer_id, exam_code, modality, clinical_indication, priority, status (ordered/scheduled/performed/reported/verified), accession_number |
| `ExamSchedule` | `radiology_exam_schedules` | Scheduled appointment for exam | order_id, scheduled_date, scheduled_time, modality_id, room_id, technologist_id, status (scheduled/arrived/started/completed/cancelled), estimated_duration |
| `ExamPerformed` | `radiology_exams_performed` | Completed exam | order_id, schedule_id, modality_id, performed_by, started_at, completed_at, patient_prep, contrast_used, dose_parameters, technique_notes, dicom_study_uid |

### 4.2 Imaging Devices (2)

| Entity | Table | Purpose | Key Fields |
|--------|-------|---------|------------|
| `Modality` | `radiology_modalities` | Imaging modality definition | modality_type (CT/MR/US/CR/DX/MG/NM), name, station_name, ae_title, ip_address, dicom_port, location_id, status |
| `RadiologyDevice` | `radiology_devices` | Physical imaging device | modality_id, manufacturer, model, serial_number, software_version, installation_date, warranty_expiry, last_maintenance_date, next_maintenance_date, calibration_due_date |

### 4.3 DICOM (4)

| Entity | Table | Purpose | Key Fields |
|--------|-------|---------|------------|
| `DICOMStudy` | `radiology_dicom_studies` | DICOM study-level metadata | study_uid, patient_id, accession_number, study_date, study_description, modality, referring_physician, performing_physician, series_count, instance_count, storage_tier, storage_path |
| `DICOMSeries` | `radiology_dicom_series` | DICOM series-level metadata | series_uid, study_id, series_number, series_description, modality, body_part, laterality, image_count, series_date, protocol_name, storage_path |
| `DICOMInstance` | `radiology_dicom_instances` | DICOM instance-level metadata | sop_instance_uid, series_id, instance_number, sop_class_uid, transfer_syntax_uid, image_type, pixel_data_size, rows, columns, bits_stored, storage_path, file_hash, file_size |
| `PACSArchive` | `radiology_pacs_archives` | PACS storage location | name, archive_type (hot/warm/cold), storage_protocol (filesystem/s3/glacier), base_path, url, access_key, active_flag, available_space, total_space |

### 4.4 MWL/MPPS (2)

| Entity | Table | Purpose | Key Fields |
|--------|-------|---------|------------|
| `ModalityWorklist` | `radiology_modality_worklist` | DICOM MWL entries | scheduled_station_ae_title, scheduled_procedure_step_id, accession_number, requested_procedure_id, study_uid, patient_id, patient_name, modality, scheduled_datetime, procedure_code, procedure_description, status (active/completed/cancelled) |
| `ModalityMPPS` | `radiology_modality_mpps` | Modality Performed Procedure Step | worklist_id, station_ae_title, performed_procedure_step_id, study_uid, procedure_code, procedure_description, started_at, ended_at, status (in_progress/completed/discontinued), performed_by, notes |

### 4.5 Reporting (2)

| Entity | Table | Purpose | Key Fields |
|--------|-------|---------|------------|
| `RadiologyReport` | `radiology_reports` | Structured radiology report | exam_id, report_template_id, radiologist_id, clinical_history, technique, findings, impression, conclusion, recommendations, status (draft/preliminary/final/addendum), verified_at, verified_by, critical_finding_flag |
| `ReportTemplate` | `radiology_report_templates` | Report templates | template_name, modality, body_part, structured_fields (JSON), sample_text, is_active, template_type (RSNA/iraqi_national/custom) |

### 4.6 AI (3)

| Entity | Table | Purpose | Key Fields |
|--------|-------|---------|------------|
| `AIModel` | `radiology_ai_models` | AI model registry | name, version, vendor, model_type (triage/detection/quantification/quality), modality, body_part, input_requirements, output_schema (JSON), status, endpoint_url, api_key, supported_sop_classes |
| `AIInference` | `radiology_ai_inferences` | AI inference record | model_id, exam_id, series_id, instance_uids (JSON), input_data, output_data (JSON), confidence_score, processing_time_ms, status, error_message |
| `AITriage` | `radiology_ai_triage` | AI triage alert | inference_id, exam_id, finding_type, severity (critical/urgent/routine), recommendation, notified_radiologist, acknowledged_at, resolved_at |

### 4.7 Archive (2)

| Entity | Table | Purpose | Key Fields |
|--------|-------|---------|------------|
| `StorageTier` | `radiology_storage_tiers` | Storage tier definitions | name (hot/warm/cold), storage_type (filesystem/s3/glacier), retention_days, compression (lossless/lossy), retrieval_cost, retrieval_time_seconds, base_path |
| `ArchiveRule` | `radiology_archive_rules` | Auto-archive rules | rule_name, trigger_event (exam_completed/report_verified/age_based), modality_filter, age_days, source_tier, destination_tier, compression_mode, enabled |

### 4.8 Device Maintenance (1)

| Entity | Table | Purpose | Key Fields |
|--------|-------|---------|------------|
| `DeviceMaintenance` | `radiology_device_maintenance` | Device maintenance records | device_id, maintenance_type (preventive/corrective/calibration), performed_by, description, performed_at, next_due, cost, status, findings |

---

## 5. Service Layer

### 5.1 RadiologyService

Core RIS business logic:

| Method | Description |
|--------|-------------|
| `create_order` | Create radiology order from referral/EHR |
| `schedule_exam` | Schedule exam slot with modality assignment |
| `arrive_patient` | Mark patient as arrived for exam |
| `start_exam` | Begin exam acquisition |
| `complete_exam` | Mark exam as completed with technique notes |
| `create_report_draft` | Create report draft from template |
| `submit_report` | Submit report for verification |
| `verify_report` | Radiologist sign-off on report |
| `add_addendum` | Add addendum to verified report |
| `flag_critical_finding` | Flag critical/urgent finding with notification |
| `get_exam_status` | Get current status of an exam workflow |
| `get_worklist` | Get worklist for modality/radiologist/department |
| `get_reading_queue` | Get unread exam queue for radiologist |

**Exam Workflow State Machine:**

```
Ordered ──→ Scheduled ──→ Arrived ──→ In Progress ──→ Completed
   │           │                                          │
   │           └→ Cancelled                               │
   └→ Cancelled                                     ↓
                                               Report Draft
                                                    │
                                                    ↓
                                              Preliminary
                                                    │
                                              ┌─────┴─────┐
                                              ↓            ↓
                                           Final      Addendum
```

### 5.2 PACSService

DICOM storage and archive management:

| Method | Description |
|--------|-------------|
| `store_dicom` | Store DICOM instance (C-STORE SCP) |
| `query_studies` | Query studies by patient/date/modality |
| `retrieve_study` | Retrieve complete study (C-GET/C-MOVE) |
| `retrieve_series` | Retrieve specific series |
| `retrieve_instance` | Retrieve single instance |
| `get_study_metadata` | Get DICOM metadata for study |
| `archive_study` | Move study from hot → warm tier |
| `deep_archive_study` | Move study from warm → cold tier |
| `restore_study` | Restore study from cold → warm tier |
| `delete_study` | Delete study (with audit trail) |
| `get_storage_usage` | Report storage usage by tier |
| `apply_archive_rules` | Evaluate and apply auto-archive rules |
| `get_dicom_statistics` | DICOM storage statistics |

**Three-Tier Storage:**

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Hot Tier  │────→│  Warm Tier  │────→│  Cold Tier  │
│ (0-90 days) │     │ (91-365 d)  │     │ (>365 days) │
│             │     │             │     │             │
│ Fast SSD    │     │ Standard    │     │ S3/Glacier  │
│ Storage     │     │ HDD/S3      │     │ Deep Archive│
│             │     │             │     │             │
│ <10ms       │     │ <100ms      │     │ >5min       │
│ retrieval   │     │ retrieval   │     │ retrieval   │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       └───────────────────┴───────────────────┘
                         │
                    ┌─────┴─────┐
                    │ Archive   │
                    │ Rules     │
                    │ Engine    │
                    └───────────┘
```

### 5.3 DeviceIntegrationService

DICOM modality integration:

| Method | Description |
|--------|-------------|
| `generate_mwl` | Generate Modality Worklist for scheduled exams |
| `query_mwl` | Handle MWL query from modality (DICOM C-FIND) |
| `mpps_in_progress` | Handle MPPS N-CREATE (exam started) |
| `mpps_completed` | Handle MPPS N-SET (exam completed) |
| `mpps_discontinued` | Handle MPPS N-SET (exam discontinued) |
| `store_result` | Handle DICOM C-STORE from modality |
| `register_modality` | Register new modality with AE title |
| `test_modality_connection` | Test DICOM connectivity with modality |
| `get_modality_status` | Get connectivity and status of modality |
| `broadcast_mwl` | Broadcast worklist update to subscribed modalities |

**DICOM Integration Flow:**

```
┌──────────┐    MWL Query     ┌──────────────┐
│ Modality │ ←────────────── │   NRISP      │
│ (CT/MRI) │                  │   MWL SCP    │
│          │ ──────────────→ │              │
│          │   MWL Response   │              │
└────┬─────┘                  └──────────────┘
     │                              │
     │  MPPS N-CREATE               │
     │  (Exam Started)              │
     │ ──────────────────────────→ │
     │                              │
     │  DICOM C-STORE               │
     │  (Images)                    │
     │ ──────────────────────────→ │
     │                              │
     │  MPPS N-SET                  │
     │  (Exam Completed)            │
     │ ──────────────────────────→ │
     │                              │
     ↓                              ↓
┌──────────┐                  ┌──────────┐
│ Modality │                  │  PACS    │
│ Complete │                  │ Stored   │
└──────────┘                  └──────────┘
```

### 5.4 AIService

AI imaging abstraction layer:

| Method | Description |
|--------|-------------|
| `register_model` | Register AI model in the model registry |
| `activate_model` | Activate model for inference |
| `deactivate_model` | Deactivate model |
| `run_inference` | Run inference on exam/series |
| `run_inference_batch` | Batch inference on queued exams |
| `get_triage_alerts` | Get active AI triage alerts |
| `acknowledge_triage` | Acknowledge triage alert |
| `resolve_triage` | Resolve triage alert |
| `get_model_performance` | Model performance metrics |
| `get_ai_dashboard` | AI service dashboard |

**AI Abstraction Layer:**

```
┌───────────────────────────────────────────────┐
│              NRISP AI Service                   │
│  ┌──────────────────────────────────────────┐  │
│  │          Model Registry                   │  │
│  │  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐ │  │
│  │  │ Model│  │ Model│  │ Model│  │ Model│ │  │
│  │  │ A    │  │ B    │  │ C    │  │ D    │ │  │
│  │  └──┬───┘  └──┬───┘  └──┬───┘  └──┬───┘ │  │
│  └──────┼────────┼────────┼────────┼──────┘  │
│         │        │        │        │         │
│  ┌──────┴────────┴────────┴────────┴──────┐  │
│  │        Inference Pipeline               │  │
│  │  Input: DICOM series                   │  │
│  │  Output: Structured findings (JSON)     │  │
│  └──────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────┐  │
│  │        Triage Engine                     │  │
│  │  Critical findings → Alert radiologist   │  │
│  └──────────────────────────────────────────┘  │
└───────────────────────────────────────────────┘
         │              │               │
         ↓              ↓               ↓
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Vendor A     │ │ Vendor B     │ │ Open-Source  │
│ API Gateway  │ │ API Gateway  │ │ Model (Local) │
└──────────────┘ └──────────────┘ └──────────────┘
```

### 5.5 ViewerService

Web-based image viewing:

| Method | Description |
|--------|-------------|
| `get_study_thumbnails` | Generate/retrieve study thumbnails |
| `get_series_images` | Stream series images to viewer |
| `convert_dicom_to_png` | Convert single DICOM frame to PNG |
| `get_dicom_tags` | Extract DICOM metadata tags for viewer |
| `get_window_level` | Apply window/level to image |
| `save_annotation` | Save viewer annotation |
| `get_measurement` | Save measurement from viewer |
| `get_viewer_config` | Get viewer configuration for user |

---

## 6. API Endpoints (55+)

### 6.1 Exam Workflow (9)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/radiology/exams` | List exams with filters |
| POST | `/radiology/exams` | Create exam order |
| GET | `/radiology/exams/{id}` | Get exam detail |
| PUT | `/radiology/exams/{id}` | Update exam |
| POST | `/radiology/exams/{id}/schedule` | Schedule exam |
| POST | `/radiology/exams/{id}/arrive` | Patient arrival |
| POST | `/radiology/exams/{id}/start` | Start exam |
| POST | `/radiology/exams/{id}/complete` | Complete exam |
| POST | `/radiology/exams/{id}/cancel` | Cancel exam |

### 6.2 Reporting (9)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/radiology/reports` | List reports |
| POST | `/radiology/reports` | Create report draft |
| GET | `/radiology/reports/{id}` | Get report detail |
| PUT | `/radiology/reports/{id}` | Update report |
| POST | `/radiology/reports/{id}/submit` | Submit for review |
| POST | `/radiology/reports/{id}/verify` | Radiologist verify |
| POST | `/radiology/reports/{id}/addendum` | Add addendum |
| GET | `/radiology/reports/templates` | List report templates |
| POST | `/radiology/reports/templates` | Create report template |

### 6.3 PACS/DICOM (11)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/radiology/pacs/store` | Store DICOM instances |
| GET | `/radiology/pacs/studies` | Query studies |
| GET | `/radiology/pacs/studies/{id}` | Get study detail |
| GET | `/radiology/pacs/studies/{id}/series` | Study series list |
| GET | `/radiology/pacs/series/{id}` | Series detail |
| GET | `/radiology/pacs/series/{id}/instances` | Series instances |
| GET | `/radiology/pacs/instances/{id}` | Instance detail |
| GET | `/radiology/pacs/instances/{id}/download` | Download DICOM file |
| POST | `/radiology/pacs/archive` | Archive study manually |
| POST | `/radiology/pacs/restore` | Restore from archive |
| GET | `/radiology/pacs/storage` | Storage usage by tier |

### 6.4 Device Integration (8)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/radiology/modalities` | List modalities |
| POST | `/radiology/modalities` | Register modality |
| GET | `/radiology/modalities/{id}` | Get modality detail |
| PUT | `/radiology/modalities/{id}` | Update modality |
| GET | `/radiology/modalities/{id}/status` | Modality connectivity |
| GET | `/radiology/modalities/{id}/worklist` | Modality worklist |
| POST | `/radiology/modalities/{id}/mpps` | MPPS notification |
| GET | `/radiology/devices` | List imaging devices |

### 6.5 AI Imaging (8)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/radiology/ai/models` | List AI models |
| POST | `/radiology/ai/models` | Register AI model |
| PUT | `/radiology/ai/models/{id}` | Update AI model |
| POST | `/radiology/ai/models/{id}/activate` | Activate model |
| POST | `/radiology/ai/models/{id}/deactivate` | Deactivate model |
| POST | `/radiology/ai/inference` | Run inference on exam |
| GET | `/radiology/ai/triage` | Get triage alerts |
| PUT | `/radiology/ai/triage/{id}/acknowledge` | Acknowledge triage |

### 6.6 Viewer (6)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/radiology/viewer/studies/{id}/thumbnails` | Study thumbnails |
| GET | `/radiology/viewer/studies/{id}/series` | Study series for viewer |
| GET | `/radiology/viewer/series/{id}/images` | Series image frames |
| GET | `/radiology/viewer/instances/{id}/png` | DICOM→PNG conversion |
| GET | `/radiology/viewer/instances/{id}/metadata` | DICOM tags for viewer |
| POST | `/radiology/viewer/annotations` | Save annotation |

### 6.7 Device Maintenance (4)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/radiology/devices/{id}/maintenance` | Maintenance history |
| POST | `/radiology/devices/{id}/maintenance` | Record maintenance |
| GET | `/radiology/devices/maintenance/due` | Maintenance due items |
| PUT | `/radiology/devices/{id}/maintenance/{mid}` | Update maintenance |

### 6.8 Configuration (3)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/radiology/config/tiers` | Storage tier config |
| POST | `/radiology/config/tiers` | Create storage tier |
| GET | `/radiology/config/archive-rules` | Archive rules |

---

## 7. DICOM Integration

### 7.1 DICOM Services Supported

| Service | Role | Standard |
|---------|------|----------|
| C-STORE SCP | Receive images from modalities | DICOM PS3.4 |
| C-STORE SCU | Send images to other PACS | DICOM PS3.4 |
| C-FIND SCP | Handle modality MWL queries | DICOM PS3.4 |
| C-FIND SCU | Query other PACS for studies | DICOM PS3.4 |
| C-MOVE SCU | Retrieve studies from other PACS | DICOM PS3.4 |
| C-GET SCP | Provide studies to querying systems | DICOM PS3.4 |
| N-CREATE SCU | MPPS exam started notification | DICOM PS3.4 |
| N-SET SCU | MPPS exam completed/update | DICOM PS3.4 |
| Modality Worklist | C-FIND-based MWL SCP | DICOM PS3.4 |
| Storage Commitment | C-store followed by commitment | DICOM PS3.4 |

### 7.2 Modality Worklist (MWL)

The MWL service provides scheduled exams to modalities via DICOM C-FIND:

- **MWL SCP**: NRISP acts as the worklist provider
- **Query Keys**: Patient ID, Accession Number, Scheduled Date, Modality, Station AE Title
- **Return Fields**: Patient demographics, scheduled procedure step, requested procedure, imaging location
- **Filtering**: Modality requests only exams scheduled for its station AE title
- **Update**: Worklist updated in real-time when exams are scheduled/cancelled

### 7.3 Modality Performed Procedure Step (MPPS)

MPPS provides real-time exam status updates from modalities:

- **N-CREATE**: Modality notifies NRISP that an exam has started
- **N-SET**: Modality notifies NRISP that an exam is completed or discontinued
- **Data**: Procedure step ID, start/end time, status, performer, notes
- **Response**: NRISP updates exam status, triggers PACS routing
- **Error Handling**: Timeout monitoring for exams started but not completed

---

## 8. PACS Architecture

### 8.1 Three-Tier Storage Model

| Tier | Storage Type | Retention | Retrieval | Cost/GB/Month |
|------|-------------|-----------|-----------|---------------|
| Hot (Tier 0) | NVMe SSD / local | 0-90 days | < 10ms | High |
| Warm (Tier 1) | Standard HDD / S3 | 91-365 days | < 100ms | Medium |
| Cold (Tier 2) | S3 Glacier / Deep Archive | > 365 days | > 5 min | Low |

### 8.2 Storage Strategy

| Data Type | Retention | Compression |
|-----------|-----------|-------------|
| Active studies (in reporting) | Hot tier | Lossless (original DICOM) |
| Recently completed (< 90d) | Hot tier | Lossless |
| Older studies (91-365d) | Warm tier | Lossless |
| Archived studies (> 365d) | Cold tier | Lossless (lossy for large series where acceptable) |
| Thumbnails | Hot tier (separate cache) | JPEG lossy |
| AI inputs/outputs | Hot tier (30 days) | Lossless |

### 8.3 Auto-Archive Rules

Rules are evaluated by a scheduled background job:

| Rule | Condition | Action |
|------|-----------|--------|
| Report verified archive | Report status = final | Move from hot → warm |
| Age-based cold archive | Study age > 365 days | Move from warm → cold |
| Modality-based retention | CT/MRI studies keep on hot for 14 days post-report | Conditional hot retention |
| Critical finding archive | Critical flagged studies stay on hot 30 days post-report | Extended hot retention |

### 8.4 Retrieval Workflow

```
User requests old study (cold tier)
       ↓
Restore request added to queue
       ↓
System initiates retrieval from Glacier
       ↓
Study restored to warm tier (estimated time displayed)
       ↓
Notification sent to user when ready
       ↓
User accesses study from warm tier
```

---

## 9. Image Viewer

### 9.1 Viewer Architecture

```
Web Browser (cornerstone.js / OHIF Viewer)
       │
       │ HTTP/HTTPS
       ↓
NRISP Viewer Service
       │
       ├── Thumbnail Generator (DICOM → JPEG thumbnail)
       ├── Image Converter (DICOM → PNG)
       ├── Streaming Engine (DICOM WADO-URI / WADO-RS)
       ├── Metadata Provider (DICOM tags JSON)
       └── Annotation Manager (save/load annotations)
```

### 9.2 Supported Features

- **Multi-frame viewing**: Scroll through image series
- **Window/Level**: Adjustable contrast and brightness
- **Zoom/Pan**: Image manipulation tools
- **Measurement**: Distance, angle, area, ROI tools
- **Annotations**: Text and graphic annotations (saved per user/protected health information-compliant)
- **Multi-series**: Side-by-side comparison of series
- **Concatenation**: View multiple studies/procedures together
- **Layout**: Configurable grid layouts (1×1, 2×2, 3×3)
- **DICOM→PNG**: Download individual frames as PNG
- **Keyboard shortcuts**: Configurable hotkeys for power users
- **RTL/Arabic**: RTL layout support in viewer UI

### 9.3 Streaming Protocol

- **Primary**: DICOM WADO-URI (HTTP GET with query parameters)
- **Secondary**: DICOM WADO-RS (RESTful DICOMweb)
- **Fallback**: Custom streaming over WebSocket for real-time viewing
- **Caching**: Browser-side caching of recently viewed frames
- **Prefetching**: Background prefetch of contiguous frames

---

## 10. AI Imaging Abstraction

### 10.1 Model Registry

NRISP maintains a vendor-independent AI model registry:

| Field | Description |
|-------|-------------|
| Name | Human-readable model name |
| Version | Semantic version |
| Vendor | Model provider |
| Type | triage / detection / quantification / quality |
| Modality | CT / MR / XR / US / MG / NM |
| Body Part | chest / brain / abdomen / musculoskeletal / etc. |
| Supported SOP Classes | DICOM SOP class UIDs this model accepts |
| Input Requirements | Image type, series requirements, preprocessing |
| Output Schema | Structured output definition (JSON Schema) |
| Endpoint URL | Where to send inference requests |
| Status | active / inactive / deprecated |
| Performance Metrics | accuracy, sensitivity, specificity, AUC |

### 10.2 AI Triage System

When an AI model detects a critical finding, the triage system:

1. Creates an `AITriage` record with finding type and severity
2. Adds the exam to the radiologist's priority reading queue
3. Sends notification to the radiologist (in-app + optional email/SMS)
4. Exam is visually flagged in the reading worklist
5. Radiologist acknowledges the alert when they begin review
6. Alert is resolved when the report is verified

### 10.3 Supported AI Use Cases

| Use Case | Modality | Model Type | Output |
|----------|----------|------------|--------|
| Pulmonary nodule detection | CT Chest | Detection | Nodule locations, sizes, characteristics |
| Stroke detection | CT Head / MRI Brain | Triage | ASPECTS score, hemorrhage detection |
| Fracture detection | XR | Detection | Fracture location, type |
| Breast cancer screening | MG | Triage | BI-RADS category, calcification detection |
| Image quality assessment | All modalities | Quality | Motion score, positioning adequacy |
| Dose estimation | CT | Quantification | Dose metrics (DLP, CTDIvol) |
| Automated measurements | Echo | Quantification | EF, chamber sizes, valve gradients |

---

## 11. Reuse Summary

| Component | Reused From | How |
|-----------|-------------|-----|
| Patient model | `models/patient.py` | FK in imaging orders, studies |
| LabUser model | `models/lab_user.py` | Radiologist, technologist identity |
| Organization models | `models/organization.py` | Department, facility references |
| AuditService | `services/audit_service.py` | All report and exam mutations logged |
| Auth/JWT | `security/auth.py` | API authentication |
| RBAC | `security/rbac.py` | Radiology roles (radiologist, tech, admin) |
| Database session | `database.py` | Shared SQLAlchemy engine |
| Encryption | `security/encryption.py` | PHI in DICOM metadata |
| Event bus | `core/events.py` | Publish exam/report events to EHR |
| Notification service | `notifications/` | Critical finding alerts, triage notifications |
| Storage abstraction | `shared/storage/` | File system and S3 storage for DICOM |

### 11.1 Existing Connectors Reused

| Connector | Source | Purpose |
|-----------|--------|---------|
| DICOM SCP | Shared DICOM library | Receive images from modalities |
| DICOM C-FIND | Shared DICOM library | Query modalities and other PACS |
| DICOM C-MOVE | Shared DICOM library | Retrieve studies from other PACS |
| FHIR client | `ehr_service.py` | Send FHIR imaging study resources to EHR |
| HL7 v2 (ORM^O01) | Device Bridge | Receive radiology orders from legacy HIS |
| HL7 v2 (ORU^R01) | Device Bridge | Send radiology reports to legacy HIS |

---

## 12. IHE Compliance

### 12.1 Supported IHE Profiles

| Profile | Domain | NRISP Role |
|---------|--------|------------|
| **Scheduled Workflow (SWF)** | RAD | Order Filler, Image Manager, Report Manager |
| **Patient Information Reconciliation (PIR)** | RAD | Patient ID cross-referencing, merge management |
| **Consistent Presentation of Images (CPI)** | RAD | Grayscale standard display function |
| **Portable Data for Imaging (PDI)** | RAD | Export to CD/DVD/USB with viewer |
| **Cross-enterprise Document Sharing for Imaging (XDS-I.b)** | ITI/RAD | Document source, consumer |
| **Audit Trail and Node Authentication (ATNA)** | ITI | Secure node, audit record repository |
| **Basic Patient Privacy Consents (BPPC)** | ITI | Consent management for imaging data |
| **Retrieve Form for Data Capture (RFD)** | ITI | Form-based data capture for structured reports |

### 12.2 SWF Actors

```
┌──────────────┐  Order Placed  ┌──────────────┐
│  Order       │ ────────────→ │  Order        │
│  Placer      │               │  Filler      │
│  (EHR/HIS)   │               │  (NRISP)      │
└──────────────┘               └──────┬───────┘
                                      │
                                      │ MWL Query
                                      ↓
                              ┌──────────────┐
                              │  Image       │
                              │  Manager     │
                              │  (NRISP)     │
                              └──────┬───────┘
                                      │
                          ┌───────────┴───────────┐
                          │                       │
                          ↓                       ↓
                  ┌──────────────┐       ┌──────────────┐
                  │  Modality    │       │  PACS        │
                  │  (CT/MRI)    │       │  Archive     │
                  └──────────────┘       └──────────────┘
                          │                       │
                          └───────────┬───────────┘
                                      │
                                      ↓
                              ┌──────────────┐
                              │  Reporting   │
                              │  Manager     │
                              │  (NRISP)     │
                              └──────┬───────┘
                                      │
                              ┌───────┴────────┐
                              │                │
                              ↓                ↓
                      ┌──────────────┐ ┌──────────────┐
                      │  Report      │ │  Report      │
                      │  Repository  │ │  Reader      │
                      └──────────────┘ └──────────────┘
```

---

## 13. Offline-First Design

- **Exam documentation**: Technicians can document exams offline (patient prep, contrast, technique notes), sync when online
- **Report creation**: Radiologists can draft reports offline for later sync
- **MWL caching**: Worklist is cached locally on modalities (standard DICOM MWL behavior)
- **DICOM store**: Modalities store images locally until PACS confirms storage (C-STORE with storage commitment)
- **Thumbnail cache**: Viewer thumbnails are cached for recently viewed studies
- **Critical finding flagging**: Available offline; sync and notification trigger when connectivity restored
- **Device registration**: Available offline; registered when online

---

## 14. RTL/Arabic-First

- All NRISP UI components designed for RTL layout as default
- Report templates available in Arabic (RSNA templates adapted for Arabic)
- Patient-facing material (prep instructions, consent forms) in Arabic
- Modality worklist displays patient names in Arabic script
- Viewer UI supports RTL layout (measurement labels, annotations)
- Search supports Arabic text normalization
- Date/time formats follow Iraqi conventions
- Report PDFs generated in Arabic with proper RTL rendering

---

## 15. FHIR Mappings

| NRISP Entity | FHIR Resource | Mapping Notes |
|-------------|---------------|---------------|
| ImagingOrder | `ServiceRequest` | code, subject, requester, reasonCode, specimen |
| ExamPerformed | `ImagingStudy` | uid, modality, bodySite, series, started, numberOfSeries |
| DICOMStudy | `ImagingStudy` | uid, identifier (accession), series list |
| DICOMSeries | `ImagingStudy.series` | uid, number, modality, bodySite, started |
| DICOMInstance | `ImagingStudy.series.instance` | uid, number, sopClass |
| RadiologyReport | `DiagnosticReport` | status, code, subject, issued, performer, resultsInterpreter, imagingStudy, conclusion |
| ReportTemplate | `DiagnosticReport` (extension) | Extension on DiagnosticReport for template metadata |
| ModalityWorklist | `Schedule` + `Slot` | Schedule and Slot for MWL timing |
| RadiologyDevice | `Device` | type, manufacturer, modelNumber, serialNumber |
| AIModel | `ActivityDefinition` | code, intent, participant, productCodeableConcept |

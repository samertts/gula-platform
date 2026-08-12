# National Hospital Desktop Workspace (NHDW) — Architecture

**Platform:** NHDW — National Hospital Desktop Workspace
**Mission:** 025
**Status:** Active Development
**Version:** 1.0.0

---

## 1. Overview

The National Hospital Desktop Workspace (NHDW) is a Windows-native desktop application providing unified hospital operations management for Iraqi healthcare facilities. It is the desktop complement to the existing web-based hospital module (`backend/app/hospital/`) and delivers real-time bed management, patient flow (admissions/discharges/transfers), clinical task management, departmental occupancy analytics, and multi-department communication.

NHDW is built with PySide6 (Qt for Python) and operates under an **offline-first** architecture — all core functions work without internet connectivity and synchronise automatically when the connection is restored. The application is **Arabic-first** with full RTL support at every UI layer.

### 1.1 Key Objectives

- Provide a single approved desktop application for all connected Iraqi hospitals
- Enable real-time bed management and patient flow across departments
- Deliver clinical task management with assignment and prioritization
- Support offline-first operation for hospitals with intermittent connectivity
- Integrate with the existing GULA hospital module without modifying it
- Provide KPI-driven analytics for hospital administration
- Serve as the desktop hub for multi-department communication and alerting

### 1.2 Scope

| Area | In Scope | Out of Scope |
|------|----------|--------------|
| Patient flow | Admissions, discharges, transfers, queue management | Patient registration (handled by web module) |
| Bed management | Real-time occupancy, department view, availability | Billing integration |
| Clinical tasks | Assignment, prioritization, status tracking | Clinical documentation (handled by Nursing Platform) |
| Communication | Department messaging, critical alerts | Voice/video calls |
| Analytics | KPI dashboards, occupancy trends, length-of-stay | Population health analytics |
| Offline | Full CRUD offline, delta sync | Real-time collaboration |

---

## 2. System Context

```
+------------------------------------------------------------------+
|                      NHDW Desktop Application                      |
|                          (PySide6/Qt)                              |
+------------------------------------------------------------------+
|                                                                     |
|  +-----------------+  +-----------------+  +---------------------+ |
|  |   Dashboard     |  |  Admissions     |  |  Clinical Tasks     | |
|  |   (KPI Cards,   |  |  (ADT Workflow,  |  |  (Assignment,      | |
|  |   Occupancy,    |  |   Bed Board,    |  |   Status, Priority) | |
|  |   Trends)       |  |   Queue)        |  |                     | |
|  +-----------------+  +-----------------+  +---------------------+ |
|                                                                     |
|  +-----------------+  +-----------------+  +---------------------+ |
|  |   Communication |  |   Reports       |  |   Settings/Admin    | |
|  |   (Messages,    |  |   (Export PDF,  |  |   (Theme, Lang,    | |
|  |   Alerts)       |  |   Excel, Charts)|  |   Sync Config)     | |
|  +-----------------+  +-----------------+  +---------------------+ |
+---------------------------+---------------------------------------+
                            |
+---------------------------+---------------------------------------+
|                      NHDW Service Layer (Desktop)                    |
|                                                                     |
|  +---------------------+  +---------------------+  +--------------+ |
|  |   Sync Engine       |  |   Offline DB         |  |   ApiClient  | |
|  |   (Delta Sync,      |  |   (Encrypted SQLite, |  |   (REST,     | |
|  |   Conflict Resolve) |  |   Full CRUD)         |  |   Auth, JWT) | |
|  +---------------------+  +---------------------+  +--------------+ |
+---------------------------+---------------------------------------+
                            |
+---------------------------+---------------------------------------+
|                      GULA Backend API                                |
|                                                                     |
|  +---------------------+  +---------------------+  +--------------+ |
|  |   /nhdw/*           |  |   /hospital/*       |  |   Auth/*     | |
|  |   (NHDW-specific    |  |   (Existing         |  |   (JWT,      | |
|  |    endpoints)       |  |    hospital module)  |  |    Refresh)  | |
|  +---------------------+  +---------------------+  +--------------+ |
+------------------------------------------------------------------+
|                                                                     |
|  +-------------------------------------------------------------+   |
|  |  PostgreSQL 16 (Hospital Module Tables + NHDW Extension)     |   |
|  |  Redis 7 (Cache, Session, Real-time Alerts)                  |   |
|  +-------------------------------------------------------------+   |
+------------------------------------------------------------------+
```

---

## 3. Module Structure

### 3.1 Desktop Application (`hospital_desktop/`)

```
hospital_desktop/
├── main.py                  # Application entry point, QApplication bootstrap
├── config.py                # AppConfig dataclass, JSON config persistence
├── l10n.py                  # TranslationManager, ArStrings (530+ Arabic strings)
├── theme.py                 # Theme system (dark/light), 730-line QSS theme
├── session.py               # SessionManager (login state, token persistence)
├── api_client.py            # ApiClient (requests-based, retry, JWT refresh)
├── offline.py               # OfflineDatabase (SQLite) + SyncEngine
├── run.py                   # CLI entry wrapper
├── requirements.txt         # PySide6, requests, cryptography, sqlalchemy, plyer
├── views/
│   ├── __init__.py
│   ├── dashboard.py          # KPI cards, occupancy gauge, trend charts
│   ├── admissions.py         # ADT workflow, bed board, queue
│   ├── clinical.py           # Clinical task assignment and tracking
│   ├── patients.py           # Patient search, profile, history
│   ├── queue.py              # Waiting list management
│   ├── communication.py      # Department messaging, critical alerts
│   ├── reports.py            # PDF/Excel export, charts
│   ├── resources.py          # Equipment, rooms, departments
│   └── settings.py           # Theme, language, sync configuration
├── widgets/
│   ├── __init__.py
│   ├── charts.py             # KpiCard, MiniChart, OccupancyGauge, TrendChart
│   ├── dialogs.py            # LoginDialog, AlertDialog, ConfirmDialog
│   ├── navbar.py             # Navigation sidebar (RTL-aware)
│   └── statusbar.py          # Connection status, sync indicator
└── windows/
    ├── __init__.py
    └── main_window.py        # MainWindow (QMainWindow with dock system)
```

### 3.2 Backend API Module (`backend/app/`)

The existing hospital module (`backend/app/hospital/`) provides the foundation:

```
backend/app/hospital/
├── __init__.py
├── base.py                  # DeclarativeBase for hospital models
└── models/
    ├── __init__.py           # Exports all 13 models
    └── ...                   # 13 ORM models (see §4)
```

New NHDW-specific endpoints are added under the `/nhdw/` prefix (see §6), extending the hospital module without modifying existing code.

---

## 4. Core Entities

The hospital module defines **13 core models** in `backend/app/hospital/models/`. NHDW adds **2 additional models** for a total of 15.

### 4.1 Existing Hospital Models (13)

| Entity | Table | Purpose | Key Fields |
|--------|-------|---------|------------|
| `HospitalMaster` | `hospitals` | Top-level hospital record | code, name, name_ar, hospital_type, license_number |
| `Campus` | `hospital_campuses` | Physical campus within a hospital | hospital_id, name, address, phone |
| `Building` | `hospital_buildings` | Building within a campus | campus_id, name, floors |
| `Floor` | `hospital_floors` | Floor within a building | building_id, name, floor_number |
| `Unit` | `hospital_units` | Clinical unit/department sub-division | floor_id, name, specialty |
| `Department` | `hospital_departments` | Clinical department | hospital_id, code, name_ar, department_type |
| `Clinic` | `hospital_clinics` | Outpatient clinic | name_ar, specialty |
| `Room` | `hospital_rooms` | Patient room | department_id, room_number, room_type |
| `Bed` | `hospital_beds` | Individual bed | room_id, bed_label, bed_type, status |
| `BedAssignment` | `bed_assignments` | Patient-bed assignment | bed_id, patient_id, assigned_at, discharge_at |
| `OperationTheater` | `operation_theaters` | Surgical operating room | department_id, name, status |
| `MedicalEquipment` | `medical_equipment` | Tracked medical devices | department_id, name, serial, calibration_date |
| `CostCenter` | `cost_centers` | Financial cost center | hospital_id, code, name, budget |

### 4.2 NHDW-Added Models (2)

| Entity | Table | Purpose | Key Fields |
|--------|-------|---------|------------|
| `ClinicalTask` | `clinical_tasks` | Assignable clinical tasks | patient_id, department_id, task_type, description, assignee_id, priority, status, due_date |
| `DepartmentAlert` | `department_alerts` | Department-level critical alerts | department_id, alert_type, severity, title, message, patient_id, acknowledged_by, resolved_at |

### 4.3 Entity Relationships

```
HospitalMaster (1) ──< Campus (1) ──< Building (1) ──< Floor (1) ──< Unit
       │                                    │
       ├──< Department (1) ──< Room (1) ──< Bed (1) ──< BedAssignment
       │         │
       │         ├──< Clinic
       │         ├──< OperationTheater
       │         ├──< MedicalEquipment
       │         └──< CostCenter
       │
       ├──< ClinicalTask
       └──< DepartmentAlert
```

---

## 5. Service Layer

### 5.1 NHDWService

The `NHDWService` class encapsulates all NHDW-specific business logic. It handles:
- Patient admission workflow (search, admit, assign bed, notify)
- Discharge planning and execution
- Inter-department transfers
- Clinical task CRUD with assignment validation
- Bed availability and occupancy calculations
- Department alert creation and acknowledgment

### 5.2 KPI Engine

The KPI Engine is a separate module (`backend/app/services/kpi_engine.py`) that computes:

| KPI | Formula | Refresh |
|-----|---------|---------|
| Bed occupancy rate | occupied / total beds × 100 | Real-time |
| Average length of stay | SUM(length_of_stay) / discharges | Daily |
| Admission rate | admissions / period | Hourly |
| Discharge rate | discharges / period | Hourly |
| Transfer rate | transfers / period | Daily |
| ED waiting time | AVG(arrival_to_bed) | Real-time |
| Readmission rate (30d) | readmissions / discharges × 100 | Daily |
| Bed turnaround time | AVG(discharge_to_clean) | Daily |
| Department capacity | current_occupancy / capacity × 100 | Real-time |
| Task completion rate | completed / total tasks × 100 | Real-time |

The engine exposes a `get_kpi_dashboard(lab_id, department_id, period)` method that returns structured KPI data consumable by the desktop dashboard.

### 5.3 OfflineService

The `OfflineService` (implemented in `hospital_desktop/offline.py`) manages:
- Local SQLite database with 9 tables mirroring a subset of backend data
- Full CRUD operations on all local entities
- Change tracking via `sync_log` table (action + entity_id + data + status)
- Delta sync (pull changes since last sync timestamp)
- Push changes (outbox-pattern: upsert/delete to backend, mark synced)
- Conflict resolution (last-writer-wins based on `updated_at` timestamps)
- Background periodic sync with configurable interval

### 5.4 Desktop Service Classes

| Class | File | Responsibility |
|-------|------|----------------|
| `ApiClient` | `api_client.py` | HTTP client with retry, JWT auth, token refresh, singleton |
| `OfflineDatabase` | `offline.py` | SQLite wrapper with thread-safe CRUD, change logging |
| `SyncEngine` | `offline.py` | Bidirectional sync: pull, push, conflict resolution |
| `SessionManager` | `session.py` | Login state, token persistence, session restore |
| `ThemeManager` | `theme.py` | Dark/light theme application, QSS injection |
| `TranslationManager` | `l10n.py` | Runtime locale switching (ar/en), 530+ string keys |
| `AppConfig` | `config.py` | Persistent user configuration (JSON file) |

---

## 6. API Endpoints

NHDW adds **52 endpoints** under the `/nhdw/` prefix:

### 6.1 Dashboard & KPIs

| Method | Path | Description |
|--------|------|-------------|
| GET | `/nhdw/dashboard/kpi` | KPI dashboard data (occupancy, admissions, discharges) |
| GET | `/nhdw/dashboard/occupancy` | Department-level bed occupancy |
| GET | `/nhdw/dashboard/trends` | Trend data for selected KPI over period |
| GET | `/nhdw/dashboard/alerts` | Active department alerts summary |

### 6.2 Patient Flow (ADT)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/nhdw/admissions` | List admissions with filters |
| POST | `/nhdw/admissions` | Create new admission (with bed assignment) |
| GET | `/nhdw/admissions/{id}` | Get admission detail |
| PUT | `/nhdw/admissions/{id}` | Update admission |
| POST | `/nhdw/admissions/{id}/discharge` | Discharge patient |
| POST | `/nhdw/admissions/{id}/transfer` | Transfer to another department |
| GET | `/nhdw/admissions/stats` | Admission statistics |

### 6.3 Bed Management

| Method | Path | Description |
|--------|------|-------------|
| GET | `/nhdw/beds` | List beds with filters (department, status) |
| GET | `/nhdw/beds/{id}` | Get bed detail |
| PUT | `/nhdw/beds/{id}` | Update bed status |
| GET | `/nhdw/beds/available` | Available beds by department |
| GET | `/nhdw/beds/occupancy` | Occupancy report |
| POST | `/nhdw/beds/{id}/assign` | Assign patient to bed |
| POST | `/nhdw/beds/{id}/release` | Release bed |

### 6.4 Departments & Queue

| Method | Path | Description |
|--------|------|-------------|
| GET | `/nhdw/departments` | List departments |
| GET | `/nhdw/departments/{id}` | Department detail with occupancy |
| GET | `/nhdw/departments/{id}/queue` | Department waiting queue |
| POST | `/nhdw/queue` | Add patient to queue |
| PUT | `/nhdw/queue/{id}` | Update queue entry |
| DELETE | `/nhdw/queue/{id}` | Remove from queue |
| GET | `/nhdw/waiting-list` | Hospital-wide waiting list |

### 6.5 Clinical Tasks

| Method | Path | Description |
|--------|------|-------------|
| GET | `/nhdw/tasks` | List clinical tasks |
| POST | `/nhdw/tasks` | Create clinical task |
| GET | `/nhdw/tasks/{id}` | Get task detail |
| PUT | `/nhdw/tasks/{id}` | Update task |
| DELETE | `/nhdw/tasks/{id}` | Delete task |
| POST | `/nhdw/tasks/{id}/assign` | Assign task to user |
| POST | `/nhdw/tasks/{id}/complete` | Mark task complete |
| GET | `/nhdw/tasks/my` | Current user's assigned tasks |
| GET | `/nhdw/tasks/stats` | Task completion statistics |

### 6.6 Communication

| Method | Path | Description |
|--------|------|-------------|
| GET | `/nhdw/messages` | List messages (sent/received) |
| POST | `/nhdw/messages` | Send message |
| GET | `/nhdw/messages/{id}` | Get message detail |
| PUT | `/nhdw/messages/{id}/read` | Mark message as read |
| DELETE | `/nhdw/messages/{id}` | Delete message |
| GET | `/nhdw/alerts` | List alerts |
| POST | `/nhdw/alerts` | Create alert |
| PUT | `/nhdw/alerts/{id}/acknowledge` | Acknowledge alert |
| PUT | `/nhdw/alerts/{id}/resolve` | Resolve alert |

### 6.7 Reports

| Method | Path | Description |
|--------|------|-------------|
| GET | `/nhdw/reports/occupancy` | Occupancy report (PDF/JSON) |
| GET | `/nhdw/reports/admissions` | Admissions report |
| GET | `/nhdw/reports/discharges` | Discharges report |
| GET | `/nhdw/reports/tasks` | Clinical tasks report |
| GET | `/nhdw/reports/department` | Department activity report |
| GET | `/nhdw/reports/export` | Export to PDF/Excel |

### 6.8 Sync

| Method | Path | Description |
|--------|------|-------------|
| GET | `/nhdw/sync/status` | Sync status for a lab |
| GET | `/nhdw/sync/changes` | Get changes since timestamp (entity_type, since) |
| POST | `/nhdw/sync/push` | Push local changes to server |
| GET | `/nhdw/sync/full` | Trigger full data pull |

### 6.9 Configuration

| Method | Path | Description |
|--------|------|-------------|
| GET | `/nhdw/config` | Get NHDW configuration |
| PUT | `/nhdw/config` | Update NHDW configuration |
| GET | `/nhdw/config/features` | Feature flags |
| GET | `/nhdw/health` | NHDW module health |

---

## 7. Integration with Existing Hospital Module

NHDW is designed as an **extension** of the existing `hospital/` module. The integration follows these principles:

### 7.1 Non-Modification Principle

NHDW **never modifies** existing hospital module code. Instead:

- **New endpoints** are added under `/nhdw/` prefix (not modifying `/hospital/` routes)
- **New models** use `NHDWBase` (a separate declarative base) with foreign keys to existing hospital tables
- **New services** import and compose existing `HospitalService` methods rather than duplicating them

### 7.2 Data Sharing

| Existing Table | NHDW Usage |
|----------------|------------|
| `hospitals` | Read: used for context/scope (lab_id scoping) |
| `hospital_departments` | Read: shown in department views, queue management |
| `hospital_beds` | Read + Update status: bed management UI writes status changes via NHDW endpoints |
| `hospital_bed_assignments` | Read + Create: ADT workflow creates assignments |
| `hospital_rooms` | Read: displayed in bed board |
| `patients` | Read: patient search, profile display |
| `lab_users` | Read: staff directory, task assignment |

### 7.3 Extension Points

NHDW adds value without modifying existing code through:
1. **View layer only** — The desktop reads existing hospital data and presents it in a unified UI
2. **New processes** — Clinical tasks, department alerts, and KPI analytics are genuinely new additions
3. **Status updates** — Bed status changes flow through NHDW endpoints, which also write to audit log

---

## 8. Reuse Summary

| Component | Reused From | How |
|-----------|-------------|-----|
| Hospital models (13) | `hospital/models/` | Imported directly in NHDW service layer |
| `HospitalService` | `services/hospital_service.py` | Composed into NHDWService for hospital CRUD |
| `AuditService` | `services/audit_service.py` | Shared audit logging for all NHDW mutations |
| Authentication | `security/auth.py` | ApiClient uses JWT tokens from existing auth system |
| RBAC | `security/rbac.py` | Endpoint-level permission checks reuse existing roles |
| Database | `database.py` | Shared SQLAlchemy engine and session |
| Patient model | `models/patient.py` | Patient search and profile display |
| LabUser model | `models/lab_user.py` | Staff directory and task assignment |
| Encryption | `security/encryption.py` | Local SQLite encryption uses same crypto primitives |
| Logging | `core/logging_config.py` | Structured JSON logging pattern |

---

## 9. Desktop Application Architecture

### 9.1 PySide6 (Qt for Python)

NHDW uses **PySide6** as its desktop UI framework. The decision is documented in ADR-001.

**Application Bootstrap** (`main.py`):
1. `load_config()` — loads persisted `AppConfig` from `~/.config/NHDW/config.json`
2. `QApplication` creation with application name, org, version
3. Splash screen display during initialization
4. `QLockFile` — single-instance enforcement
5. `ThemeManager.apply_theme()` — applies dark/light QSS theme
6. RTL/LTR layout direction based on `config.language`
7. `SessionManager.load_session()` — restores previous authenticated session
8. `LoginDialog` — if no valid session, show login form
9. `MainWindow` — primary window with dockable panels

### 9.2 Window Architecture

```
MainWindow (QMainWindow)
├── NavBar (QWidget, left sidebar)
│   ├── Dashboard button
│   ├── Admissions button
│   ├── Clinical Tasks button
│   ├── Communication button
│   ├── Reports button
│   └── Settings button
├── Central stacked widget (QStackedWidget)
│   ├── DashboardView
│   ├── AdmissionView
│   ├── ClinicalTasksView
│   ├── CommunicationView
│   ├── ReportsView
│   └── SettingsView
├── StatusBar (QStatusBar)
│   ├── Connection indicator
│   ├── Sync status widget
│   ├── Last sync time
│   └── User info
└── System tray icon (QSystemTrayIcon)
    ├── Minimize to tray
    ├── Background notifications
    └── Quick actions menu
```

### 9.3 Threading Model

| Thread | Purpose |
|--------|---------|
| Main thread | Qt event loop, UI rendering |
| Background sync | `SyncEngine` runs on `QTimer`-triggered calls in main thread (non-blocking HTTP) |
| Offline DB | SQLite operations use `threading.Lock` for thread safety |

The `ApiClient` uses `requests` (synchronous) — all HTTP calls are fast enough that they do not block the UI perceptibly. For future bulk operations, a `QThread`-based worker pool is planned.

### 9.4 Theme System

The `ThemeManager` applies a comprehensive QSS stylesheet (730+ lines) with:
- **Dark theme** — GitHub-dark inspired palette (`#0d1117` background, `#161b22` surface)
- **Light theme** — Clean clinical interface
- **RTL-aware** — Padding/margin inversion for Arabic UI
- **Color system** — 100+ color tokens organized by role (background, surface, text, border, input, chart, KPI, badge, progress, scrollbar)

---

## 10. Security Model

| Concern | Implementation |
|---------|---------------|
| Authentication | JWT-based via `ApiClient.login()` — username/password → access + refresh tokens |
| Token refresh | Automatic silent refresh on 401 responses |
| Session persistence | Encrypted session file in `~/.config/NHDW/session.json` |
| Single instance | `QLockFile` prevents multiple instances |
| TLS | All API calls use HTTPS in production |
| RBAC | Backend enforces role-based permissions; desktop shows/hides UI elements accordingly |
| Local data | SQLite database is not encrypted by default (planned: SQLCipher integration) |
| Audit log | All mutations on backend are logged through `AuditService` |
| Input validation | Pydantic models validate all data at API boundary |

---

## 11. Offline-First Design

### 11.1 Architecture

```
Online Mode:
Desktop UI ←→ ApiClient ←→ Backend API ←→ PostgreSQL

Offline Mode:
Desktop UI ←→ OfflineDatabase (SQLite) ←→ SyncEngine (pending changes queue)

Transition:
SyncEngine detects connectivity → delta_sync() / push_changes()
```

### 11.2 Local SQLite Schema

9 tables are mirrored locally (see `offline.py:LOCAL_SCHEMA`):
- `patients`, `admissions`, `visits`, `clinical_tasks`, `messages`, `alerts`
- `sync_log` (change tracking), `metadata` (key-value store), `department_occupancy`

### 11.3 Sync Strategy

| Aspect | Approach |
|--------|----------|
| Pull | Full sync on first connect, delta sync (`/changes?since=`) thereafter |
| Push | Outbox pattern: all local changes logged to `sync_log` table, pushed in order |
| Conflict | Last-writer-wins by `updated_at` timestamp comparison |
| Frequency | Configurable interval (default 60s) via `auto_sync_interval` config |
| Background | `SyncEngine.start_background_sync()` runs periodic delta sync |

---

## 12. RTL/Arabic-First Design Decisions

### 12.1 UI Layer

- Application layout direction set at startup based on `config.language`
- All UI strings stored in `ArStrings` class (530+ entries)
- `TranslationManager` handles runtime locale switching
- QSS theme includes directional overrides for RTL padding/margins
- Department names, room labels, and clinical terms use Arabic text natively

### 12.2 Data Layer

- Models include `name_ar` fields alongside English equivalents
- Audit logs record Arabic user-facing messages
- Reports generate in Arabic (PDF with RTL text rendering)

### 12.3 Desktop Specifics

- Qt layout direction set to `RightToLeft` for Arabic mode
- Navigation sidebar positioned on the right in RTL mode
- Text alignment defaults to right-justified
- Date formats follow Iraqi convention (DD/MM/YYYY)
- Numeric formats use Arabic-Indic digits where appropriate

---

## 13. FHIR Mappings

NHDW data maps to FHIR R4 resources for interoperability:

| NHDW Entity | FHIR Resource | Mapping Notes |
|-------------|---------------|---------------|
| Patient | `Patient` | Identifier (MRN), name, gender, birthDate, telecom |
| Admission | `Encounter` | class, period, diagnosis, hospitalization.destination |
| Discharge | `Encounter` (status=finished) | period.end, hospitalization.dischargeDisposition |
| Transfer | `Encounter` (status=in-progress) | location changed, period |
| Bed | `Location` | physicalType="bd", mode="instance" |
| BedAssignment | `Encounter.location` | location reference with period |
| Department | `Location` | physicalType="dept", mode="instance" |
| ClinicalTask | `Task` | code, status, intent, requester, owner, description |
| Alert | `Communication` | category="alert", payload, sender, recipient |
| Provider | `Practitioner` + `PractitionerRole` | name, identifier, role, specialty |

---

## 14. Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Desktop UI | PySide6 (Qt for Python) | >= 6.6.0 |
| HTTP Client | requests + urllib3 | >= 2.31.0 |
| Local Database | SQLite (via sqlite3 stdlib) | Built-in |
| ORM (local) | SQLAlchemy | >= 2.0.0 |
| Encryption | cryptography | >= 41.0.0 |
| Desktop Notifications | plyer | >= 2.1.0 |
| Backend Framework | FastAPI | via GULA stack |
| Backend DB | PostgreSQL 16 | via GULA stack |
| Env Configuration | python-dotenv | >= 1.0.0 |
| Packaging | PyInstaller | For Windows distribution |
| Installer | NSIS / Inno Setup | For Windows installer |

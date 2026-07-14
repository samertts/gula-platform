# GULA Platform — Sequence Diagrams

**Contract Tag:** `integration-contracts-v1.0` | **Date:** 2026-07-14

---

## 1. Order Creation → Validation → Results Flow

```mermaid
sequenceDiagram
    participant DR as Doctor
    participant REC as Receptionist
    participant API as GULA API
    participant SVC as Order Service
    participant PAT as Patient Service
    participant DB as PostgreSQL
    participant AUD as Audit Log
    participant OUT as Outbox
    participant TECH as Technician
    participant PATH as Pathologist

    DR->>API: Refer patient with tests
    REC->>API: POST /patients
    API->>PAT: Create/find patient
    PAT->>DB: INSERT patients
    DB-->>PAT: Patient record
    PAT-->>API: Patient ID

    REC->>API: POST /orders {patient_id, results}
    API->>SVC: Create order
    SVC->>PAT: Verify patient exists
    SVC->>DB: INSERT lab_orders
    SVC->>DB: INSERT lab_results (pending)
    SVC->>DB: INSERT outbox_events (lims.order.accessioned)
    SVC->>DB: INSERT audit_log
    DB-->>SVC: Success
    SVC-->>API: Order {id, status: pending}
    API-->>REC: 201 Created

    REC->>API: POST /samples {order_id, sample_type}
    API->>SVC: Register specimen
    SVC->>DB: INSERT samples
    SVC->>DB: INSERT outbox_events (lims.specimen.registered)
    SVC->>DB: INSERT audit_log
    DB-->>SVC: Barcode
    SVC-->>API: Sample {barcode}
    API-->>REC: Barcode label

    TECH->>API: PATCH /samples/{barcode} {status: collected}
    API->>SVC: Collect specimen
    SVC->>DB: UPDATE samples
    SVC->>DB: INSERT outbox_events (lims.specimen.collected)
    DB-->>SVC: Updated
    SVC-->>API: Success

    TECH->>API: POST /results {order_id, values}
    API->>SVC: Enter results
    SVC->>DB: UPDATE lab_results (completed)
    SVC->>SVC: Auto-validation rules
    SVC->>SVC: Delta check against history
    SVC->>SVC: Critical value check
    SVC->>DB: INSERT outbox_events (lims.result.created, lims.result.auto_validated)
    SVC->>DB: INSERT audit_log

    alt Critical Value
        SVC->>OUT: lims.result.critical event
        OUT->>API: Notify ordering physician
    end

    DB-->>SVC: Results saved
    SVC-->>API: Results {status: completed}
    API-->>TECH: 200 OK

    PATH->>API: POST /results/{id}/validate
    API->>SVC: Validate results
    SVC->>DB: UPDATE lab_results (verified)
    SVC->>DB: UPDATE lab_orders (validated)
    SVC->>DB: INSERT outbox_events (lims.order.validated)
    SVC->>DB: INSERT audit_log
    DB-->>SVC: Updated
    SVC-->>API: Validated
    API-->>PATH: 200 OK

    PATH->>API: POST /orders/{id}/release
    API->>SVC: Release results
    SVC->>DB: UPDATE lab_orders (released)
    SVC->>DB: INSERT outbox_events (lims.order.released)
    DB-->>SVC: Released
    SVC-->>API: Released
    API-->>PATH: Report URL
```

## 2. FHIR Resource Retrieval

```mermaid
sequenceDiagram
    participant CON as Consumer
    participant GW as API Gateway
    participant AUTH as Auth
    participant FHIR as FHIR Mapper
    participant SVC as Service Layer
    participant DB as PostgreSQL

    CON->>GW: GET /compliance/fhir/Patient/C-12345
    GW->>AUTH: Validate JWT
    AUTH-->>GW: user={lab_id, role}

    GW->>FHIR: get_fhir_patient(C-12345, lab_id)
    FHIR->>SVC: Fetch citizen domain model
    SVC->>DB: SELECT citizens WHERE fhir_id = 'C-12345'
    DB-->>SVC: Citizen row

    SVC->>DB: SELECT patients WHERE citizen_id = ? AND lab_id = ?
    DB-->>SVC: Patient row

    SVC-->>FHIR: Domain models
    FHIR->>FHIR: Apply GULAPatientProfile mapping rules
    Note over FHIR: citizen.health_number → Patient.identifier[0]<br/>citizen.national_id_hash → Patient.identifier[1] (truncated)<br/>citizen.first_name+father_name+last_name → Patient.name<br/>citizen.gender → Patient.gender<br/>patient.lab_id → Patient.managingOrganization

    FHIR-->>GW: FHIR Patient resource
    GW-->>CON: 200 + application/fhir+json
```

## 3. HL7 Message Ingestion

```mermaid
sequenceDiagram
    participant INST as Instrument
    participant API as GULA API
    participant HL7P as HL7 Parser
    participant MATCH as Order Matcher
    participant SVC as Result Service
    participant DB as PostgreSQL
    participant OUT as Outbox

    INST->>API: POST /lims/integration/hl7/receive<br/>{instrument_id, raw_message}
    API->>HL7P: Parse HL7 message
    HL7P->>HL7P: Split on \r\n
    HL7P->>HL7P: Extract MSH header
    HL7P->>HL7P: Extract PID-3 patient_id
    HL7P->>HL7P: Extract SPM-2 specimen_id
    HL7P->>HL7P: Extract OBR-3 result_id
    HL7P->>HL7P: Extract OBX fields (code, value, unit, ref_range, flag)
    HL7P-->>API: List[HL7Result]

    API->>MATCH: Match results to orders
    MATCH->>DB: Find order by specimen barcode
    DB-->>MATCH: Order found or null

    alt New Results
        MATCH-->>API: Matched to order
        API->>SVC: Create/update results
        SVC->>DB: INSERT lab_results
        SVC->>DB: INSERT outbox_events (lims.result.created)
        SVC->>SVC: Auto-validation
        SVC->>SVC: Critical checker

        alt Critical
            SVC->>OUT: lims.result.critical
        end

        SVC-->>API: Saved
        API->>HL7P: Build ACK (AA)
    else No Match
        API->>HL7P: Build ACK (AR)
    end

    HL7P-->>API: MSH|...\rMSA|AA|MSGID
    API-->>INST: 200 + HL7 ACK
```

## 4. ASTM Instrument Communication

```mermaid
sequenceDiagram
    participant INST as Instrument
    participant BUF as ASTMBuffer
    participant FP as Frame Processor
    participant PARSER as ASTM Parser
    participant MB as Message Builder
    participant ADAPT as Adapter
    participant TME as Test Mapping Engine
    participant NORM as Normalizer
    participant API as GULA API
    participant DB as PostgreSQL

    Note over INST,API: Serial/TCP Connection Established
    INST->>BUF: Raw bytes (serial/TCP stream)
    BUF->>BUF: Accumulate bytes
    BUF->>FP: STX (0x02) detected

    FP->>FP: Read until ETX (0x03)
    FP->>FP: Extract checksum (2 hex chars)
    FP->>FP: validate_checksum()

    alt Checksum OK
        FP->>PARSER: Decoded payload
        PARSER->>PARSER: Split on CR
        PARSER->>PARSER: Parse H frame (header)
        PARSER->>PARSER: Parse P frame (patient/specimen)
        PARSER->>PARSER: Parse O frame (order/test code)
        PARSER->>PARSER: Parse R frame (result value)
        PARSER->>PARSER: Parse L frame (terminator)
        PARSER->>MB: List[ASTMRecord]

        MB->>ADAPT: Resolve vendor adapter
        ADAPT->>ADAPT: Apply vendor transforms (e.g., HGB→HB)
        ADAPT->>TME: Transformed records
        TME->>TME: Map to canonical test codes
        TME->>NORM: Canonical records
        NORM->>NORM: Create NormalizedResult

        NORM->>API: Forward to GULA backend

        API->>DB: Save results
        API-->>NORM: 200 OK
        NORM-->>BUF: ACK (0x06)
        BUF-->>INST: ACK byte

    else Checksum Fail
        FP-->>BUF: ParserError
        BUF-->>INST: NAK (0x15) → Retransmit
    end
```

## 5. Citizen Consent Flow

```mermaid
sequenceDiagram
    participant CIT as Citizen
    participant PORT as Portal
    participant API as GULA API
    participant CONS as Consent Service
    participant DB as PostgreSQL
    participant AUD as Audit Log
    participant DOC as Doctor

    CIT->>PORT: Log in to citizen portal
    PORT->>API: GET /test-results/citizen/{health_id}
    API-->>PORT: Results list

    DOC->>API: GET /patients/{id}/results
    API->>CONS: check_consent(gpid, grantee_id, scope)
    CONS->>DB: Query consent_registry
    DB-->>CONS: No active consent
    CONS-->>API: allowed=false
    API-->>DOC: 403 Consent Not Granted

    DOC->>CIT: Request data access
    CIT->>PORT: POST /consent/grant
    Note over CIT,PORT: {gpid, grantee_id, scope, expires_in_hours}

    PORT->>API: POST /consent/grant
    API->>CONS: grant_consent()
    CONS->>DB: INSERT consent_registry
    CONS->>DB: INSERT audit_log
    DB-->>CONS: consent_id
    CONS-->>API: {consent_id, expires_at}
    API-->>PORT: Granted

    DOC->>API: GET /patients/{id}/results (retry)
    API->>CONS: check_consent()
    CONS->>DB: Query active consent
    DB-->>CONS: Active
    CONS-->>API: allowed=true
    API-->>DOC: Patient results

    CIT->>PORT: POST /consent/revoke
    Note over CIT,PORT: {gpid, grantee_id, scope}

    API->>CONS: revoke_consent()
    CONS->>DB: Soft-delete consent
    CONS->>DB: INSERT audit_log
    DB-->>CONS: Revoked
    API-->>PORT: {revoked: true}
```

## 6. Patient Merge Flow

```mermaid
sequenceDiagram
    participant OP as Operator
    participant API as GULA API
    participant MPI as MPI Service
    participant MATCH as Matcher
    participant DB as PostgreSQL
    participant AUD as Audit Log
    participant OUT as Outbox

    OP->>API: GET /patients/search?q=محمد
    API->>MPI: Search patients
    MPI->>DB: Full-text search
    DB-->>MPI: Multiple matches, possible duplicates

    MPI->>MATCH: Score duplicate candidates
    MATCH->>MATCH: Name similarity (edit distance)
    MATCH->>MATCH: Phone match
    MATCH->>MATCH: National ID match
    MATCH->>MATCH: DOB match
    MATCH-->>MPI: Duplicate with confidence 0.92

    OP->>API: POST /patients/{id}/merge
    Note over OP,API: {target_id: 100, source_id: 101, confidence: 0.92}

    API->>MPI: propose_merge(100, 101)
    MPI->>DB: BEGIN transaction
    MPI->>DB: INSERT merge_proposals (pending)
    DB-->>MPI: proposal_id

    alt Auto-merge (confidence > 0.95)
        MPI->>DB: UPDATE patients SET merged_to=100 WHERE id=101
        MPI->>DB: UPDATE lab_orders SET patient_id=100 WHERE patient_id=101
        MPI->>DB: UPDATE lab_results SET patient_id=100 WHERE patient_id=101
        MPI->>DB: UPDATE samples SET patient_id=100 WHERE patient_id=101
        MPI->>DB: INSERT outbox_events (identity.citizen.merged)
    else Pending Review (confidence 0.80-0.95)
        DB-->>MPI: proposal pending
        MPI-->>API: {status: pending_review, proposal_id}
    end

    MPI->>DB: INSERT audit_log
    DB-->>MPI: COMMIT
    MPI-->>API: Merge result
    API-->>OP: Merged successfully
```

## 7. Outbox Event Delivery

```mermaid
sequenceDiagram
    participant SVC as Service
    participant TX as DB Transaction
    participant BUS as Business Table
    participant OUT as outbox_events
    participant WKR as Outbox Worker
    participant PUB as Publisher
    participant WEB as Webhook
    participant EXT as External System

    SVC->>TX: BEGIN
    SVC->>BUS: INSERT/UPDATE business data
    SVC->>OUT: INSERT event (status=pending)
    TX->>TX: COMMIT (atomic)

    loop Every 10 seconds
        WKR->>OUT: SELECT * WHERE status=pending<br/>ORDER BY created_at LIMIT 50<br/>FOR UPDATE SKIP LOCKED
        OUT-->>WKR: Batch of events

        alt No events
            WKR->>WKR: Sleep 10s
        end

        loop Each event (max 5 attempts)
            WKR->>PUB: publish(event)

            PUB->>WEB: POST to webhook URL
            Note over PUB,WEB: X-GULA-Event, X-GULA-Delivery, X-GULA-Signature

            alt Success (2xx)
                WEB-->>PUB: 200 OK
                PUB->>OUT: UPDATE status=delivered
                OUT-->>PUB: Done
            else Retryable (5xx)
                WEB-->>PUB: 500
                PUB->>OUT: UPDATE attempts+=1
                alt Max attempts reached
                    PUB->>OUT: UPDATE status=dead_letter
                    PUB->>EXT: Alert operations team
                end
            else Rejected (4xx)
                WEB-->>PUB: 400
                PUB->>OUT: UPDATE status=dead_letter
            end
        end
    end
```

## 8. Edge Device Registration

```mermaid
sequenceDiagram
    participant EA as Edge Agent
    participant API as GULA API
    participant EDGE as Edge Service
    participant DB as PostgreSQL
    participant CRYPTO as Crypto Service
    participant AUD as Audit Log

    EA->>EA: Generate keypair
    EA->>API: POST /edge/devices/register
    Note over EA,API: {public_key_pem, role_mode, agent_version, capabilities}

    API->>EDGE: Register device
    EDGE->>CRYPTO: Verify key format
    CRYPTO-->>EDGE: Valid

    EDGE->>EDGE: Generate agent_token (JWT)
    EDGE->>EDGE: Generate device_id (ULID)
    EDGE->>EDGE: Calculate trust_score (initial)

    EDGE->>DB: INSERT edge_devices
    EDGE->>DB: INSERT audit_log
    DB-->>EDGE: Device saved

    EDGE-->>API: {device_id, agent_token, trust_score, nonce}
    API-->>EA: Registration response

    EA->>EA: Store credentials

    loop Every 60 seconds
        EA->>API: POST /edge/heartbeat<br/>Authorization: Bearer <agent_token>
        EA->>EA: Echo-and-sign nonce
        API->>EDGE: mark_heartbeat(device_id)
        EDGE->>DB: UPDATE last_seen_at
        DB-->>EDGE: Updated
        EDGE->>EDGE: Recalculate trust_score
        EDGE-->>API: {status: active, pending_tasks: [...]}
        API-->>EA: Heartbeat acknowledged
    end
```

## 9. Break-Glass Emergency Access

```mermaid
sequenceDiagram
    participant DOC as Doctor
    participant API as GULA API
    participant BG as Break-Glass Service
    participant AUTH as Auth Service
    participant CONS as Consent Service
    participant DB as PostgreSQL
    participant AUD as Audit Log
    participant NOTIF as Notifications

    DOC->>API: GET /patients/{id}/results
    API->>AUTH: Verify JWT
    API->>CONS: check_consent()
    CONS-->>API: No consent
    API-->>DOC: 403 FORBIDDEN

    DOC->>API: POST /security/break-glass
    Note over DOC,API: {patient_id: 42, reason: "Emergency — patient unresponsive", duration_minutes: 60}

    API->>BG: initiate_emergency_access()
    BG->>DB: INSERT break_glass_log
    Note over BG,DB: patient_id, doctor_id, reason, duration, status=active

    BG->>NOTIF: Notify lab admin of emergency access
    NOTIF->>NOTIF: Send push/email/SMS

    BG->>AUD: Log emergency access
    DB-->>BG: Created
    BG-->>API: {access_token, expires_at}

    API-->>DOC: Emergency token (60 min TTL)

    DOC->>API: GET /patients/{id}/results
    Note over DOC,API: Authorization: Bearer <emergency_token>

    API->>AUTH: Verify emergency token
    AUTH-->>API: Emergency scope, patient_id
    API->>DB: Fetch patient results
    DB-->>API: Results
    API-->>DOC: 200 + Patient results

    Note over DOC,NOTIF: === Auto-expiry after 60 minutes ===

    BG->>BG: Check expired entries (cron)
    BG->>DB: UPDATE break_glass_log SET status=expired
    BG->>AUD: Log expiry
```

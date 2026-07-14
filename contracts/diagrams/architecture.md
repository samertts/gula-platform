# GULA Platform — Architecture Diagrams

**Contract Tag:** `integration-contracts-v1.0` | **Date:** 2026-07-14

---

## 1. System Architecture (All Components)

```mermaid
graph TB
    subgraph External
        USERS[Users: Web/Mobile]
        INST[Lab Instruments]
        HIS[External HIS/EMR]
        MOH[Ministry of Health]
        CI[Citizen Portal]
    end

    subgraph Edge
        EA[Edge Agent]
        DB[Device Bridge]
    end

    subgraph "GULA Backend"
        subgraph "API Layer"
            NGINX[nginx TLS]
            GW[api-gateway<br/>nginx :8080]
        end

        subgraph "FastAPI App"
            MIDDLEWARE[Middleware Stack<br/>10 layers]
            ROUTES[36 Route Modules]
            AUTH[Security: JWT/RBAC/ABAC]
        end

        subgraph "Business Logic"
            LIMS[LIMS Services]
            MPI[Master Patient Index]
            AI[Clinical AI]
            QC[Quality Control]
        end

        subgraph "Infrastructure"
            PSQL[(PostgreSQL 16)]
            REDIS[(Redis 7)]
            KERNEL[Engineering Kernel<br/>Capability Registry]
        end

        subgraph "Events"
            OUTBOX[Transactional Outbox<br/>outbox_events]
            WORKER[Outbox Worker]
            WEBHOOK[Webhooks]
        end

        subgraph "Integration"
            FHIR[FHIR R4 Mapper]
            HL7[HL7 v2.5 Parser]
            ASTM[ASTM E1394 Parser]
        end
    end

    USERS --> NGINX
    NGINX --> GW
    GW --> MIDDLEWARE
    MIDDLEWARE --> ROUTES
    ROUTES --> AUTH
    ROUTES --> LIMS
    ROUTES --> AI
    ROUTES --> FHIR

    INST --> DB
    DB -->|ASTM/TCP| LIMS
    INST -->|HL7/HTTP| HL7
    HL7 --> LIMS
    ASTM --> LIMS

    LIMS --> PSQL
    LIMS --> OUTBOX
    OUTBOX --> WORKER
    WORKER --> WEBHOOK
    WEBHOOK --> HIS
    WEBHOOK --> MOH

    EA -->|Offline Sync| LIMS
    LIMS --> MPI
    LIMS --> QC
    AI --> PSQL
    KERNEL --> LIMS
    REDIS --> AUTH
    REDIS --> ROUTES

    USERS --> CI
    CI --> ROUTES

    LIMS --> FHIR
    FHIR --> MOH
```

## 2. Request Lifecycle

```mermaid
sequenceDiagram
    participant C as Client
    participant NGX as nginx
    participant GW as api-gateway
    participant MW as Middleware Stack
    participant RT as Route Handler
    participant SVC as Service Layer
    participant DB as PostgreSQL
    participant RDS as Redis

    C->>NGX: HTTPS Request
    NGX->>GW: Reverse Proxy
    GW->>MW: :8080

    Note over MW: 1. MaxBodySizeMiddleware<br/>413 if >10MB
    Note over MW: 2. RequestIDMiddleware<br/>Assign X-Request-ID
    Note over MW: 3. DocsAuthMiddleware<br/>(production: admin JWT required)
    Note over MW: 4. CORSMiddleware
    Note over MW: 5. RequestTimingMiddleware<br/>Log latency + X-Response-Time
    Note over MW: 6. SecurityHeadersMiddleware<br/>CSP, HSTS, etc.
    Note over MW: 7. GZipMiddleware
    Note over MW: 8. ReadinessMiddleware<br/>503 if system not ready
    Note over MW: 9. DegradedModeMiddleware<br/>503 if DB circuit open
    Note over MW: 10. ConcurrencyLimitMiddleware<br/>Backpressure if >200 in-flight

    MW->>RT: Clean request
    RT->>RDS: Check JWT blacklist
    RT->>SVC: Business logic
    SVC->>DB: Query/Write
    SVC->>SVC: AuditLog.write()
    SVC->>DB: OutboxEvent.insert()
    DB-->>SVC: Result
    SVC-->>RT: Response
    RT-->>MW: Response
    MW-->>GW: Enriched response
    GW-->>NGX: Response
    NGX-->>C: HTTPS Response
```

## 3. Event Flow (Outbox Pattern)

```mermaid
graph LR
    subgraph "Write Path"
        REQ[HTTP Request]
        SVC[Service Layer]
        TX[DB Transaction]
        BUS[Business Table]
        OUTBOX[outbox_events]
    end

    subgraph "Delivery Path"
        POLL[Outbox Worker<br/>poll every 10s]
        PUB[Publisher]
        WEB[Webhook Endpoint]
        DLQ[Dead Letter Queue]
    end

    subgraph "Consumers"
        LIS[Listeners]
        EXT[External Systems]
    end

    REQ --> SVC
    SVC --> TX
    TX --> BUS
    TX --> OUTBOX

    POLL -->|fetch batch of 50| OUTBOX
    POLL --> PUB
    PUB --> WEB
    WEB --> LIS
    WEB --> EXT

    PUB -->|max 5 attempts| DLQ
    DLQ -->|alert ops| EXT

    style OUTBOX fill:#f96,stroke:#333
    style POLL fill:#6f9,stroke:#333
```

## 4. FHIR Mapping Flow

```mermaid
graph LR
    subgraph "Source Models"
        CIT[Citizen]
        PAT[Patient]
        ORG[Organization]
        PRAC[Practitioner]
        LAB[LabResult]
        ORD[LabOrder]
        SPEC[Specimen]
    end

    subgraph "FHIR Mappers"
        PM[PatientMapper]
        ORGM[OrganizationMapper]
        PRM[PractitionerMapper]
        OM[ObservationMapper]
        DRM[DiagnosticReportMapper]
        SM[SpecimenMapper]
        SRM[ServiceRequestMapper]
    end

    subgraph "FHIR Resources"
        FP[Patient]
        FO[Organization]
        FPR[Practitioner]
        FOB[Observation]
        FDR[DiagnosticReport]
        FS[Specimen]
        FSR[ServiceRequest]
    end

    subgraph "Endpoint Families"
        CMP[Compliance<br/>/compliance/fhir]
        LIMSFHIR[LIMS<br/>/lims/{res}s/{id}/fhir]
        NAT[National<br/>/national/fhir]
    end

    CIT --> PM
    PAT --> PM
    ORG --> ORGM
    PRAC --> PRM
    LAB --> OM
    LAB --> DRM
    ORD --> SRM
    SPEC --> SM

    PM --> FP
    ORGM --> FO
    PRM --> FPR
    OM --> FOB
    DRM --> FDR
    SM --> FS
    SRM --> FSR

    FP --> CMP
    FOB --> CMP
    FDR --> CMP
    FSR --> CMP

    FS --> LIMSFHIR
    FSR --> LIMSFHIR
    FOB --> LIMSFHIR
    FDR --> LIMSFHIR

    FP --> NAT
    FO --> NAT
    FPR --> NAT
    FOB --> NAT
```

## 5. HL7/ASTM Ingestion Pipeline

```mermaid
graph TB
    subgraph "Instruments"
        ROCHE[Roche Cobas]
        SYSMEX[Sysmex XN]
        ABBOTT[Abbott Architect]
        MINDRAY[Mindray BC]
        GENERIC[Generic ASTM]
    end

    subgraph "Transport"
        SERIAL[RS-232 Serial]
        TCP[TCP/IP Socket]
        HTTP[HTTP POST]
    end

    subgraph "Device Bridge (services/device_bridge)"
        BUF[ASTMBuffer<br/>byte accumulation]
        FRAME[Frame Extractor<br/>STX...ETX+checksum]
        CHECKSUM[Checksum Validator]
        ASTMPARSE[ASTM Parser]
        MB[Message Builder]
        AR[Adapter Registry]
        TME[Test Mapping Engine]
        PM[Patient Matcher]
        NORM[Normalizer]
        RR[Result Repository]
        GC[GulaClient<br/>REST Forwarder]
        RQ[RetryQueue]
        EB[EdgeBuffer]
    end

    subgraph "Backend (monolith)"
        HL7P[HL7 Parser]
        ASTMP[ASTM Parser]
        MATCH[Order Matcher]
        SAVE[Result Saver]
        AUDIT[Audit Logger]
        AUTO[Auto-Validator]
        CRIT[Critical Checker]
    end

    ROCHE -->|ASTM/TCP| TCP
    SYSMEX -->|ASTM/Serial| SERIAL
    ABBOTT -->|HL7/HTTP| HTTP
    MINDRAY -->|ASTM/Serial| SERIAL
    GENERIC -->|ASTM| TCP

    SERIAL --> BUF
    TCP --> BUF
    HTTP --> HL7P

    BUF --> FRAME
    FRAME --> CHECKSUM
    CHECKSUM --> ASTMPARSE
    ASTMPARSE --> MB
    MB --> AR
    AR --> TME
    TME --> PM
    PM --> NORM
    NORM --> RR
    RR --> GC

    GC -->|HTTP| ASTMP
    GC --> HL7P
    HL7P --> MATCH
    ASTMP --> MATCH
    MATCH --> SAVE
    SAVE --> AUDIT
    SAVE --> AUTO
    SAVE --> CRIT

    GC -->|on failure| RQ
    GC -->|edge mode| EB
```

## 6. Auth/Security Flow

```mermaid
sequenceDiagram
    participant U as User
    participant C as Client
    participant API as API Gateway
    participant AUTH as Auth Service
    participant DB as PostgreSQL
    participant RDS as Redis

    U->>C: Enter credentials
    C->>API: POST /login
    API->>AUTH: Verify password
    AUTH->>DB: Fetch user + hash
    DB-->>AUTH: User record
    AUTH->>AUTH: bcrypt verify
    AUTH->>AUTH: build_token_payload()
    AUTH->>AUTH: JWT.encode(HS256)
    AUTH-->>API: {access_token, refresh_token}
    API-->>C: Tokens
    C-->>U: Authenticated

    Note over U, RDS: === Authenticated Request ===

    C->>API: POST /orders<br/>Authorization: Bearer <token>
    API->>RDS: Check blacklist(jti)
    RDS-->>API: Not blacklisted
    API->>API: JWT.decode(SECRET_KEY)
    API->>API: Check token type=access
    API->>API: Check perm_version
    API->>API: Check role permission
    API->>API: Check tenant isolation (lab_id)
    API->>API: ABAC policy evaluation
    API->>DB: Execute operation
    API->>DB: Write audit log
    API-->>C: Response
    C-->>U: Result

    Note over U, RDS: === Logout ===

    C->>API: POST /auth/logout
    API->>RDS: SET blacklist:jti:<jti>
    API-->>C: Logged out
```

## 7. LIMS State Machine

```mermaid
stateDiagram-v2
    state "Order States" as ORDER {
        [*] --> pending
        pending --> completed
        completed --> validated
        validated --> released
        pending --> cancelled
        completed --> corrected
    }

    state "Sample States" as SAMPLE {
        [*] --> ordered
        ordered --> registered
        registered --> collected
        collected --> transporting
        transporting --> received
        received --> accepted
        received --> rejected
        accepted --> analysis_started
        analysis_started --> analyzed
        analyzed --> verified
        verified --> validated
        validated --> released
        released --> archived
        archived --> disposed
        rejected --> [*]
        disposed --> [*]
    }

    state "Result States" as RESULT {
        [*] --> pending
        pending --> completed
        completed --> verified
        verified --> validated
        pending --> rejected
        validated --> corrected
    }

    state "QC States" as QC {
        [*] --> in_control
        in_control --> warning
        warning --> out_of_control
        out_of_control --> in_control
    }
```

## 8. Sub-domain Boundaries (DDD)

```mermaid
graph TB
    subgraph "Identity & Access"
        AUTH[Authentication]
        RBAC[RBAC/ABAC]
        CONSENT[Consent]
        AUDIT[Audit Log]
    end

    subgraph "Clinical Laboratory"
        PAT[Patient Management<br/>MPI]
        ORD[Order Management]
        SAMP[Sample Tracking]
        RES[Result Management]
        QC[Quality Control]
        INST[Instrument Integration]
    end

    subgraph "National Health"
        NID[National ID]
        FHIR[FHIR Interoperability]
        SNDHS[SNDHS-lite Reporting]
        GOV[Governance Hierarchy]
    end

    subgraph "Financial"
        CLAIM[Insurance Claims]
        BILL[Billing]
        TIER[Subscription Tiers]
    end

    subgraph "Edge & Mobile"
        EDGE[Edge Computing]
        SYNC[Offline Sync]
        PUSH[Push Notifications]
    end

    subgraph "Platform"
        EVENTS[Event Bus / Outbox]
        INTEG[Integration Connectors]
        KERNEL[Engineering Kernel]
        CAP[Capability Registry]
    end

    subgraph "AI"
        CLIN[Clinical Interpretation]
        CHAT[Assistant Chat]
        ANOM[Anomaly Detection]
    end

    AUTH --> RBAC
    RBAC --> CONSENT
    RBAC --> AUDIT

    PAT --> ORD
    ORD --> SAMP
    SAMP --> RES
    RES --> QC
    INST --> RES

    PAT --> NID
    NID --> SNDHS
    FHIR --> SNDHS
    GOV --> SNDHS

    RES --> CLAIM
    ORD --> CLAIM

    EDGE --> SYNC
    RES --> EDGE

    EVENTS --> INTEG
    KERNEL --> EVENTS
    CAP --> KERNEL

    RES --> CLIN
    CLIN --> CHAT
    CLIN --> ANOM
```

## 9. Deployment Architecture

```mermaid
graph TB
    subgraph "Internet"
        DNS[DNS: gula-platform.org]
        CDN[Cloudflare CDN]
    end

    subgraph "Docker Host"
        subgraph "Proxy Layer"
            NGINX[nginx<br/>TLS termination<br/>:443]
            GW[api-gateway<br/>nginx<br/>127.0.0.1:8080]
        end

        subgraph "Application Layer"
            BACKEND[gula-backend<br/>FastAPI + gunicorn<br/>:8000<br/>3 workers]
            WORKER[gula-worker<br/>Background tasks<br/>Outbox delivery]
        end

        subgraph "Data Layer"
            PG[(PostgreSQL 16<br/>:5432)]
            REDIS[(Redis 7<br/>:6379)]
        end

        subgraph "Monitoring (opt-in)"
            PROM[Prometheus]
            GRAF[Grafana]
            HA[HAProxy :8404/stats<br/>scale mode]
        end
    end

    subgraph "External Services"
        SENTRY[Sentry Error Tracking]
        PG_HOUSE[PostHog Analytics]
        FCM[Firebase Cloud Messaging]
        AI_API[Google AI Studio<br/>Gemini API]
    end

    subgraph "Off-Premise"
        EA[Edge Agent]
        DB[Device Bridge]
    end

    DNS --> CDN
    CDN --> NGINX
    NGINX --> GW
    GW --> BACKEND

    BACKEND --> PG
    BACKEND --> REDIS
    WORKER --> PG
    WORKER --> REDIS

    BACKEND --> SENTRY
    BACKEND --> PG_HOUSE
    BACKEND --> FCM
    BACKEND --> AI_API

    EA -->|Sync| BACKEND
    DB -->|ASTM/HL7 Results| BACKEND

    PROM --> BACKEND
    GRAF --> PROM
    HA --> BACKEND

    NGINX -->|scale mode| HA
    HA --> BACKEND
```

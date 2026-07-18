# GULA Platform Future Architecture

> Version: 1.0 | Status: Vision Document | Last Updated: 2026-07-17
> Target: 2029-2030 Architecture State (Phase 3-4)

---

## 1. Architecture Vision Statement

**In 3 years, the GULA Platform is a domain‑driven, event‑driven, multi‑region healthcare platform serving 500+ labs across 3+ countries, with AI‑augmented clinical decision support and full FHIR R4 compliance.**

The monolith remains the system of record for lab operations, but it is a *modular* monolith that has been surgically decomposed into 12+ domain services around it. These services communicate via an event backbone (Redis Streams → Kafka/RabbitMQ) with REST/HTTP and gRPC for synchronous query paths.

The architecture is:
- **Domain-driven**: Each bounded context owns its data and exposes it via API + events
- **Event-driven**: State changes publish domain events; services react asynchronously
- **API-first**: OpenAPI schemas govern all service boundaries; FHIR R4 is the interoperability standard
- **Observable-by-design**: Every component emits OpenTelemetry traces, structured logs, and Prometheus metrics
- **Self-healing**: Circuit breakers, bulkheads, and degraded-mode operation (from `core/self_healing.py`) are universal patterns
- **Zero Trust-ready**: mTLS between all services, policy-based access control, continuous verification

The monolith is not deleted—it evolves into the **Lab Operations Hub**, the system of record for the core lab workflow (orders, results, samples). Everything else (auth, notifications, analytics, AI, payments, patient registry, device integration) is a domain service.

---

## 2. Domain‑Driven Design Bounded Contexts

### 2.1 Context Map (Strategic DDD)

```
┌─────────────────────────────────────────────────────────────────┐
│                     GULA Platform Context Map                    │
│                                                                  │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌────────┐ │
│  │  Auth &   │◄────│   Lab    │◄────│  Order   │────►│Result  │ │
│  │ Identity  │     │ Ops Hub  │     │Management│     │Manager │ │
│  └──────────┘     └──────────┘     └──────────┘     └────────┘ │
│       ▲                                    │              ▲      │
│       │                                    ▼              │      │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐          │      │
│  │Patient   │◄────│  Device  │────►│ Sample   │──────────┘      │
│  │Registry  │     │  Bridge  │     │ Management│                │
│  │ (MPI)    │     └──────────┘     └──────────┘                │
│  └──────────┘                                                   │
│       │                                                         │
│       ▼                                                         │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌────────┐ │
│  │National  │◄────│ Financial│     │  AI      │     │ Notif-  │ │
│  │HIE (NHOP)│     │  Engine  │     │ Service  │     │ ication │ │
│  └──────────┘     └──────────┘     └──────────┘     └────────┘ │
│                                              ┌──────────────┐   │
│                                              │  Edge Mesh   │   │
│                                              │  (1000+      │   │
│                                              │   agents)    │   │
│                                              └──────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Bounded Context Definitions

| # | Context | Type | Data Owner | Communication | Current Location |
|---|---------|------|------------|---------------|-----------------|
| BC1 | Auth & Identity | Core | Shared (multi-tenant) | REST + OAuth 2.0 | `backend/app/security/` |
| BC2 | Lab Operations Hub | Core | Lab | In-process (monolith) | `backend/app/` (core) |
| BC3 | Order Management | Core | Lab | Events + REST | `backend/app/routes/orders.py` |
| BC4 | Result Manager | Core | Lab | Events + REST | `backend/app/routes/results.py` |
| BC5 | Sample Management | Supporting | Lab | Events + REST | `backend/app/routes/samples.py` |
| BC6 | Patient Registry (MPI) | Supporting | Global | Events + FHIR | `backend/app/services/mpi/` |
| BC7 | Device Bridge | Core | Lab | ASTM/HL7 + HTTP | `services/device_bridge/` |
| BC8 | Financial Engine | Supporting | Lab/Global | Events + REST | `backend/app/financial/` |
| BC9 | AI Service | Generic | Global | gRPC + Events | `backend/app/ai/` + `services/ai/` |
| BC10 | Notification Service | Generic | Shared | Events | `backend/app/notifications/` |
| BC11 | Audit & Compliance | Supporting | Global | Append-only events | `backend/app/audit/` |
| BC12 | Stats & Analytics | Generic | Global | Read-only (materialized views) | `backend/app/routes/stats.py` |
| BC13 | National HIE (NHOP) | Core | Country | Events + FHIR | `nhop-platform/` |
| BC14 | Edge Mesh | Core | Lab | Offline-sync + Events | `edge_agent/` |
| BC15 | Telemedicine/Referral | Supporting | Global | Events + FHIR | Not yet built |
| BC16 | Marketplace | Generic | Global | REST + Events | Not yet built |

### 2.3 Ubiquitous Language (Key Terms)

| Term | Definition |
|------|-----------|
| Lab Order | A request for one or more lab tests, placed by a doctor for a patient |
| Lab Result | The outcome of a lab test, including numerical value, reference range, and interpretation |
| Sample Specimen | Physical material collected from a patient for analysis |
| Patient Registry | The master index of all patients across all labs, with national ID resolution |
| Device Instrument | A physical lab analyzer producing ASTM/HL7 result messages |
| Critical Alert | A lab result that exceeds critical threshold, requiring immediate clinical action |
| Visit | A clinical encounter (SNDHS concept) that groups one or more orders |
| National ID | The Iraqi national identification number (encrypted at rest) |
| SNDHS | Iraqi National Health Data System (the national health information exchange) |
| Edge Agent | A local server at a remote lab that caches data and syncs when online |

---

## 3. Service Mesh Architecture

### 3.1 Mesh Topology

```
                    ┌──────────────────────┐
                    │   Cloudflare (CDN)    │
                    │  + WAF + DDoS Shield  │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │   Ingress Gateway     │
                    │   (Istio/Kong)        │
                    │   TLS termination     │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │   Service Mesh        │
                    │   (Istio/Linkerd)     │
                    │                       │
                    │  ┌─────────────────┐  │
                    │  │  Sidecar Proxy   │  │
                    │  │  (Envoy/Linkerd) │  │
                    │  └─────────────────┘  │
                    │         │             │
                    │  ┌──────┴──────┐      │
                    │  │  Services    │      │
                    │  │  (Pod/Deploy)│      │
                    │  └─────────────┘      │
                    └───────────────────────┘
```

### 3.2 Mesh Features

| Feature | Implementation | Timeline |
|---------|---------------|----------|
| Service discovery | Istio DNS + Kubernetes DNS | Phase 2 |
| mTLS | Istio mTLS (STRICT mode) | Phase 2 (internal), Phase 3 (external) |
| Traffic management | Istio VirtualService + DestinationRule | Phase 2 |
| Circuit breaking | Istio OutlierDetection | Phase 2 |
| Rate limiting | Istio EnvoyFilter + local rate limiting | Phase 2 |
| Retry + timeout | Istio VirtualService retry/timeout | Phase 2 |
| Fault injection | Istio VirtualService fault (chaos testing) | Phase 2 |
| Traffic mirroring | Istio VirtualService mirror | Phase 2 |
| Access control | Istio AuthorizationPolicy | Phase 3 |
| Observability | Istio + Prometheus + Grafana + Kiali + Jaeger | Phase 2 |
| Multi-cluster | Istio multi-primary (multi-region) | Phase 4 |

### 3.3 Mesh Policies

```yaml
# Example: Istio AuthorizationPolicy for Lab Ops Hub
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: lab-ops-authz
spec:
  selector:
    matchLabels:
      app: lab-ops-hub
  action: ALLOW
  rules:
  - from:
    - source:
        principals: ["cluster.local/ns/default/sa/auth-service"]
    to:
    - operation:
        methods: ["POST", "PUT"]
        paths: ["/api/v2/orders/*"]
  - from:
    - source:
        namespaces: ["lab-ops"]
    to:
    - operation:
        methods: ["GET"]
        paths: ["/api/v2/orders/*"]
```

---

## 4. Event Storming Results

### 4.1 Key Domain Events

| Event | Publisher | Subscribers | Trigger |
|-------|-----------|-------------|---------|
| `OrderPlaced` | Order Management | Sample Mgmt, Notifications, AI Service, Stats | Doctor submits order |
| `SampleCollected` | Sample Management | Order Mgmt, Notifications | Phlebotomist collects sample |
| `SampleReceivedAtLab` | Sample Management | Order Mgmt, Result Manager | Lab receives sample |
| `ResultEntered` | Device Bridge / Manual Entry | Result Manager, AI Service, Notifications | Instrument produces result |
| `ResultValidated` | Result Manager | Notifications, Stats, AI Service | Tech approves result |
| `ResultPublished` | Result Manager | Notifications, Stats, Patient Registry | Result released to patient/doctor |
| `CriticalAlertTriggered` | Result Manager | Notifications, AI Service (escalation) | Result exceeds critical threshold |
| `PatientMerged` | Patient Registry (MPI) | All contexts (via event bus) | MPI deduplication finds duplicate |
| `LabDeviceStatusChanged` | Device Bridge | Lab Ops Hub, Edge Mesh | Device online/offline/error |
| `NationalIdLinked` | Patient Registry | Audit, SNDHS Bridge | National ID associated with patient |
| `PaymentProcessed` | Financial Engine | Notifications, Order Mgmt | Payment completed |
| `EdgeSyncCompleted` | Edge Mesh | Lab Ops Hub, Result Manager | Edge agent syncs offline data |

### 4.2 Key Commands

| Command | Handler | Preconditions | Postconditions |
|---------|---------|---------------|----------------|
| `PlaceOrder` | Order Management | Patient exists, lab is active, tests valid | OrderPlaced event |
| `CollectSample` | Sample Management | Order exists, sample type valid | SampleCollected event |
| `EnterResult` | Result Manager | Sample exists, instrument valid | ResultEntered event |
| `ValidateResult` | Result Manager | Result exists, user has permissions | ResultValidated event |
| `PublishResult` | Result Manager | Result validated | ResultPublished event |
| `MergePatients` | Patient Registry | Two patients identified as same | PatientMerged event |
| `LinkNationalId` | Patient Registry | Patient exists, NID verified | NationalIdLinked event |
| `TriggerCriticalAlert` | Result Manager | Result exceeds critical threshold | CriticalAlertTriggered event |

### 4.3 Aggregates

| Aggregate | Context | Key | Events It Emits |
|-----------|---------|-----|-----------------|
| LabOrder | Order Management | order_id | OrderPlaced, OrderCancelled, OrderCompleted |
| LabResult | Result Manager | result_id | ResultEntered, ResultValidated, ResultPublished, CriticalAlertTriggered |
| Sample | Sample Management | sample_id | SampleCollected, SampleReceivedAtLab, SampleDisposed |
| Patient | Patient Registry | patient_id | PatientCreated, PatientMerged, NationalIdLinked |
| LabDevice | Device Bridge | device_id | LabDeviceStatusChanged, LabDeviceCalibrated |

---

## 5. CQRS/Event Sourcing

### 5.1 Where to Introduce CQRS

| Context | Command Side | Query Side | When | Why |
|---------|-------------|------------|------|-----|
| **Result Manager** | Write-optimized: current monolith DB | Read-optimized: materialized views for result history | Phase 2 | Result queries (patient history, trends) dominate read load |
| **Stats & Analytics** | None (event-sourced) | Dedicated analytics DB (ClickHouse) with denormalized aggregates | Phase 3 | Complex aggregation queries must not impact transactional paths |
| **Audit** | Append-only event log | Search-optimized audit index (Elasticsearch) | Phase 3 | Forensic audit queries are structurally different from writes |
| **Patient Registry** | Write: current patient DB | Read: FHIR-optimized patient view | Phase 3 | FHIR patient queries have different shape than internal writes |
| **Order Management** | Write: current order DB | Read: order status materialized view | Phase 2-3 | Dashboard queries for order status dominate |

### 5.2 Event Sourcing Candidates

| Context | Event Store | Snapshot Strategy | Why Not Full ES |
|---------|-------------|-------------------|-----------------|
| **Audit** (full ES) | Append-only event store (separate DB) | Daily snapshots | Audit is naturally event-sourced; current v2 chain is partial |
| **Order State Machine** (partial ES) | Current DB + event log | Current state in DB + event history | Full ES is too complex for order management; hybrid is better |
| **Financial Transactions** (full ES) | Append-only ledger | End-of-day balance snapshots | Financial audit requires full event sourcing |

### 5.3 CQRS Architecture Diagram

```
                    ┌────────────────────────────┐
                    │      Event Bus              │
                    │  (Redis Streams / Kafka)    │
                    └──────┬──────────┬───────────┘
                           │          │
            ┌──────────────▼──┐  ┌────▼──────────────┐
            │  Command Side   │  │   Query Side       │
            │  (Write Model)  │  │   (Read Model)     │
            │                 │  │                    │
            │  ┌───────────┐  │  │  ┌────────────┐   │
            │  │ Aggregate  │  │  │  │Materialized│   │
            │  │  Root      │──┼──┼──│  View      │   │
            │  └───────────┘  │  │  └────────────┘   │
            │  ┌───────────┐  │  │  ┌────────────┐   │
            │  │ Event Store│  │  │  │ Read-      │   │
            │  │ (Optional) │  │  │  │ Optimized  │   │
            │  └───────────┘  │  │  │    DB      │   │
            └─────────────────┘  └────┬──────────────┘
                                       │
                              ┌────────▼────────┐
                              │  API Gateway    │
                              │  (REST for cmd, │
                              │   REST for qry) │
                              └─────────────────┘
```

---

## 6. Multi-Region Deployment

### 6.1 Region Topology (2030 Target)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        GULA Global Mesh                             │
│                                                                      │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐            │
│   │  Iraq-North  │    │  Iraq-Central│   │  Iraq-South  │           │
│   │  (Erbil)     │    │  (Baghdad)   │   │  (Basra)     │           │
│   │  Active      │◄──►│  Primary     │◄──►│  Active      │           │
│   └─────────────┘    └─────────────┘    └─────────────┘            │
│         │                   │                   │                    │
│         └───────────────────┼───────────────────┘                    │
│                             │                                        │
│                    ┌────────▼────────┐                               │
│                    │   Global        │                               │
│                    │   Control Plane │                               │
│                    │   (Istio)       │                               │
│                    └────────┬────────┘                               │
│                             │                                        │
│         ┌───────────────────┼───────────────────┐                    │
│         │                   │                   │                    │
│   ┌─────▼─────┐      ┌─────▼─────┐      ┌─────▼─────┐              │
│   │  MENA-1   │      │  MENA-2   │      │  EU-West  │              │
│   │  (UAE)    │◄────►│  (KSA)    │◄────►│  (Frankfurt)│            │
│   │  Active   │      │  Active   │      │  (GDPR)   │              │
│   └───────────┘      └───────────┘      └───────────┘              │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.2 Data Replication Strategy

| Data Type | Replication | Consistency | Region Priority |
|-----------|-------------|-------------|-----------------|
| Lab operations (orders, results, samples) | Active-active (3 Iraqi regions) | Read-your-writes | Baghdad = Erbil = Basra |
| Patient registry | Leader-follower (Baghdad primary) | Strong (eventual for far regions) | Baghdad primary |
| Financial data | Active-active with conflict resolution | Strong (financial must reconcile) | Baghdad primary |
| Audit logs | Append-only, cross-region replicated | Eventual | All regions |
| AI models | Distributed (trained centrally, deployed per region) | Version-based | All regions |
| Configuration | GitOps (one source of truth per region) | Strong | Per-region |

### 6.3 Cross-Region Communication

- **Synchronous**: gRPC with timeout/retry (max 200ms cross-region)
- **Asynchronous**: Kafka with cross-region mirroring (MirrorMaker 2)
- **Latency targets**: Baghdad <-> Erbil < 50ms p95, Baghdad <-> Basra < 80ms p95, Cross-country < 200ms p95
- **Degraded mode**: If cross-region link fails, each region operates independently and syncs when reconnected

---

## 7. Edge Computing Mesh

### 7.1 Edge Architecture

```
                    ┌────────────────────────────────────┐
                    │         Cloud (GULA Backend)        │
                    │  - Central DB, AI training          │
                    │  - Global API, FHIR server          │
                    │  - Device bridge cloud relay        │
                    └──────┬────────────────────┬─────────┘
                           │                    │
                    ┌──────▼──────┐    ┌────────▼────────┐
                    │  Regional   │    │   Regional       │
                    │  Edge Hub   │    │   Edge Hub       │
                    │  (Erbil)    │    │   (Basra)        │
                    └──────┬──────┘    └────────┬─────────┘
                           │                    │
            ┌──────────────┼──────────────┬─────┼──────────────┐
            │              │              │     │              │
     ┌──────▼──────┐ ┌─────▼─────┐ ┌─────▼┐ ┌──▼────────┐ ┌──▼───┐
     │Edge Agent   │ │Edge Agent │ │Edge  │ │Edge Agent │ │Edge  │
     │ (Lab 001)   │ │ (Lab 002) │ │Agent │ │ (Lab 050) │ │Agent │
     │ Device      │ │ Device    │ │(N)   │ │ Device    │ │(N)   │
     │ Bridge +    │ │ Bridge +  │ │      │ │ Bridge +  │ │      │
     │ AI Infer.   │ │ AI Infer. │ │      │ │ AI Infer. │ │      │
     └─────────────┘ └───────────┘ └──────┘ └───────────┘ └──────┘
```

### 7.2 Edge Agent Capabilities

| Capability | Current | Phase 2 (2028) | Phase 3 (2029) | Phase 4 (2030) |
|-----------|---------|---------------|---------------|---------------|
| Offline operation | Basic | Full offline with local DB | Local AI inference | Autonomous operation |
| Sync | Manual | Automatic (when online) | Prioritized sync | Real-time (when available) |
| Devices supported | 3 brands | 10+ brands | 20+ brands | All major brands |
| AI at edge | None | Critical value detection | Result validation | Predictive maintenance |
| Local FHIR | None | Read-only FHIR cache | Read-write FHIR | Full FHIR server |

### 7.3 Edge Device Support Matrix (2030 Target)

| Device Manufacturer | Protocol | Edge Agent Support | Cloud Relay |
|--------------------|----------|-------------------|-------------|
| Sysmex | ASTM | Native | Yes |
| Roche | ASTM/HL7 | Native | Yes |
| Mindray | ASTM | Native | Yes |
| Abbott | HL7 | Native | Yes |
| Beckman Coulter | ASTM/HL7 | Native | Yes |
| Siemens | HL7 | Yes | Yes |
| Bio-Rad | ASTM | Yes | Yes |
| BD (Becton Dickinson) | ASTM/HL7 | Yes | Yes |
| Thermo Fisher | LIS2-A | Yes | Yes |
| Generic LIS | ASTM/HL7/LIS2 | In development | Yes |
| Wearables (CGM, BP) | BLE/API | In development (Phase 4) | Yes |

---

## 8. National Health Information Exchange

### 8.1 SNDHS Integration Architecture

```
                    ┌─────────────────────────────────────┐
                    │         SNDHS National HIE          │
                    │  (Ministry of Health, Iraq)          │
                    └────────┬────────────────┬───────────┘
                             │                │
                    ┌────────▼────┐    ┌──────▼──────────┐
                    │ SNDHS API   │    │ SNDHS Analytics │
                    │ (FHIR R4)   │    │ (Population)   │
                    └────────┬────┘    └─────────────────┘
                             │
                    ┌────────▼──────────────────────────┐
                    │      GULA SNDHS Bridge Service     │
                    │  - National ID resolution          │
                    │  - Visit tracking                  │
                    │  - Result submission               │
                    │  - Patient lookup                  │
                    │  - Audit chain v2                  │
                    └────────────────────────────────────┘
                             │
                    ┌────────▼──────────────────────────┐
                    │         GULA Platform              │
                    │  - Lab Operations Hub              │
                    │  - Patient Registry                │
                    │  - All domain services             │
                    └────────────────────────────────────┘
```

### 8.2 SNDHS Phase Progression

| Phase | Status | Capabilities | Flags |
|-------|--------|-------------|-------|
| Phase 1 | In Progress | National ID, visit tracking, audit v2 | `SNDHS_ENABLE_VISITS`, `SNDHS_ENABLE_NATIONAL_ID` |
| Phase 2 | Planned (2027) | Result submission to SNDHS, patient lookup | Additional flags |
| Phase 3 | Planned (2028) | Full FHIR R4 exchange, population reporting | FHIR compliance |
| Phase 4 | Planned (2030) | Cross-region HIE, WHO-compliant | International health ID |

### 8.3 SNDHS Data Flow

```
1. Patient registers at lab
2. National ID is encrypted (ENCRYPTION_KEY) and stored
3. Patient lookup via NID_HMAC_KEY generates HMAC for blind index
4. Visit created (if SNDHS_ENABLE_VISITS enabled)
5. Lab order created → linked to visit (lab_orders.visit_id)
6. Lab result generated → ResultPublished event
7. SNDHS Bridge Service subscribes to ResultPublished
8. Bridge translates result to SNDHS format and submits
9. Audit v2 log records the submission
```

---

## 9. AI Mesh

### 9.1 AI Architecture

```
                    ┌─────────────────────────────────────┐
                    │         AI Orchestrator             │
                    │  - Model registry                   │
                    │  - Inference routing                │
                    │  - A/B testing                      │
                    │  - Shadow mode                      │
                    └────────┬────────────────┬───────────┘
                             │                │
                    ┌────────▼────┐    ┌──────▼──────────┐
                    │  Cloud AI   │    │   Edge AI        │
                    │  Inference  │    │   Inference      │
                    │             │    │                  │
                    │  ┌───────┐  │    │  ┌────────────┐  │
                    │  │LLM    │  │    │  │Critical    │  │
                    │  │(Arabic│  │    │  │Value Det.  │  │
                    │  │Clinical│  │    │  └────────────┘  │
                    │  └───────┘  │    │  ┌────────────┐  │
                    │  ┌───────┐  │    │  │Result      │  │
                    │  │Result │  │    │  │Validation  │  │
                    │  │Interp.│  │    │  └────────────┘  │
                    │  └───────┘  │    └──────────────────┘
                    │  ┌───────┐  │
                    │  │Pop.   │  │
                    │  │Health │  │
                    │  └───────┘  │
                    └─────────────┘
```

### 9.2 AI Model Portfolio (Phase 3 Target)

| Model | Location | Input | Output | Criticality | Training Data |
|-------|----------|-------|--------|-------------|---------------|
| Critical Value Detector | Edge + Cloud | Lab result | Alert level (normal/critical) | Critical | Historical results + clinical guidelines |
| Result Validator | Cloud | Result + patient history | Confidence score (0-1) | High | Validated results from lab techs |
| Reference Range Predictor | Cloud | Patient demographics | Predicted reference ranges | Medium | Population health data |
| Arabic Clinical LLM | Cloud | Clinical text (Arabic) | Structured data, summaries | Medium | Arabic medical texts, clinical notes |
| Anomaly Detector (QC) | Edge + Cloud | QC sample results | QC pass/fail + trend | High | Historical QC data |
| Patient Deduplication | Cloud | Patient records | Match probability | Critical | Patient registry (MPI) |
| Predictive Maintenance | Cloud | Device telemetry | Failure probability | Medium | Device logs, maintenance records |
| Population Health Model | Cloud | Aggregated lab data | Disease prevalence trends | Low | Anonymized lab data |

### 9.3 AI Governance

| Principle | Implementation |
|-----------|---------------|
| Human-in-the-loop | All critical alerts must be confirmed by a lab professional before release |
| Shadow mode | New models run in shadow for 30 days before active deployment |
| Bias monitoring | Quarterly fairness audit across gender, age, and region |
| Explainability | All AI decisions must include explanation (SHAP/LIME) |
| Data privacy | No patient-identifiable data used for training; differential privacy on population models |
| Model versioning | Every model version is tracked; rollback supported |

---

## 10. Data Mesh

### 10.1 Data Product Catalog

| Data Product | Owner | Source | Format | Access | Consumers |
|-------------|-------|--------|--------|--------|-----------|
| Lab Results | Lab Ops Hub | Transactional DB | Parquet (export) + FHIR | API + Event | Stats, AI, Population Health |
| Patient Registry | Patient Context | Patient DB | FHIR Patient Resource | API (REST) | All contexts |
| Financial Ledger | Financial Engine | Financial DB | CSV + double-entry | API (Restricted) | Finance, Compliance |
| Audit Trail | Audit Context | Append-only store | JSON + structured | API (Restricted) | Compliance, Security |
| Device Telemetry | Device Bridge | Time-series DB | Prometheus metrics | Push | AI, Operations |
| Population Stats | Stats Context | Materialized views | ClickHouse + dashboards | Dashboard + API | MoH, Public Health |
| QC Data | Lab Ops Hub | QC tables | Parquet | API | AI, Compliance |

### 10.2 Data Mesh Principles Applied

1. **Domain ownership**: Each bounded context owns its data products
2. **Data as a product**: Each data product has documented schema, SLOs, owners
3. **Self-serve data platform**: Common infrastructure (storage, catalog, lineage) provided centrally
4. **Federated computational governance**: Global standards (FHIR) + local autonomy

---

## 11. Zero Trust Architecture

### 11.1 Zero Trust Principles Applied

| Principle | Current | Phase 2 | Phase 3 | Phase 4 |
|-----------|---------|---------|---------|---------|
| Verify explicitly | JWT at API gateway | mTLS between services | + Continuous verification | + Behavioral analytics |
| Least privilege | RBAC (9 roles) | RBAC + ABAC | + Policy engine (OPA) | + Just-in-time access |
| Assume breach | Audit logs | + Intrusion detection | + Automated response | + Self-healing quarantine |

### 11.2 Zero Trust Implementation

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Zero Trust Architecture                           │
│                                                                      │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐      │
│   │ Identity  │    │ Device   │    │ Network  │    │ Data     │      │
│   │ Pillar    │    │ Pillar   │    │ Pillar   │    │ Pillar   │      │
│   │           │    │          │    │          │    │          │      │
│   │ - OIDC   │    │ - mTLS  │    │ - Micro- │    │ - AES-   │      │
│   │ - OAuth2 │    │ - Device │    │   seg.   │    │   256    │      │
│   │ - FIDO2  │    │   trust  │    │ - Ingress │   │ - TDE   │      │
│   │ - JWT    │    │ - MDM   │    │ - Egress  │    │ - Token- │      │
│   │          │    │          │    │   control │    │  ization  │      │
│   └──────────┘    └──────────┘    └──────────┘    └──────────┘      │
└─────────────────────────────────────────────────────────────────────┘
```

### 11.3 Policy Decision Point (PDP)

```yaml
# Open Policy Agent (OPA) policy example
# data.gula.lab_result.access
default allow = false

# Lab users can read results for their lab
allow {
  input.user.role == "lab_technician"
  input.resource.lab_id == input.user.lab_id
  input.operation == "read"
}

# Doctors can read results for their patients
allow {
  input.user.role == "doctor"
  input.resource.patient_id in input.user.patient_ids
  input.operation == "read"
}

# National HIE can read anonymous aggregate data
allow {
  input.user.role == "national_hie"
  input.operation == "aggregate_read"
  input.resource.anonymized == true
}
```

---

## 12. Future Component Map

### 12.1 Infrastructure Components

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Future Component Map                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ACCESS LAYER                                                        │
│  ├── Cloudflare CDN + WAF                                            │
│  ├── Ingress Gateway (Istio/Kong)                                    │
│  └── API Gateway (custom)                                            │
│                                                                      │
│  SERVICE MESH (Istio/Linkerd)                                        │
│  ├── Auth & Identity (S1) ───────────────────── OAuth 2.0/OIDC       │
│  ├── Lab Operations Hub (BC2) ──────────────── System of Record      │
│  │   ├── Order Management (BC3) ───────────── Domain service         │
│  │   ├── Result Manager (BC4) ─────────────── Domain service         │
│  │   └── Sample Management (BC5) ──────────── Domain service         │
│  ├── Patient Registry / MPI (BC6) ─────────── FHIR + SNDHS          │
│  ├── Device Bridge (BC7) ──────────────────── ASTM/HL7 + Edge       │
│  ├── Financial Engine (BC8) ───────────────── Phase B+               │
│  ├── AI Service (BC9) ─────────────────────── Inference + Models    │
│  ├── Notification Service (BC10) ──────────── SMS/Email/Push        │
│  ├── Audit Service (BC11) ─────────────────── Append-only          │
│  ├── Stats & Analytics (BC12) ─────────────── ClickHouse/Dashboards │
│  ├── National HIE Bridge (BC13) ───────────── SNDHS FHIR Gateway    │
│  ├── Telemedicine (BC15) ──────────────────── Referral + Second Op. │
│  └── Marketplace (BC16) ───────────────────── Provider Directory    │
│                                                                      │
│  DATA LAYER                                                          │
│  ├── PostgreSQL 16 (per service, shared cluster)                     │
│  │   ├── Lab Operations DB (sharded by lab_id)                       │
│  │   ├── Patient Registry DB (global, encrypted)                     │
│  │   └── Financial DB (append-only ledger)                           │
│  ├── Redis 7 Cluster (cache + streams)                               │
│  ├── Kafka / RabbitMQ (event bus)                                    │
│  ├── ClickHouse (analytics, aggregations)                            │
│  ├── MinIO / S3 (large files, backups)                               │
│  └── Elasticsearch (audit search, log aggregation)                   │
│                                                                      │
│  AI LAYER                                                            │
│  ├── Model Registry (MLflow)                                         │
│  ├── Cloud Inference (GPU cluster)                                   │
│  ├── Edge Inference (ONNX/TensorRT)                                  │
│  ├── Feature Store (Feast)                                           │
│  └── Training Pipeline (Kubeflow)                                    │
│                                                                      │
│  EDGE LAYER                                                          │
│  ├── Edge Agent (per lab) ───────── Rust + ONNX runtime              │
│  ├── Regional Edge Hub ─────────── Aggregation point                 │
│  └── Device Connectors ─────────── ASTM/HL7/BLE                      │
│                                                                      │
│  OBSERVABILITY LAYER                                                 │
│  ├── Prometheus + Grafana ──────── Metrics                           │
│  ├── OpenTelemetry ─────────────── Traces                            │
│  ├── Loki ──────────────────────── Logs                              │
│  ├── Kiali ─────────────────────── Service mesh visualization        │
│  └── Jaeger/Tempo ──────────────── Distributed tracing               │
│                                                                      │
│  SECURITY LAYER                                                      │
│  ├── OPA / CASB ────────────────── Policy engine                    │
│  ├── Vault ─────────────────────── Secret management                 │
│  ├── Cert Manager ──────────────── mTLS certificates                 │
│  └── Falco ────────────────────── Runtime security                   │
│                                                                      │
│  CI/CD LAYER                                                         │
│  ├── GitHub Actions ────────────── CI pipeline                       │
│  ├── ArgoCD ───────────────────── GitOps deployment                  │
│  └── Artifact Registry ────────── Container images                   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 12.2 Component Dependency Graph (simplified)

```
Auth (S1) ← all services depend on it
   ↑
Device Bridge (BC7) → Lab Ops Hub (BC2) → Result Manager (BC4)
   ↑                       ↑                      ↑
Edge Mesh (BC14)    Order Mgmt (BC3) ← Sample Mgmt (BC5)
                        ↑                      ↑
                   Patient Reg. (BC6) ← → Notification (BC10)
                        ↑
                   National HIE (BC13)
                        ↑
                   AI Service (BC9)
                        ↑
                   Stats (BC12)

Financial Engine (BC8) ← depends on: Auth, Orders, Results
Telemedicine (BC15) ← depends on: Auth, Patient, Orders, Results
Marketplace (BC16) ← depends on: Auth, Labs, Financial
```

---

## 13. Technology Radar

### 13.1 Adopt (Proven, use by default)

| Technology | Domain | Why |
|-----------|--------|-----|
| Python 3.13+ | All services | Mature async, pattern matching, performance |
| FastAPI | API services | Proven in monolith, async-native |
| PostgreSQL 16 | Primary data store | Rich types, partitioning, publication |
| SQLAlchemy 2.0+ | ORM | Mature, async support |
| Alembic | Migrations | Proven, immutable migration policy |
| Redis 7 | Cache + Streams | Multi-model, sentinel/cluster |
| Prometheus + Grafana | Metrics | Proven stack |
| Docker Compose | Dev + small prod | Simplicity for MVP |
| GitHub Actions | CI | Already in use |
| Pydantic v2 | Validation | FastAPI-native, performance |
| OpenTelemetry | Tracing | Vendor-neutral, growing adoption |
| Cloudflare | CDN + WAF + DNS | Already in use |

### 13.2 Trial (Promising, evaluate in staging)

| Technology | Domain | Trial Phase | Success Criteria |
|-----------|--------|-------------|-----------------|
| Istio | Service mesh | Phase 2 | <5ms latency overhead, stable in staging |
| Kafka | Event bus | Phase 2 | Better durability than Redis Streams for critical events |
| FHIR R4 (HAPI server) | Interoperability | Phase 2 | Passes all GULA FHIR test cases |
| ClickHouse | Analytics | Phase 2 | 10x faster than PostgreSQL for aggregation queries |
| K8s (k3s/k8s) | Orchestration | Phase 2 | Team can operate without external support |
| ArgoCD | GitOps | Phase 2 | Zero-downtime deployments |
| OPA (Open Policy Agent) | Policy engine | Phase 3 | 1000+ policies with <5ms evaluation |
| gRPC | Inter-service sync | Phase 2 | 2x throughput vs REST for high-volume calls |

### 13.3 Assess (Worth investigating)

| Technology | Domain | Assessment Question | Timeline |
|-----------|--------|-------------------|----------|
| WebAssembly (Wasm) | Edge computing | Can Wasm replace Docker on edge agents? | Phase 3 |
| WASI / WasmEdge | Edge runtime | Performance vs. native Rust/Go? | Phase 3 |
| eRPC (eRPC) | Edge sync | Better than HTTP for unreliable networks? | Phase 3 |
| DuckDB | Embedded analytics | Better than ClickHouse for edge analytics? | Phase 3 |
| Hugging Face TGI | LLM serving | Performance for Arabic clinical LLM? | Phase 3 |
| Feast | Feature store | Worthwhile for AI feature management? | Phase 3 |
| Tempo | Tracing backend | Better than Jaeger for multi-region traces? | Phase 2 |
| Vault | Secrets management | Better than K8s secrets? | Phase 2 |
| Dapr | Runtime for microservices | Reduces Istio complexity? | Phase 3 |

### 13.4 Hold (Not ready; revisit later)

| Technology | Reason to Hold | Revisit |
|-----------|---------------|---------|
| Serverless (Lambda) | Long-running healthcare transactions | 2029+ |
| Blockchain (full) | No clear use case; SSI/VC is better fit | 2031+ |
| Event Sourcing (full ES) | Operational complexity > benefit for most contexts | 2029+ |
| GraphQL | Extra complexity; REST + FHIR covers needs | 2028+ |
| Service Mesh (Istio for all) | Overkill for <10 services; revisit at 15+ | Phase 3 |
| Rust rewrite | High migration cost; Wasm extensions are better | 2030+ |
| Apache Flink | Stream processing not needed yet; Kafka Streams sufficient | 2029+ |
| Web3/DeFi | No healthcare application | Not planned |
| MongoDB/NoSQL | PostgreSQL covers polymorphic data with JSONB | Not planned |
| Machine learning on blockchain | Premature; no clear advantage | 2031+ |

---

## 14. Architecture Decision Records Index

### ADRs Needed for Future State

| ADR ID | Title | Phase | Decision Type | Status |
|--------|-------|-------|---------------|--------|
| ADR-001 | Auth Service: Build vs. Buy (Keycloak/Auth0 vs. custom) | Phase 1 | Technology | Pending |
| ADR-002 | Event Bus Technology: Redis Streams vs. Kafka vs. RabbitMQ | Phase 1 | Technology | Pending |
| ADR-003 | Monolith-to-Service Migration: Strangler Fig vs. Branch by Abstraction | Phase 1 | Process | Pending |
| ADR-004 | Service Mesh: Istio vs. Linkerd vs. No mesh | Phase 2 | Technology | Pending |
| ADR-005 | K8s Distribution: k3s vs. EKS vs. AKS vs. GKE | Phase 2 | Technology | Pending |
| ADR-006 | FHIR Server: HAPI vs. IBM FHIR vs. Custom | Phase 2 | Technology | Pending |
| ADR-007 | CQRS: Which contexts, which technology | Phase 2 | Architecture | Pending |
| ADR-008 | Multi-Region: Active-Active vs. Active-Passive | Phase 3 | Architecture | Pending |
| ADR-009 | Data Mesh: Implementation vs. Stay Monolithic Warehouse | Phase 3 | Architecture | Pending |
| ADR-010 | AI Inference: Cloud vs. Edge split decision | Phase 3 | Architecture | Pending |
| ADR-011 | Observability Stack: Grafana Cloud vs. Self-hosted vs. Hybrid | Phase 2 | Technology | Pending |
| ADR-012 | Secret Management: Vault vs. K8s Secrets vs. Cloud KMS | Phase 2 | Technology | Pending |
| ADR-013 | Telemedicine Architecture: Embedded vs. Standalone Service | Phase 3 | Architecture | Pending |
| ADR-014 | National HIE: Direct FHIR vs. Translation Layer | Phase 2 | Architecture | Pending |
| ADR-015 | Edge Agent Runtime: Python vs. Rust vs. Go vs. Wasm | Phase 2 | Technology | Pending |

---

## Appendix A: Key Architecture Principles (Summary)

1. **Single system of record**: Lab Ops Hub monolith owns core lab data; all services derive from it
2. **Eventual consistency is acceptable** for read models; commands are strongly consistent
3. **Degraded mode is mandatory**: Every service must function (at reduced capacity) when dependent services are down
4. **No shared databases**: Services communicate via API + events, never via DB sharing
5. **Feature flags gate every architectural change**: Rollback is always possible
6. **Observability is a requirement, not an afterthought**: No service ships without logs, metrics, traces, and health
7. **Security is pervasive**: mTLS, encryption at rest, audit trail, policy-based access — not a separate layer
8. **Arabic-first internationalization**: UI defaults to Arabic; RTL support is not optional

## Appendix B: Target Metrics (2030)

| Metric | Target |
|--------|--------|
| Lab count | 5,000+ |
| Countries | 10+ |
| Patient records | 50M+ |
| Monthly results | 10M+ |
| API availability | 99.99% |
| p50 latency | <100ms |
| p99 latency | <500ms |
| Data loss | 0 (guaranteed by outbox pattern) |
| Audit immutability | Cryptographically verified |
| AI model accuracy | >99.5% for critical value detection |
| Security incidents | <1 per year (severe) |
| Deployment frequency | On-demand (multiple per day) |
| MTTR | <15 minutes |

---

*This document represents the target architecture. Actual implementation may vary based on ADR outcomes, team capacity, and market conditions. Review and update quarterly.*

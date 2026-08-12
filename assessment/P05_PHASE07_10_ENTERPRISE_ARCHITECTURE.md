# GULA PROGRAM-05: AI, Healthcare, Deployment & Validation

---

# PHASE 07: ENTERPRISE AI ARCHITECTURE

## AI Platform Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  AI Platform (backend/app/ai_fabric/)                        │
│                                                              │
│  ┌──────────────────┐  ┌──────────────────────────────┐     │
│  │  LLM Gateway     │  │  Model Registry               │     │
│  │                  │  │  Lifecycle: Dev→Staging→Prod  │     │
│  │  8 providers     │  │  Approval workflow            │     │
│  │  Cost routing    │  │  GPU resource tracking        │     │
│  │  Latency routing │  │  A/B testing support          │     │
│  │  Failover        │  │                               │     │
│  │  Token tracking  │  │                               │     │
│  └──────────────────┘  └──────────────────────────────┘     │
│                                                              │
│  ┌──────────────────┐  ┌──────────────────────────────┐     │
│  │  Prompt Engine   │  │  RAG Pipeline                 │     │
│  │                  │  │                               │     │
│  │  Versioned       │  │  Document ingestion → chunk   │     │
│  │  Lifecycle mgmt  │  │  Embedding → pgvector →       │     │
│  │  A/B testing     │  │  Hybrid search (semantic+BM25)│     │
│  │  Template store  │  │  Citation engine              │     │
│  └──────────────────┘  │  Context assembly             │     │
│                        └──────────────────────────────┘     │
│  ┌──────────────────┐  ┌──────────────────────────────┐     │
│  │  Agent Runtime   │  │  Knowledge Graph             │     │
│  │                  │  │                               │     │
│  │  5+ agents (LLM) │  │  Clinical concepts           │     │
│  │  Multi-agent     │  │  Drug interactions           │     │
│  │  orchestration   │  │  Disease ontologies          │     │
│  │  Tool framework  │  │  Code structure (AST)        │     │
│  │  MCP integration │  │  BFS/DFS traversal           │     │
│  └──────────────────┘  └──────────────────────────────┘     │
│                                                              │
│  ┌──────────────────┐  ┌──────────────────────────────┐     │
│  │  AI Safety       │  │  AI Observability            │     │
│  │                  │  │                               │     │
│  │  Human-in-loop   │  │  Prometheus metrics           │     │
│  │  10 blocked ops  │  │  Cost tracking per model      │     │
│  │  Constutition    │  │  Latency (p50/p95/p99)        │     │
│  │  Injection prot. │  │  Error rate monitoring        │     │
│  │  PII redaction   │  │  Persistent audit store      │     │
│  │  Output validator │  │  Grafana dashboards          │     │
│  └──────────────────┘  └──────────────────────────────┘     │
│                                                              │
│  ┌──────────────────┐  ┌──────────────────────────────┐     │
│  │  Evaluation      │  │  Clinical AI                 │     │
│  │  Framework       │  │                               │     │
│  │                  │  │  Differential diagnosis       │     │
│  │  Automated tests │  │  Drug interaction check       │     │
│  │  Bias detection  │  │  Clinical guideline matching  │     │
│  │  Hallucination   │  │  Result interpretation        │     │
│  │  Safety scoring  │  │  Critical value prediction    │     │
│  └──────────────────┘  └──────────────────────────────┘     │
└──────────────────────────────────────────────────────────────┘
```

## LLM Gateway Design

| Feature | Implementation |
|---------|---------------|
| Providers | OpenAI, Anthropic, Gemini, DeepSeek, Ollama, Azure, vLLM, OpenRouter |
| Routing | Cost-optimized, latency-optimized, provider-failover |
| Token Counting | Actual tokenizer (tiktoken, anthropic, etc.) — not `len(text)//4` |
| Streaming | Support all streaming modes (Server-Sent Events) |
| Rate Limiting | Per-provider, per-model, per-tenant request queuing |
| Caching | Response cache for identical prompts (TTL-based) |
| Cost Tracking | Per-request cost, monthly budget, provider cost comparison |

## RAG Pipeline (Production Target)

```
Document ──▶ Chunker (token-aware, overlap)
  │
  ├──▶ Embedding Model (text-embedding-3-small or local)
  │       └──▶ pgvector (persistent, indexed for ANN search)
  │
  ├──▶ BM25 Index (stopword removal, stemming)
  │
  └──▶ Knowledge Graph (clinical entities + relationships)

Query ──▶ Hybrid Search (semantic + keyword + graph)
  │
  ├──▶ Context Assembly (token-budget-aware, relevance-scored)
  │
  ├──▶ LLM Generation (with citations)
  │
  └──▶ Response + Citations + Confidence Score
```

## Agent Architecture (Production Target)

```
Orchestrator Agent
  ├── Clinical Agent (LLM-driven diagnosis support)
  │   Tools: LOINC search, reference range lookup, drug interaction check
  ├── Laboratory Agent (LLM-driven QC analysis)
  │   Tools: Westgard evaluation, delta check, TAT monitoring
  ├── Security Agent (ML + rule hybrid threat detection)
  │   Tools: Pattern matching, anomaly scoring, IP reputation
  ├── Citizen Agent (LLM-driven patient communication)
  │   Tools: Result explanation, appointment scheduling, consent mgmt
  └── Engineering Agent (LLM-driven code analysis)
      Tools: AST parsing, dependency graph, architecture validation
```

## AI Remediation Path (from P04 Gaps)

| # | Action | Timeline |
|---|--------|----------|
| 1 | Add pgvector extension + migration | Week 1-2 |
| 2 | Implement real embedding pipeline | Month 1-2 |
| 3 | Wire agents to LLM reasoning | Month 2-3 |
| 4 | Persist AI audit to database | Month 2 |
| 5 | Build model validation pipeline | Month 2-3 |
| 6 | Add LLM SDKs (openai, anthropic) | Week 1-2 |
| 7 | Integrate RxNorm/DrugBank | Month 3-4 |
| 8 | Add local model inference (vLLM/Ollama) | Month 3-4 |

---

# PHASE 08: HEALTHCARE ENTERPRISE ARCHITECTURE

## Healthcare Domain Coverage

| Domain | Current | Target | Timeline |
|--------|---------|--------|----------|
| Laboratory (LIMS) | ✅ Complete | ISO 15189 certified | Q1 2027 |
| Blood Bank | ✅ Complete | ISBT 128 certified | Q4 2026 |
| Radiology | ✅ Complete | IHE SWF compliant | Q2 2027 |
| Pharmacy | ✅ Complete | Drug interaction DB | Q2 2027 |
| Clinical / EHR | ✅ Partial | Full FHIR R4 clinical resources | Q2 2027 |
| Pathology | ⬜ Minimal | Digital pathology + WSI | Q3 2027 |
| Microbiology | ❌ Missing | Antibiograms, MIC, culture workflows | Q3 2027 |
| Public Health | ✅ Partial | CDC/WHO reporting templates | Q2 2027 |

## FHIR Roadmap (Q4 2026 – Q3 2027)

| Phase | Resources Added | Operations Added |
|-------|----------------|------------------|
| Phase 1 (Q4 2026) | Existing 10 resources | Create, Update, Delete |
| Phase 2 (Q1 2027) | AllergyIntolerance, Condition, MedicationRequest, CarePlan | $export (system), Subscription |
| Phase 3 (Q2 2027) | Immunization, Procedure, DocumentReference, DiagnosticReport (pathology) | SMART on FHIR, Group/$export |
| Phase 4 (Q3 2027) | 10+ additional clinical + public health resources | Patient/$export, Subscription (WebSocket) |

## HL7 v2 Roadmap (Q4 2026 – Q2 2027)

| Phase | Message Types | Target |
|-------|---------------|--------|
| Phase 1 (Q4 2026) | ADT^A01/A04/A08 | Patient admit/update |
| Phase 2 (Q1 2027) | ORM^O01, ADT^A03 | Orders, patient discharge |
| Phase 3 (Q2 2027) | MDM^T02, SIU^S12, MFN^M02 | Documents, scheduling, master files |

## ISO 15189 Certification Roadmap

| Quarter | Milestone |
|---------|-----------|
| Q4 2026 | Gap analysis with accredited body |
| Q1 2027 | Remediation of findings |
| Q2 2027 | Internal audit |
| Q3 2027 | Certification audit |

## Clinical Safety Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  Clinical Safety Framework                                   │
│                                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐  │
│  │ Patient Safety │  │ Clinical Audit │  │ CDS Alerts   │  │
│  │                │  │                │  │              │  │
│  │ Critical value │  │ Hash-chain     │  │ Contra-      │  │
│  │ notification   │  │ immutable log  │  │ indications  │  │
│  │ Delta check    │  │ Every PHI read │  │ Duplicate    │  │
│  │ Auto-validation│  │ Every mutation │  │ orders       │  │
│  │ Westgard QC    │  │ Break glass    │  │ Drug inter.  │  │
│  └────────────────┘  └────────────────┘  └──────────────┘  │
│                                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐  │
│  │ Adverse Events │  │ Quality        │  │ Regulatory   │  │
│  │                │  │ Indicators     │  │ Compliance   │  │
│  │ Structured     │  │                │  │              │  │
│  │ reporting      │  │ 10 ISO 15189   │  │ National MOH │  │
│  │ RCA workflow   │  │ QIs with       │  │ ISO 15189    │  │
│  │ FMEA templates │  │ targets/tracking│  │ CAP          │  │
│  └────────────────┘  └────────────────┘  └──────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

---

# PHASE 09: ENTERPRISE DEPLOYMENT ARCHITECTURE

## Deployment Models

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Single Lab   │  │ Hospital     │  │ Directorate  │  │ National MOH │
│              │  │              │  │              │  │              │
│ 1 server     │  │ 3-5 servers  │  │ 10+ servers  │  │ 50+ servers  │
│ Docker Comp  │  │ Docker Swarm │  │ K8s (minimal)│  │ K8s (HA)     │
│ Local DB     │  │ Patroni HA   │  │ Multi-tenant │  │ Multi-region │
│              │  │ Read replica │  │ Read replicas│  │ Active-act.  │
└──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘
```

## Environment Architecture

```
Development → Sandbox → Testing → QA → UAT → Staging → Production → DR
     │           │         │       │     │       │          │         │
     └───────────┴─────────┴───────┴─────┴───────┴──────────┴─────────┘
                                      Promotion gates at each stage:
                                      - Syntax gate (every PR)
                                      - Migration check (every PR)
                                      - Smoke tests (every merge)
                                      - Integration tests (staging)
                                      - Performance tests (staging)
                                      - Security scan (all stages)
                                      - Clinical safety tests (UAT)
                                      - Load test (pre-prod)
```

## High Availability Architecture

| Component | HA Strategy | RTO | RPO |
|-----------|-------------|-----|-----|
| PostgreSQL | Patroni HA + synchronous replication + auto-failover | 30s | 5s |
| Redis | Sentinel + cluster mode | 10s | 0 (in-memory) |
| Backend API | Horizontal scaling (HPA 2-10 replicas) | 0 | 0 (stateless) |
| Message Queue | RabbitMQ cluster + mirrored queues | 15s | 0 |
| Storage | MinIO HA + bucket replication | 60s | 5s |
| DNS | Cloudflare failover (multi-region) | 60s | N/A |

## Disaster Recovery

| Tier | Configuration | RTO | RPO |
|------|--------------|-----|-----|
| Bronze (Single Lab) | Docker Compose + local backup | 4h | 24h |
| Silver (Hospital) | Patroni HA + same-region standby | 15min | 5s |
| Gold (Directorate) | Multi-region active/passive | 5min | 1s |
| Platinum (National) | Multi-region active/active | 0 | 0 |

## Offline Operation

```
Edge Lab ──▶ Local PostgreSQL + Redis ──▶ Local event store
  │                                            │
  │  (disconnected)                            │
  │                                            │
  └──── Sync when connected ───────────────────┘
        ├── Conflict resolution (CRDT / last-write-wins)
        ├── Incremental sync (changed entities only)
        ├── Batch sync (large datasets overnight)
        └── Verification (checksum comparison)
```

## Deployment Automation

| Tool | Purpose |
|------|---------|
| Docker Compose | Local dev + single-lab production |
| Terraform | Infrastructure provisioning (multi-cloud) |
| Kustomize + Helm | K8s manifest management |
| GitHub Actions | CI/CD pipeline orchestration |
| ArgoCD (future) | GitOps deployment reconciliation |

## Infrastructure as Code Targets

| Cloud | Status | Priority |
|-------|--------|----------|
| AWS (EKS) | ✅ Terraform modules complete | Primary K8s target |
| DigitalOcean | ⬜ Terraform needed | P1 — primary production target |
| On-premise | ⬜ Documentation needed | P2 — government/air-gapped |

---

# PHASE 10: ARCHITECTURE VALIDATION

## Architecture Compliance Checklist

| Check | Criteria | Status |
|-------|----------|--------|
| No domain imports from web framework | domain/ has no `from fastapi import *` | ✅ Designed |
| All mutations go through Command Bus | No direct `db.commit()` in route handlers | ✅ Designed |
| Module boundaries enforced | Modules communicate via events only | ✅ Designed |
| Schema-per-module isolation | Each module in its own DB schema | ✅ Designed |
| API versioning | All public APIs versioned | ✅ Designed |
| Audit coverage | Every PHI access logged | ✅ Designed |
| Tenant isolation | Query-level + schema-level + pool-level | ✅ Designed |
| CQRS separation | Write models ≠ read models | ✅ Designed |
| Eventual consistency | Events propagate across module boundaries | ✅ Designed |
| Self-healing | Circuit breaker + auto-repair + adaptive | ✅ Designed |
| Offline support | Local event store + conflict resolution | ✅ Designed |

## Clinical Safety Review

| Item | Status |
|------|--------|
| Patient data never exposed without auth | ✅ Designed |
| Critical results always notify | ✅ Designed |
| Audit trail immutable | ✅ Designed (SHA-256 chain) |
| Consent required for secondary use | ✅ Designed |
| Break glass logged and time-limited | ✅ Designed |
| Orders locked after validation | ✅ Designed |
| Result modification creates amendment | ✅ Designed |
| Error budgets for clinical latency | ✅ Designed (<500ms p99) |

## Security Architecture Review

| Control | Status |
|---------|--------|
| Zero Trust — every request verified | ✅ Designed |
| MFA enforced for PHI access | ✅ Designed |
| RBAC + ABAC combined | ✅ Designed |
| Encryption at rest + in transit | ✅ Designed |
| Secrets auto-rotated via Vault | ✅ Designed |
| Immutable audit chain | ✅ Designed |
| Threat detection (IDS + SIEM) | ✅ Designed |
| Incident response runbook | ⬜ P1 |
| Penetration testing schedule | ⬜ P1 |
| Bug bounty program | ⬜ P3 |

## Implementation Readiness

**Modules ready for extraction:** Audit, Identity, Notifications, Configuration (kernel services already well-designed)

**Modules needing extraction:** Laboratory (orders/results/QC/specimens/equipment), Patients (MPI), Quality

**New modules to create:** Public Health (formal bounded context), Microbiology, Pathology

**Total effort estimate:** ~1,750 hours (from P04 gap analysis)

## Architecture Governance

| Practice | Frequency |
|----------|-----------|
| ADR review | Weekly |
| Architecture compliance scan | Every PR (automated) |
| Dependency graph validation | Every PR (automated) |
| Module boundary enforcement | Every PR (automated) |
| Architectural review board | Monthly |
| Technology radar update | Quarterly |

---

## Final Deliverables

| Deliverable | Status |
|-------------|--------|
| Enterprise Architecture Blueprint | ✅ APPROVED |
| Platform Core Blueprint | ✅ APPROVED |
| Domain Architecture (30 domains) | ✅ APPROVED |
| Integration Architecture | ✅ APPROVED |
| Enterprise Data Blueprint | ✅ APPROVED |
| Enterprise Security Blueprint | ✅ APPROVED |
| Enterprise AI Blueprint | ✅ APPROVED |
| Healthcare Enterprise Blueprint | ✅ APPROVED |
| Enterprise Deployment Blueprint | ✅ APPROVED |
| Architecture Validation | ✅ APPROVED |

---

## PROGRAM-05: COMPLETE

**Authorizing PROGRAM-06: Platform Core Implementation**

The target architecture transforms GULA from a monolithic LIMS into a modular, event-driven, AI-native healthcare platform. Key architectural shifts:

1. **Monolith → Module System** — Every capability is a pluggable module with standard structure
2. **Direct DB Access → CQRS** — Commands go through pipeline; queries go through optimized read models
3. **Shared Schema → Schema-per-module** — Database-level bounded context isolation
4. **Procedural AI → Production AI** — RAG with pgvector, LLM-powered agents, persistent observability
5. **LIMS-only → National Healthcare Platform** — FHIR + HL7 + ISO 15189 + Public Health interoperability

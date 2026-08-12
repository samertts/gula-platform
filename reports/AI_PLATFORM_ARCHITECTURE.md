# SOVEREIGN AI PLATFORM (SAP) — ARCHITECTURE

**Design Authority:** Chief AI Architect, Chief Security Officer
**Status:** PROPOSED
**Version:** 1.0.0

---

## EXECUTIVE SUMMARY

The Sovereign AI Platform (SAP) is the unified AI infrastructure for GULA, designed for **complete AI vendor independence**. No business logic depends on any single AI provider. Models can be swapped, added, or removed without changing application code.

**Core Principles:**
1. **AI Vendor Independence** — Abstract routing layer decouples business logic from model providers
2. **Data Sovereignty** — PHI/PII never leaves controlled infrastructure
3. **Offline-First** — Local models handle critical operations without internet
4. **Clinical Safety** — Human-in-the-loop for diagnostic decisions
5. **Zero Trust** — Every AI operation authenticated, authorized, audited

---

## ARCHITECTURE OVERVIEW

```
┌──────────────────────────────────────────────────────────────┐
│                    GULA APPLICATIONS                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │Citizen   │ │Doctor    │ │Lab       │ │Ministry  │        │
│  │Portal    │ │Dashboard │ │Dashboard │ │Dashboard │        │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘        │
│       └────────────┴────────────┴────────────┴──────┘        │
│                          │                                    │
│                     ┌────▼────┐                              │
│                     │  AI     │                              │
│                     │ Gateway │                              │
│                     └────┬────┘                              │
│                          │                                    │
│                     ┌────▼────┐                              │
│                     │ Model   │                              │
│                     │ Router  │                              │
│                     └────┬────┘                              │
│                          │                                    │
│               ┌──────────┼──────────┐                        │
│               ▼          ▼          ▼                        │
│        ┌──────────┐ ┌──────────┐ ┌──────────┐               │
│        │Cloud     │ │On-Prem   │ │Edge      │               │
│        │Models    │ │Models    │ │Models    │               │
│        └──────────┘ └──────────┘ └──────────┘               │
│               │          │          │                        │
│               ▼          ▼          ▼                        │
│        ┌─────────────────────────────────────┐               │
│        │      Sovereign Connector Gateway    │               │
│        │      (All external AI via SCG)      │               │
│        └─────────────────────────────────────┘               │
└──────────────────────────────────────────────────────────────┘
```

---

## COMPONENT SPECIFICATIONS

### 1. AI Gateway

**Purpose:** Single entry point for all AI operations in the platform.

| Aspect | Specification |
|--------|---------------|
| Protocol | gRPC (internal) + REST (external) |
| Auth | Platform JWT + SCG-signed token |
| Rate limiting | Per-tenant, per-model, per-operation |
| Cost tracking | Per-request cost accumulation |
| Latency SLAs | Clinical: <500ms, Analytical: <5s, Batch: <60s |
| Safety layer | All requests pass through safety engine |

**Endpoint Categories:**
```yaml
endpoints:
  clinical:
    - interpret_result: clinical_interpretation
    - suggest_diagnosis: differential_diagnosis
    - flag_critical: alert_generation
    - verify_medication: drug_interaction_check
  operational:
    - optimize_schedule: workflow_optimization
    - predict_demand: resource_forecasting
    - detect_anomaly: quality_control
  analytical:
    - analyze_trends: population_health
    - detect_outbreak: epidemiological_surveillance
    - generate_report: automated_reporting
  citizen:
    - answer_query: health_information
    - triage_symptom: symptom_assessment
    - summarize_record: patient_summary
```

### 2. Model Router

**Purpose:** Automatically select the optimal model for each request.

**Routing Dimensions:**
| Dimension | Values | Weight |
|-----------|--------|--------|
| Clinical sensitivity | standard, sensitive, phi, critical | High |
| Latency requirement | realtime, interactive, batch | High |
| Cost budget | low, medium, high, unlimited | Medium |
| Offline requirement | online_only, offline_capable, offline_required | Medium |
| Reasoning depth | simple, moderate, complex, deep | Medium |
| Language | ar, en, ku, tr, sy | High |
| Modality | text, vision, audio, multimodal | High |
| Security level | standard, high_security, air_gapped | High |

**Routing Algorithm:**
```
1. Filter: Remove models not meeting hard requirements (air_gapped, offline, security)
2. Score: Weighted scoring against routing dimensions
3. Cost check: Verify within tenant budget
4. Fallback chain: Define ordered fallback (e.g., local → regional → cloud)
5. Select: Highest scoring model within budget
```

**Example Routing Table:**
```yaml
routing:
  clinical_interpretation:
    # PHI data — prefer local
    primary: ollama:llama3-70b
    fallback: ollama:qwen2-72b
    offline_only: true
  citizen_query:
    # Public health info — cost-optimized
    primary: deepseek:deepseek-chat
    fallback: mistral:mixtral-8x7b
    budget: low
  outbreak_detection:
    # Population-level — accuracy preferred
    primary: anthropic:claude-opus
    fallback: openai:gpt-4o
    budget: high
```

### 3. Prompt Router

**Purpose:** Route prompts through safety, redaction, and optimization pipeline.

**Pipeline:**
```
Raw Prompt → PII Detection → PHI Detection → Redaction
  → Policy Check → Prompt Optimization → Enriched Prompt
  → [Model Execution] → Response Validation
  → Redaction Reversal → Purity Check → Audited Response
```

**Prompt Templates:**
```yaml
templates:
  clinical_interpretation:
    system: |
      You are a clinical laboratory AI assistant for {lab_name}.
      Analyze the following lab results and provide:
      1. Interpretation of each abnormal value
      2. Potential clinical significance
      3. Recommendations for follow-up
      IMPORTANT: This is for physician reference only.
      Never provide a diagnosis without physician confirmation.
    user: |
      Patient: {age}y/o {gender}
      Results:
      {results_table}
```

### 4. Context Manager

**Purpose:** Manage conversation context, memory, and knowledge retrieval.

| Feature | Specification |
|---------|---------------|
| Short-term memory | In-memory, last 10 exchanges |
| Long-term memory | Vector DB (Qdrant/Pgvector), auto-summarized |
| Patient context | FHIR-based, auto-attached for clinical queries |
| Lab context | Current lab configuration, test catalog |
| User context | Role, permissions, language preference |
| Session timeout | 30 minutes inactivity |
| Context window | Configurable per model (4K-200K tokens) |

### 5. RAG Engine

**Purpose:** Retrieve relevant knowledge for AI model context.

**Knowledge Sources:**
| Source | Type | Update Frequency |
|--------|------|-----------------|
| Medical literature | PubMed, guidelines | Monthly |
| Lab reference ranges | Internal | Real-time |
| Clinical guidelines | WHO, national | Quarterly |
| Drug interactions | DrugBank | Weekly |
| Government policies | National | On change |
| Training manuals | Internal | On change |

**Chunking Strategy:**
- Medical text: 512 tokens with 128 overlap
- Lab values: Exact (no chunking)
- Guidelines: Section-based (by heading)
- Drug data: Per-drug chunks

**Retrieval Strategy:**
- Clinical queries: Dense retrieval (bi-encoder) + keyword (BM25)
- Operational queries: Keyword (BM25) only
- Hybrid with reciprocal rank fusion
- Top-k: 5 for clinical, 3 for operational

### 6. Safety Engine

**Purpose:** Prevent harmful, inaccurate, or unsafe AI outputs.

| Check | Method | Action |
|-------|--------|--------|
| Prompt injection | Classifier + regex patterns | Block, log, alert |
| Jailbreak detection | Classifier (BERT-based) | Block, log, alert |
| Hallucination detection | Consistency check + confidence scoring | Flag for review |
| PII/PHI leakage | Named entity recognition + regex | Redact before output |
| Output validation | Schema check + policy enforcement | Block malformed |
| Clinical safety | Rule-based + confidence threshold | Require human approval |
| Bias detection | Demographic parity check | Flag for review |

**Confidence Scoring:**
```yaml
thresholds:
  clinical_diagnosis:
    high_confidence: 0.95  # Auto-accept with physician notification
    medium_confidence: 0.80 # Flag for physician review
    low_confidence: 0.00   # Require explicit human approval
  lab_interpretation:
    high_confidence: 0.90
    medium_confidence: 0.70
    low_confidence: 0.00
  citizen_query:
    high_confidence: 0.85
    medium_confidence: 0.60
    low_confidence: 0.00
```

### 7. Model Registry

**Purpose:** Source of truth for all available models.

**Model Entry Schema:**
```json
{
  "model_id": "ollama:llama3-70b",
  "provider": "ollama",
  "name": "Llama 3 70B",
  "version": "4.0",
  "capabilities": ["text", "reasoning", "coding"],
  "languages": ["en", "ar"],
  "context_window": 8192,
  "pricing": {"input": 0, "output": 0, "currency": "USD"},
  "latency_p50": 1200,
  "latency_p99": 5000,
  "quality_score": 0.92,
  "security_level": "air_gapped",
  "status": "active",
  "deployment": {
    "type": "local",
    "endpoint": "http://ollama:11434",
    "requires_gpu": true,
    "min_vram_gb": 16
  },
  "routing_weights": {
    "clinical": 0.9,
    "reasoning": 0.85,
    "arabic": 0.7,
    "coding": 0.8
  },
  "fallback_models": ["ollama:qwen2-72b", "ollama:mistral-7b"]
}
```

### 8. Agent Runtime

**Purpose:** Execute AI agents with tool access, state management, and safety controls.

**Agent Types:**
| Agent | Capabilities | Tool Access |
|-------|-------------|-------------|
| Citizen Agent | Health queries, appointment scheduling, result explanation | Patient portal (read-only), appointment system |
| Doctor Agent | Clinical decision support, result interpretation | EMR (read), lab results, drug database |
| Lab Agent | QC monitoring, workflow optimization | LIMS, QC data, device telemetry |
| Radiology Agent | Image analysis, report drafting | PACS (read), DICOM, reporting |
| Nursing Agent | Care plan suggestions, vital sign analysis | Nursing records, care plans |
| Pharmacy Agent | Drug interaction check, dispense verification | Pharmacy system (read), drug database |
| Hospital Agent | Bed management, resource optimization | Hospital management system |
| Ministry Agent | Population health analytics, outbreak detection | National health data (aggregate only) |
| Security Agent | Threat detection, anomaly identification | Security logs, audit data |
| Research Agent | Data analysis, cohort identification | De-identified clinical data |

**Agent Execution Flow:**
```
1. Intent received → validate against agent capabilities
2. Context assembled (user, patient, lab, conversation history)
3. Policy check → allowed operations
4. Tool discovery → available tools matching intent
5. Prompt construction with context + tool descriptions
6. Model execution (via Model Router)
7. Tool calls routed through SCG
8. Response validation (safety, accuracy, policy)
9. Human approval if required (confidence below threshold)
10. Response delivery + audit logging
```

### 9. Model Benchmark

**Purpose:** Continuously evaluate model quality across healthcare tasks.

**Benchmark Categories:**
| Category | Metrics | Frequency |
|----------|---------|-----------|
| Clinical accuracy | F1, precision, recall on lab interpretation | Daily |
| Hallucination rate | % of verified false statements | Per-deployment |
| Arabic quality | BLEU, chrF for Arabic clinical text | Weekly |
| Latency | p50, p95, p99 response times | Continuous |
| Cost efficiency | Cost per correct interpretation | Daily |
| Safety compliance | % of blocked harmful outputs | Continuous |
| User satisfaction | Rating (1-5) from feedback loop | Per-interaction |

**Benchmark Datasets:**
- 1,000 annotated lab result interpretations
- 500 clinical Q&A pairs (Arabic + English)
- 200 drug interaction queries
- 100 outbreak detection scenarios
- 50 prompt injection attempts

### 10. Cost Manager

**Purpose:** Track, optimize, and control AI spending.

| Feature | Specification |
|---------|---------------|
| Per-tenant budget | Monthly cap (configurable) |
| Per-model cost tracking | Real-time accumulation |
| Cost optimization | Route to cheaper model when quality allows |
| Budget alerts | 50%, 80%, 90%, 100% thresholds |
| Cost allocation | By tenant, department, user |
| Invoice generation | Monthly usage report |
| Token accounting | Input + output token tracking |

**Cost Optimization Strategies:**
1. **Smart routing** — Use cheaper model when confidence is acceptable
2. **Response caching** — Cache identical queries (TTL based on volatility)
3. **Batching** — Combine non-urgent requests
4. **Local-first** — Prefer local models for simple operations
5. **Context pruning** — Minimize context window usage
6. **Response compression** — Request shorter responses where acceptable

---

## LOCAL AI DEPLOYMENT

### Supported Configurations

| Tier | Hardware | Models | Throughput |
|------|----------|--------|------------|
| Edge | Raspberry Pi 5 / Jetson Nano | Qwen2:0.5b, Phi-3:mini | 1-5 req/min |
| Clinic | NUC / Mini PC (32GB RAM) | Llama 3:8b, Mistral:7b | 10-50 req/min |
| Hospital | Single GPU (A100 40GB) | Llama 3:70b, Qwen2:72b | 50-200 req/min |
| Regional | Multi-GPU cluster | Full model suite | 500-2000 req/min |
| National | Data center cluster | All models | 2000+ req/min |

### Air-Gapped Deployment
- No external network access required
- All models pre-loaded during deployment
- Model updates via physical media or signed packages
- Audit logs queued for periodic sync
- SCG operates in local-only mode

---

## AI GOVERNANCE

| Control | Implementation |
|---------|---------------|
| Model approval | New models require clinical safety review |
| Prompt audit | All prompts logged (redacted for PHI) |
| Output review | Random 5% sampling for quality audit |
| Bias monitoring | Monthly demographic bias analysis |
| Explainability | Feature attribution for clinical decisions |
| Human oversight | Configurable human-in-the-loop thresholds |
| Version control | Model versions pinned for reproducibility |
| Compliance | GDPR, HIPAA, national health data regulations |

---

## FALLBACK & DISASTER RECOVERY

| Scenario | Response |
|----------|----------|
| Primary model unavailable | Automatic fallback (defined per model) |
| All cloud models unavailable | Local models only mode |
| All models unavailable | Safe degradation — no AI features |
| GPU failure | CPU inference (slower but functional) |
| Network partition | Queue requests, process when reconnected |
| Data center outage | Active-passive replica in second region |

---

## IMPLEMENTATION ROADMAP

| Phase | Components | Timeline |
|-------|------------|----------|
| **P1** | AI Gateway, Model Router (local only), Safety Engine, Audit | Month 1-2 |
| **P2** | Cloud model routing, Prompt Router, Context Manager | Month 3-4 |
| **P3** | RAG Engine, Knowledge Base, Cost Manager | Month 5-6 |
| **P4** | Agent Runtime, Tool Framework, SCG integration | Month 7-8 |
| **P5** | Model Benchmark, Quality Dashboard, Clinical review workflow | Month 9-10 |
| **P6** | Full agent ecosystem, Multi-region, Air-gapped validation | Month 11-12 |

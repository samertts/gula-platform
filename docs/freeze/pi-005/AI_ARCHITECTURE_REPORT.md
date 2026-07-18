# AI Architecture Report — National AI, Decision Intelligence & Digital Twin Platform

**PI-005 | GULA Platform v2.1.0**  
**Date:** 2026-07-16  
**Status:** FINAL

---

## 1. Executive Summary

The National AI & Intelligence Fabric (NAIF) is a unified, multi-agent AI layer embedded in the GULA Platform. It provides clinical decision support, operational intelligence, population health surveillance, citizen engagement, and digital twin simulation through a common AI gateway, RAG pipeline, knowledge graph, and agent registry.

NAIF reuses shared infrastructure from `shared.ai`, `app.kernel.ai_runtime`, `app.ai.guardrails`, `app.ai.approval`, `app.ai.sandbox`, and `app.knowledge_graph`, while exposing a clean REST API via `/ai/fabric/*` routes.

---

## 2. Multi-Agent AI Fabric Architecture

### 2.1 Agent System

The agent system (`backend/app/ai_fabric/agents/`) implements a registry-based multi-agent architecture:

| Agent | File | Domain | Task Types |
|---|---|---|---|
| **ClinicalAgent** | `clinical_agent.py` | Clinical decision support | clinical, interpretation, cds, diagnosis |
| **LaboratoryAgent** | `laboratory_agent.py` | Laboratory operations | laboratory, lab, qc, delta, workload |
| **CitizenAgent** | `citizen_agent.py` | Patient engagement | citizen, patient, health_query, education, wellness |
| **SecurityAgent** | `security_agent.py` | Security monitoring | security, intrusion, access_control, monitoring |
| **EngineeringAgent** | `engineering_agent.py` | DevOps & architecture | engineering, architecture, code, devops, config |

All agents inherit from `AIAgent` (`agents/base.py`), which provides:
- **Lifecycle management** (INITIALIZED → READY → RUNNING → ERROR → SHUTDOWN)
- **AgentMemory** with short-term (dict) and long-term (namespaced list) storage
- **Tool registration** via `AgentTool` with typed parameters and approval requirements
- **Heartbeat** and metrics reporting

### 2.2 Agent Registry

`AgentRegistry` (`agents/registry.py`) is a singleton that manages all agent instances:
- Registration and unregistration
- `find_for_task(task_type)` — dispatches to the correct agent
- `initialize_all()` and `shutdown_all()` — lifecycle orchestration
- Heartbeat collection and statistics

```python
# Integration point: backend/app/ai_fabric/integration.py
def _register_default_agents(registry: AgentRegistry) -> None:
    registry.register(ClinicalAgent())
    registry.register(LaboratoryAgent())
    registry.register(SecurityAgent())
    registry.register(EngineeringAgent())
    registry.register(CitizenAgent())
```

### 2.3 Agent Lifecycle

```
INITIALIZED → READY → RUNNING → (completes) → IDLE
                  ↓                    ↓
              SHUTDOWN              ERROR
```

---

## 3. AI Gateway and Model Routing

### 3.1 Provider Architecture

The `AIGateway` (`gateway.py`) provides a unified interface to multiple AI providers with automatic failover and cost optimization:

| Provider | Type | Models | Cost/1K Input | Cost/1K Output |
|---|---|---|---|---|
| **OpenAI** | `openai` | gpt-4o, gpt-4o-mini, text-embedding-3-small | $0.0025 | $0.01 |
| **Anthropic** | `anthropic` | claude-3-opus, claude-3-sonnet | $0.003 | $0.015 |
| **Gemini** | `gemini` | gemini-2.0-flash, gemini-2.0-pro | $0.0005 | $0.0015 |
| **Ollama** (local) | `ollama` | llama3.2:1b, llama3.1:8b, mistral:7b | $0 | $0 |
| **vLLM** (local) | `vllm` | gula-medical-7b | $0 | $0 |
| **Azure** | `azure` | — | $0.0025 | $0.01 |
| **OpenRouter** | `openrouter` | — | $0.001 | $0.003 |
| **DeepSeek** | `deepseek` | deepseek-chat, deepseek-coder | $0.0005 | $0.002 |

### 3.2 Failover Strategy

`FailoverStrategy` implements automatic provider failover:
1. Select primary provider based on model availability and latency
2. On failure, fall through fallback providers (up to 2 retries)
3. Returns error only if all providers fail

### 3.3 Cost Optimization

`CostOptimizer` tracks:
- Total spend and average cost per request
- Cheapest provider selection for a given model
- Real-time cost estimation based on token counts

### 3.4 Request Lifecycle

```python
request = InferenceRequest(prompt="...", model="gpt-4o-mini", temperature=0.3)
response = gateway.chat(request)
# → ProviderRouter.select_for_model()
# → FailoverStrategy.execute()
# → AIClient.chat()
# → CostOptimizer.record_usage()
# → AIObserver.record_inference()
```

---

## 4. RAG Implementation and Knowledge Graph

### 4.1 RAG Engine

The `RAGEngine` (`rag.py`) implements a production-grade retrieval-augmented generation pipeline:

**Components:**
- `VectorStore` — In-memory vector store with cosine similarity search, supporting pgvector/qdrant/milvus backends
- `BM25Index` — Keyword search using BM25 ranking algorithm
- `SemanticSearch` — Hybrid search fusing semantic (vector) and keyword results
- `CitationEngine` — Generates structured citations with relevance scoring
- `ContextBuilder` — Builds token-budget-aware LLM context from retrieved documents

**Search Modes:** `SEMANTIC`, `KEYWORD`, `HYBRID`

**Query Flow:**
```
query → embed → vector search → (optional) keyword search → fusion → context building → LLM → citations
```

### 4.2 Knowledge Graph

The `KnowledgeGraphService` (`knowledge_graph.py`) wraps `app.knowledge_graph.engine.KnowledgeGraphEngine`:

**Entity Types:** patient, laboratory, test, result, order, disease, medication, observation, physician, facility, protocol, instrument

**Relationship Types:** has_result, ordered_by, diagnosed_with, treated_with, correlated_with, follows, precedes, associated_with, located_at, performed_by, derived_from

**Capabilities:**
- `GraphQuery` — Entity lookup, related entity traversal, path finding, search
- `GraphBuilder` — Entity/relationship creation, bulk ingestion from lab results
- Traversal strategies: BFS, DFS, shortest path
- Snapshot and graph integrity verification

---

## 5. Local AI and Edge Inference

### 5.1 Local AI Engine

`LocalAIEngine` (`local_ai.py`) manages on-premise GPU inference:

- NVIDIA GPU detection via `nvidia-smi`
- Job scheduling with concurrency limits (configurable pool size)
- GPU selection based on utilization
- CPU-only fallback when no GPU detected

### 5.2 Model Registry

`ModelRegistry` (extends `KernelModelRegistry`) tracks model lifecycle:
- `DEVELOPMENT` → `STAGING` → `PRODUCTION` → `DEPRECATED` → `RETIRED`
- Model approval gates (only production models are auto-approved)
- Capability tracking (context length, streaming support, structured output)

### 5.3 Embedding and Reranking

- `EmbeddingService` — Generates embeddings using shared AI provider
- `RerankingService` — Cross-encoder reranking via LLM relevance scoring

---

## 6. Observability

### 6.1 AI Observer

`AIObserver` (`observability.py`) is a singleton that records every AI inference:

**Metrics tracked per request:**
- Model, provider, user_id, endpoint
- Latency (ms), input/output tokens, cost
- Success/error status

**Aggregated metrics:**
- Request volume, error rate, latency percentiles (p50, p95, p99)
- Total tokens, total cost, average cost per request
- Usage breakdown by model
- Daily usage history (30-day window)

### 6.2 Health Monitoring

```
GET /ai/fabric/health → status + provider count + agent stats + vector store info
```

---

## 7. AI SDK and Service Integration

### 7.1 UnifiedAISDK

The `UnifiedAISDK` (`sdk.py`) provides a single entry point to all AI capabilities:

```python
sdk = UnifiedAISDK()
response = await sdk.chat("Analyze this lab result")
embeddings = await sdk.embed([text1, text2])
health = sdk.get_health()
```

### 7.2 Specialized SDKs

- **AgentSDK** — Context creation, agent execution, task routing
- **RAGSDK** — Query and index documents

### 7.3 REST API Routes

All AI capabilities are exposed via FastAPI routes in `routes.py`:

| Endpoint | Method | Purpose |
|---|---|---|
| `/ai/fabric/chat` | POST | General AI chat |
| `/ai/fabric/rag/query` | POST | RAG-powered query |
| `/ai/fabric/rag/index` | POST | Index documents |
| `/ai/fabric/knowledge-graph/*` | GET | Knowledge graph operations |
| `/ai/fabric/clinical/*` | POST | Clinical analysis, summarization, drug interactions |
| `/ai/fabric/lab/*` | POST | Delta check, critical detection, QC, workload |
| `/ai/fabric/public-health/*` | POST/GET | Surveillance, outbreak detection |
| `/ai/fabric/governance/*` | POST/GET | Prompt registry, model approval, evaluation |
| `/ai/fabric/observability/*` | GET | Usage statistics, errors, model performance |
| `/ai/fabric/security/*` | POST | Input inspection, output validation, PII redaction |
| `/ai/fabric/agents/*` | GET/POST | Agent listing, execution, initialization |

### 7.4 Integration Point

`initialize_ai_fabric()` in `integration.py` bootstraps the entire AI fabric:

1. Initializes the AI Gateway with configured providers
2. Registers and initializes all 5 default agents
3. Mounts the AI fabric router on the FastAPI app
4. Returns health status with agent and provider counts

---

## 8. Digital Twin Integration

The simulation engine (`backend/app/simulation/engine.py`) powers four twin types:

- **HospitalTwin** — Patient flow, bed occupancy, resource utilization
- **LaboratoryTwin** — Test volume, TAT prediction, equipment utilization
- **DirectorateTwin** — Multi-facility coordination, disease scenario modeling
- **NationalHealthTwin** — Outbreak modeling (SIR), population health metrics

Statistical methods used: SMA, EMA, linear regression, random walk, SIR compartmental model, seasonal factor decomposition.

**API:** `/simulation/*` routes with twin CRUD, simulation execution, prediction, and dashboard.

---

## 9. File Reference

| File | Description |
|---|---|
| `backend/app/ai_fabric/base.py` | Core data types (InferenceRequest, InferenceResponse, AIServiceProvider) |
| `backend/app/ai_fabric/gateway.py` | AI Gateway with provider routing, failover, cost optimization |
| `backend/app/ai_fabric/rag.py` | RAG engine (vector store, BM25, semantic search, citations) |
| `backend/app/ai_fabric/knowledge_graph.py` | Knowledge graph service |
| `backend/app/ai_fabric/local_ai.py` | Local inference engine, model registry, embedding service |
| `backend/app/ai_fabric/agents/base.py` | Agent base class, memory, tools, lifecycle |
| `backend/app/ai_fabric/agents/registry.py` | Agent registry singleton |
| `backend/app/ai_fabric/agents/*.py` | Five specialized agents |
| `backend/app/ai_fabric/enums.py` | AI enums (providers, capabilities, statuses) |
| `backend/app/ai_fabric/observability.py` | Usage tracking and monitoring |
| `backend/app/ai_fabric/sdk.py` | Unified AI SDK |
| `backend/app/ai_fabric/routes.py` | REST API routes |
| `backend/app/ai_fabric/integration.py` | FastAPI integration point |
| `backend/app/ai_fabric/clinical.py` | Clinical decision support, drug interaction, summarization |
| `backend/app/ai_fabric/security.py` | Prompt injection protection, PII redaction, output validation |
| `backend/app/ai_fabric/governance.py` | Governance (prompts, model approval, evaluation, constitution) |
| `backend/app/ai_fabric/laboratory_intelligence.py` | Lab intelligence (delta check, critical results, QC, workload) |
| `backend/app/ai_fabric/public_health.py` | Disease surveillance, outbreak detection, population analytics |
| `backend/app/simulation/engine.py` | Digital twin engine (4 twin types) |
| `backend/app/simulation/models.py` | Simulation ORM models |
| `backend/app/simulation/routes.py` | Simulation REST API |
| `backend/app/clinical/cds/models.py` | Clinical CDS ORM models |
| `ai/ai_service.py` | Legacy AI gateway |
| `ai/clinical/clinical_ai/clinical_engine.py` | Clinical rules engine |
| `ai/lab_business_ai/demand_prediction.py` | Demand prediction |
| `ai/population_health.py` | Population health statistics |
| `ai/anomaly_detection.py` | Anomaly detection |

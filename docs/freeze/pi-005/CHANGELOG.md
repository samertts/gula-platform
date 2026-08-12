# Changelog — National AI, Decision Intelligence & Digital Twin Platform

**Platform:** GULA Platform  
**Component:** National AI & Intelligence Fabric (NAIF) + Digital Twin Engine  
**Version:** 2.1.0

---

## [2.1.0] — 2026-07-16 — PI-005 Release

### Added

#### AI Fabric (`backend/app/ai_fabric/`)
- **Multi-Agent System** — 5 specialized AI agents (Clinical, Laboratory, Citizen, Security, Engineering)
- **AI Gateway** — 9 provider support (OpenAI, Anthropic, Gemini, Ollama, vLLM, Azure, OpenRouter, DeepSeek, HuggingFace)
- **Provider Failover** — Automatic retry across fallback providers with configurable max retries
- **Cost Optimizer** — Per-request cost tracking, cheapest-provider selection, cumulative spend
- **RAG Engine** — Hybrid semantic+keyword retrieval, BM25 indexing, citation engine, context builder
- **Knowledge Graph** — Entity/relationship management, graph traversal, dependency analysis
- **Local AI Engine** — GPU detection, job scheduling, CPU-only fallback
- **Model Registry** — Full lifecycle management (development → staging → production → deprecated → retired)
- **Embedding Service** — Text embedding generation with configurable dimensions
- **Reranking Service** — Cross-encoder relevance scoring
- **Unified SDK** — Single entry point for all AI capabilities
- **Agent SDK** — Context management, task routing, agent execution
- **RAG SDK** — Document indexing and querying

#### Clinical AI (`backend/app/ai_fabric/clinical.py`)
- **ClinicalDecisionSupport** — Result analysis, differential diagnosis, guideline checking
- **DrugInteractionDetector** — Drug-drug interaction detection, prescription analysis, allergy checking
- **ClinicalSummarizer** — Narrative summary generation, longitudinal history summaries

#### Governance (`backend/app/ai_fabric/governance.py`)
- **PromptRegistry** — Version-controlled prompt management with full lifecycle
- **ModelApproval** — Gated model approval workflow (submit → evaluate → approve/reject)
- **EvaluationFramework** — 7-dimension model evaluation (accuracy, bias, safety, hallucination, toxicity, fairness, robustness)
- **AIConstitution** — 7 enforceable ethical articles for AI governance

#### Security (`backend/app/ai_fabric/security.py`)
- **AIFirewall** — Input/output security with defense-in-depth
- **PromptInjectionProtector** — 12 injection pattern categories
- **PIIProtector** — 8 PII types detection, redaction, masking
- **OutputValidator** — Blocked phrases, confidentiality, schema validation

#### Laboratory Intelligence (`backend/app/ai_fabric/laboratory_intelligence.py`)
- **DeltaChecker** — Configurable delta thresholds, batch checking
- **CriticalResultDetector** — Per-test critical thresholds, batch detection
- **QCAnalyzer** — Full Westgard rules (1-2s, 1-3s, 2-2s, R-4s, 4-1s, 10x)
- **WorkloadPredictor** — Daily/TAT prediction, peak hour analysis, staffing recommendations

#### Public Health (`backend/app/ai_fabric/public_health.py`)
- **DiseaseSurveillance** — Baseline-relative surveillance with z-score alerting (5 levels)
- **OutbreakDetector** — Cluster detection, geographic spread analysis
- **PopulationHealthAnalytics** — Trend analysis, disease prevalence, immunization coverage

#### Observability (`backend/app/ai_fabric/observability.py`)
- **AIObserver** — Per-request tracking, latency percentiles (p50/p95/p99), cost aggregation
- **Daily usage** — 30-day cost and volume trends, model breakdown

#### Digital Twin Engine (`backend/app/simulation/`)
- **DigitalTwinEngine** — 4 twin types: Hospital, Laboratory, Directorate, National Health
- **SIR Model** — Compartmental infectious disease modeling
- **Capacity Planning** — Automated capacity recommendations with priority scoring
- **Health Monitoring** — Twin health scoring (0-100), data freshness, prediction accuracy
- **Simulation Snapshots** — State capture for reproducibility
- **Prediction Tracking** — Actual vs. predicted value comparison, MAPE-based accuracy

#### API Routes (`backend/app/ai_fabric/routes.py`)
- 30+ REST endpoints covering all AI capabilities
- Full CRUD for governance, agents, RAG, knowledge graph
- Clinical analysis, drug interaction, lab intelligence
- Public health surveillance, outbreak detection
- Security inspection, PII redaction
- Observability statistics, daily usage

### Changed

- N/A — Initial versioned release of AI platform components

### Fixed

- N/A — Initial versioned release

### Deprecated

- Legacy `ai/ai_service.py` gateway — replaced by `AIGateway` with multi-provider support
- Legacy `ai/clinical/clinical_ai/clinical_engine.py` — replaced by `ClinicalDecisionSupport`
- Legacy `ai/anomaly_detection.py` — replaced by `DeltaChecker` with configurable thresholds

### Security

- PII protection on all AI inputs and outputs
- Prompt injection detection (12 pattern categories)
- Output validation with confidentiality scanning
- Human-in-the-loop for all clinical AI actions
- Model approval gates with 7-dimension evaluation

---

## [2.0.0] — 2026-04-01 — Initial AI Infrastructure

### Added
- `backend/app/ai_fabric/` directory structure
- Shared AI provider abstractions (`shared.ai.provider`, `shared.ai.client`)
- Kernel AI runtime (`app.kernel.ai_runtime`)
- Guardrails (`app.ai.guardrails`)
- Approval workflow (`app.ai.approval`)
- Sandbox execution (`app.ai.sandbox`)
- Knowledge graph engine (`app.knowledge_graph`)

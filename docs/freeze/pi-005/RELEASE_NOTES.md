# Release Notes — National AI, Decision Intelligence & Digital Twin Platform v1.0

**PI-005 | GULA Platform v2.1.0**  
**Release Date:** 2026-07-16  
**Tag:** `national-ai-platform-v1.0`

---

## Overview

This release introduces the National AI & Intelligence Fabric (NAIF) and Digital Twin Engine to the GULA Platform — a comprehensive AI layer for clinical decision support, operational intelligence, public health surveillance, citizen engagement, and predictive simulation. It consolidates AI capabilities previously distributed across separate repositories into a unified, governed, and observable platform.

---

## What's New

### AI Gateway & Model Routing
- Unified gateway supporting 9 AI providers (OpenAI, Anthropic, Gemini, Ollama, vLLM, Azure, OpenRouter, DeepSeek, HuggingFace)
- Automatic provider failover with configurable retry strategy
- Cost optimization engine with real-time spend tracking
- Embedding service for vector search
- Cross-encoder reranking service

### Multi-Agent AI System
- 5 specialized AI agents with lifecycle management:
  - **ClinicalAgent** — CDS, interpretation, diagnosis support
  - **LaboratoryAgent** — QC, delta checks, workload prediction
  - **CitizenAgent** — Patient education, result explanation, reminders
  - **SecurityAgent** — Intrusion detection, access monitoring
  - **EngineeringAgent** — Architecture audit, dependency checking
- Singleton registry with task-based routing
- Tool-based architecture with per-tool approval requirements

### RAG & Knowledge Graph
- Hybrid semantic+keyword retrieval (BM25 + vector search)
- Citation engine with relevance scoring
- Token-budget-aware context builder
- Knowledge graph with 12 entity types and 11 relationship types
- Graph traversal (BFS, DFS, shortest path)

### Clinical Decision Support
- Real-time result analysis with abnormal flag detection
- Differential diagnosis generation via LLM
- Drug-drug interaction detection and allergy checking
- Clinical summarization for both physicians and patients
- Delta checking with configurable thresholds
- Critical result detection with panic values

### Laboratory Intelligence
- Westgard QC rule implementation (1-2s, 1-3s, 2-2s, R-4s, 4-1s, 10x)
- Workload prediction with TAT estimation
- Peak hour analysis and staffing recommendations
- Configurable per-test critical thresholds

### Public Health Intelligence
- Disease surveillance with z-score alerting (5 severity levels)
- Outbreak cluster detection and geographic spread analysis
- Population health trend analysis
- Immunization coverage tracking with WHO gap analysis
- SIR compartmental disease modeling

### Digital Twin Engine
- 4 twin types: Hospital, Laboratory, Directorate, National Health
- Predictive analytics: patient flow, bed occupancy, test volume, TAT
- Disease scenario modeling with mitigation strategies
- National-level outbreak simulation (Iraq ~40M population)
- Capacity planning with automated recommendations
- Twin health scoring (0-100) with data freshness tracking

### AI Governance & Security
- Prompt registry with full lifecycle management
- Model approval workflow (submit → evaluate → approve/reject)
- 7-dimension evaluation framework (accuracy, bias, safety, hallucination, toxicity, fairness, robustness)
- AI Constitution with 7 enforceable ethical articles
- Prompt injection protection (12 pattern categories)
- PII detection and redaction (8 data types)
- Output validation with confidentiality scanning
- Full observability with latency percentiles, cost tracking, error monitoring

### AI SDK & API
- `UnifiedAISDK` — Single entry point for all AI capabilities
- `AgentSDK` — Context creation and agent execution
- `RAGSDK` — Document indexing and querying
- 30+ REST API endpoints under `/ai/fabric/*`
- 10+ REST API endpoints under `/simulation/*`

---

## Breaking Changes

- Legacy `ai/ai_service.py` AI gateway is deprecated in favor of `AIGateway` and the `/ai/fabric/` routes
- Legacy `ai/clinical/clinical_ai/` rules engine is superseded by `ClinicalDecisionSupport`
- The `ClinicalAgent` now requires human approval for clinical actions

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | — | OpenAI API key |
| `ANTHROPIC_API_KEY` | — | Anthropic API key |
| `GEMINI_API_KEY` | — | Google Gemini API key |
| `DEEPSEEK_API_KEY` | — | DeepSeek API key |
| `AZURE_OPENAI_KEY` | — | Azure OpenAI API key |
| `AZURE_OPENAI_ENDPOINT` | — | Azure OpenAI endpoint |
| `OPENROUTER_API_KEY` | — | OpenRouter API key |
| `VLLM_API_KEY` | — | vLLM API key |
| `VLLM_BASE_URL` | `http://localhost:8001` | vLLM endpoint |
| `OLLAMA_BASE_URL` | `http://host.docker.internal:11434` | Ollama endpoint |

### Feature Flags

| Flag | Default | Description |
|---|---|---|
| `RUNTIME_MODE` | `api` | Execution context (api / worker / test / cli) |

---

## Migration Notes

1. Existing deployments using the legacy `ai/ai_service.py` should migrate to `/ai/fabric/chat`
2. The agent system auto-registers at startup via `integration.py` — no manual registration needed
3. Digital twins are created on-demand via `/simulation/twins` POST
4. PII protection is enabled by default for all AI operations
5. Clinical AI suggestions require approval — configure approval workflows in `app.ai.approval`

---

## Known Limitations

1. **Vector store** — Current implementation uses in-memory storage; production deployments should configure pgvector, Qdrant, or Milvus backends
2. **Model evaluation** — Kit includes the framework; organizations must run their own evaluation datasets
3. **Digital twin accuracy** — Initial predictions use linear trend models; accuracy improves as historical data accumulates
4. **Provider latency** — Local models (Ollama) may show higher latency on CPU-only deployments

---

## Future Roadmap

| Version | Focus |
|---|---|
| v1.1 | FHIR R4 integration for CDS alerts |
| v1.2 | Multi-language NLP (Arabic primary) |
| v1.3 | Federated learning for cross-lab models |
| v2.0 | Real-time streaming inference, MLflow model registry integration |

---

## Files in This Release

```
backend/app/ai_fabric/         — 18 modules (core AI fabric)
backend/app/simulation/        — 3 modules (digital twin engine)
backend/app/clinical/          — 3 subpackages (CDS models, knowledge, quality)
ai/                            — Legacy AI modules (deprecated)
```

---

## Support

For issues: https://github.com/anomalyco/opencode/issues  
Documentation: Refer to docs/freeze/pi-005/ for complete freeze documentation.

# GULA AI Platform Architecture

## Overview

The GULA AI Platform is an enterprise-grade, privacy-first AI system for healthcare
laboratory operations. Every component follows the clinical safety invariant:

> **AI = Suggest | Human = Approve | System = Enforce**

The platform integrates semantic search, knowledge graphs, RAG, multi-agent orchestration,
memory, governance, and clinical decision support — all tenant-isolated, auditable,
and secured against prompt injection and PII leakage.

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                     API Layer (Routes)                       │
│  /api/ai/* (v1)  +  /api/ai/v2/* (v2)                       │
├─────────────────────────────────────────────────────────────┤
│                    Orchestration Layer                        │
│  AIOrchestrator — intent classification → subsystem routing  │
├─────────────────────────────────────────────────────────────┤
│           Agent Runtime    │    RAG Pipeline                  │
│  Tool registry + planning  │  Retrieve → Augment → Generate  │
├─────────────────────────────────────────────────────────────┤
│  Vector DB  │  Knowledge  │  Memory  │  CDS  │  Governance  │
│  (pgvector)  │   Graph     │  Store   │ Engine │  Registry   │
├─────────────────────────────────────────────────────────────┤
│                    Safety Layer (v1)                          │
│  Guardrails → Approval → Sandbox                             │
├─────────────────────────────────────────────────────────────┤
│               Observability + Security                        │
│  Prometheus metrics  │  PII scan  │  Injection detection     │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Vector Database (`app/ai/vector_store.py`)
- **Storage**: pgvector extension on PostgreSQL 16
- **Embeddings**: Google Gemini `text-embedding-004` (768 dimensions)
- **Fallback**: Deterministic SHA-256 hash-based embedding (zero-dependency)
- **Search**: Cosine distance via `<=>` operator (pgvector) or in-memory
- **Filtering**: Metadata JSONB filters + tenant isolation (`lab_id`)
- **Methods**: `index_text()`, `search()`, `search_by_metadata()`, `delete()`

### 2. Knowledge Graph (`app/ai/knowledge_graph.py`)
- **Nodes**: 50 built-in nodes covering lab tests, conditions, medications, specimens, panels, departments
- **Edges**: 65+ relationships: `includes_test`, `indicates`, `treated_by`, `monitored_by`, `performed_by`, etc.
- **Standards**: LOINC codes for tests, SNOMED CT for conditions, RxNorm for medications
- **Languages**: Arabic aliases for all major nodes
- **Operations**: Search, neighbors, shortest path, BFS traversal
- **Persistence**: Optional DB sync to `ai_knowledge_nodes`/`ai_knowledge_edges`

### 3. RAG Pipeline (`app/ai/rag_pipeline.py`)
- **Retrieval**: Vector similarity + keyword reranking (70/30 weighted)
- **Augmentation**: System prompt + context formatting with deduplication
- **Generation**: Gemini 2.0 Flash via existing `google_ai` gateway
- **Safety**: Hallucination detection via token overlap scoring
- **Citations**: Automatically extracted from response text matching document sources
- **Fallback**: Graceful degradation when no documents retrieved

### 4. Agent Runtime (`app/ai/agent_runtime.py`)
- **Tools**: Registered via `@register_tool()` decorator
- **Built-in tools**: `lookup_patient`, `get_recent_results`, `analyze_lab_pattern`, `get_lab_info`, `search_knowledge_graph`
- **Planning**: LLM-based tool selection from available registry
- **Execution**: Sequential plan execution with approval gates for sensitive tools
- **Integration**: Writes to existing `ApprovalStore` and `AISandbox` for guarded operations

### 5. AI Orchestrator (`app/ai/orchestrator.py`)
- **Intent Classification**: Keyword-based scoring (clinical, patient, knowledge, agent, chat)
- **Routing**: Dispatches to appropriate subsystem (RAG, agent, CDS, chat)
- **Task Tracking**: Status, timing, error logging per orchestration

### 6. Memory Store (`app/ai/memory.py`)
- **In-memory + DB**: Dual-layer storage for speed and persistence
- **Session Management**: Create, read, list, delete sessions
- **History**: Token-aware truncation for context window management
- **Persistence**: `ai_conversations` and `ai_conversation_messages` tables

### 7. Clinical Decision Support (`app/ai/healthcare_cds.py`)
- **Range Checking**: Normal, warning, and critical panic thresholds
- **Test Weights**: Clinical severity weighting (electrolytes > cardiac > hematology)
- **Age/Gender Adjustments**: Creatinine in elderly males, hemoglobin in elderly
- **Condition Mapping**: Knowledge graph integration for suspected condition inference
- **Multi-result Analysis**: Pattern detection across order panels

### 8. Governance (`app/ai/governance.py`)
- **Model Registry**: 5 pre-registered models (Gemini, Ollama, Groq)
- **Prompt Manager**: 5 versioned templates (clinical, agent, RAG, Arabic, etc.)
- **Evaluation Framework**: Score computation (length, forbidden phrases, language detection)
- **Persistence**: `ai_model_registry` and `ai_evaluations` tables

### 9. Observability (`app/ai/observability.py`)
- **Counters**: Requests by intent/model/status, errors by type
- **Latency**: Running average + total samples
- **Tokens**: Input/output tracking with cost estimation
- **Guardrails**: Violation counters
- **Approvals**: Submitted, approved, rejected counts
- **Prometheus**: `/api/ai/v2/metrics/prometheus` endpoint with standard format

### 10. Security (`app/ai/security.py`)
- **PII Detection**: Iraqi national ID, phone (+964), email, IP, credit card
- **Prompt Injection**: 9 patterns (ignore previous, system prompt, role play, Arabic bypass)
- **Unsafe Content**: SQL injection, system exploitation, data destruction
- **Sanitization**: PII masking in responses

### 11. Safety Layer (v1 — existing)
- **Guardrails**: Operation whitelist/blacklist, confidence validation
- **Approval**: TTL-based pending approvals, auto-approve for display-only
- **Sandbox**: Read-only execution, operation registry, audit logging

## Database Schema

### New Tables (Migration: `20260719_0001`)
| Table | Purpose |
|-------|---------|
| `ai_embeddings` | Vector store with pgvector embeddings |
| `ai_conversations` | Session management for chat/agent memory |
| `ai_conversation_messages` | Per-message history with metadata |
| `ai_agent_executions` | Tool execution audit trail |
| `ai_knowledge_nodes` | Knowledge graph node persistence |
| `ai_knowledge_edges` | Knowledge graph edge persistence |
| `ai_model_registry` | Model capability registry |
| `ai_evaluations` | Prompt/response evaluation records |

### pgvector Extension
- Optional: set `ENABLE_PGVECTOR=true` to use native vector operations
- Fallback: in-memory cosine similarity when extension unavailable

## API Endpoints

All v2 endpoints under `/api/ai/v2/`:

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/search` | Semantic vector search |
| POST | `/index` | Index content for search |
| GET | `/embedding-info` | Embedding model status |
| POST | `/rag/query` | RAG question answering |
| GET | `/knowledge-graph/info` | KG statistics |
| POST | `/knowledge-graph/search` | Search KG nodes |
| GET | `/knowledge-graph/node/{id}` | Node details + neighbors |
| GET | `/knowledge-graph/path` | Shortest path |
| GET | `/agents/tools` | List agent tools |
| POST | `/agents/execute` | Execute agent task |
| POST | `/orchestrate` | Intelligent query routing |
| GET | `/orchestrate/tasks` | Task history |
| POST | `/sessions` | Create conversation session |
| POST | `/sessions/message` | Add message |
| GET | `/sessions/{id}` | Get session history |
| POST | `/cds/evaluate` | Single result CDS |
| POST | `/cds/evaluate-order` | Multi-result CDS |
| GET | `/governance/models` | Model registry |
| GET | `/governance/prompts` | Prompt templates |
| GET | `/governance/evaluations` | Eval statistics |
| POST | `/security/scan` | PII/injection scan |
| GET | `/metrics` | Platform metrics |
| GET | `/metrics/prometheus` | Prometheus format |

## Configuration

### Environment Variables
| Variable | Default | Purpose |
|----------|---------|---------|
| `ENABLE_PGVECTOR` | `false` | Enable pgvector extension queries |
| `EMBEDDING_MODEL` | `text-embedding-004` | Gemini embedding model |
| `EMBEDDING_DIMENSIONS` | `768` | Vector dimension count |

### Dependencies (optional)
- `google-generativeai>=0.8.0` — Gemini SDK (raw HTTP fallback without it)
- PostgreSQL 16 + pgvector extension — for production vector search

## Testing

```bash
# Run all AI platform tests (84 tests)
cd backend && python3 -m pytest tests/test_ai_platform.py -v

# Run existing guardrail tests (27 tests)
python3 -m pytest tests/test_ai_guardrails.py -v

# Run evaluation tests (8 tests)
python3 -m pytest tests/test_ai_evaluation.py -v
```

Test coverage includes:
- Embedding generation and similarity computation
- Knowledge graph BFS traversal and path finding
- RAG context augmentation and hallucination detection
- Agent tool registration and execution
- Orchestrator intent classification
- Memory session management
- Clinical decision support thresholds
- Security PII scanning and injection detection
- Observability metrics and Prometheus formatting
- Integration tests across component boundaries

## Security Invariants

1. All AI operations flow through guardrails → approval → sandbox
2. Absolutely blocked operations can never be created as AISuggestion objects
3. No AI component writes directly to clinical state
4. PII detection runs on all user inputs before processing
5. Prompt injection patterns are checked before LLM invocation
6. Tenant isolation enforced via `lab_id` on all vector and memory queries
7. Embeddings are content-addressed (SHA-256 deduplication)

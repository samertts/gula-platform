# Architecture Decision Records — National AI & Digital Twin Platform

**PI-005 | GULA Platform v2.1.0**

---

## ADR-001: Unified AI Gateway with Multi-Provider Routing

**Status:** ACCEPTED  
**Date:** 2026-07-16

**Context:** The platform needs to support multiple AI providers (OpenAI, Anthropic, Gemini, local models) with automatic failover, cost optimization, and unified observability.

**Decision:** Implement a single `AIGateway` class that:
- Uses `ProviderRouter` to register and select providers by model availability and cost
- `FailoverStrategy` for automatic retry across fallback providers
- `CostOptimizer` for real-time cost tracking and cheapest-provider selection
- All providers implement the `AIServiceProvider` protocol

**Consequences:**
- Single integration point for all AI operations
- Transparent failover without caller awareness
- Centralized cost tracking and optimization
- Additional providers can be added by implementing the protocol and registering

**Files:** `backend/app/ai_fabric/gateway.py`, `backend/app/ai_fabric/base.py`

---

## ADR-002: Singleton Agent Registry with Task-Based Routing

**Status:** ACCEPTED  
**Date:** 2026-07-16

**Context:** Multiple AI agents need to be discoverable, their lifecycles managed, and tasks routed to the correct agent dynamically.

**Decision:** Implement `AgentRegistry` as a singleton that:
- Registers agents at startup via `integration.py`
- Routes tasks via `find_for_task(task_type)` string matching
- Manages agent lifecycle (init → ready → running → shutdown)
- Collects heartbeats and metrics from all agents

**Consequences:**
- Decoupled task dispatch from agent implementation
- Centralized lifecycle management
- Agents can be added without changing routing logic
- Singleton pattern ensures single source of truth for agent state

**Files:** `backend/app/ai_fabric/agents/registry.py`, `backend/app/ai_fabric/agents/base.py`

---

## ADR-003: Hybrid RAG with Semantic + BM25 Fusion

**Status:** ACCEPTED  
**Date:** 2026-07-16

**Context:** Medical knowledge retrieval requires both semantic understanding and exact keyword matching (lab test names, drug names, ICD codes).

**Decision:** Implement `SemanticSearch` with three modes:
- `SEMANTIC` — Vector cosine similarity only
- `KEYWORD` — BM25 ranking only
- `HYBRID` — Reciprocal rank fusion of both result sets

**Consequences:**
- Hybrid mode catches both semantic matches and exact keyword matches
- BM25 provides interpretable keyword matching for regulatory compliance
- Vector embeddings enable concept-level retrieval
- Token-budget-aware context building prevents oversized LLM contexts

**Files:** `backend/app/ai_fabric/rag.py`

---

## ADR-004: Human-in-the-Loop for Clinical AI Actions

**Status:** ACCEPTED  
**Date:** 2026-07-16

**Context:** Clinical AI suggestions must never be executed without human approval to ensure patient safety and regulatory compliance.

**Decision:** All clinical AI tools (suggest_interpretation, suggest_reorder) require human approval via:
1. `ai_suggest()` — Records the suggestion with full context
2. `approval_store.submit()` — Creates an approval record
3. Human must approve/reject before execution
4. System enforces the decision

**Consequences:**
- Patient safety is ensured through mandatory human oversight
- Full audit trail of all clinical AI suggestions
- Slightly increased latency for clinical operations
- Compliance with ART-003 (Human Oversight) of the AI Constitution

**Files:** `backend/app/ai_fabric/agents/clinical_agent.py`, `backend/app/ai.approval`

---

## ADR-005: Digital Twin Architecture with Twin-Type Specialization

**Status:** ACCEPTED  
**Date:** 2026-07-16

**Context:** Different entities (hospitals, labs, directorates, national health) require different simulation models and data sources, but share common infrastructure (state management, persistence, forecast methods).

**Decision:** Implement `DigitalTwinEngine` as orchestrator with specialized twin classes:
- `HospitalTwin` — Patient flow, bed occupancy, resource utilization
- `LaboratoryTwin` — Test volume, TAT, equipment utilization
- `DirectorateTwin` — Multi-facility coordination, disease scenarios
- `NationalHealthTwin` — Population-level outbreak modeling, health metrics

**Consequences:**
- Clean separation of domain-specific simulation logic
- Shared statistical utilities (SMA, EMA, linear regression, SIR model)
- Common persistence and health monitoring layer
- New twin types can be added by implementing the simulator interface

**Files:** `backend/app/simulation/engine.py`, `backend/app/simulation/models.py`

---

## ADR-006: AI Observability as Singleton with Sliding Window

**Status:** ACCEPTED  
**Date:** 2026-07-16

**Context:** Every AI inference must be tracked for cost, latency, errors, and usage patterns. The observer must handle high throughput without unbounded memory growth.

**Decision:** Implement `AIObserver` as a singleton that:
- Records every inference with model, provider, latency, tokens, cost, success
- Maintains a 100K-record sliding window (trims to last 50K on overflow)
- Computes aggregate statistics: latency percentiles, error rates, cost breakdowns
- Provides daily usage history (30-day window)

**Consequences:**
- Bounded memory usage regardless of request volume
- Rich observability data for monitoring and cost allocation
- Singleton ensures single source of truth across workers
- Configurable time windows for statistics computation

**Files:** `backend/app/ai_fabric/observability.py`

---

## ADR-007: Multi-Layer AI Security with Defense-in-Depth

**Status:** ACCEPTED  
**Date:** 2026-07-16

**Context:** AI systems handling patient data require multiple independent security layers to prevent prompt injection, PII leakage, and unauthorized actions.

**Decision:** Implement `AIFirewall` with three independent subsystems:
1. **PromptInjectionProtector** — 12 regex patterns for common injection categories
2. **PIIProtector** — 8 PII patterns with detection, redaction, and masking
3. **OutputValidator** — Blocked phrases, confidentiality checks, schema validation

**Consequences:**
- Defense-in-depth: input scanning + output validation + PII protection
- Independent subsystems can be updated without affecting others
- Each layer provides configurable thresholds
- Slightly increased latency for AI operations due to scanning overhead

**Files:** `backend/app/ai_fabric/security.py`

---

## ADR-008: Prompt Registry with Full Lifecycle Management

**Status:** ACCEPTED  
**Date:** 2026-07-16

**Context:** AI prompts need version control, approval workflow, and lifecycle management for regulatory compliance and reproducibility.

**Decision:** Implement `PromptRegistry` with:
- Full semantic versioning (semver)
- Lifecycle states: DRAFT → REVIEW → APPROVED → ACTIVE → DEPRECATED → RETIRED
- Author tracking and approval recording
- Search and version history

**Consequences:**
- Every prompt change is tracked with version and author
- Rollback to previous versions is supported
- Regulatory audits can trace any prompt to its exact version
- Active promotion workflow ensures production prompts are reviewed

**Files:** `backend/app/ai_fabric/governance.py`

---

## ADR-009: AI Constitution for Ethical Guardrails

**Status:** ACCEPTED  
**Date:** 2026-07-16

**Context:** The AI system must operate within defined ethical boundaries that are enforceable and auditable.

**Decision:** Implement `AIConstitution` with 7 articles covering:
- Patient safety, data privacy, human oversight, transparency, fairness, accountability, clinical conservatism
- Each article has severity (critical/high/medium) and enforceability flag
- Compliance checking against actions
- Automated compliance reports

**Consequences:**
- Ethical principles are code-enforceable, not just documentation
- Compliance checking provides automated governance
- Articles can be added, updated, or deprecated independently
- Severity levels enable risk-based enforcement

**Files:** `backend/app/ai_fabric/governance.py`

---

## ADR-010: Local AI Inference with GPU Pool Management

**Status:** ACCEPTED  
**Date:** 2026-07-16

**Context:** Some deployments require fully offline AI inference on local hardware for data residency or connectivity reasons.

**Decision:** Implement `LocalAIEngine` with:
- NVIDIA GPU detection via nvidia-smi
- Job queue with configurable concurrency pool
- GPU selection by utilization (load balancing)
- CPU-only fallback when no GPU detected
- Integration with ModelRegistry for lifecycle management

**Consequences:**
- Fully offline inference capability
- Automatic GPU discovery and load balancing
- Graceful degradation to CPU-only mode
- Support for on-premise models (Ollama, vLLM)

**Files:** `backend/app/ai_fabric/local_ai.py`

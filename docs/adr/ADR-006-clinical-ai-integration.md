# ADR-006: Clinical AI Integration

**Status:** Accepted
**Date:** 2026-07-08
**Deciders:** Engineering Lead, AI Team Lead

## Context

The GULA Platform needs to provide clinical intelligence features: result interpretation suggestions, anomaly detection, trend analysis, and predictive analytics for patient outcomes. These features must integrate with the existing FastAPI monolith without compromising stability or data integrity.

## Decision

Integrate AI capabilities through a dedicated AI module within the monolith (`backend/app/ai/`) that communicates with external AI services (Ollama, OpenAI-compatible APIs) via an abstraction layer.

### Architecture
- `backend/app/ai/` — Monolith-side AI integration module
- `ai/` (project root) — Independent AI services and models
- Abstraction layer supports multiple AI providers (Ollama primary, OpenAI-compatible fallback)
- Feature flag gated (`ENABLE_AI_FEATURES`)
- All AI operations are asynchronous and non-blocking

### Supported Features
1. **Result Interpretation** — Suggest clinical interpretations for lab results
2. **Anomaly Detection** — Flag out-of-range or unusual results
3. **Trend Analysis** — Patient result trends over time
4. **Predictive Analytics** — Risk stratification and outcome prediction

## Alternatives Considered

### 1. Tight Coupling with Specific AI Provider

**Pros:** Simpler integration, fewer abstraction layers.
**Cons:** Vendor lock-in, difficult to switch providers.
**Rejected because:** The AI provider landscape is evolving rapidly; abstraction prevents lock-in.

### 2. Separate AI Microservice

**Pros:** Independent scaling, technology freedom.
**Cons:** Network latency, serialisation overhead, deployment complexity.
**Rejected because:** For current scale, monolith integration is simpler and faster. Microservice decomposition can follow if AI load demands it.

### 3. Embedded ML Models (ONNX, TensorFlow)

**Pros:** No external dependency, offline capable.
**Cons:** Model size, update frequency, GPU requirements.
**Rejected because:** External AI services provide more flexibility for model updates and don't require GPU hardware in the deployment.

## Consequences

### Positive
- AI features are available without external service dependencies for basic operations
- Abstraction layer allows provider switching without code changes
- Asynchronous design prevents AI latency from blocking main request path
- Feature flag allows gradual rollout

### Negative
- External AI service dependency for advanced features
- Additional latency for AI-enhanced operations
- Need to manage AI service availability and fallback behaviour

### Neutral
- AI module follows the same patterns as the rest of the monolith
- New AI models can be added without architectural changes

## References
- `backend/app/ai/` — Monolith AI integration module
- `ai/` — Independent AI services and models
- `backend/app/routes/ai.py` — AI API routes
- `backend/app/core/feature_flags.py` — Feature flag gating

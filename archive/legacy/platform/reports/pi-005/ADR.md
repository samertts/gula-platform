# PI-005 — Architecture Decision Records

## AI Platform — Key Architecture Decisions

**Version:** 2.1.0

---

## ADR-001: Model Registry as Central Governance Hub

**Status:** Accepted
**Date:** 2026-03-15

**Context:** Multiple AI models from different teams need lifecycle management, versioning, and approval workflows.

**Decision:** Implement a `ModelRegistry` class as the single source of truth for all ML models. All models must be registered before deployment. The registry enforces a strict state machine (Development → Staging → Production → Deprecated → Retired) with no skip transitions.

**Consequences:**
- Positive: Single governance point, lineage tracking, easy auditing
- Positive: Prevents untested models from reaching production
- Negative: Additional registration step in deployment pipeline
- Negative: In-memory storage limits scale (consider persistent DB)

---

## ADR-002: Prompt Registry with Template Isolation

**Status:** Accepted
**Date:** 2026-03-20

**Context:** LLM prompts need versioning, testing, and approval, and must protect against prompt injection.

**Decision:** All LLM interactions go through the `PromptRegistry` with strict template separation. System prompts are fixed and immutable once approved. User input is injected only at designated variable positions.

**Consequences:**
- Positive: Eliminates prompt injection via template isolation
- Positive: Version control for all prompts with rollback capability
- Positive: Optimization history tracked per version
- Negative: Requires new prompt version for any system message change
- Negative: Variable injection adds complexity for dynamic prompts

---

## ADR-003: Bilingual Explainability (Arabic + English)

**Status:** Accepted
**Date:** 2026-04-01

**Context:** Clinical AI decisions must be explainable to both Arabic-speaking clinicians and English-speaking technical reviewers.

**Decision:** All explanations are generated in both Arabic and English. The `ExplainabilityService` produces human-readable explanations in both languages from a single inference.

**Consequences:**
- Positive: Serves all users regardless of language preference
- Positive: Single explanation generation call produces both outputs
- Negative: Approximately 40% increase in explanation generation time
- Negative: Arabic NLP requires separate validation for medical terminology

---

## ADR-004: Bias Detection as Separate Service Layer

**Status:** Accepted
**Date:** 2026-04-10

**Context:** Bias detection must run independently of model inference to avoid performance impact and allow cross-model analysis.

**Decision:** Implement `BiasDetector` as a standalone service that analyzes pre-computed predictions. It runs on a scheduled basis (daily/weekly) rather than inline with inference.

**Consequences:**
- Positive: No latency impact on inference
- Positive: Can analyze across multiple models and time periods
- Positive: Easy to add new protected attributes without changing models
- Negative: Bias detection is not real-time (max 24-hour delay)
- Negative: Requires separate prediction log storage

---

## ADR-005: Four-Component Confidence Score

**Status:** Accepted
**Date:** 2026-04-15

**Context:** A single model confidence score is insufficient for clinical safety. Need multi-dimensional confidence assessment.

**Decision:** Confidence scores are computed from four weighted components: model confidence (40%), data quality (20%), feature coverage (20%), and historical accuracy (20%).

**Consequences:**
- Positive: More nuanced confidence assessment
- Positive: Identifies specific dimensions of uncertainty
- Positive: Thresholds can be set per dimension for different actions
- Negative: Requires data quality and historical accuracy tracking infrastructure
- Negative: More complex scoring may confuse users if not properly communicated

---

## ADR-006: Human-in-the-Loop Gate for Clinical Decisions

**Status:** Accepted
**Date:** 2026-04-20

**Context:** Clinical AI decisions affecting patient care must have human oversight per regulatory requirements.

**Decision:** A mandatory human review gate is implemented for: critical drug interactions, panic lab values, and treatment pathway changes. The system blocks the action until a qualified human reviews and approves/modifies/rejects.

**Consequences:**
- Positive: Regulatory compliance (Iraqi MoH clinical AI guidelines)
- Positive: Patient safety guaranteed
- Negative: Adds latency to time-critical decisions
- Negative: Requires 24/7 qualified reviewer availability

---

## ADR-007: In-Memory Registry with DB Persistence Bridge

**Status:** Accepted
**Date:** 2026-05-01

**Context:** ModelRegistry and PromptRegistry need fast query performance while maintaining durability.

**Decision:** In-memory Map-based storage for runtime performance, with a persistence bridge for periodic snapshots and recovery. Future migration to persistent DB (PostgreSQL) is planned.

**Consequences:**
- Positive: Sub-millisecond queries for model/prompt lookups
- Positive: Simple implementation
- Negative: Data loss risk on service restart (mitigated by persistence bridge)
- Negative: Not horizontally scalable without shared cache

---

## ADR-008: Domain-Specific AI Module Organization

**Status:** Accepted
**Date:** 2026-05-10

**Context:** AI services span clinical, operational, citizen, and engineering domains with different requirements.

**Decision:** Organize AI modules by domain (`clinical/`, `predictive/`, `digital_twin/`, `citizen/`, `engineering/`, `governance/`) rather than by technical layer (model, data, inference).

**Consequences:**
- Positive: Clear ownership boundaries (clinical team owns clinical/)
- Positive: Domain-specific concerns isolated
- Negative: Some cross-cutting concerns (logging, metrics) must be shared
- Negative: Duplication of common patterns across domains

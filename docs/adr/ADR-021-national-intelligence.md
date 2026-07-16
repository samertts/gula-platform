# ADR-021: National Health Intelligence Platform

**Status:** Accepted
**Date:** 2026-07-15
**Deciders:** Engineering Lead, AI Lead, Chief Clinical Officer

---

## Context

Healthcare generates vast amounts of data that, when analyzed intelligently, can improve patient outcomes, optimize operations, and enable early disease detection. Currently, AI/ML capabilities are fragmented across the GULA platform: the `backend/app/ai/` module handles clinical AI for laboratory results, and the top-level `ai/` directory contains experimental modules. There is no unified intelligence platform that serves all healthcare applications with consistent AI capabilities.

**Requirements:**
- Centralized AI/ML platform serving all national platform applications (EHR, laboratory, clinical, hospital, public health)
- Clinical AI for diagnostic support, result interpretation, and anomaly detection
- Laboratory AI for quality control, workflow optimization, and predictive maintenance
- Hospital AI for resource optimization, patient flow prediction, and readmission risk
- Public Health AI for disease surveillance, outbreak detection, and population health analytics
- LLM gateway with safety filters, prompt guards, and usage governance
- Model lifecycle management (training, evaluation, deployment, monitoring, retirement)
- Feature store integration with the National Data Platform (ADR-017)
- Explainability and audit trails for all AI decisions affecting patient care

**Constraints:**
- Must support batch (offline) and real-time (online) inference workloads
- Must integrate with the National Data Platform (ADR-017) for training data and features
- Must comply with Iraqi health AI regulations and clinical safety standards
- Must support both cloud-based and edge inference for low-connectivity settings
- Must provide explainable AI (XAI) for all clinical decisions — no black-box models for patient care

## Decision

Build a dedicated **National Health Intelligence Platform** at `national/intelligence/` that provides a unified AI/ML layer for all healthcare applications. The platform is organized into four intelligence domains (clinical, laboratory, hospital, public health) with a shared LLM gateway and model lifecycle manager.

### Architecture

```
+------------------------------------------------------------------+
|               National Health Intelligence Platform               |
+------------------------------------------------------------------+
|                                                                   |
|  +-----------------------------------------------------------+   |
|  |                    LLM Gateway                             |   |
|  |  Prompt Guard  |  Safety Filter  |  Usage Governance      |   |
|  |  Model Router  |  Token Management |  Audit Log           |   |
|  +--------------------------+--------------------------------+   |
|                              |                                    |
|  +--------------------------+--------------------------------+   |
|  |                    Intelligence Domains                     |   |
|  |                                                              |   |
|  |  +-------------+  +-------------+  +-------------+          |   |
|  |  | Clinical AI |  | Laboratory  |  | Hospital AI |          |   |
|  |  |             |  | AI          |  |             |          |   |
|  |  | - Diagnostic|  | - QC        |  | - Resource  |          |   |
|  |  | - Risk      |  | - Workflow  |  | - Patient   |          |   |
|  |  | - Alerts    |  | - Predictive|  | - Readmission|         |   |
|  |  +------+------+  +------+------+  +------+------+          |   |
|  |         |               |               |                   |   |
|  |  +------+---------------+---------------+------+            |   |
|  |  |         Public Health AI                      |          |   |
|  |  |  Disease Surveillance | Outbreak Detection   |          |   |
|  |  |  Population Analytics | Epidemiology Models   |          |   |
|  |  +----------------------------------------------+          |   |
|  +--------------------------+--------------------------------+   |
|                              |                                    |
|  +--------------------------+--------------------------------+   |
|  |                    Shared Services                         |   |
|  |                                                              |   |
|  |  +----------+  +----------+  +----------+  +----------+     |   |
|  |  | Model    |  | Feature  |  | Training |  | Inference|     |   |
|  |  | Registry |  | Store    |  | Pipeline |  | Serving  |     |   |
|  |  +----------+  +----------+  +----------+  +----------+     |   |
|  +--------------------------+--------------------------------+   |
|                              |                                    |
|  +--------------------------+--------------------------------+   |
|  |              Data Platform Integration                     |   |
|  |  (Feature ingestion, training data, feedback loops)        |   |
|  +----------------------------------------------------------+   |
|                                                                   |
+------------------------------------------------------------------+
```

### Key Design Decisions

1. **Single AI platform, multiple domains** — All AI capabilities are built on a shared infrastructure (model registry, feature store, training pipeline, inference serving). Domains organize models by purpose but share the same platform.

2. **LLM gateway with safety guardrails** — All LLM access goes through a gateway that enforces: prompt injection guards, harmful content filters, PII redaction, usage quotas, and full audit logging. No application directly accesses an LLM.

3. **Explainable AI for clinical decisions** — Models that affect patient care must provide human-interpretable explanations for their outputs (SHAP, LIME, or domain-specific explanations). Black-box models are prohibited for clinical decision support.

4. **Reusable by all applications** — The platform exposes APIs that any national platform application can consume. The Citizen Super App (ADR-020) uses Health Intelligence AI, the Doctor Workspace (ADR-023) uses Clinical AI, etc.

5. **Feedback loops** — Every AI inference includes a mechanism for end-users to provide feedback (correct, incorrect, uncertain). Feedback is captured in the data platform and used for model improvement and drift detection.

### Implementation Strategy

| Phase | Scope | Timeline |
|-------|-------|----------|
| **Phase 1** | Platform infrastructure: model registry, inference serving, feature store integration | 10 weeks |
| **Phase 2** | Clinical AI (result interpretation, anomaly detection, risk scoring) | 8 weeks |
| **Phase 3** | Laboratory AI and LLM gateway with safety filters | 8 weeks |
| **Phase 4** | Hospital AI, Public Health AI, explainability, feedback loops | 10 weeks |

## Consequences

### Positive
- **Single AI platform** — Consistent infrastructure, governance, and safety across all AI use cases
- **LLM safety** — Centralized gateway prevents unsafe or ungoverned LLM usage
- **Reusable by all applications** — No AI silos; every application benefits from the platform
- **Explainable AI** — Clinical decisions are transparent and auditable
- **Feature store** — Pre-computed features reduce training time and ensure consistency
- **Feedback-driven improvement** — Continuous model improvement through user feedback

### Negative
- **Infrastructure cost** — GPU infrastructure for model training and inference is expensive
- **Operational complexity** — Managing model lifecycle, feature pipelines, and inference serving requires specialized skills
- **Latency for real-time inference** — Complex models may not meet real-time requirements for all use cases
- **Model governance overhead** — Each model requires documentation, validation, monitoring, and periodic retraining

### Risks
- **Clinical safety** — An AI error could harm a patient. Mitigated by: all clinical AI decisions are advisory (not autonomous), explicit confidence thresholds, human-in-the-loop for high-risk recommendations, continuous monitoring for accuracy drift.
- **Bias in models** — AI models trained on Iraqi health data may encode demographic, geographic, or socioeconomic biases. Mitigated by: bias testing in model validation, diverse training data, fairness metrics in model evaluation, regular bias audits.
- **LLM hallucination** — LLMs may generate inaccurate medical information. Mitigated by: strict prompt templates, retrieval-augmented generation (RAG) grounded in verified clinical sources, output validation filters, disclaimer labeling.

## Compliance

This ADR is consistent with:
- **Engineering Constitution Section 3** — Data integrity and patient safety; AI decisions are advisory only
- **Engineering Constitution Section 4** — Security and safety; LLM gateway enforces safe usage
- **ADR-006** — Clinical AI integration is subsumed by the broader intelligence platform
- **ADR-017** — National Data Platform provides training data and feature store
- **ADR-019** — Ecosystem enables external AI/ML integrations through adapters
- **WHO Ethics and Governance of AI for Health** — Transparency, accountability, and safety guidelines
- **EU AI Act compliance** — Risk-based classification, explainability requirements, human oversight

# PI-005 — Release Notes

## national-ai-platform-v1.0

**Release Date:** July 2026
**Version:** 2.1.0

---

## Overview

This release delivers the GULA National AI Governance Platform — the complete orchestration, governance, and safety layer for all artificial intelligence services across the Iraqi national health system. The platform enforces strict model governance, explainability, bias detection, and human-in-the-loop approval workflows for all clinical AI decisions.

---

## What's Included

### Governance Layer
- **Model Registry**: Full ML model lifecycle management with state machine (Development → Staging → Production → Deprecated → Retired), lineage tracking, approval workflow, and deployment history
- **Prompt Registry**: Version-controlled, approved-only LLM prompt management with template isolation, variable injection, automated testing, and optimization tracking
- **Explainability Service**: Multi-type explanation generation (feature importance, decision path, counterfactual) with bilingual output (Arabic + English)
- **Bias Detector**: Continuous monitoring across 6 bias types and 6 protected attributes with 3 fairness tests (demographic parity, equal opportunity, disparate impact)

### Clinical AI Services
- **Drug Interaction Checker**: Analyzes prescription combinations against 450K+ interaction pairs with severity-graded alerts
- **Critical Result Detection**: Real-time panic value detection with escalating notification chain (5min → 15min → 30min → 60min)
- **Clinical Pathways**: 273 evidence-based pathways across 8 specialties with compliance tracking
- **Decision Support**: 250+ CDS rules for drug, allergy, disease, and dosing guidance

### Predictive Analytics
- **Bed Occupancy Prediction**: 7-day forecast with 7.8% MAPE
- **Disease Forecasting**: 30-day forecasts for 8 diseases with early warning system (4-tier alert)
- **Resource Optimization**: Staff scheduling (28% improvement), supply chain (75% stockout reduction)
- **Failure Prediction**: 8 failure types with 87-100% accuracy and auto-repair actions

### Additional Modules
- **Digital Twin**: Patient and population health simulation
- **Citizen AI**: Health assistant and symptom checker (Arabic-first)
- **Engineering AI**: System failure prediction and self-healing suggestions
- **Privacy & Data**: Anonymization pipeline, differential privacy (ε=1.0), consent engine

---

## Breaking Changes

- **Governance API v2**: Model and prompt registry APIs have been updated. Previous v1 API endpoints are deprecated.
- **Confidence scoring**: Changed from single-score to four-component model. Consumers must update to use the new `ConfidenceScore` interface.
- **Module structure**: AI modules reorganized from technical layering to domain-based structure. Update import paths accordingly.

---

## Known Issues

| ID | Description | Severity | Target Fix |
|----|-------------|----------|------------|
| AI-001 | Bias detector statistical significance may overflow on very large datasets (>1M) | Low | v2.2.0 |
| AI-002 | Explainability service does not support multimodal inputs (images + text) | Medium | v2.3.0 |
| AI-003 | Model Registry in-memory only (no DB persistence) — data lost on restart | Medium | v2.2.0 |
| AI-004 | Prompt Registry Arabic prompts have 5% higher hallucination rate | Medium | v2.1.1 |

---

## Future Roadmap

### v2.2.0
- Persistent database backend for Model Registry + Prompt Registry
- Real-time bias detection (inline with inference)
- Enhanced Arabic NLP for medical terminology
- Expanded clinical pathways (requested: neurology, psychiatry)

### v2.3.0
- Multimodal AI support (image + text + lab data)
- Federated learning for privacy-preserving model training
- Automated clinical guideline updates
- Integration with international health AI standards

### v3.0.0
- Autonomous clinical AI agents with supervised workflow
- Real-time population health digital twin
- Cross-institutional AI model sharing
- Full IEC 62304 medical software certification

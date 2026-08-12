# PI-005 — Changelog

## AI Platform Version History

**Package:** `@gula/ai-platform`

---

## v2.1.0 (July 2026)

### Added
- **ModelRegistry**: Full lifecycle management with state machine (5 states, 6 transitions)
- **PromptRegistry**: Version-controlled prompt management with approval workflow
- **ExplainabilityService**: Multi-type explanation generation (SHAP, LIME, decision path, counterfactual)
- **BiasDetector**: 6 bias types, 6 protected attributes, 3 fairness tests, 5 mitigation strategies
- **Clinical AI Module**: Drug interaction checking, critical result detection, clinical pathways
- **Predictive Analytics Module**: Bed occupancy, disease forecasting, resource optimization
- **Digital Twin Module**: Patient and population health simulation
- **Citizen AI Module**: Health assistant, symptom checker
- **Engineering AI Module**: Failure prediction, self-healing suggestions
- **Privacy Module**: Data anonymization pipeline, differential privacy, consent engine

### Changed
- Core governance types extracted to shared interfaces
- Confidence scoring moved to four-component model (model + data + coverage + history)
- Folder structure reorganized by domain (clinical/predictive/engineering/citizen)

### Fixed
- State machine transition validation (Retired → any) properly restricted
- Bias detector statistical significance computation edge case (zero division)
- Prompt registry version limit enforcement

---

## v2.0.0 (April 2026)

### Added
- Initial AI Governance architecture
- Model and Prompt type definitions
- Basic registry implementations

### Notes
- Pre-release version, not deployed to production
- APIs subject to change before v2.1.0 stabilization

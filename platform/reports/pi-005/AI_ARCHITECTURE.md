# PI-005 — AI Architecture Report

## National AI Governance Platform Architecture

**Version:** 2.1.0
**Date:** July 2026
**Package:** `@gula/ai-platform`

---

## 1. AI Platform Overview

The GULA National AI Governance Platform (`@gula/ai-platform`) provides the orchestration and governance layer for all artificial intelligence services across the healthcare ecosystem. It enforces strict model governance, explainability, bias detection, and human-in-the-loop approval workflows for all clinical AI decisions.

### Core Principles

1. **Human-in-the-loop**: No AI decision affecting patient care is final without human review
2. **Explainability**: Every AI prediction must be explainable in natural language (Arabic + English)
3. **Bias detection**: All models are continuously monitored for demographic, selection, and algorithmic bias
4. **Audit trail**: Every model version, prompt version, and AI decision is immutably logged
5. **Clinical safety**: All AI outputs pass through clinical safety validation before reaching patients

### Architecture Layers

```
┌──────────────────────────────────────────────────────────────┐
│                    Application Layer                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ Clinical │ │Predictive│ │ Digital  │ │ Citizen  │       │
│  │ AI       │ │Analytics │ │ Twin     │ │ AI       │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
├──────────────────────────────────────────────────────────────┤
│                    Governance Layer                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ Model    │ │ Prompt   │ │Explain-  │ │ Bias     │       │
│  │ Registry │ │ Registry │ │ ability  │ │ Detector │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
├──────────────────────────────────────────────────────────────┤
│                    Infrastructure Layer                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ LLM      │ │ Embedding│ │ Vector   │ │ Model    │       │
│  │ Gateway  │ │ Service  │ │ Database  │ │ Serving  │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. Core Governance Components

### 2.1 Model Registry (`ModelRegistry.ts`)

The Model Registry manages the complete lifecycle of ML models from development through retirement.

```
┌─────────────────────────────────────────────┐
│              Model Registry                  │
├─────────────────────────────────────────────┤
│ Status Machine:                              │
│                                              │
│  Development ──▶ Staging ──▶ Production     │
│       ▲              │              │        │
│       │              ▼              ▼        │
│       │          Deprecated ──▶ Retired      │
│       │              │                      │
│       └──────────────┘                      │
├─────────────────────────────────────────────┤
│ Features:                                    │
│ • Model versioning with full lineage         │
│ • Approval workflow (4 stages)               │
│ • Deployment history tracking                │
│ • Performance metrics registry               │
│ • Checksum verification                      │
│ • Query by name, version, status, tags       │
└─────────────────────────────────────────────┘
```

**Key interfaces:**
- `ModelMetadata` — Name, version, author, framework, task type, input/output schema, performance metrics
- `ModelVersion` — Full model definition with deployment and approval history
- `ApprovalRecord` — Reviewer, status (pending/approved/rejected/changes_requested), stage, timestamp
- `LineageNode` — Parent-child model relationships for model genealogy

**Model lifecycle enforcement:**
```typescript
validTransitions: {
  Development:  [Staging],
  Staging:      [Production, Development],
  Production:   [Deprecated],
  Deprecated:   [Retired, Production],
  Retired:      [],  // Terminal state
}
```

### 2.2 Prompt Registry (`PromptRegistry.ts`)

The Prompt Registry provides version-controlled, approved-only prompt management for LLM interactions.

```
┌─────────────────────────────────────────────┐
│            Prompt Registry                   │
├─────────────────────────────────────────────┤
│ Status Machine:                              │
│                                              │
│  Draft ──▶ Testing ──▶ Approved             │
│   ▲                     │                    │
│   │                     ▼                    │
│   │              Deprecated ──▶ Retired      │
│   │                     │                    │
│   └─────────────────────┘                    │
├─────────────────────────────────────────────┤
│ Features:                                    │
│ • Template-based prompt management           │
│ • Variable injection with validation         │
│ • Automated prompt testing                   │
│ • Optimization history tracking              │
│ • Locale-specific prompts (ar/en/both)       │
│ • Full audit logging                         │
│ • Approval gate (configurable)               │
└─────────────────────────────────────────────┘
```

**Prompt template structure:**
```typescript
PromptTemplate {
  systemPrompt: "You are a clinical decision support system...",
  userPromptTemplate: "Analyze lab results for {{patientName}}: {{results}}",
  variables: [{ name: "patientName", type: "string", required: true }],
  model: "gula-clinical-v1",
  temperature: 0.2,
  maxTokens: 1024,
  locale: "both"
}
```

### 2.3 Explainability Service (`ExplainabilityService.ts`)

Provides human-readable explanations for all AI predictions.

```
┌─────────────────────────────────────────────┐
│         Explainability Service               │
├─────────────────────────────────────────────┤
│ Explanation Types:                           │
│ • SHAP values (feature contribution)         │
│ • LIME values (local surrogate model)        │
│ • Feature importance (global)                │
│ • Decision path (tree-based models)          │
│ • Rule-based (symbolic AI)                   │
│ • Counterfactual (what-if analysis)          │
├─────────────────────────────────────────────┤
│ Features:                                    │
│ • Feature contribution analysis              │
│ • Decision path visualization                │
│ • Confidence scoring (4 components)          │
│ • Counterfactual generation                  │
│ • Bilingual output (Arabic + English)        │
└─────────────────────────────────────────────┘
```

**Confidence scoring formula:**
```
Overall = ModelConfidence × 0.4 + DataQuality × 0.2 + FeatureCoverage × 0.2 + HistoricalAccuracy × 0.2
Levels: VeryHigh (≥0.9), High (≥0.7), Medium (≥0.5), Low (≥0.3), VeryLow (<0.3)
```

### 2.4 Bias Detector (`BiasDetector.ts`)

Continuously monitors models for unfair bias across protected attributes.

```
┌─────────────────────────────────────────────┐
│             Bias Detector                    │
├─────────────────────────────────────────────┤
│ Protected Attributes:                        │
│ • Age, Gender, Ethnicity                     │
│ • Socioeconomic status, Region, Disability   │
├─────────────────────────────────────────────┤
│ Bias Types Detected:                         │
│ • Demographic bias (representation)          │
│ • Selection bias (sampling)                  │
│ • Measurement bias (labeling)                │
│ • Confirmation bias (feedback loop)          │
│ • Algorithmic bias (prediction disparity)    │
├─────────────────────────────────────────────┤
│ Tests:                                       │
│ • Demographic parity (max disparity ≤ 0.1)   │
│ • Equal opportunity (TPR/FPR ≤ 0.05)         │
│ • Disparate impact (ratio ≥ 0.8)             │
├─────────────────────────────────────────────┤
│ Mitigation Strategies:                       │
│ • Instance reweighting                        │
│ • Adversarial debiasing                       │
│ • Data augmentation                           │
│ • Fairness constraints                        │
│ • Label audit                                │
└─────────────────────────────────────────────┘
```

---

## 3. AI Service Modules

### 3.1 Clinical AI Services (`src/clinical/`)

| Service | Description | Human-in-Loop Required |
|---------|-------------|------------------------|
| Drug Interaction Checker | Analyzes prescription combinations for adverse reactions | Yes (pharmacist reviews) |
| Critical Result Detection | Flags abnormal lab values requiring immediate action | Yes (clinician notified) |
| Clinical Pathways | Suggests evidence-based treatment pathways | Yes (physician decides) |
| Decision Support | Real-time clinical decision augmentation | Yes |

### 3.2 Predictive Analytics (`src/predictive/`)

| Service | Description | Horizon |
|---------|-------------|---------|
| Bed Occupancy Prediction | Predicts hospital bed availability 7 days ahead | 7 days |
| Disease Forecasting | Epidemiological trend prediction for 10 diseases | 30 days |
| Resource Optimization | Staff and supply optimization recommendations | 14 days |
| Patient Admission Risk | 30-day readmission risk scoring | Per admission |

### 3.3 Digital Twin (`src/digital_twin/`)

| Capability | Description |
|------------|-------------|
| Patient Digital Twin | Longitudinal health profile with predictive modeling |
| Population Health Twin | Anonymized aggregate for epidemiology simulation |
| What-if Simulation | Intervention impact analysis before deployment |
| Treatment Optimization | Personalized treatment plan simulation |

### 3.4 Citizen AI (`src/citizen/`)

| Service | Description |
|---------|-------------|
| Health Assistant | Conversational AI for health queries (Arabic) |
| Symptom Checker | ML-based symptom triage |
| Medication Reminder | Smart scheduling with drug interaction alerts |
| Health Insights | Personalized health trend analysis |

### 3.5 Engineering AI (`src/engineering/`)

| Service | Description |
|---------|-------------|
| Failure Prediction | Anticipates system failures from metrics (CPU, memory, disk) |
| Self-Healing Suggestions | Recommends auto-remediation actions |
| Anomaly Detection | Identifies unusual patterns in system behavior |
| Capacity Forecasting | Predicts resource needs 30-90 days ahead |

### 3.6 Privacy & Data (`src/privacy/` + `src/data/`)

| Component | Description |
|-----------|-------------|
| Data Anonymization | De-identification pipeline for PHI |
| Differential Privacy | ε-DP guarantees on aggregate queries |
| Consent Engine | Patient consent enforcement for data usage |
| Data Quality | Automated data quality scoring and validation |

---

## 4. Model Serving Architecture

```
External LLM APIs (OpenAI, Claude, etc.)
    │
    ▼
LLM Gateway (unified API, failover, rate limiting)
    │
    ├── Prompt Registry (approved prompts only)
    ├── Context Builder (retrieves patient data via secure API)
    ├── Safety Filter (input/output guardrails)
    │
    ▼
Response Processor
    ├── Explainability Service (generates explanation)
    ├── Bias Detector (checks for bias)
    ├── Clinical Safety Validator
    └── Human Review Queue (if required)
    │
    ▼
Structured Response (JSON with explanation + confidence + audit trail)
```

---

## 5. Data Flow

```
User Query (Arabic/English)
    ▼
Prompt Registry → Approved Prompt Template
    ▼
Context Builder → Patients API → Patient Data (anonymized)
    ▼
LLM Gateway → Model Inference
    ▼
Explainability → Feature Contributions + Decision Path
    ▼
Bias Detection → Fairness Check
    ▼
Clinical Safety → Validation Pass/Fail
    ▼
Human Review (if needed) → Approve/Reject/Modify
    ▼
Response → Audit Log → Notification (if critical)
```

---

## 6. Audit Trail

Every AI interaction is logged:

```typescript
AIRecord {
  id: string;
  modelName: string;
  modelVersion: string;
  promptId: string;
  promptVersion: string;
  input: Record<string, unknown>;    // Input data (anonymized)
  output: Record<string, unknown>;   // AI output
  explanation: ExplanationResult;    // Human-readable explanation
  biasCheck: BiasResult[];           // Bias detection results
  confidence: number;                // Confidence score
  humanReview: {                     // Human review (if required)
    reviewer: string | null;
    status: 'pending' | 'approved' | 'rejected' | 'modified';
    comments: string;
    timestamp: Date | null;
  };
  clinicalSafety: {                  // Clinical safety validation
    passed: boolean;
    checks: string[];
  };
  latency: number;                   // End-to-end latency
  timestamp: Date;
}
```

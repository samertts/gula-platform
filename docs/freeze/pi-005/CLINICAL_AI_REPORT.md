# Clinical AI Report — Clinical Decision Support, Drug Safety & Pathways

**PI-005 | GULA Platform v2.1.0**  
**Date:** 2026-07-16  
**Status:** FINAL

---

## 1. Clinical Decision Support (CDS) System

### 1.1 Architecture

The CDS system spans two layers:

**Layer 1 — AI Fabric (`backend/app/ai_fabric/clinical.py`):**  
The `ClinicalDecisionSupport` class provides real-time AI-powered analysis:

- **`analyze_results()`** — Flags abnormal results (H, L, critical flags) and generates structured `ClinicalRecommendation` objects with severity, confidence, and action.
- **`generate_differential()`** — Uses LLM (gpt-4o-mini) to produce differential diagnoses from symptoms and lab results.
- **`check_clinical_guidelines()`** — Maps diagnoses to applicable clinical guidelines with evidence levels.

**Layer 2 — Clinical Agent (`agents/clinical_agent.py`):**  
The `ClinicalAgent` exposes CDS as agent tools with human-in-the-loop approval:

| Tool | Description | Requires Approval |
|---|---|---|
| `suggest_interpretation` | Interpret single lab result | Yes |
| `analyze_clinical_pattern` | Analyze multi-test patterns | No |
| `suggest_reorder` | Suggest re-running a test | Yes |

All suggestions go through `ai_suggest()` and `approval_store.submit()` from `app.ai.guardrails` and `app.ai.approval`.

### 1.2 Recommendation Model

```python
@dataclass
class ClinicalRecommendation:
    id: str
    type: str          # abnormal_result, critical_value, etc.
    severity: str      # info, warning, critical
    title: str
    description: str
    evidence: list[str]
    confidence: float  # 0.0 - 1.0
    action: str        # review_by_physician, immediate_intervention, etc.
```

---

## 2. Drug Interaction and Allergy Detection

### 2.1 DrugInteractionDetector

`DrugInteractionDetector` (`clinical.py:111`) provides:

- **`register_interaction()`** — Load known drug-drug interactions into memory
- **`check_interaction()`** — Look up interaction between two drugs
- **`check_prescription()`** — Analyze a full medication list for pairwise interactions
- **`check_allergy()`** — Match drug names against patient allergy records with severity escalation

**Interaction Model:**
```python
@dataclass
class DrugInteraction:
    drug_a: str
    drug_b: str
    severity: str        # minor, moderate, severe, contraindicated
    description: str
    recommendation: str
    mechanism: str       # pharmacokinetic, pharmacodynamic
    evidence_level: str  # A, B, C, D
```

### 2.2 Contraindication DB Model

The `Contraindication` model (`clinical/cds/models.py:142`) stores structured drug-disease, drug-drug, and drug-lab contraindications:

- Subject (drug/condition) → Contraindicated item
- Relationship type, severity, mechanism, management guidance
- Absolute vs. relative contraindication flags
- Evidence and source tracking

---

## 3. Critical Result Detection

### 3.1 CriticalResultDetector

`CriticalResultDetector` (`laboratory_intelligence.py:114`) implements threshold-based critical value detection:

- Configurable per-test thresholds (critical_low, critical_high)
- Batch detection across result sets
- Returns structured `CriticalResult` with direction (low/high) and severity (panic)

### 3.2 Clinical Alert Model

The `ClinicalAlert` model (`clinical/cds/models.py:97`) provides persistent alerting:

- Alert type, severity, patient/encounter/provider linkage
- Trigger code and value tracking
- Acknowledgment and resolution workflow
- `ClinicalAlertAction` — tracks actions taken on alerts

---

## 4. Clinical Pathways and National Guidelines

### 4.1 Order Sets & Care Bundles

The CDS models define clinical pathways:

- **`OrderSet`** / **`OrderSetItem`** — Condition-specific order sets with priority, optional/required items, sequence, frequency, and instructions
- **`CareBundle`** / **`CareBundleElement`** — Evidence-based care bundles with compliance thresholds and all-or-none scoring

### 4.2 Preventive Recommendations

`PreventiveRecommendation` (`clinical/cds/models.py:210`) provides guideline-driven preventive screening:

- Age range, gender filtering
- Risk factor assessment
- Evidence level per recommendation
- Source and guideline linkage

### 4.3 Legacy Preventive Engine

The `ai/preventive/` directory contains rule-based engines:

- `preventive_engine.py` — Age/gender-based test suggestions
- `preventive_rules.py` — Structured rule definitions

---

## 5. Explainable AI and Human Approval Workflow

### 5.1 Human-in-the-Loop

Every clinical AI action follows the principle: **AI = Suggest, Human = Approve, System = Enforce**

The approval workflow (`app.ai.approval`):
1. `ai_suggest()` — Creates a suggestion with operation type, payload, model, confidence
2. `approval_store.submit()` — Records suggestion for human review
3. `approval_store.approve/reject()` — Human acts on the suggestion
4. System enforces the result

### 5.2 Confidence Scoring

- All suggestions include confidence scores (0.0–1.0)
- Recommendations include the AI model and version that generated them
- The `EvaluationFramework` (`governance.py:202`) tracks accuracy, bias, safety, and hallucination scores per model version

### 5.3 Clinical Summarization

`ClinicalSummarizer` (`clinical.py:158`) generates LLM-powered summaries:

- **`summarize_results()`** — Converts raw lab results into narrative clinical summaries with key findings and recommendations
- **`generate_history_summary()`** — Produces longitudinal history summaries from past result batches

---

## 6. Reference Range Intelligence

### 6.1 Delta Checking

`DeltaChecker` (`laboratory_intelligence.py:54`) compares current vs. previous values:

- Configurable significant delta thresholds (% and absolute)
- Batch checking across result history
- Flag generation (significant_increase, significant_decrease)

### 6.2 Quality Control Analysis

`QCAnalyzer` (`laboratory_intelligence.py:166`) implements Westgard rules for QC:

| Rule | Description |
|---|---|
| 1-2s | Warning — 1 value exceeds 2 SD |
| 1-3s | Reject — 1 value exceeds 3 SD |
| 2-2s | 2 consecutive values exceed 2 SD |
| R-4s | Range of 2 values exceeds 4 SD |
| 4-1s | 4 consecutive values exceed 1 SD on same side |
| 10x | 10 consecutive values on same side of mean |

- Statistics calculation (mean, SD, CV%)
- Multi-instrument QC data support

### 6.3 Anomaly Detection

The legacy `ai/anomaly_detection.py` provides simple delta-based anomaly detection (>3× previous value).

---

## 7. File Reference

| File | Description |
|---|---|
| `backend/app/ai_fabric/clinical.py` | CDS, drug interaction, clinical summarization |
| `backend/app/ai_fabric/laboratory_intelligence.py` | Delta check, critical results, QC, workload |
| `backend/app/ai_fabric/agents/clinical_agent.py` | Clinical agent with human-in-the-loop approval |
| `backend/app/clinical/cds/models.py` | CDS ORM models (alerts, order sets, care bundles, contraindications, reminders) |
| `backend/app/clinical/enums.py` | Clinical enums |
| `backend/app/clinical/quality/models.py` | Quality models |
| `backend/app/clinical/knowledge/models.py` | Knowledge models |
| `ai/clinical/clinical_ai/clinical_engine.py` | Legacy rules-based clinical engine |
| `ai/clinical/clinical_ai/clinical_rules.py` | Clinical rule definitions |
| `ai/anomaly_detection.py` | Legacy anomaly detection |
| `ai/preventive_engine.py` | Legacy preventive screening |
| `ai/preventive/preventive_ai/preventive_engine.py` | Structured preventive engine |

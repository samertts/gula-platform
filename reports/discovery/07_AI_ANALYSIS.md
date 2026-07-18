# GULA Platform — AI Analysis
**Date:** 2026-07-17

---

## 1. AI Component Inventory

| Component | Location | Status | Purpose |
|-----------|----------|--------|---------|
| AI Routes | `backend/app/routes/ai.py` (39,938 bytes) | **Production** | Clinical AI + human-in-loop |
| AI Telemetry | `backend/app/routes/ai_telemetry.py` (19,846 bytes) | **Production** | Interaction dataset collection |
| AI Sandbox | `backend/app/ai/` | **Production** | Read-only operation registry |
| AI Guardrails | `backend/app/ai/` | **Production** | Payload validation, classification |
| Approval Store | `backend/app/ai/` | **Production** | Human-in-loop (30min TTL) |
| System Optimizer | `backend/app/ai/` | **Production** | /proc metrics + AI analysis |
| AI Service | `services/ai/main.py` (225 lines) | **Functional** | Ollama-only microservice |
| AI Top-Level | `ai/` | **Functional** | Gateway, outbreak, Ali Reza, etc. |
| Clinical Engine | `backend/app/services/clinical_engine.py` | **Production** | 4 sub-engines orchestrator |
| Clinical Intelligence | `backend/app/services/clinical_intelligence.py` | **Production** | 15 multi-test patterns |
| Interpretation | `backend/app/services/interpretation.py` (1,100+ lines) | **Production** | 30+ tests Arabic/English |

---

## 2. AI Providers

| Provider | Integration | Location | Status |
|----------|-------------|----------|--------|
| **Ollama** (local) | HTTP `http://ollama:11434` | `services/ai/main.py` | Production |
| **Gemini** (Google) | Google AI SDK / HTTP gateway | `backend/app/gateways/google_ai.py` | Route-level |
| **Groq** (cloud) | HTTP API | `backend/app/routes/ai.py` | Route-level |

Executive Order 3 & 4 mandate: Only local Ollama AI, no external providers.
**Contradiction**: Backend routes support Gemini and Groq despite local-only mandate.

---

## 3. Clinical AI Capabilities

### Smart Interpretation Engine (`interpretation.py` — 1100+ lines)
- 30+ lab tests with Arabic + English interpretations
- Tests covered: glucose, Hb, WBC, platelets, creatinine, urea, cholesterol, triglycerides, ALT, AST, TSH, potassium, sodium, HbA1c, vitamin D, iron studies, CRP, ESR, procalcitonin, cardiac markers, coagulation, hormones, urinalysis, pancreas
- Multi-level thresholds: normal, low, high, critical_high
- Age/gender-aware (e.g., pediatric hemoglobin)

### Clinical Engine v2.1 (`clinical_engine.py`)
- 4 sub-engines with priority-based conflict resolution:
  1. `ali_reza` — direct measurement interpretation
  2. `clinical_intelligence` — multi-test pattern detection
  3. `epidemiology` — outbreak signals
  4. `samir` — guidance/recommendations

### Clinical Intelligence (`clinical_intelligence.py`)
- 15 composite clinical alerts:
  1. Sepsis risk (WBC + CRP + procalcitonin + lactate)
  2. DKA (glucose + ketones + pH)
  3. Severe anemia (Hb + HCT + reticulocytes)
  4. Thyroid storm (TSH + T3 + T4)
  5. Renal failure (creatinine + BUN + eGFR + K)
  6. Hepatic injury (ALT + AST + bilirubin + PT)
  7. Electrolyte crisis (Na + K + Ca + Mg)
  8. Hyperlipidemia (cholesterol + TG + LDL)
  9. Acute MI (troponin + CK-MB + ECG)
  10. Pancreatitis (amylase + lipase)
  11. Iron deficiency anemia (Hb + ferritin + TIBC)
  12. Inflammatory sepsis (CRP + ESR + procalcitonin)
  13. Coagulopathy (PT + aPTT + INR + platelets)
  14. Hepatic failure (albumin + bilirubin + PT)
  15. Metabolic syndrome (glucose + HbA1c + lipids)

### Top-Level AI Modules (`ai/`)
- AI Gateway (DeepSeek, Gemini, HuggingFace)
- Ali Reza — Arabic lab advice engine
- Anomaly detection
- Lab brain (reference ranges)
- Population health analytics
- Preventive health engine
- Outbreak detection (200+ count threshold)
- Clinical CDS rules engine
- Demand prediction
- Lab dashboard AI

---

## 4. AI Safety Architecture

### AI Sandbox (`backend/app/ai/`)
- Read-only operation registry
- No write/modify operations allowed
- All AI operations are non-destructive

### AI Guardrails
- Operation classification (safe/risky/blocked)
- Payload validation against schema
- Risk scoring per request

### Approval Store
- Human-in-the-loop for risky operations
- 30-minute TTL on pending approvals
- Audit trail for all AI decisions

### AI Interaction Dataset
- `ai_interactions` table: prompt, response, latency, confidence, risk_level
- `ai_feedback` table: user feedback (helpful/not_helpful/incorrect)
- `ai_retrieval_refs` table: source documents used
- `ai_unresolved_questions` table: questions AI couldn't answer

---

## 5. Executive Order Violations Found

| Order | Mandate | Evidence | Status |
|-------|---------|----------|--------|
| EO 3 | Only local Ollama AI | `routes/ai.py` uses Gemini + Groq | **VIOLATED** |
| EO 4 | No external AI providers | `gateways/google_ai.py` exists | **VIOLATED** |
| EO 19 | 3 AI tiers (Operational, Clinical, Population) | Implemented in `services/ai/main.py` | **Compliant** |

---

## 6. Critical Findings

| Finding | Evidence | Risk |
|---------|----------|------|
| **EO 3 & 4 violations** | Gemini + Groq integrations exist | **HIGH** — regulatory non-compliance |
| **Duplicate AI engines** | services/ai (Ollama-only) vs routes/ai.py (multi-provider) | **MEDIUM** — fragmentation |
| **Clinical intelligence non-functional** | 15 syndrome patterns defined but no evidence of triggering | **MEDIUM** — may be dead code |
| **AI interaction dataset captured** | Lawful data collection | **LOW** — compliant |
| **No vector database** | No pgvector, Pinecone, or Qdrant found | **MEDIUM** — no RAG capability |
| **No MCP servers** | No Model Context Protocol | **LOW** — not yet needed |
| **Interpretation engine is rule-based** | Not ML/AI — hard-coded thresholds | **LOW** — deterministic is safer for clinical |

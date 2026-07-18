# GULA Platform — AI Atlas

**Classification:** CONFIDENTIAL
**Date:** 2026-07-18
**AI Maturity:** Production for clinical rules; schema/partial for LLM-based AI

---

## 1. Current AI Modules

### Backend AI (Monolith)

| Module | Location | Status | Purpose |
|--------|----------|--------|---------|
| Clinical interpretation | `services/interpretation.py` | ✅ 5 test types | glucose, HbA1c, TSH, potassium, hemoglobin |
| Clinical intelligence | `services/clinical_intelligence.py` | ⚠️ Partial | Multi-test syndrome patterns |
| Clinical engine | `services/clinical_engine.py` | ⚠️ Partial | Rule-based clinical logic |
| Epidemiology | `services/epidemiology.py` | ⚠️ Partial | Population health analysis |
| AI guardrails | `ai/guardrails.py` | ⚠️ Partial | Safety filters |
| AI sandbox | `ai/sandbox.py` | ⚠️ Partial | Isolated execution |
| AI approval | `ai/approval.py` | ⚠️ Partial | Human-in-the-loop workflow |
| System optimizer | `ai/system_optimizer.py` | ⚠️ Partial | Adaptive concurrency |
| Ali Reza engine | `services/ali_reza_engine.py` | ⚠️ Partial | Arabic clinical rules |
| AI telemetry routes | `routes/ai_telemetry.py` | ✅ Complete | Usage tracking |

### Top-Level AI Modules

| Module | Location | Status | Issue |
|--------|----------|--------|-------|
| AI service | `ai/ai_service.py` | ❌ Externals | Calls DeepSeek, Gemini, HuggingFace (violates EO4) |
| AI agent | `ai/ai_agent.py` | ❌ Externals | Calls OpenAI |
| Anomaly detection | `ai/anomaly_detection.py` | ⚠️ 8-line stub | Not functional |
| Lab brain | `ai/lab_brain.py` | ⚠️ 23-line stub | Not functional |
| Population health | `ai/population_health.py` | ⚠️ 14-line stub | Not functional |
| Outbreak detection | `ai/outbreak/outbreak_detector.py` | ❌ Broken | Imports non-existent module |
| Clinical AI | `ai/clinical/clinical_ai/` | ⚠️ Stubs | Rule-based only |
| Population AI | `ai/population/population_ai/` | ⚠️ Stubs | Local JSON file |
| Preventive AI | `ai/preventive/preventive_ai/` | ⚠️ Stubs | Rule-based |
| Lab business AI | `ai/lab_business_ai/` | ⚠️ Stubs | Demand prediction stubs |

### Microservice AI

| Service | Location | Status |
|---------|----------|--------|
| AI service (Ollama-only) | `services/ai/main.py` | ✅ Local-only, 3 tiers (operational/clinical/population) |

### Frontend AI

| Integration | Location | Status |
|-------------|----------|--------|
| Gemini AI (lab results) | `frontend-v2/src/services/geminiService.ts` | ⚠️ Calls Google Gemini |
| AI assistant widget | `frontend/` HTML files | ⚠️ Inline Gemini/DeepSeek calls |
| AI Summary | `frontend-v2/src/components/AISummary.tsx` | ⚠️ Component exists |
| Global AI assistant | `frontend-v2/src/components/GlobalAiAssistant.tsx` | ⚠️ Component exists |

---

## 2. AI Governance Status

| Article | Constitutional Mandate | Status |
|---------|----------------------|--------|
| §5.1 | AI Constitution & Guardrails | ⚠️ Partial — guardrails.py exists, not comprehensive |
| §5.2 | Explainability for every AI output | ❌ Missing |
| §5.3 | Prompt Registry (versioned, immutable) | ❌ Missing |
| §5.4 | Model Registry (version, provenance, validation) | ❌ Missing |
| §5.5 | Model Validation Pipeline | ❌ Missing |
| §5.6 | Model Monitoring / Drift Detection | ❌ Missing |
| §5.7 | Hallucination Detection | ❌ Missing |
| §5.8 | Bias Detection / Monitoring | ❌ Missing |
| §5.9 | AI Audit Trail | ❌ Missing |
| §5.10 | Human-in-the-Loop Approval | ⚠️ Partial — approval.py exists |

---

## 3. AI Infrastructure Gaps

| Gap | Priority | Impact |
|-----|----------|--------|
| No AI Gateway (single entry point) | **P0** | Ad-hoc AI integration, no governance |
| No model routing | **P0** | Hardcoded model selection per feature |
| No safety engine for clinical AI | **P0** | Risk of harmful outputs |
| No RAG / vector database | **P1** | AI lacks medical context; no document Q&A |
| No hallucination detection | **P1** | Clinical safety risk |
| No confidence scoring | **P1** | Cannot auto-approve safe outputs |
| No cost tracking | **P1** | Cannot budget AI spend |
| No multi-model support | **P1** | Vendor lock-in |
| External provider calls (EO violation) | **P1** | Regulatory non-compliance |
| No offline AI fallback | **P2** | Service degrades without internet |
| No AI audit trail | **P2** | Cannot verify AI decisions |
| No model benchmarking | **P2** | Cannot compare quality |
| No prompt management | **P2** | Prompts scattered in code |

---

## 4. Proposed Architecture: Sovereign AI Platform (SAP)

### Phase 1: Foundation (Months 1-3)
1. **AI Gateway** — Single gRPC/REST entry point for all AI operations
2. **Local Model Router** — Route between Ollama models, no external calls
3. **Safety Engine** — Prompt injection detection, output validation, clinical thresholds
4. **Audit Integration** — Every AI operation logged to hash-chained audit log
5. **Remove external AI calls** — Gate/remove all direct provider calls

### Phase 2: Intelligence (Months 4-6)
1. **Cloud Model Router via SCG** — Add external providers through Sovereign Connector Gateway
2. **Clinical Interpretation 2.0** — Expand from 5 to 50+ test types
3. **RAG Engine** — Medical knowledge base (guidelines, literature, internal data)
4. **Confidence Scoring** — Auto-approve high-confidence results, flag others

### Phase 3: Agents (Months 7-12)
1. **Agent Runtime** — Citizen, Doctor, Lab, Ministry agents
2. **Tool Framework** — AI agents use tools via SCG
3. **Multi-modal** — Vision for radiology, voice for clinical notes
4. **Continuous Benchmarking** — Automated quality evaluation

---

## 5. Immediate AI Cleanup Actions

| Action | Location | Timeline |
|--------|----------|----------|
| Remove or gate external AI calls | `ai/ai_service.py`, `ai/ai_agent.py` | Week 1 |
| Fix broken imports | `ai/outbreak/outbreak_detector.py` | Week 2 |
| Audit frontend AI calls | `frontend-v2/`, `frontend/` | Week 2-3 |
| Consolidate AI into SAP | `services/ai/main.py` | Month 1-2 |
| Evaluate ali_reza_engine for clinical rules | `backend/app/services/` | Month 2 |

# GULA PLATFORM — AI MASTER PLAN

**Status:** VERIFIED (from audit) + PROPOSED (architecture)
**Date:** 2026-07-17

---

## CURRENT AI STATE (Verified)

### Backend AI Modules
| Module | Location | Status |
|--------|----------|--------|
| Clinical interpretation engine | `backend/app/services/interpretation.py` | ✅ 5 test types (glucose, HbA1c, TSH, potassium, hemoglobin) |
| Clinical intelligence | `backend/app/services/clinical_intelligence.py` | ⚠️ Partial |
| Clinical engine | `backend/app/services/clinical_engine.py` | ⚠️ Partial |
| Epidemiology | `backend/app/services/epidemiology.py` | ⚠️ Partial |
| AI guardrails | `backend/app/ai/guardrails.py` | ⚠️ Partial |
| AI sandbox | `backend/app/ai/sandbox.py` | ⚠️ Partial |
| AI approval | `backend/app/ai/approval.py` | ⚠️ Partial |
| System optimizer | `backend/app/ai/system_optimizer.py` | ⚠️ Partial |
| AI interactions DB | `backend/app/models/ai_interaction.py` | ✅ Schema complete |
| AI telemetry routes | `backend/app/routes/ai_telemetry.py` | ✅ Routes exist |

### Top-Level AI Modules
| Module | Location | Status |
|--------|----------|--------|
| AI service (DeepSeek/Gemini/HuggingFace) | `ai/ai_service.py` | ❌ Calls external providers (violates EO4) |
| AI agent (OpenAI) | `ai/ai_agent.py` | ❌ Calls external provider |
| Anomaly detection | `ai/anomaly_detection.py` | ⚠️ 8-line stub |
| Lab brain | `ai/lab_brain.py` | ⚠️ 23-line stub |
| Population health | `ai/population_health.py` | ⚠️ 14-line stub |
| Outbreak detection | `ai/outbreak/outbreak_detector.py` | ❌ Imports non-existent module |
| Clinical AI | `ai/clinical/clinical_ai/` | ⚠️ Rule-based stubs |
| Population AI | `ai/population/population_ai/` | ⚠️ Reads local JSON file |
| Preventive AI | `ai/preventive/preventive_ai/` | ⚠️ Rule-based |
| Lab business AI | `ai/lab_business_ai/` | ⚠️ Demand prediction stubs |
| Ali Reza engine | `backend/app/services/ali_reza_engine.py` | ⚠️ Arabic clinical rules |

### Microservice AI
| Service | Location | Status |
|---------|----------|--------|
| AI service (Ollama only) | `services/ai/main.py` | ✅ Local-only, 3 tiers (operational/clinical/population) |

### Frontend AI
| Integration | Location | Status |
|-------------|----------|--------|
| Gemini AI (lab results) | `frontend-v2/src/services/geminiService.ts` | ⚠️ Calls Google Gemini |
| AI assistant widget | `frontend/` HTML files | ⚠️ Inline Gemini/DeepSeek calls |
| AI summary | `frontend-v2/src/components/AISummary.tsx` | ⚠️ Component exists |
| Global AI assistant | `frontend-v2/src/components/GlobalAiAssistant.tsx` | ⚠️ Component exists |

---

## AI INFRASTRUCTURE GAPS

| Gap | Impact | Priority |
|-----|--------|----------|
| No AI Gateway (single entry point) | Ad-hoc AI integration, no governance | P0 |
| No model routing | Hardcoded model selection per feature | P0 |
| No safety engine for clinical AI | Risk of harmful outputs | P0 |
| No RAG/Knowledge base | AI lacks medical context | P1 |
| No hallucination detection | Clinical safety risk | P1 |
| No confidence scoring | Cannot auto-approve safe outputs | P1 |
| No cost tracking | Cannot budget AI spend | P1 |
| No multi-model support | Vendor lock-in | P1 |
| No offline AI fallback | Service degrades without internet | P2 |
| No AI audit trail | Cannot verify AI decisions | P2 |
| No model benchmarking | Cannot compare quality | P2 |
| No prompt management | Prompts scattered in code | P2 |

---

## PROPOSED AI ARCHITECTURE

The **Sovereign AI Platform (SAP)** is documented separately in `reports/AI_PLATFORM_ARCHITECTURE.md`. Key points:

### Phase 1: Foundation (Months 1-3)
1. **AI Gateway** — Single gRPC/REST entry point for all AI operations
2. **Local Model Router** — Route between Ollama models, no external calls
3. **Safety Engine** — Prompt injection detection, output validation, clinical thresholds
4. **Audit Integration** — Every AI operation logged to hash-chained audit log
5. **Remove external AI calls** — Gate/remove all direct provider calls

### Phase 2: Intelligence (Months 4-6)
1. **Cloud Model Router** — Add OpenAI/Anthropic/DeepSeek support via SCG
2. **Clinical Interpretation 2.0** — Expand from 5 to 50+ test types
3. **RAG Engine** — Medical knowledge base (guidelines, literature, internal data)
4. **Confidence Scoring** — Auto-approve high-confidence results, flag others

### Phase 3: Agents (Months 7-12)
1. **Agent Runtime** — Citizen, Doctor, Lab, Ministry agents
2. **Tool Framework** — AI agents use tools via SCG
3. **Multi-modal** — Vision for radiology, voice for clinical notes
4. **Continuous Benchmarking** — Automated quality evaluation

---

## EXISTING AI CLEANUP

| Action | Location | Timeline |
|--------|----------|----------|
| Remove or gate external AI calls | `ai/ai_service.py`, `ai/ai_agent.py` | Week 1 |
| Fix broken imports | `ai/outbreak/outbreak_detector.py` | Week 2 |
| Audit frontend AI calls | `frontend-v2/`, `frontend/` | Week 2-3 |
| Consolidate AI service into SAP | `services/ai/main.py` | Month 1-2 |
| Evaluate ali_reza_engine for clinical rules | `backend/app/services/` | Month 2 |

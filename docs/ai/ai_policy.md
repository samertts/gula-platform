# GULA AI Policy

**Version:** 1.0  
**Status:** RATIFIED  

---

## 1. AI Philosophy

**AI suggests. Humans decide. Systems enforce.**

GULA's AI is designed as a clinical assistant, not an autonomous agent. Every AI capability is built on a foundation of safety, transparency, and human control. AI autonomy is strictly limited to non-clinical, non-safety-critical domains.

## 2. AI Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  User Input │────→│  AI Firewall │────→│    Router   │
│  (Clinician)│     │  (Injection  │     │  (Provider  │
│             │     │   Detection) │     │  Selection)  │
└─────────────┘     └──────────────┘     └──────┬──────┘
                                                 │
                    ┌────────────────────────────┐
                    │        AI Providers        │
                    │  Ollama │ Gemini │ OpenAI  │
                    │  Claude │ Azure  │ vLLM    │
                    │  OpenRouter │ DeepSeek     │
                    └───────────────┬────────────┘
                                    │
┌─────────────┐     ┌──────────────┐     ┌──────┴──────┐
│   Output    │←────│  AI Firewall │←────│  Guardrails │
│  (Clinician)│     │  (PII/       │     │  (Safety    │
│             │     │   Validation)│     │   Check)    │
└─────────────┘     └──────────────┘     └─────────────┘
```

## 3. AI Constitution

### Article 1: Patient Safety First
AI must never compromise patient safety. Critical clinical decisions require human approval.

### Article 2: Data Privacy
AI must respect patient privacy. No patient data is used for model training without explicit consent.

### Article 3: Human Oversight
Every AI clinical suggestion requires human review before action. AI may not autonomously modify, delete, or create clinical data.

### Article 4: Transparency
AI decisions must be explainable. Every suggestion must carry provenance (model, version, confidence, rationale).

### Article 5: Fairness
AI must not discriminate. Models must be evaluated for bias across demographic groups.

### Article 6: Accountability
AI system failures are engineering failures. Accountability rests with the engineering team, not the AI.

### Article 7: Conservatism
Clinical AI should be conservative. When uncertain, the AI should express uncertainty rather than guess.

## 4. AI Safety Architecture

### 4.1 Guardrails (MANDATORY)
Every AI component must have guardrails that classify operations:

| Classification | Description | Required Approval |
|---------------|-------------|------------------|
| DISPLAY_ONLY | Read-only information display | None (auto-approve) |
| ENRICHMENT | Data enrichment without clinical impact | None (auto-approve) |
| SUGGESTION | Clinical suggestions requiring action | Human approval required |
| BLOCKED | Cannot be performed by AI regardless of approval | Absolutely blocked |

### 4.2 Absolutely Blocked Operations
AI may NEVER perform these operations under any circumstances:

1. `validate_order` — Validate a lab order
2. `modify_result` — Modify a lab result
3. `delete_patient` — Delete a patient record
4. `send_critical_alert` — Send critical value alerts
5. `release_results` — Release results to patient
6. `approve_qa` — Approve quality assurance steps
7. `override_doctor` — Override a doctor's order
8. `prescribe_medication` — Prescribe medication
9. `diagnose_disease` — Give a diagnosis
10. `modify_interpretation` — Modify an existing interpretation

### 4.3 Sandboxed Execution
All AI operations that produce clinical output must execute in a sandbox:
- Operation whitelist (only registered operations allowed)
- All outputs marked `display_only=True` by default
- No direct database write access
- No direct API mutation access

### 4.4 Human-in-the-Loop
AI suggestions requiring action go through an approval lifecycle:

```
Pending → Approved → Executed
       → Rejected
       → Expired (30-minute TTL)
```

## 5. AI Provider Policy

### 5.1 Provider Priority

For clinical AI, providers are prioritized by:

1. **Local (Ollama / vLLM):** Preferred for latency, privacy, and sovereignty
2. **Regional (Gemini):** Acceptable for non-critical workloads
3. **Cloud (OpenAI, Claude, Azure):** Fallback only

Local LLMs must always be tried first. Cloud providers are fallbacks.

### 5.2 Provider Requirements

| Requirement | Standard |
|-------------|----------|
| Data residency | Data must stay in-region where possible |
| Training data | Patient data must not be used for training |
| SLA | Provider must meet clinical availability requirements |
| Security | Provider must have SOC 2 or equivalent |
| Audit trail | All API calls must be logged with full context |

### 5.3 Fallback Chain

```
Ollama (local) → Gemini (regional) → Groq (fallback) → OpenAI (emergency)
```

## 6. AI Model Governance

### 6.1 Model Approval
All models used in clinical AI must go through formal approval:

1. **Submit:** Model metadata, evaluation results, bias assessment
2. **Review:** AI Board + Clinical Board review
3. **Approve/Reject:** Formal decision with rationale
4. **Registry:** Approved models registered with version, provider, capabilities

### 6.2 Model Evaluation

Models must be evaluated on:

| Dimension | Method | Threshold |
|-----------|--------|-----------|
| Accuracy | Ground truth comparison | >90% |
| Bias | Demographic group analysis | <5% variance |
| Safety | Adversarial testing | No harmful outputs |
| Hallucination | Factual consistency | <2% hallucination rate |
| Toxicity | Content filtering | No toxic outputs |
| Fairness | Equal outcome across groups | Statistical parity |
| Robustness | Input perturbation | Stable outputs |

### 6.3 Prompt Registry
All clinical prompts must be:
- Versioned (draft → review → approved → active → deprecated → retired)
- Reviewed by Clinical Board before activation
- Immutable once approved (new version required for changes)
- Archived for audit purposes

## 7. AI Security

### 7.1 Prompt Injection Protection
Every AI input must be checked for:
- Instruction override attempts
- Jailbreak attempts
- SQL injection
- XSS
- Credential leakage
- Role-playing attacks
- Context manipulation

### 7.2 PII Protection
AI outputs must be scanned for:
- National IDs
- Email addresses
- Phone numbers
- Credit card numbers
- Full names (when not expected)
- IP addresses

Matching PII must be redacted or masked before output.

### 7.3 Output Validation
AI outputs must be validated:
- Empty/large output detection
- Confidentiality pattern detection
- Format compliance
- Clinical plausibility

## 8. AI Observability

### 8.1 Required Metrics
Every AI interaction must record:
- Model and provider used
- Request and response tokens
- Latency (p50, p95, p99)
- Cost
- Success/error status
- Guardrail classification
- Approval status
- User and lab ID

### 8.2 Monitoring
- Per-model performance dashboards
- Error rate alerts
- Latency alerts
- Cost tracking
- Usage patterns
- Safety event monitoring

## 9. AI Cost Management

### 9.1 Cost Optimization
- Use local models by default (no cost)
- Cost-optimized routing for non-critical tasks
- Token usage budgets per tenant
- Caching for repeated queries
- Rate limiting per user

### 9.2 Budget Tracking
- Per-provider cost tracking
- Per-tenant cost allocation
- Monthly budget alerts
- Cost anomaly detection

## 10. AI Development Rules

### 10.1 For AI Engineers
- Every AI feature must include guardrails
- Every AI feature must include approval workflow
- Every AI feature must include monitoring
- Every AI feature must include fallback strategy
- Every AI feature must be evaluated before deployment

### 10.2 For AI Agents (System)
When AI agents (like this one) operate on the GULA codebase:
- Always analyze before implementing
- Never assume — verify with repository evidence
- Always respect architecture boundaries
- Always update affected documentation
- Always run quality gates after implementation
- Never introduce hidden dependencies
- Never modify the Engineering Constitution without explicit approval

## 11. AI Risk Management

| Risk | Mitigation | Owner |
|------|-----------|-------|
| Hallucination in clinical output | Guardrails, human review, sandbox, evaluation | AI Team |
| Patient data leakage | PII protection, encryption, audit | Security Team |
| Model bias | Evaluation, diverse training data, monitoring | AI Team |
| Provider dependency | Multi-provider gateway, local-first | AI Team |
| Cost escalation | Budget tracking, caching, local models | Operations |
| Regulatory non-compliance | AI Constitution, Clinical Board, audit | Compliance |

---

*This AI Policy is mandatory. All exceptions require AI Board approval.*

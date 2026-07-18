# AI Security Report — Governance, Bias, Guardrails & Privacy Compliance

**PI-005 | GULA Platform v2.1.0**  
**Date:** 2026-07-16  
**Status:** FINAL

---

## 1. AI Governance

### 1.1 AIGovernance System

The `AIGovernance` class (`governance.py:371`) integrates four governance subsystems:

| Subsystem | File | Purpose |
|---|---|---|
| PromptRegistry | `governance.py:59` | Version-controlled prompt management |
| ModelApproval | `governance.py:130` | Model approval workflow |
| EvaluationFramework | `governance.py:202` | Multi-dimension model evaluation |
| AIConstitution | `governance.py:264` | Ethical principles and compliance |

### 1.2 Model Approval Workflow

Models follow a gated approval pipeline:

```
Submit → PENDING → Evaluate (7 dimensions) → REVIEW → APPROVED / REJECTED / CONDITIONAL
                                                          ↓
                                                   DEPLOYMENT (staging → production)
```

Each model version requires:
- Evidence package (benchmark results, validation data)
- Human reviewer sign-off
- Optional conditional approval with constraints

### 1.3 Audit Trail

Every AI action is auditable through:
- `AIObserver` — Records all inference requests/responses with model, provider, user, cost, latency, success status
- `ClinicalAlert` — Persistent alerting with acknowledgment and resolution tracking
- Governance logs — Prompt promotions, model approvals, evaluation results

### 1.4 Monitoring

The AI fabric exposes comprehensive monitoring:
- `GET /ai/fabric/observability/statistics` — Aggregate performance
- `GET /ai/fabric/observability/errors` — Recent error listing
- `GET /ai/fabric/observability/daily-usage` — Daily cost and volume trends
- `GET /ai/fabric/observability/model/{model}` — Per-model performance

---

## 2. Bias Detection and Hallucination Detection

### 2.1 Evaluation Dimensions

The `EvaluationFramework` scores models on:

| Dimension | Bias/Hallucination Detection |
|---|---|
| **Accuracy** | Correctness of outputs against ground truth |
| **Bias** | Measures demographic fairness (target ≤ 0.10) |
| **Safety** | Harmful content detection (target ≥ 0.90) |
| **Hallucination** | Factual accuracy under retrieval conditions (target ≤ 0.10) |
| **Toxicity** | Toxic language detection (target ≤ 0.05) |
| **Fairness** | Inter-group outcome parity (target ≥ 0.80) |
| **Robustness** | Performance under adversarial perturbations (target ≥ 0.70) |

### 2.2 Threshold Configuration

Thresholds are configurable per dimension:

```python
self._thresholds = {
    EvaluationDimension.ACCURACY: 0.8,
    EvaluationDimension.BIAS: 0.1,
    EvaluationDimension.SAFETY: 0.9,
    EvaluationDimension.HALLUCINATION: 0.1,
    EvaluationDimension.TOXICITY: 0.05,
    EvaluationDimension.FAIRNESS: 0.8,
    EvaluationDimension.ROBUSTNESS: 0.7,
}
```

Models must pass ALL dimensions with configured thresholds before production deployment.

---

## 3. Prompt Registry and Versioning

### 3.1 PromptVersion Model

```python
@dataclass
class PromptVersion:
    id: str
    name: str
    version: str           # Semantic versioning (1.0.0)
    content: str           # Prompt template content
    system_prompt: str     # System-level instructions
    model: str             # Target model
    author: str
    status: PromptStatus   # draft → review → approved → active → deprecated → retired
    changelog: str
    created_at: float
    approved_by: str
    tags: list[str]
    metadata: dict
```

### 3.2 Lifecycle Management

```
DRAFT → REVIEW → APPROVED → ACTIVE → DEPRECATED → RETIRED
```

- **DRAFT** — Initial creation, editable
- **REVIEW** — Under review, locked for editing
- **APPROVED** — Ready for activation
- **ACTIVE** — Currently serving production traffic (only one per name)
- **DEPRECATED** — No longer recommended, kept for rollback
- **RETIRED** — Removed from service

### 3.3 API Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/ai/fabric/governance/prompt/register` | POST | Register new prompt version |
| `/ai/fabric/governance/prompt/{name}` | GET | Retrieve prompt (latest or specific version) |
| `/ai/fabric/governance/promote` | POST | Promote prompt to new status |
| /list on prompt_registry | — | List all prompts with version history |

---

## 4. AI Safety Guardrails and Sandbox

### 4.1 AIFirewall

The `AIFirewall` (`security.py:178`) provides defense-in-depth:

**Input Protection:**
- `PromptInjectionProtector` — 12 injection pattern categories
- `PIIProtector` — 8 PII type detection and redaction
- Real-time blocking with risk scoring

**Output Protection:**
- `OutputValidator` — Blocked phrases, confidentiality patterns, length limits
- `PIIProtector` — Automatic PII redaction in outputs

### 4.2 Guardrail Integration

AIGovernance integrates with `app.ai.guardrails` and `app.ai.approval`:

```python
def check_guardrail(self, operation: str, payload: dict[str, Any]) -> dict[str, Any]:
    suggestion = ai_suggest(operation=operation, payload=payload, ...)
    approval = approval_store.submit(suggestion)
    return {
        "allowed": True,
        "suggestion_id": suggestion.id,
        "approval_id": approval.id,
    }
```

### 4.3 Sandbox Execution

The AI fabric uses `app.ai.sandbox` for isolated AI execution, ensuring:
- No filesystem access
- No network access (except to AI providers)
- Memory limits
- Timeout enforcement

---

## 5. Privacy and FHIR Compliance

### 5.1 PII Protection Layers

**Layer 1 — Input Filtering:**
All inputs are scanned for PII before reaching AI models:
- SSN, National ID, Email, Phone, Credit Card, Names with titles, IP addresses

**Layer 2 — Context Isolation:**
Patient data queries enforce `lab_id = current_user.lab_id` tenant isolation.

**Layer 3 — Output Sanitization:**
All AI outputs are validated for:
- PII leakage (automatic redaction)
- Confidential data patterns
- Length and content constraints

**Layer 4 — Encryption:**
- `patients.national_id` encrypted at rest
- All patient data queries require proper tenant scoping

### 5.2 FHIR Alignment

The clinical data models align with FHIR R4 resources:
- `Patient` → Patient resource
- `LabOrder` → ServiceRequest
- `LabResult` → DiagnosticReport / Observation
- `ClinicalAlert` → Communication
- `Contraindication` → AllergyIntolerance / DetectedIssue
- `CareBundle` → CarePlan / Goal

### 5.3 Data Residency

- No patient data leaves the platform boundary
- Local AI (Ollama, vLLM) enables fully offline inference
- External providers only receive de-identified, PII-free text
- All AI operations are logged with full audit trail

### 5.4 Security Headers

The middleware stack includes:
- CSP (Content Security Policy)
- HSTS (HTTP Strict Transport Security)
- X-Frame-Options, X-Content-Type-Options
- SecurityHeadersMiddleware

---

## 6. Security Agents

### 6.1 SecurityAgent

The `SecurityAgent` (`agents/security_agent.py`) provides autonomous security monitoring:

| Tool | Description | Risk Detection |
|---|---|---|
| `detect_intrusion` | IP-based intrusion detection | Integration with `app.security.intrusion_detection` |
| `analyze_access_pattern` | User behavior anomaly detection | High-volume detection, sensitive action flagging |
| `check_prompt_injection` | Text-based injection analysis | 5 injection patterns, risk scoring |

### 6.2 Intrusion Detection

Integration with `app.security.intrusion_detection`:
- IP reputation checking
- Rate limit enforcement
- Block/allow decisions
- Integration with `ConcurrencyLimitMiddleware` and `DegradedModeMiddleware`

---

## 7. File Reference

| File | Description |
|---|---|
| `backend/app/ai_fabric/governance.py` | Prompt registry, model approval, evaluation, constitution |
| `backend/app/ai_fabric/security.py` | AIFirewall, PII protection, injection detection, output validation |
| `backend/app/ai_fabric/observability.py` | Usage tracking and audit |
| `backend/app/ai_fabric/agents/security_agent.py` | Security monitoring agent |
| `backend/app/ai_fabric/routes.py` | Security inspection endpoints |
| `backend/app/ai_fabric/enums.py` | AI enums (permissions, model lifecycle) |
| `backend/app/core/self_healing.py` | Circuit breaker and degraded mode |
| `backend/app/security/` | Security infrastructure |

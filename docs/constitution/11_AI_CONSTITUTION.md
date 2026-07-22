# GULA AI Constitution

## Principles

### 1. Human Oversight
Every AI-generated recommendation, prediction, or classification is reviewed by a qualified human before it affects patient care. AI assists; clinicians decide. No fully autonomous clinical decisions.

### 2. Explainability
Every AI output must be explainable to a clinician in terms they understand. Black-box models that cannot explain their reasoning are not used for clinical decision support. Feature importance, confidence scores, and alternative predictions are surfaced.

### 3. Safety First
AI features that affect patient care are tested against:
- False positive / false negative rates
- Bias across demographic groups
- Edge case behavior
- Degradation under distribution shift
- Adversarial robustness

### 4. Privacy by Design
AI models are trained on de-identified data or within secure enclaves. Patient data never leaves the platform's security boundary for model training without explicit consent and governance approval.

### 5. Continuous Validation
Model performance is monitored in production. Drift detection triggers retraining or alerting. Models that fall below accuracy thresholds are automatically disabled.

### 6. Human-in-the-Loop
Critical AI decisions require human confirmation:
- Critical result flagging → clinician reviews before notification
- Diagnosis suggestion → physician reviews before chart inclusion
- Treatment recommendation → ordering clinician confirms before dispensing

## AI Capabilities

| Capability | Autonomy Level | Review Required |
|------------|---------------|-----------------|
| Result validation | Assisted | Yes, for criticals |
| Reference range flagging | Automated | No |
| Duplicate detection | Automated | No |
| Clinical decision support | Suggested | Yes |
| Predictive analytics | Advisory | Yes, for interventions |
| Image analysis | Assisted | Yes, radiologist review |
| NLP / document AI | Assisted | Yes, for clinical use |
| Administrative automation | Automated | No |
| Public health surveillance | Automated | No |

## Prohibited Uses

- Fully autonomous diagnosis
- Fully autonomous treatment recommendation
- Patient-facing diagnostic AI without clinician mediation
- AI systems that cannot explain their reasoning for clinical decisions
- Models trained on patient data without governance approval

## AI Governance

7. **AI model registry** tracks every deployed model: version, training data, performance metrics, validation results, and approval status.

8. **Model lifecycle** includes: research → development → validation → approval → deployment → monitoring → retirement.

9. **Bias testing** is mandatory before deployment. Models must demonstrate acceptable performance across age, gender, geographic, and socioeconomic groups.

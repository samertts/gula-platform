# Risk Management

**Mission:** GAIOS-MASTER-001
**Created:** 2026-08-04
**Status:** Active

---

## Purpose

Risk management framework for the GULA Platform.
Every significant task requires risk assessment.

---

## Risk Score Formula

```
Risk Score = Likelihood × Impact
```

| Likelihood | Score | Description |
|---|---|---|
| Rare | 1 | Very unlikely |
| Unlikely | 2 | Could happen |
| Possible | 3 | Might happen |
| Likely | 4 | Will probably happen |
| Almost Certain | 5 | Will happen |

| Impact | Score | Description |
|---|---|---|
| Negligible | 1 | No significant effect |
| Minor | 2 | Some inconvenience |
| Moderate | 3 | noticeable impact |
| Major | 4 | Serious impact |
| Catastrophic | 5 | System failure/data loss |

---

## Risk Matrix

|  | Negligible (1) | Minor (2) | Moderate (3) | Major (4) | Catastrophic (5) |
|---|---|---|---|---|---|
| **Almost Certain (5)** | 5 MEDIUM | 10 HIGH | 15 HIGH | 20 CRITICAL | 25 CRITICAL |
| **Likely (4)** | 4 LOW | 8 MEDIUM | 12 HIGH | 16 HIGH | 20 CRITICAL |
| **Possible (3)** | 3 LOW | 6 MEDIUM | 9 MEDIUM | 12 HIGH | 15 HIGH |
| **Unlikely (2)** | 2 LOW | 4 LOW | 6 MEDIUM | 8 MEDIUM | 10 HIGH |
| **Rare (1)** | 1 LOW | 2 LOW | 3 LOW | 4 LOW | 5 MEDIUM |

---

## Risk Levels

| Level | Score | Action |
|---|---|---|
| LOW | 1-4 | Accept, monitor |
| MEDIUM | 5-9 | Mitigate, document |
| HIGH | 10-15 | Mitigate required, review |
| CRITICAL | 16-25 | Stop, escalate, approve |

---

## Risk Assessment Template

```markdown
## Risk Assessment

### Risk 1: [Risk Name]
- **Likelihood:** [1-5]
- **Impact:** [1-5]
- **Score:** [calculated]
- **Level:** [LOW/MEDIUM/HIGH/CRITICAL]
- **Mitigation:** [How to reduce]
- **Detection:** [How to detect]
- **Recovery:** [How to recover]
- **Residual Risk:** [Score after mitigation]
```

---

## Required Risk Assessments

| Task Type | Risk Assessment Required |
|---|---|
| Bug fix | NO |
| New feature | YES (MEDIUM+) |
| Architecture change | YES (HIGH+) |
| Security change | YES (HIGH+) |
| Database migration | YES (HIGH+) |
| Data deletion | YES (CRITICAL) |
| Constitution change | YES (CRITICAL) |

---

## Risk Registry

| ID | Risk | Score | Level | Status |
|---|---|---|---|---|
| (none tracked yet) | | | | |

---

## Related Knowledge

- `.ai/core/quality/GOVERNANCE_RULES.md` — Governance rules
- `.ai/core/kup/QUALITY_REQUIREMENTS.md` — Quality requirements
- `docs/ai/RISK_REGISTER.md` — Project risk register

---

## References

- `docs/ai/RISK_REGISTER.md` — Full risk register
- `security/RISK_REGISTER.md` — Security risks

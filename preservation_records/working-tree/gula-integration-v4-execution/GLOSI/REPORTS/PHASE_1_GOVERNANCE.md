# GLOSI Phase 1 — Governance and Evaluation Framework

**Date:** 2026-11-15
**Status:** PASS (documentation and machine-readable rules established)
**Scope:** Governance only; no adopted project and no GULA Core change.

## 1. Deliverables

| Document | Purpose |
|---|---|
| `GLOSI/GOVERNANCE.md` | Roles, decision authority, review workflow, conflict-of-interest rules, audit trail |
| `GLOSI/EVALUATION_FRAMEWORK.md` | 100-point model, weights, confidence, bands, status semantics |
| `GLOSI/MASTER_REGISTRY_SCHEMA.md` | JSON schema, required fields, validation rules |
| `GLOSI/SOURCE_CATALOG.md` | Authoritative source hierarchy and evidence expectations |
| `GLOSI/DOMAIN_TAXONOMY.md` | Health, standards, infrastructure, AI, and government categories |
| `GLOSI/INTEGRATION_POLICY.md` | ADOPT/INTEGRATE/ADAPT/REIMPLEMENT/STUDY/MONITOR/REJECT controls |
| `GLOSI/SECURITY_AND_LICENSE_POLICY.md` | Security, privacy, license, and supply-chain gates |
| `GLOSI/DECISION_RECORDS/README.md` | Decision-record lifecycle and statuses |
| `GLOSI/DECISION_RECORDS/TEMPLATE.md` | Mandatory decision-record template |
| `GLOSI/ROADMAP.md` | Phases and research batches B2–B8 |

## 2. Evaluation model

| Dimension | Weight |
|---|---|
| Functionality fit | 15 |
| Maturity and stability | 15 |
| Security and privacy | 15 |
| Interoperability | 15 |
| Engineering quality | 10 |
| License sustainability | 10 |
| Reliability and scalability | 10 |
| Cost and maintenance | 5 |
| Iraqi context | 5 |
| **Total** | **100** |

Bands: `90–100 excellent`, `80–89 strong_candidate`, `70–79 needs_verification`, `60–69 limited_study`, `0–59 not_recommended`.

Decision states are proposed by default. `APPROVED` is impossible without a COMPLETE evaluation, named technical/security/legal reviewers, a known license, completed security and legal review, and an ADR reference.

## 3. Human control points

- Technical, security, and legal reviewers are declared but remain `UNASSIGNED`; no human approval exists.
- A critical security finding blocks adoption regardless of score.
- Unknown or incompatible licenses block adoption.
- No project may be imported into GULA Core by GLOSI automation.

## 4. Phase result

**PASS** — Governance and the evaluation framework are documented and encoded in the validator.

**Limitation:** Governance roles are proposed; organizational appointment is pending.

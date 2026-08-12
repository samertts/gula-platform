# Phase 18-03 — Phase 18 Regulatory Mapping

This is the Phase-18 deep-dive mapping. The cross-phase global mapping is in
[`../STANDARDS_MAPPING_MATRIX.md`](../STANDARDS_MAPPING_MATRIX.md).

## Healthcare Regulatory Standards (Phase 18 in scope)

### ISO 15189 — Medical Laboratories

- **Clauses 4.1 / 4.2** (organisation, quality management) → governance
  architecture, role-separation matrix
- **Clauses 4.13 / 4.14** (records, internal audit) → audit chain, quarterly
  checklist
- **Clauses 5.4 / 5.5** (pre-examination, examination) → sample chain of
  custody, order state machine
- **Clauses 5.7 / 5.8** (post-examination, reporting) → critical-result
  delivery, result-release governance
- **Clause 5.10** (laboratory information management) → tenant isolation,
  audit, backup, DR

### CAP — College of American Pathologists

- Result release governance with two-person QC override
- Reference-range and calibration audit (data quality)
- Proficiency testing data flow (where applicable)

### CLSI — Clinical and Laboratory Standards Institute

- Reference-interval data governance
- Quality control + quality assurance audit
- Method-validation evidence retention

## Information-Security Regulatory References

### ISO 27001 — Information Security Management

- A.5 (organisational controls) → governance architecture
- A.6 (people controls) → role separation, two-person rule
- A.8 (technological controls) → encryption, audit chain, access logs
- A.9 (controls related to information security incidents) → incident-response
  framework

### ISO 27799 — Health Information Security

- 6.1 / 6.2 (information security policies for health) → patient-data
  encryption at rest, audit immutability, retention floor
- 7 (asset management) → dependency register

### NIST SP 800-53 (moderate baseline)

- AC (access control), AU (audit), CP (contingency planning), IA
  (identification & authentication), IR (incident response), RA (risk
  assessment), SC (system & communications protection), SI (system &
  information integrity).

The mapping is documentation-only; certifying to NIST 800-53 is out of
scope for the platform without explicit program funding.

## Privacy & Data-Protection References

### GDPR (referenced as a maturity baseline; jurisdictional mapping required)

- Art. 5 (principles) → minimisation, retention floor (configurable), data
  quality
- Art. 9 (special categories) → health data treatment, encryption,
  authorisation
- Art. 25 (data protection by design) → tenant isolation, fail-closed
  behavior
- Art. 30 (records of processing) → audit chain
- Art. 32 (security of processing) → controls inventory
- Art. 33 (notification of breach) → incident-response framework

### National Iraqi Data Protection (jurisdictional)

- Data residency for patient identifiers and clinical data
- Cross-border transfer authorization workflow
- Sovereign retention floors per data class

This area is **jurisdiction-led**. The platform respects the configured
retention and residency policy; the policy itself is set by Iraqi
regulatory authority.

## AI / Algorithmic Governance References

### ISO/IEC 42001 — AI Management System

- AI capability registry
- AI lifecycle management
- AI explainability + auditability hooks (Phase 21)

### WHO Ethics & Governance of AI for Health

- Human oversight (clinical override is mandatory)
- Transparency (explainability metadata)
- Equity (no model is deployed without bias review)
- Privacy (AI models do not exfiltrate identifiers)

### EU AI Act — high-risk system practices (maturity reference)

- Risk management system (per-capability risk register)
- Data governance (training data provenance)
- Technical documentation (model card)
- Record-keeping (AI invocation audit)
- Transparency (human review of recommendations)
- Human oversight (AI is advisory)
- Accuracy / robustness (fail-closed under degraded conditions)

## Per-Standard Gap Calls

For each above, the gap register identifies:

- Which controls exist as code (e.g., RBAC, audit chain).
- Which exist as process (e.g., quarterly review).
- Which are documented-only and need promotion.
- The owner, ETA, and dependent phase for promotion.

Gap entries flow into `06-governance-risk-register.md`.

# GULA PLATFORM — LEGAL MASTER PLAN

**Status:** PROPOSED (strategic recommendations)
**Date:** 2026-07-17

---

## CURRENT STATUS

**Verified Ground Truth:**
- **No LICENSE file** exists at repository root
- `setup.py` declares `MIT License` (classifiers)
- `pyproject.toml` declares `Proprietary` license
- `package.json` declares `PROPRIETARY` license
- Contradictory license declarations = **legal risk**

---

## RECOMMENDED LICENSE: AGPL v3 (Community Edition)

### Rationale
| Criterion | AGPL v3 | MIT | Apache 2.0 | GPL v3 |
|-----------|---------|-----|------------|--------|
| Strong copyleft | ✅ | ❌ | ❌ | ✅ |
| Network use triggers copyleft | ✅ | ❌ | ❌ | ❌ |
| Patent protection | ❌ | ❌ | ✅ | ✅ |
| Compatible with commercial licensing | ✅ | ✅ | ✅ | Moderate |
| Healthcare industry standard | Moderate | Common | Common | Low |
| Prevents proprietary forking | ✅ | ❌ | ❌ | ✅ |
| Government adoption | Moderate | High | High | Low |

### Why AGPL v3
1. **Network copyleft** — Any organization running modified GULA as a web service must release their modifications. This prevents proprietary SaaS forks.
2. **Dual licensing** — AGPL allows commercial licensing for organizations that want proprietary use without copyleft obligations.
3. **Community protection** — Ensures all improvements benefit the community.
4. **Industry precedent** — MongoDB, GitLab, Element (Matrix) use AGPL for similar open-core models.

---

## CONTRIBUTOR LICENSE AGREEMENT (CLA)

### Required for all contributions

**CLA Terms:**
1. Contributor grants project **perpetual, worldwide, non-exclusive, royalty-free license** to their contribution
2. Project may **relicense** the contribution under any license (including commercial)
3. Contributor warrants they have the right to submit the contribution
4. No transfer of copyright ownership — contributor retains copyright

**Implementation:**
- Use **CLA Assistant** (GitHub App) for automated CLA signing
- Block PRs until CLA is signed
- Store signed CLAs in repository

---

## DEVELOPER CERTIFICATE OF ORIGIN (DCO)

### Recommended alongside CLA

- DCO is simpler than CLA (one line: `Signed-off-by: Name <email>`)
- Used by Linux Kernel, Docker, many CNCF projects
- Verifies contributor has right to submit
- Less legal friction for small contributions

**Recommendation:** Use CLA for code contributions, DCO for documentation/trivial fixes.

---

## COMMERCIAL LICENSE

### Enterprise Edition License Terms

| Clause | Terms |
|--------|-------|
| License type | Per-instance, annual subscription |
| Usage | Unlimited users within licensed organization |
| Modification | Permitted for internal use |
| Distribution | Not permitted (no redistribution of modified version) |
| Sublicensing | Not permitted |
| Warranty | 90-day bug fix warranty |
| Liability | Limited to license fees paid |
| Termination | On breach, with 30-day cure period |
| Audit rights | Annual usage audit with 30-day notice |

### Government Contract Addendum

| Clause | Terms |
|--------|-------|
| Data sovereignty | All data remains within national borders |
| Source escrow | Source code deposited with government-approved escrow |
| Security audits | Right to conduct independent security audit |
| SLA | 99.9% uptime, 4-hour response for critical issues |
| Termination for convenience | Government may terminate with 90 days notice |
| Force majeure | Standard clause |
| Governing law | Laws of the contracting country |

---

## TRADEMARK STRATEGY

### What to Register

| Mark | Class | Jurisdiction | Priority |
|------|-------|-------------|----------|
| **GULA** (word mark) | 9, 42, 44 | Iraq, UAE, KSA, EU, US | High |
| **GULA Logo** (design mark) | 9, 42, 44 | Iraq, UAE, KSA, EU, US | High |
| **GULA Health** (word mark) | 44 | Iraq, EU, US | Medium |
| **Sovereign Connector Gateway** | 9, 42 | Strategic markets | Low (descriptive) |

### Trademark Usage Policy

```yaml
permitted_use:
  - Referring to the official GULA platform
  - Stating compatibility with GULA ("Works with GULA")
  - Community discussion about GULA

prohibited_use:
  - Using GULA in company/product name without permission
  - Implying official affiliation without authorization
  - Registering confusingly similar domains (gula-platform.org is official)
  - Using GULA logo without trademark notice (®/™)

enforcement:
  - Monitoring for domain squatting
  - Cease and desist for unauthorized commercial use
  - Trademark infringement claims for counterfeit versions
```

---

## COPYRIGHT STRATEGY

### Copyright Notices

Every source file should contain:
```python
# Copyright (c) 2024-2026 GULA Platform Contributors
# SPDX-License-Identifier: AGPL-3.0-or-later OR Commercial
```

### Copyright Assignment
- Contributors retain copyright (per CLA)
- Project maintains collective work copyright
- Commercial licensees get no copyright transfer

---

## PATENT STRATEGY

### Patentable Innovations (Assessment)

| Innovation | Patentability | Priority | Notes |
|-----------|--------------|----------|-------|
| Healthcare MPI with Fellegi-Sunter + NID short-circuit | Low | N/A | Existing prior art |
| SCG intent-based AI-connector architecture | **Medium** | File provisional | Novel architecture |
| Multi-tier sovereign AI routing with clinical safety gating | **Medium** | File provisional | Specific to healthcare AI |
| Offline-first lab instrument data pipeline | Low | N/A | Existing prior art |
| Consent model with cryptographic chain verification | **Low** | N/A | Based on existing patterns |
| Hash-chained audit with DB trigger enforcement | Low | N/A | Existing prior art |

**Recommendation:** File provisional patents for SCG intent-based architecture and sovereign AI routing to establish defensive prior art.

---

## OPEN SOURCE COMPLIANCE

### Current Status

| Requirement | Status | Action Needed |
|-------------|--------|---------------|
| LICENSE file | ❌ Missing | Add AGPL v3 |
| Copyright headers | ❌ Missing | Add to all files |
| Third-party license notices | ⚠️ Partial | Generate SBOM with licenses |
| Dependency license compatibility | ❌ Not audited | Full dependency audit needed |
| Export control classification | ❌ Not done | Self-classification under EAR |
| Privacy policy | ❌ Missing | Draft for SaaS deployments |
| Terms of service | ❌ Missing | Draft for SaaS deployments |

---

## PRIVACY & DATA PROTECTION

### GDPR Readiness

| Requirement | Status | Gap |
|-------------|--------|-----|
| Data Processing Agreement | ❌ | Need DPA template |
| Data Protection Officer | ❌ | Appoint DPO |
| Data breach notification | ⚠️ | Audit trail exists, notification process missing |
| Consent management | ⚠️ | Consent table exists, GDPR-required fields missing |
| Right to deletion | ⚠️ | Patient delete routes exist but no complete erasure workflow |
| Data portability | ❌ | No export endpoint |
| Privacy Impact Assessment | ❌ | Not conducted |

### HIPAA Considerations

| Requirement | Status | Gap |
|-------------|--------|-----|
| BA agreement | ❌ | Need BAA template |
| Encryption at rest | ⚠️ | National ID only, not all PHI |
| Access controls | ⚠️ | RBAC exists, no automatic timeouts, no session recording |
| Audit controls | ✅ | Hash-chained audit log |
| Integrity controls | ✅ | Optimistic locking, audit chain |
| Emergency access | ⚠️ | Break glass exists in governance but no procedure |

---

## COUNTRY-SPECIFIC CONSIDERATIONS

| Country | Regulations | Impact |
|---------|-------------|--------|
| **Iraq** | National Health Data Law, SNDHS | Primary compliance requirement |
| **KSA** | NPHIES, PDPL (Personal Data Protection Law) | Data localization, consent requirements |
| **UAE** | DHA (Dubai), DOH (Abu Dhabi), Nesa | Certification required per emirate |
| **Jordan** | MoH digital health regulations | Similar to Iraq |
| **Egypt** | Personal Data Protection Law | Data localization, registration required |
| **EU** | GDPR | Complete overhaul for data processing |
| **US** | HIPAA, HITECH | BAAs, security rule, privacy rule |

---

## LEGAL ROADMAP

| Phase | Action | Timeline | Cost Estimate |
|-------|--------|----------|---------------|
| **P0** | Add AGPL v3 LICENSE file | Week 1 | $0 (choose license) |
| **P0** | Add copyright headers to all files | Week 2-4 | $5-10K (automated) |
| **P1** | Register trademark (GULA) in Iraq and UAE | Month 1-2 | $2-5K per jurisdiction |
| **P1** | Draft and implement CLA | Month 1 | $3-5K (legal review) |
| **P1** | Resolve license contradictions in setup.py/pyproject.toml | Week 1 | $0 |
| **P2** | Full dependency license audit | Month 2 | $2-3K (automated tooling) |
| **P2** | Draft DPA, Terms of Service, Privacy Policy | Month 2-3 | $10-20K (legal) |
| **P2** | File provisional patents (SCG + AI routing) | Month 3 | $15-25K (patent attorney) |
| **P3** | Register trademark in KSA, EU, US | Month 3-6 | $10-20K |
| **P3** | GDPR compliance project | Month 4-6 | $30-50K |
| **P4** | HIPAA compliance assessment | Month 6-8 | $20-40K |
| **P4** | Country-specific compliance (KSA, UAE, Jordan) | Month 6-12 | $20-50K per country |

---

## TOTAL LEGAL BUDGET (Year 1)

| Category | Estimated Cost |
|----------|---------------|
| License selection + headers | $5-10K |
| Trademark registration (initial) | $15-25K |
| CLA + DCO implementation | $3-5K |
| Patent filing (provisional) | $15-25K |
| DPA/TOS/Privacy Policy | $10-20K |
| Dependency audit | $2-3K |
| GDPR readiness | $30-50K |
| Total Year 1 | **$80-138K** |

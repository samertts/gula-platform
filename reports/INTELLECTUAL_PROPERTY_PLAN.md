# GULA PLATFORM — INTELLECTUAL PROPERTY PLAN

**Status:** PROPOSED
**Date:** 2026-07-17

---

## WHAT CAN BE LEGALLY PROTECTED

### Copyright (automatic upon creation)
| Asset | Protection | Notes |
|-------|-----------|-------|
| Source code | ✅ Full copyright | All original code is copyrighted |
| Documentation | ✅ Copyright | API docs, architecture docs, guides |
| Architecture diagrams | ✅ Copyright | Visual representations |
| Logo designs | ✅ Copyright + Trademark | Register trademark separately |
| API specifications | ✅ Copyright | OpenAPI specs, SDK definitions |
| AI model weights (trained) | ❓ Unclear | Training data + process may be trade secret |
| Database schema design | ✅ Copyright | Creative selection/organization |

### Trademark (requires registration)
| Asset | Protectable | Priority |
|-------|------------|----------|
| "GULA" word mark | ✅ Yes | **High** — Register immediately |
| GULA Logo (stylized) | ✅ Yes | **High** |
| "GULA Platform" | ✅ Yes | Medium |
| "Sovereign Connector Gateway" | ⚠️ Likely descriptive | Low |
| "GULA Health" | ✅ Yes | Medium |

### Patent (requires filing)
| Innovation | Status | Action |
|-----------|--------|--------|
| Intent-based API → Connector architecture (SCG) | Unfiled | File provisional patent |
| Multi-tier AI routing with clinical safety gating | Unfiled | File provisional patent |
| Fellegi-Sunter MPI with NID short-circuit | Prior art exists | Do not file |
| Hash-chained audit with DB trigger | Prior art exists | Do not file |

### Trade Secret
| Asset | Protection | Risk |
|-------|-----------|------|
| Deployment configurations | Confidential | Low if not distributed |
| Customer lists | Confidential | Medium |
| Business processes | Confidential | Medium if not discoverable |
| AI training data/curation | Confidential | High — source could be reverse-engineered |
| Security incident details | Confidential | Low |

---

## WHAT CANNOT BE PROTECTED

| Asset | Why | Strategy |
|-------|-----|----------|
| Ideas/concepts | Copyright protects expression, not ideas | Document in ADRs, publish as thought leadership |
| Algorithms (standard) | Prior art exists | Use as is, no patent |
| API to standard formats (FHIR, HL7) | Standards must be implemented interoperably | No restriction |
| Facts (lab reference ranges) | Not original creative work | Use authoritative sources |
| SQLAlchemy/base patterns | Common practice | No restriction |
| Docker/naming conventions | Industry standard | No restriction |

---

## COPYRIGHT STRATEGY

### File Headers
Every source file must include:
```python
# Copyright (c) 2024-2026 GULA Platform Contributors
# SPDX-License-Identifier: AGPL-3.0-or-later OR Commercial
```

### Copyright Registration
- **Core platform code** — Register with copyright office in country of incorporation
- **Major releases** — Register each major version
- **Cost:** ~$35-55 per registration (US)

### Enforcement
- GitHub DMCA takedown process for unauthorized reproduction
- Cease and desist for commercial misuse
- Source code watermarking (optional)

---

## TRADEMARK STRATEGY

### Registration Priority
1. **Iraq** — Primary market, use existing trademark office or regional route
2. **UAE** — Regional hub, Dubai trademark office
3. **KSA** — Saudi Authority for Intellectual Property (SAIP)
4. **EU** — EUIPO for European protection
5. **US** — USPTO for US protection

### Classes
| Class | Description | Goods/Services |
|-------|-------------|----------------|
| 9 | Software | Downloadable software for lab management |
| 42 | SaaS | Platform as a service, cloud computing |
| 44 | Medical | Medical laboratory services, health data |

### Cost Estimate
| Jurisdiction | Per Class | Total (3 classes) |
|-------------|-----------|-------------------|
| Iraq | $200-400 | $600-1,200 |
| UAE | $500-700 | $1,500-2,100 |
| KSA | $500-700 | $1,500-2,100 |
| EU (EUIPO) | €850 | €2,550 |
| US (USPTO) | $350 | $1,050 |

---

## PATENT STRATEGY

### Recommendation: Defensive Patent Pool
1. **File 2 provisional patents** (~$130 each US PTO)
2. **Purpose:** Establish prior art, prevent others from patenting
3. **Do NOT file non-provisional** unless funded — high cost ($10-30K per patent)
4. **Patent pledge:** Commit to non-assertion for open source community

### Provisional Patent Filings

**1. Intent-Based Connector Architecture**
- Novel aspect: AI agent submits intent, SCG resolves via policy → token → connector
- Key claims: Intent schema, policy engine, token broker, isolated runtime
- Filing: US provisional (covers all markets via Paris Convention)

**2. Clinical Safety AI Routing**
- Novel aspect: Multi-tier model routing with clinical sensitivity gating
- Key claims: Routing based on PHI level, offline requirements, safety thresholds
- Filing: US provisional

---

## OPEN SOURCE IP RISKS

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Code copied without attribution | Medium | Low | Copyright notice in every file, DMCA process |
| AGPL violation by SaaS provider | Medium | Medium | Monitoring, enforcement policy |
| Trademark infringement | Medium | Medium | Trademark registration, monitoring |
| Patent troll assertion | Low | High | Defensive patents, prior art |
| Contributor IP claim | Low | Medium | CLA requirement, copyright assignment |
| Trade secret disclosure | Low | High | Access controls, NDAs, compartmentalization |

---

## IP BUDGET (Year 1)

| Item | Cost |
|------|------|
| Copyright registration (core) | $100-200 |
| Trademark registration (Iraq + UAE initial) | $2,500-4,000 |
| Provisional patents (2) | $260 + attorney fees |
| CLA legal review | $3,000-5,000 |
| Total Year 1 | **$6,000-10,000** |

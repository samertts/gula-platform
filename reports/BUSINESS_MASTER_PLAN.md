# GULA PLATFORM — BUSINESS MASTER PLAN

**Date:** 2026-07-17
**Status:** PROPOSED (strategic recommendations)

---

## 1. MARKET POSITION

GULA currently operates as a **vertically integrated LIMS SaaS** for Iraqi medical laboratories. The platform scope has expanded to a **national healthcare platform** covering 19+ clinical domains.

### Current Market
- **Primary:** Iraqi private medical laboratories (1000+ estimated)
- **Secondary:** Iraqi public hospitals and clinics
- **Tertiary:** Ministry of Health (SNDHS integration, NHOP)

### Addressable Market Expansion
| Segment | Size (IQ) | Revenue Potential |
|---------|-----------|------------------|
| Private labs | 1,000-2,000 | $2-5M/yr at $200-500/mo |
| Public hospitals | 200-300 | $1-3M/yr at $500-2000/mo |
| Private hospitals | 100-150 | $0.5-1.5M/yr |
| Ministry of Health | 1 (national) | $1-5M/yr contract |
| Regional (ME/NA) | 10,000+ labs | $20-50M/yr |

---

## 2. OPEN SOURCE STRATEGY

### Recommendation: Open Core + Enterprise Edition

| Edition | License | Features | Price |
|---------|---------|----------|-------|
| **Community Edition** | AGPL v3 | Core LIMS, basic auth, 1 lab | Free |
| **Professional** | Commercial | Multi-lab, QC, AI, support | $200-500/mo |
| **Enterprise** | Commercial | All features, SLA, white-label, on-prem | $1000-5000/mo |
| **Government** | Custom | National deployment, SNDHS, dedicated infra | Custom |

### Rationale
1. **AGPL v3** — Strong copyleft prevents proprietary forking, allows commercial licensing
2. **Open core** drives adoption, community, and ecosystem
3. **Enterprise features** (SNDHS, multi-branch, AI) remain proprietary
4. **Government contracts** require custom licensing

### Risks
- AGPL may deter some enterprise adoption
- Open source competitors could emerge
- Support burden from free users

---

## 3. COMMERCIAL STRATEGY

### Revenue Streams

| Stream | Maturity | Projected Annual (Year 1-3) |
|--------|----------|------------------------------|
| SaaS subscriptions | Current | $50K → $500K → $2M |
| On-prem licenses | Current | $20K → $200K → $1M |
| Professional services | New | $50K → $300K → $1M |
| Training & certification | New | $10K → $100K → $500K |
| Connector marketplace | Future | $0 → $50K → $500K |
| Government contracts | Future | $0 → $500K → $5M |
| AI services (API calls) | Future | $0 → $100K → $500K |

### Pricing Model

**SaaS (monthly):**
| Tier | Labs | Staff | Patients/mo | AI Calls | Price |
|------|------|-------|-------------|----------|-------|
| Starter | 1 | 5 | 1,000 | 100 | $199 |
| Growth | 3 | 20 | 10,000 | 1,000 | $499 |
| Enterprise | Unlimited | Unlimited | Unlimited | 10,000 | $1,999 |

**On-prem (annual):**
| Tier | Price |
|------|-------|
| Starter | $2,400/yr |
| Growth | $6,000/yr |
| Enterprise | $24,000/yr |

---

## 4. LICENSING STRATEGY

### Dual Licensing Model

| Aspect | Community | Commercial |
|--------|-----------|------------|
| License | AGPL v3 | Commercial |
| Cost | Free | Paid |
| Features | Core LIMS only | Full platform |
| Support | Community | SLA-backed |
| White-label | No | Yes |
| Source code | Available | Available (paid) |
| Contribution | CLA required | N/A |

### Contributor License Agreement (CLA)
- **Required for all contributions** to Community Edition
- Grants project the right to relicense under Commercial terms
- Ensures copyright assignment for enforcement

---

## 5. PARTNER PROGRAM

### Partner Tiers

| Tier | Requirements | Benefits |
|------|--------------|----------|
| **Reseller** | $5K/yr, certified staff | 30% margin, lead sharing |
| **Integrator** | $10K/yr, 2 certified staff | 25% margin, priority support |
| **Technology Partner** | Integration built | Co-marketing, early access |
| **Government Partner** | Country-specific | Exclusive territory, joint sales |

---

## 6. CONNECTOR MARKETPLACE

### Business Model
- **Official connectors** (PostgreSQL, Redis, FHIR, HL7) — Free with Enterprise
- **Certified connectors** (Slack, Discord, Jira, etc.) — $50-200/mo each
- **Partner connectors** — Revenue share (70% partner, 30% platform)
- **Community connectors** — Free, community supported
- **Custom connectors** — Professional services engagement

### Revenue Projection
| Year | Connectors | Revenue |
|------|-----------|---------|
| 1 | 10 | $50K |
| 2 | 50 | $200K |
| 3 | 200+ | $1M |

---

## 7. INVESTMENT STRATEGY

### Seed Round ($2M)
- **Purpose:** Product completion, initial sales, compliance certification
- **Use of funds:**
  - Engineering: $1.2M (6-8 engineers for 18 months)
  - Sales & Marketing: $400K
  - Compliance & Legal: $200K
  - Operations: $200K

### Series A ($10M)
- **Purpose:** Regional expansion, enterprise sales, AI platform
- **Use of funds:**
  - Regional offices: $3M (UAE, KSA, Jordan)
  - Enterprise sales: $2M
  - AI/ML R&D: $2.5M
  - Compliance (HIPAA, GDPR): $1.5M
  - Reserve: $1M

### Grant Opportunities

| Grant | Amount | Focus |
|-------|--------|-------|
| World Bank Digital Health | $500K-5M | LMIC health systems |
| EU Horizon Europe | €1-10M | Digital health research |
| Gates Foundation | $100K-3M | Global health |
| USAID Digital Health | $500K-5M | Health system strengthening |
| GIZ (Germany) | €500K-3M | ME health infrastructure |

---

## 8. GOVERNMENT CONTRACTS

### Target Markets (Priority Order)
1. **Iraq** — Ministry of Health (existing SNDHS relationship)
2. **Kurdistan Region** — Regional health ministry
3. **Jordan** — MoH digital transformation
4. **UAE** — DHA, Abu Dhabi Health
5. **Saudi Arabia** — Ministry of Health (Seha, NPHIES)
6. **Egypt** — MoH digital health initiative

### Contract Types
| Type | Value | Duration |
|------|-------|----------|
| National EMR/LIMS platform | $1-5M | 3-5 years |
| Regional health information exchange | $500K-2M | 2-3 years |
| Disease surveillance system | $200K-1M | 1-3 years |
| Training & capacity building | $100K-500K | 1-2 years |

---

## 9. FINANCIAL PROJECTIONS

### Year 1-3 (Conservative)

| Metric | Year 1 | Year 2 | Year 3 |
|--------|--------|--------|--------|
| SaaS customers | 50 | 200 | 500 |
| On-prem deployments | 10 | 40 | 100 |
| Government contracts | 1 | 3 | 5 |
| Revenue | $250K | $1.5M | $5M |
| Gross margin | 60% | 70% | 75% |
| Team size | 8 | 20 | 40 |
| Burn rate | $120K/mo | $250K/mo | $400K/mo |
| Cash need | $2M | $3M | $5M |

---

## 10. INTERNATIONAL EXPANSION ROADMAP

| Phase | Region | Timeline | Investment |
|-------|--------|----------|------------|
| 1 | Iraq | Current | $0 |
| 2 | Kurdistan Region | Month 6 | $50K |
| 3 | Jordan | Month 12 | $200K |
| 4 | UAE | Month 18 | $500K |
| 5 | Saudi Arabia | Month 24 | $1M |
| 6 | Egypt/North Africa | Month 36 | $2M |
| 7 | Turkey | Month 48 | $3M |

---

## 11. LONG-TERM SUSTAINABILITY

### Factors
1. **Open source community** — Reduces marketing cost, drives adoption
2. **Dual licensing** — Ensures revenue from commercial users
3. **Government contracts** — High-value, long-term, recurring
4. **Marketplace** — Creates ecosystem lock-in and recurring revenue
5. **Training/certification** — Low-margin but high-volume revenue
6. **Professional services** — High-margin, builds relationships

### Risks to Sustainability
| Risk | Impact | Mitigation |
|------|--------|------------|
| Government contract dependency | Revenue concentration | Diversify across 5+ countries |
| Open source competitor | Market erosion | Maintain technical lead, focus on clinical safety |
| Brain drain (key engineers) | Product stagnation | Documentation, knowledge transfer, competitive comp |
| Regulatory changes | Compliance cost | Modular compliance, dedicated legal team |
| Currency fluctuation (IQD) | Revenue volatility | Price in USD, local partnerships |

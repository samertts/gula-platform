# GULA Partner Ecosystem Framework

**Version:** 2.1.0  
**Status:** DRAFT  
**Last Updated:** 2026-07-17

---

## 1. Partner Types

### 1.1 Technology Partners

Cloud, infrastructure, and hardware providers whose technology GULA integrates with.

| Partner Type | Examples | Integration Point |
|-------------|----------|-------------------|
| Cloud Provider | DigitalOcean, AWS, Azure, GCP | Deployment scripts, K8s configs |
| Database | PostgreSQL, Redis Labs | Connection pooling, optimization |
| AI/ML | OpenAI, Anthropic, Ollama | AI Fabric gateway (`AIGateway`) |
| Device Manufacturers | Sysmex, Roche, Mindray, Abbott, Beckman Coulter | Device Bridge (`services/device_bridge/`) |
| CDN | Cloudflare, Akamai | Static asset delivery, DDoS protection |
| Monitoring | Grafana, ELK, Sentry | `config/prometheus/`, `config/grafana/` |

**Integration Model:**
- Joint technical integration testing
- Reference architecture documentation
- Co-marketing opportunities
- Priority support for joint customers

### 1.2 Integration Partners

Organizations that integrate their systems with GULA.

| Integration Type | Examples | Mechanism |
|-----------------|----------|-----------|
| EHR Systems | openEHR, FHIR servers | `AdapterBase` at `backend/app/interoperability/` |
| National Platforms | SNDHS (Iraq), NPHIES (KSA), NABIDH (UAE) | Country-specific adapter packs |
| Insurance Systems | Iraqi public/private insurers | Insurance Gateway Pack |
| Lab Information Systems | Legacy LIS data migration | Data migration toolkit |
| Pharmacy Systems | Drug databases, inventory | Pharmacy Pack integration |
| Government Registries | National ID, civil registry | National Identity routes |

**Onboarding:**
1. Sign integration partner agreement
2. Integration partner deploys sandbox instance
3. Joint technical workshop
4. Adapter development & testing
5. Certification testing
6. Production deployment
7. Ongoing maintenance

### 1.3 Implementation Partners

System integrators and consultants who deploy and configure GULA for end customers.

| Tier | Requirements | Services |
|------|-------------|----------|
| Registered | 2+ certified engineers | Basic deployment, user training |
| Silver | 5+ certified engineers, 3+ implementations | Full deployment, custom config |
| Gold | 10+ certified engineers, 10+ implementations | Complex deployments, migrations |
| Platinum | 20+ certified engineers, strategic relationship | Enterprise transformation |

**Certification Path:**
1. `GULA Foundation` — platform architecture, core LIMS
2. `GULA Implementation` — deployment, configuration, migration
3. `GULA Integration` — adapter development, API integration
4. `GULA Advanced` — AI, analytics, performance tuning
5. `GULA Master` — solution architecture, enterprise design

### 1.4 Solution Partners

Independent software vendors (ISVs) who build and sell packs on the GULA marketplace.

| Pack Type | Examples | Revenue Model |
|-----------|----------|---------------|
| Vertical Packs | Radiology, Pharmacy, Blood Bank | Marketplace sale |
| Horizontal Packs | Analytics, Reporting, Compliance | SaaS subscription |
| Connector Packs | Device adapters, FHIR connectors | One-time + maintenance |
| AI Skills | Diagnostic models, prediction engines | Usage-based pricing |

**Solution Partner Requirements:**
- Pass pack certification (Community → Verified → Certified → Enterprise)
- Maintain documentation in Arabic and English
- Provide customer support in covered regions
- Respond to security vulnerabilities within SLA
- Maintain compatibility with latest kernel API

### 1.5 Reseller Partners

Distributors who resell GULA licenses and services.

| Reseller Type | Coverage | Typical Deal Size |
|---------------|----------|-------------------|
| Regional Distributor | Single country | $50K–$500K/year |
| National Reseller | Multi-region within country | $100K–$1M/year |
| Channel Partner | Government/enterprise focus | $200K–$2M/year |

**Reseller Benefits:**
- Wholesale pricing (30–50% discount off list)
- Joint marketing development funds (MDF)
- Lead sharing from platform marketing
- Dedicated partner sales manager
- Co-branded marketing materials
- Quarterly business reviews

### 1.6 Content Partners

Medical content, training, and reference data providers.

| Content Type | Examples | Integration |
|--------------|----------|-------------|
| Medical References | Drug databases, lab test compendia | Reference data packs |
| Clinical Guidelines | WHO, national treatment protocols | Knowledge Graph |
| Training Content | Lab technique videos, CME courses | Learning Pack |
| Terminology | LOINC, SNOMED CT, ICD-10/11 | FHIR interoperability |
| Research Data | Population health stats, clinical trials | Research Pack |

### 1.7 Research Partners

Universities, research institutes, and clinical research organizations.

| Partner Type | Collaboration Model |
|-------------|---------------------|
| Academic Research | De-identified data access, joint publications |
| Clinical Research | Trial patient recruitment, data collection |
| Population Health | Epidemiological studies, outbreak analysis |
| AI Research | Model training datasets, algorithm validation |

**Data Governance:**
- All research data access via `backend/app/consent/`
- De-identification pipeline with IRB oversight
- Audit trail for every data access
- Break-glass emergency override for clinical safety
- Patient opt-in/opt-out via consent management

### 1.8 Government Partners

Ministries of health, national health authorities, and regulatory bodies.

| Partner | Region | Integration |
|---------|--------|-------------|
| Iraqi MoH | Iraq | SNDHS, NHOP |
| KSA MOH | Saudi Arabia | NPHIES, Sehhaty, CBAHI |
| UAE DOH | UAE | NABIDH, Malaffi, Riayati |
| Jordan MoH | Jordan | HAK |
| Egypt MoH | Egypt | Unified Medical Record |
| WHO | Global | ICD-11, disease surveillance |

**Government Partner Benefits:**
- National-level deployment support
- Compliance certification
- Data sovereignty guarantees
- Dedicated security review
- Co-development of government packs
- Priority feature requests

---

## 2. Partner Tier System

### 2.1 Tier Structure

```
                      ┌─────────────┐
                      │  Platinum   │
                      │  Top 5%     │
                      └──────┬──────┘
                             │
                      ┌──────▼──────┐
                      │    Gold     │
                      │  Top 20%    │
                      └──────┬──────┘
                             │
                      ┌──────▼──────┐
                      │   Silver    │
                      │  Mid-tier   │
                      └──────┬──────┘
                             │
                      ┌──────▼──────┐
                      │  Registered │
                      │  Entry      │
                      └─────────────┘
```

### 2.2 Tier Requirements

| Criteria | Registered | Silver | Gold | Platinum |
|----------|-----------|--------|------|----------|
| Signed Agreement | Required | Required | Required | Required |
| Certified Engineers | 0 | 3 | 10 | 20 |
| Completed Projects | 0 | 3 | 10 | 25+ |
| Customer Satisfaction | N/A | >3.5/5 | >4.0/5 | >4.5/5 |
| Support SLA | N/A | Business hours | 24/7 | 24/7 dedicated |
| Revenue (Annual) | $0 | >$50K | >$250K | >$1M |
| Marketplace Apps | 0 | 0 | 2+ | 5+ |
| Security Certification | N/A | Self-attestation | SOC 2 | SOC 2 + ISO 27001 |

### 2.3 Tier Benefits

| Benefit | Registered | Silver | Gold | Platinum |
|---------|-----------|--------|------|----------|
| Revenue Share | 70% | 75% | 80% | 85% |
| Technical Support | Community | Email (24h) | Priority (4h) | Dedicated (1h) |
| Training Credits | 0 | $2K/yr | $10K/yr | $25K/yr |
| MDF (Co-marketing) | $0 | $5K/yr | $25K/yr | $100K/yr |
| Sales Leads | No | Quarterly | Monthly | Weekly |
| Partner Manager | No | Shared | Dedicated | Senior dedicated |
| Early Access | No | Beta only | Beta + RC | All pre-release |
| Custom SLA | No | No | Yes | Yes |
| Joint Roadmap | No | No | Quarterly | Monthly |
| Executive Sponsorship | No | No | Yes | Yes |

---

## 3. Partner Onboarding

### 3.1 Onboarding Flow

```
Application → Screening → Agreement → Technical Setup → Training → Certification → Active
```

### 3.2 Step-by-Step Process

**Step 1: Application**
- Submit partner application via partner portal
- Provide company information, services offered, target market
- Identify partner type(s)
- Provide references (for Silver+ tiers)

**SLA:** 5 business days for initial response

**Step 2: Screening**
- Background check (sanctions, PEP screening)
- Technical capability assessment
- Market fit evaluation
- Reference checks (Silver+)

**SLA:** 10 business days

**Step 3: Partner Agreement**
- Review and sign partner agreement
- Specific terms per partner type:
  - Technology: IP terms, integration commitments
  - Integration: Data handling, security requirements
  - Implementation: Certification requirements, quality standards
  - Solution: Marketplace terms, revenue share, IP ownership
  - Reseller: Territorial rights, minimum commitments
  - Content: Licensing terms, attribution
  - Research: Data use agreement, publication rights
  - Government: Data sovereignty, compliance requirements

**SLA:** 5 business days for countersignature

**Step 4: Technical Setup**
- Access to partner sandbox environment
- API keys and credentials
- Developer documentation access
- Integration environment configuration
- Sample data provisioning

**SLA:** 2 business days

**Step 5: Training**
- Self-paced online courses (GULA Academy)
- Virtual instructor-led training (VILT)
- Hands-on lab exercises
- Certification exam preparation

**Duration:**
- Foundation: 2 days (self-paced)
- Implementation: 3 days (VILT)
- Integration: 2 days (VILT)
- Advanced/Master: 5 days (in-person)

**Step 6: Certification**
- Exam (online, proctored)
- Practical project submission
- Peer review (for Master level)
- Annual recertification required

**Step 7: Active Status**
- Partner profile published on GULA website
- Access to partner portal
- Welcome kit (digital + physical)
- Quarterly business review scheduling
- Kickoff call with partner manager

---

## 4. Partner Portal

### 4.1 Portal Features

The self-service partner portal at `partner.gula.health` provides:

**Dashboard:**
- Revenue summary and trends
- Active deals pipeline
- Certification status and expiry
- Support ticket queue
- Training progress
- Upcoming events

**Deal Registration:**
- Register opportunities with end customers
- Automatic protection period (45 days)
- Deal status tracking
- Co-selling request submission

**Asset Library:**
- Sales presentations and battle cards
- Technical documentation
- Case studies and testimonials
- Demo environments
- Marketing collateral (co-brandable)
- Video tutorials

**Training:**
- Course catalog
- Enrollment and progress tracking
- Certification exam scheduling
- Instructor-led session calendar
- Lab environment access

**Support:**
- Case creation and tracking
- Knowledge base
- Community forum
- Escalation request

**Marketplace (Solution Partners):**
- Pack upload and management
- Version publishing
- Sales analytics
- Customer usage metrics
- Payout history

**Reporting:**
- Monthly/quarterly performance reports
- Customer satisfaction scores
- Revenue by product/region
- Certification compliance

### 4.2 Technical Portal

For integration partners and developers:

- API reference documentation (OpenAPI 3.0)
- Interactive API playground (Swagger UI)
- SDK downloads (Python, JS)
- Webhook testing tools
- Plugin pack scaffolding tools
- Migration script generator
- Performance testing toolkit
- Security scanning tools

---

## 5. Partner Agreement

### 5.1 Key Terms by Partner Type

| Clause | Technology | Integration | Implementation | Solution | Reseller |
|--------|-----------|-------------|----------------|----------|----------|
| Term | 1 year auto-renew | 1 year auto-renew | 1 year auto-renew | 2 year auto-renew | 1 year auto-renew |
| IP Ownership | Joint improvements | Partner owns adapters | N/A | Pack developer owns IP | N/A |
| Non-Compete | Narrow (defined category) | None | None | Narrow (defined domain) | Territory-based |
| Data Handling | No customer data | Agreed scope | Customer data processor | Customer data processor | N/A |
| Minimum Commit | N/A | N/A | N/A | N/A | $50K+/year |
| Revenue Share | N/A | N/A | N/A | 70-85% | 50-70% (discount) |
| Liability Cap | 12mo fees | 12mo fees | 12mo fees | 12mo fees | Deal value |
| Indemnification | IP infringement | IP infringement | Performance | IP + data | IP infringement |
| Audit Rights | Yes (security) | Yes (security) | Yes (quality) | Yes (quality) | Yes (compliance) |
| Termination | 30d notice | 30d notice | 60d notice | 60d notice | 90d notice |

### 5.2 Standard Obligations

**Partner Obligations:**
- Maintain confidentiality of platform IP
- Comply with data protection requirements
- Maintain adequate insurance ($2M cyber liability minimum)
- Provide timely customer support
- Participate in annual business review
- Maintain certification currency
- Report security incidents within 24 hours

**Platform Owner Obligations:**
- Provide API stability and backward compatibility
- Maintain SLA for platform uptime (99.9%)
- Provide technical support per tier
- Provide training and certification materials
- Share roadmap quarterly (Gold+)
- Protect partner IP and confidential information
- Pay commissions/revenue share within 45 days

---

## 6. Revenue Sharing Model

### 6.1 Marketplace Commission Structure

| Transaction | Standard Commission | Partner Share |
|-------------|-------------------|---------------|
| Marketplace pack sale | 20% of gross | 80% of gross |
| Marketplace subscription | 15% of gross | 85% of gross |
| Implementation services | 0% (partner keeps all) | 100% |
| Referral fee (lead to partner) | 10% of partner fee | 90% to partner |
| Co-sell (platform + partner) | 15% of total | 85% of total |

### 6.2 Revenue Share by Partner Tier

| Tier | Marketplace | Co-Sell | Referral |
|------|-------------|---------|----------|
| Registered | 70/30 | 60/40 | 5% referral fee |
| Silver | 75/25 | 65/35 | 7.5% referral fee |
| Gold | 80/20 | 75/25 | 10% referral fee |
| Platinum | 85/15 | 80/20 | 12.5% referral fee |

### 6.3 Payment Terms

- Monthly reconciliation
- Net-45 payment terms
- Minimum payout threshold: $100
- Payment methods: Wire transfer, Wise
- Deductions: Applicable withholding taxes
- Currency: USD (default), local currency options for MENA partners

---

## 7. Partner Performance Metrics

### 7.1 Scorecard Dimensions

| Dimension | Weight | Metrics |
|-----------|--------|---------|
| Revenue | 25% | Gross revenue, revenue growth, deal size |
| Customer Success | 25% | NPS, retention, support satisfaction |
| Technical Excellence | 20% | Certification currency, project quality, innovation |
| Engagement | 15% | Training completion, portal activity, event participation |
| Compliance | 15% | Security posture, audit results, agreement compliance |

### 7.2 Tier Movement

**Upgrade Path:**
- Quarterly review of scorecard
- Meets next-tier requirements → automatic upgrade
- Upgrade effective following quarter
- Benefits apply immediately

**Downgrade Path:**
- Fails to meet current tier for 2 consecutive quarters
- Downgrade effective following quarter
- 60-day notice with remediation plan
- Can re-apply after 6 months at lower tier

**Termination:**
- Breach of agreement terms
- Security incident with negligence
- Repeated SLA failures
- Fraud or misrepresentation
- Immediate termination with cause

### 7.3 Annual Partner Summit

- Top partners invited to annual summit (Baghdad or Dubai)
- Awards for: Partner of the Year, Innovation, Customer Impact, Rising Star
- Roadmap preview and feedback sessions
- Networking and co-innovation workshops
- Technical deep-dives and training

---

## 8. Co-Selling Model

### 8.1 Co-Sell Engagement

```
Lead Identified
    │
    ├─ Platform-sourced → Assigned to matching partner
    ├─ Partner-sourced → Registered for protection
    └─ Joint pursuit → Shared pipeline
    │
    ▼
Opportunity Qualified
    │
    ├─ Partner-led → Partner manages, Platform supports
    └─ Platform-led → Platform manages, Partner supports
    │
    ▼
Solution Design
    │
    ├─ Reference architecture
    ├─ Scoping workshop
    └─ Competitive positioning
    │
    ▼
Proposal & Close
    │
    ├─ Pricing approved
    ├─ Contract signed
    └─ Handoff to delivery
```

### 8.2 Co-Sell Incentives

| Role | Revenue Share | Responsibilities |
|------|--------------|-----------------|
| Partner sells, Partner delivers | 85/15 (partner/platform) | Full sales + delivery |
| Platform sells, Partner delivers | 65/35 (partner/platform) | Platform leads sale, partner deploys |
| Partner sells, Platform delivers | 70/30 (partner/platform) | Partner manages relationship, platform delivers |
| Joint sell, Joint deliver | 50/50 | Equal contribution |

### 8.3 Deal Registration

- Register within 30 days of first customer contact
- Minimum 45-day protection period
- Extendable upon showing progress
- Registered deals are commission-protected
- Dispute resolution via partner manager

---

## 9. Partner Community

### 9.1 Community Platform

**Location:** `community.gula.health`

**Features:**
- Discussion forums by topic (implementation, integration, development)
- Knowledge base with articles and FAQs
- Code samples and reusable components
- Plugin/connector sharing (open source)
- Feature request voting
- Bug reporting and tracking
- Partner directory (searchable by region, expertise, tier)
- Events calendar (webinars, workshops, conferences)

### 9.2 Events

| Event | Frequency | Format | Audience |
|-------|-----------|--------|----------|
| Partner Webinar | Monthly | Virtual, 60min | All partners |
| Regional Meetup | Quarterly | In-person | Regional partners |
| Partner Summit | Annually | In-person (3 days) | Gold+ partners |
| Hackathon | Bi-annually | Hybrid | Developer partners |
| Training Bootcamp | Quarterly | In-person (5 days) | Implementation partners |

### 9.3 Certification Program

**Certification Levels:**
1. **GULA Foundation** — Platform overview, core concepts (online exam)
2. **GULA Implementation** — Deployment, configuration, migration (online exam + project)
3. **GULA Integration** — Adapter development, API mastery (online exam + code review)
4. **GULA Advanced** — AI, analytics, performance optimization (project + presentation)
5. **GULA Master** — Enterprise architecture, solution design (board review)

**Recertification:**
- Foundation + Implementation: every 2 years
- Integration + Advanced: every 1 year
- Master: every 2 years + continuous education credits

---

## Appendix A: Partner Agreement Template (Summary)

```
GULA PARTNER AGREEMENT

1. Parties
2. Definitions
3. Partner Type and Scope
4. Term and Termination
5. Partner Obligations
6. Platform Owner Obligations
7. Intellectual Property
8. Revenue Share / Compensation
9. Confidentiality
10. Data Protection
11. Compliance
12. Warranties
13. Limitation of Liability
14. Indemnification
15. Insurance
16. Dispute Resolution
17. Governing Law
18. General Provisions

SCHEDULE A: Services / Products
SCHEDULE B: Compensation Structure
SCHEDULE C: Service Level Agreement
SCHEDULE D: Data Processing Terms
SCHEDULE E: Security Requirements
```

## Appendix B: Partner Application Form Fields

- Company name, legal entity, registration number
- Headquarters address, country
- Website, LinkedIn, social media
- Primary contact (name, title, email, phone)
- Partner type(s) applying for
- Current healthcare customers (count, names)
- Geographic coverage
- Technical team size and certifications
- Current integrations with healthcare systems
- Service offerings
- References (2-3 customer references)
- Security certifications (if any)
- Annual revenue (optional)
- Business plan (1-page summary)

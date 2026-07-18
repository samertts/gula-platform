# GULA PLATFORM — OPEN SOURCE STRATEGY

**Status:** PROPOSED
**Date:** 2026-07-17

---

## STRATEGIC OBJECTIVES

1. **Drive adoption** — Make GULA the default choice for laboratory and healthcare IT in the Middle East
2. **Build ecosystem** — Community contributors, connector marketplace, partner network
3. **Commercial conversion** — Free Community Edition → paid Enterprise Edition
4. **Government credibility** — Open source = transparency = trust for government deployments
5. **Talent acquisition** — Open source community = recruiting pipeline

---

## COMMUNITY EDITION SCOPE

### Included (Free)

**Core LIMS:**
- Patient management (1,000 patients)
- Lab order management
- Lab result entry and display
- Basic test catalog (50 tests)
- Sample tracking (barcode-based)
- JWT authentication + RBAC
- Single lab tenant
- REST API (rate-limited)
- Basic dashboard
- PDF report generation
- QR code patient cards

**Infrastructure:**
- Docker Compose deployment
- PostgreSQL + Redis
- Prometheus metrics
- Basic health endpoints

### EXCLUDED (Enterprise only)

- Multi-branch lab management
- Quality control (Westgard rules, IQC, EQA)
- AI interpretation and clinical intelligence
- Advanced analytics and epidemiology
- Insurance integration and claims
- National ID integration (SNDHS)
- FHIR/HL7 interoperability
- Device bridge (LabLink-Core)
- Edge AI platform
- Advanced audit and compliance
- White-label and custom branding
- SLA and priority support
- Connector marketplace
- SCG (Sovereign Connector Gateway)
- SAP (Sovereign AI Platform)
- Multi-region and HA deployment
- Government reporting modules
- Enterprise SSO (SAML, OIDC, LDAP)
- Audit and compliance reports

---

## GOVERNANCE MODEL

| Role | Responsibility | Selection |
|------|---------------|-----------|
| **BDFL** (Project Lead) | Final decision authority, vision, trademark | Founder |
| **Core Team** | Code review, architecture, releases | Appointed by BDFL |
| **Committers** | Write access to specific modules | Core Team vote |
| **Contributors** | Submit PRs, issues, translations | Anyone |
| **Community** | Users, testers, advocates | Anyone |

### Voting Process
- Strategic decisions: Core Team supermajority (2/3)
- Technical decisions: Lazy consensus (48h objection period)
- New committers: Core Team vote (majority)
- License changes: BDFL decision + community consultation

---

## RELEASE PROCESS

```yaml
release_cycle:
  major: "Every 12 months (breaking changes)"
  minor: "Every 2-3 months (features)"
  patch: "As needed (bug fixes, security)"
  
versioning: "Semantic Versioning 2.0.0"

process:
  - Feature freeze (2 weeks before release)
  - Release candidate (1 week testing)
  - Changelog generation
  - Tag and sign release
  - Docker image build and push
  - Deploy to community demo instance
  - Announce on GitHub, Twitter, LinkedIn

security_releases:
  - Critical: 24-48 hours turnaround
  - High: 1 week
  - Medium: Next minor release
  - Low: Next major release
```

---

## COMMUNITY ENGAGEMENT

| Channel | Purpose | Target |
|---------|---------|--------|
| GitHub Discussions | Technical Q&A, feature requests | Developers |
| Discord/Slack | Real-time community chat | Contributors |
| Twitter/LinkedIn | Announcements, thought leadership | Healthcare IT |
| YouTube | Tutorials, architecture talks | Technical audience |
| Arabic blog | Regional content | ME healthcare |
| Meetups | Baghdad, Erbil, Amman, Dubai | Regional community |

---

## FUNDING MODEL

| Source | Amount | Description |
|--------|--------|-------------|
| Enterprise licenses | 70% | Primary revenue |
| Professional services | 15% | Implementation, training, custom development |
| Support contracts | 10% | SLA-backed support |
| Sponsorships | 5% | GitHub Sponsors, Open Collective |
| Grants | Variable | World Bank, Gates Foundation, EU Horizon |

---

## COMPETITIVE POSITIONING

### Against Open Source
| Competitor | GULA Advantage |
|------------|----------------|
| OpenMRS | Modern architecture (FastAPI vs Java), Arabic-first, LIMS focus |
| Bahmni | More modern tech, better DevOps, active development |
| OpenELIS | Python-native, DICOM/PACS, device bridge |
| SENAITE | Built-in AI, national platform, connector ecosystem |

### Against Commercial
| Competitor | GULA Advantage |
|------------|----------------|
| Epic (LIMS) | Fraction of cost, open source, Middle East focus |
| Cerner | Modern API, easier deployment, no vendor lock-in |
| Orchard Software | Open core, community, regional compliance |
| LabVantage | AGPL prevents lock-in, sovereign deployment |

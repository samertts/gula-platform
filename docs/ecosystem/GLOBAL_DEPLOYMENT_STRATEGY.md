# GULA Global Deployment Strategy

**Version:** 2.1.0  
**Status:** DRAFT  
**Last Updated:** 2026-07-17  
**Owner:** Platform Architecture Team

---

## 1. Current State

### 1.1 Production Architecture (Iraq)

```
Internet
    │
    ▼
Host Nginx (TLS termination, Let's Encrypt)
    │
    ▼
api-gateway (Docker nginx on 127.0.0.1:8080)
    │
    ├── gula-backend (FastAPI, gunicorn + uvicorn)
    │   ├── PostgreSQL 16 (gula-postgres)
    │   └── Redis 7 (gula-redis)
    │
    ├── services/device_bridge (ASTM/HL7)
    │
    └── frontend apps (React, tRPC, PWA)
```

**Infrastructure:**
- **Hosting:** DigitalOcean Droplet (Ubuntu 22.04)
- **Region:** AMS3 (Amsterdam) — nearest reliable region for Iraq
- **Size:** 8 vCPU, 16GB RAM, 200GB SSD
- **Database:** PostgreSQL 16 on same droplet (single-node)
- **Cache:** Redis 7 on same droplet
- **CDN:** Cloudflare (static assets, DNS, DDoS protection)
- **Backup:** Daily pg_dump to S3-compatible storage
- **Monitoring:** Prometheus + Grafana (internal, SSH tunnel)
- **Scale:** Single backend instance (no HA)

**Limitations:**
- Single point of failure (no HA, no load balancing)
- Limited scalability (vertical only)
- High latency for Iraqi users (Amsterdam routing)
- No data sovereignty guarantees
- No disaster recovery across regions

### 1.2 Current Scale

| Metric | Value |
|--------|-------|
| Active labs | 50–200 (estimate) |
| Daily orders | 5,000–20,000 |
| Daily results | 50,000–200,000 |
| Peak concurrent users | 100–500 |
| Storage used | ~50GB (DB) + ~20GB (files) |
| Uptime | 99.5% (target 99.9%) |

---

## 2. MENA Expansion (2027–2028)

### 2.1 Target Markets

| Country | Population | Labs (Est.) | Healthcare Spend | Entry Strategy |
|---------|-----------|-------------|-----------------|----------------|
| Saudi Arabia | 35M | 2,500+ | $52B | Partner-led (local SI) |
| UAE | 10M | 1,200+ | $22B | Direct + Partner |
| Jordan | 11M | 800+ | $3B | Partner-led |
| Egypt | 110M | 3,000+ | $12B | Partner-led (govt focus) |
| Kuwait | 4.5M | 400+ | $8B | Direct |

### 2.2 Regional Compliance Requirements

| Requirement | IQ | SA | UAE | JO | EG | KW |
|-------------|----|----|-----|----|----|----|
| Health Data Law | ✅ | NPHIES | NABIDH | HAK | UMR | KICS |
| Data Localization | Required | Required | Required | Required | Required | Required |
| PDPL (Data Privacy) | Draft | PDPL | N/A | N/A | N/A | N/A |
| GDPR Equivalent | No | No | No | No | No | No |
| Cloud Approval | N/A | NCA | TRA | N/A | N/A | N/A |
| FHIR Required | Partial | Yes | Yes | Yes | Yes | Yes |
| Health ID System | SNDHS | Sehhaty | Malaffi | HAK | Unified ID | KICS |
| Language | Arabic | Arabic | Arabic/EN | Arabic | Arabic | Arabic |
| Weekend | Fri-Sat | Fri-Sat | Fri-Sat | Fri-Sat | Fri-Thu | Fri-Sat |

### 2.3 Data Sovereignty: In-Country vs Regional Cloud

| Country | Recommended Deployment | Justification |
|---------|----------------------|---------------|
| Iraq | In-country (govt cloud) | SNDHS data sovereignty, no local hyperscaler |
| KSA | In-country (AWS me-south-1 or local) | NCA approval required, PDPL enforcement |
| UAE | In-country (AWS me-central-1 or local) | TRA approval, NABIDH mandate |
| Jordan | Regional (AWS) or in-country | HAK integration, limited local infra |
| Egypt | In-country (local provider) | UMR mandate, data sovereignty |
| Kuwait | Regional (Azure) or in-country | KICS integration |

**Regional Cloud Hub:** AWS Bahrain (me-south-1) serves KSA, Kuwait; AWS UAE (me-central-1) serves UAE, Jordan; AWS Egypt (forthcoming) for Egypt.

### 2.4 Arabic Language Variations by Country

| Country | Dialect | Key Differences |
|---------|---------|-----------------|
| Iraq | Iraqi Arabic | Distinct vocabulary, Mesopotamian dialect |
| KSA | Najdi/Hejazi | Formal Saudi terms, CBAHI terminology |
| UAE | Gulf Arabic | Emirati terms, Dubai Health Authority specific |
| Jordan | Levantine Arabic | Shared terms with Palestine, Syria |
| Egypt | Egyptian Arabic | Distinct idioms, most widely understood |

**Strategy:** Base Arabic is Modern Standard Arabic (MSA), with country-specific term overrides as language pack patches. Core platform UI stays MSA; country packs provide localized terminology.

### 2.5 Local Health System Integrations

| Country | Systems to Integrate | Adapter Required |
|---------|---------------------|------------------|
| Iraq | SNDHS, NHOP | ✅ Existing (SNDHS Pack) |
| KSA | NPHIES, Sehhaty, CBAHI, Wasfaty | ✅ New (KSA Country Pack) |
| UAE | NABIDH, Malaffi, Riayati, Sheryan | ✅ New (UAE Country Pack) |
| Jordan | HAK, National EHR | ✅ New (Jordan Country Pack) |
| Egypt | Unified Medical Record, NILE | ✅ New (Egypt Country Pack) |
| Kuwait | KICS, National Health ID | ✅ New (Kuwait Country Pack) |

---

## 3. International Expansion (2029–2031)

### 3.1 Target Markets

| Region | Target Countries | Timeline | Strategy |
|--------|-----------------|----------|----------|
| United Kingdom | England, Scotland, Wales, NI | 2029 | NHS Digital partner, GP Connect |
| European Union | Germany, France, Netherlands, Nordics | 2029–2030 | openEHR leader, GDPR compliance |
| Southeast Asia | Malaysia, Indonesia, Thailand | 2030 | Partner-led, emerging markets |
| Africa | Nigeria, Kenya, South Africa | 2030–2031 | Donor/WHO-funded, public health focus |

### 3.2 GDPR Compliance (Required for EU/UK)

| Requirement | Implementation |
|-------------|---------------|
| Data Processing Agreement (DPA) | Updated terms of service |
| Data Protection Officer (DPO) | Appointed for EU operations |
| Breach Notification | 72-hour notification to supervisory authority |
| Right to Erasure | Patient data deletion workflow |
| Data Portability | Patient data export (FHIR, CSV) |
| Privacy by Design | PII encryption, minimal data collection |
| Consent Management | Granular consent per purpose of use |
| Records of Processing | Automated data mapping |
| DPIAs | Impact assessments for each country pack |
| Representative in EU | Legal entity established in EU member state |

### 3.3 Multi-Language Support

| Language | Locale | Country Context | RTL | Status |
|----------|--------|-----------------|-----|--------|
| Arabic | ar-IQ | Iraq | Yes | **Complete** |
| Arabic | ar-SA | Saudi Arabia | Yes | Country Pack |
| Arabic | ar-AE | UAE | Yes | Country Pack |
| Arabic | ar-JO | Jordan | Yes | Country Pack |
| Arabic | ar-EG | Egypt | Yes | Country Pack |
| English | en-GB | UK | No | In Development |
| English | en-US | Global | No | In Development |
| Kurdish (Sorani) | ku | Iraq (KRG) | Yes | In Development |
| Kurdish (Kurmanji) | kmr | Regional | Yes | Planned |
| Turkish | tr | Turkey | No | Planned |
| Farsi | fa | Iran | Yes | Planned |
| French | fr | EU, Africa | No | Planned |
| German | de | Germany, EU | No | Planned |
| Dutch | nl | Netherlands | No | Planned |
| Malay | ms | Malaysia, Indonesia | No | Planned |

### 3.4 Interoperability by Region

| Region | Primary Standard | Secondary | Coding Systems |
|--------|-----------------|-----------|----------------|
| Iraq | SNDHS (proprietary) | FHIR R4 | LOINC, ICD-10-AM |
| KSA | NPHIES (FHIR R4) | HL7 v2 | LOINC, SNOMED CT, ICD-10 |
| UAE | NABIDH (FHIR R4) | openEHR | LOINC, SNOMED CT, ICD-10 |
| Jordan | HAK (FHIR R4) | HL7 v2 | LOINC, ICD-10 |
| Egypt | Unified Record (openEHR) | FHIR R4 | LOINC, SNOMED CT, ICD-10 |
| Kuwait | KICS (proprietary) | HL7 v2 | LOINC, ICD-10 |
| UK | NHS (FHIR R4, GP Connect) | HL7 v2, ITK | SNOMED CT, READ v2, ICD-10 |
| EU | openEHR | FHIR R4, IHE | SNOMED CT, LOINC, ICD-10, ICPC-2 |
| SE Asia | FHIR R4 | HL7 v2 | LOINC, ICD-10 |
| Africa | WHO SMART Guidelines | FHIR R4 | ICD-11, LOINC |

### 3.5 Cloud Provider Strategy

| Provider | Regions | Primary Use | Data Residency |
|----------|---------|-------------|----------------|
| AWS | me-south-1 (Bahrain), me-central-1 (UAE) | MENA (KSA, UAE, Kuwait, Jordan) | In-region |
| AWS | eu-west-2 (London) | UK | In-country |
| AWS | eu-central-1 (Frankfurt), eu-west-1 (Ireland) | EU | In-region |
| AWS | ap-southeast-1 (Singapore) | SE Asia | In-region |
| AWS | af-south-1 (Cape Town) | Africa | In-region |
| Azure | UAE North, Qatar Central | MENA (backup) | In-region |
| Azure | UK South, West Europe | UK, EU | In-region |
| GCP | me-central2 (Dammam) | KSA (upcoming) | In-country |
| DigitalOcean | AMS3, FRA1 | Current (Iraq), dev/staging | Not for prod data |

---

## 4. Deployment Models

### 4.1 Model Comparison

| Feature | SaaS Multi-Tenant | Single-Tenant Cloud | On-Premises | Hybrid | Air-Gapped | Government Cloud |
|---------|-------------------|---------------------|-------------|--------|------------|------------------|
| **Infrastructure** | Shared (platform-managed) | Dedicated (platform-managed) | Customer-managed | Split (cloud + edge) | Fully isolated | Government-managed |
| **Data Residency** | Platform-defined region | Customer-chosen region | Customer premises | Varies | Fully on-prem | Gov DC |
| **Isolation** | Logical (lab_id) | Full (separate instance) | Full | Logical + Physical | Physical | Physical |
| **Updates** | Continuous (zero-downtime) | Scheduled | Customer-managed | Scheduled + edge sync | Manual | Government-approved |
| **Internet Required** | Always | Always | Optional | Edge offline-capable | None | Restricted |
| **Compliance** | Platform certified | Customer audit | Customer-managed | Platform + customer | Customer-managed | Government audited |
| **SLA** | 99.9% | 99.95% | N/A | 99.5% (cloud) | N/A | Per contract |
| **Cost** | Lowest | Medium | Highest | Medium–High | High | Per contract |
| **Best For** | Small/medium labs | Enterprise, government | Sensitive, large hospitals | Remote sites, clinics | Military, intelligence | National systems |

### 4.2 Deployment Decision Matrix

```
                   ┌─────────────────────────────────────────────┐
                   │           Requirements                     │
                   ├────────────────────┬────────────────────────┤
                   │                    │                        │
         ┌─────────▼─────┐      ┌──────▼──────────┐             │
         │ Internet OK?  │      │ Data Sovereignty?│             │
         └───────┬───────┘      └──────┬───────────┘             │
                 │ No                  │ Yes                     │
         ┌───────▼───────┐     ┌───────▼───────────┐             │
         │  Air-Gapped    │     │   Government?     │             │
         └───────────────┘     └───────┬───────────┘             │
                                      │ Yes                     │
                              ┌───────▼───────────┐             │
                              │ Government Cloud   │             │
                              └───────┬───────────┘             │
                                      │ No                      │
                              ┌───────▼───────────┐             │
                              │ On-Premises         │            │
                              │ or Single-Tenant    │            │
                              └────────────────────┘             │
                                      │                          │
                          Need Edge? ──┤                          │
                                      │ Yes                     │
                              ┌───────▼───────────┐             │
                              │  Hybrid (cloud     │             │
                              │  + edge agent)     │             │
                              └───────┬───────────┘             │
                                      │ No                      │
                              ┌───────▼───────────┐             │
                              │  SaaS Multi-Tenant │             │
                              └───────────────────┘             │
```

### 4.3 SaaS Multi-Tenant (Default)

```
┌─────────────────── Global Load Balancer ─────────────────────┐
                            │
       ┌────────────────────┼────────────────────┐
       │                    │                    │
  ┌────▼────┐         ┌────▼────┐         ┌────▼────┐
  │ Region 1│         │ Region 2│         │ Region 3│
  │ (me-south-1)      │ (eu-west-2)        │ (ap-southeast-1)
  │         │         │         │         │         │
  │ ┌─────┐ │         │ ┌─────┐ │         │ ┌─────┐ │
  │ │API  │ │         │ │API  │ │         │ │API  │ │
  │ │GW   │ │         │ │GW   │ │         │ │GW   │ │
  │ └──┬──┘ │         │ └──┬──┘ │         │ └──┬──┘ │
  │    │    │         │    │    │         │    │    │
  │ ┌──▼──┐ │         │ ┌──▼──┐ │         │ ┌──▼──┐ │
  │ │App  │ │         │ │App  │ │         │ │App  │ │
  │ │Pool │ │         │ │Pool │ │         │ │Pool │ │
  │ └──┬──┘ │         │ └──┬──┘ │         │ └──┬──┘ │
  │    │    │         │    │    │         │    │    │
  │ ┌──▼──┐ │         │ ┌──▼──┐ │         │ ┌──▼──┐ │
  │ │ DB  │ │         │ │ DB  │ │         │ │ DB  │ │
  │ └─────┘ │         │ └─────┘ │         │ └─────┘ │
  └─────────┘         └─────────┘         └─────────┘
```

- **Tenant isolation:** Logical via `lab_id` (existing mechanism)
- **Data separation:** By region (no cross-region data movement)
- **Global components:** (in each region):
  - Load balancer (ALB/NLB)
  - API Gateway (Nginx/Envoy)
  - App pool (Auto-scaling group)
  - PostgreSQL (RDS/Aurora, multi-AZ)
  - Redis (ElastiCache, cluster mode)
  - Object storage (S3)

### 4.4 Single-Tenant Cloud (Dedicated)

```
┌─────────────────────────────────────────┐
│           Customer's VPC                 │
│                                          │
│  ┌───────────────────────────────────┐   │
│  │  gula-backend (ECS Fargate / K8s) │   │
│  ├───────────────────────────────────┤   │
│  │  PostgreSQL (RDS, single-AZ)      │   │
│  ├───────────────────────────────────┤   │
│  │  Redis (ElastiCache)              │   │
│  ├───────────────────────────────────┤   │
│  │  S3 bucket (isolated)             │   │
│  ├───────────────────────────────────┤   │
│  │  Cloudflare tunnel / Direct VPN   │   │
│  └───────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

- **Terraform module** deploys full stack in customer's account/VPC
- **CI/CD pipeline** per customer (GitHub Actions → ECR → ECS)
- **Monitoring:** Customer's CloudWatch + optional Grafana
- **Updates:** Rolling updates via blue-green deployment
- **Pricing:** Instance-based + management fee

### 4.5 On-Premises

```
┌──────────────────────────────────────────────┐
│           Customer Data Center                │
│                                               │
│  ┌─────────────────────────────────────────┐  │
│  │  Docker Compose / K3s / Rancher          │  │
│  │                                          │  │
│  │  gula-backend (3 replicas)               │  │
│  │  PostgreSQL 16 (Patroni HA)              │  │
│  │  Redis 7 (Sentinel HA)                   │  │
│  │  api-gateway (Nginx)                     │  │
│  │  device-bridge (USB/Serial pass-through) │  │
│  │  edge-agent (local cache)                │  │
│  └─────────────────────────────────────────┘  │
│                                               │
│  Backup: Local + encrypted to cloud storage   │
│  VPN: Site-to-site for remote support          │
└──────────────────────────────────────────────┘
```

- **Min hardware:** 4 vCPU, 16GB RAM, 200GB SSD (per node)
- **Recommended:** 3-node cluster for HA
- **Ship via:** Docker images on portable storage (if air-gapped)
- **Updates:** USB drive or VPN-based
- **Support:** 24/7 remote + local partner

### 4.6 Hybrid (Cloud + Edge)

```
┌────────────────────────────────┐
│         Cloud Region            │
│                                 │
│  Central Management             │
│  - Patient registry (MPI)       │
│  - Analytics & reporting        │
│  - National integration         │
│  - Backup & DR                  │
│  - Marketplace & updates        │
│                                 │
└─────────────┬──────────────────┘
              │ Internet / VPN
              │ (async, offline-tolerant)
    ┌─────────┼─────────┐
    │         │         │
┌───▼──┐ ┌───▼──┐ ┌───▼──┐
│Edge 1│ │Edge 2│ │Edge 3│
│      │ │      │ │      │
│Local │ │Local │ │Local │
│ DB   │ │ DB   │ │ DB   │
│Cache │ │Cache │ │Cache │
│Sync  │ │Sync  │ │Sync  │
└──────┘ └──────┘ └──────┘
```

**Edge Agent Location:** `edge_agent/` (top-level directory)
- Offline-capable local instance of GULA
- Patient registration, order entry, result entry
- Device bridge integration (local instruments)
- Async sync to cloud when connectivity available

### 4.7 Air-Gapped

```
┌─────────────────────────────────────┐
│        No External Connectivity      │
│                                      │
│  ┌───────────────────────────────┐   │
│  │  All GULA components in one   │   │
│  │  isolated network (no WAN)    │   │
│  │                               │   │
│  │  - No internet access         │   │
│  │  - No cloud sync              │   │
│  │  - Manual data transfer       │   │
│  │    via encrypted USB          │   │
│  │  - Local AI only (Ollama)     │   │
│  │  - On-prem AI Fabric          │   │
│  │  - Local only authentication  │   │
│  └───────────────────────────────┘   │
└─────────────────────────────────────┘
```

**Use Cases:**
- Military/government secure facilities
- Intelligence agencies
- Maximum security healthcare installations
- Disaster zones (temporary)

**Limitations:**
- No marketplace access
- Manual pack installation
- No real-time national reporting
- Limited AI capabilities (local models only)

### 4.8 Government Cloud (Iraqi National Data Center)

```
┌──────────────────────────────────────────────┐
│           Iraqi National Data Center           │
│                  (Government DC)               │
│                                                │
│  ┌──────────────────────────────────────────┐  │
│  │  Government-Owned Infrastructure          │  │
│  │                                           │  │
│  │  - Sovereign cloud (OpenStack/VMware)     │  │
│  │  - Physical isolation from other tenants  │  │
│  │  - Government-grade security controls     │  │
│  │  - Committee-approved deployment          │  │
│  │  - Limited egress (monitored)             │  │
│  │  - SNDHS data at rest + in transit        │  │
│  └──────────────────────────────────────────┘  │
└──────────────────────────────────────────────┘
```

**Data Residency:**
- All patient data remains inside Iraq
- SNDHS data: Government DC only
- Backup: Secondary government DC (geo-redundant in Iraq)

---

## 5. Regional Infrastructure

### 5.1 Region Mapping

| Region | Primary Cloud | Region Code | Deployment Models | Countries |
|--------|---------------|-------------|-------------------|-----------|
| Iraq (ME) | DigitalOcean (current), AWS (planned) | me-south-1 / iraq-gov | On-Prem, Gov Cloud, Hybrid | IQ |
| Gulf (MENA-1) | AWS | me-south-1 (Bahrain) | SaaS, Single-Tenant, Hybrid | SA, BH, QA |
| Gulf (MENA-2) | AWS | me-central-1 (UAE) | SaaS, Single-Tenant, Hybrid | AE, KW, OM |
| Levant (MENA-3) | AWS | me-south-1 | SaaS, On-Prem, Hybrid | JO, PS, LB |
| Egypt (MENA-4) | AWS / Azure | forthcoming | SaaS, On-Prem, Government | EG |
| UK (EU-1) | AWS | eu-west-2 (London) | SaaS, Single-Tenant, On-Prem | GB |
| EU (EU-2) | AWS | eu-central-1 (Frankfurt) | SaaS, Single-Tenant | DE, NL, FR, DK, SE |
| SE Asia (APAC) | AWS | ap-southeast-1 (Singapore) | SaaS, Hybrid | MY, ID, TH, PH |
| Africa (AFR) | AWS | af-south-1 (Cape Town) | SaaS, On-Prem, Hybrid | NG, KE, ZA |

### 5.2 Data Residency Requirements by Country

```yaml
Iraq:
  requirement: "Must store patient data within Iraqi borders"
  solution: "On-Premises or Government Cloud (National Data Center)"
  exceptions: "Backup can be encrypted and stored in regional cloud (me-south-1) with MoH approval"
  cloud_approved: "None (no hyperscaler in Iraq)"
  enforcement_body: "Ministry of Health, Communications and Media Commission"

Saudi Arabia:
  requirement: "Health data must remain in KSA (NCA regulation)"
  solution: "AWS me-south-1 (Bahrain) or Saudi-local cloud (upcoming me-central3)"
  exceptions: "De-identified data with NCA approval"
  cloud_approved: "AWS me-south-1, Oracle Jeddah, Microsoft Azure (Qatar pending)"
  enforcement_body: "National Cybersecurity Authority (NCA)"

UAE:
  requirement: "Health data in UAE or approved jurisdiction"
  solution: "AWS me-central-1 (UAE) or Azure UAE North"
  exceptions: "TRA-regulated data transfer agreements"
  cloud_approved: "AWS me-central-1, Azure UAE North, Oracle Dubai"
  enforcement_body: "Telecommunications Regulatory Authority (TRA)"

United Kingdom:
  requirement: "UK Health data in UK (NHS DSP Toolkit)"
  solution: "AWS eu-west-2 (London)"
  exceptions: "EU (adequate jurisdiction) with DPA"
  cloud_approved: "AWS eu-west-2, Azure UK South, GCP London"
  enforcement_body: "ICO, NHS Digital"

European Union:
  requirement: "GDPR — data in EU/EEA or adequacy decision"
  solution: "AWS eu-central-1 (Frankfurt) or eu-west-1 (Ireland)"
  exceptions: "Standard Contractual Clauses (SCCs)"
  cloud_approved: "All AWS/Azure/GCP EU regions"
  enforcement_body: "National DPAs, EDPB"
```

### 5.3 Latency Optimization

| Strategy | Implementation | Benefit |
|----------|---------------|---------|
| CDN | Cloudflare (static assets, API caching) | 50–100ms reduction |
| Edge Nodes | `edge_agent/` at lab sites | Near-zero (local) |
| Regional DB | RDS read replicas per region | <50ms read latency |
| Connection Pooling | PgBouncer per region | Reduced connection overhead |
| Cache Partitioning | Redis cluster per region | <5ms cache access |
| Global Routing | Route53 latency-based routing | Best-region selection |
| Image Optimization | WebP, responsive images | 60–80% size reduction |

**Target Latencies:**
- Local (on-prem): <5ms
- Same region: <20ms
- Cross-region (MENA): <100ms
- Cross-region (Intercontinental): <250ms

---

## 6. Localization Strategy

### 6.1 Language Pack Architecture

```
i18n/
├── ar.json                         # Modern Standard Arabic (default)
├── ar-IQ.json                      # Iraqi Arabic overrides
├── ar-SA.json                      # Saudi Arabic overrides
├── ku.json                         # Kurdish Sorani
├── tr.json                         # Turkish
├── fa.json                         # Farsi
├── fr.json                         # French
├── de.json                         # German
├── en-GB.json                      # British English
├── en-US.json                      # American English
└── base/                           # Shared translation keys
    ├── clinical.json               # Clinical terminology
    ├── errors.json                 # Error messages
    ├── dates.json                  # Date/time formats
    └── numbers.json                # Number formatting
```

**Key format:** Dot-notation with namespacing
```json
{
  "patient.create.title": "إنشاء مريض جديد",
  "patient.create.name_label": "اسم المريض",
  "patient.create.national_id": "الرقم الوطني",
  "errors.validation.required": "هذا الحقل مطلوب",
  "dates.format.long": "YYYY/MM/DD",
  "dates.format.short": "YY/MM/DD",
  "numbers.decimal_separator": ".",
  "numbers.grouping_separator": ","
}
```

### 6.2 Cultural Adaptation

| Domain | Iraqi | Saudi | Emirati | British |
|--------|-------|-------|---------|---------|
| Date Format | YYYY/MM/DD | DD/MM/YYYY | DD/MM/YYYY | DD/MM/YYYY |
| Week Start | Sunday | Sunday | Sunday | Monday |
| Weekend | Fri-Sat | Fri-Sat | Fri-Sat | Sat-Sun |
| Time Format | 24h | 12h (AM/PM) | 12h (AM/PM) | 12h (AM/PM) |
| Number Format | 1,234.56 | 1,234.56 | 1,234.56 | 1,234.56 |
| Currency | IQD | SAR | AED | GBP |
| Units | Metric | Metric | Metric | Mixed |
| Blood Type | A+ | A+ | A+ | A RhD Positive |
| Lab Units | Varies by test | LOINC | LOINC | UKAS |
| Name Order | Given + Family | Given + Family | Given + Family | Given + Family |
| Gender Segregation | In some clinics | Strict | None | None |
| Holiday Calendar | Iraqi | Saudi | UAE | UK |

### 6.3 Local Laboratory Standards Mapping

| Test | Iraqi Code | Saudi Code | UAE Code | UK Code |
|------|-----------|------------|----------|---------|
| CBC | CBC-001 | CBC-LAB-01 | CBC-01 | XaIRp |
| HbA1c | HBA1C-001 | HBA1C-LAB-01 | HBA1C-01 | XaL5c |
| TSH | TSH-001 | TSH-LAB-01 | TSH-01 | XaDib |
| Vitamin D | VITD-001 | VITD-LAB-01 | VITD-01 | XaepR |
| CRP | CRP-001 | CRP-LAB-01 | CRP-01 | XaElx |

**Implementation:** Country Pack provides a lookup table mapping local codes to LOINC.

---

## 7. Partner-Led Expansion

### 7.1 Partner Model by Market

| Market | Lead Partner | Model | Rationale |
|--------|-------------|-------|-----------|
| Saudi Arabia | Local SI (Tahaluf, Elm, or similar) | Reseller + Implementation | NCA compliance, government relationships |
| UAE | Local SI (e& enterprise, Injazat) | Reseller + Implementation | TRA compliance, Dubai Health connections |
| Jordan | Regional SI | Implementation Partner | HAK integration expertise |
| Egypt | Government partner (MoH, NTRA) | Government + Implementation | UMR mandate, large-scale deployment |
| Kuwait | Local SI | Reseller + Implementation | KICS integration |
| UK | NHS-approved supplier | Implementation + Reseller | NHS Digital onboarding, DSP Toolkit |
| EU | openEHR specialist | Technology + Implementation | openEHR integration expertise |

### 7.2 Partner Recruitment Criteria

| Criteria | Weight | Assessment |
|----------|--------|------------|
| Healthcare expertise | 30% | Number of healthcare projects, certifications |
| Technical capability | 25% | Development team, architecture skills, cloud expertise |
| Market presence | 20% | Government relationships, lab/hospital connections |
| Financial stability | 15% | Revenue, profitability, credit rating |
| Cultural fit | 10% | Shared values, customer-first approach |

---

## 8. Regulatory Timeline

### 8.1 Market Entry Timeline

| Market | Regulatory Start | Expected Approval | Market Entry | Key Regulatory Body |
|--------|-----------------|-------------------|--------------|---------------------|
| Iraq | ✅ Complete | ✅ Complete | ✅ Live | MoH Iraq, CMC |
| KSA | Q1 2027 | Q3 2027 | Q4 2027 | NCA, SFDA, CBAHI |
| UAE | Q2 2027 | Q4 2027 | Q1 2028 | TRA, DOH, DHA |
| Jordan | Q3 2027 | Q1 2028 | Q2 2028 | MoH, HAK |
| Egypt | Q1 2028 | Q3 2028 | Q4 2028 | MoH, NTRA |
| Kuwait | Q2 2028 | Q4 2028 | Q1 2029 | MoH, CITRA |
| UK | Q1 2029 | Q3 2029 | Q4 2029 | NHS Digital, ICO, CQC |
| EU (DE) | Q2 2029 | Q4 2029 | Q1 2030 | BfDI, CMEK, gematik |
| SE Asia | Q2 2030 | Q4 2030 | Q1 2031 | MOH (per country) |

### 8.2 Regulatory Activities per Market

```yaml
Phase 1 — Discovery (3 months):
  - Legal review: Data protection, health regulations
  - Compliance gap analysis
  - Local partner identification
  - Regulatory body engagement

Phase 2 — Preparation (3 months):
  - Compliance implementation
  - Localization (language, standards)
  - Data residency setup
  - Partner onboarding and training

Phase 3 — Certification (3 months):
  - Security audit (local standards)
  - Integration certification (local health systems)
  - Data protection certification
  - Submission to regulatory body

Phase 4 — Launch (1 month):
  - Soft launch (pilot labs)
  - Hard launch (full GA)
  - Marketing and sales activation
  - Support and escalation setup
```

---

## 9. Cost Model

### 9.1 Infrastructure Cost by Deployment Model

| Model | Monthly Cost (Est.) | Includes | Scaling |
|-------|-------------------|----------|---------|
| SaaS (per lab) | $50–$200 | Shared infra, per-lab overhead | Linear |
| Single-Tenant Cloud | $500–$2,000 | Dedicated instance, DB, cache | Vertical |
| On-Premises + Support | $1,000–$5,000 | Support, updates, remote | Per cluster |
| Hybrid (cloud + edge) | $200–$1,000 | Cloud + edge agent licensing | Per edge |
| Air-Gapped | $500–$3,000 | Support (via courier), updates | Per instance |
| Government Cloud | N/A (per contract) | Custom | Per agreement |

### 9.2 Infrastructure Cost Breakdown (SaaS, per region)

| Component | AWS me-south-1 | AWS eu-west-2 | Azure UAE North |
|-----------|---------------|---------------|-----------------|
| ECS/App (3 x medium) | $300 | $450 | $350 |
| RDS PostgreSQL (db.r6g.large) | $350 | $500 | $380 |
| ElastiCache Redis (cache.r6g.large) | $200 | $300 | $220 |
| ALB | $30 | $40 | $35 |
| S3 / EBS | $50 | $60 | $50 |
| Data Transfer | $100 | $150 | $120 |
| Monitoring (CloudWatch) | $50 | $70 | $55 |
| **Total per region** | **$1,080** | **$1,570** | **$1,210** |

### 9.3 Revenue per Lab by Deployment Model

| Model | Revenue/Lab/Month | Margin (Est.) |
|-------|-------------------|---------------|
| SaaS (Iraq/FY) | $50–$200 | 60–70% |
| SaaS (MENA) | $100–$500 | 50–60% |
| SaaS (UK/EU) | $200–$1,000 | 40–50% |
| Single-Tenant | $500–$2,000 | 30–40% |
| On-Prem (support) | $200–$500 | 70–80% |

---

## 10. Support Model

### 10.1 Follow-the-Sun Support

```
Americas                EMEA                    APAC
(08:00–18:00 EST)       (08:00–18:00 CET)       (08:00–18:00 SGT)
     │                        │                        │
     └─────────── Global Triage ────────────┘
                         │
                    L2/L3 Engineers
                    (EMEA + Regional)
```

| Time Zone | Coverage | Team Location |
|-----------|----------|---------------|
| UTC-5 to UTC-5 | Americas business hours | Remote (optional) |
| UTC+1 to UTC+3 | EMEA business hours | Iraq, Jordan, Egypt |
| UTC+3 to UTC+4 | Gulf business hours | Riyadh, Dubai |
| UTC+8 to UTC+8 | APAC business hours | Singapore (future) |

### 10.2 Support Tiers

| Tier | Channel | Response (P1) | Response (P2) | Response (P3) | Availability |
|------|---------|---------------|---------------|---------------|--------------|
| Free | Community | No SLA | No SLA | No SLA | Business hours |
| Standard | Ticket | 4 hours | 8 hours | 24 hours | Business hours |
| Premium | Ticket + Chat | 1 hour | 4 hours | 8 hours | 24/7 |
| Enterprise | Ticket + Chat + Phone | 15 min | 1 hour | 4 hours | 24/7 dedicated |

### 10.3 Severity Levels

| Severity | Definition | Example | Target Fix Time |
|----------|-----------|---------|-----------------|
| P1 (Critical) | System down, data loss, security breach | DB crash, patient data inaccessible | 4 hours |
| P2 (High) | Major feature broken, performance degraded | Results not loading, slow queries | 8 hours |
| P3 (Medium) | Minor feature broken, cosmetic issue | Wrong label text, export format issue | 2 business days |
| P4 (Low) | Enhancement request, documentation | Feature request, FAQ update | Next release |

---

## Appendix A: Country Pack Boilerplate

New country packs must include:

```
pack_<country>/
├── pack.json                    # Country pack manifest
├── __init__.py                  # Plugin entry point
├── adapters/                    # Local health system adapters
│   ├── __init__.py
│   └── <local_system>_adapter.py
├── compliance/                  # Local compliance requirements
│   ├── __init__.py
│   └── data_protection.py
├── routes/                      # Country-specific routes
│   └── __init__.py
├── models/                      # Country-specific models
│   └── __init__.py
├── i18n/                        # Language overrides
│   ├── ar-<LOCALE>.json
│   └── en.json
├── mappings/                    # Code mappings
│   ├── test_codes.csv
│   └── lab_standards.json
├── tests/
└── docs/
    ├── REGULATORY_COMPLIANCE.md
    ├── DEPLOYMENT_GUIDE.md
    └── INTEGRATION.md
```

## Appendix B: Global KPI Targets

| Metric | Current (Iraq) | 2027 (MENA) | 2029 (EU/UK) | 2031 (Global) |
|--------|---------------|-------------|--------------|---------------|
| Active labs | 50–200 | 1,000+ | 3,000+ | 10,000+ |
| Countries | 1 | 6 | 12 | 20+ |
| Languages | 2 | 5 | 8 | 12+ |
| Packs on Marketplace | 0 | 25+ | 100+ | 500+ |
| Partners | 0 | 10+ | 50+ | 200+ |
| Revenue (ARR) | $260K | $2M+ | $10M+ | $50M+ |
| Uptime SLA | 99.5% | 99.9% | 99.95% | 99.95% |
| Data Centers | 1 | 4 | 7 | 12+ |
| Deployment Engineers | 3 | 15 | 40 | 100+ |

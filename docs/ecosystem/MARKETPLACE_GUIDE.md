# GULA Marketplace Guide

**Version:** 2.1.0  
**Status:** DRAFT  
**Last Updated:** 2026-07-17

---

## 1. Marketplace Architecture

### 1.1 System Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                        End Users (Browser)                          │
└──────────────────────────┬─────────────────────────────────────────┘
                           │ HTTPS
┌──────────────────────────▼─────────────────────────────────────────┐
│                      gula-marketplace (Microservice)                 │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  Catalog API  │  │   Storefront  │  │  Developer    │             │
│  │  (public)     │  │  (React SPA)  │  │  Dashboard    │             │
│  └──────┬───────┘  └──────┬───────┘  │  (React SPA)  │             │
│         │                 │          └──────┬───────┘              │
│  ┌──────▼─────────────────▼───────────────▼───────┐                │
│  │               Marketplace Core                    │               │
│  │  ┌─────────┐ ┌────────┐ ┌────────┐ ┌──────────┐ │               │
│  │  │ Listing │ │Pricing │ │Payment │ │Licensing  │ │               │
│  │  │ Service │ │Service │ │Service │ │Service    │ │               │
│  │  └─────────┘ └────────┘ └────────┘ └──────────┘ │               │
│  │  ┌─────────┐ ┌────────┐ ┌────────┐ ┌──────────┐ │               │
│  │  │Download │ │ Rating │ │Subscrip│ │ Security  │ │               │
│  │  │ Service │ │Service │ │Service │ │ Scanner   │ │               │
│  │  └─────────┘ └────────┘ └────────┘ └──────────┘ │               │
│  └──────────────────────┬───────────────────────────┘               │
└─────────────────────────┼───────────────────────────────────────────┘
                          │ Internal gRPC / Redis
┌─────────────────────────▼───────────────────────────────────────────┐
│                        gula-backend (Kernel)                         │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  PluginMarketplaceInterface  │  PluginManager  │  Sandbox    │   │
│  └──────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
```

### 1.2 Component Details

| Component | Technology | Description |
|-----------|-----------|-------------|
| Storefront | React SPA | Customer-facing marketplace at `marketplace.gula.health` |
| Developer Dashboard | React SPA | Developer portal at `dev.gula.health` |
| Catalog API | FastAPI | Public API for browsing, searching, downloading packs |
| Listing Service | FastAPI | CRUD for pack listings, versions, metadata |
| Pricing Service | FastAPI | Pricing tiers, regional pricing, discounts |
| Payment Service | FastAPI + Stripe/Zain Cash | Payment processing |
| Licensing Service | FastAPI | License key generation, DRM, activation |
| Subscription Service | FastAPI | Billing cycles, renewals, upgrades/downgrades |
| Download Service | FastAPI + CDN | Signed URL-based secure download |
| Rating Service | FastAPI | Reviews, ratings, verified purchase tracking |
| Security Scanner | Python (sandboxed) | Automated malware/vulnerability scanning |
| Analytics Service | FastAPI + ClickHouse | Sales, usage, developer analytics |

### 1.3 Integration with Kernel

The marketplace connects to `gula-backend` via two mechanisms:

1. **PluginMarketplaceInterface** (`backend/app/kernel/plugin/marketplace.py`):
   - Used by the kernel to discover available plugins
   - Provides search, list, and download interfaces
   - Caches marketplace catalog locally for offline support

2. **Direct REST API**:
   - The `gula-marketplace` service calls backend APIs for license validation
   - Backend calls marketplace for pack download and version checking

---

## 2. Product Types

### 2.1 Product Categories

| Product Type | Description | Packaging | Delivery |
|-------------|-------------|-----------|----------|
| **Pack** | Complete domain module (full functionality) | `.gpk` archive | Download + install |
| **Plugin** | Runtime-loaded extension | `.gpk` (plugin type) | Hot-reload |
| **Extension** | Lightweight add-on (API, UI, data) | `.gpk` (extension type) | Install + restart |
| **Connector** | Protocol adapter for external systems | `.gpk` (connector type) | Configure + activate |
| **AI Skill** | AI model or agent | `.gai` archive | AI Fabric registration |
| **Template** | Report, form, or layout template | `.gtpl` archive | Import to template library |
| **Theme** | Visual theme / branding | `.gtheme` archive | Apply to instance |
| **Language Pack** | Translation file set | `.glang` archive | Add locale to instance |

### 2.2 Pack Product Types (Detailed)

| Pack Type | Contents | Example |
|-----------|----------|---------|
| Healthcare Pack | Full domain: routes, models, services, migrations, UI | Radiology Pack |
| Government Pack | National integration: adapters, compliance, reporting | SNDHS Pack |
| Education Pack | Learning content: courses, assessments, CME | Training Pack |
| Research Pack | Analytics: cohorts, data export, de-identification | Population Health Pack |
| Industry Pack | Vertical: pharma, insurance, devices | Insurance Billing Pack |
| Country Pack | Regional: localization, regulatory, integrations | Saudi Arabia Pack |

### 2.3 Product Statuses

```
Draft → Under Review → Published → Deprecated → Archived
                         ↓
                     Update Available
```

| Status | Description |
|--------|-------------|
| Draft | Developer is working on listing, not visible |
| Under Review | Submitted for certification |
| Published | Visible and purchasable in marketplace |
| Deprecated | Marked for removal, still available |
| Archived | No longer available for download |
| Update Available | New version exists, current customers can upgrade |

---

## 3. Listing Requirements

### 3.1 Required Fields

| Field | Required | Format | Example |
|-------|----------|--------|---------|
| Product Name | Yes | String (max 100 chars) | "Radiology Pack" |
| Display Name (AR) | Yes | Arabic string | "حزمة الأشعة" |
| Display Name (EN) | Yes | English string | "Radiology Pack" |
| Description (AR) | Yes | Markdown (max 5000 chars) | Arabic description |
| Description (EN) | Yes | Markdown (max 5000 chars) | English description |
| Category | Yes | Enum | "clinical", "integration" |
| Subcategory | Yes | Enum | "radiology", "ehr" |
| Version | Yes | SemVer | "1.0.0" |
| Min Kernel Version | Yes | SemVer | "2.1.0" |
| Max Kernel Version | No | SemVer | "3.0.0" |
| Author | Yes | Object | `{name, email, website}` |
| License | Yes | Enum | "MIT", "GPL-3.0", "Commercial" |
| Icon | Yes | Image (PNG, 256x256) | `icon.png` |
| Screenshots | Recommended | Image (1920x1080) | `screenshot_1.png` |
| Tags | Recommended | Array of strings | `["radiology", "dicom"]` |
| Dependencies | Yes | Object | `{pack_name: ">=1.0.0"}` |
| Permissions | Yes | Array of strings | `["read:patients"]` |
| Pricing | Yes | Object | `{model: "subscription", price: 99}` |
| Changelog | Yes | Markdown | Version history |
| Docs URL | Recommended | URL | `https://docs.gula.health/pack/radiology` |
| Support URL | Recommended | URL | `https://support.gula.health/radiology` |
| Source URL | For open source | URL | `https://github.com/partner/radiology-pack` |

### 3.2 Quality Requirements

| Requirement | Community | Verified | Certified | Enterprise |
|-------------|-----------|----------|-----------|------------|
| Security scan | ✅ | ✅ | ✅ | ✅ |
| Tests pass | ✅ | ✅ | ✅ | ✅ |
| API documentation | ✅ | ✅ | ✅ | ✅ |
| Arabic translations | ✅ | ✅ | ✅ | ✅ |
| English translations | Recommended | ✅ | ✅ | ✅ |
| Deployment guide | ✅ | ✅ | ✅ | ✅ |
| Migration idempotent | N/A | ✅ | ✅ | ✅ |
| Tenant isolation audit | ✅ | ✅ | ✅ | ✅ |
| Audit coverage | ✅ | ✅ | ✅ | ✅ |
| Performance benchmark | N/A | N/A | ✅ | ✅ |
| Clinical safety review | N/A | N/A | ✅ | ✅ |
| Code review | N/A | N/A | ✅ | ✅ |
| SLA for support | N/A | N/A | Optional | ✅ |
| Security review | N/A | Basic | Full | Full |

### 3.3 Listing Submission

```
1. Developer uploads .gpk via Developer Dashboard
2. System extracts metadata from pack.json
3. Developer fills in listing details (descriptions, screenshots, pricing)
4. Submit for review
5. Automated checks run:
   - Unpack and validate pack.json
   - Security scan (malware, CVEs, secrets)
   - Compatibility check against kernel API
   - Test suite execution
   - Migration round-trip test
   - Tenant isolation verification
6. Manual review (for Certified+)
7. Approval / Rejection with reason
8. Listing published
```

**Review SLAs:**

| Certification | Automated Review | Manual Review | Total |
|---------------|-----------------|---------------|-------|
| Community | <1 hour | N/A | <1 hour |
| Verified | <1 hour | N/A | <1 hour |
| Certified | <1 hour | <3 business days | <4 business days |
| Enterprise | <1 hour | <5 business days | <6 business days |

---

## 4. Pricing Models

### 4.1 Available Pricing Models

| Model | Description | Commission | Best For |
|-------|-------------|-----------|----------|
| **Free** | No cost, open source | 0% | Community packs, connectors |
| **One-Time** | Single purchase, perpetual license | 20% | Connectors, themes |
| **Subscription** | Monthly or annual recurring | 15% | Full packs, SaaS features |
| **Usage-Based** | Per-order, per-test, per-patient | 10% | AI skills, analytics |
| **Freemium** | Free tier + paid upgrade | 20% (on paid) | Packs with limited free version |
| **Enterprise** | Custom pricing, volume license | Negotiable | Country packs, government |

### 4.2 Pricing Tiers Examples

| Model | Price Range (USD) | Typical |
|-------|-------------------|---------|
| Free | $0 | Community connectors |
| One-Time | $50–$5,000 | Device connectors, report templates |
| Subscription (monthly) | $10–$500/mo | Full packs (per instance) |
| Subscription (annual) | $100–$5,000/yr | Full packs (per instance) |
| Usage-Based | $0.01–$1.00/unit | AI inference, per-result processing |
| Freemium Free Tier | $0 | Limited features, capped usage |
| Freemium Paid Tier | $50–$500/mo | Full features, unlimited usage |
| Enterprise | Custom | Country packs, government compliance |

### 4.3 Regional Pricing

Pricing can differ by region to reflect local market conditions:

```json
{
  "default_price": 99,
  "currency": "USD",
  "regional_pricing": {
    "IQ": {"price": 150000, "currency": "IQD"},
    "SA": {"price": 399, "currency": "SAR"},
    "AE": {"price": 399, "currency": "AED"},
    "JO": {"price": 70, "currency": "JOD"},
    "EG": {"price": 1500, "currency": "EGP"},
    "GB": {"price": 79, "currency": "GBP"},
    "EU": {"price": 89, "currency": "EUR"},
    "TR": {"price": 2500, "currency": "TRY"}
  }
}
```

### 4.4 Discount Engine

| Discount Type | Description | Max Discount |
|---------------|-------------|-------------|
| Launch Promotion | New packs, limited time | 50% |
| Volume Discount | Bulk licenses | Tiered (10–40%) |
| Bundle Discount | Multi-pack purchase | 20% |
| Tier Discount | Gold+ partner packs | 10–20% |
| Non-Profit | Educational, NGO | 50% |
| Government | Public sector | 30% |

---

## 5. Payment Processing

### 5.1 Supported Payment Gateways

| Gateway | Region | Fees | Payout Currency |
|---------|--------|------|-----------------|
| Stripe | Global | 2.9% + $0.30 | USD, local |
| Zain Cash | Iraq | 2% | IQD |
| Asia Hawala | Iraq | 1% | IQD |
| FastPay | Iraq | 2.5% | IQD |
| Moyasar | KSA | 2.9% + SAR 1 | SAR |
| Tabby | KSA/UAE | BNPL | SAR/AED |
| PayPal | Global | 3.9% + $0.49 | USD |
| PayTabs | MENA | 2.75% | Local |
| Bank Transfer | Enterprise | Negotiable | Any |

### 5.2 Payment Flow

```
1. Customer clicks "Purchase" on marketplace
2. Marketplace generates order with line items
3. Customer selects payment method
4. Payment gateway processes transaction
5. On success:
   a. License key generated (for paid packs)
   b. Download URL generated (signed, time-limited)
   c. Order confirmation sent
   d. Developer payout calculation triggered
6. On failure:
   a. Error returned to customer
   b. Retry options offered
   c. Support ticket created for repeated failure
```

### 5.3 Payout Schedule

| Payout Trigger | Frequency | Terms |
|---------------|-----------|-------|
| Marketplace Sale | Monthly | Net-45 from month-end |
| Subscription Revenue | Monthly | Net-45 from subscription month |
| Usage Revenue | Monthly | Net-60 from usage month |
| Enterprise Deal | Per milestone | As negotiated |

---

## 6. Subscription Management

### 6.1 Subscription Lifecycle

```
Active → Renewing (auto-renew) → Renewed
  ↓         ↓ (cancel)
Expiring → Expired → Grace Period → Suspended → Terminated
```

| State | Description | License Status |
|-------|-------------|----------------|
| Active | Subscription current | Valid |
| Renewing | Auto-renewal processing | Valid |
| Expiring | Near end date (7 days) | Valid |
| Expired | Past end date | Valid (grace) |
| Grace Period | 30 days past expiration | Valid (warnings) |
| Suspended | 30+ days past expiration | Invalid (degraded) |
| Terminated | 90+ days past expiration / cancelled | Invalid (removed) |

### 6.2 Upgrade/Downgrade Flows

**Upgrade** (e.g., Basic → Pro):
- Immediate activation of upgraded features
- Prorated charge for remainder of billing period
- No data loss or migration needed

**Downgrade** (e.g., Pro → Basic):
- Effective at end of current billing period
- Advanced features disabled at downgrade
- Data retained (not deleted) for 90 days
- Re-upgrade possible within that window

### 6.3 Billing Periods

| Period | Discount | Refund Policy |
|--------|----------|---------------|
| Monthly | None | 7-day prorated |
| Annual | 15% off | 14-day full refund |
| Biannual | 10% off | 14-day prorated |
| Quarterly | 5% off | 7-day prorated |

---

## 7. Rating & Review System

### 7.1 Review Mechanics

- **Verified purchases only** — reviews must come from paying customers
- **Rating scale:** 1–5 stars (1=Poor, 5=Excellent)
- **Review fields:** Rating + Title + Body (minimum 50 chars)
- **Media:** Up to 3 screenshots per review
- **Developer response:** Published within 14 days
- **Helpful votes:** Customers can vote "Helpful" on reviews

### 7.2 Rating Calculation

```
Overall Rating = Weighted average of:
  - Last 12 months: 60% weight
  - Older reviews: 40% weight (decaying)
  - Enterprise reviews: double weight
  - Developer response resolves negative review? Weight reduced
```

### 7.3 Moderation

- Automated moderation (profanity, spam, off-topic)
- Manual review for flagged reviews
- Developer can flag reviews for moderation
- Removed reviews: policy violation
- Verified badge: confirmed purchase
- Helpful ranking shift: highly voted reviews appear first

---

## 8. Search & Discovery

### 8.1 Catalog Browsing

| Browse Dimension | Values |
|-----------------|--------|
| Category | Clinical, Integration, Government, AI, Infrastructure, Developer Tools |
| Subcategory | LIMS, EHR, Radiology, Pharmacy, Nursing, Blood Bank, etc. |
| Type | Pack, Plugin, Connector, AI Skill, Template, Theme, Language Pack |
| Pricing | Free, Paid, Subscription, Usage-Based |
| Certification | Community, Verified, Certified, Enterprise |
| Partner Tier | Registered, Silver, Gold, Platinum |
| Language | Arabic, English, Kurdish, Turkish, Farsi |
| Country | Iraq, KSA, UAE, Jordan, Egypt, Kuwait, UK, EU |

### 8.2 Search Features

- Full-text search across name, description, tags
- Faceted filtering (category, price, certification, language)
- Sort by: relevance, rating, downloads, newest, price
- Autocomplete suggestions
- Typo-tolerant search
- Arabic keyword search (morphological analysis)

### 8.3 Recommendation Engine

- **Collaborative filtering:** "Customers who bought X also bought Y"
- **Usage-based:** "Most popular packs for your lab type"
- **Complementary:** "Complete your setup with these packs"
- **Trending:** "What's popular this month"
- **Personalized:** Based on current pack installs and lab profile

### 8.4 Featured & Promoted Listings

- **Featured:** Platform-curated picks on homepage (rotation)
- **Promoted:** Paid placement in search results (sponsored)
- **New Releases:** Recently published packs
- **Editor's Choice:** Picked by platform team

---

## 9. Developer Dashboard

### 9.1 Dashboard Sections

| Section | Features |
|---------|----------|
| **Overview** | Revenue summary, active listings, total downloads, customer count |
| **Listings** | Manage packs (create, edit, version, publish, deprecate) |
| **Sales Analytics** | Revenue by product, region, time period; conversion rates |
| **Customer Management** | Active customers, subscription status, support tickets |
| **Version Management** | Version history, release notes, upgrade paths |
| **Payouts** | Payment history, pending payments, tax documents |
| **Reviews** | Customer reviews, respond, moderation requests |
| **Analytics** | Downloads, installs, active usage, feature usage |
| **Settings** | Profile, payment info, tax info, notification prefs |
| **Support** | Ticket queue, knowledge base, community forum |

### 9.2 Sales Analytics API

```json
GET /api/v1/developer/sales?period=last_30_days
{
  "summary": {
    "revenue": 15000.00,
    "currency": "USD",
    "orders": 45,
    "new_customers": 12,
    "renewals": 33,
    "refunds": 2
  },
  "by_product": [
    {"product": "Radiology Pack", "revenue": 8000, "orders": 20},
    {"product": "Device Bridge Connector", "revenue": 5000, "orders": 15}
  ],
  "by_region": [
    {"region": "Iraq", "revenue": 10000, "orders": 30},
    {"region": "KSA", "revenue": 3000, "orders": 8},
    {"region": "UAE", "revenue": 2000, "orders": 7}
  ],
  "trend": {
    "daily_revenue": [...],
    "daily_orders": [...]
  }
}
```

### 9.3 Version Management

```json
POST /api/v1/developer/packs/{id}/versions
{
  "version": "1.1.0",
  "changelog": {
    "ar": "إصلاح مشكلة في عرض التقارير",
    "en": "Fixed report rendering issue"
  },
  "pack_file": "radiology-pack-1.1.0.gpk",
  "min_kernel_version": "2.1.0",
  "compatibility_notes": "Requires migration: alembic upgrade head",
  "release_date": "2026-07-17"
}
```

---

## 10. Enterprise Procurement

### 10.1 Volume Licensing

| Volume Tier | License Count | Discount | Support |
|-------------|--------------|----------|---------|
| Small | 2–10 instances | 10% | Standard |
| Medium | 11–50 instances | 20% | Priority |
| Large | 51–200 instances | 30% | Premium |
| Enterprise | 201+ instances | Custom | Dedicated |

### 10.2 Quote & Purchase Order Flow

1. Customer requests quote from marketplace
2. Developer receives notification with requirements
3. Quote generated (custom pricing, terms, SLA)
4. Customer reviews and accepts
5. Purchase order (PO) issued by customer
6. PO approved, payment terms defined
7. License keys generated in batch
8. Customer downloads and activates
9. Annual renewal with volume reconciliation

### 10.3 Enterprise Terms

| Term | Standard | Enterprise |
|------|----------|------------|
| Payment Terms | Prepaid | Net-30 to Net-90 |
| Contract Term | 1 year | 1–3 years |
| SLA | Standard (99.9%) | Premium (99.95%) |
| Support | Business hours | 24/7 dedicated |
| Audit Rights | Standard | Enhanced |
| Data Processing | Standard terms | Custom DPA |
| Termination | 30 days | 90 days |
| Renewal | Auto-renew | Mutual agreement |

---

## 11. Tax & Compliance

### 11.1 Tax Handling by Region

| Country | Tax Type | Rate | Marketplace Responsible |
|---------|----------|------|------------------------|
| Iraq | Sales Tax | 0% (healthcare exemption) | N/A |
| Iraq (KRG) | Sales Tax | 0% (healthcare exemption) | N/A |
| Saudi Arabia | VAT | 15% | Platform (reverse charge) |
| UAE | VAT | 5% | Platform (reverse charge) |
| Jordan | Sales Tax | 16% (healthcare exemption) | Platform |
| Egypt | VAT | 14% | Platform |
| Kuwait | VAT | 0% (healthcare exemption) | N/A |
| UK | VAT | 20% (healthcare exemption) | Platform |
| EU | VAT-VIES | Varies | Platform (MOSS/IOSS) |
| US | Sales Tax | Varies by state | Platform (marketplace facilitator) |

### 11.2 Developer Tax Obligations

- Developers are responsible for their own income tax
- Marketplace provides annual earnings summary
- Withholding tax managed per jurisdiction
- W-8BEN/W-9 collection for US tax compliance
- VAT registration required for EU-based developers

---

## 12. Refund Policy

### 12.1 Standard Refund Terms

| Purchase Type | Refund Window | Fee |
|---------------|--------------|-----|
| One-Time Purchase | 14 days | Full refund minus payment fees |
| Monthly Subscription | 7 days | Full prorated refund |
| Annual Subscription | 14 days | Prorated refund (minus discount) |
| Usage-Based | N/A (pay-as-you-go) | No refund |
| Enterprise Deal | Per contract | Per contract |
| Bundle | 14 days | Full bundle refund |

### 12.2 Refund Process

1. Customer initiates refund via marketplace
2. Automated check: eligibility, fraud detection
3. If eligible: automatic approval and refund
4. If flagged: manual review within 48 hours
5. Refund processed to original payment method
6. License deactivated within 24 hours
7. Developer notified of refund
8. Revenue reversed from developer payout

### 12.3 Developer Revenue Impact

- Refunds deducted from developer revenue
- Refund rate >5% triggers quality review
- Repeated refund abuse → delisting
- Fraud refunds → full developer chargeback

---

## 13. Security Scanning

### 13.1 Automated Scan Pipeline

```
Upload → Extract (.gpk) → Parse pack.json → Dependency Scan → SAST → Secret Scan → Malware Scan → Report → Pass/Fail
```

| Scan Type | Tool | Checks |
|-----------|------|--------|
| Dependency Scan | Safety + pip-audit | Known CVEs in Python dependencies |
| SAST | Bandit | Python security issues (injection, XSS, crypto) |
| Secret Scan | Gitleaks | Hardcoded secrets, API keys, passwords |
| Malware Scan | ClamAV | Malware signatures in package files |
| Container Scan | Trivy | Container image vulnerabilities |
| License Scan | Scancode | License compliance check |
| Behavioral Analysis | Custom sandbox | Runtime behavior monitoring |

### 13.2 Security Requirements by Certification Level

| Requirement | Community | Verified | Certified | Enterprise |
|-------------|-----------|----------|-----------|------------|
| No critical CVEs | ✅ | ✅ | ✅ | ✅ |
| No high CVEs | ✅ | ✅ | ✅ | ✅ |
| No hardcoded secrets | ✅ | ✅ | ✅ | ✅ |
| No malware | ✅ | ✅ | ✅ | ✅ |
| License compliance | ✅ | ✅ | ✅ | ✅ |
| No medium CVEs | ❌ | ✅ | ✅ | ✅ |
| SAST pass | ❌ | ✅ | ✅ | ✅ |
| Dependency fresh (<1yr) | ❌ | ✅ | ✅ | ✅ |
| Penetration test | ❌ | ❌ | ✅ | ✅ |
| SOC 2 evidence | ❌ | ❌ | ❌ | ✅ |

### 13.3 Vulnerability Disclosure

- Security issues found post-release → developer notified via security advisory
- Critical: 7 days to fix before public disclosure
- High: 30 days to fix
- Medium: 90 days to fix
- Fix verification scan required
- CVE assignment for qualifying vulnerabilities
- Security advisory published on marketplace listing

---

## Appendix A: Marketplace API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/catalog/search` | GET | Search marketplace |
| `/api/v1/catalog/products/{id}` | GET | Product details |
| `/api/v1/catalog/categories` | GET | List categories |
| `/api/v1/purchase/order` | POST | Create purchase order |
| `/api/v1/purchase/license` | GET | Get license key |
| `/api/v1/purchase/download/{pack_id}` | GET | Download pack |
| `/api/v1/subscription/create` | POST | Create subscription |
| `/api/v1/subscription/cancel` | POST | Cancel subscription |
| `/api/v1/subscription/upgrade` | POST | Upgrade plan |
| `/api/v1/reviews/{product_id}` | GET/POST | Get/add reviews |
| `/api/v1/developer/products` | GET | Developer's products |
| `/api/v1/developer/products/{id}` | PUT | Update product |
| `/api/v1/developer/products/{id}/versions` | POST | New version |
| `/api/v1/developer/analytics/sales` | GET | Sales analytics |
| `/api/v1/developer/analytics/usage` | GET | Usage analytics |
| `/api/v1/developer/payouts` | GET | Payout history |
| `/api/v1/admin/scan/{version_id}` | POST | Trigger security scan |
| `/api/v1/admin/certify/{version_id}` | POST | Certify version |

## Appendix B: Pack Manifest Schema

See `pack.json` specification in the Extension Guide (docs/ecosystem/EXTENSION_GUIDE.md)

## Appendix C: License Key Format

```
GULA-{PRODUCT_ID}-{VERSION}-{CUSTOMER_ID}-{YYYYMMDD}-{SIGNATURE}
```

Components:
- PRODUCT_ID: 8-char hex product identifier
- VERSION: Pack version (e.g., 1.0.0)
- CUSTOMER_ID: 8-char hex customer identifier
- YYYYMMDD: License expiry date
- SIGNATURE: HMAC-SHA256 of preceding fields

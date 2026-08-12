# GULA Platform — Business Maturity Assessment
**Date:** 2026-07-17

---

## 1. Maturity Levels

| Dimension | Current Level | Target | Gap |
|-----------|--------------|--------|-----|
| **Prototype** | ✅ PASSED | — | — |
| **MVP** | ✅ PASSED | — | — |
| **Production Ready** | ✅ ACHIEVED (Core LIMS) | — | — |
| **Enterprise Ready** | ⚠️ PARTIAL | Multi-branch, RBAC, audit | Subscription tiers not hardened |
| **Government Ready** | ⚠️ PARTIAL | SNDHS phase 1 done | National platform domains schema-only |
| **Healthcare Ready** | ⚠️ PARTIAL | Core LIMS + basic EHR | Pharmacy, radiology, nursing are schema-only |
| **International Ready** | ❌ NOT YET | Arabic-first | No i18n for other languages, Iraq-only focus |

---

## 2. Current Business Capabilities

### Delivered (Marketable Now)
- Laboratory Information Management System (LIMS)
- Patient registration and management
- Lab order creation, tracking, validation
- Lab result entry, interpretation, release
- Sample tracking with barcodes
- Quality control (Westgard rules)
- Digital patient cards (QR code)
- PDF report generation (Arabic)
- WhatsApp/SMS result delivery
- Basic EHR (clinical notes, conditions, medications)
- Multi-tenant isolation (per-lab)
- Role-based access control (9 roles)
- Audit logging (hash chain, tamper-proof)
- Subscription tiers (starter/growth/enterprise)
- REST API + FHIR R4

### Partially Delivered
- Insurance claims (submission workflow exists, integration TBD)
- National ID integration (verification flow exists)
- Device integration (ASTM/HL7 device_bridge production-ready)
- Dashboard and analytics (stats routes exist)
- Mobile access (mobile routes exist)

### Not Yet Delivered (Schema Only)
- Pharmacy management
- Radiology / DICOM
- Nursing workflows
- Emergency services
- Blood bank
- Critical care
- Biomedical engineering
- Public health surveillance
- National health command center
- Full clinical decision support

---

## 3. Market Position

### Target Market: Iraq
| Segment | Labs | Potential | GULA Fit |
|---------|------|-----------|----------|
| Private labs | ~500 | High | ✅ Primary target |
| Government labs | ~400 | High | ⚠️ SNDHS integration needed |
| Hospital labs | ~200 | High | ⚠️ Hospital module partial |
| Clinic labs | ~100 | Medium | ✅ Subscription starter tier |

### Competitive Advantages
- **Only Arabic-first LIS** in the market
- **Iraqi national ID integration** (MoI)
- **SNDHS-lite compliant** (National Health Data System)
- **IQD support** (Iraqi Dinar claims)
- **Offline-capable** (edge agent, PWA)
- **Government-ready** by design
- **Open source** (transparency for government)

### Pricing Strategy (from BUSINESS_PLAN.md)
| Tier | Price | Target |
|------|-------|--------|
| Starter | ~$100/mo | Small private labs |
| Growth | ~$500/mo | Medium labs |
| Enterprise | ~$5,000+/mo | Large hospital chains |
| Government | Custom | MoH, national programs |

---

## 4. Regulatory Readiness

| Regulation | Status | Evidence |
|-----------|--------|----------|
| **Iraqi SNDHS** | Phase 1 complete | Migrations, backfill scripts, flags |
| **MoI National ID** | Integration ready | Gateway stub, NID verification route |
| **Health Insurance Law No.22** | Partial | Claims routes exist |
| **ISO 27001** | Partial | Audit hash chain, encryption, access control |
| **HIPAA** | Not targeted | US regulation, not applicable |

---

## 5. Business Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **Market too small** (~1200 labs) | Medium | High | MENA expansion planned |
| **Government procurement slow** | High | Medium | Private lab focus first |
| **Competition from global LIS** | Medium | Medium | Arabic-first + Iraqi-specific integration |
| **Regulatory changes** | Medium | High | Feature flags, SNDHS phased approach |
| **Single country dependency** | High | Critical | MENA expansion in business plan |
| **Revenue model unproven** | Medium | High | No evidence of paying customers |

---

## 6. Maturity Recommendations

| Area | Recommendation | Priority |
|------|---------------|----------|
| Close schema-only domains | Ship at least one national domain (e.g., pharmacy) | High |
| Expand beyond Iraq | Internationalization framework | Medium |
| Government certification | Formal SNDHS certification process | High |
| Customer acquisition | First paying customer validation | Critical |
| Pricing refinement | Market testing needed | Medium |

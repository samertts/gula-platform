# GULA Platform — Multi-Tenancy Model

**Version:** 1.0.0

---

## 1. Tenant Hierarchy

```
Global (Country: Iraq)
├── Governorate (18 tenants)
│   ├── Directorate (122 tenants)
│   │   ├── Public Hospital (273 tenants)
│   │   ├── Private Hospital (180+ tenants)
│   │   ├── PHC Center (2,500+ tenants)
│   │   ├── Laboratory (public + private)
│   │   ├── Blood Bank
│   │   ├── Radiology Center
│   │   ├── Pharmacy
│   │   ├── Vaccination Center
│   │   ├── Public Health Office
│   │   ├── Epidemiology Unit
│   │   ├── Emergency Services
│   │   └── Medical Warehouse
│   ├── Medical University
│   └── Health Insurance Office
├── Ministry of Health (national tenant)
├── Medical Council (national tenant)
├── Nursing Council (national tenant)
├── Pharmacists Syndicate (national tenant)
└── WHO (observer tenant)
```

## 2. Tenant Model

```python
class Tenant:
    id: UUID
    tenant_id: str
    name_en: str
    name_ar: str
    type: TenantType          # governorate | directorate | hospital | lab | etc.
    parent_tenant_id: UUID | None
    level: int                # 1=country, 2=governorate, 3=directorate, 4=facility, 5=department
    hierarchy_path: str       # Materialized path: /iraq/baghdad/rusafa/hospital1
    contact_info: JSON
    config: TenantConfig
    status: active | suspended | archived
    created_at: datetime
    updated_at: datetime
```

## 3. Tenant Configuration

```json
{
  "features": {
    "ai_assist": true,
    "telemedicine": false,
    "fhir_export": true,
    "bulk_operations": true,
    "patient_portal": true,
    "insurance_billing": true,
    "research_module": false
  },
  "limits": {
    "max_users": 500,
    "max_patients": 100000,
    "max_storage_gb": 50,
    "api_rate_limit": 1000
  },
  "branding": {
    "logo_url": "https://...",
    "primary_color": "#0f172a",
    "secondary_color": "#3b82f6",
    "favicon_url": "https://..."
  },
  "localization": {
    "language": "ar",
    "timezone": "Asia/Baghdad",
    "date_format": "YYYY-MM-DD",
    "number_format": "ar_IQ"
  },
  "regulatory": {
    "framework": "iraqi_moh_2024",
    "consent_required": true,
    "audit_retention_days": 2555,
    "data_residency": "iraq"
  }
}
```

## 4. Tenant Isolation Strategies

| Strategy | Description | Used For |
|----------|-------------|----------|
| **Schema Isolation** | Separate DB schema per governorate | Governorate-level tenants |
| **Row-Level Isolation** | `tenant_id` column on all tables | Directorate, facility tenants |
| **Hybrid Isolation** | Schema for governorate, rows for facilities | Default strategy |
| **No Isolation** | Shared everything | Cross-tenant analytics |

### 4.1 Isolated Data

| Data Type | Isolation Level | Notes |
|-----------|----------------|-------|
| Patient records | Row-level by facility | Cross-tenant with consent |
| Lab orders | Row-level by facility | |
| Lab results | Row-level by facility | |
| Financial data | Row-level by facility | |
| User accounts | Row-level by org | |
| Audit logs | Schema by governorate | National audit cross-schema |
| Analytics | Schema by governorate | National rollup |

### 4.2 Shared Data

| Data Type | Storage | Notes |
|-----------|---------|-------|
| Reference data | Shared schema | Test catalogs, ICD codes, etc. |
| User directory | Shared schema | For cross-org lookup |
| National reports | National schema | Aggregated, de-identified |
| Consent registry | Shared schema | Patient consent across orgs |

## 5. Cross-Tenant Operations

### 5.1 Patient Transfer

```
Patient transfers from Hospital A (Baghdad) to Hospital B (Basra)
  → Both hospitals have consent
  → Patient record copied with consent marker
  → Original record preserved
  → Audit trail in both tenants
```

### 5.2 National Reporting

```
Governorate-level data → Materialized aggregates → National tenant
  → De-identified
  → Row counts for non-sensitive metrics
  → Differential privacy for sensitive metrics
```

### 5.3 Emergency Cross-Tenant Access

```
Treating physician at Hospital B needs Hospital A's records
  → Emergency mode activated
  → Break-glass policy applied
  → Temporary cross-tenant access
  → Notify Hospital A compliance
  → Full audit trail
```

## 6. Tenant Provisioning

```
Request → Approve → Configure
  → Create schema (if schema-isolated)
  → Seed reference data
  → Assign administrator
  → Configure feature flags
  → Set limits
  → Activate
```

## 7. Tenant API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/tenants` | List tenants |
| GET | `/tenants/:id` | Get tenant details |
| POST | `/tenants` | Create tenant |
| PUT | `/tenants/:id` | Update tenant |
| DELETE | `/tenants/:id` | Archive tenant |
| GET | `/tenants/:id/hierarchy` | Get tenant hierarchy |
| GET | `/tenants/:id/config` | Get tenant configuration |
| PUT | `/tenants/:id/config` | Update tenant configuration |
| GET | `/tenants/:id/stats` | Get tenant usage statistics |

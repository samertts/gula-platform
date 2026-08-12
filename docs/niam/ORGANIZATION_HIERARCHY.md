# NIAM — Organization Hierarchy

## Overview

The NIAM Organization model (`NIAMOrganization`, table `niam_organizations`) represents the complete national healthcare organizational hierarchy as a tree structure. Each node has a `parent_org_id` self-referencing foreign key that enables arbitrary depth hierarchies.

---

## Organizational Levels

```mermaid
graph TD
    MOH[Ministry of Health<br/>وزارة الصحة] --> D1[Health Directorate - Baghdad<br/>دائرة صحة بغداد]
    MOH --> D2[Health Directorate - Basra<br/>دائرة صحة البصرة]
    MOH --> D3[Health Directorate - Nineveh<br/>دائرة صحة نينوى]

    D1 --> H1[Baghdad Teaching Hospital<br/>مستشفى بغداد التعليمي]
    D1 --> H2[Al-Kindy Hospital<br/>مستشفى الكندي]
    D1 --> PHC1[Al-Mansour PHC Sector<br/>قطاع المنصور للرعاية الصحية]
    D1 --> GL1[Central Public Health Lab<br/>مختبر الصحة العامة المركزي]

    H1 --> Dept1[Emergency Dept<br/>قسم الطوارئ]
    H1 --> Dept2[Hematology Lab<br/>مختبر أمراض الدم]
    H1 --> Dept3[Radiology Dept<br/>قسم الأشعة]

    PHC1 --> HC1[Al-Mansour Health Center<br/>مركز المنصور الصحي]
    PHC1 --> HC2[Al-Waziriya Health Center<br/>مركز الوزيرية الصحي]

    subgraph "Level 1: Ministry"
        MOH
    end
    subgraph "Level 2: Directorate"
        D1, D2, D3
    end
    subgraph "Level 3: Facilities"
        H1, H2, PHC1, GL1
    end
    subgraph "Level 4: Departments/Units"
        Dept1, Dept2, Dept3, HC1, HC2
    end
```

---

## Organization Types (19)

| # | Type | Arabic | Description |
|---|---|---|---|
| 1 | `ministry` | وزارة | National ministry (e.g., Ministry of Health) |
| 2 | `directorate` | دائرة | Health directorate (governorate-level) |
| 3 | `government_hospital` | مستشفى حكومي | Public hospital |
| 4 | `private_hospital` | مستشفى أهلي | Private hospital |
| 5 | `primary_healthcare_sector` | قطاع رعاية صحية أولية | PHC sector (group of health centers) |
| 6 | `health_center` | مركز صحي | Primary health center |
| 7 | `government_laboratory` | مختبر حكومي | Public laboratory |
| 8 | `private_laboratory` | مختبر أهلي | Private laboratory |
| 9 | `blood_bank` | بنك دم | Blood bank |
| 10 | `forensic_medicine` | طب عدلي | Forensic medicine facility |
| 11 | `university` | جامعة | Medical university/college |
| 12 | `research_center` | مركز أبحاث | Research center |
| 13 | `insurance_company` | شركة تأمين | Health insurance company |
| 14 | `ngo` | منظمة غير حكومية | Non-governmental organization |
| 15 | `supplier` | مورد | Medical equipment/pharmaceutical supplier |
| 16 | `vendor` | بائع | Vendor |
| 17 | `medical_company` | شركة طبية | Medical company |
| 18 | `pharmacy` | صيدلية | Pharmacy |
| 19 | `external_authority` | هيئة خارجية | External authority (e.g., WHO, ICRC) |

---

## Model Structure

```python
class NIAMOrganization(IdentityBaseEntity):
    __tablename__ = "niam_organizations"

    # Identity
    uuid: str                    # Stable global identifier
    org_id: str                  # Business identifier (e.g., "MOH-BAGHDAD-001")

    # Names (bilingual)
    name_en: str                 # English name
    name_ar: str                 # Arabic name

    # Type & Hierarchy
    org_type: str                # From ORG_TYPES list
    parent_org_id: str | None    # Self-referencing FK

    # Accreditation
    license_number: str | None   # Unique license
    accreditation: str | None    # Accreditation body
    accreditation_expires: datetime | None

    # Status
    status: str                  # active, inactive, suspended

    # Integration
    fhir_endpoint: str | None    # FHIR API URL
    digital_certificate: str | None
    certificate_expires: datetime | None

    # Contact
    contact_email: str | None
    contact_phone: str | None
    address: str | None
    website: str | None

    # Geography
    governorate: str | None      # Governorate
    district: str | None         # District within governorate

    # Extensible
    subscriptions: dict | None   # Feature subscriptions (JSON)
    settings: dict | None        # Org settings (JSON)
    tags: dict | None            # Tags (JSON)
```

---

## Typical Hierarchy

### Ministry of Health Tree

```
Ministry of Health (ministry)
├── Baghdad Health Directorate (directorate)
│   ├── Baghdad Teaching Hospital (government_hospital)
│   │   ├── Emergency Department (department scope in Assignment)
│   │   ├── Hematology Laboratory (department)
│   │   └── Radiology Department (department)
│   ├── Al-Karama Hospital (government_hospital)
│   ├── Al-Mansour PHC Sector (primary_healthcare_sector)
│   │   ├── Al-Mansour Health Center (health_center)
│   │   └── Al-Waziriya Health Center (health_center)
│   └── Central Public Health Lab (government_laboratory)
├── Basra Health Directorate (directorate)
│   ├── Basra Teaching Hospital (government_hospital)
│   └── Basra Public Health Lab (government_laboratory)
└── Nineveh Health Directorate (directorate)
    └── ...
```

### Private Sector Example

```
Al-Mansour Private Laboratory Group (private_laboratory)
├── Al-Mansour Main Lab (private_laboratory)
└── Al-Mansour Satellite Lab - Karrada (private_laboratory)
```

---

## Multi-Tenant Isolation

NIAM achieves multi-tenant isolation through organization scoping:

### Organization-Based Data Isolation

Every identity-related operation is scoped to one or more organizations:

| Entity | Scoping Field | Isolation |
|---|---|---|
| `IdentityRecord` | `issued_by_organization` | Identities are issued by specific orgs |
| `Employment` | `organization_id` | Employment is specific to an org |
| `Assignment` | `organization_id` | Role assignments are org-scoped |
| `MachineIdentity` | `organization_id` | Machines belong to an org |
| `EnterpriseAccount` | `organization_id` | Enterprise accounts belong to an org |
| `Device` | (via person's employments) | Implicit org scoping |

### Query Pattern

```python
# Authorization check enforces org scope
async def has_permission(person_id, permission, organization_id=None):
    assignments = await assignment_repo.find_by_person_id(person_id)
    for assignment in assignments:
        if assignment.status != "active":
            continue
        if organization_id and assignment.organization_id != organization_id:
            continue  # Different org scope
        if permission_check(assignment, permission):
            return True
    return False
```

### Tenant Hierarchy Example

```
MoH (national tenant)
├── Baghdad Directorate (tenant within MoH)
│   ├── Baghdad Hospital (tenant within directorate)
│   └── Al-Kindy Hospital (tenant within directorate)
└── Basra Directorate (separate tenant)
```

A user employed at Baghdad Hospital:
- Can see data for Baghdad Hospital (their org)
- Cannot see data for Al-Kindy Hospital (different org, same directorate)
- Cannot see data for Basra Directorate (different directorate)
- A directorate-level admin can see all facilities within their directorate
- A ministry-level admin can see all organizations

---

## Repository Queries

The `OrganizationRepository` provides hierarchy-aware queries:

```python
class OrganizationRepository(IdentityRepositoryBase[NIAMOrganization]):

    # Find children of an organization
    async def find_children(self, parent_id: str) -> list[NIAMOrganization]:
        # SELECT * FROM niam_organizations WHERE parent_org_id = :parent_id

    # Find organizations by type
    async def find_by_type(self, org_type: str) -> list[NIAMOrganization]:
        # SELECT * FROM niam_organizations WHERE org_type = :org_type

    # Find organizations in a governorate
    async def find_by_governorate(self, governorate: str) -> list[NIAMOrganization]:
        # SELECT * FROM niam_organizations WHERE governorate = :governorate

    # Find by business identifier
    async def find_by_org_id(self, org_id: str) -> NIAMOrganization | None:
        # SELECT * FROM niam_organizations WHERE org_id = :org_id
```

---

## Organization Lifecycle

### Creation

```mermaid
graph LR
    A[Create Organization] --> B[Set type, names, parent]
    B --> C[Assign license/accreditation]
    C --> D[Set geographic scope]
    D --> E[Audit: organization_created]
```

### Updates

- Org details can be updated (names, contact, accreditation)
- `parent_org_id` can change (org tree reorganization)
- Status can change (active, inactive, suspended)
- Audit: `organization_updated`

### Deactivation

- Org is soft-deleted (`is_active=False`)
- Child orgs are NOT automatically deactivated (preserves hierarchy)
- Employments referencing this org are not auto-terminated (application-level decision)
- Enterprise accounts are not auto-deactivated

---

## Integration with Existing Lab Model

The old `Lab` model (`labs` table) is a flat, single-level organization representation. NIAM's `NIAMOrganization` replaces it with:

| Capability | Old `Lab` | NIAM `NIAMOrganization` |
|---|---|---|
| Hierarchy | Flat, single-level | Tree with `parent_org_id` |
| Types | 4 types (private, government, hospital, clinic) | 19 types |
| Geographic | `city` only | `governorate` + `district` |
| Bilingual | No | `name_en` + `name_ar` |
| Accreditation | No | Full accreditation tracking |
| Integration | No | `fhir_endpoint`, `digital_certificate` |
| Extensible | No | JSON `settings`, `subscriptions`, `tags` |
| Multi-tenant | Implicit (by lab_id) | Explicit hierarchy-based scoping |

During migration, each `Lab` becomes an `NIAMOrganization` with `org_type` mapped from `lab_type`, preserving backward compatibility through a Lab → NIAMOrganization lookup table.

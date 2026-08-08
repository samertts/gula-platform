# GULA Platform — ABAC Design

**Version:** 1.0.0

---

## 1. Attribute Model

ABAC evaluates access based on attributes from four categories:

### 1.1 Subject Attributes (Who)

| Attribute | Type | Source | Example |
|-----------|------|--------|---------|
| `user.id` | UUID | Identity Service | `usr_12345` |
| `user.type` | string | User Type | `physician` |
| `user.roles` | list | Role Mapper | `[specialist, department_head]` |
| `user.organization` | UUID | Org Service | `org_hospital_001` |
| `user.organization.type` | string | Org Service | `hospital` |
| `user.directorate` | UUID | Org Hierarchy | `dir_baghdad` |
| `user.governorate` | UUID | Org Hierarchy | `gov_baghdad` |
| `user.department` | UUID | Org Service | `dept_cardiology` |
| `user.specialty` | string | Credential Service | `cardiology` |
| `user.license` | string | Medical Council | `ML-98765` |
| `user.license_valid` | boolean | License Check | `true` |
| `user.employment_type` | string | HR | `permanent` |
| `user.clearance_level` | int | Security | `3` |
| `user.training_completed` | list | Training | `[fhir_training, consent_training]` |
| `user.mfa_verified` | boolean | Session | `true` |
| `user.risk_score` | float | Risk Engine | `0.15` |

### 1.2 Resource Attributes (What)

| Attribute | Type | Source | Example |
|-----------|------|--------|---------|
| `resource.type` | string | Resource Registry | `patient` |
| `resource.id` | UUID | Resource Registry | `res_67890` |
| `resource.owner_id` | UUID | Resource | `usr_12345` |
| `resource.organization_id` | UUID | Resource | `org_hospital_001` |
| `resource.sensitivity` | string | Classification | `sensitive` |
| `resource.classification` | string | Classification | `confidential` |
| `resource.consent_required` | boolean | Consent Service | `true` |
| `resource.consent_granted` | boolean | Consent Service | `true` |
| `resource.purpose_of_use` | string | Access Request | `treatment` |
| `resource.restricted_to` | list | Resource Policy | `[dept_cardiology]` |
| `resource.created_at` | datetime | Resource | `2026-01-15` |
| `resource.emergency_locked` | boolean | Emergency | `false` |

### 1.3 Action Attributes (How)

| Attribute | Type | Source | Example |
|-----------|------|--------|---------|
| `action.id` | string | Permission | `patient.read.sensitive` |
| `action.domain` | string | Permission Domain | `patient` |
| `action.operation` | string | CRUD | `read` |
| `action.is_sensitive` | boolean | Permission | `true` |
| `action.is_destructive` | boolean | Classification | `false` |
| `action.requires_justification` | boolean | Permission | `true` |

### 1.4 Environment Attributes (Where/When)

| Attribute | Type | Source | Example |
|-----------|------|--------|---------|
| `environment.time` | time | System Clock | `14:30:00` |
| `environment.day_of_week` | int | System Clock | `2` (Tuesday) |
| `environment.is_business_hours` | boolean | Config | `true` |
| `environment.is_holiday` | boolean | Calendar | `false` |
| `environment.ip_address` | string | Network | `10.0.1.50` |
| `environment.network_zone` | string | Network | `hospital_lan` |
| `environment.device_type` | string | Device | `workstation` |
| `environment.device_trusted` | boolean | Device Trust | `true` |
| `environment.geo_location` | string | GeoIP | `baghdad` |
| `environment.emergency_mode` | boolean | Emergency | `false` |
| `environment.risk_score` | float | Risk Engine | `0.05` |

---

## 2. Policy Model

```python
class Policy:
    id: UUID
    policy_id: str
    name_en: str
    name_ar: str
    description: str
    version: str              # semver
    status: draft | review | active | deprecated | archived
    effect: permit | deny
    priority: int             # Higher priority wins
    category: str             # access_control, data_protection, emergency
    target: PolicyTarget       # What this policy applies to
    conditions: list[Condition]
    obligations: list[Obligation]
    validity_period: TimeRange
    signature: str            # HMAC signature
    created_by: UUID
    approved_by: UUID
    published_at: datetime
    tags: list[str]
```

### 2.1 Policy Target

```python
class PolicyTarget:
    subjects: list[SubjectSelector]    # Who this applies to
    resources: list[ResourceSelector]  # What resources
    actions: list[ActionSelector]      # What actions
    environments: list[EnvSelector]    # Under what conditions
```

### 2.2 Condition

```python
class Condition:
    attribute: str          # e.g., "user.organization"
    operator: str            # eq, neq, in, not_in, gt, gte, lt, lte, contains
    value: any               # The value to compare against
    function: str | None     # Optional function to apply (e.g., "date_diff")
```

### 2.3 Obligation

```python
class Obligation:
    type: str                # audit, log, notify, mfa_required, consent_check
    config: dict             # Obligation-specific configuration
```

---

## 3. Policy Examples

### 3.1 Basic Access Control

```json
{
  "policy_id": "patient_read_own_org",
  "name": "Patient Read - Same Organization",
  "effect": "permit",
  "priority": 100,
  "conditions": [
    {"attribute": "user.organization_id", "operator": "eq", "value": "resource.organization_id"},
    {"attribute": "action.id", "operator": "eq", "value": "patient.read"}
  ]
}
```

### 3.2 Sensitive Data Access

```json
{
  "policy_id": "sensitive_data_restricted",
  "name": "Sensitive Data - Specialist + Justification",
  "effect": "permit",
  "priority": 200,
  "conditions": [
    {"attribute": "resource.sensitivity", "operator": "eq", "value": "sensitive"},
    {"attribute": "user.roles", "operator": "contains", "value": "specialist_physician"},
    {"attribute": "action.is_sensitive", "operator": "eq", "value": true},
    {"attribute": "user.clearance_level", "operator": "gte", "value": 3}
  ],
  "obligations": [
    {"type": "audit", "config": {"level": "detailed"}},
    {"type": "justification", "config": {"required": true}}
  ]
}
```

### 3.3 Emergency Access

```json
{
  "policy_id": "emergency_break_glass",
  "name": "Emergency Break Glass Access",
  "effect": "permit",
  "priority": 1000,
  "conditions": [
    {"attribute": "environment.emergency_mode", "operator": "eq", "value": true},
    {"attribute": "user.roles", "operator": "in", "value": ["physician", "emergency_physician", "nurse"]}
  ],
  "obligations": [
    {"type": "audit", "config": {"level": "maximum"}},
    {"type": "notify", "config": {"targets": ["supervisor", "compliance_officer"]}},
    {"type": "time_limit", "config": {"duration_minutes": 240}}
  ]
}
```

### 3.4 Time-Based Access

```json
{
  "policy_id": "lab_technician_business_hours",
  "name": "Lab Technician - Business Hours Only",
  "effect": "deny",
  "priority": 50,
  "conditions": [
    {"attribute": "user.roles", "operator": "contains", "value": "lab_technician"},
    {"attribute": "environment.is_business_hours", "operator": "eq", "value": false}
  ]
}
```

### 3.5 Patient Consent Check

```json
{
  "policy_id": "research_data_consent",
  "name": "Research Data - Requires Patient Consent",
  "effect": "deny",
  "priority": 300,
  "conditions": [
    {"attribute": "resource.consent_required", "operator": "eq", "value": true},
    {"attribute": "resource.consent_granted", "operator": "neq", "value": true},
    {"attribute": "environment.emergency_mode", "operator": "neq", "value": true}
  ]
}
```

### 3.6 Cross-Organization Data Sharing

```json
{
  "policy_id": "cross_org_data_sharing",
  "name": "Cross-Organization Data Sharing",
  "effect": "permit",
  "priority": 150,
  "conditions": [
    {"attribute": "user.organization_id", "operator": "neq", "value": "resource.organization_id"},
    {"attribute": "action.id", "operator": "in", "value": ["patient.read", "result.read"]},
    {"attribute": "environment.purpose_of_use", "operator": "eq", "value": "treatment"},
    {"attribute": "resource.consent_granted", "operator": "eq", "value": true}
  ],
  "obligations": [
    {"type": "audit", "config": {"level": "detailed"}},
    {"type": "notify", "config": {"targets": ["resource.owner_org_compliance"]}}
  ]
}
```

---

## 4. Policy Evaluation

### 4.1 Decision Algorithm

```
1. Collect all attributes (subject, resource, action, environment)
2. Find all policies matching the request (by target)
3. Sort policies by priority (highest first)
4. For each policy:
   a. Evaluate all conditions
   b. If all conditions match:
      - If effect is "deny": return DENY
      - If effect is "permit": return PERMIT
5. Return NOT_APPLICABLE
6. Return INDETERMINATE on error
```

### 4.2 Combining Algorithms

| Algorithm | Behavior |
|-----------|----------|
| `deny_overrides` | Any deny = DENY (default) |
| `permit_overrides` | Any permit = PERMIT |
| `first_applicable` | First matching policy decides |
| `only_one` | Exactly one policy must apply |

---

## 5. ReBAC (Relationship-Based Access Control)

ReBAC extends ABAC with relationship-based policies.

### 5.1 Relationship Types

| Relationship | Subject | Object | Direction |
|-------------|---------|--------|-----------|
| `treating` | Doctor | Patient | Directed |
| `referred_by` | Doctor | Doctor | Directed |
| `guardian_of` | Guardian | Patient | Directed |
| `employed_by` | Staff | Organization | Directed |
| `assigned_to` | User | Department | Directed |
| `supervises` | Supervisor | Employee | Directed |
| `member_of` | User | Team | Directed |
| `family_of` | Person | Person | Undirected |
| `researcher_of` | Researcher | Study | Directed |
| `assigned_to_case` | Staff | Case | Directed |

### 5.2 Relationship Policy Example

```json
{
  "policy_id": "treating_physician_access",
  "name": "Treating Physician - Full Access",
  "effect": "permit",
  "conditions": [
    {"attribute": "relationship.type", "operator": "eq", "value": "treating"},
    {"attribute": "relationship.subject_id", "operator": "eq", "value": "user.id"},
    {"attribute": "relationship.object_id", "operator": "eq", "value": "resource.patient_id"}
  ]
}
```

---

## 6. Policy Lifecycle

```
Draft (Policy Author)
  → Review (Security Committee)
    → Approved (CISO)
      → Published (System) 
        → Active
          → Deprecated (Policy Author)
            → Archived (System)
              → Deleted (System, after retention)
```

### 6.1 Versioning

- Every policy change creates a new version
- Version history is preserved
- Rollback restores previous version
- Policy simulator can test any version

### 6.2 Policy Testing

- Built-in policy simulator
- Dry-run mode for new policies
- Impact analysis before publishing
- A/B testing of policy variants

---

## 7. Attribute Providers

| Provider | Attributes | Refresh |
|----------|-----------|---------|
| Identity Service | user.id, user.type, user.name | Per-request |
| Role Engine | user.roles, user.permissions | On role change |
| Organization Service | org, directorate, governorate | Per-request |
| Credential Service | license, specialty, certifications | Daily |
| Risk Engine | risk_score, trust_level | Per-request |
| Consent Service | consent_granted, consent_type | On consent change |
| Device Trust | device_type, device_trusted | Per-session |
| Network Service | ip, network_zone, geo | Per-request |
| Calendar | is_holiday, business_hours | Daily |
| Emergency Service | emergency_mode | Real-time |
| Session Service | mfa_verified, auth_method | Per-request |

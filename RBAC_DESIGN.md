# GULA Platform — RBAC Design

**Version:** 1.0.0

---

## 1. Role Model

```python
class Role:
    id: UUID
    role_id: str          # e.g., "lab_technician"
    name_en: str          # "Lab Technician"
    name_ar: str          # "فني مختبر"
    description: str
    level: str            # national | governorate | institution | department | personal
    parent_role_id: str | None   # Inherits permissions from parent
    role_group_id: str | None
    is_temporary: bool    # Can be assigned temporarily
    is_delegatable: bool  # Can be delegated to another user
    requires_mfa: bool    # MFA required for this role
    max_duration_hours: int | None  # Max continuous assignment
    permissions: list[Permission]
    created_at: datetime
    updated_at: datetime
    version: int
```

## 2. Role Inheritance

Roles form a hierarchy. A role inherits all permissions from its ancestors.

```
minister_of_health
  └── director_general
       └── governorate_director
            └── hospital_director
                 └── medical_director
                      └── department_head
                           └── specialist_physician
                                └── resident_physician
                                     └── intern_physician
```

### Inheritance Rules
- A child role **inherits** all permissions from its parent
- A child role can **add** additional permissions
- A child role can **never remove** inherited permissions
- Multiple inheritance is supported (e.g., `lab_quality_officer` inherits from both `lab_technician` and `quality_officer`)

## 3. Role Assignment

```python
class RoleAssignment:
    id: UUID
    user_id: UUID           # Assigned user
    role_id: UUID           # Role reference
    organization_id: UUID   # Scope (where this role applies)
    facility_id: UUID       # Optional facility scope
    department_id: UUID     # Optional department scope
    assigned_by: UUID       # Who assigned
    assigned_at: datetime
    expires_at: datetime | None  # For temporary assignments
    is_primary: bool        # Primary role for UI defaults
    is_delegated: bool      # Was this role delegated?
    delegation_id: UUID | None
    status: active | suspended | expired
```

### Assignment Rules
- A user can have multiple role assignments
- Each assignment is scoped to an organization/facility/department
- One primary role determines default UI experience
- Temporary roles have an expiration
- Delegated roles track the delegation source

## 4. Role Groups

```python
class RoleGroup:
    id: UUID
    group_id: str
    name_en: str
    name_ar: str
    description: str
    roles: list[Role]
    is_template: bool       # Can be used as provisioning template
```

### Groups

| Group | Included Roles | Common Purpose |
|-------|---------------|----------------|
| `hospital_executive` | hospital_director, deputy_director, medical_director, nursing_director, financial_director | Hospital leadership team |
| `lab_operations` | lab_director, lab_supervisor, lab_technician, senior_technician, phlebotomist | Complete lab team |
| `emergency_team` | emergency_director, emergency_physician, emergency_nurse, paramedic, dispatcher | Emergency department |
| `phc_team` | phc_director, gp, nurse, pharmacist, community_worker | PHC center team |
| `surgery_team` | surgeon, anesthesiologist, surgical_nurse, scrub_tech | Operating room |

## 5. Role Templates

Templates allow rapid provisioning of common role combinations:

```json
{
  "template_id": "hospital_leadership",
  "name": "Hospital Leadership Team",
  "roles": ["hospital_director", "deputy_hospital_director", "medical_director"],
  "default_permissions_extras": ["system.admin.reports"],
  "on_create": {
    "notify": ["governorate_director"],
    "create_shared_resources": true
  }
}
```

## 6. Permission Model

```python
class Permission:
    id: UUID
    permission_id: str      # e.g., "patient.read"
    name_en: str            # "Read Patient"
    name_ar: str            # "عرض المريض"
    description: str
    domain: str             # patient, order, result, etc.
    resource: str           # The resource type
    action: str             # create, read, update, delete, etc.
    is_sensitive: bool      # Requires additional justification
    is_audited: bool        # Always audit this action
    requires_mfa: bool      # MFA required for this permission
    requires_justification: bool  # Reason required
    risk_level: low | medium | high | critical  # Risk classification
```

## 7. Permission Assignment

Permissions can be assigned at multiple levels:

1. **Role-level**: Assigned to a role, inherited by all role members
2. **User-level**: Direct permission override for specific users
3. **Temporary**: Time-bound permission grants
4. **Contextual**: Permission granted based on context (ABAC)

### Resolution Order

```
User-level explicit deny → Contextual deny → Role-level deny
  → User-level explicit allow → Contextual allow → Role-level allow
  → Default deny
```

## 8. Role ↔ Permission Matrix Generation

The role-permission matrix is generated from role hierarchy and permission definitions. Each role's effective permission set is computed by:

1. Start with all permissions from parent roles (recursive)
2. Add role-specific permissions
3. Apply any user-level overrides
4. Apply any context-based constraints (ABAC)
5. Return the resolved permission set

## 9. Role Provisioning Workflow

```
Request → Verify Identity → Select Role → Assign Organization
  → Configure Scope → Approve (if required) → Notify
    → Activate → Periodic Review → Modify → Deactivate
```

## 10. RBAC API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/rbac/roles` | List all roles |
| GET | `/rbac/roles/:id` | Get role details |
| POST | `/rbac/roles` | Create role |
| PUT | `/rbac/roles/:id` | Update role |
| DELETE | `/rbac/roles/:id` | Delete role |
| GET | `/rbac/roles/:id/permissions` | Get role's effective permissions |
| PUT | `/rbac/roles/:id/permissions` | Update role's permissions |
| GET | `/rbac/assignments` | List role assignments |
| POST | `/rbac/assignments` | Assign role to user |
| PUT | `/rbac/assignments/:id` | Update assignment |
| DELETE | `/rbac/assignments/:id` | Remove assignment |
| GET | `/rbac/groups` | List role groups |
| POST | `/rbac/groups` | Create role group |
| GET | `/rbac/templates` | List role templates |
| POST | `/rbac/templates/apply` | Apply template |

## 11. RBAC Audit

Every RBAC operation is audited:
- Role creation, modification, deletion
- Role assignment, removal
- Permission changes
- Role group changes
- Template applications
- All tracked with who, when, why, and previous values

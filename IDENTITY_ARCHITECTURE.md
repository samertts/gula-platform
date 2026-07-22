# GULA National Identity & Authorization Architecture

**Version:** 1.0.0
**Date:** 2026-07-22
**Authority:** Chief Identity & Authorization Architect
**Domain:** gula-platform.org

---

## 1. Identity Model

### 1.1 Identity Types

The platform supports 18 identity types unified under a single `Identity` abstraction:

| ID Type | Source | Verification | Purpose |
|---------|--------|-------------|---------|
| `national_health_id` | GULA Registry | Biometric + document | Primary patient identifier |
| `national_id` | Civil Affairs Authority | Document scan | Legal identity |
| `passport` | Immigration | Document scan | Cross-border care |
| `residency_id` | Residency Affairs | Document scan | Resident care |
| `employee_id` | HR System | Internal | Staff identification |
| `medical_license` | Medical Council | Degree verification | Clinical practice |
| `student_id` | University | Enrollment verification | Academic placement |
| `insurance_id` | Insurance Provider | Policy verification | Billing |
| `temporary_visitor_id` | GULA Registry | Short-duration | Transient care |
| `biometric_id` | GULA Biometric Service | Fingerprint/iris | Strong auth |
| `qr_identity` | GULA QR Service | Cryptographic token | Patient card |
| `patient_card_id` | GULA Card Service | HMAC-signed token | Digital card |
| `device_identity` | GULA Device Registry | X.509 cert | Lab instrument |
| `api_identity` | GULA API Gateway | API key | System integration |
| `service_account` | GULA Admin | JWT | Automated tasks |
| `robot_account` | GULA Robot Registry | Client cert | Robotic process |
| `ai_agent_identity` | GULA AI Registry | API key + token | AI operations |
| `edge_device_identity` | GULA Edge Registry | Device cert | Offline sites |
| `iot_identity` | GULA IoT Registry | Device attestation | Smart devices |

### 1.2 Identity Lifecycle

```
Request → Verify → Issue → Activate → Suspend → Reactivate → Revoke → Archive
```

Each identity type has its own lifecycle workflow with configurable steps.

### 1.3 Identity Unification

The `Identity` model binds all identity types to a single person or entity:

```
Person
  ├── national_id: IQN123456789
  ├── passport: P123456
  ├── national_health_id: GULA-00000001
  ├── employee_id: EMP-00123
  ├── medical_license: ML-98765
  └── insurance_ids: [INS-ABC-001, INS-DEF-002]
```

### 1.4 Identity Verification Levels

| Level | Name | Requirements |
|-------|------|-------------|
| L0 | Anonymous | No verification |
| L1 | Basic | Email + phone OTP |
| L2 | Verified | National ID scan |
| L3 | Enhanced | National ID + biometric |
| L4 | High Assurance | In-person + biometric + document verification |

---

## 2. Identity Service Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Identity Service                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Identity  │  │ Verification│  │ Biometric │  │ QR/Card  │   │
│  │ Registry  │  │ Service   │  │ Service   │  │ Service   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Federation│  │ Credential│  │ Audit     │  │ Sync     │   │
│  │ Service   │  │ Service   │  │ Service   │  │ Service   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 2.1 Identity Registry

Central store for all identity records. Encrypted at rest with column-level encryption for sensitive fields (national_id, phone, address).

### 2.2 Verification Service

Handles identity verification workflows:
- Document verification (AI-assisted)
- Biometric matching
- Liveness detection
- Third-party verification (Civil Affairs, Immigration)

### 2.3 Federation Service

Federates identity across:
- Ministry of Health identity system
- Civil Affairs Authority
- Medical Council
- Insurance providers
- University systems
- International health identity systems (WHO)

### 2.4 Credential Service

Manages credential lifecycle:
- Password hashing (bcrypt, PBKDF2, Argon2id)
- TOTP/WebAuthn MFA enrollment
- API key generation and rotation
- X.509 certificate management
- OAuth2/OIDC token issuance

### 2.5 QR/Card Service

Generates and verifies:
- HMAC-signed patient card tokens
- QR codes with cryptographic signatures
- Barcode generation (PDF417, Code128)
- Card revocation and reissue

---

## 3. Organization Hierarchy

```
Country (Iraq)
├── Governorate (18)
│   ├── Directorate (122)
│   │   ├── Public Hospital (273)
│   │   ├── Private Hospital (180+)
│   │   ├── PHC Center (2,500+)
│   │   ├── Laboratory (both public/private)
│   │   ├── Blood Bank
│   │   ├── Radiology Center
│   │   ├── Pharmacy
│   │   ├── Vaccination Center
│   │   ├── Public Health Office
│   │   ├── Epidemiology Unit
│   │   ├── Emergency Services
│   │   ├── Medical Warehouse
│   │   └── Medical University
│   └── Directorate-Level Authorities
│       ├── Health Insurance Office
│       └── Medical Research Center
├── Ministry of Health
│   ├── Minister's Office
│   ├── Deputy Ministers
│   ├── Directorates General
│   └── National Centers
├── Medical Council
├── Nursing Council
├── Pharmacists Syndicate
├── Universities (Medical Colleges)
├── NGOs (Health sector)
└── WHO (Observer)
```

### 3.1 Organizational Identity

Every organization entity gets a `Organization` record with:
- Legal identifier (Ministry registration)
- Organization type
- Parent organization
- Geolocation (province, district, coordinates)
- Contact information
- Digital signature (for document signing)
- Accreditation status

---

## 4. Tenant Model

### 4.1 Tenant Hierarchy

```
Global Tenant (Country)
├── Governorate Tenant (18)
│   ├── Directorate Tenant (122)
│   │   ├── Facility Tenant (3,000+)
│   │   │   ├── Department Tenant
│   │   │   │   ├── Team Tenant
│   │   │   │   └── Personal Workspace
│   │   │   └── Laboratory Tenant
│   │   └── Cross-Org Collaboration Space
│   └── Regional Services Tenant
└── National Services Tenant
    ├── National Registry Tenant
    ├── National Analytics Tenant
    └── National AI Tenant
```

### 4.2 Tenant Isolation

- **Hard isolation**: Separate database schemas for governorate-level data
- **Soft isolation**: Row-level filtering by `tenant_id` within schemas
- **Cross-tenant**: Federated queries with explicit consent for national reporting

### 4.3 Tenant Capabilities

Each tenant has configurable:
- Feature flags
- Storage quota
- API rate limits
- User capacity
- Integration endpoints
- Custom branding
- Language preferences
- Timezone
- Regulatory framework (base + local)

---

## 5. Authorization Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Authorization Service                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐       │
│  │ RBAC     │  │ ABAC     │  │ PBAC     │  │ ReBAC        │       │
│  │ Engine   │  │ Engine   │  │ Engine   │  │ (Relationship)│       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────┬───────┘       │
│       │              │             │               │               │
│  ┌────┴──────────────┴─────────────┴───────────────┴────────┐      │
│  │                    Policy Decision Point (PDP)            │      │
│  └────────────────────────────┬─────────────────────────────┘      │
│                               │                                    │
│  ┌────────────────────────────┴─────────────────────────────┐      │
│  │               Policy Enforcement Point (PEP)              │      │
│  └──────────────────────────────────────────────────────────┘      │
│                                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ Policy   │  │ Policy   │  │ Role     │  │ Delegation       │  │
│  │ Registry │  │ Simulator│  │ Manager  │  │ Service          │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ Audit    │  │ Break    │  │ Session  │  │ Emergency        │  │
│  │ Logger   │  │ Glass    │  │ Manager  │  │ Access Service   │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.1 RBAC (Phase 3+4)

- 120–180 enterprise roles
- Role hierarchy with inheritance
- Role groups for common assignments
- Role templates for rapid provisioning
- Temporary and delegated roles

### 5.2 ABAC (Phase 5)

- Attribute-based policy evaluation
- 30+ attribute categories
- XACML-inspired policy language
- Policy versioning and lifecycle
- Policy simulation and testing

### 5.3 ReBAC (Relationship-Based)

- Doctor ↔ Patient (treating, referred, consulted)
- Guardian ↔ Child (parental, legal guardian, custodian)
- Lab ↔ Specimen (collected, processed, stored)
- Hospital ↔ Staff (employed, contracted, visiting)
- Supervisor ↔ Employee (direct, dotted-line, temporary)
- Researcher ↔ Study (principal, co-investigator, assistant)
- Citizen ↔ Family (member, dependent, head)
- Emergency Team ↔ Incident (assigned, backup, commander)

### 5.4 Authorization Decision Flow

```
Request → PEP intercepts → Build context (user, resource, action, environment)
  → PDP evaluates policies (RBAC → ABAC → ReBAC → PBAC → Break Glass)
  → Decision (Permit/Deny/NotApplicable/Indeterminate)
  → Audit log → PEP enforces → Response
```

---

## 6. Field-Level Security

Every field in every resource type has a security profile:

| Security Level | Behavior |
|---------------|----------|
| PUBLIC | Visible to all authenticated users |
| INTERNAL | Visible within the same organization |
| RESTRICTED | Visible based on role + need-to-know |
| SENSITIVE | Visible only with explicit permission + purpose |
| PROTECTED | Hidden by default, revealed on consent |
| CONFIDENTIAL | Encrypted, visible only with break-glass |
| SECRET | Never displayed, audit-only access |

### 6.1 Field Categories

| Category | Fields | Default Level |
|----------|--------|--------------|
| Demographic | Name, DOB, gender | PUBLIC |
| Contact | Phone, email, address | RESTRICTED |
| Identity | National ID, passport | PROTECTED |
| Clinical | Diagnosis, lab results | RESTRICTED |
| Sensitive | HIV, cancer, psychiatric | CONFIDENTIAL |
| Genetic | DNA, genome data | SECRET |
| Financial | Insurance, billing | PROTECTED |
| Employment | Salary, performance | RESTRICTED |
| Legal | Court orders, consent | CONFIDENTIAL |

---

## 7. Delegation Model

| Delegation Type | Duration | Scope | Approval |
|----------------|----------|-------|----------|
| Temporary | Fixed hours | Defined role subset | Self + supervisor |
| Shift | Per shift period | Full role | Schedule |
| Emergency | Until resolved | Escalated role | Break-glass |
| Vacation | Calendar days | Full role | Supervisor |
| Supervisor | Ongoing | Direct reports | HR |
| Acting Director | Appointment term | Full role | Ministry |

### 7.1 Delegation Constraints

- Maximum delegation period (configurable per role)
- One active delegation per user per role
- Audit trail for every delegation action
- Automatic expiration with notification
- Multi-level approval for critical roles

---

## 8. Emergency Access (Break Glass)

### 8.1 Triggers

- Patient critical condition
- System failure
- Natural disaster
- Epidemic outbreak
- Missing primary physician
- Time-sensitive clinical decision

### 8.2 Process

```
Alert → Justification required → Temporary elevated access granted
  → Parallel notification to supervisor + security team
  → Automatic audit record
  → Access expires after configured period
  → Post-event review required
```

### 8.3 Control Measures

- Justification is mandatory (free text + category)
- Time limit enforced (default: 4 hours, max: 24 hours)
- All actions during break-glass are recorded and highlighted
- Weekly review of all break-glass incidents
- Quarterly trend analysis
- Abuse triggers immediate revocation + investigation

---

## 9. Authorization Governance

| Function | Body | Frequency |
|----------|------|-----------|
| Policy Creation | Authorization Team | As needed |
| Policy Review | Security Committee | Quarterly |
| Policy Approval | CISO + CPO | On creation |
| Policy Versioning | Git-based | Every change |
| Policy Publication | Automated | After approval |
| Policy Rollback | Authorized admin | With reason |
| Policy Simulation | Test environment | Before deployment |
| Compliance Audit | External auditor | Annually |
| Digital Signing | Policy author | Every policy |

### 9.1 Policy Engine

```
Policy = {
  id: uuid,
  name: string,
  version: semver,
  description: string,
  category: string,
  status: draft|review|active|deprecated|archived,
  rules: [Rule],
  effect: permit|deny,
  priority: integer,
  validity_period: {start, end},
  signature: string (HMAC),
  created_by: User,
  approved_by: User,
  published_at: datetime,
  tags: [string]
}
```

### 9.2 Policy Simulator

Allows authorized administrators to:
- Select a role and user context
- Simulate an access request
- View which policies apply and their decisions
- See the full policy evaluation trace
- Export simulation results for audit

---

## 10. Authorization Audit

Every authorization decision is recorded:

| Field | Description |
|-------|-------------|
| `decision_id` | UUID of the decision |
| `timestamp` | UTC timestamp |
| `user_id` | The requesting user |
| `user_role` | User's current role |
| `user_org` | User's organization |
| `action` | The attempted action |
| `resource_type` | Type of resource |
| `resource_id` | Resource identifier |
| `decision` | Permit/Deny |
| `policies_applied` | List of policy IDs |
| `policy_engine` | RBAC/ABAC/ReBAC/BreakGlass |
| `context` | Request context (device, IP, location, time) |
| `risk_score` | Computed risk score |
| `justification` | If break-glass, the provided reason |
| `delegation_id` | If delegated, the delegation reference |
| `emergency` | Boolean, was this emergency access |

### 10.1 Audit Storage

- Immutable append-only log
- Hash-chain linking for tamper detection
- Multi-region replication
- Retention: 7 years (legal requirement)
- Daily integrity verification

---

## 11. Authorization API

### 11.1 Core Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/authz/check` | Check single permission |
| POST | `/authz/check-batch` | Check multiple permissions |
| GET | `/authz/permissions` | Get user's permissions |
| GET | `/authz/roles` | Get role definitions |
| GET | `/authz/menus` | Get dynamic menu tree |
| GET | `/authz/routes` | Get allowed routes |
| GET | `/authz/field-security` | Get field-level security |
| GET | `/authz/widgets` | Get dashboard widgets |
| GET | `/authz/actions` | Get allowed actions |
| POST | `/authz/delegate` | Create delegation |
| GET | `/authz/delegations` | List delegations |
| POST | `/authz/break-glass` | Activate emergency access |
| GET | `/authz/audit` | Query authorization audit log |
| POST | `/authz/policies` | Create policy |
| GET | `/authz/policies` | List policies |
| GET | `/authz/policies/:id/simulate` | Simulate policy |
| GET | `/authz/roles/:id/preview` | Preview role |
| GET | `/authz/me` | Get current user's full authorization context |

### 11.2 Authorization Context Response

```json
{
  "user": { "id": "uuid", "name": "...", "type": "doctor" },
  "organizations": [{ "id": "uuid", "type": "hospital", "role": "chief_of_staff" }],
  "roles": ["hospital_doctor", "senior_physician"],
  "permissions": ["patient.read", "patient.write", "order.create"],
  "menus": [{ "id": "patients", "label": "المرضى", "icon": "users", "children": [...] }],
  "routes": ["/patients", "/patients/new", "/patients/:id"],
  "field_security": {
    "patient": {
      "national_id": "protected",
      "phone": "restricted",
      "diagnosis": "restricted"
    }
  },
  "widgets": ["pending_orders", "critical_alerts", "today_appointments"],
  "features": ["ai_assist", "bulk_import", "export_pdf"],
  "tenant": { "id": "uuid", "type": "hospital", "hierarchy": [...] },
  "delegations": [],
  "emergency_mode": false,
  "session": { "id": "uuid", "expires_at": "...", "mfa_verified": true }
}
```

---

## 12. Security Principles

1. **Least Privilege**: Users get only the permissions they need
2. **Separation of Duties**: Conflicting permissions are never combined
3. **Defense in Depth**: RBAC + ABAC + field-level security + audit
4. **Fail Secure**: Default deny for all decisions
5. **Complete Mediation**: Every access is checked, every time
6. **Accountability**: Every decision is logged and attributable
7. **Privacy by Design**: Data minimization, purpose limitation
8. **Consent**: Patient consent is integrated into access decisions
9. **Emergency Access**: Break-glass with mandatory justification + audit
10. **Continuous Verification**: Re-verify for sensitive operations

---

## 13. Compliance & Standards

| Standard | Application |
|----------|------------|
| ISO 27001 | Information security management |
| ISO 27799 | Health informatics security |
| HIPAA | Privacy and security rules |
| GDPR | Data protection and privacy |
| Iraqi MoH | National health data regulations |
| NIST SP 800-53 | Security and privacy controls |
| HL7 FHIR | Healthcare interoperability |
| XACML 3.0 | ABAC policy language |
| SCIM 2.0 | Identity provisioning |
| OAuth 2.0 + OIDC | Authentication and identity |
| SAML 2.0 | Enterprise SSO |
| WebAuthn | Passwordless authentication |

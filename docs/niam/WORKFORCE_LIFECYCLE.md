# NIAM — Workforce Lifecycle

## Overview

NIAM supports two distinct workforce lifecycles: **Private Workforce** (enterprise-admin managed) and **Government Workforce** (HR-driven). Both flow through identity verification, licensing checks, conflict detection, and activation before reaching operational status.

---

## Private Workforce Lifecycle

### State Machine

```mermaid
stateDiagram-v2
    [*] --> Requested: Enterprise Admin Creates Request
    Requested --> NationalIDValidation: Submit NID
    NationalIDValidation --> LicenseValidation: NID Verified
    NationalIDValidation --> Rejected: NID Not Found
    LicenseValidation --> BoardVerification: License Valid
    LicenseValidation --> Rejected: Invalid/Missing License
    BoardVerification --> ConflictDetection: Board Cleared
    BoardVerification --> Rejected: Board Disciplinary Action
    ConflictDetection --> Approval: No Conflicts
    ConflictDetection --> Rejected: Conflicts Detected
    Approval --> Activation: Approved
    Activation --> Operational: Account Activated
    Operational --> Suspended: Violation
    Suspended --> Activation: Appeal & Restore
    Suspended --> Termination: Permanent
    Operational --> Transfer: Transfer Request
    Transfer --> Operational: Transfer Complete
    Operational --> Termination: Resignation/Termination
    Termination --> HistoricalPreservation: Archive
    HistoricalPreservation --> [*]
```

### Request Model (`WorkforceRequest`)

Fields: `request_id`, `request_type`, `requesting_org_id`, `requested_by`, `person_id`, `national_id_hash`, `license_number`, `board_registration`, `employment_rules_check` (JSON), `conflict_report` (JSON), `restrictions` (JSON).

Key checks:
- **Employment Rules**: Ministry of Health employment rules compliance
- **Conflict Detection**: Existing employments, time conflicts, org conflicts
- **Restrictions**: Gag orders, legal restrictions, board sanctions

---

## Government Workforce Lifecycle

### State Machine

```mermaid
stateDiagram-v2
    [*] --> Draft: HR Initiates Appointment
    Draft --> HRApproval: Submit to HR
    HRApproval --> IdentityCreated: HR Approved
    IdentityCreated --> CredentialIssued: Identity Verified
    CredentialIssued --> AccountActivated: Credential Created
    AccountActivated --> PermissionsAssigned: Account Activated
    PermissionsAssigned --> Active: Permissions Set
    Active --> Promotion: Career Progression
    Promotion --> Active: Promoted
    Active --> Transfer: Org Change
    Transfer --> Active: Transferred
    Active --> Retirement: End of Service
    Retirement --> Delegation: Knowledge Transfer
    Delegation --> [*]
```

### Appointment Model (`GovernmentAppointment`)

Fields: `appointment_id`, `person_id`, `organization_id`, `hr_reference`, `appointment_type`, `position`, `grade`, `salary_scale`, `department`, `start_date`, `end_date`.

Boolean gates for lifecycle progression:
- `hr_approved_by` / `hr_approved_at`
- `identity_created`
- `credential_issued`
- `account_activated`
- `permissions_assigned`

### Career Events

- **Promotion**: `promotion_history` (JSON array of position changes)
- **Transfer**: `transfer_history` (JSON array of org/department changes)
- **Retirement**: End-of-service processing with delegation
- **Delegation**: Knowledge transfer handover to successor

---

## Common Features

### Suspension

Both workforce types support suspension with:
- `suspension_reason`, severity levels
- Time-bound or indefinite
- Appeal workflow (connected to IDENTITY_GOVERNANCE appeals)
- Restoration with audit trail

### Termination

Tracked via `termination_reason` and `termination_date`. Private workforce supports `historical_preserved` flag for archival.

### Historical Preservation

Terminated employments are preserved for audit purposes. The `WorkforceRequest.historical_preserved` flag ensures HR records remain accessible post-termination.

---

## Database Tables

| Table | Purpose |
|-------|---------|
| `niam_lifecycle_workforce_requests` | Private workforce lifecycle |
| `niam_lifecycle_gov_appointments` | Government workforce lifecycle |

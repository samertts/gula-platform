# NIAM — Audit Model

## Overview

The NIAM audit system (`IdentityAuditEntry`, table `niam_audit_entries`) provides an immutable, comprehensive audit trail for every identity-related event in the platform. Every person creation, identity verification, account lock, session start, permission grant, and security breach is recorded with full context for non-repudiation.

---

## Audit Entry Structure

```python
class IdentityAuditEntry(IdentityBaseEntity):
    __tablename__ = "niam_audit_entries"

    uuid: str                    # Unique event identifier
    action: str                  # From AuditAction enum (38 values)
    actor_id: str | None         # Who performed the action
    actor_type: str | None       # Actor category (person, system, machine, enterprise)
    target_type: str | None      # Entity type affected
    target_id: str | None        # Entity ID affected
    changes: dict | None         # JSON diff (before/after)
    metadata: dict | None        # Additional structured data
    context: dict | None         # Request-level context
    ip_address: str | None       # Client IP address
    user_agent: str | None       # HTTP User-Agent header
    session_id: str | None       # Session UUID
    occurred_at: datetime        # Event timestamp (NOT NULL, INDEXED)
    organization_id: str | None  # Organizational context
    outcome: str                 # success, failure, denied
    error_message: str | None    # Error details if outcome=failure
```

---

## Audit Actions (38)

### Person Actions

| Action | Description |
|---|---|
| `person_created` | A new person record was created |
| `person_updated` | Person biographical data was updated |
| `person_deactivated` | Person was deactivated/soft-deleted |

### Identity Actions

| Action | Description |
|---|---|
| `identity_created` | An identity record was created for a person |
| `identity_verified` | An identity was verified (in-person, NID check, etc.) |
| `identity_revoked` | An identity was revoked |

### Account Actions

| Action | Description |
|---|---|
| `account_created` | A new account was created for an identity |
| `account_locked` | Account was locked (failed attempts or admin action) |
| `account_unlocked` | Account was unlocked (auto or admin) |
| `account_password_changed` | Password was changed |
| `account_mfa_enabled` | MFA was enabled on the account |
| `account_mfa_disabled` | MFA was disabled on the account |

### Employment Actions

| Action | Description |
|---|---|
| `employment_created` | Employment record was created |
| `employment_terminated` | Employment was terminated |

### Assignment Actions

| Action | Description |
|---|---|
| `assignment_created` | Role assignment was created |
| `assignment_revoked` | Role assignment was revoked |

### Session Actions

| Action | Description |
|---|---|
| `session_started` | User logged in and session was created |
| `session_terminated` | Session was terminated (logout, expiry, admin) |

### Credential Actions

| Action | Description |
|---|---|
| `credential_created` | A credential (passkey, API key, etc.) was registered |
| `credential_revoked` | A credential was revoked |

### Role/Permission Actions

| Action | Description |
|---|---|
| `role_assigned` | A role was assigned to a person |
| `role_revoked` | A role was revoked from a person |
| `permission_granted` | A permission was granted |
| `permission_revoked` | A permission was revoked |

### Policy Actions

| Action | Description |
|---|---|
| `policy_created` | A new ABAC policy was created |
| `policy_updated` | An existing policy was updated |
| `policy_enforced` | A policy allowed an action |
| `policy_denied` | A policy denied an action |

### Device Actions

| Action | Description |
|---|---|
| `device_trusted` | A device was marked as trusted |
| `device_revoked` | A device was revoked |

### Security Actions

| Action | Description |
|---|---|
| `breach_detected` | A security breach or anomaly was detected |

### Organization Actions

| Action | Description |
|---|---|
| `organization_created` | A new organization was created |
| `organization_updated` | Organization details were updated |

### License Actions

| Action | Description |
|---|---|
| `license_issued` | A professional license was issued |
| `license_suspended` | A license was suspended |

### Bootstrap Actions

| Action | Description |
|---|---|
| `bootstrap_started` | NIAM bootstrap/seed process started |
| `bootstrap_completed` | NIAM bootstrap/seed process completed |

---

## Audit Recording

### Service Layer

The `AuditService` provides two recording methods:

```python
class AuditService:
    async def record(
        self,
        action: AuditAction,
        actor_id: str | None = None,
        actor_type: str | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
        changes: dict | None = None,
        metadata: dict | None = None,
        context: dict | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        session_id: str | None = None,
        organization_id: str | None = None,
        outcome: str = "success",
        error_message: str | None = None,
    ) -> IdentityAuditEntry: ...

    async def record_event(
        self,
        action: str,
        actor_id: str | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
        metadata: dict | None = None,
        organization_id: str | None = None,
        outcome: str = "success",
    ) -> IdentityAuditEntry: ...
```

### Usage Examples

```python
# Person created
await audit_service.record(
    action=AuditAction.person_created,
    actor_id=admin_account.uuid,
    actor_type="person",
    target_type="person",
    target_id=new_person.uuid,
    metadata={"given_name": "Ali", "family_name": "Al-Mansour"},
    ip_address="192.168.1.1",
    organization_id=org.id,
)

# Failed login
await audit_service.record(
    action=AuditAction.session_started,
    actor_id=account.uuid,
    actor_type="person",
    target_type="session",
    outcome="failure",
    error_message="Invalid password",
    ip_address="192.168.1.1",
    metadata={"failed_attempts": 3},
)

# Policy denied
await audit_service.record(
    action=AuditAction.policy_denied,
    actor_id=person.uuid,
    actor_type="person",
    target_type="resource",
    target_id="lab:results:critical",
    context={
        "policy_id": "pol-night-restrict",
        "reason": "After-hours access denied",
        "time": "23:15",
    },
    outcome="denied",
)
```

---

## Context Capture

Every audit entry captures:

| Context field | Source | Example |
|---|---|---|
| `ip_address` | HTTP request | "192.168.1.1" |
| `user_agent` | HTTP header | "Mozilla/5.0..." |
| `session_id` | JWT/session | "550e8400-..." |
| `organization_id` | Request context | Org ULID |
| `actor_id` | Authenticated user | Account UUID |
| `actor_type` | Account type | "person", "system", "machine" |
| `outcome` | Operation result | "success", "failure", "denied" |
| `error_message` | Error details | "Account locked" |

---

## Non-Repudiation Approach

NIAM uses multiple mechanisms to ensure non-repudiation:

### 1. Complete Event Capture

Every identity-related event is recorded, regardless of outcome:
- Successful operations (audit trail of who did what)
- Failed operations (audit trail of attempts)
- Denied operations (audit trail of blocked access)

### 2. Contextual Attribution

Every entry identifies:
- **Who**: Actor (person, system, machine) via `actor_id` + `actor_type`
- **What**: Action + target
- **When**: `occurred_at` timestamp
- **Where**: IP address, user agent
- **Why**: Session ID, organization context

### 3. Immutable Storage

- Audit entries are **append-only** — records are never deleted or modified
- `IdentityAuditEntry` does not support soft delete (no `is_active` column pattern)
- The `id` ULID provides temporal ordering

### 4. Change Tracking

The `changes` JSON field captures before/after state for mutations:

```json
{
  "changes": {
    "before": {"email": "old@example.com", "phone": null},
    "after": {"email": "new@example.com", "phone": "+9647701234567"}
  }
}
```

### 5. Hash Chain Ready

The audit model is designed for future hash-chain linking (SHA-256):

```python
# Future enhancement
# Each audit entry would include:
#   previous_hash: str  # SHA-256 of previous entry
#   entry_hash: str     # SHA-256 of (previous_hash + action + actor + timestamp)
```

This would enable:
- Tamper detection (changing any entry breaks the chain)
- Merkle tree verification
- External audit verification

---

## Query Patterns

### By Action Type

```python
# Find all lockout events
entries = db.query(IdentityAuditEntry).filter(
    IdentityAuditEntry.action == "account_locked"
).all()
```

### By Actor

```python
# Find all actions by a specific user
entries = db.query(IdentityAuditEntry).filter(
    IdentityAuditEntry.actor_id == user_uuid
).order_by(IdentityAuditEntry.occurred_at.desc()).all()
```

### By Target

```python
# Find all events affecting a specific entity
entries = db.query(IdentityAuditEntry).filter(
    IdentityAuditEntry.target_id == person_uuid
).all()
```

### By Time Range

```python
# Get events in a time window
entries = db.query(IdentityAuditEntry).filter(
    IdentityAuditEntry.occurred_at >= start_time,
    IdentityAuditEntry.occurred_at <= end_time,
).all()
```

### Failure Analysis

```python
# Find all failed operations
failed_entries = db.query(IdentityAuditEntry).filter(
    IdentityAuditEntry.outcome != "success"
).all()
```

---

## Audit Action Categories by Security Level

| Level | Actions | Access |
|---|---|---|
| **Info** | `person_created`, `person_updated`, `session_started`, `organization_created` | General audit |
| **Warning** | `account_locked`, `session_terminated`, `identity_revoked` | Security team |
| **Critical** | `breach_detected`, `policy_denied`, `account_mfa_disabled` | Security team |
| **Admin** | `role_assigned`, `role_revoked`, `permission_granted` | Admin audit |

---

## Compliance

The NIAM audit model supports compliance with:

- **HIPAA** — Access and disclosure logging
- **Iraqi Health Data Protection Law** — Identity event tracking
- **ISO 27001** — Information security event logging (A.12.4)
- **SOC 2** — Security and availability monitoring
- **National Health Data Governance** — Full identity audit trail

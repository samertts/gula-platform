# GULA Identity Platform — Audit Model

> Generated: 2026-07-23T11:23:43.299118+00:00
> Program: PROGRAM-IDENTITY-ENTERPRISE-001

## Audit Principles

1. **Every identity operation is immutable** — No delete or update on audit records
2. **Hash-chain integrity** — Each record links to the previous via SHA-256
3. **Correlation context** — Every audit event carries request_id, user_id, lab_id
4. **Tamper evidence** — Chain breaks are detectable via recomputation

## Audit Domains

| Domain | Events | Storage | Hash-Chained |
|--------|--------|---------|-------------|
| **Authentication** | Login, logout, failed login, MFA verify | `AuditLog` (audit_service.py) | ✅ Yes |
| **Authorization** | Permission check, role assignment, delegation | `AuthorizationAudit` | ✅ (SHA-256) |
| **Identity Merge** | Auto-merge, manual merge, split, reassign | `MergeAudit` (MPI) | ✅ Yes |
| **Break Glass** | Emergency access activation/deactivation | `AuthorizationAudit` + `BreakGlassSession` | ✅ Yes |
| **Token Operations** | Token issue, refresh, revoke | `AuditLog` | ✅ Yes |
| **Role Changes** | Role assign, unassign, delegation | `AuthorizationAudit` | ✅ Yes |
| **Delegation** | Delegate, revoke delegation | `AuthorizationAudit` + `Delegation` | ✅ Yes |

## Identity Events Captured

| Event | Audit Source | Fields Captured |
|-------|-------------|-----------------|
| Login success | `login.py` | user_id, email (HMAC), timestamp, IP, user-agent |
| Login failure | `login.py` | email (HMAC), timestamp, IP, reason |
| Logout | `login.py` | user_id, timestamp, blacklisted JTI |
| Password change | `login.py` / reset flow | user_id, timestamp |
| Registration | `register.py` | email, phone, role, timestamp |
| MFA device enrolled | MFA flow | user_id, device_type, credential_id |
| MFA device removed | MFA flow | user_id, device_id |
| Token issued | `oauth2.py` | client_id, user_id, scopes, grant_type |
| Token refreshed | `oauth2.py` | client_id, user_id, old JTI revoked |
| Token revoked | `oauth2.py` | user_id, JTI |
| Role assigned | `authorization.py` | actor_id, target_user_id, role, scope |
| Role unassigned | `authorization.py` | actor_id, target_user_id, role |
| Delegation created | `authorization.py` | delegator_id, delegate_id, role, expires |
| Delegation revoked | `authorization.py` | delegator_id, delegate_id |
| Break glass activated | `authorization.py` | user_id, emergency_category, justification |
| Break glass deactivated | `authorization.py` | user_id, deactivation_time |
| Identity resolved (MPI) | `mpi/api.py` | patient_id, citizen_id, score, method |
| Identity merged (MPI) | `mpi/api.py` | source_citizen, target_citizen, merge_type |
| Authorization decision | `authorization.py` | user_id, resource, action, decision, policies |

## Audit Model Components

### AuthorizationAudit Table (227 lines in model file)

| Column | Type | Description |
|--------|------|-------------|
| `decision_id` | String (unique) | UUID for each decision |
| `user_id` | FK → User | Who performed the action |
| `user_role` | String | Role at time of action |
| `action` | String | Action performed |
| `resource_type` | String | Type of resource accessed |
| `resource_id` | String | Specific resource identifier |
| `decision` | String | allow / deny / pending |
| `policies_applied` | JSON | Policies evaluated |
| `context` | JSON | Environmental context |
| `risk_score` | Float | Calculated risk score |
| `is_emergency` | Boolean | Emergency access flag |
| `delegation_id` | FK → Delegation | If delegated |
| `created_at` | DateTime | Timestamp |

### AuthN Audit (233 lines in audit_service.py)

The `AuditLog` service captures authentication events with SHA-256 hash chain.
Each record links to the previous via `previous_hash` field.

### MPI MergeAudit (187 lines in MPI models)

The `MergeAudit` model captures every identity decision:
- `auto_merge` — Automatic merge above 0.90 threshold
- `manual_merge` — Admin-adjudicated merge
- `split` — Identity split
- `reassign` — Patient → Citizen reassignment
- `create` — New citizen creation

## Audit Integrity Verification

Every audit log entry includes `previous_hash` forming an immutable chain:

```
Block 1: hash(Block1 data + "0"*64) → SHA-256
Block 2: hash(Block2 data + Block1.hash) → SHA-256
Block 3: hash(Block3 data + Block2.hash) → SHA-256
...
```

Tampering with any block breaks all subsequent hashes, detectable via
chain recomputation.

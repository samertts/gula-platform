# P4 Non-Production Rollback Rehearsal

**Purpose:** Validate that sensitive capability rollback disables rollout without bypassing authentication, authorization, tenant isolation or audit.

**Boundary:** Non-production only. No production deployment, database mutation, or live-data operation is authorized by this runbook.

## Preconditions

The rehearsal must use an isolated database and a release artifact identified by commit SHA. The test environment must have synthetic data only, `DEMO_DATA_ISOLATION_ACK=true` where demo mode is used, and no government/provider credentials. The test operator records the starting commit, migration head, flag values, database URL class, and test dataset identifier.

## Starting state

| Control | Required rehearsal state |
|---|---|
| `GULA_CLINICAL_GATEWAY_MODE` | `OFF` unless the test explicitly starts from a non-production pilot state |
| Clinical account/organization allowlists | Empty unless the test explicitly validates pilot rollback |
| `GULA_ADAPTER_MODE_*` | `stub` |
| `PUBLIC_SELF_REGISTRATION_ENABLED` | `false` |
| National identity/OCR/NFC/biometrics/government registry | Disabled or candidate-only; no authoritative identity mutation |
| Authorization | Fully active |
| Audit | Fully active |
| Workspace and membership server enforcement | Fully active |
| Test data | Synthetic and isolated |

## Rehearsal steps

1. Record the release commit, migration head, current flag manifest, and a baseline authorization/audit test result.
2. Exercise a permitted clinical read through the canonical gateway and record the request/correlation ID, workspace context, decision and audit event.
3. Exercise a denied cross-workspace or cross-organization read and record the 403/blocked result and audit event.
4. Exercise Account Request intake and confirm it remains `PENDING_REVIEW`; do not activate an account.
5. Set the clinical gateway mode to `OFF`, clear allowlists, set all adapters to `stub`, and keep public self-registration `false` in the isolated environment.
6. Re-run the permitted clinical read and confirm a safe disabled/503 or blocked result. Confirm no legacy REST fallback is used.
7. Re-run the denied cross-scope request and confirm authorization remains enforced rather than being bypassed by rollback.
8. Re-run audit integrity and sensitive-field redaction checks. Confirm passwords, OTPs, secrets and unnecessary identifiers are absent.
9. Verify no account, Person, Identity, Membership, Workspace, Role, Permission, Entitlement or Delegation was created or escalated by rollback.
10. Verify database migration state and transaction closure in the isolated database, then restore the environment to the approved non-production state.

## Pass criteria

The rehearsal passes only when the sensitive feature is disabled, the canonical authorization path remains active, audit remains active, cross-scope denial remains effective, Account Request remains review-gated, no legacy fallback is used, and synthetic database integrity is unchanged.

## Failure handling

Any authorization bypass, missing audit event, unexpected activation, cross-scope read, secret leakage, or data mutation is a hard failure. Stop the rehearsal, preserve logs, classify the event as `REGRESSION_DETECTED`, and do not proceed toward release.

## Production boundary

A successful non-production rehearsal does not authorize production rollback or deployment. Production rollback requires explicit release-owner approval, a selected deployment SHA, read-only runtime/database/flag verification, and an auditable change record. Rollback must never be implemented by disabling authorization, audit, tenant isolation, or security gates.

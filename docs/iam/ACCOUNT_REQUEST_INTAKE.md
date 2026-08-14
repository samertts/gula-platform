# Account Request Intake Contract

## Purpose

`POST /niam/account-requests/` receives a request for human account review. It does **not** create an account, authenticate a person, activate an organization, create a workspace, assign a role, grant a permission, or establish professional or government authority.

## Request contract

The request body is deliberately minimal:

```json
{
  "email": "person@example.com",
  "phone": null,
  "display_name": "Person Example",
  "requested_account_type": "human"
}
```

The request must include an `Idempotency-Key` header with at least 16 characters. Unknown body fields are rejected. Control characters are rejected. At least one of email or phone is required. Public intake accepts `human` only; service, machine, organization, government, professional and other authority-bearing account types are not activated through this endpoint.

## State machine

```text
PENDING_REVIEW
    ├── APPROVED  (future governed reviewer action only)
    ├── REJECTED  (future governed reviewer action only)
    └── CANCELLED (future governed requester/reviewer action only)
```

The current implementation creates only `PENDING_REVIEW`. There is no public approval, rejection, cancellation, account-linking, role assignment or workspace activation endpoint in this change.

## Data protection

Contact values and display name are encrypted at rest using the existing Fernet helper and the deployment-provided `ENCRYPTION_KEY`. Blind indexes and idempotency/fingerprint values are keyed HMAC digests using deployment-provided `NID_HMAC_KEY`; plaintext contact values are not used for lookup and are not returned in the response.

The response is intentionally non-enumerating:

```json
{
  "accepted": true,
  "status": "pending_review",
  "request_id": "opaque-request-uuid",
  "message": "Your request was received for review."
}
```

A repeated idempotency key returns the same safe response. A duplicate pending contact request is suppressed and returns the same non-enumerating shape. Passwords, tokens, authorization headers, cookies, secrets, contact ciphertext, lookup digests and request fingerprints are excluded from audit metadata and generic identity serialization.

## Abuse and failure behavior

The endpoint applies the existing authentication rate limiter by client IP with a stricter five-requests-per-minute budget. Missing encryption/HMAC key material fails closed with a generic `503` response and stores no request. Invalid input returns `422` without exposing internal configuration. The direct `/niam/accounts/` creation endpoint and unscoped lock/unlock endpoints return `410` until a governed authorization surface exists.

## Operational boundary

This contract is an intake preparation surface, not public account registration. Review, identity proofing, account creation, membership, role assignment, workspace activation and external verification integrations require separate governed work with explicit permissions, audit, tests, migration review and human approval.

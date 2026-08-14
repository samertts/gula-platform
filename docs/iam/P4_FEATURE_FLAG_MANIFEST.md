# P4 Feature-Flag Manifest

**Baseline:** `origin/main` at `d736e4f166fae20e4084847c3d7d5c8fc6dfeff6`.

**Production-state rule:** Current production values are `UNVERIFIED` unless read-only environment inspection proves otherwise. Source defaults are not production evidence.

| Flag or capability | Environment | Default | Owner | Server/client | Activation condition | Rollback | Audit requirement | Current production value |
|---|---|---|---|---|---|---|---|---|
| `GULA_CLINICAL_GATEWAY_MODE` | server env | `OFF` | Clinical + Platform Security | Server-only | Approved clinical gateway release, allowlists and authorization evidence | Set `OFF`; clear allowlists | Record flag change and rollout decision | `UNVERIFIED` |
| `GULA_CLINICAL_GATEWAY_ACCOUNT_ALLOWLIST` | server env | Empty | Clinical + Platform Security | Server-only | Explicit pilot account review | Clear allowlist | Record actor, scope, reason and expiry | `UNVERIFIED` |
| `GULA_CLINICAL_GATEWAY_ORGANIZATION_ALLOWLIST` | server env | Empty | Clinical + Platform Security | Server-only | Explicit pilot organization review | Clear allowlist | Record actor, scope, reason and expiry | `UNVERIFIED` |
| `GULA_ADAPTER_MODE` | server env | `stub` | Integration Security | Server-only | Provider credentials and approved integration review | Set `stub` | Record provider, mode, owner and change reason | `UNVERIFIED` |
| `GULA_ADAPTER_MODE_NID` | server env | Inherits global | Identity Integration | Server-only | Official provider approval and credential verification | Set `stub` | Record provider and verification source | `UNVERIFIED` |
| `GULA_ADAPTER_MODE_INSURANCE` | server env | Inherits global | Integration Owner | Server-only | Provider contract and technical approval | Set `stub` | Record provider and rollout scope | `UNVERIFIED` |
| `GULA_ADAPTER_MODE_RESIDENCY` | server env | Inherits global | Identity Integration | Server-only | Official provider approval and credential verification | Set `stub` | Record provider and verification source | `UNVERIFIED` |
| `GULA_ADAPTER_MODE_CLOUDFLARE` | server env | Inherits global | Platform Owner | Server-only | Approved control-plane integration | Set `stub` | Record change and rollback event | `UNVERIFIED` |
| `PUBLIC_SELF_REGISTRATION_ENABLED` | server env | `false` | Identity Governance | Server-only | Approved onboarding policy and security review | Set `false` | Record activation and approval reference | `UNVERIFIED` |
| `DIRECT_REST_SCOPED_READS_BLOCKED` | frontend source contract | `true` | Frontend + Clinical Security | Client contract; backend remains authoritative | Must remain true while canonical gateway is required | Keep `true`; remove any legacy fallback | Frontend contract test and release evidence | Source `true`; production bundle `UNVERIFIED` |
| Account Request intake | server route/config | Review-gated | Identity Governance | Server-only | Review workflow, encryption key and rate-limit controls | Disable intake or keep `PENDING_REVIEW` only | Audit submission, review and activation decision | `UNVERIFIED` |
| OCR/camera capture | server route/device policy | Candidate-only; no authoritative activation | Identity Governance | Server/device boundary | Separate approved capture release; never grants authority | Disable route/ingress and keep candidate-only output | Audit capture and confirmation without identity mutation | `UNVERIFIED` |
| NFC identity capture | governance/device policy | `OFF` | Identity Governance | Server/device boundary | Official reader design, security review and approval | Keep `OFF` | Audit activation decision and device scope | `UNVERIFIED` |
| Biometrics | integration/device policy | `OFF` | Identity + Security Governance | Server-only | Separate biometric threat model and approval | Keep `OFF` | Audit enrollment/verification policy change | `UNVERIFIED` |
| National identity verification | adapter policy | `stub`-safe; production stub returns `503` | Identity Integration | Server-only | Official provider, credentials and governance approval | Set adapter `stub` | Record provider/source and decision | `UNVERIFIED` |
| Government registry verification | adapter policy | `stub`/`OFF` | Governance + Integration | Server-only | Official source and approval; no fabricated provider | Set `stub`/`OFF` | Record source and approval | `UNVERIFIED` |
| Nationwide organization onboarding | onboarding policy | Pending/review-gated | Organization Governance | Server-only | Formal organization verification workflow and approval | Disable activation; keep `PENDING_VERIFICATION` | Audit request, verification and activation | `UNVERIFIED` |
| MFA/passkeys enrollment | security policy | No P4 production activation claim | Security Owner | Server-only | Completed recovery, rate-limit, audit and activation review | Disable enrollment/requirement under approved runbook | Audit policy and enrollment changes | `UNVERIFIED` |

## Enforcement requirements

The browser must not be able to enable any sensitive flag, change workspace or membership status, assign roles, or activate an external identity/device integration. A source default, test result, preview deployment, or documentation entry must not be used as evidence of a production value.

## Current conclusion

The manifest is technically prepared. Production values, owners in the deployed environment, and flag-audit records remain `UNVERIFIED` until read-only environment inspection is authorized and available. This document does not activate any capability and does not authorize P5.

# Trust Authorization Runtime Status

Phase 8/9 of the "P1/P2 INTEGRATED SECURITY, RELIABILITY & ARCHITECTURE
CLOSURE" workstream. Covers every endpoint in
`app/identity/trust/routes.py` — the six `TrustFramework` endpoints
(already fixed and proven in a prior operation,
`docs/security/TRUSTFRAMEWORK_STATE_MACHINE_STATUS.md`) plus the 26
remaining endpoints across `AssuranceService`, `TrustAnchorService`,
`FederationTrustService`, `IdentityProofingService`, and
`TrustEvaluationService`.

## Endpoint classification

| Endpoint | Auth dependency | Platform Authority capability | Object scope | Service | Audit | Mutation | Classification |
|---|---|---|---|---|---|---|---|
| `POST /assurance-profiles` (`create_assurance_profile`) | router `_AUTH_REQUIRED` | `platform.trust.manage` (added) | platform-global | `AssuranceService.assign_profile` | `TRUST_ASSURANCE_PROFILE_ASSIGNED` (added) | yes | was VULNERABLE → **fixed** |
| `GET /assurance-profiles` | `_AUTH_REQUIRED` | none (read) | platform-global | `AssuranceService.list_profiles` | n/a | no | SAFE (read, engine fixed) |
| `GET /assurance-profiles/{uuid}` | `_AUTH_REQUIRED` | none (read) | platform-global | `AssuranceService.get_profile` | n/a | no | SAFE |
| `GET /assurance-profiles/identity/{id}` | `_AUTH_REQUIRED` | none (read) | platform-global | `AssuranceService.get_profiles_for_identity` | n/a | no | SAFE |
| `POST /assurance-profiles/{uuid}/revoke` | `_AUTH_REQUIRED` | `platform.trust.manage` (added) | platform-global | `AssuranceService.revoke_profile` | `TRUST_ASSURANCE_PROFILE_REVOKED` (added) | yes | was VULNERABLE → **fixed** |
| `POST /anchors` (`create_anchor`) | `_AUTH_REQUIRED` | `platform.trust.manage` (added) | platform-global | `TrustAnchorService.create_anchor` | `TRUST_ANCHOR_CREATED` (added) | yes | was VULNERABLE → **fixed** |
| `GET /anchors`, `GET /anchors/{id}`, `GET /anchors/{id}/validate` | `_AUTH_REQUIRED` | none (read) | platform-global | `TrustAnchorService` reads | n/a | no | SAFE |
| `POST /anchors/{id}/revoke` | `_AUTH_REQUIRED` | `platform.trust.manage` (added) | platform-global | `TrustAnchorService.revoke_anchor` | `TRUST_ANCHOR_REVOKED` (added) | yes | was VULNERABLE → **fixed** |
| `POST /federation` (`create_federation_trust`) | `_AUTH_REQUIRED` | `platform.trust.manage` (added) | platform-global | `FederationTrustService.create_trust` | `TRUST_FEDERATION_CREATED` (added) | yes | was VULNERABLE → **fixed** |
| `GET /federation`, `GET /federation/{id}`, `GET /federation/org/{id}` | `_AUTH_REQUIRED` | none (read) | platform-global | `FederationTrustService` reads | n/a | no | SAFE |
| `POST /federation/{id}/suspend` | `_AUTH_REQUIRED` | `platform.trust.manage` (added) | platform-global | `FederationTrustService.suspend_trust` | `TRUST_FEDERATION_SUSPENDED` (added) | yes | was VULNERABLE → **fixed** |
| `POST /federation/{id}/terminate` | `_AUTH_REQUIRED` | `platform.trust.manage` (added) | platform-global | `FederationTrustService.terminate_trust` | `TRUST_FEDERATION_TERMINATED` (added) | yes | was VULNERABLE → **fixed** |
| `POST /proofing` (`create_proofing`) | `_AUTH_REQUIRED` | `platform.trust.manage` (added) | platform-global | `IdentityProofingService.create_proofing` | `TRUST_PROOFING_CREATED` (added) | yes | was VULNERABLE → **fixed** |
| `GET /proofing`, `GET /proofing/{id}`, `GET /proofing/person/{id}` | `_AUTH_REQUIRED` | none (read) | platform-global | `IdentityProofingService` reads | n/a | no | SAFE |
| `POST /proofing/{id}/verify` | `_AUTH_REQUIRED` | `platform.trust.manage` (added) | platform-global | `IdentityProofingService.verify_proofing` | `TRUST_PROOFING_VERIFIED` (added) | yes | was VULNERABLE → **fixed** |
| `POST /proofing/{id}/reject` | `_AUTH_REQUIRED` | `platform.trust.manage` (added) | platform-global | `IdentityProofingService.reject_proofing` | `TRUST_PROOFING_REJECTED` (added) | yes | was VULNERABLE → **fixed** |
| `POST /evaluations` (`create_evaluation`) | `_AUTH_REQUIRED` | `platform.trust.manage` (added) | platform-global | `TrustEvaluationService.create_evaluation` | `TRUST_EVALUATION_CREATED` (added) | yes | was VULNERABLE → **fixed** |
| `GET /evaluations`, `GET /evaluations/{id}`, `GET /evaluations/target/{t}/{id}` | `_AUTH_REQUIRED` | none (read) | platform-global | `TrustEvaluationService` reads | n/a | no | SAFE |

**11 VULNERABLE, all 11 fixed. 15 SAFE reads (engine bug fixed, no
capability change needed — read-only). 0 DEAD, 0 INTERNAL_ONLY, 0
DUPLICATE, 0 OUT_OF_SCOPE.** No new permission was created — every
mutating operation uses the existing `platform.trust.manage` capability,
the same one already governing `TrustFramework`'s `activate_framework`.

## Object-level authorization

All 26 endpoints operate on platform-global resources — none carry an
organization/tenant dimension the way, e.g., a lab-scoped resource
would. `FederationTrust.source_org_id`/`target_org_id` reference real
organizations but the *authorization* to create/suspend/terminate a
federation trust is a platform-level administrative act (matching
`platform.trust.manage`'s existing architecture, which is explicitly
never organization-scoped — see
`docs/security/CERTIFICATE_AUTHORIZATION_RUNTIME_COMPLETION.md`'s
identical finding for the certificate cluster). No org-scope check was
added merely because two organization ids appear as data — that would
be introducing a boundary this axis was never designed to have.

## Real HTTP + PostgreSQL proof (all 11 mutating operations)

Seeded three real accounts: no-capability, wrong-capability
(`certificates_manage`), correct-capability (`trust_manage`), plus a
real expired session for the correct-capability account. Full matrix,
every operation:

| Operation | No token | Expired session | No capability | Wrong capability | Correct capability |
|---|---|---|---|---|---|
| `create_assurance_profile` | 401 | 401 | 403 | 403 | 200 |
| `revoke_assurance_profile` | 401 | 401 | 403 | 403 | 200 |
| `create_anchor` | 401 | 401 | 403 | 403 | 200 |
| `revoke_anchor` | 401 | 401 | 403 | 403 | 200 |
| `create_federation_trust` | 401 | 401 | 403 | 403 | 200 |
| `suspend_federation_trust` | 401 | 401 | 403 | 403 | 200 |
| `terminate_federation_trust` | 401 | 401 | 403 | 403 | 200 |
| `create_proofing` | 401 | 401 | 403 | 403 | 200 |
| `verify_proofing` | 401 | 401 | 403 | 403 | 200 |
| `reject_proofing` | 401 | 401 | 403 | 403 | 200 |
| `create_evaluation` | 401 | 401 | 403 | 403 | 200 |

**Fresh-session audit evidence:** all 11 event types present
(`TRUST_ASSURANCE_PROFILE_ASSIGNED/REVOKED`, `TRUST_ANCHOR_CREATED/REVOKED`,
`TRUST_FEDERATION_CREATED/SUSPENDED/TERMINATED`,
`TRUST_PROOFING_CREATED/VERIFIED/REJECTED`, `TRUST_EVALUATION_CREATED`),
every row has a non-null `uuid` and `actor_id` matching the acting
account, 17 total audit rows for the 11 successful mutations proven
(some endpoints exercised more than once across the negative-then-positive
matrix design).

## GATE C

- Every endpoint inspected: **yes** (26/26, table above).
- Every proven-vulnerable endpoint repaired using the existing capability
  model: **yes** (11/11, `platform.trust.manage`, no new permission).
- No endpoint left vulnerable "because the original estimate said ~20"
  — the real count (26) was used, not the estimate.
- Real HTTP proof for all mutating operations: **yes**.

## RESULT

**VERIFIED.**

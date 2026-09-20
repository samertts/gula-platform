# NIAM Platform Authority — Completion Pass

Extends Phase 10's Platform Authority foundation (`federation.update_provider`,
`trust.update_framework`, already VERIFIED) to the remaining six named
operations. Same four capabilities reused (`platform.federation.manage`,
`platform.trust.manage`, `platform.certificates.manage`,
`platform.governance.manage`) — no new capability, no new role, no
generic superuser, no bypass.

## Per-operation trace

| Operation | Route | Auth (pre-existing) | Platform capability (added) | Service (added) | Audit (added) | Transaction (added) | Scope |
|---|---|---|---|---|---|---|---|
| `federation.register_provider` | `POST /niam/federation/providers` | router-level `_AUTH_REQUIRED` (valid NIAM actor) — **no capability check existed** | `platform.federation.manage` | `FederationService.register_provider` | `FEDERATED_PROVIDER_REGISTERED` | `await db.commit()` | platform-global (`FederatedProvider` has no org column) |
| `trust.activate_framework` | `POST /niam/niam/trust/frameworks/{id}/activate` | same | `platform.trust.manage` | `TrustFrameworkService.activate_framework` | `TRUST_FRAMEWORK_ACTIVATED` | `await db.commit()` | platform-global |
| `trust.supersede_framework` | **no route exists** | n/a | n/a | service method present, unreachable via HTTP | n/a | n/a | **N/A — dead/unreachable code, not authorized because there is nothing to authorize** |
| `certificates.issue_certificate` | `POST /niam/certificates/issue` | same | `platform.certificates.manage` | `CertificateService.issue_certificate` | `CERTIFICATE_ISSUED` | `await db.commit()` | conditionally scoped (`organization_id` optional on `DigitalCertificate`) — platform capability authorizes regardless, matching the existing "platform" (not org-delegated) semantics of the capability itself |
| `certificates.revoke_certificate` | `POST /niam/certificates/{id}/revoke` | same | `platform.certificates.manage` | `CertificateService.revoke_certificate` | `CERTIFICATE_REVOKED` | `await db.commit()` | same as issue |
| `governance.create_authority` | `POST /niam/niam/governance/authorities` | same | `platform.governance.manage` | `GovernanceService.create_authority` | `IDENTITY_AUTHORITY_CREATED` | `await db.commit()` | platform-global (`IdentityAuthority`/`niam_gov_authorities` has no org column) |

Every one of these six operations previously had **authentication** (the
router-level `_AUTH_REQUIRED = [Depends(get_current_niam_actor)]`
dependency already required a valid logged-in NIAM account) but **zero
authorization** — any authenticated account of any role could register a
federation provider, activate a trust framework, issue or revoke a
certificate, or create a national identity authority. None of the six had
an audit trail, and none of the reachable five ever committed a
transaction (same systemic gap NIAM_LIVE_PATH_PROOF_3.md closed for
`update_provider`/`update_framework`, now closed here too for consistency).

`supersede_framework` was traced fully: a real service method exists
(`TrustFrameworkService.supersede_framework`), but no route calls it —
confirmed via `grep -rn "supersede_framework" app/identity/` (only the
service definition and one comment reference it). Per this operation's own
instruction ("if an operation requires a new architectural authority
concept, STOP... and document it instead of inventing one") — this
doesn't need a *new* concept, but adding a route where none exists is a
product decision (what HTTP contract, what request shape) outside this
pass's authority-completion scope. Documented, not fabricated.

## Incidental finding (not fixed, documented)

`app/identity/governance/routes.py` declares `prefix="/niam/governance"`,
which — mounted again under the aggregator's own `/niam` prefix — produces
the double-prefixed real path `/niam/niam/governance/...`, the same class
of bug Phase 10.6 found in `trust/routes.py` (`/niam/niam/trust/...`).
Confirmed via the real, effective HTTP path used successfully in this
pass's live proof below. Not fixed here (out of this workstream's scope,
a routing/contract concern, not an authorization one) — tracked for
Workstream 7.

## Real HTTP + PostgreSQL proof (all six operations, real disposable DB)

| Case | register_provider | activate_framework | issue_certificate | revoke_certificate | create_authority |
|---|---|---|---|---|---|
| No token | 401 | 401 | 401 | 401 | 401 |
| Wrong/missing capability | 403 | 403 | 403 | 403 | 403 |
| Correct capability | 200 | 200 | 200 | 200 | 200 |

Fresh-session evidence (separate DB session, after the requests):
```json
{
  "provider_persisted": true, "provider_status": "active",
  "framework_persisted": true, "framework_status": "active",
  "authority_persisted": true,
  "audit_event_types": ["CERTIFICATE_ISSUED", "CERTIFICATE_REVOKED",
    "FEDERATED_PROVIDER_REGISTERED", "IDENTITY_AUTHORITY_CREATED",
    "TRUST_FRAMEWORK_ACTIVATED"],
  "audit_count": 5, "audit_all_have_uuid": true, "audit_all_have_actor": true
}
```
All five reachable operations: real 401/403/200, real persisted state,
real audit entries with real UUIDs and real actor attribution — the exact
shape already proven for `update_provider`/`update_framework` in
`NIAM_LIVE_PATH_PROOF_3.md`.

## Focused tests

`backend/tests/identity/test_platform_authority_workstream1.py` (new, 11
tests, same established fake-session pattern): unauthenticated-denied,
missing-capability-denied (including a wrong-capability-still-denies
cross-check for `create_authority`), correct-capability-succeeds-with-
audit-and-commit, not-found-never-commits. All pass;
`tests/identity/` as a whole: 209 passed, 4 skipped (was 198 before this
pass).

## GATE 1

- Every targeted, HTTP-reachable operation (5 of 6) has an explicit
  authorization path: **YES**.
- No known reachable operation remains accidentally unprotected:
  **YES**, for the six named in this workstream (a broader repository-wide
  sweep is Workstream 4, not this section).
- Real runtime evidence exists for all five reachable operations: **YES**
  (table above).
- Audit and transaction behavior proven: **YES** (fresh-session evidence).
- `supersede_framework` requires a new route (a product/contract decision,
  not an authority-model one) — **documented, not invented**, per this
  workstream's own instruction.

**STATUS: VERIFIED** (5 of 6 named operations; the 6th is unreachable
dead code, correctly not authorized because nothing calls it).

## Files changed

`federation/services.py`, `federation/routes.py`, `trust/services.py`,
`trust/routes.py`, `certificates/services.py`, `certificates/routes.py`,
`governance/services.py`, `governance/routes.py`,
`tests/identity/test_platform_authority_workstream1.py` (new).
No migration. No schema change.

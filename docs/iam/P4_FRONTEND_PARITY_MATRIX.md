# P4 Frontend/Backend Parity Matrix

**Rule:** Source presence is not runtime verification. `VERIFIED` requires a real route/service/test/deployment chain. `PARTIAL` means some source/test evidence exists. `UNVERIFIED` means evidence was not independently confirmed. `NOT_BUILT` means the platform or surface was not built/tested in this execution.

| Screen or capability | Frontend route/surface | API | Backend handler/service | Permission | Workspace/org context | Audit | Tests | Deployment | Status |
|---|---|---|---|---|---|---|---|---|---|
| Account Request | NIAM onboarding/intake surface | `POST /niam/account-requests/` | Account Request endpoint/service | Review-gated; no client activation | Server-derived account context | Submission/review audit | `test_account_request_security.py` and CI | Preview evidence only for latest remediation | PARTIAL |
| Login/session | Login/auth surfaces | Auth/session/refresh routes | NIAM auth/session services | Server-authoritative session and actor | Session/workspace resolved server-side | Authentication/session events | Security regression and CI | Production version alignment unverified | PARTIAL |
| Workspace list | NIAM workspace surface | `GET /niam/workspaces` | WorkspaceService/list eligible | Actor/session required | Server-derived eligible workspaces | Workspace events where applicable | Authorization/membership suite | Production runtime unverified | PARTIAL |
| Workspace detail | NIAM workspace surface | `GET /niam/workspaces/{id}` | WorkspaceService | Actor/session required | Server-derived scope | Access/audit policy | Authorization suite | Production runtime unverified | PARTIAL |
| Workspace switch | NIAM workspace surface | `POST /niam/workspaces/{id}/switch` | WorkspaceService.switch + AuditService | Server-authoritative; no client status mutation | Account/session/workspace context | `workspace_switched` | Authorization/membership/security suite | Production runtime unverified | PARTIAL |
| Membership | NIAM membership surface | Membership API routes | Membership service | Organization/facility/workspace scope | Server-side context | Membership lifecycle events | `test_membership_phase6.py` and CI | Production runtime unverified | PARTIAL |
| Roles/permissions | NIAM roles surface | Role/permission routes | Canonical role/permission services | No self-escalation | Scope-aware | Role assignment audit | Authorization suite | Production runtime unverified | PARTIAL |
| Clinical patients | Patients workspace | `/api/v1/clinical/patients` | Clinical Gateway | `patients.read` plus backend decision | Required org/facility/workspace envelope | Gateway/audit policy | `workspaceScopedReads` tests and clinical tests | PR previews; production commit is older | PARTIAL |
| Clinical orders | Orders workspace | `/api/v1/clinical/orders` | Clinical Gateway | `orders.read` plus backend decision | Required org/facility/workspace envelope | Gateway/audit policy | `workspaceScopedReads` tests and clinical tests | PR previews; production commit is older | PARTIAL |
| Legacy clinical REST | No permitted frontend-v3 surface | `/patients`, `/lims/orders` | Legacy routes may exist | Must not be used by frontend-v3 | Not accepted as canonical context | Not accepted as canonical fallback | Contract test asserts blocked | Production bundle alignment unverified | PARTIAL |
| Audit | NIAM audit surface | Audit search/export/integrity routes | AuditService | Privileged audit permissions | Scope and actor context | Canonical audit/hash-chain design | Security audit tests | Runtime audit evidence missing | PARTIAL |
| Identity verification | NIAM verification surfaces | Verification routes | Verification services | Explicit verification permission | No automatic authority | Verification audit required | Partial identity tests | Production flag unverified | UNVERIFIED |
| OCR/camera capture | No authoritative identity UI permitted | `/id-scan/scan` | OCR/capture route | Authenticated route; confirmation required | Candidate data only | Capture audit policy requires verification | No full P4 acceptance bundle | Activation unverified | UNVERIFIED |
| National identity | No activation permitted | `/national-id/verify` | Adapter-backed route | Server-only adapter mode | No authority from user-entered ID | Verification audit required | No official integration proof | Stub/production state unverified | UNVERIFIED |
| MFA/passkeys | Security surfaces exist in source | MFA/WebAuthn routes | MFA service | Security policy | Session-bound | Security audit | No complete P4 activation bundle | Production state unverified | UNVERIFIED |
| Organization onboarding | Governance/onboarding surfaces | Registration/approval routes | Organization lifecycle service | Review/approval permissions | Organization hierarchy | Lifecycle audit | Organization tests partial | No automatic activation proof | PARTIAL |

## Frontend hard boundaries

`DIRECT_REST_SCOPED_READS_BLOCKED` is `true` in `frontend-v3`. The canonical client uses only versioned clinical gateway paths, requires a verified workspace context, maps 401/403/429/503 to safe blocked states, rejects unsupported contract versions, and rejects sensitive response fields such as `national_id`, `phone`, `lab_id`, and raw `results`.

## Mobile parity

Mobile source counts are evidence of source presence only: `mobile/android` contains 138 Kotlin files, `mobile/ios` contains 116 Swift files, and `mobile/desktop` contains 131 Dart files. No complete Android/iOS/Flutter/Desktop build, authorization parity, or deployment verification was run in this remediation batch. Mobile status therefore remains `UNVERIFIED` or `NOT_BUILT`; it must not be reported as `VERIFIED`.

# GULA Privacy and Legal Architecture

**Program:** PUBLIC-001 · **Status:** PARTIALLY VERIFIED · No code changed.

**Governing rule: CONSENT ≠ AUTHORIZATION.** A consent record is a citizen's
permission. It is not a clinical authorization decision, and nothing in a
Privacy Centre may be allowed to grant access. Authorization stays server-side
and contextual.

---

## 1. Can GULA expose a genuine Privacy Centre?

**Partially — and the honest answer is that the backend is further along than
the frontend, but it is unreachable.** Every capability below was checked
against a real endpoint and a real table, not a route name.

| Capability | Backend endpoint | Table | Reachable from the app? | Status |
|---|---|---|---|---|
| Consent — grant | `POST /niam/consents` | `niam_consents` (exists, empty) | **no** — needs a NIAM token | **BLOCKED** |
| Consent — my consents | `GET /niam/consents/me` | `niam_consents` | **no** | **BLOCKED** |
| Consent — check | `GET /niam/consents/{id}/check` | `niam_consents` | **no** | **BLOCKED** |
| Consent — withdraw | `POST /niam/consents/{id}/withdraw` | `niam_consents` | **no** | **BLOCKED** |
| Active sessions | `GET /niam/sessions/account/{id}` | `niam_sessions` | **no** | **BLOCKED** |
| Terminate a session | `POST /niam/sessions/{uuid}/terminate` | `niam_sessions` | **no** | **BLOCKED** |
| Terminate all sessions | `POST /niam/sessions/account/{id}/terminate-all` | `niam_sessions` | **no** | **BLOCKED** |
| Devices — register / trust / revoke | `/niam/devices/*` | `niam_devices` | **no** | **BLOCKED** |
| Access history | `GET /niam/audit`, `/audit/export`, `/audit/integrity` | `niam_audit_entries` + the SHA-256 hash-chained `audit_logs` | **no** | **BLOCKED** |
| Memberships (who I am, where) | `GET /niam/memberships/me` | `niam_memberships` | **no** | **BLOCKED** |
| What data GULA stores | — | — | — | **NOT STARTED** |
| Why data is used | — | — | — | **NOT STARTED** |
| Who may access it | partially derivable from `niam_role_assignments` / `niam_permissions` | exists | no | **NOT STARTED** |
| Data sharing | — | — | — | **NOT STARTED** |
| Connected applications | `/oauth2/*` exists | — | no | **NOT STARTED** |
| Data correction / access requests | — | — | — | **NOT STARTED** |
| Account controls (close, export) | — | — | — | **NOT STARTED** |

Every BLOCKED row has the same single cause: the endpoints require a NIAM
`account_uuid` token and an active `niam_sessions` row, and `POST /login` issues
neither (see `public-auth-boundary.md` §1). The Privacy Centre is not missing a
backend — it is behind the same closed door as the workspace model.

**A Privacy Centre must not be built before AUTH-002.** Building the UI first
would mean either fabricating the data or standing up a second consent path —
both forbidden. There is exactly one consent system (`niam_consents`) and it
must stay that way.

## 2. What exists on the frontend today

* `/privacy-policy` and `/terms-of-service` — `LegalPage`, four i18n sections
  each, plus a standing review-required banner.
* `/settings/accessibility` — a real accessibility centre.
* `/capabilities/healthcare-consent` — an **admin API surface**, not a citizen
  privacy control. It must not be relabelled as one.

There is **no** citizen-facing privacy UI, no access-history view, no session
list, no consent screen. Nothing fake was found: the frontend does not pretend
to offer controls it lacks. That honesty must be preserved.

## 3. Legal information architecture

| Document | State | Owner |
|---|---|---|
| Terms of Service | exists, 4 sections, review banner | legal review required |
| Privacy Policy | exists, 4 sections, review banner | legal review required |
| Health Data Policy | **NOT STARTED** | legal + clinical |
| Consent explanation (plain language) | **NOT STARTED** | legal + clinical |
| Security statement | **NOT STARTED** | platform |
| Accessibility statement | **NOT STARTED** | platform |
| Cookies | **NOT STARTED** — note the app uses httpOnly session cookies, so a statement is owed | legal |
| Third-party processing | **NOT STARTED** | legal |
| AI / data processing | **NOT STARTED** — the platform ships clinical AI modules | legal + clinical |
| Data retention | **NOT STARTED** | legal |
| Data minimisation | **NOT STARTED** | legal |
| Account controls | **NOT STARTED** | product + legal |

**No compliance claim exists in the repository and none may be added.** No
certification, audit report or regulatory assessment was found. Any statement
of conformity with a law, standard or certification requires evidence that does
not currently exist.

## 4. Real privacy assets worth surfacing once reachable

These are genuine and unusually strong, and are what a truthful Privacy Centre
would be built on:

* **An immutable audit trail.** `audit_logs` is SHA-256 hash-chained and
  append-only, enforced by the PL/pgSQL trigger `audit_logs_deny_mutation`, with
  HMAC anchor checkpoints. `GET /niam/audit/integrity` verifies the chain.
  "Who looked at my record, and proof the log was not edited" is a real
  capability, not a promise.
* **Server-authoritative authorization.** `AuthContext` fetches memberships and
  effective permissions from the server and documents them as "never a local
  authorization fallback." Consent can be displayed without ever becoming an
  access decision.
* **National ID encrypted at rest**, HMAC-signed patient-card tokens, and
  tenant isolation as a stated invariant.

## 5. Recommended sequence

| Batch | Scope | Depends on |
|---|---|---|
| **AUTH-002** | Identity bridge — prerequisite for everything below | architecture decision |
| **PRIVACY-001** | Access history + active sessions + devices, read-only, on `/niam/audit` and `/niam/sessions` | AUTH-002 |
| **PRIVACY-002** | Consent view and withdrawal on `/niam/consents`, with an explicit "this does not grant clinical access" statement | PRIVACY-001 |
| **LEGAL-001** | Security, accessibility and cookies statements — factual, no compliance claims | — (independent) |
| **LEGAL-002** | Health Data Policy, retention, AI processing, third-party processing | **legal review, not engineering** |

Nothing in PRIVACY-001 or PRIVACY-002 may create a second consent store, a
second session store, or any control whose backend does not already exist.

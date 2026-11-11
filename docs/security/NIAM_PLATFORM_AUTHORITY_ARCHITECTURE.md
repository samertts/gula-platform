# NIAM Platform Authority — Canonical Architecture

Architecture only. No source file, migration, role, permission, route,
service, model, or test was modified to produce this document. Both
findings below remain open:

- `federation/services.py::update_provider` → **VERIFIED VULNERABLE / OPEN**
- `trust/services.py::update_framework` → **VERIFIED VULNERABLE / OPEN**

Working assumption for this phase, per the directive: **GULA/NIAM SHALL
HAVE a platform-level authority model distinct from organization-scoped
RBAC.** This document designs what that model should be; it does not
implement it.

Every claim is tagged **VERIFIED** (read directly from source/migrations/
git history this pass or in Phase 7/8A), **INFERRED** (a conclusion from
VERIFIED evidence), **PROPOSED DESIGN** (this document's design content —
not yet decided or built), **UNKNOWN** (no evidence found), or **BLOCKED**
(needs a decision this document cannot make).

### A note on the ADR deliverable

Section 16 asked for `docs/adr/ADR-NIAM-PLATFORM-AUTHORITY.md`, *unless*
repository convention requires a different process. It does.
**VERIFIED**: `docs/adr/README.md` defines ADRs as sequentially numbered
(`ADR-NNN-title.md`) and requiring a Draft → Discuss → **Decide (Engineering
Lead approves or rejects)** → Record → Implement process — not a
unilaterally authored, unilaterally accepted document. **VERIFIED**: on
`origin/claude/p0-2-pharmacy-reconciliation`, `docs/adr/` already contains
`ADR-026-purpose-scoped-identity-assurance.md` through
`ADR-029-shared-metadata-for-the-mutually-referencing-bases.md`; my branch
has no ADR past `ADR-025`. Creating an `ADR-026` (or any fixed number) here
would either collide with his branch's already-claimed numbers or invent
approval this document cannot grant. Per the phase's own instruction, the
proposed ADR content is folded into §15 below instead of a separate numbered
file.

---

## 1. AUTHORITY BOUNDARY

**PROPOSED DESIGN.** Three distinct, non-overlapping authorization axes:

```
Platform Authority   ≠   Organization RBAC   ≠   Patient/Clinical Authorization
```

**Platform Authority governs** (platform-global resources — VERIFIED to have
no tenant/organization column, or, for the certificates domain, VERIFIED to
be conditionally platform-global — see the scope note below):
- Platform-global identity/security configuration: `RiskPolicy`,
  `SessionPolicy` (`adaptive_auth` — VERIFIED no `organization_id`)
- Federation configuration: `FederatedProvider` (VERIFIED no
  `organization_id`)
- Trust frameworks: `TrustFramework` (VERIFIED no `organization_id`)
- Trust anchors: `TrustAnchor` (VERIFIED no `organization_id`)
- Certificates and certificate authorities: `DigitalCertificate`,
  `CertificateAuthority` — **VERIFIED, corrected from Phase 8A's blanket
  treatment**: both have a *nullable* `organization_id`
  (`certificates/models.py:23,62`). This is a mixed-scope resource, not
  purely platform-global: a certificate issued *for* an organization
  (`organization_id` set) is arguably organization-scoped data even though
  the issuing mechanism is platform infrastructure; a certificate with no
  `organization_id` (e.g. a platform CA's own certificate) is
  unambiguously platform-global. `APIKey`, by contrast, has a *required*
  `organization_id` (`nullable=False`, `certificates/models.py:119`) — it is
  organization-scoped, not platform authority's concern at all, and is
  listed here only to mark it explicitly out of scope.
- Platform governance authorities: `IdentityAuthority` (VERIFIED no
  `organization_id`)
- Any future platform-global security/control resource matching this same
  shape (no tenant column, or tenant column optional and meaningfully
  nullable to "platform-owned")

**Platform Authority MUST NOT automatically grant** (PROPOSED DESIGN,
stated as an invariant — see §14):
- patient access, clinical access, laboratory access, pharmacy access,
  hospital operational access, organization data access, facility data
  access — **unless** a separate, independent organization-scoped
  authorization (today: `AuthorizationDecisionService` + `Membership` +
  `RolePermissionService`, per `authorization_decision.py`, VERIFIED)
  explicitly permits it. Platform Authority and organization RBAC are
  additive, never substitutive: holding platform authority answers "may
  this account administer platform infrastructure," never "may this
  account see this patient's data."

**Relationship to the existing two axes (VERIFIED distinct today):**
- **Organization RBAC** = `AuthorizationDecisionService` +
  `Membership`/`RolePermissionService` — resolves "does this account have
  a role, within this organization, with this permission" (VERIFIED,
  `authorization_decision.py:279-294`). Requires `organization_id`;
  structurally denies when absent outside `NON_ORGANIZATIONAL_READS`
  (VERIFIED, re-confirmed Phase 8A).
- **Patient/Clinical authorization** = the legacy monolith's tenant-isolated
  `lab_id`/`current_user.lab_id` model (`CLAUDE.md` security invariant #1)
  plus, per AUTH-002/AUTH-005 (VERIFIED via commit `be7d904c`, `27bd108c`),
  `ClinicalAuthorizationContextService` and the identity-evidence/assurance
  gate on citizen↔patient linkage. This is a third, independently-evolving
  mechanism, already distinct from organization RBAC in the codebase today
  (a lab is not modeled as a NIAM `Organization` membership in the parts of
  AUTH-002 read this pass) — Platform Authority must not be wired to imply
  anything about it either.

---

## 2. CANONICAL ACTOR MODEL

**VERIFIED evidence available:**
- `NiamActor(account, session)` (`workspaces.py:25-27`) is the only
  currently-resolved actor shape; it carries an `Account` and a
  `UserSession`, nothing else.
- `Account` (`app/identity/models/account.py`, referenced throughout) is the
  authenticated principal today for all NIAM authorization decisions
  (`AuthorizationRequest.subject_account_id`).
- `Person` (`app/identity/services/person_service.py`,
  `app/identity/models/...`) is a separate registry entity — demographic/
  identity data — related to but distinct from `Account`. Phase 6 already
  found `person_service.py::update_person` has no route caller at all, so
  the Account↔Person relationship's exact cardinality/role in authorization
  was not fully re-verified this pass beyond what Phase 6 established.
- `Membership` (`app/identity/models/membership.py`) is the existing
  account↔organization grant table, resolved by
  `AuthorizationDecisionService._resolve_membership`.
- No equivalent "account↔platform-authority" grant table exists (Phase 8A,
  re-confirmed here by the same grep).

**PROPOSED DESIGN — conceptual chain:**

```
Account
  ↓  (existing, VERIFIED: Account is the authenticated subject)
Identity / Person
  ↓  (existing concept, relationship to Account not fully re-verified this pass — UNKNOWN in detail)
Platform Authority Grant     ← NEW CONCEPT, does not exist today
  ↓
Platform-level permissions
```

**Should the grant be account-bound, identity-bound, person-bound,
role-bound, or assignment-bound?**

- **PROPOSED DESIGN, with reasoning, not a final choice:** **account-bound**
  is the option most consistent with how every other authorization
  mechanism in this codebase already resolves a subject.
  `AuthorizationRequest.subject_account_id` (org RBAC),
  `NiamActor.account` (session resolution), and
  `_record_admin_event`'s `actor_id` (audit) are all `Account`-keyed, not
  `Person`-keyed. A platform-authority grant keyed to anything else
  (`Person`, `Identity`) would require translating between two different
  subject spaces at every enforcement point — a new class of bug this
  design should not introduce.
- **Role-bound vs. direct grant** is **UNKNOWN as a final answer** but
  narrowed by evidence: this codebase's org-RBAC model already separates
  "role" (a named bundle of permissions) from "membership" (the grant that
  binds an account to a role within an organization) — `RolePermissionService`
  resolves `effective_permissions` from that pair. Reusing that same
  *shape* (a small platform-role catalog + a platform-membership-equivalent
  grant table), rather than raw per-permission grants, would be consistent
  with existing precedent, but this document does not treat that as decided
  — see §3's A/B/C framing, which is the same open question restated for
  permissions specifically.
- **Assignment-bound** (i.e., time-boxed, task-specific, expiring) is
  **PROPOSED DESIGN as worth keeping distinct from break-glass** (§10) but
  not otherwise evidenced as required for the steady-state grant; noted as
  a question for whoever makes the final call, not resolved here.

**Marked UNKNOWN rather than invented:** the exact Account↔Person↔Identity
cardinality and whether a platform grant should ever need to reach through
to `Person` (e.g. for a governance authority's designated human contact) —
insufficient evidence was gathered this pass to state this with confidence,
and Phase 9 explicitly asks that gaps be marked UNKNOWN rather than filled
by invention.

---

## 3. PLATFORM AUTHORITY ROLES (minimum taxonomy)

**PROPOSED DESIGN.** Least-privilege starting point — four narrow
permissions, not a hierarchy:

| Permission (proposed name, not final) | Protected resource | Protected operation | Security impact | Platform-global? | Affects auth/trust? | Elevated assurance? |
|---|---|---|---|---|---|---|
| `platform.federation.manage` | `FederatedProvider` | create/update/rotate-credentials/change-anchor/activate/suspend | Compromise lets an attacker redirect authentication flows, harvest credentials via a malicious IdP, or exfiltrate via a stolen client secret | Yes | **Yes — directly** (an IdP is an authentication trust root) | Yes (see §8) |
| `platform.trust.manage` | `TrustFramework`, `TrustAnchor` | create/update-metadata/update-assurance-policy/change-scope/activate/supersede/revoke-anchor | Compromise rewrites what the platform considers "trusted" and at what assurance level — a platform-wide policy change, not a single record edit | Yes | **Yes — directly** (assurance policy governs how identity is trusted platform-wide) | Yes (see §8) |
| `platform.certificates.manage` | `DigitalCertificate`, `CertificateAuthority`, `CertificateRevocationList` | issue/revoke/rotate | Compromise lets an attacker mint or revoke trust material | Conditional — see §1's scope note; when `organization_id` is set, this may need to compose with org RBAC too (not resolved here — flagged, not decided) | **Yes — directly** (certificates are cryptographic trust material) | Yes (see §8) |
| `platform.governance.manage` | `IdentityAuthority` | create/update/deactivate | Compromise lets an attacker fabricate or alter a governance-body record other resources (e.g. `TrustFramework.authority_id`) attribute lineage to | Yes | Indirect (governance authority attribution feeds into trust framework lineage, not directly into authentication) | Not obviously — flagged as **UNKNOWN**, not asserted either way |

**A/B/C — how these should be organized:**

**PROPOSED DESIGN, reasoning shown, not chosen for convenience:**
**Option B — grouped under a small number of platform capabilities**
(the four rows above) is the shape most consistent with evidenced
precedent, for a specific reason: `_require_policy_admin`
(`adaptive_auth/routes.py`) already treats "policy administration" as one
undifferentiated capability rather than splitting risk-policy-admin from
session-policy-admin, and the sibling-service evidence (Phase 8A §5) shows
domain boundaries drawn at the *service* level (federation vs. trust vs.
certificates vs. governance), not at the individual-operation level. Four
domain-scoped capabilities mirrors that existing service boundary
one-to-one.

**Why not A (independent permission per operation)?** Nothing in the
evidence shows operation-level granularity is needed yet — Option A is
not ruled out, but adopting it now would be inventing granularity ahead of
a demonstrated need, which the directive asks this document to avoid
("do not choose based on convenience alone" cuts both ways — it also means
not over-engineering without evidence).

**Why not further-collapsed (one single `platform.admin` capability)?**
The four domains have materially different blast radii and different
plausible operators in practice (a certificate-authority operator is not
necessarily who should administer federation IdPs) — collapsing them
would re-create exactly the "admin' generically as sufficient evidence"
anti-pattern the directive explicitly warns against.

This grouping (Option B) is **PROPOSED, not decided** — the actual choice
among A/B/C, like the actor-grant shape in §2, is part of what
implementation-phase sign-off (§13) would need to confirm, not something
this document treats as settled.

---

## 4. RESOURCE AUTHORITY MATRIX

| Resource | Scope | Canonical owner (resource ownership) | Platform authority required | Org RBAC required? | Sensitive fields | Immutable fields | Lifecycle operations | Generic update allowed? | Audit requirement | Concurrency requirement | Emergency containment behavior |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `FederatedProvider` | Platform-global (VERIFIED, no org column) | Undetermined — no resource-ownership record exists today (Phase 8A §1.2); this document does not assign one | `platform.federation.manage` (proposed) | No | `client_secret_encrypted`, `certificate`, `trust_anchor_id`, `status`, endpoints/`redirect_uris` | `provider_id`, `uuid` | activate / suspend / deactivate (proposed — none exist today) | **No** (proposed — currently yes, this is the open vulnerability) | Every mutation, field-level before/after for sensitive fields (see §9) | None today (VERIFIED — `IdentityBaseEntity` has no version column); not proposed to add one here (out of scope, would be a schema change) | Route-level fail-closed stub until platform authority exists (Option D, §8B of the decision gate — not enabled by this document) |
| `TrustFramework` | Platform-global (VERIFIED) | `IdentityAuthority` via `authority_id` is descriptive only (VERIFIED, Phase 8A §2.2) — not an owner in the authorization sense | `platform.trust.manage` (proposed) | No | `status`, `assurance_policies`, `scope`, `authority_id`, `supersedes_framework_id` | `framework_id`, `uuid` | activate (**exists**, `activate_framework`) / supersede (**exists**, `supersede_framework`) — both currently unauthorized | **No** (proposed — currently yes) | Same as above | None today (same basis) | Same containment posture as `FederatedProvider` |
| `TrustAnchor` | Platform-global (VERIFIED, no org column) | Undetermined, same as `FederatedProvider` | `platform.trust.manage` (proposed — grouped with `TrustFramework` since both are "trust" domain per §3) | No | `certificate_chain`, `public_key_hash`, `status`, `signed_by` (chain-of-trust lineage) | `anchor_id`, `uuid` | revoke (**exists**, `revoke_anchor`) — no generic update exists at all (VERIFIED, Phase 8A §5) | **N/A — already true today**, no generic update method exists for this entity | Same pattern as above; not currently audited (VERIFIED — no audit calls in `trust/services.py`) | Same (no version column) | Not a Phase 6 finding; not proposed for containment here, but shares the same missing-authorization gap |
| `Certificate` (`DigitalCertificate`) | **Mixed** — organization-scoped when `organization_id` is set, platform-global when it is null (VERIFIED, `certificates/models.py:23`) | The organization, when set; otherwise undetermined | `platform.certificates.manage` (proposed); **composition with org RBAC when `organization_id` is set is UNKNOWN** — not resolved by this document | **Conditional — UNKNOWN**, flagged rather than guessed | `private_key_encrypted`, `certificate_pem`, `public_key`, `thumbprint` | `certificate_id`, `serial_number`, `thumbprint` | issue (exists) / revoke (exists) / **rotate (exists — `rotate_certificate`, strong existing precedent for §6)** | No generic update method exists at all today (VERIFIED) | Not currently audited (VERIFIED, no audit calls found in `certificates/services.py` in this pass — not exhaustively re-checked, treat as INFERRED from the same absence pattern seen elsewhere) | Same (no version column on `IdentityBaseEntity`) | Not a Phase 6 finding |
| `IdentityAuthority` (Governance Authority) | Platform-global (VERIFIED, no org column) | Self-owned / apex — nothing above it in this hierarchy today | `platform.governance.manage` (proposed) | No | `status`, `parent_authority_id`, `accredited_by` | `authority_id`, `uuid` | None exist today beyond create (VERIFIED — no `deactivate`/`suspend` method found in this pass) | Not applicable — no generic update method was located for this entity in this pass (UNKNOWN whether one exists elsewhere; not found in `governance/routes.py`'s first 60 lines read) | Same absent-audit pattern | Same (no version column) | Not a Phase 6 finding |

**RESOURCE OWNERSHIP vs. ACTOR AUTHORITY — the distinction this matrix
draws explicitly:** "Canonical owner" above answers *whose record is this*
(today: largely undetermined, because these are platform-global resources
with no owning organization). "Platform authority required" answers *who
may act on it regardless of ownership*. These are different questions with
different answers in every row — none of these resources has a
resource-level owner in the way a `Hospital` row is owned by a `lab_id`;
what they need is actor authority, not ownership resolution. Conflating the
two is exactly the mistake `AuthorizationDecisionService`'s membership
model would make if force-applied here (it resolves ownership-style
membership, which doesn't exist for these resources), which is *why* it
fails closed for them today (Phase 8A §3, re-confirmed).

---

## 5. FIELD-LEVEL SECURITY MODEL

Four categories (as directed), applied to the four named resource
families. This restates and slightly extends Phase 8A §4's per-resource
matrices — see that document for the full field-by-field basis; only new
material (Certificate, TrustAnchor's specific fields) is elaborated fresh
here.

**FederatedProvider**
- SAFE_METADATA: `name_en`, `name_ar`, `provider_type`, `client_id`,
  `scopes`, `metadata_url` — **UNKNOWN/plausibly-safe**, not asserted safe
  without a requirements review (unchanged from Phase 8A).
- SECURITY_SENSITIVE: `client_secret_encrypted`, `certificate`,
  `signature_algorithm`, `trust_anchor_id`, `status`, `issuer_url`,
  `authorization_endpoint`, `token_endpoint`, `jwks_uri`,
  `userinfo_endpoint`, `redirect_uris`.
- SERVER_DERIVED: `id`, `created_at`, `updated_at`, `last_sync_at`.
- IMMUTABLE: `provider_id`, `uuid`.

**TrustFramework**
- SAFE_METADATA: `name_en`, `name_ar`, `version`, `effective_date` —
  same UNKNOWN caveat.
- SECURITY_SENSITIVE: `status`, `assurance_policies`, `scope`,
  `authority_id`, `supersedes_framework_id`.
- SERVER_DERIVED: `id`, `created_at`, `updated_at`.
- IMMUTABLE: `framework_id`, `uuid`.

**TrustAnchor** (new this document — not covered field-by-field in Phase 7/8A)
- SAFE_METADATA: `name`, `anchor_type` — UNKNOWN/plausibly-safe.
- SECURITY_SENSITIVE: `public_key_hash`, `certificate_chain`, `issuer`,
  `subject`, `status`, `signed_by`, `valid_from`/`valid_to`, `revoked_at`,
  `revocation_reason` — an anchor's entire reason to exist is cryptographic
  trust material and its lineage; nearly every field is sensitive.
- SERVER_DERIVED: `id`, `created_at`, `updated_at`.
- IMMUTABLE: `anchor_id`, `uuid`.
- Note: no generic update path exists for this entity today (§4) — this
  category breakdown is offered for completeness/future-proofing, not
  because a vulnerable generic update needs closing here.

**Certificate (`DigitalCertificate`)**
- SAFE_METADATA: none confidently — even `subject`/`issuer` (requested by
  name in the directive) identify what the certificate asserts and are
  arguably SECURITY_SENSITIVE, not safe metadata, since altering either
  post-issuance would misrepresent what was actually issued.
- SECURITY_SENSITIVE: `subject`, `issuer`, `public_key`,
  `private_key_encrypted`, `certificate_pem`, `certificate_chain`,
  `thumbprint`, `status`, `revoked_at`, `revocation_reason`,
  `issuer_ca_id`.
- SERVER_DERIVED: `id`, `issued_at`, `last_rotated_at`, `created_at`,
  `updated_at`.
- IMMUTABLE: `certificate_id`, `serial_number`, `thumbprint` (thumbprint is
  listed twice deliberately: it is both a derived cryptographic fingerprint
  of the material — SERVER_DERIVED in the sense that it's computed, not
  chosen — and IMMUTABLE in the sense that changing it post-issuance while
  keeping the same `certificate_id` would misrepresent which material this
  record actually attests to. Whichever single category this collapses to
  is a detail for implementation, not decided here.)

**Invariant this section establishes (restated formally in §14):** no
security-sensitive field, in any of the four families, should remain
reachable through an unrestricted generic update operation once this
architecture is implemented.

---

## 6. DOMAIN OPERATIONS (boundaries, not implementations)

Per-family operation boundaries, using existing sibling precedent
(Phase 8A §5) wherever it exists, and marking where none exists yet:

**FederatedProvider** (conceptual — none of these except the vulnerable
generic path exist today):
- `update_metadata` — SAFE_METADATA fields only.
- `rotate_credentials` — `client_secret_encrypted`, `certificate`,
  `signature_algorithm`. Precedent: `CertificateService.rotate_certificate`
  already exists as a dedicated operation in the sibling `certificates`
  domain (VERIFIED, `certificates/services.py:132`) — strong evidence this
  boundary is not novel, just not yet applied here.
- `change_trust_anchor` — `trust_anchor_id` only. Precedent:
  `TrustAnchor` itself has no generic update, only `create`/`revoke`
  (VERIFIED) — reassigning which anchor a provider trusts is a comparably
  significant act and warrants the same isolation.
- `activate` / `suspend` / `deactivate` — `status` only. Precedent:
  `TrustFrameworkService.activate_framework` (VERIFIED, dedicated) and
  `FederationTrustService`/`CrossOrgTrustService`'s `suspend_trust`/
  `terminate_trust` (VERIFIED, dedicated, no generic alternative exists).

**TrustFramework** (two of these already exist and are named identically
to what would be kept):
- `update_metadata` — SAFE_METADATA fields only (does not exist today;
  today's `update_framework` conflates this with everything else).
- `update_assurance_policy` — `assurance_policies` only.
- `change_scope` — `scope` only.
- `activate` — **already exists** (`activate_framework`) — proposal is to
  keep it, not replace it, and to finally authorize it.
- `supersede` — **already exists** (`supersede_framework`) — same.
- `suspend`/`deactivate` — does not exist today; `TrustFramework.is_active`
  exists on the model but no dedicated method sets it (only the generic
  loop could, today, insecurely).

Splitting `assurance_policies` and `scope` into their own operations (rather
than folding them into a single "everything sensitive" bucket) reflects
that these are conceptually different decisions — a scope change redefines
*what a framework applies to*; an assurance-policy change redefines *what
level of proof it demands* — made plausibly by different reviewers even if
the same permission (`platform.trust.manage`, §3) gates both today. This is
offered as a design boundary, not asserted as requiring different
permissions — that split is not evidenced and is left as a future
refinement, not invented here.

**Do NOT assume these exact names must be implemented** — restated per the
directive; the boundaries (which fields group together, which precedent
supports each grouping) are the actual content of this section.

---

## 7. AUTHORIZATION FLOW

**PROPOSED DESIGN**, fail-closed at every step:

```
request
  ↓
authenticated NIAM identity/session         (existing: get_current_niam_actor — VERIFIED)
  ↓
platform-authority resolution                (NEW — does not exist; must fail closed if
  ↓                                           the grant lookup itself errors or is ambiguous)
required platform permission check           (NEW — e.g. platform.federation.manage;
  ↓                                           unknown/missing permission → deny, never allow)
resource type check                          (does the requested resource type fall under
  ↓                                           platform authority at all, per §4's matrix —
  ↓                                           a resource NOT in the registry, §12, must not
  ↓                                           silently default to "no authority needed")
field/operation policy                       (§5/§6 — which operation, which fields;
  ↓                                           an operation touching a SECURITY_SENSITIVE
  ↓                                           field outside its designated narrow operation
  ↓                                           is rejected, not silently narrowed)
security/assurance requirement               (§8 — some operations need stronger proof
  ↓                                           than "holds the permission"; missing/
  ↓                                           unresolvable assurance → deny)
concurrency validation if required           (§4 — none of these resources have it today;
  ↓                                           if added later, a failed check blocks the
  ↓                                           write, never silently proceeds)
mutation
  ↓
audit event                                  (§9 — if the audit write itself fails, the
                                              mutation must not be treated as successful;
                                              this mirrors AUTH-005's own
                                              `reason_code=AUDIT_FAILURE` enum value,
                                              VERIFIED present in
                                              `authorization_decision.py:57`, which already
                                              treats audit failure as a first-class deny
                                              reason for the *existing* org-RBAC path —
                                              the same posture should carry over)
```

**Authentication alone MUST NOT authorize platform-global mutation** — this
is precisely today's vulnerability in both `update_provider` and
`update_framework` (authentication via `_AUTH_REQUIRED` is the *only* check
present) and is restated here as the flow's first structural fix point,
not yet applied to source.

---

## 8. ASSURANCE REQUIREMENTS

**VERIFIED — existing NIAM assurance vocabulary**, reused here rather than
inventing new levels: `IAL1-4`, `AAL1-3`, `FAL1-3` (`trust/models.py:7-18`),
scored per-purpose by `AssuranceEngine`/`VerificationPolicy` per AUTH-004
(`6a8c5c42` — "Assurance is now a profile — one level per purpose, no
combined number... require the purpose as a required argument"). AUTH-004's
purposes, as documented in that commit, are contact/identity/professional/
organization — **none of which is "platform administration."**

**INFERRED, not invented:** AUTH-004's own design principle — "a call that
omits [the purpose] raises `TypeError` ... rather than answering a
different question from the one the caller believed it asked" — means
platform-authority operations should **not** silently borrow one of the
four existing purposes (e.g. reusing "professional" assurance for
"rotate a federation IdP's client secret" would repeat exactly the mistake
AUTH-004 fixed: answering a different question than the one being asked).

**The gap, stated rather than filled:** whether high-risk operations
(credential rotation, trust-anchor change, certificate replacement,
assurance-policy change, trust-framework lifecycle transition — the five
named in the directive) require an assurance check at all, and if so under
which purpose, is **BLOCKED**: the current model has no "platform
administration" purpose, and AUTH-004's design explicitly resists adding a
fifth purpose casually (each purpose maps to a specific, well-understood
kind of proof — contact, identity, professional license, organization
registry — and "I am authorized to administer the platform" is not
obviously any of those, nor obviously reducible to them). **This document
does not invent a fifth purpose.** What can be said without inventing
anything: `AuthorizationRequest` already has a `required_assurance` field
and `AuthorizationDecisionValue`/`AuthorizationReason.step_up_required`
machinery (VERIFIED, `authorization_decision.py:51,229-232,273-277`) tied
to `session.mfa_used` — i.e., the *mechanism* for "this operation needs
stronger proof than a valid session" already exists in the codebase
(currently keyed to MFA-used, not to IAL/AAL/FAL purpose scoring). Reusing
*that* mechanism (require `session.mfa_used` for the five named high-risk
operations) is a smaller, less invasive claim than inventing a purpose, and
is offered as the more evidenced of the two paths — but is still a
decision, not something this document resolves on its own authority.

---

## 9. AUDIT MODEL

**PROPOSED DESIGN**, built on the existing NIAM audit mechanism
(`AuditService`/`AuditEventInput`, VERIFIED via `admin/services.py`'s
`_record_admin_event` — Phase 7 §5, re-confirmed, not re-litigated):

Minimum fields per platform-authority mutation event:
- actor identity — `account.id`/`account.uuid` (existing `NiamActor`
  shape)
- platform authority — which capability was checked (e.g.
  `platform.federation.manage`), so a reviewer can see *which* grant
  authorized the action, not just that some grant did
- permission/capability — the specific operation-level permission if §3
  Option A/B is later resolved toward finer granularity
- resource type — e.g. `"federated_provider"`, matching how these
  resources are already addressed in their own route files (business key,
  not internal `id` — Phase 7 §5, restated)
- resource ID — `provider_id`/`framework_id`/`anchor_id`/`certificate_id`
- operation — which of §6's narrow operations (`rotate_credentials`,
  `change_trust_anchor`, etc.), not merely "update"
- timestamp — existing `AuditEventInput` behavior
- tenant/org context — `None` for the unambiguously platform-global
  resources; the organization, when `Certificate.organization_id` is set
  (§1/§4's scope nuance)
- security-sensitive field indication — **which** fields changed, not
  their values, for anything classified SECURITY_SENSITIVE in §5
- result — success/denied, and if denied, the reason (mirroring
  `AuthorizationReason`'s existing enum pattern, VERIFIED,
  `authorization_decision.py:30-58`)
- correlation/request ID — VERIFIED this already exists platform-wide via
  `RequestIDMiddleware` (`CLAUDE.md`'s documented middleware stack) —
  should be threaded into the platform-authority audit event the same way,
  not reinvented

**Before/after values:** appropriate for SAFE_METADATA and non-secret
SECURITY_SENSITIVE fields (e.g. `status`, `scope`, `trust_anchor_id` — a
reference id, not a secret) so a reviewer can see exactly what changed.
**NEVER for secret/cryptographic material** — restated as a hard rule
below.

**PROPOSED INVARIANT:** `client_secret_encrypted`, `private_key_encrypted`,
`certificate_pem`/`certificate_chain`/`public_key`, and any other field
matching `IdentityBaseEntity`'s own existing
`_is_sensitive_column`/`_SENSITIVE_SERIALIZATION_TERMS` redaction set
(VERIFIED, `base.py:19-35` — already redacts `password`, `token`, `secret`,
`credential`, `private_key`, `encrypted`, `lookup`, `fingerprint` in
`to_dict()`) must **never** appear in audit before/after evidence in
plaintext. The audit event should record *that* such a field changed
(boolean/field-name), reusing this exact existing redaction logic rather
than inventing a second one — the mechanism to avoid duplicating it already
lives in `base.py`.

---

## 10. BREAK-GLASS / EMERGENCY CONTROL (conceptual boundary only)

**PROPOSED DESIGN**, explicitly not implemented:

- **Should it exist at all?** Plausibly yes, for the narrow case of a
  platform-authority holder being unavailable during an active federation/
  trust incident (e.g. a compromised IdP needs `status` flipped to
  suspended immediately). **Not evidenced as required** — no incident
  runbook or existing break-glass mechanism for this specific domain was
  found in this pass; the existing `AuthorizationRequest.break_glass`/
  `break_glass_authorized` fields (VERIFIED,
  `authorization_decision.py:92-93,223-232`) show the *concept* already
  exists in the org-RBAC model (requiring `break_glass_reason`,
  `break_glass_expires_at`, and `session.mfa_used`), so extending it to
  platform authority would reuse an existing pattern rather than invent one
  — **if** the decision is made to have it at all.
- **Who can invoke it:** UNKNOWN — not decided by this document; plausibly
  a narrower set than ordinary platform-authority holders (e.g. reserved
  for a designated incident-response role), but no such role exists today
  to point to.
- **Stronger assurance required:** **Yes, by direct precedent** — the
  existing break-glass path already requires `session.mfa_used` (VERIFIED,
  `authorization_decision.py:228-232`); reusing that same requirement here
  is the evidenced choice, not a new invention.
- **Mandatory reason:** **Yes, by direct precedent** — existing
  `break_glass_reason` field already required (VERIFIED).
- **Audit requirements:** every break-glass invocation is itself a distinct,
  higher-visibility audit event beyond §9's baseline — the fact that
  break-glass was used at all is as important a signal as what was changed.
- **Duration / automatic expiry:** **Yes, by direct precedent** —
  `break_glass_expires_at` already exists as a required field on the
  existing mechanism (VERIFIED) — the same time-boxing should carry over,
  not be reinvented weaker.
- **Review requirements:** UNKNOWN/not evidenced — no existing post-hoc
  review workflow for break-glass usage was found in this pass; flagged as
  a gap for whoever designs this further, not filled here.
- **Explicit constraint carried forward:** break-glass is not a substitute
  for §7's normal flow and must not become the default path for routine
  platform administration — restated as an invariant in §14.

---

## 11. COMPATIBILITY

| Reference | What it established (VERIFIED from commit/source) | Compatibility with this design |
|---|---|---|
| AUTH-002 (`be7d904c`) | Identity-bridge decision (Option A); legacy↔NIAM claims bridging; `NR-035` (token identity-table ambiguity) | Orthogonal — this design sits entirely within NIAM's own actor model (`Account`/`NiamActor`), does not touch the legacy↔NIAM bridge |
| AUTH-003 (`94836afa`) | Token carries an explicit `act` discriminator ({user, lab_user}); `resolve_token_subject()` | Orthogonal — platform authority is a NIAM-side grant on top of an already-resolved `Account`, not a token-resolution concern |
| AUTH-004 (`6a8c5c42`) | Per-purpose assurance scoring (contact/identity/professional/organization); `AssuranceEngine`/`VerificationPolicy` | Directly relevant to §8 — this design deliberately does **not** invent a fifth purpose, reusing the *mechanism* (assurance requirement + step-up) rather than the *existing purposes* themselves, consistent with AUTH-004's own stated principle |
| AUTH-005 (`27bd108c`, `05291260`, `04bcc97a`, `4935bf85`) | Identity evidence gates citizen↔patient linkage; `NR-038`-`NR-044` (`/niam/trust/assurance-profiles` route hardening, async-layer break discovered) | Orthogonal resource (`IdentityAssuranceProfile`, not `TrustFramework`/`FederatedProvider`) — same `trust` package, different entity, not touched by this design; NR-044's finding (the whole async NIAM layer cannot reach the DB — `TypeError` on `await session.execute`) is a **separate, more urgent, already-recorded blocker** that would affect *any* implementation of this design too, since `update_provider`/`update_framework`/the proposed new operations are all async — this document flags that dependency rather than re-investigating it (NR-044 is Abu Ali's finding, on his branch; not independently re-verified against this branch in this pass) |
| NR-038 | Client could self-supply `ial`/`aal`/`fal`/`assessed_by` on assurance-profile creation | Same *shape* of bug as this design's two target vulnerabilities (client-controlled fields with no independent boundary) — reinforces, doesn't conflict |
| NR-043 | Deactivated-organization membership narrowing (`_requires_management_authority`-adjacent) | Orthogonal — organization-membership-specific, not applicable to platform-global resources |
| NR-044 | The entire async NIAM layer cannot reach the database (`TypeError` awaiting a sync `ChunkedIteratorResult`) | **Directly relevant and unresolved** — if true on the branch this design would eventually be implemented on, no async platform-authority check (nor the vulnerable async `update_provider`/`update_framework` themselves) can currently execute against a real database at all. This is not this design's finding to resolve; noted as a precondition an implementer must re-verify, not assumed fixed. |
| NR-046 (`810fd01a`) | An expired NIAM session still authenticated | Directly relevant to §7's first step ("authenticated NIAM identity/session") — this design's authorization flow sits *after* session validation and inherits whatever that step currently guarantees; if NR-046's fix is not on the branch this is implemented against, platform-authority checks would inherit the same session-expiry gap. Not re-verified against this branch this pass — flagged as a dependency. |
| NR-047 (`fb988f26`, `2bc51f28`) | `Organization` ORM/column mapping mismatch, fixed so an "allow" path reaches 200 | Not directly relevant to platform-global resources (no `Organization` involved for `FederatedProvider`/`TrustFramework`); relevant only for `Certificate`'s conditional org-scoped case (§1/§4), where correctness of `Organization` mapping would matter if composition with org RBAC is later resolved |
| Existing NIAM session model (`get_current_niam_actor`) | Resolves `Account`+`UserSession` from a bearer token | This design's first flow step reuses it unchanged — **no duplicate session/identity mechanism is introduced** |
| Existing assurance model | Per-purpose IAL/AAL/FAL (AUTH-004) | Reused via the step-up/MFA mechanism (§8), not duplicated or forked |
| Organization-scoped RBAC | `AuthorizationDecisionService` | Left completely untouched — this design adds a **parallel** resolution path for platform-global resources, explicitly not routed through `AuthorizationDecisionService` (which structurally cannot express it, Phase 8A §3) |

**Where the new Platform Authority layer sits:** **PROPOSED DESIGN** — as a
resolution step parallel to, not layered on top of or beneath,
`AuthorizationDecisionService`. Both consume the same
`NiamActor`/`Account` produced by the existing session layer; both would
produce the same shape of `AuthorizationDecision` (allow/deny +
reason code) so call sites and audit logging can treat them uniformly, but
they resolve independently (organization membership is never consulted for
a platform-authority decision, and vice versa) — this is what makes the
`≠` in §1's boundary diagram enforceable rather than aspirational.

---

## 12. PLATFORM-GLOBAL RESOURCE REGISTRY (conceptual)

**PROPOSED DESIGN** — schema, not implementation:

```
resource_type            e.g. "federated_provider", "trust_framework",
                          "trust_anchor", "certificate", "certificate_authority",
                          "identity_authority"
canonical_owner           per §4 — "undetermined" is a valid, honest value,
                          not a placeholder to fill in eventually with a guess
scope                     "platform_global" | "conditional(<column>)" |
                          "organization_scoped" — Certificate's mixed shape
                          (§1) needs the middle value, not a forced binary
authority_model           which of §3's platform capabilities governs it
allowed_operations         per §6's boundaries
sensitive_operations       the subset of allowed_operations gated by §8's
                          assurance requirement
audit_policy               per §9 — which fields get before/after, which are
                          redacted
assurance_requirement      per §8 — "none" is a valid, explicit value where
                          not yet decided, not an implicit default
lifecycle_model             which dedicated lifecycle operations exist
                          (e.g. activate/suspend/supersede/revoke) vs. "none
                          defined yet"
```

**Should this become documentation/ADR-only, machine-readable metadata,
runtime policy, or another mechanism?**

**PROPOSED DESIGN, not chosen for convenience — reasoning shown:**
Starting as **documentation** (this table, kept current as resources are
added) is the only option consistent with *not* implementing anything this
phase, and is a legitimate stopping point on its own — many platforms never
outgrow a documented registry. Evolving it to **machine-readable metadata**
(e.g. a small declarative table each new resource type registers against,
so the authorization flow in §7 can look up "does this resource type
require platform authority, and which capability" rather than that logic
being hand-written per route) becomes worth doing specifically *if* a
sixth or seventh platform-global resource family appears — the four found
in this pass (federation, trust/anchors, certificates, governance) already
show enough repetition (Phase 8A §5's sibling-service pattern) that
hand-writing the same check four times is a plausible, if not yet proven,
maintenance burden. **Runtime policy** (a policy engine evaluating this
registry dynamically, akin to `IdentityPolicy`/`_matching_policy` already
used by `AuthorizationDecisionService`, VERIFIED
`authorization_decision.py:18,296-302`) is the most powerful option and
has direct existing precedent to build on **if** the platform-authority
model turns out to need policy-level nuance beyond a flat
permission-per-domain check — not evidenced as necessary yet. This
document does not choose among the three; it records that all three are
viable evolutions of the same starting table, in increasing order of
investment, and that the choice should track actual growth in the number
and complexity of platform-global resources, not be front-loaded.

---

## 13. MIGRATION STRATEGY (future sequence — not executed here)

**PROPOSED DESIGN**, restating the directive's own ordering with this
document's findings folded in:

1. **Introduce authority model** — resolve §2's actor-grant shape and §3's
   A/B/C question (both currently open, not decided by this document);
   add the schema this requires (new table/column) as its own reviewed
   migration, following the existing migration policy (nullable/
   backward-compatible, idempotent guards, new revision — `CLAUDE.md`).
2. **Establish initial authorized platform operators** — **do not invent
   initial operator identities** (per the directive) — this is a
   deployment/bootstrapping decision for whoever owns production access,
   not something to seed with an assumed account.
3. **Add authorization enforcement** — wire the §7 flow into
   `update_provider`/`update_framework` (closing the two Phase 6 findings)
   and, per Phase 8A's finding that the gap is systemic, into
   `register_provider`, `activate_framework`, `supersede_framework`,
   `issue_certificate`, `revoke_certificate`, `create_authority` at the
   same time — fixing only the two named routes while leaving identical,
   already-discovered gaps open elsewhere would be inconsistent given they
   share one root cause.
4. **Separate sensitive operations** — implement §6's operation boundaries,
   retiring the generic `update_provider`/`update_framework` field-blob
   path once its narrower replacements exist.
5. **Add audit coverage** — wire §9 into every new operation, reusing
   `AuditService`/`AuditEventInput` and `base.py`'s existing sensitive-field
   redaction set.
6. **Add negative regression tests** — mirroring this session's established
   discipline (Phase 5/6): unauthorized-role-denied, allow-list/
   field-boundary-holds, audit-row-exists, and a revert→fail→restore→pass
   negative proof for each new check.
7. **Verify existing clients/contracts** — confirm nothing outside this
   codebase currently depends on `update_provider`/`update_framework`'s
   current (vulnerable) open-write behavior; NOT verified in this pass
   (out of scope — architecture only).
8. **Remove/restrict legacy generic update paths** — once step 4's
   replacements are live and step 7 confirms no live dependency on the old
   behavior, retire the generic setattr-loop path entirely rather than
   leaving it reachable-but-now-checked (a checked-but-still-generic path
   is a weaker end state than dedicated operations, per §6).

**No existing migration is modified. No initial operator identity is
invented. No step above is executed by this document.**

---

## 14. SECURITY INVARIANTS

Restated directive examples plus additions this analysis supports:

1. Authenticated ≠ authorized.
2. Organization RBAC ≠ platform authority.
3. Platform authority ≠ clinical authority.
4. Platform-global resource mutation requires explicit platform authority.
5. Security-sensitive fields cannot be changed through an unrestricted
   generic update operation.
6. Missing authority fails closed.
7. Cross-scope access fails closed (a platform-authority holder gets
   nothing from organization RBAC by virtue of that grant, and vice versa —
   restates #2/#3 as a runtime behavior, not just a taxonomy).
8. Security-sensitive mutations are audited.
9. Secrets/private cryptographic material never enter audit in plaintext —
   reuse `base.py`'s existing redaction set rather than a second one (§9).
10. Lifecycle transitions use dedicated domain operations, not a generic
    field-blob update (§6).
11. Platform authority does not imply patient-data access.
12. **(new)** A resource not present in the platform-global registry (§12)
    is never treated as requiring no authorization by default — an
    unregistered platform-global resource is a documentation gap to fix,
    not evidence it's safe to leave open (this closes the exact loophole
    that let `update_provider`/`update_framework` go unauthorized for as
    long as they did — they were never registered anywhere as needing a
    check).
13. **(new)** An audit-write failure blocks the mutation it was meant to
    record, mirroring the existing `AuthorizationReason.audit_failure`
    posture already present in `authorization_decision.py` for org RBAC —
    extended here to platform authority rather than re-invented.
14. **(new)** Break-glass is never the default or fallback path for routine
    platform administration (§10) — its existence, if built, must not
    quietly become how platform authority is normally exercised because
    the ordinary grant is inconvenient to obtain.
15. **(new)** A `Certificate`'s conditional scope (§1) is resolved
    explicitly per-record (is `organization_id` set or not), never assumed
    uniformly platform-global or uniformly organization-scoped across the
    whole resource type.

---

## 15. DOCUMENTATION

This file. Proposed ADR content (in lieu of a separately numbered
`docs/adr/` file, per the note at the top of this document):

> **Proposed ADR title:** NIAM Platform Authority — a distinct
> authorization axis for platform-global identity/security/governance
> resources, separate from organization-scoped RBAC.
> **Status:** Proposed (not Accepted — this document does not have the
> authority to accept an ADR per `docs/adr/README.md`'s own process).
> **Context:** §§1-2, restated. **Decision:** the boundary in §1, the actor
> model in §2 (with its open sub-questions marked, not resolved), the
> minimum taxonomy in §3 (Option B proposed with reasoning, not finalized).
> **Consequences:** §11's compatibility table plus §13's migration
> sequence. **Alternatives considered:** §3's A/B/C and §12's three
> registry evolutions, each with reasoning for why it wasn't simply
> assumed. When and if this content is formally accepted, it should be
> filed as the next available sequential `docs/adr/ADR-NNN-*.md` — a
> number this document deliberately does not assign, since the correct
> next number depends on reconciling with whichever branch's ADR sequence
> is canonical at merge time (§ top-of-document note).

---

## 16. NO IMPLEMENTATION (confirmation)

Confirmed for this document: no source modification, no migration, no new
DB table, no new role/permission in code, no route/service/model/test
change, no emergency 403 containment enabled, no branch switch, no merge/
rebase/cherry-pick. `git status` before writing this document was clean on
`claude/mustafa-parallel-engineering`; only this new file and the
Phase 6-8B documents already committed this session are new.

## 17. VALIDATION

- Every existing mechanism cited above (`NiamActor`, `AuthorizationDecisionService`,
  `_require_policy_admin`, `AssuranceEngine`/`VerificationPolicy`,
  `base.py`'s redaction set, `activate_framework`/`supersede_framework`,
  `TrustAnchorService`, `rotate_certificate`, `IdentityAuthority`,
  `docs/adr/README.md`'s process, and the AUTH-/NR- commits) was checked
  against current source or git history in this pass or in Phase 7/8A —
  none is asserted from memory alone.
- Checked git history for NR-046/NR-047 (full commit messages read this
  pass) in addition to the AUTH-002-005 series already read in Phase 8A;
  NR-043/NR-044 confidence is lower — NR-044's content is drawn from being
  quoted inside the AUTH-005-finalization commit body (`4935bf85`, already
  read in Phase 8A) rather than independently re-fetched this pass, and is
  flagged as such in §11 rather than presented with equal confidence to a
  directly-read commit.
- No proposed permission (§3) duplicates an existing one — checked against
  the same permission-catalog grep as Phase 8A, plus this pass's fresh read
  of `certificates/`/`governance/` route files; none had any existing
  permission_key to collide with.
- Platform authority is designed (§1, §14 invariant #11) to never imply
  organization access — enforced by keeping the two resolution paths
  structurally parallel (§11) rather than one wrapping or extending the
  other.
- All six resource families named in the directive are covered: `FederatedProvider`,
  `TrustFramework`, `TrustAnchor`, `Certificate`, `IdentityAuthority`
  (Governance Authority — the directive's fifth and sixth items are the
  same entity under two names, confirmed by reading
  `governance/models.py`/`governance/routes.py`, which has only one
  authority concept, `IdentityAuthority`).
- No implementation was accidentally modified — confirmed via the same
  `git status` check noted in §16.
- Full test suite was not run, per instruction.

---

## FINAL REPORT

**STATUS:** PARTIALLY VERIFIED
(Every factual claim about current code/history is verified or clearly
marked otherwise; the design itself is, correctly, PROPOSED — not
verifiable by definition, and several of its sub-questions are explicitly
left UNKNOWN or BLOCKED rather than resolved by assumption.)

**DESIGN DECISION:** A Platform Authority axis, structurally parallel to
(never layered on) organization-scoped RBAC and clinical authorization
(§1), resolved from `Account` via a not-yet-existing platform-authority
grant (§2, shape undecided among account/role/assignment-bound), expressed
as a small number of domain-scoped capabilities — proposed as four:
`platform.federation.manage`, `platform.trust.manage`,
`platform.certificates.manage`, `platform.governance.manage` (§3, Option B,
reasoned not assumed) — enforced through a fail-closed flow (§7) that sits
alongside, and never substitutes for, existing session/assurance/audit
mechanisms (§8/§9/§11), with sensitive lifecycle operations split from
generic field updates following precedent already present in
`TrustAnchorService`, `FederationTrustService`, `CrossOrgTrustService`, and
`CertificateService.rotate_certificate` (§5/§6).

**OPEN QUESTIONS** (genuinely unanswerable from repository evidence):
1. Should the platform-authority grant be account-bound, role-bound, or
   assignment-bound (§2)? Account-bound is the more evidenced default;
   role-vs-direct-grant is not decided.
2. Is Option A (independent per-operation permissions), B (four domain
   capabilities, proposed), or C (another model) correct (§3)?
3. Does `Certificate`'s conditional organization-scoping (§1/§4) need to
   compose platform authority with organization RBAC, and if so, how
   (AND? OR? organization-scoped takes precedence when set)?
4. Should high-risk operations require a new assurance purpose, reuse the
   existing MFA/step-up mechanism, or neither (§8)? This document leans on
   evidence toward "reuse step-up," but does not decide it.
5. Does break-glass need to exist for this domain at all, and if so, who
   may invoke it (§10)?
6. Is NR-044's "the entire async NIAM layer cannot reach the database"
   finding still true on the implementation target branch (§11) — not
   re-verified against this branch this pass, and blocking for any async
   implementation if so.

**SECURITY IMPACT (once implemented, not yet realized):** closes the
"authenticated = authorized" gap for platform-global resources across all
four families found to share it (federation, trust/anchors, certificates,
governance), not just the two named Phase 6 findings; removes the ability
for any authenticated NIAM actor to rewrite federation credentials, trust
anchors, or assurance policy; establishes an audit trail for these
mutations where none exists today; and — critically, per §14's new
invariant #12 — closes the structural loophole (no registry of
"which resources need this check") that let the two current
vulnerabilities go unauthorized without being caught by any existing
mechanism.

**IMPLEMENTATION PHASE (the exact smallest next step, after this design is
approved — not executed here):** resolve **only** §13 step 1 (introduce the
authority model: pick the actor-grant shape and the A/B/C permission
question) plus step 2 (establish initial authorized operators, without this
document inventing who) as their own reviewed migration + sign-off. Every
later step (enforcement, operation-splitting, audit wiring, tests, legacy
path removal) depends on that first decision and should not be attempted
before it lands.

**FILES:**
- Created: `docs/security/NIAM_PLATFORM_AUTHORITY_ARCHITECTURE.md` (this
  file)
- No other file created or modified. No ADR file created (§ top-of-document
  note explains why, per the directive's own fallback instruction).

**The two existing vulnerabilities are NOT fixed by this document:**
- `federation.update_provider` → **VERIFIED VULNERABLE / OPEN**
- `trust.update_framework` → **VERIFIED VULNERABLE / OPEN**

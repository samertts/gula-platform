# NIAM Platform Authority — Decision Package

Extracted from `docs/security/NIAM_PLATFORM_AUTHORITY_ARCHITECTURE.md`
(Phase 9), `docs/security/NIAM_PLATFORM_AUTHORITY_DECISION_GATE.md`
(Phase 8B), `docs/security/FEDERATION_TRUST_AUTHORIZATION_CONTRACT.md`
(Phase 7), and `docs/security/FEDERATION_TRUST_AUTHORITY_DECISION.md`
(Phase 8A). None of those four documents is rewritten here — no factual
contradiction was found in re-reading them for this pass, so nothing in
them is corrected. This document exists to isolate exactly two decisions
from everything else those four documents already cover, so that whoever
decides does not have to re-read four documents to find the two open
questions that actually block implementation.

No source code, migration, role, permission, or schema was touched to
produce this document. Both flagged vulnerabilities remain open:

- `federation/services.py::update_provider` → **VERIFIED VULNERABLE / OPEN**
- `trust/services.py::update_framework` → **VERIFIED VULNERABLE / OPEN**

No emergency containment has been authorized.

---

## CURRENT ARCHITECTURE (already established — not reopened here)

From Phase 9, restated without re-deriving:

- A Platform Authority axis is designed to sit structurally parallel to —
  never layered on, never substituting for — organization-scoped RBAC
  (`AuthorizationDecisionService`) and clinical/patient-data authorization.
  Authentication (`get_current_niam_actor`) is not, by itself, authorization
  for any of the three axes.
- Platform-global resource scope (VERIFIED, re-confirmed each pass):
  `FederatedProvider`, `TrustFramework`, `TrustAnchor`, `IdentityAuthority`
  have no `organization_id`. `DigitalCertificate`/`CertificateAuthority`
  have a *nullable* `organization_id` (conditionally scoped). `APIKey` has
  a required `organization_id` (organization-scoped, out of this design's
  reach).
- `AuthorizationDecisionService` cannot structurally authorize the
  unconditionally platform-global resources without widening
  `NON_ORGANIZATIONAL_READS` — a separate canonical-semantics question,
  not reopened here.
- Field-level security categories (SAFE_METADATA / SECURITY_SENSITIVE /
  SERVER_DERIVED / IMMUTABLE) and per-resource classifications are designed
  (Phase 9 §5) and not reopened here.
- Operation-boundary design (splitting `update_provider`/`update_framework`
  into metadata / credential-rotation / trust-anchor-change / lifecycle /
  assurance-policy / scope operations, following the precedent already in
  `TrustAnchorService`, `FederationTrustService`, `CrossOrgTrustService`,
  and `CertificateService.rotate_certificate`) is designed (Phase 9 §6) and
  not reopened here.
- The authorization flow shape (fail-closed at every step), audit-event
  shape (reusing `AuditService`/`AuditEventInput` and `base.py`'s existing
  secret-redaction set), and compatibility mapping against AUTH-002 through
  AUTH-005/NR-038/043/044/046/047 (Phase 9 §7/§9/§11) are designed and not
  reopened here.

**What none of the above settles, and what this document isolates:** *who*
can hold platform authority, expressed as *what*, in *how many* pieces.
That is the actor/grant shape and the permission model — the two decisions
below.

---

## DECISIONS REQUIRED

### Decision 1 — Actor / Grant Shape

**The question:** when the platform-authority axis is implemented, what is
the thing that is granted, and to what kind of subject?

Four options, compared without ranking (A/B/D restate Phase 9 §2's framing;
C is named there but not previously laid out side-by-side with the same
dimensions):

#### A. Account-bound grant

- **Authorization semantics:** the grant attaches directly to `Account.id`
  — the same subject key `AuthorizationRequest.subject_account_id` and
  `NiamActor.account` already use for every other authorization decision in
  this codebase (VERIFIED, `authorization_decision.py`, `workspaces.py`).
- **Lifecycle implications:** grant lifecycle (create/revoke) is a single
  row keyed to one account; no dependency on `Person`/`Identity` resolution
  at check time.
- **Audit implications:** trivial to attribute — `_record_admin_event`-style
  audit already logs `actor_id` as an account id (VERIFIED,
  `admin/services.py`), so this needs no new actor-identification logic.
- **Revocation implications:** revoking = deleting/deactivating one row;
  takes effect on the account's next check, no cascading resolution needed.
- **Relationship to NIAM session identity:** direct — `NiamActor.account`
  already is the account; no additional resolution step between "who is
  logged in" and "what platform authority do they hold."
- **Relationship to organization RBAC:** fully independent axis — an
  account's org memberships (`Membership`) are untouched by, and do not
  need to be consulted for, this grant.
- **Relationship to assurance:** none inherent — a platform-authority grant
  does not itself carry an assurance level; §8 of the architecture (not
  reopened here) separately considers whether *using* the grant for
  high-risk operations should require stepped-up assurance.
- **Migration implications:** smallest schema footprint of the four — one
  new table/column keyed to `Account.id` (e.g. a grant table with
  `account_id`, `capability`, granted-by/at, revoked-by/at).
- **Compatibility implications:** directly compatible with every existing
  authorization/audit mechanism surveyed in Phase 9 §11, since all of them
  already resolve to an account id.

#### B. Identity/person-bound grant

- **Authorization semantics:** the grant attaches to `Person` (the
  registry/demographic entity, `app/identity/services/person_service.py`)
  or an `Identity` record, rather than the login `Account`.
- **Lifecycle implications:** requires resolving `Account → Person/Identity`
  at every check (Phase 9 §2 flagged this exact mapping's cardinality as
  **UNKNOWN**, not independently re-verified this pass either) — an extra
  resolution step and an extra failure mode (what happens if the mapping is
  missing or ambiguous) not present in Option A.
- **Audit implications:** would need to record both the authenticated
  account *and* the person/identity the grant is attached to, or accept
  that audit attribution is one hop removed from the session that actually
  performed the action.
- **Revocation implications:** revoking a person-level grant revokes it for
  every account that resolves to that person, if the mapping is
  many-accounts-to-one-person (cardinality UNKNOWN, per above) — a
  potentially broader blast radius per revocation than Option A, not
  necessarily a wanted or unwanted property, just a different one.
- **Relationship to NIAM session identity:** indirect — sits one resolution
  step below `NiamActor`/`Account`.
- **Relationship to organization RBAC:** independent axis, same as A.
- **Relationship to assurance:** `IdentityAssuranceProfile` is already
  `person_id`+`identity_id`-keyed (VERIFIED, `trust/models.py`) — if a
  future decision ties platform-authority assurance requirements to a
  *person's* proven identity level rather than a *session's* MFA state,
  this option aligns with that data shape more directly than Option A does.
  This is stated as a property of the option, not a reason to choose it —
  Phase 9 §8 explicitly leaves the assurance-purpose question open.
- **Migration implications:** larger — needs the grant table plus reliance
  on (or hardening of) the Account↔Person↔Identity mapping, which Phase 9
  §2 already marked as insufficiently evidenced to build on today.
- **Compatibility implications:** weakest fit with existing mechanisms
  surveyed in Phase 9 §11, all of which resolve to `Account`, not `Person`.

#### C. Assignment-bound grant

- **Authorization semantics:** the grant is scoped to a specific,
  time-boxed task or incident rather than standing indefinitely — e.g. "you
  hold `platform.trust.manage` for this change window / this ticket."
- **Lifecycle implications:** requires an expiry mechanism and a renewal/
  re-assignment workflow; the grant is not a fire-and-forget row but has an
  active lifecycle of its own (open → active → expired/closed).
- **Audit implications:** each use of the grant should reference which
  assignment authorized it, not just that *a* grant existed — richer audit
  trail, more moving parts to get right.
- **Revocation implications:** natural expiry handles the common case;
  explicit early revocation is still needed for the incident-response case.
- **Relationship to NIAM session identity:** compatible with either A or B
  as the underlying subject — assignment-bound is an orthogonal axis (*how
  long* the grant lasts), not a replacement for *who* holds it, so this
  option is not strictly exclusive with A/B; presented here as the
  directive asked, without resolving that overlap.
- **Relationship to organization RBAC:** independent axis, same as A/B.
- **Relationship to assurance:** Phase 9 §10 already noted the existing
  `AuthorizationRequest.break_glass`/`break_glass_expires_at` machinery
  (VERIFIED) is exactly this shape (time-boxed, reason-required) for the
  *emergency* case — this option, for *standing* administration, would be
  reusing that same pattern more broadly, which is a design consideration,
  not a decision made here.
- **Migration implications:** largest of the four for full generality (an
  assignment/grant-lifecycle table, not just a grant table); could be
  approximated cheaply if piggybacked on Option A/B's table with an
  optional expiry column instead of a full workflow.
- **Compatibility implications:** compatible with the existing break-glass
  field shape (Phase 9 §10) if that pattern is deliberately reused; not
  otherwise different from A/B's compatibility profile.

#### D. Role-bound grant

- **Authorization semantics:** the grant is indirect — an account (or
  person) is assigned a named *role* (e.g. "Federation Administrator"),
  and the role, not the individual account, carries the permission set.
- **Lifecycle implications:** two lifecycles instead of one — the role
  definition's (which permissions it carries) and the assignment's (who
  holds the role) — mirroring the existing org-RBAC shape, where
  `Membership` (assignment) and a role's permission set are already
  separate concerns (VERIFIED, `RolePermissionService.effective_permissions`
  resolves through both).
- **Audit implications:** an audit event can cite the role held at time of
  action, which is arguably more legible to a reviewer than a raw
  permission string, at the cost of needing the role definition to be
  looked up too.
- **Revocation implications:** revoking one account's role assignment
  doesn't touch the role definition or other holders — same granularity as
  Option A's revocation, but reached through one more table.
- **Relationship to NIAM session identity:** compatible with Option A as
  the underlying subject (role assigned to an `Account`) — like Option C,
  this is not strictly exclusive with A, and is presented as the directive
  asked without resolving that overlap.
- **Relationship to organization RBAC:** the *shape* mirrors org-RBAC's
  existing role/permission separation, which is a point in favor of
  operator familiarity — but the grant itself would still need to be a
  platform-scoped assignment, not an organization membership, to avoid
  collapsing the very distinction (`platform authority ≠ organization RBAC`)
  Phase 9 §14 establishes as an invariant.
- **Relationship to assurance:** no inherent difference from Option A.
- **Migration implications:** two new tables (role definitions + role
  assignments) rather than one flat grant table, unless the four proposed
  capabilities (§ Decision 2 Option A) are treated as fixed enough that a
  role is just a named bundle of them defined in code rather than data —
  which shrinks this back toward Option A's footprint at the cost of
  runtime flexibility.
- **Compatibility implications:** most structurally similar to the existing
  org-RBAC pattern of any of the four options, which could ease review by
  people already familiar with that pattern, or could invite confusing the
  two axes — cuts both ways, not resolved here.

---

### Decision 2 — Permission Model

**The question:** once *something* can hold platform authority (Decision
1), how many distinct permissions/capabilities exist, and at what
granularity?

#### A. Four explicit domain permissions

`platform.federation.manage`, `platform.trust.manage`,
`platform.certificates.manage`, `platform.governance.manage` — as proposed
in Phase 9 §3, reasoned from the existing per-domain service-file boundary
(federation/ vs. trust/ vs. certificates/ vs. governance/ as separate
Python packages with separate service classes, VERIFIED).

- **Authorization semantics:** one permission gates every mutating
  operation within a domain (e.g. `platform.trust.manage` gates
  `update_framework`, `activate_framework`, `supersede_framework`, and any
  future split operations on `TrustFramework`/`TrustAnchor` alike).
- **Lifecycle implications:** four grantable units total; adding a fifth
  platform-global domain later means adding a fifth permission, not
  restructuring existing grants.
- **Audit implications:** an audit event's "platform authority" field
  (Phase 9 §9) has exactly four possible values today — simple to log,
  simple to review.
- **Revocation implications:** revoking `platform.trust.manage` from an
  account removes access to *all* trust operations at once, including ones
  of different sensitivity (e.g. `update_metadata` vs.
  `update_assurance_policy`, per Phase 9 §6's split) — coarser revocation
  granularity than Option B.
- **Relationship to NIAM session identity:** unaffected by this decision —
  determined by Decision 1.
- **Relationship to organization RBAC:** these four names deliberately
  don't collide with any existing `permission_key` value (re-checked this
  pass against the same catalog search Phase 8A/9 used — no
  `federation`/`trust`/`certificate`/`governance` platform-scoped
  permission_key exists today).
- **Relationship to assurance:** none inherent — Decision 2 doesn't itself
  decide whether any operation needs stepped-up assurance (Phase 9 §8,
  not reopened here); a domain permission and an assurance requirement
  would be two independent checks in the flow (Phase 9 §7).
- **Migration implications:** if permissions are just fixed string
  constants checked in code (not database rows), no new table is needed
  beyond Decision 1's grant table with a `capability` column holding one
  of these four strings; if they're modeled as catalog rows (mirroring
  `Permission`/`PermissionSensitivity`, VERIFIED to exist for org-RBAC),
  four new rows.
- **Compatibility implications:** matches the sibling-service separation
  Phase 8A §5 found already exists in the codebase (`TrustAnchorService`
  vs. `FederationTrustService` vs. `CrossOrgTrustService` as separate
  classes) — this option's four-way split tracks that existing structure
  one-to-one, rather than inventing a new grouping.

#### B. Smaller grouped capabilities

E.g. a single `platform.security.manage` (or two: one covering
federation+trust+certificates as "cryptographic trust material," one
covering governance authorities separately), collapsing Option A's four
into fewer.

- **Authorization semantics:** one permission gates a wider set of
  operations across domain boundaries.
- **Lifecycle implications:** fewer grantable units; a new platform-global
  domain discovered later either fits into an existing group or forces
  redefining the group's boundary (a small migration of meaning, not
  schema, if permissions are code constants).
- **Audit implications:** an audit event's "platform authority" field has
  fewer distinct values, which could make a reviewer's job *harder* (which
  specific action was this broad grant used for?) unless the audit event
  still separately records the specific operation (Phase 9 §9 already
  proposes recording the operation regardless of permission granularity, so
  this loss is partially mitigated by a decision already made elsewhere).
- **Revocation implications:** revoking the one grouped permission removes
  access to everything it covers at once — even coarser than Option A;
  there is no way to revoke, say, federation authority while keeping trust
  authority, if both are under one grouped capability.
- **Relationship to NIAM session identity:** unaffected, same as A.
- **Relationship to organization RBAC:** same non-collision property as A,
  re-checked the same way.
- **Relationship to assurance:** same independence from this decision as A.
- **Migration implications:** smallest of the two options that are backed
  by any evidence — one or two capability values instead of four.
- **Compatibility implications:** this is explicitly the shape Phase 9 §3
  reasoned *against* ("why not further-collapsed... re-create exactly the
  'admin' generically as sufficient evidence anti-pattern the directive
  explicitly warns against") — restated here as a documented consideration
  for whoever decides, not as this document overriding that reasoning;
  Phase 9 did not choose Option A over B, it only explained why it leaned
  away from full collapse. The four-domain split (Option A) and a
  two-group split (e.g. crypto-trust-material vs. governance) are both
  smaller than "operation-level" (Phase 9 §3's Option A-in-that-document,
  a different axis than this document's A/B) and larger than one universal
  admin bit; where exactly between four and one is correct is the actual
  open question this section leaves to the decider.

#### C. Another model, only if repository evidence supports it

**No repository evidence surfaced this pass, or in Phase 9, supporting a
third model beyond a domain-count spectrum between Option A (four) and
Option B (fewer/grouped).** Operation-level granularity (a distinct
permission per operation, e.g. `platform.trust.rotate_credentials`
separate from `platform.trust.update_metadata`) was considered and
explicitly not adopted as a proposal in Phase 9 §3 ("adopting it now would
be inventing granularity ahead of a demonstrated need") — it remains a
theoretically available point on the same spectrum, not a structurally
different model, so it is noted here rather than presented as a distinct
Option C. No option is added under C without evidence; this section is
intentionally left as a placeholder for one, per this phase's own
instruction ("only if repository evidence supports it").

---

## NOT YET DECISIONS (explicitly out of scope for this package)

Restated so this document is not mistaken for settling more than the two
items above:

- **Assurance purpose** (Phase 9 §8) — whether high-risk platform-authority
  operations reuse the existing MFA/step-up mechanism, need a new assurance
  purpose, or neither. Independent of both decisions above; a grant (however
  shaped) and a permission (however grouped) can each be combined with any
  answer to this question without redesigning either.
- **Break-glass** (Phase 9 §10) — whether emergency access should exist for
  this domain at all, and if so, who may invoke it. Independent of the two
  decisions above, though Decision 1's Option C (assignment-bound) shares
  its time-boxing shape with the existing break-glass fields, as noted.
- **Certificate conditional-scope composition** (Phase 9 §1/§4, Phase 8A) —
  how platform authority and organization RBAC compose (if at all) for
  `DigitalCertificate`/`CertificateAuthority` when `organization_id` is set.
  Independent of the two decisions above; whichever grant shape and
  permission model are chosen still need this composition question answered
  separately before `Certificate` operations (not part of the two named
  Phase 6 vulnerabilities) are brought under this architecture.
- **Implementation schema** (exact column names, table names, migration
  file) — a consequence of Decision 1 (and, if catalog rows are chosen for
  Decision 2, of Decision 2 too), not decided or previewed here beyond what
  each option's "migration implications" already states in general terms.
- **Initial authorized operators** — per Phase 9 §13 step 2 and the
  standing instruction not to invent operator identities, who the first
  real platform-authority holder(s) are is a deployment decision, not an
  architectural one, and is not addressed by resolving Decision 1 or 2.
- **Whether/how to extend enforcement to the other systemically-affected
  routes** (`register_provider`, `activate_framework`, `supersede_framework`,
  `issue_certificate`, `revoke_certificate`, `create_authority` — Phase 8A
  §1.2/§6) beyond the two named vulnerabilities — a scoping decision for
  the implementation phase, not this decision package.

---

## SECURITY PRESERVATION (Part C)

Explicitly restated, none altered by this document:

- Authenticated ≠ authorized.
- Platform authority ≠ organization RBAC.
- Platform authority ≠ clinical authorization.
- No platform authority automatically grants patient-data access.
- Security-sensitive lifecycle operations remain designed to be separated
  from generic update operations (Phase 9 §6) — not implemented by this
  document.
- Missing authority must fail closed (Phase 9 §7, §14 invariant #6).
- Both current vulnerabilities remain **OPEN**:
  `federation/services.py::update_provider`,
  `trust/services.py::update_framework`.
- No emergency containment has been authorized — the Option D containment
  described in `docs/security/NIAM_PLATFORM_AUTHORITY_DECISION_GATE.md` §D
  remains undecided and unimplemented.

---

## FINAL REPORT

**STATUS:** PARTIALLY VERIFIED — the current-architecture summary above is
drawn from prior VERIFIED/INFERRED findings in Phase 7-9, re-read this pass
for contradiction (none found) rather than re-derived from source; the two
decisions themselves are, correctly, undecided options, not verifiable
facts.

**AUTHORITY STATUS:** BLOCKED_PENDING_ACTOR_GRANT_AND_PERMISSION_DECISION

**NEXT ACTION:** Obtain the two decisions above — actor/grant shape
(A/B/C/D) and permission model (A/B, with C open only if new evidence
emerges) — from whoever holds authority over NIAM's canonical
identity/authorization architecture. No further code investigation
resolves either; both are genuine design choices among options this
document has deliberately left unranked.

**FILES:**
- Created: `docs/security/NIAM_PLATFORM_AUTHORITY_DECISION_PACKAGE.md`
  (this file).
- No other file created or modified. No source, migration, role,
  permission, CI workflow, or schema change was made.

**The two existing vulnerabilities are NOT fixed by this document:**
- `federation.update_provider` → **VERIFIED VULNERABLE / OPEN**
- `trust.update_framework` → **VERIFIED VULNERABLE / OPEN**

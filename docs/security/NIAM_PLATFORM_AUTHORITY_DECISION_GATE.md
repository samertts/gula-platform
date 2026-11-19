# NIAM Platform Authority — Decision Gate

This document records a single open architectural decision. It does not
make that decision, does not rank the candidate models below, and does not
modify any source file, role, permission, or schema. It builds on
`docs/security/FEDERATION_TRUST_AUTHORIZATION_CONTRACT.md` (Phase 7) and
`docs/security/FEDERATION_TRUST_AUTHORITY_DECISION.md` (Phase 8A) without
correcting either.

---

## VERIFIED EVIDENCE

(Restated from Phase 7/8A — re-derived from source in those passes, not
re-verified again here; see those documents for file/line citations.)

- `FederatedProvider` (`app/identity/federation/models.py`) is
  platform-global: no `organization_id`, `facility_id`, or tenant column.
- `TrustFramework` (`app/identity/trust/models.py`) is platform-global: no
  tenant column.
- Neither resource has an `organization_id`.
- No existing platform-level administrative authority concept was found
  anywhere in the role/permission tables (exhaustive grep, zero hits for a
  platform-admin/super-admin role or equivalent).
- `IdentityAuthority` (`app/identity/governance/models.py`, the FK target of
  `TrustFramework.authority_id`) is descriptive governance metadata — a
  record of a governance body's name, jurisdiction, and accreditation. It
  has no relationship to `Account`, `Membership`, or any grant table, so it
  is not an account→authority grant.
- No platform-admin role or permission concept exists in
  `app/identity/models/authorization.py` or the NIAM completion migration.
- Existing sibling operations in the same two service files
  (`TrustAnchorService`, `FederationTrustService`, `CrossOrgTrustService`,
  and `TrustFrameworkService.activate_framework`/`.supersede_framework`)
  use narrow, dedicated lifecycle methods rather than one unrestricted
  generic field-update method.
- `federation/services.py::update_provider` and
  `trust/services.py::update_framework` remain **VERIFIED VULNERABLE**:
  reachable by any authenticated NIAM actor, no permission check, security-
  sensitive fields (`client_secret_encrypted`, `certificate`,
  `trust_anchor_id`, `status`, `assurance_policies`, `scope`, lineage
  fields) settable via an unguarded `setattr` loop.
- The identical "no authorization dependency at all" gap exists on
  `certificates/routes.py` (`issue_certificate`, `revoke_certificate`) and
  `governance/routes.py` (`create_authority`) — the absence of a platform
  authority concept is systemic to this corner of NIAM, not isolated to
  federation/trust.
- `AuthorizationDecisionService` cannot structurally authorize either
  resource type without widening `NON_ORGANIZATIONAL_READS` — a change to
  canonical authorization semantics, not something decided by reading code.
- The final authorization model for `update_provider`/`update_framework` is
  **BLOCKED** on the platform-authority question below.

**These two vulnerabilities remain OPEN.** Nothing in this document closes,
mitigates, or reduces their severity; it only frames the decision that
would let a fix proceed.

---

## THE OPEN DECISION

> **Does NIAM require a platform-level administrative authority model,
> distinct from organization-scoped RBAC, for platform-global identity,
> federation, trust, certificate, and governance resources?**

This single question gates a correct fix for both `update_provider` and
`update_framework`, and also gates the identical latent gap already found
in `certificates/` and `governance/`. It cannot be answered from source
code, migrations, or commit history on either branch — both branches leave
it open (Phase 8A §8).

---

## DESIGN OPTIONS

Presented without ranking or recommendation. Each is described only along
the dimensions requested; no option is marked preferred, easier, or safer
than another beyond what is stated as a direct, literal consequence.

### A. Explicit platform-level administrative authority

**What it would govern:** A new, first-class authorization concept —
e.g. an explicit flag/role/claim recognized platform-wide, independent of
any organization membership — that identifies certain accounts as holding
platform authority. Would apply uniformly to every platform-global resource
(not just the two in question).

**What it would NOT govern:** Anything already organization-scoped
(memberships, org-level roles/permissions, facility/department/unit scope).
`AuthorizationDecisionService`'s existing membership-based model would be
untouched for organizational resources.

**Relationship to organization-scoped RBAC:** A parallel, separate
authorization axis. An account could hold platform authority independent of
(or in addition to) any organizational membership. Would not extend or
reuse `AuthorizationDecisionService`'s membership/permission resolution —
it would need its own check, structurally similar to (but distinct from)
`_require_policy_admin`'s current fail-closed stub, except actually granting
rather than always denying.

**Implications for FederatedProvider:** `update_provider` (and, if wanted,
`register_provider`) would gate on holding platform authority. Does not by
itself determine field-level granularity (§ separate operations, per
Phase 8A §5, remain a distinct question from who may call them).

**Implications for TrustFramework:** Same shape as federation:
`update_framework`, `activate_framework`, `supersede_framework` would each
gate on platform authority (today none of the three do).

**Implications for certificates:** `issue_certificate`/`revoke_certificate`
would also need to gate on this new concept to close the identical gap
found there — otherwise the platform ends up with two classes of
"platform-global sensitive resource," one gated and one not, for no
principled reason.

**Implications for governance authorities:** `create_authority` (and any
future authority-lifecycle operations) would also gate on it, which raises
a bootstrapping question this option must answer: who grants the *first*
platform-authority holder, and is that itself an `IdentityAuthority`-rooted
decision or independent of it.

**Migration/compatibility implications:** Requires a new column or table
(e.g. a flag on `Account`, or a new grant table) — a schema change, which
per this platform's migration policy is out of scope for this document and
would need its own reviewed migration, nullable/backward-compatible per
existing policy.

**Audit implications:** A new authority grant/revocation is itself a
security-relevant event requiring its own audit trail, in addition to
auditing the actions the authority is used to perform.

**Implementation scope:** Largest of the four options — new schema, new
grant/revocation workflow, new check wired into every platform-global
route across four+ modules (federation, trust, certificates, governance,
and previously adaptive_auth's already-stubbed routes).

---

### B. Extend/reuse an existing NIAM authority concept

**What it would govern:** Repurposing `IdentityAuthority`
(`niam_gov_authorities`) itself — or some other already-modeled entity — as
the authorization anchor, by adding the missing account→authority mapping
that Phase 8A found does not currently exist, rather than introducing a
wholly new concept.

**What it would NOT govern:** Anything where "which authority does this
account represent" is not a meaningful question — e.g. it is unclear under
this option how a citizen-facing or lab-facing account would ever relate to
a governance authority at all, so this option may not naturally extend to
every platform-global resource (see certificates/federation caveats below).

**Relationship to organization-scoped RBAC:** Would sit alongside it as a
second resolution path (account → authority, rather than account →
organization → membership), reusing `IdentityAuthority`'s existing
hierarchy (`parent_authority_id`, `jurisdiction`) rather than building a
new one.

**Implications for FederatedProvider:** Would require deciding whether
`FederatedProvider` should gain its own `authority_id` (it has none today —
unlike `TrustFramework`, which already has one) to make this option
applicable at all. Without that, this option has no natural anchor point
for federation providers specifically.

**Implications for TrustFramework:** More directly applicable than for
federation, since `authority_id` already exists on the model — but Phase 8A
already found no account↔authority grant mapping exists, so this option's
core work is building that missing mapping, not merely "using what's
there."

**Implications for certificates:** `CertificateService`
(`certificates/routes.py`) has no `authority_id`-equivalent field noted in
this pass — same gap as FederatedProvider; would need its own extension or
be left out of this option's coverage.

**Implications for governance authorities:** Circular by construction:
`create_authority` creates the very entities this option would use as the
authorization anchor. Requires deciding who may create/modify an
`IdentityAuthority` in the first place, independent of who may use one to
authorize a trust-framework or provider change.

**Migration/compatibility implications:** Requires a new account→authority
mapping table (or column), and possibly a new `authority_id` column on
`FederatedProvider`/certificates — schema changes, same caveat as Option A,
though narrower in scope (extending an existing concept rather than
introducing a parallel one).

**Audit implications:** Same as Option A — granting/revoking an
account's association with an authority is itself auditable, separately
from actions taken under that authority.

**Implementation scope:** Narrower than Option A for `TrustFramework`
(the FK already exists), wider than Option A for `FederatedProvider`/
certificates (a new field would be needed first). Uneven scope across the
four resource families is the defining characteristic of this option.

---

### C. Dedicated administrative/control-plane boundary

**What it would govern:** Moving platform-global administrative
operations (all of adaptive_auth's policy routes, federation, trust,
certificates, governance authorities) behind a structurally separate
surface — e.g. a distinct internal-only router/deployment boundary,
network-level restriction, or a separate service — rather than an
in-request permission check layered onto the existing public API.

**What it would NOT govern:** Anything meant to be reachable by ordinary
tenant/org-scoped users through the normal API — this option is explicitly
about narrowing *who can reach the endpoint at all*, not refining
in-application permission logic for a broadly-reachable endpoint.

**Relationship to organization-scoped RBAC:** Largely orthogonal — RBAC
would continue to govern organizational resources on the main surface;
this option adds a boundary *outside* or *beneath* that model rather than
extending it. An account might still need some in-application check too,
depending on how the boundary is implemented (e.g. network-level isolation
alone does not distinguish among different callers who do reach it).

**Implications for FederatedProvider:** `update_provider` (and
`register_provider`) would move to (or be reachable only from) the
control-plane boundary, unreachable from the primary public NIAM API
surface used by ordinary sessions.

**Implications for TrustFramework:** Same relocation for
`update_framework`/`activate_framework`/`supersede_framework`.

**Implications for certificates:** Same relocation for
`issue_certificate`/`revoke_certificate`, closing that identical gap by the
same mechanism.

**Implications for governance authorities:** Same relocation for
`create_authority` and any future authority-lifecycle operations —
notably, this option would place the entity that Option B considers using
*as* an authorization anchor behind the same boundary, which sidesteps
Option B's circularity concern rather than resolving it.

**Migration/compatibility implications:** Depends heavily on
implementation choice (separate FastAPI mount + network policy vs. a truly
separate deployable service vs. an existing internal-admin convention
elsewhere in this monorepo, if one exists — not searched for in this pass).
Could avoid a schema change entirely if implemented as a routing/network
boundary rather than a new grant model, or could still need one if paired
with any in-application check.

**Audit implications:** Access to the control-plane boundary itself
(who reached it, from where) becomes an auditable event, potentially in
addition to auditing the actions taken through it.

**Implementation scope:** Scope depends entirely on which boundary
mechanism is chosen — could range from "a new router prefix plus a network
rule" to "a new service," a wider range than Options A/B, whose scope is
comparatively bounded by "add a check to existing routes."

---

### D. Temporary fail-closed containment while the authority model is decided

**What it would govern:** Nothing new is granted access — this option
governs by refusal. The specific routes carrying the two verified
vulnerabilities (and, if extended, the identical gaps in
`register_provider`, `activate_framework`, `supersede_framework`,
`issue_certificate`, `revoke_certificate`, `create_authority`) would
unconditionally deny every caller until Options A/B/C (or another) is
chosen — the same shape of stub already in place today for
`adaptive_auth`'s `RiskPolicy`/`SessionPolicy` routes
(`_require_policy_admin`).

**What it would NOT govern:** It does not answer the platform-authority
question — it defers it. It does not restore any legitimate write
capability for these resources; any workflow that currently depends on
being able to call `update_provider`/`update_framework` (or the other
listed routes, if this option is extended to them) would stop working
until a real model (A, B, or C) is chosen and implemented.

**Relationship to organization-scoped RBAC:** None — it does not touch,
extend, or reuse the RBAC model at all. It is a placeholder, not an
authorization model.

**Implications for FederatedProvider:** `update_provider` returns 403 for
every caller. Read paths (`get_provider`, `list_providers`) and
`register_provider` are unaffected unless explicitly included in scope.

**Implications for TrustFramework:** `update_framework` returns 403 for
every caller. Read paths, `create_framework`, `activate_framework`,
`supersede_framework` unaffected unless explicitly included in scope.

**Implications for certificates:** Not required by the two named Phase 6
findings, but the identical gap exists there (Phase 8A §1.2/§6) — whether
to extend this containment to `issue_certificate`/`revoke_certificate` is
itself a scoping choice, not something this document decides.

**Implications for governance authorities:** Same caveat as certificates —
`create_authority` shares the gap but is outside the two named findings.

**Migration/compatibility implications:** None — no schema change, no new
table, no new role. Purely an application-layer dependency addition.

**Audit implications:** Minimal — a denied request can be logged as a
denial, but there is no legitimate action to produce field-level
before/after audit evidence for, since nothing is permitted to happen.

**Implementation scope:** Smallest of the four — a single new dependency
function plus wiring it onto the specific route(s) in scope. This is the
only option that does not require §THE OPEN DECISION to be answered first;
it requires only the separate, narrower agreement that refusal is
preferable to the current open-write state. It is explicitly a stopgap,
not a resolution — Options A/B/C remain the actual decision this document
is gating.

---

## Explicit constraint

**No implementation should proceed on Options A, B, or C until the
platform-authority model is selected.** The only implementation that may
proceed independently of that selection is Option D (temporary fail-closed
containment), and only once separately, explicitly authorized on its own
narrower terms — its own sign-off is not granted by this document either.

The two verified vulnerabilities
(`federation/services.py::update_provider`,
`trust/services.py::update_framework`) **remain OPEN.** This document
selects nothing, implements nothing, and reduces the severity of neither
finding.

---

## STATUS

**BLOCKED_PENDING_ARCHITECTURAL_DECISION**

## NEXT ACTION

Obtain the platform-authority architectural decision — i.e., a choice among
Options A, B, C (or an alternative not listed here), made by whoever holds
authority over NIAM's canonical identity/authorization architecture. No
further code investigation changes this: the blocking fact is the absence
of a decision, not a gap in evidence.

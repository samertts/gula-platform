# Federation / Trust-Framework Authorization Contract

Status of the two Phase 6 findings: **OPEN, UNPATCHED, TRACKED.**

1. `app/identity/federation/services.py::update_provider` (called from
   `PUT /niam/federation/providers/{id}`) — any authenticated NIAM actor can
   overwrite `client_secret_encrypted`, `certificate`, `trust_anchor_id`,
   `status`, `issuer_url`, etc. via a raw request body.
2. `app/identity/trust/services.py::update_framework` (called from
   `PUT /niam/trust/frameworks/{id}`) — any authenticated NIAM actor can
   overwrite `status`, `assurance_policies`, `scope`, `authority_id`,
   `supersedes_framework_id` via a raw request body.

This document is investigation-only, per Phase 7's instruction: no source
file under `app/identity/` was modified to produce it. Every statement below
is tagged **VERIFIED** (read directly from the cited file/line on this
branch), **INFERRED** (a reasonable conclusion from VERIFIED evidence, not
itself directly stated anywhere), **UNKNOWN** (no evidence either way was
found), or **BLOCKED** (the question cannot be answered without a canonical
decision this branch is not authorized to make).

---

## 1. Federation update authorization contract

### A. Caller identity

- **VERIFIED.** The only actor dependency in scope is
  `get_current_niam_actor` (`app/identity/api/workspaces.py:65-89`), applied
  at router-inclusion level: `router.include_router(federation_routes.router,
  dependencies=_AUTH_REQUIRED)` (`app/identity/api/router.py:49`), where
  `_AUTH_REQUIRED = [Depends(get_current_niam_actor)]`. It decodes the bearer
  token, resolves an `Account` + active `UserSession` pair, and returns a
  `NiamActor(account, session)`. It proves only "this is a live, active NIAM
  session" — it resolves no role, permission, or organization membership.
- **VERIFIED.** `update_provider`'s route handler
  (`app/identity/federation/routes.py:97-107`) adds no further
  `Depends(...)` beyond `db: AsyncSession = Depends(get_db)`. There is no
  per-route authorization check at all.
- **VERIFIED — identical on the active redesign branch.**
  `git show origin/claude/p0-2-pharmacy-reconciliation:backend/app/identity/federation/routes.py`
  shows the same handler shape (sync `Session` instead of async, otherwise
  unchanged): `body: dict[str, Any]`, `db: Session = Depends(get_db)`, no
  authorization dependency. `identity/api/router.py` on that branch also
  still mounts `federation_routes.router` with only `dependencies=_AUTH_REQUIRED`.

### B. Required authorization

- **UNKNOWN, and the codebase says so explicitly for a materially identical
  case.** No permission key, role, or "federation-admin" concept exists
  anywhere in the repository for federation-provider mutation.
  `app/identity/models/authorization.py` (`Permission`, `PermissionSensitivity`)
  and the NIAM completion migration
  (`backend/migrations/versions/20260723_0002_niam_completion_tables.py`)
  define no permission row for `federated_provider`/`trust_framework`
  resource types (VERIFIED — grepped, zero hits).
- **INFERRED, from direct precedent already in this codebase.**
  `app/identity/adaptive_auth/routes.py:15-44` documents the identical shape
  of problem for `RiskPolicy`/`SessionPolicy` (also genuinely platform-global
  resources with no `organization_id`): the existing org-scoped
  `AuthorizationDecisionService` cannot express "platform administrator" at
  all, and the file's own docstring states widening its allowlist "would be a
  change to canonical NIAM authorization semantics this branch is not
  authorized to make on its own." It resolved this by failing closed
  (`_require_policy_admin` unconditionally raises 403) rather than inventing
  a role. `FederatedProvider` has the same shape (no `organization_id` column
  — see §3below) so the same reasoning applies; see §9 for why this is
  proposed as the interim pattern, not a new invention.
- **Do NOT invent** `federation-admin`/`platform-admin` as a real role: no
  such role is declared in this codebase's role/permission tables today.

### C. Object scope

- **VERIFIED.** `FederatedProvider` (`app/identity/federation/models.py:11-47`)
  has no `organization_id`, `facility_id`, or any tenant-scoping column at
  all. It is a platform-wide singleton registry of federation IdPs, not an
  org-owned resource.
- **INFERRED.** Because there is no tenant column, "what must happen on
  cross-tenant access" does not apply to this resource — the correct
  question is platform-wide authority, not tenant isolation. This is a
  materially different shape from every other domain audited in Phase 5/6
  (Hospital, Nursing, NHDW), which are genuinely org/lab-scoped.
- **VERIFIED — server-side target resolution is already correct** in the
  narrow sense that matters here: `update_provider` looks up the row by
  `provider_id` from the path, never trusts a client-supplied primary key
  (`app/identity/federation/services.py:79-91`). The gap is authorization,
  not object-identity confusion.

### D. Field mutability (federation)

| Field | Classification | Basis |
|---|---|---|
| `client_secret_encrypted` | **SECURITY_SENSITIVE** | VERIFIED present on model; an IdP client secret. Client-writable today with no check. |
| `certificate` | **SECURITY_SENSITIVE** | VERIFIED; signing/verification trust material for the federation relationship. |
| `trust_anchor_id` | **SECURITY_SENSITIVE** | VERIFIED; changes which trust anchor is asserted to back this provider. |
| `jwks_uri`, `token_endpoint`, `authorization_endpoint`, `userinfo_endpoint`, `issuer_url` | **SECURITY_SENSITIVE** | VERIFIED; redirecting any of these to an attacker-controlled URL turns the provider into a credential-harvesting redirect. |
| `status` | **SECURITY_SENSITIVE** | VERIFIED; gates whether the provider is usable (`list_providers` filters `is_active`; `status` is read by callers not audited in this pass — treat as sensitive until proven otherwise). |
| `redirect_uris` | **SECURITY_SENSITIVE** | VERIFIED; an OAuth/OIDC redirect allow-list — the canonical open-redirect / auth-code-interception vector for this resource type. |
| `provider_id`, `uuid` | **IMMUTABLE** | VERIFIED unique identifiers; no legitimate update should change them. |
| `client_id`, `scopes`, `signature_algorithm`, `metadata_url`, `name_en`, `name_ar`, `provider_type` | **UNKNOWN** | Plausibly SAFE_MUTABLE administrative metadata, but no requirements doc defines the intended update surface — do not assume. |
| `last_sync_at`, `created_at`, `updated_at`, `id` | **SERVER_DERIVED** | VERIFIED — set by the system (sync jobs / ORM defaults), never legitimately client-supplied. |

None of this is presently enforced: the loop
(`federation/services.py:87-89`) applies every one of these to the ORM
instance guarded only by `hasattr(provider, key) and value is not None` —
`hasattr` is true for every column above, sensitive or not.

---

## 2. Trust framework update authorization contract

### A. Caller identity

- **VERIFIED.** Identical shape to federation: `trust_routes.router` is
  mounted with only `dependencies=_AUTH_REQUIRED`
  (`app/identity/api/router.py:47`); `update_framework`'s route handler
  (`app/identity/trust/routes.py:87-97`) adds no further dependency.
- **VERIFIED — identical on the active redesign branch.** Same check as
  federation: `git show origin/claude/p0-2-pharmacy-reconciliation:...trust/routes.py`
  shows `update_framework` with the same `body: dict[str, Any]`, no
  authorization dependency, sync `Session` instead of async being the only
  difference.

### B. Required authorization

- **UNKNOWN**, same as federation — no `trust_framework` permission key
  exists in the Permission catalog.
- **INFERRED — checked directly, not assumed.**
  `TrustFramework.authority_id` (`trust/models.py:34-36`) foreign-keys to
  `niam_gov_authorities` (`IdentityAuthority`,
  `app/identity/governance/models.py:11-40`). This looked like it might
  establish "the authority owns/administers its frameworks," so it was
  checked directly: `IdentityAuthority` has no relationship to `Account`,
  `Membership`, or any grant table — it is a governance-body *reference*
  record (a ministry/regulator's name, jurisdiction, accreditation dates),
  not an actor or a permission grant. It does not, by itself, establish
  which authenticated account may edit a framework referencing it. Using it
  as an authorization anchor would require a new mapping (account →
  authority → "may manage this authority's frameworks") that does not exist
  today — that mapping would itself be a canonical-identity decision, not
  something to invent here.
- Do **NOT** invent `trust-admin` as a real role: not declared anywhere in
  this codebase's role/permission tables.

### C. Object scope

- **VERIFIED.** `TrustFramework` has no `organization_id` column — same
  platform-global shape as `FederatedProvider` and as the already-documented
  `RiskPolicy`/`SessionPolicy` case in `adaptive_auth`.
- **VERIFIED — target resolution is correct.** `update_framework` looks up
  by `framework_id` from the path (`trust/services.py:106-111`), no
  client-supplied primary key trusted.

### D. Field mutability (trust framework)

| Field | Classification | Basis |
|---|---|---|
| `status` | **SECURITY_SENSITIVE** | VERIFIED; controls whether a framework is `draft`/active/`superseded` — `activate_framework`/`supersede_framework` are the framework's own dedicated state-transition operations (`trust/services.py`), so the generic update path being able to set `status` directly bypasses whatever invariants those dedicated operations enforce (e.g. `supersede_framework` also sets `supersedes_framework_id`; a bare `status` write through `update_framework` does not). |
| `assurance_policies` | **SECURITY_SENSITIVE** | VERIFIED (JSON field); this is the policy data that presumably governs IAL/AAL/FAL requirements framework-wide — rewriting it changes assurance requirements platform-wide with no review. |
| `scope` | **SECURITY_SENSITIVE** | VERIFIED (JSON field); defines what the framework applies to. |
| `authority_id`, `supersedes_framework_id` | **SECURITY_SENSITIVE** | VERIFIED FK fields; rewriting either changes the framework's governance lineage/attribution. |
| `framework_id`, `uuid` | **IMMUTABLE** | VERIFIED unique identifiers. |
| `name_en`, `name_ar`, `version`, `effective_date` | **UNKNOWN** | Plausibly SAFE_MUTABLE metadata, but see below — even `version` free-text editing without a review step for a *trust framework specifically* is not obviously safe, and no requirements doc says otherwise. |
| `created_at`, `updated_at`, `id` | **SERVER_DERIVED** | VERIFIED ORM-managed. |

Same enforcement gap as federation: the loop
(`trust/services.py:112-114`) is guarded only by
`hasattr(entity, key) and value is not None`.

---

## 3. Field-level mutation matrix

Combined summary (see §1D/§2D for the full per-field basis):

- **SECURITY_SENSITIVE, currently unprotected, in both operations:** every
  field that changes trust/crypto/redirect material or framework
  status/policy/lineage. This is the core of both VERIFIED_VULNERABLE
  findings from Phase 6 — restated here, not re-litigated.
- **IMMUTABLE, currently unprotected:** primary/business identifiers
  (`provider_id`, `framework_id`, `uuid`) — `hasattr`-only guard permits an
  attacker to attempt to rewrite these too, though colliding with a `unique`
  constraint would raise a DB error rather than silently succeed for `uuid`
  changes (VERIFIED both are `unique=True` in their model definitions).
- **SERVER_DERIVED, currently unprotected in principle, low practical risk:**
  timestamps and internal id — client-supplied values here mostly get
  overwritten again by ORM `onupdate`/generation, but nothing structurally
  prevents them being briefly wrong or, for `id`, rejected by a subsequent
  query miss rather than a clean 400.
- **UNKNOWN fields exist in both operations** — this contract does not
  assume they are safe just because no attack was found for them in this
  pass; they need the same explicit classification once real requirements
  exist.

---

## 4. Tenant/object-scope rules

- **VERIFIED.** Neither resource has a tenant/organization column. There is
  no cross-tenant scenario to defend against for these two specific
  operations — the applicable boundary is "platform-authority" (who may
  administer platform-wide trust/federation configuration at all), not
  tenant isolation.
- **BLOCKED.** What "platform-authority" means as an enforceable, real
  permission concept in NIAM is exactly the open question in §1B/§2B. This
  contract cannot resolve it without a canonical decision.

---

## 5. Audit requirements

- **VERIFIED — currently zero.** Neither `federation/services.py` nor
  `trust/services.py` contains any call to `AuditService`/`AuditEventInput`
  or any other audit mechanism, in any method (create, get, update, list) —
  grepped for `audit` in both files, zero matches. This gap predates and is
  broader than the two flagged update methods.
- **INFERRED — the canonical NIAM audit mechanism for this kind of write.**
  `app/identity/admin/services.py::_record_admin_event` (lines ~37-63) is the
  established in-domain pattern: it constructs an `AuditEventInput` with
  `category="ADMINISTRATION"`, `action`, `actor_id`, `actor_type`,
  `organization_id`, `target_type`, `target_id`, `decision`, `reason_code`,
  `outcome`, `data_classification`, then calls `self.audit.record(...)`
  (backed by `app.identity.services.audit_service.AuditService` — distinct
  from the legacy monolith's `AuditLog`/`log_action` mechanism used outside
  `app/identity/`). This is the mechanism a federation/trust equivalent
  should reuse, not the legacy one, since these resources live inside NIAM.
- Required event shape, once authorization exists to actually gate the
  write: actor identity (`account.id`/`account.uuid` from `NiamActor`),
  resource type (`"federated_provider"` / `"trust_framework"`), resource id
  (`provider_id`/`framework_id`, not the internal `id`, to match how these
  resources are addressed everywhere else in the two route files),
  `organization_id=None` (VERIFIED — genuinely not organization-scoped, so
  this is correct, not a gap), and **field-level before/after evidence**
  given how security-sensitive the mutable fields are (§1D/§2D) — a bare
  "updated" event without naming which fields changed would not let a
  reviewer distinguish "renamed the provider" from "rotated the trust
  anchor." This last point is a design recommendation, not something
  VERIFIED as already-required anywhere in the codebase.

---

## 6. Concurrency requirements

- **VERIFIED.** `IdentityBaseEntity` (`app/identity/base.py:38-63`), the
  common base for every model in `app/identity/` including
  `TrustFramework` and `FederatedProvider`, defines only `id`, `created_at`,
  `updated_at` — **no `version` column, no `OptimisticLockMixin`, anywhere
  in the NIAM identity models.** This is uniform across the entire
  `app/identity/` tree, not specific to these two resources.
- **INFERRED.** Adding optimistic locking here would mean a new migration
  (a new `version` column on two tables) — squarely a DB schema change,
  which this branch's own repair-queue discipline and the platform's
  migration policy both flag as requiring separate review, not something to
  fold into a security patch.
- **Conclusion: no CAS/If-Match/version requirement is being added by this
  contract.** The current last-write-wins concurrency model is consistent
  with every other NIAM identity write path (including the already-reviewed
  `admin/services.py::update_subscription`), so introducing it only for
  these two would be inventing a new invariant, not closing the flagged
  vulnerability. If optimistic locking is wanted platform-wide for
  `app/identity/`, that is its own, separate proposal.

---

## 7. Migration/data compatibility

- **INFERRED, not independently re-verified this pass.** `niam_trust_frameworks`
  and `niam_fed_providers` are pre-existing, already-migrated tables (both
  domains have working `create_*`/`get_*`/`list_*` routes reachable and
  presumably tested elsewhere in the suite) — no new migration is implied by
  fixing the authorization gap itself, since the fix is application-layer
  (a permission check + field allow-list), not a schema change.
- **BLOCKED.** Whether a real permission-key row (e.g. a future
  `trust_framework.manage` / `federated_provider.manage` permission) would
  need a data migration to seed it depends entirely on the still-undecided
  question in §1B/§2B — cannot be answered until that decision exists.
- **VERIFIED.** No role/permission table currently has any row referencing
  these two resource types (§1B) — so today, even if `AuthorizationDecisionService`
  could structurally apply to non-organizational resources (it cannot — see
  §8), there is no permission to check against yet.

---

## 8. Compatibility with active redesign (`origin/claude/p0-2-pharmacy-reconciliation`)

- **VERIFIED — the active redesign does not touch these two operations.**
  The AUTH-002 through AUTH-005 commit series on that branch (`be7d904c`,
  `94836afa`, `97b6a283`, `59bf3c78`, `6a8c5c42`, `05291260`, `27bd108c`,
  `04bcc97a`, `4935bf85`) is a real, extensively-documented identity
  authentication/assurance redesign — but its scope is: (a) resolving which
  identity table a legacy integer token id refers to (`AUTH-002`/`AUTH-003`,
  `NR-035`), (b) per-purpose assurance scoring (`AUTH-004`, `NR-037`), and
  (c) gating citizen/health-data linkage on verified identity evidence
  (`AUTH-005`, `NR-038`-`NR-040`, on the **`POST /niam/trust/assurance-profiles`**
  route — a different route in the same `trust` package, not
  `update_framework`). None of these commits mention `update_provider`,
  `update_framework`, or a federation/trust-framework permission model.
- **VERIFIED, checked directly rather than assumed from the commit
  messages.** `git show origin/claude/p0-2-pharmacy-reconciliation` for both
  `trust/routes.py::update_framework` and `federation/routes.py::update_provider`
  shows the identical authorization shape as this branch: `body: dict[str,
  Any]`, no authorization dependency beyond router-level `_AUTH_REQUIRED`,
  same `**body`/`**kwargs` unpack into an unguarded `setattr` loop. The large
  line-count diffs on that branch for `trust/routes.py` (289 lines) and
  `trust/services.py` (260 lines) are real, but — per the evidence above —
  they are not a fix for this gap; they are the assurance-profile
  work (`NR-038`) and a sync-vs-async / structural refactor, landing in the
  same files.
- **VERIFIED — `identity/api/router.py`'s own redesign (`NR-108`, visible in
  that branch's current file) fixed a related-but-different problem**: three
  routers (`persons`, `sessions`, `devices`) had **no** `_AUTH_REQUIRED` at
  all — a strictly worse bug (unauthenticated access) than trust/federation's
  "authenticated but unauthorized" gap. That fix did not add anything beyond
  `_AUTH_REQUIRED` to `trust_routes.router`/`federation_routes.router` — both
  already had it on both branches, and NR-108's own list of examples does not
  include either.
- **Conclusion: BLOCKED, not merely unresolved by coincidence.** The active
  redesign does not define — and, on the evidence available, has not yet
  reached — an authorization contract for platform-wide
  trust-framework/federation-provider mutation. This is not "wait for his
  branch to land the fix"; there is no evidence a fix for this specific gap
  exists in flight there. It is the same open question on both branches.

---

## 9. Unresolved questions / blockers

1. **BLOCKED.** What real, platform-scoped authorization concept should gate
   `update_provider`/`update_framework`? Candidates considered and rejected
   as not-yet-real: a `federation-admin`/`trust-admin` role (not declared
   anywhere), `IdentityAuthority`-based delegation (no account↔authority
   grant mapping exists), and the existing `AuthorizationDecisionService`
   (structurally cannot authorize a non-organizational resource type outside
   `NON_ORGANIZATIONAL_READS` — confirmed by reading `_resolve_membership`
   and the `membership_unresolved` deny path in
   `app/identity/services/authorization_decision.py:243-296`, which denies
   unconditionally when `organization_id` is `None` and the resource type
   isn't in that frozenset).
2. **BLOCKED.** Should `NON_ORGANIZATIONAL_READS` ever be widened to cover
   platform-wide *writes* (not just reads, despite its name) for exactly
   this class of resource (`risk_policy`, `session_policy`,
   `trust_framework`, `federated_provider`)? This is the canonical-semantics
   change the `adaptive_auth` docstring already flagged as out of this
   branch's authority to decide alone — restated here because it recurs for
   both new findings, not resolved differently just because it recurs.
3. **UNKNOWN.** Is a field-level allow-list (mirroring the request schema, as
   done for Hospital in Phase 5) sufficient once authorization exists, or do
   `status` transitions specifically need to go through the existing
   dedicated operations (`activate_framework`, `supersede_framework`) instead
   of being reachable via the generic update path at all? No requirements
   doc answers this; flagged rather than guessed.
4. **UNKNOWN.** Intended audit retention/classification level for
   trust/federation configuration changes — `_record_admin_event`'s
   `data_classification="CONFIDENTIAL"` is a plausible default (matching
   `admin/services.py`) but not confirmed against any written policy for
   this specific data class.

---

## Proposed minimal repair shape (DESIGN ONLY — no code in this document)

Not implemented. Offered because Phase 7 asked for the smallest concrete
shape, not because it is authorized to be applied by this branch without a
sign-off, given §9.1/§9.2 are canonical-authorization-semantics questions.

1. Apply the **same fail-closed stub pattern already proven in this exact
   codebase** at `adaptive_auth/routes.py:_require_policy_admin`, to both
   `update_provider` and `update_framework`'s route handlers: a
   `_require_platform_trust_admin()` (or equivalently named) dependency that
   unconditionally raises 403 with a docstring stating the same reasoning as
   `_POLICY_AUTHORITY_UNAVAILABLE` — until a real platform-scoped permission
   concept exists, this closes the "any authenticated user can rewrite
   federation/trust config" gap without inventing a role or widening
   `AuthorizationDecisionService`'s semantics.
   - This is the **minimal, non-guessing** move: it does not decide what the
     real permission model should be (§9.1/§9.2 remain open), it only stops
     the currently-provable exploit path the same way the identical shape of
     problem was already stopped for `RiskPolicy`/`SessionPolicy`.
2. Once a real authorization decision exists (from whoever owns that
   canonical decision), replace the stub with a real permission check, add
   the field-level allow-list from §1D/§2D (excluding IMMUTABLE/SERVER_DERIVED
   fields, gating SECURITY_SENSITIVE fields at minimum on the same
   permission, possibly a stricter one), and wire `_record_admin_event`-style
   audit logging with field-level before/after evidence (§5).
3. No optimistic locking, no migration, no new role/permission row is part
   of the minimal repair (§6/§7) — those are separate, larger proposals if
   ever wanted.

---

## Acceptance-criteria confirmation

- Both vulnerabilities remain **OPEN** — no source file under `app/identity/`
  was modified to produce this document.
- No new role or permission was invented; §9 explicitly declines to invent
  `federation-admin`/`trust-admin`/widened `NON_ORGANIZATIONAL_READS`.
- No claim of resolution is made anywhere above.
- Every VERIFIED claim above cites the exact file/line/command that produced
  it (models, routes, services, `authorization_decision.py`, `git show`
  against `origin/claude/p0-2-pharmacy-reconciliation`, `git log --all` for
  the AUTH-series commits).
- Existing `AUTH-`/`NR-` terminology is preserved and cross-referenced
  (`NR-038` re: the *different* assurance-profiles route, `NR-108` re: the
  *different*, worse missing-auth-entirely bug on other routers) without
  claiming either resolves this contract's two findings.
- No merge/rebase/cherry-pick/branch-switch was performed; both repositories
  were inspected read-only (`git show <ref>:<path>`, `git log --all`).
- No full test suite was run; no broad repository scan beyond the files this
  directive named plus the specific helper modules (`authorization_decision.py`,
  `workspaces.py`, `base.py`, `admin/services.py`, `governance/models.py`)
  needed to answer A–H for the two named operations.

---

## STATUS

**PARTIALLY VERIFIED.**

Every factual claim about the *current* code (both branches) is VERIFIED by
direct inspection. The canonical authorization contract itself — what
permission/role should gate these two operations — is **BLOCKED**: it does
not exist yet in either branch, and this branch is not authorized to invent
it.

## NEXT ACTION

The smallest concrete code change available **today, without any further
canonical decision**, is item 1 of the proposed minimal repair: add a
fail-closed `_require_platform_trust_admin`-style dependency (mirroring
`adaptive_auth/routes.py:_require_policy_admin` verbatim in structure) to
`update_provider` (`federation/routes.py:97-107`) and `update_framework`
(`trust/routes.py:87-97`), closing the currently-provable "any authenticated
user" exploit path without inventing a permission model. This still requires
explicit sign-off before implementation, since it changes externally-visible
API behavior (both endpoints go from "any authenticated user can update" to
"403 for everyone" — the same functionality-vs-security tradeoff the
`adaptive_auth` precedent already accepted) and touches files Abu Ali's
branch is concurrently rewriting (§8) — not because the technical change
itself is unclear.

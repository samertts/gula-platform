# Federation / Trust-Framework — Canonical Authority Decision

Investigation-only, per Phase 8A's instruction. No source file under
`app/identity/` was modified. No role, permission, or migration was added.
This builds directly on `docs/security/FEDERATION_TRUST_AUTHORIZATION_CONTRACT.md`
(Phase 7) — nothing in that document is corrected here; this document adds
evidence Phase 7 didn't need (sibling-service lifecycle patterns,
`certificates`/`governance` routes, role/permission catalog search), all of
which is consistent with, not contradictory to, Phase 7's findings.

Tags: **VERIFIED** (read directly from cited file/line), **INFERRED**
(a conclusion from VERIFIED evidence), **UNKNOWN** (no evidence found),
**BLOCKED** (answerable only by a decision this branch cannot make alone).

---

## 1. FederatedProvider authority

**1.1 Conceptual ownership: A — platform-global.**
**VERIFIED.** `FederatedProvider` (`app/identity/federation/models.py:11-47`)
has no `organization_id`, `facility_id`, or any tenant column. It is a single
platform-wide registry of federation identity providers (OAuth2/OIDC IdPs
the whole NIAM platform trusts), not a resource any one organization owns.
Not "indeterminate" — the absence of a tenant column is a positive,
checkable fact, not missing data.

**1.2 Existing authority concept governing federation administration /
IdP configuration / credentials / trust anchors / activation: none found.**
- **VERIFIED.** `federation/routes.py` has no authorization dependency on
  any route beyond the router-level `_AUTH_REQUIRED` (any authenticated
  NIAM actor) — confirmed for `register_provider`, `update_provider`,
  `link_identity` by reading the full route file.
- **VERIFIED — the adjacent `certificates` domain has the identical gap,
  not a working example to borrow from.** `app/identity/certificates/routes.py`
  (`issue_certificate`, `revoke_certificate`) has **zero** authorization
  dependency in either handler's signature — just `db: Depends(get_db)`.
  Certificate issuance/revocation is at least as sensitive as federation
  provider credentials, and it is unauthorized in exactly the same way. This
  is evidence the gap is systemic across this cluster of NIAM sub-domains,
  not something federation alone forgot to adopt from a working sibling.
- **VERIFIED — `governance/routes.py::create_authority` (the operation that
  creates the `IdentityAuthority` rows `TrustFramework.authority_id` points
  at) also has no authorization dependency.** So even the "authority" concept
  itself is currently unguarded at its source — it cannot be the missing
  permission anchor for federation, because creating an authority record
  requires no more privilege than creating a federation provider does today.
- **INFERRED.** No dedicated `activate`/`deactivate` lifecycle operation
  exists for `FederatedProvider` at all — `register_provider` (create) and
  `update_provider` (generic field update, which also happens to accept
  `status`) are the only two mutators. Contrast with `TrustAnchorService`
  (below) and `FederationTrustService`/`CrossOrgTrustService`, which do have
  dedicated lifecycle methods. `FederatedProvider` is the one place in this
  cluster where lifecycle, credentials, and metadata are undifferentiated —
  not because an authority concept was deliberately withheld from it, but
  because no operation-splitting was done here at all.

**1.3 Existing role/permission/workflow implying ownership: none found.**
- **VERIFIED.** Grepped `app/identity` for `super_admin`, `system_admin`,
  `SUPER_ADMIN`, `PLATFORM_ROLES`, `SYSTEM_ROLES`, a role-catalog class —
  zero matches. No platform-wide administrative role is declared anywhere
  in this codebase's role/permission tables.
- **VERIFIED (restated from Phase 7, re-checked, not re-litigated).**
  `Permission`/`PermissionSensitivity` (`app/identity/models/authorization.py`)
  and the NIAM completion migration
  (`backend/migrations/versions/20260723_0002_niam_completion_tables.py`)
  define no permission row referencing `federated_provider` as a
  `resource_type`.
- **INFERRED.** The only real precedent for "a genuinely platform-global
  NIAM resource with no permission model" is `RiskPolicy`/`SessionPolicy` in
  `adaptive_auth`, which the codebase itself resolved by failing closed
  (`_require_policy_admin`) rather than assigning ownership to any existing
  role. No workflow anywhere assigns federation-provider ownership to a role,
  an organization, or an authority.

---

## 2. TrustFramework authority

**2.1 Conceptual ownership: A — platform-global.**
**VERIFIED.** Same basis as §1.1: `TrustFramework`
(`app/identity/trust/models.py:21-39`) has no tenant column.
`authority_id` is a descriptive foreign key (which governance body the
framework is associated with), not a scoping column — checked directly,
not assumed (see 2.2).

**2.2 Existing authority concept: `IdentityAuthority` exists but does not
establish ownership.**
- **VERIFIED.** `TrustFramework.authority_id` FKs to `niam_gov_authorities`
  (`IdentityAuthority`, `app/identity/governance/models.py:11-40`) — a
  record describing a governance body (name, jurisdiction, accreditation
  dates, parent authority). It has no relationship to `Account`,
  `Membership`, or any grant table — checked directly in
  `governance/models.py`, not inferred from the name. There is no
  "this account represents this authority" mapping anywhere in the schema.
  Referencing an authority is not the same as being governed by it.
- **VERIFIED.** `activate_framework` and `supersede_framework`
  (`trust/services.py:75-92`) are dedicated, narrower lifecycle operations
  that already exist *separately* from `update_framework` — this is the
  codebase's own established idiom for status transitions on this exact
  entity, not something Phase 8A needs to invent. Neither one is
  authorization-gated either (`trust/routes.py` has no dependency on
  `activate_framework`'s route) — so the idiom of separating lifecycle
  operations already exists, but was never paired with an authorization
  check on any of the three (`update_framework`, `activate_framework`,
  `supersede_framework`).

**2.3 Existing role/permission/workflow implying ownership: none found.**
Same conclusion and same evidence as §1.3 — no platform role, no
permission-catalog row for `trust_framework`, no workflow.

---

## 3. Existing authorization mechanisms (survey, for completeness)

| Mechanism | Applies to trust/federation? | Basis |
|---|---|---|
| `get_current_niam_actor` / `_AUTH_REQUIRED` | Authentication only, not authorization | VERIFIED — proves a live session, resolves no role/permission (`workspaces.py:65-89`) |
| `AuthorizationDecisionService` + `_require_permission` (admin/compliance/audit/security domains) | No — structurally cannot | VERIFIED (re-checked from Phase 7): denies unconditionally when `organization_id` is `None` and resource type isn't in `NON_ORGANIZATIONAL_READS = {"role_catalog","permission_catalog"}` (`authorization_decision.py:174,249,290,339`) |
| `_require_policy_admin` fail-closed stub (`adaptive_auth`) | Not directly, but is the only proven pattern for this exact shape of problem | VERIFIED as existing code; INFERRED as the applicable precedent |
| Certificate issuance/revocation authorization | No — same gap, not a model to copy | VERIFIED, `certificates/routes.py` |
| Governance-authority creation authorization | No — same gap | VERIFIED, `governance/routes.py` |
| A platform-wide admin role | Does not exist | VERIFIED by exhaustive grep, zero hits |

**Conclusion: there is no existing authorization mechanism in this codebase
that already applies to platform-global NIAM resources except the fail-closed
stub precedent.** This is not one gap among several working alternatives —
it is the systemic shape of this entire corner of NIAM (adaptive_auth
policies, certificates, governance authorities, federation providers, trust
frameworks all share it).

---

## 4. Field-level authority matrix

### FederatedProvider

| Field | Classification | Notes |
|---|---|---|
| `client_secret_encrypted` | **SECURITY_SENSITIVE** | Credential material. |
| `certificate`, `signature_algorithm` | **SECURITY_SENSITIVE** | Signing/verification trust material. |
| `trust_anchor_id` | **SECURITY_SENSITIVE** | Changes which anchor backs this provider's trust chain. |
| `status` | **SECURITY_SENSITIVE** | Lifecycle gate; no dedicated activate/deactivate op exists today (§1.2) — currently only reachable via the generic update. |
| `issuer_url`, `authorization_endpoint`, `token_endpoint`, `jwks_uri`, `userinfo_endpoint`, `redirect_uris` | **SECURITY_SENSITIVE** | Redirect/endpoint hijack surface (open-redirect / credential interception). |
| `provider_id`, `uuid` | **IMMUTABLE** | Unique identifiers. |
| `client_id`, `scopes`, `metadata_url`, `name_en`, `name_ar`, `provider_type` | **UNKNOWN**, plausibly SAFE_METADATA | No requirements doc confirms these are safe to leave client-writable without review; not asserted either way. |
| `id`, `created_at`, `updated_at`, `last_sync_at` | **SERVER_DERIVED** | ORM/system-managed. |

### TrustFramework

| Field | Classification | Notes |
|---|---|---|
| `status` | **SECURITY_SENSITIVE** | Already has dedicated ops (`activate_framework`, `supersede_framework`) that exist precisely because status is not a bare metadata field — see §5. |
| `assurance_policies` | **SECURITY_SENSITIVE** | Platform-wide IAL/AAL/FAL policy data (JSON); rewriting it changes assurance requirements framework-wide. |
| `scope` | **SECURITY_SENSITIVE** | Defines what the framework governs. |
| `authority_id`, `supersedes_framework_id` (lineage) | **SECURITY_SENSITIVE** | Governance attribution/lineage; `supersedes_framework_id` is also set by the dedicated `supersede_framework` op — a bare field write bypasses that op's paired `status="superseded"` transition. |
| `framework_id`, `uuid` | **IMMUTABLE** | Unique identifiers. |
| `name_en`, `name_ar`, `version`, `effective_date` | **UNKNOWN**, plausibly SAFE_METADATA | Same caveat as above — not asserted safe, just not shown vulnerable to a specific named attack in this pass. |
| `id`, `created_at`, `updated_at` | **SERVER_DERIVED** | ORM-managed. |

---

## 5. Operations that should remain separate

**Evidence-based, not a new design opinion** — the codebase already applies
exactly this separation everywhere else in the same two service files, and
`update_provider`/`update_framework` are the outliers:

| Candidate separate operation | Existing precedent for separation | Applies to |
|---|---|---|
| **Lifecycle status change** | `TrustFrameworkService.activate_framework` / `.supersede_framework` (dedicated, narrow) vs. generic `update_framework` (`trust/services.py:75-92` vs `106-116`); `FederationTrustService.suspend_trust`/`.terminate_trust` and `CrossOrgTrustService.suspend_trust`/`.terminate_trust` have **no generic update method at all** — status transitions are the *only* mutation path for those two entities (`trust/services.py:346-360`, `federation/services.py:261-286`) | Both |
| **Trust-anchor change** | `TrustAnchorService` has **no generic update method** — only `create_anchor`, `revoke_anchor`, `list_anchors`, `validate_chain` (`trust/services.py:215-298`). A trust anchor is never bulk-field-updated anywhere in this codebase; only `FederatedProvider.trust_anchor_id` (a foreign reference to one) is, via the generic loop. | FederatedProvider (assigning/changing which anchor backs it) |
| **Credential rotation** | No existing dedicated op for `FederatedProvider`, but `CertificateService` (`certificates/`) treats issuance and revocation as dedicated, narrow operations rather than a generic field update (`certificates/routes.py:16-58`) — same idiom, different entity | FederatedProvider (`client_secret_encrypted`, `certificate`, `signature_algorithm`) |
| **Assurance-policy change** | No existing dedicated op, but `assurance_policies` is qualitatively different from descriptive metadata (name/version) in the same way `RiskPolicy`'s thresholds are treated as requiring `_require_policy_admin` rather than open update in `adaptive_auth` — same class of "changes a platform-wide security control," same reasoning applies | TrustFramework |
| **Scope change** | No existing dedicated op; grouped with assurance-policy change above by similarity, not separately evidenced | TrustFramework |
| **Metadata update** | Implicitly, everything not listed above (`name_en`/`name_ar`/`version`/`effective_date` for TrustFramework; `name_en`/`name_ar`/`client_id`/`scopes`/`metadata_url`/`provider_type` for FederatedProvider) — no precedent says this must be separate, but nothing found says it's dangerous either | Both |

**Conclusion: YES, these should be separated — this is not a novel proposal,
it is bringing `update_framework`/`update_provider` into line with the
separation already used by every sibling service in these same two files.**

---

## 6. VERIFIED

- Both resources are platform-global (no tenant column) — §1.1/§2.1.
- No authorization dependency exists today on `update_provider`,
  `update_framework`, `register_provider`, `activate_framework`,
  `supersede_framework`, `issue_certificate`, `revoke_certificate`, or
  `create_authority` — the gap spans the whole federation/trust/
  certificates/governance cluster, not just the two Phase 6 findings.
- `AuthorizationDecisionService` cannot structurally authorize either
  resource type without widening `NON_ORGANIZATIONAL_READS` (re-confirmed
  by re-reading `_resolve_membership`/the deny path).
- No platform-wide administrative role exists in the role/permission tables
  (exhaustive grep, zero hits).
- `IdentityAuthority` (`authority_id`) is a descriptive reference, not a
  grant of authority over the framework — checked directly in its model.
- The codebase's own idiom, applied consistently to `TrustAnchor`,
  `FederationTrust`, `CrossOrganizationTrust`, and partially to
  `TrustFramework` itself (`activate`/`supersede`), already separates
  lifecycle transitions from generic field updates. `FederatedProvider` and
  the generic halves of `TrustFramework`'s update path are the exceptions.

## 7. UNKNOWN

- Whether `name_en`/`name_ar`/`version`/`provider_type`/`client_id`/`scopes`/
  `metadata_url`/`effective_date` are actually safe to leave client-writable
  without review (classified UNKNOWN/plausibly-SAFE_METADATA, not asserted
  safe).
- Intended audit classification/retention for a future trust/federation
  admin action (noted in Phase 7 §9.4, unchanged here).
- Whether `certificates`/`governance` domains' identical authorization gaps
  are already tracked elsewhere (not found in this pass; out of this
  directive's named scope to resolve, but flagged since they share the root
  cause).

## 8. BLOCKED

- **The canonical authority model itself.** No repository evidence — code,
  migration, permission row, role, ADR, or commit on either branch —
  establishes who or what should be authorized to administer platform-global
  NIAM resources (adaptive_auth policies, trust frameworks, federation
  providers, certificates, governance authorities). This is not a gap this
  branch can fill by choosing a role name; the `adaptive_auth` precedent
  explicitly declined to do so for the identical shape of problem, and nothing
  found since contradicts that judgment.
- Whether `IdentityAuthority` is *intended* to eventually become that
  authority anchor (via a future account↔authority grant mapping that does
  not exist yet) is plausible but **not evidenced** — it would be inventing
  a role/mapping to say so now.

---

## 9. Smallest canonical authorization decision required

One question, and it is the same question `adaptive_auth/routes.py`'s own
docstring already posed and left open:

> **Does NIAM have, or intend to have, a platform-level administrative
> authority concept — distinct from the organization-scoped RBAC that
> `AuthorizationDecisionService` implements — and if so, what identifies an
> account as holding it (a boolean flag on `Account`, a reserved
> organization, a mapping to `IdentityAuthority`, or something else)?**

Everything else in this document (roles, permission rows, field allow-lists,
which operations to split) is downstream of that one answer. It is a human/
architectural decision, not a code question — it decides identity/
authorization semantics for the whole platform-global corner of NIAM, not
just these two resources, which is exactly why Phase 6/7/8A have each
declined to guess at it.

---

## 10. Emergency containment option (separate from §9 — does not require it)

This does **not** need the §9 decision to be made first. It only requires
agreeing that "temporarily unavailable to everyone" is safer than "writable
by any authenticated user" for these two specific operations — a much
narrower, already-precedented call (`adaptive_auth` made exactly this call
for `RiskPolicy`/`SessionPolicy`).

**Option:** add a fail-closed dependency (mirroring
`adaptive_auth/routes.py:_require_policy_admin` verbatim in structure and in
its documented reasoning) to `update_provider`
(`federation/routes.py:97-107`) and `update_framework`
(`trust/routes.py:87-97`) only. Both endpoints return 403 for every caller
until §9 is resolved. No role, permission, schema, or migration change. Read
operations (`get_provider`, `list_providers`, `get_framework`,
`list_frameworks`), `register_provider`/`create_framework`, and the
already-separate lifecycle ops (`activate_framework`, `supersede_framework`)
are **not** touched by this option — it is scoped to the two confirmed
mass-assignment/missing-authorization findings only. Note that
`register_provider`, `activate_framework`, `supersede_framework`,
`issue_certificate`, `revoke_certificate`, and `create_authority` share the
identical "no authorization dependency" gap (§6) but were out of Phase 6's
named scope — this containment option does not extend to them, and doing so
would be widening scope beyond what was asked.

This is presented as an option, not applied — it is still a change to
externally-visible API behavior and touches files under active concurrent
rewrite on `origin/claude/p0-2-pharmacy-reconciliation` (per Phase 7 §8), so
it still needs explicit sign-off before implementation.

---

## 11. Exact code changes that would follow AFTER a decision

**Track A — emergency containment only (needs only §10's narrower sign-off,
not §9):**
1. Add `_require_platform_trust_admin()` (or equivalently named) to
   `federation/routes.py` and `trust/routes.py`: an unconditional
   `raise HTTPException(403, ...)`, documented the same way
   `_POLICY_AUTHORITY_UNAVAILABLE` is.
2. Add it as a `Depends(...)` on `update_provider` and `update_framework`
   only.
3. No test changes beyond asserting both routes now 403 regardless of
   caller.

**Track B — full resolution (needs §9 resolved first):**
1. Add a real permission-catalog row (or equivalent access-control record)
   for whatever resource-type name the §9 decision settles on, scoped to
   however the decision defines "platform authority" (a flag, a reserved
   org, an authority-mapping table).
2. Replace the Track-A stub with a real check against that mechanism.
3. Split `update_provider`/`update_framework` per §5 into narrower
   operations (metadata / credential-rotation / trust-anchor-change /
   lifecycle-status-change / assurance-policy-change / scope-change),
   mirroring the separation already used by `TrustAnchorService`,
   `FederationTrustService`, `CrossOrgTrustService`, and
   `TrustFrameworkService.activate_framework`/`.supersede_framework`.
   Field-level gating per §4's matrix (IMMUTABLE/SERVER_DERIVED fields
   never settable via any of these operations; SECURITY_SENSITIVE fields
   gated on the strongest available permission; UNKNOWN fields reclassified
   before being exposed, not defaulted to writable).
4. Add audit logging via the `_record_admin_event`-equivalent NIAM
   `AuditService` pattern already used in `admin/services.py`, with
   field-level before/after evidence (per Phase 7 §5).
5. No optimistic locking / migration is implied by any of the above (per
   Phase 7 §6/§7, unchanged).

---

## Acceptance-criteria confirmation

- No source-code modification was made.
- No role or permission was invented — §9 explicitly names the undecided
  question rather than answering it with an assumed role.
- Result is legitimately **BLOCKED** at the canonical-authority level (§8),
  as the directive anticipated it might be.
- Phase 7's contract is not corrected — this document's additional evidence
  (sibling-service separation idiom, certificates/governance gaps, absence
  of a platform role) is consistent with, and extends, Phase 7's findings.
- No full test suite was run; no repository scanning beyond the files this
  directive named plus the specific adjacent modules needed to answer 1-3
  (`certificates/routes.py`, `governance/routes.py`,
  `governance/models.py`, `authorization.py`, `ARCHITECTURE_DECISION_LOG.md`).
- No merge/rebase/cherry-pick/branch switch was performed.

---

## STATUS

**BLOCKED** at the canonical-authority level (§8/§9).
**PARTIALLY VERIFIED** at the evidence level — every factual claim about
current code, on both branches, is directly verified; only the authority
model itself is undetermined.

## NEXT ACTION

Not a code change. The smallest human/architectural decision required is
§9: whether NIAM has, or is meant to have, a platform-level administrative
authority concept distinct from organization-scoped RBAC, and if so, how an
account is recognized as holding it. Until that is answered, the only
available forward motion without inventing an answer is the narrower,
already-precedented §10 emergency-containment sign-off (fail-closed on the
two named routes) — itself still requiring explicit approval before
implementation, not a decision this document makes on its own.

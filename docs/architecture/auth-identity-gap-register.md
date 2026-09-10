# Auth / Identity Gap Register (AUTH-002)

Companion to `auth-identity-bridge-decision.md` and `auth-identity-model.md`.
Findings carry ID, Severity, Area, Evidence, Current State, Risk, Canonical
Owner, Dependency, Recommended Action, Status.

---

## AUTH-F8 · P1 · `user_id` is ambiguous across two identity tables
* **Area** identity integrity
* **Evidence** `app/security/dependencies.py:65-71` queries `LabUser.id == user_id`
  first, then falls back to `User.id == user_id`. Both tables have independent
  `INTEGER` primary keys; the token carries no discriminator. The platform
  already models the discriminator elsewhere — `get_perm_version(..., account_kind="user"|"lab")`
  and `LegacyAccountLinkSource = {user, lab_user}`.
* **Current state** `users` = 0 rows, `lab_users` = 6. The ambiguity is therefore
  latent, not live.
* **Risk** account-takeover class. The moment citizens are registered into
  `users`, a token for `users.id = N` resolves to `lab_users.id = N` if one
  exists — silently, with the laboratory user's role and `lab_id`.
* **Canonical owner** Identity Platform
* **Dependency** resolved by the AUTH-002 bridge (Option A)
* **Action** carry `source_kind` through the bridge; do not add a discriminator
  claim to the legacy token as a separate mechanism.
* **Status** VERIFIED

## AUTH-F5 · P2 · Memberships do not confer workspace eligibility
* **Area** authorization model
* **Evidence** `WorkspaceService.list_eligible` consults `owner_account_id`,
  `OrganizationRepresentative` and `OrganizationOwnership`. It does **not**
  consult `niam_memberships`, although `GET /niam/memberships/me` exists and
  `AuthContext.refreshMemberships` fetches it.
* **Risk** the constitution's chain is *membership → workspace → role*; today
  membership is a parallel concept that grants nothing. Either it feeds
  eligibility or its purpose must be stated.
* **Canonical owner** Identity Platform
* **Dependency** none — a design question, answerable now
* **Action** decide before SWITCH; do not change `list_eligible` opportunistically.
* **Status** VERIFIED

## AUTH-F6 · P2 · No token-purpose claim distinguishes the two stacks
* **Area** token security
* **Evidence** both stacks call the same `create_token` with the same
  `SECRET_KEY`. Measurement E shows a NIAM-shaped token is cryptographically
  valid at a legacy endpoint and rejected only because `user_id` is absent.
* **Risk** the separation rests on claim presence, not on an explicit statement
  of purpose. Thin, and it thins further as claim sets converge under Option A.
* **Canonical owner** Identity Platform
* **Dependency** AUTH-002
* **Action** add an explicit purpose/audience claim as a hardening step at the
  SHADOW stage; **not** a reason to delay ADD.
* **Status** VERIFIED

## AUTH-F7 · P2 · Two revocation mechanisms must both be honoured during the bridge
* **Area** session lifecycle
* **Evidence** legacy revokes by blacklisting a `jti` and by bumping
  `perm_version`; NIAM revokes by deactivating a `niam_sessions` row. Legacy has
  no session table.
* **Risk** if the ADD stage mints a NIAM session but logout only blacklists the
  `jti`, the session row stays active — or the reverse. Logout would regress.
* **Canonical owner** Identity Platform
* **Dependency** AUTH-002 ADD stage
* **Action** logout must do both, from the first cohort onward. This is a
  correctness requirement of ADD, not a later hardening.
* **Status** VERIFIED

## AUTH-F9 · P3 · Mapper configuration depends on import order
* **Area** maintainability
* **Evidence** `CitizenLink` (`app/models/canonical_patient.py:84`) has a
  relationship to `Citizen`, which `import_all_models()` does not register. In
  the running app it is registered incidentally by
  `app/routes/register.py` importing it at module level.
* **Current state** **not a live defect** — the app boots and the suite passes.
* **Risk** any context that configures mappers without importing routes (an
  offline script, a future worker entry point) fails with
  `InvalidRequestError`. Encountered while building the AUTH-002 harness.
* **Canonical owner** platform
* **Action** add the MPI models to `import_all_models()`. Safe and trivial;
  deliberately **not** done in AUTH-002 because it touches shared startup code
  and this batch changes no production code.
* **Status** VERIFIED

---

## Prior findings this batch resolves or advances

| Finding | Movement |
|---|---|
| **PUB-001** (two identity systems, app on the wrong one) | Root cause located precisely: a *claims* mismatch, not a crypto or design failure. Bridge code found already in production use by four clinical gates. **Decision made: Option A.** |
| **PUB-006** (Privacy Centre backend unreachable) | Unblocked by the same bridge — the ADD stage creates the `niam_sessions` rows `/niam/sessions` needs. |
| **PUB-005** (citizens routed into the institutional shell) | Depends on AUTH-003; unchanged. |
| **PUB-003** (`/citizen/login` parallel auth) | Retirement is the RETIRE stage of the migration ladder. |

## Register cross-reference

`NR-035` has been added to `GULA_MASTER_NEGATIVE_REGISTER` for AUTH-F8, the only
P1 in this batch. AUTH-F5/F6/F7/F9 are tracked here and in the PUBLIC-001 gap
register rather than duplicated into the master register.

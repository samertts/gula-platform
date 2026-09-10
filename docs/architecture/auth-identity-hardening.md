# AUTH-003 — Unified Authentication + Identity Bridge Hardening

Companion to `auth-identity-bridge-decision.md` (the Option A decision),
`auth-identity-model.md` (the two stacks) and `auth-identity-gap-register.md`
(AUTH-F5…F9).

**Status: PARTIALLY DELIVERED.** One phase group is implemented and proven;
four phases are BLOCKED on evidence and decisions that cannot be manufactured
in a working session. This document states which is which, and why.

---

## 1. What was delivered

**NR-035 / AUTH-F8 — the `user_id` claim is now discriminated.** Every token
GULA mints declares which identity table its subject lives in, and resolution
selects exactly one table.

`users` and `lab_users` are two identity tables with independent `INTEGER`
primary keys. A claim of `user_id = N` did not say which one it meant.
Resolution queried `lab_users` first and fell back to `users`, so a token
issued for `users.id = N` silently resolved to `lab_users.id = N` whenever that
row existed — with that laboratory user's role and `lab_id`.

The discriminator is not new. The platform already models it in two places:

| Where | Shape |
|---|---|
| `security/session.py::perm_ver_key` | `user:{account_kind}:perm_ver:{id}`, `account_kind ∈ {user, lab}` |
| `identity/models` `LegacyAccountLinkSource` | exactly `{user, lab_user}` |

The revocation cache has therefore always kept two colliding ids apart. The
token was the single place that could not say which of them it meant. AUTH-003
carries it there, as the claim `act`.

### Sites changed

| Site | Was | Now |
|---|---|---|
| `security/auth.py::build_token_payload` | no discriminator | `act`, defaulting to `lab`; an unknown kind raises at mint time |
| `security/dependencies.py` | LabUser-first, User fallback | `resolve_token_subject()` — one table, or refuse |
| `routes/login.py` (staff) | `build_token_payload(user)` | `account_kind=ACCOUNT_KIND_LAB` |
| `routes/login.py` (citizen) | raw claims dict | `+ "act": "user"` |
| `routes/login.py` (logout) | LabUser-first, User fallback | `resolve_token_subject()` |
| `routes/citizen_portal.py` (`/citizen/login`) | raw claims dict | `+ "act": "user"` |
| `routes/mobile.py` (refresh rotation) | LabUser-first, User fallback | `resolve_token_subject()`; rotated citizen claims carry `act` |
| `routes/demo.py` | implicit | explicit `ACCOUNT_KIND_LAB` |

The mobile refresh endpoint carried the same defect as `get_current_user`, and
worse: it *mints* from what it resolves, so a citizen's refresh token could be
exchanged for an access token bearing a laboratory user's role and tenant. It
was found by grep during AUTH-003, not by AUTH-002, which recorded only the
`get_current_user` instance.

### Backward compatibility, and where it fails closed

Tokens minted before this change carry no `act`. Invalidating every live
session was avoidable, so those still resolve by search — but
`resolve_token_subject` **refuses when the id exists in both tables**, which is
precisely the case the old behaviour got wrong. Ambiguity is refused, never
guessed, and the refusal is logged at ERROR.

An `act` value that is neither `user` nor `lab` fails closed and logs at
WARNING. It cannot be minted at all: `build_token_payload` raises `ValueError`.

### Deviation from AUTH-002's stated action — declared

AUTH-002 recorded the fix as *"carry `source_kind` through the bridge; do not
add a discriminator claim to the legacy token as a separate mechanism."*
AUTH-003 adds the claim. The reasoning, stated so it can be overruled:

* The bridge is BLOCKED (§2). NR-035 is P1 and account-takeover class.
* It is latent only because `users` holds **0 rows** (measured at head:
  `users=0, lab_users=6`). It goes live at the *first citizen registration* —
  which is the stated destination of this programme (Phase 14).
* `act` is not a parallel mechanism: it carries the **same** `{user, lab_user}`
  discriminator `LegacyAccountLinkSource` already defines. When the bridge
  runs, `act` is the input to `source_kind`, not a competitor to it.

If the bridge is expected within the window before the first citizen account
exists, this claim can be dropped in favour of the link table. That is a
governance call, not a technical one.

---

## 2. What is BLOCKED, and on what

These are STOP conditions in the AUTH-003 specification, reached honestly.
None was worked around.

### Phase 2 / 3 / 7 — legacy → NIAM bridge, `/login` as canonical, citizen vs organization

**Blocked on: identity evidence that does not exist in this session.**

The ADD stage requires creating NIAM rows. The chain is
`Account.identity_id → IdentityRecord.person_id → niam_persons.id`, so
backfilling an `Account` for an existing `lab_users` row **asserts that a
Person exists**. Phase 8 of this same specification forbids exactly that:
*account creation must not automatically prove identity*, and *Account ≠ Person
≠ Patient*.

Creating those rows would therefore either violate Phase 8, or require identity
proofing semantics that no repository evidence supports. Measured at head:
`niam_persons=0, niam_accounts=0, niam_sessions=0` — there is nothing to
reconcile *against*, and the scratch database holds 6 seeded `lab_users` and 0
`users`, so the production cohort and its collision surface cannot be assessed
from here at all.

**To unblock, two things are needed and neither is a code change:**

1. A production cohort extract — how many `lab_users` and `users` rows exist,
   and how many share an integer id — measured on production, not on a seed.
2. A **collision policy**, which is a governance decision: when a legacy row
   cannot be matched to exactly one Person, does the bridge block, quarantine,
   or create a new Person? The specification's own rule decides the shape —
   *do not auto-merge on same integer id, username, role, `lab_id`, or matching
   non-authoritative fields; if deterministic identity evidence is absent,
   BLOCK the merge* — but the operational handling of blocked rows is a policy
   choice.

### Phase 6 — workspace eligibility (AUTH-F5)

**Blocked on: an open design question, unchanged since AUTH-002.**

`WorkspaceService.list_eligible` consults `owner_account_id`,
`OrganizationRepresentative` and `OrganizationOwnership`, and does **not**
consult `niam_memberships`, though `GET /niam/memberships/me` exists and the
frontend fetches it. The constitution's chain is *membership → workspace →
role*; today membership grants nothing.

Either memberships feed eligibility or their purpose must be stated. Both are
defensible; picking one silently would be inventing platform policy. AUTH-002
recorded the same action — *decide before SWITCH; do not change
`list_eligible` opportunistically* — and it is still undecided.

---

## 3. Phases assessed as needing no change

### Phase 4 — token purpose (AUTH-F6)

AUTH-002 recorded that both stacks call the same `create_token` with the same
`SECRET_KEY`, so separation rests on claim presence rather than on stated
purpose. **That statement was partly wrong and is corrected here:** access and
refresh tokens are signed with *different* secrets (`SECRET_KEY` vs
`REFRESH_TOKEN_SECRET`), so cross-use between the two fails on signature
verification, not on claim inspection. Verified empirically during AUTH-002.

The remaining thinness — a NIAM-shaped access token being cryptographically
valid at a legacy endpoint — is real but does not widen under this change: with
`act` present, a token that does not name an identity table is refused at
resolution rather than searched for. An explicit audience claim remains the
right hardening at the SHADOW stage, and remains not-yet-required.

### Phase 5 — revocation (AUTH-F7)

AUTH-F7 requires logout to honour **both** revocation mechanisms — blacklist
the `jti` *and* deactivate the `niam_sessions` row — "from the first cohort
onward". There is no first cohort: `niam_sessions=0`, because ADD is blocked.
The requirement is correctly deferred with the stage it belongs to.

What AUTH-003 *did* fix here is that legacy revocation now lands on the
identity the token names. `/logout` bumps `perm_version` as the safety net for
a wiped Redis, and it resolved its subject with the same LabUser-first
fallback: a citizen's logout bumped a colliding laboratory user's version
instead — leaving the citizen signed in everywhere and signing an unrelated
laboratory user out. Regression-tested.

---

## 4. Evidence

`backend/tests/test_auth_identity_discriminator.py` — 13 tests, all executed.

| Group | What it proves |
|---|---|
| Mint | staff tokens declare `lab`; an unknown kind is refused at mint time |
| Resolution | with colliding ids (770035 present in *both* tables), a lab token resolves to the lab user and a citizen token to the citizen, with no `lab_id` acquired by collision |
| Fail-closed | unknown `act`, missing subject, and ambiguous legacy id all resolve to `None` |
| Compatibility | an unambiguous legacy token still resolves — live sessions are not invalidated |
| The defect | the previous resolution order is reproduced directly and shown returning the wrong identity, kept as the record of why `act` exists |
| Structural | no mint site builds claims without `act`; no module takes one id to both identity tables |
| Revocation | a citizen logout bumps the citizen and not the colliding laboratory user; the Redis key already separated what the token did not |

**Negative proof** (the tests fail when the fix is removed):

* removing the fail-closed ambiguity branch →
  `AssertionError: an ambiguous legacy token resolved to an identity instead of failing closed`
* restoring the LabUser-first fallback in `mobile.py` →
  `token payloads built without an act discriminator: ['mobile.py:123']` and
  `{'mobile.py': ['user_id']} take one id to both identity tables`

Both restored after measurement.

**Suite:** 2960 passed, 34 skipped (baseline 2956 + 4 new). **Lint:** four
findings across the changed files, all pre-existing and on untouched lines
(2 × E741 and 1 × RUF001 in `citizen_portal.py`, 1 × N806 in `login.py`).

The structural guards are the durable half. NR-035 existed in two places
because the fallback was written twice; a third writing is now a test failure
rather than a discovery.

### CI evidence — the gate executed, it was not merely bound

A local pass is not evidence, and a green pull request is not evidence that a
*particular* file ran: `iam-hardening.yml` runs named test files, so an unbound
test executes nowhere. Read from the "Security and tenant isolation regression"
job log on `97b6a283` (run 34533530656, job 103059794877, Python 3.12.14):

```
collected 89 items
tests/test_security_regression.py .....................                  [ 23%]
tests/test_auth_identity_discriminator.py .............                  [ 38%]
tests/test_tenant_isolation_matrix.py .................................. [ 76%]
...........                                                              [ 88%]
tests/test_clinical_gateway_contracts.py .....                           [ 94%]
tests/test_clinical_gateway_service.py .....                             [100%]
======================= 89 passed, 3 warnings in 36.93s ========================
```

Thirteen dots against the file, on the platform's CI Python rather than the
3.13 used locally. All six checks green on that head. The
`Failed to CreateArtifact: Artifact storage quota has been hit` line in that
log is the known pre-existing quota condition on the evidence-upload step,
which carries `continue-on-error` precisely so archival cannot fail the gate it
documents; the pytest step itself is blocking and passed.

The PostgreSQL migration and schema gate — which carries the widened
schema-fidelity ledger — also concluded success. That step is blocking under
`set -o pipefail`, so its green conclusion is the proof; the counted line for
that job was read at TEST-001.1 and the invocation is unchanged apart from the
ledger contents.

---

## 5. Phase 8 — the Account ≠ Person ≠ Patient boundary, as it stands today

Checked by inspection of the only paths that create an identity today. The
boundary holds:

| Path | Creates | Does **not** create |
|---|---|---|
| `POST /register/citizen` | a `users` row (Account) **and** an MPI `Citizen` with `nid_verified=False`, `is_verified=False` | no `Patient`, no `niam_persons` row |
| `POST /register` (lab) | a `labs` row and an admin `lab_users` row | no Person, no Patient |
| `POST /register/staff`, `/register/doctor` | a `lab_users` / `users` row, `is_verified=False` pending approval | no Person, no Patient |

Self-registration therefore creates a *claim* to an identity, explicitly marked
unproven (`nid_verified=False`), and never a clinical record. This is the
property the bridge must preserve: an `Account` backfill that asserts
`niam_persons` would convert every unproven claim into a proven Person, which
is why AUTH-F10 blocks rather than proceeds.

## 6. Readiness — technical, and separately governance

**Technical readiness** means the code paths exist, execute, and are tested.
**Governance readiness** means someone with authority has decided that they
may be used on real people. AUTH-003 can only report the first.

| Capability | Technical | Governance | Gate |
|---|---|---|---|
| Internal account creation | **GO** | separate decision | `/register/staff` under an authenticated admin; unaffected by AUTH-003 |
| Internal login | **GO** | separate decision | `/login`; NR-035 closed, revocation precise, 2960-test suite green |
| Controlled **citizen** pilot | **NO-GO** | — | not the token defect any more; PUB-005 (citizens routed into the institutional shell) and PUB-006 (Privacy Centre backend unreachable) are unresolved, and PUB-006 is unblocked only by the bridge (AUTH-F10) |
| Controlled **organization** pilot | **CONDITIONAL** | separate decision | works today on legacy auth. AUTH-F5 must be decided first: memberships currently grant nothing, so a pilot would validate a workspace model the platform does not actually enforce |
| Real **patient record** pilot | **NO-GO** | — | out of AUTH-003's scope and unchanged by it. NR-003 (pharmacy primary-key divergence) remains the single true deployment blocker in the master register |
| **Public registration** | **NO-GO** | — | this is the event that makes `users` non-empty. NR-035 was the blocking *identity* defect and is closed; what remains is AUTH-F10 — opening registration creates the exact cohort the bridge has no policy for, at the moment it becomes hardest to migrate |

**The one-sentence position.** Public registration was unsafe for two
independent reasons; AUTH-003 removed one of them (a token could resolve to the
wrong identity table) and left the other untouched by design (there is no
agreed policy for what the resulting accounts become in NIAM). Opening
registration before AUTH-F10 is decided converts a governance question into a
data-migration problem.

**Not claimed.** No statement here asserts compliance with any law, standard,
certification or regulation. No privacy control was represented as working that
this session did not execute.

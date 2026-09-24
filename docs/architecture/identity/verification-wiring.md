# AUTH-005 — Verification Wiring & Registration Gate B

Companion to `verification-architecture.md` (AUTH-004), `ADR-026`,
`auth-identity-hardening.md` (AUTH-003) and `auth-identity-gap-register.md`.

**Status: PARTIALLY VERIFIED.** NR-038, NR-039 and NR-040 are closed and proven.
AUTH-F10 is encoded as policy but no migration is performed. AUTH-F5 is
half-answered: the "not sufficient" half is enforced and tested, the "sufficient
when…" half remains a platform decision.

---

## 1. A correction to AUTH-004

AUTH-004 reported that the verification domain was *"wired to nothing"*. The
test that pinned it was narrower and remains accurate — nothing called
`VerificationRecordService` — but the narrative overstated. One place *read* the
table: `WorkspaceService._professional_eligible` gates professional workspace
creation on a verified, unexpired professional record.

That sharpens the finding rather than softening it. The table had a reader and
no writer, and it holds zero rows, so `_professional_eligible` could only ever
return `False`. **Professional workspaces were unreachable by construction** —
not by policy, by the absence of the other half of the architecture.

---

## 2. NR-039 — contact is not identity, and authorization is not evidence

`CitizenRelationshipService.activate` links an account to a citizen *and a
patient, with a scope*: it is the moment a person's health data becomes visible
to an account. It refused unless the source account was "active and verified",
reading `users.is_verified` — the boolean `/auth/verification/confirm` sets from
a six-digit code delivered to an email address or phone.

Two different facts had been collapsed into one:

| Fact | Established by | Answers |
|---|---|---|
| the operation is authorized | ministry role + `platform:manage_users` | *may this actor do this?* |
| the subject's identity | a verification record, purpose `identity`, ≥ L2 | *who is this person?* |

Both are now required, and **neither substitutes for the other**. The ministry
authorization is unchanged; the identity gate is new.

### The chain, and where it refuses

```
legacy account id + account kind          ← NR-035: the kind is not optional
  → LegacyAccountLink, validated|migrated, exactly one
  → canonical Account
  → VerificationRecord, purpose=identity, verified, live
  → AssuranceEngine recomputes the level from the method
  → identity assurance ≥ L2
```

| Gap | Reason code |
|---|---|
| no mapping to a canonical account | `no_identity_evidence` (PENDING_PROOFING) |
| mapping exists but is `pending`/`collision`/`blocked` | `link_not_validated` |
| more than one validated mapping | `ambiguous_identity` |
| unknown account kind | `unknown_account_kind` |
| no target identity | `no_target_identity` |
| contact-only, OCR/NFC-only, expired or revoked | `insufficient_identity_assurance` |

Every refusal is audited with its reason code and the assurance actually held.

### The stored assurance column is not trusted

`VerificationRecord.assurance_level` exists, and this policy ignores it. The
level is recomputed from the record's **method** through `VerificationPolicy`,
the same policy that scores a live provider response. A column is a cache; the
policy is the authority. A row whose level was stamped by a compromised or buggy
writer cannot raise its own assurance — NR-038's principle applied to data at
rest. Tested directly: a contact record relabelled `identity` with `L3` written
into the column still scores L0.

---

## 3. NR-038 — the client no longer supplies the answer

`POST /niam/trust/assurance-profiles` took `ial`, `aal`, `fal`, `assessed_by`
and `evidence` as caller-supplied parameters and wrote them with
`status="active"`. No verification record was consulted and the caller named its
own assessor.

The route now names a **subject** and nothing else:

* `ial` is derived from the account's identity-purpose assurance
  (L0/L1 → IAL1, L2 → IAL2, L3 → IAL3);
* `aal` and `fal` sit at the floor — neither is derivable from verification
  records, and guessing upward is the substitution AUTH-004 removed;
* `assessed_by` is the authenticated actor, server-side;
* `evidence` records what was derived and from where;
* acting for another account additionally requires an active administrative
  assignment — and even then asserts nothing, because the inputs are evidence
  rather than claims.

`_calculate_overall` no longer averages. Averaging let AAL3 + FAL3 lift an
unproofed IAL1 identity to overall IAL2. **Independent axes do not average**:
the overall is the weakest of the three, because an assurance claim is only as
good as its weakest component.

---

## 4. NR-040 — the writer the architecture never had

`VerificationWorkflow` drives the existing machinery; it does not add a second
subsystem.

```
request()  → a record in `pending`, purpose derived from the method
start()    → `in_progress`, via VerificationRecordService.transition
apply()    → the provider's result, scored by VerificationPolicy
```

Three properties, each tested:

* **Only the state machine reaches `verified`.** `failed → verified` is refused.
* **The provider does not grade its own work.** A provider claiming L3 for an
  emailed code yields contact L1.
* **`NotConnectedProvider` stays fail-closed.** Its `not_connected` result maps
  to `failed` at L0. Nothing here turns it into a stub that passes.

A result for a different method than the record was opened for is refused: the
purpose is fixed when the record is created, so a contact check cannot close an
identity request.

### What is still blocked

The legacy OTP path at `/auth/verification/confirm` **cannot yet write a
record**: `VerificationRecord.account_id` is a non-null foreign key to
`niam_accounts`, and a legacy `users` row has no canonical account until the
AUTH-F10 bridge runs. Wiring it would require creating accounts — which is
exactly what AUTH-F10 blocks. The workflow is therefore usable by any caller
that *has* a canonical account, and retro-fitting the legacy path is queued
behind the cohort decision, not behind more code.

---

## 5. AUTH-F10 — the dispositions, encoded; no migration performed

The four dispositions are the reason codes above, and they are enforced by
`resolve_canonical_account` rather than described in prose:

| Disposition | Encoded as |
|---|---|
| DETERMINISTIC_MATCH | exactly one link in `validated`/`migrated` → proceed |
| NO_IDENTITY_EVIDENCE | no link → refuse, PENDING_PROOFING |
| CONFLICT | link in `collision`/`blocked` → refuse, audited |
| AMBIGUOUS | more than one validated link → refuse |

**Nothing is guessed.** No matching on integer id, username, email, phone, name,
role, `lab_id`, organization or MPI proximity appears anywhere in this path.

A discovery worth recording: the AMBIGUOUS branch is **unreachable through the
database**. The migrated schema carries a unique constraint on
`(source_kind, legacy_account_id)`, so a second mapping cannot be written at
all. The Python branch is defence in depth; the test pins the constraint
instead, because a constraint holds against every writer including ones that
bypass this service.

No bulk migration was performed and no `niam_persons` row was created outside a
rolled-back test transaction.

---

## 6. AUTH-F5 — half answered, and the half that is open is named

**Enforced and tested:** membership is *not* sufficient. `list_eligible` does not
consult `niam_memberships`, so holding one grants nothing. Knowing a
`workspace_id` grants nothing either — `switch` re-derives eligibility rather
than trusting the id.

**Newly enforced:** the organization's own standing. `list_eligible` returned an
organization's workspaces to an active representative **without checking that
the organization was still active**, so a representative of a deactivated
organization kept its workspaces. That is now a conjunction. This change
*narrows* access, which is why it was safe to make here.

**Still open — a platform decision, not a code gap.** The constitution's chain is
*membership → workspace → role*. Today membership is a parallel concept that
grants nothing. Making it confer eligibility would hand access to every member
of every organization the moment it is wired, so it is not a change to make
silently. The remaining factors (an organization *verification record*, a
required professional credential per workspace type) are all expressible with
existing models — `VerificationRecord` already carries `organization` and
`professional` purposes — so the blocker is the decision, not the schema.

The "all required conditions → YES" case is therefore **not implemented**, and
this batch is PARTIALLY VERIFIED on that account rather than claiming otherwise.

---

## 7. The five boundaries

| Boundary | Held by |
|---|---|
| Account verified ≠ Identity verified | `can_link_health_identity` requires purpose `identity` ≥ L2 |
| Identity verified ≠ Patient | linkage additionally requires a deterministic target and an authorized actor |
| Ministry authorization ≠ Identity evidence | both required at activation; refusal audited with its reason |
| Membership ≠ Workspace eligibility | `list_eligible` does not consult memberships |
| Client input ≠ Assurance result | the route accepts no level, assessor or evidence |

---

## 8. Evidence

`backend/tests/test_identity_link_and_assurance.py` — 17 tests, **on the
migrated PostgreSQL schema**, not `create_all`. The identity tables are
deliberately absent from conftest's metadata list, which is TEST-001's rule
working as designed: a green test must never mean "the ORM can create this
table". Real foreign keys and the real unique constraint are exercised.

**Negative proof, per control.** An earlier draft of this section removed two
changes together and attributed the resulting six failures to both. That was
imprecise, and the finalization pass isolated them. One of the two — reading
`result.assurance` instead of ignoring it — is *inert on its own*, because
`VerificationPolicy.assurance_for` never consults that field. The control is the
policy, not the field. Measured separately:

| Control removed | Tests that fail |
|---|---|
| `VerificationPolicy.assurance_for` ignoring the self-reported level | **10**, incl. `test_a_provider_cannot_declare_its_own_assurance`, `test_receiving_a_code_proves_contact_and_nothing_further`, `test_the_whole_lifecycle_…` |
| the identity threshold in `can_link_health_identity` | **9**, incl. `test_contact_verification_alone_cannot_link_health_identity`, `test_the_stored_assurance_column_cannot_raise_itself`, `test_a_refused_linkage_is_audited_with_its_reason` |
| the identity-evidence gate in `activate()` | **2**, incl. `test_activation_is_refused_without_identity_evidence` |

Each restored after measurement; the tree was verified clean between runs.

The four AUTH-004 defect-pinning tests failed on this change — which is what
they were written to do — and are rewritten to pin the resolutions rather than
deleted.

**Suite:** 2996 passed, 34 skipped (baseline 2977 + 19 new). **Lint:** clean.

---

## 9. Readiness

Technical only. **Governance and operational GO are separate decisions this
batch cannot make**, and no claim of legal compliance, certification or
government authorization is made anywhere in this document.

| Capability | Technical |
|---|---|
| Citizen account registration | **GO** |
| Citizen login | **GO** |
| Citizen account (contact) verification | **GO** |
| Citizen identity verification | **CONDITIONAL** — the workflow exists and is proven; no identity-L2 *method* is connected, and the legacy path cannot write records until AUTH-F10 |
| Health identity creation | **NO-GO** — requires identity verification above |
| Patient record link | **NO-GO** — `national_patients` does not exist (NR-022); the relationship's `patient_id` has no foreign key because its target table was never built |
| Controlled citizen pilot | **NO-GO** — PUB-005, PUB-006 |
| Organization registration | **CONDITIONAL** — accounts and workspaces work; no organization verification evidence exists |
| Organization verification | **NO-GO** — no connected method |
| Professional workspace access | **CONDITIONAL** — the gate is correct and a writer now exists; no professional registry is connected |
| Controlled organization pilot | **CONDITIONAL** — decide AUTH-F5 first |
| Public registration | **NO-GO** — AUTH-F10 |
| Real patient record pilot | **NO-GO** — NR-003 remains the deployment blocker |

**Gate B (citizen identity verification) moved from NOT MET to CONDITIONAL.**
The machinery to prove identity now exists end to end and is tested; what is
missing is a connected authority to prove it *against*, and the cohort decision
that lets legacy accounts reach it.

---

## 10. CI evidence

Bound to the **PostgreSQL migration and schema gate**, not the SQLite security
job: these tests need the migrated schema, and running them anywhere else would
defeat their purpose.

All six checks green on `27bd108c` (run 34569128113, job 103167272498, Python
3.12.14, PostgreSQL 16.4). The proof that the new file executed came from an
unusually direct place — the job's PostgreSQL **service container log**:

```
2026-09-11 06:16:33.894 UTC [133] ERROR:  duplicate key value violates unique
    constraint "uq_niam_legacy_account_link_source"
2026-09-11 06:16:33.894 UTC [133] DETAIL:  Key (source_kind, legacy_account_id)
    =(user, 880053) already exists.
2026-09-11 06:16:33.894 UTC [133] STATEMENT:  INSERT INTO
    niam_legacy_account_links (...) VALUES ('user', 880053, 'acct-dup-a',
    'fp-dup-b', 'validated', ...)
```

Those are this suite's own fixture values — legacy id `880053`, account
`acct-dup-a`, fingerprint `fp-dup-b` — from
`test_the_schema_makes_a_second_mapping_impossible`. The database refused the
second mapping in CI, on the real migrated schema, and the test passed because
it refused.

That is better evidence than a passing count. A count says a file ran; this says
the control being relied upon is the *database's*, enforced against any writer,
including one that bypasses `resolve_canonical_account` entirely.

The `Failed to CreateArtifact` line in that log is the known storage-quota
condition on the evidence-upload step, which carries `continue-on-error` so
archival cannot fail the gate it documents. The pytest step is blocking and
passed, as did `alembic downgrade` and the re-upgrade to head after it.

---

## 11. Finalization — what Phase 2 uncovered (NR-044)

AUTH-005's finalization required proving server-authoritative assurance *at the
service and database level* rather than by reading a signature. Attempting that
showed why the signature was all there was to read.

`get_db` yields a synchronous `sqlalchemy.orm.Session`. Thirty-six modules under
`app/identity/` annotate `AsyncSession` and `await session.execute(...)`, and
**no `create_async_engine` exists anywhere in `app/`**. Measured:

```
get_db is async generator?  False
get_db yields:              Session
await session.execute(text("SELECT 1"))
  -> TypeError: object ChunkedIteratorResult can't be used in 'await' expression
```

The NIAM async service layer — the trust/assurance routes, workspace
eligibility, membership, the repositories — therefore **cannot execute at
runtime**. Recorded as **NR-044 (P1)**.

This reframes two findings rather than excusing them:

* **NR-038 was never exploitable.** The route raised before a row could be
  written, so a client-authored assurance level could not be persisted.
  "Latent behind NIAM authentication" was too generous; it is latent behind a
  type error. Removing the client's authorship remains correct and is still
  pinned — but the *behavioural* proof this batch asked for cannot be produced
  for that path, so **NR-038 is PARTIALLY VERIFIED**, not VERIFIED.
* **NR-043 / AUTH-F5** narrow a function that cannot currently run. Correct
  code, unexecutable today. Also **PARTIALLY VERIFIED**.

What *does* run is the half with clinical consequences.
`CitizenRelationshipService`, `identity_link_policy` and `verification_workflow`
are synchronous end to end — route, workflow, policy, writer — and are proven
against migrated PostgreSQL. **NR-039 and NR-040 stand as VERIFIED**, and they
are the ones guarding patient data.

`backend/tests/test_identity_platform_runtime.py` pins all of this, including
the `TypeError` itself, probed with `SELECT 1` so the proof does not depend on
which schema is bound.

### Consequence for AUTH-F5's behavioural tests

The six workspace-eligibility cases this batch asked for (member without
assignment, inactive membership, missing credential, expired credential, valid
member, unauthorized switch) **cannot be executed** while `list_eligible` and
`switch` cannot run. The invariants that are statically provable are pinned —
`list_eligible` does not reference `Membership`, and `switch` re-derives
eligibility rather than trusting a `workspace_id` — and the behavioural cases
are blocked on NR-044, not on the data model. Every factor they need is
expressible with existing tables.

## 12. Final control matrix

| Control | Status | Evidence |
|---|---|---|
| Account/contact verification | **VERIFIED** | `/auth/verification` unchanged; contact L1 proven per purpose |
| Identity evidence | **VERIFIED** | `VerificationWorkflow` writes records through the state machine; migrated-PostgreSQL tests |
| Server-side assurance | **VERIFIED** (sync path) | policy overrides self-reported level; removing it fails 10 tests |
| **NR-038** | **PARTIALLY VERIFIED** | client authorship removed and pinned; route unexecutable (NR-044) |
| **NR-039** | **VERIFIED** | `can_link_health_identity`; 20 tests; 9-test negative proof; audited denial |
| **NR-040** | **VERIFIED** | writer exists, drives the state machine, persists rows |
| **AUTH-F5** | **PARTIALLY VERIFIED** | "not sufficient" pinned statically; behavioural cases blocked by NR-044 |
| **AUTH-F10** | **ENCODED, NOT EXECUTED** | four dispositions as refusal codes; unique constraint proven in CI; no migration |
| **NR-035** | **VERIFIED, INTACT** | `test_auth_identity_discriminator.py` green in the focused run |
| Token purpose / revocation | **VERIFIED, INTACT** | `test_security_regression.py` green |
| Relationship activation | **VERIFIED** | identity evidence + ministry authorization both required |
| Workspace eligibility | **PARTIALLY VERIFIED** | narrowed correctly; unexecutable (NR-044) |
| Audit | **VERIFIED** | canonical `log_action`; request/verify/revoke and refusals asserted from `audit_logs` |
| PostgreSQL proof | **VERIFIED** | identity tables absent from `create_all` by design; real FKs and constraints exercised |
| CI | **VERIFIED** | bound to the existing PostgreSQL migration gate; no new job, no `continue-on-error` |

### Can it be done safely today?

| Question | Answer |
|---|---|
| Register a citizen account safely? | **Yes** (technical) |
| Identity-verify that account? | **Yes, mechanically** — the workflow persists real evidence. But no identity-L2 *method* is connected, and the legacy OTP path cannot write a record until AUTH-F10, so in practice **no** |
| Link it to a real Citizen/Patient? | **No.** `national_citizens` and `national_patients` do not exist (NR-022); the relationship's `citizen_id`/`patient_id` have no foreign keys because their targets were never built |
| Register an organization account safely? | **Yes** (technical) |
| Can an authorized member reach its workspace? | **No** — `list_eligible` cannot execute (NR-044) |

Technical GO is not governance GO and is not operational GO. No claim of legal
compliance, certification or government authorization is made here.

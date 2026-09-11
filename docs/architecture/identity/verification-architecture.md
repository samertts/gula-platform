# AUTH-004 — Identity Verification & Assurance Architecture

Companion to `auth-identity-model.md`, `auth-identity-bridge-decision.md`,
`auth-identity-hardening.md` (AUTH-003) and `auth-identity-gap-register.md`.

**Status: PARTIALLY VERIFIED.** A discovery and architecture batch. One
architectural defect was fixed because nothing consumed it yet and the next
consumer would have inherited it; three further defects are recorded with
evidence and pinned by tests rather than patched, because each needs a policy
decision this session cannot make.

---

## 1. The finding that reframes the batch

GULA already has a verification architecture. It is more complete than the
brief assumes, and it is connected to nothing.

| Component | State |
|---|---|
| `niam_verification_records` | migration-backed (`20260814_0001`), physically present, **0 rows** |
| `VerificationRecord` model | method, provider, purpose, assurance, expiry, revocation, confidence, failure code — **no raw payload** |
| `VerificationRecordService` | 8-state machine with an explicit legal-transition table |
| `IdentityVerificationProvider` | provider-neutral `Protocol` |
| `NotConnectedProvider` | explicit safe adapter; **never claims success** |
| `AssuranceEngine` | central server-side evaluator |
| Unit tests | `test_verification_phase3.py`, `test_verification_hardening_phase3.py` |
| **Production callers** | **none** |

Nothing in `app/` constructs a `VerificationRecord`, calls
`VerificationRecordService`, instantiates `NotConnectedProvider`, or asks
`AssuranceEngine` anything. Recorded as **AUTH-V4**.

Meanwhile the verification the platform *does* perform writes to a single
boolean, `users.is_verified`, which two different paths set for two different
reasons. So the answer to "what does GULA know about this person?" is stored in
the one place that cannot express it, while the model designed to express it
stays empty.

This is the same shape as NR-036: something green and well-formed that nothing
exercises. The remedy is the same — make the gap visible and testable before
building on top of it.

---

## 2. Canonical entity model (Phase 1)

Existing owners, not new ones:

```
Account            users / lab_users            (legacy, INTEGER pk, discriminated by `act` — NR-035)
  │                niam_accounts                (Identity Platform, String(26))
  ▼
Identity           niam_identities
  ▼
Person             niam_persons                 ← asserting one is asserting proofing (AUTH-F10)
  ▼
Health Identity    mpi Citizen (canonical ULID) ← nid_verified, today only ever False
  ▼
Patient            patients                     ← clinical record, lab-scoped
```

and independently:

```
Person → Professional Credential → Organization Membership
       → Assignment → Workspace Eligibility → Role → Authorization
```

**Invariants, and where each is enforced today**

| Invariant | Enforced? |
|---|---|
| Account ≠ Person | yes — registration creates no `niam_persons` row |
| Account ≠ Patient | yes — registration creates no `Patient` |
| Authentication ≠ Identity Proofing | **no** — one boolean serves both (AUTH-V3) |
| Identity Proofing ≠ Authorization | yes — RBAC/ABAC is separate |
| Membership ≠ Workspace Eligibility | yes, by omission — membership grants nothing (AUTH-F5, undecided) |
| Civil/National ID ≠ GULA Health ID | yes — `national_id` (encrypted) vs MPI `citizen_ulid` |
| Professional Credential ≠ Account | yes — `VerificationRecordType.professional` is separate |

---

## 3. Verification purposes (Phase 2) — and the defect they expose

The brief asks for seven purposes. The platform already names four of them on
the record model, and they are the right four:

| Purpose | Question | Record type |
|---|---|---|
| **contact** | can the holder receive at, and control, this address? | `contact` |
| **identity** | who is the real-world person? | `identity` |
| **professional** | is this person licensed to practise? | `professional` |
| **organization** | is this organization real and eligible? | `organization` |

The brief's remaining three are *not* verification purposes and must not become
record types:

* **Health Identity link** and **Patient link** are consequences of identity
  assurance plus a clinical event, decided by policy — not evidence gathered.
* **High-assurance operation** is a *requirement* an operation states, answered
  by the profile below.

**The defect.** `users.is_verified` is one boolean written by two paths that
mean different purposes:

| Path | What actually happened | What it writes |
|---|---|---|
| `POST /auth/verification/confirm` | a 6-digit code sent to an email or phone was returned | `user.is_verified = True` |
| `PUT /admin/citizens/{id}/verify` | a ministry admin asserts "identity confirmed" | `citizen.is_verified = True` |

Nothing records which occurred. Recorded as **AUTH-V3**.

It bites downstream: `CitizenRelationshipService.activate()` — which links an
account to a citizen and a patient *with a scope*, i.e. grants sight of health
data — refuses unless the source account is "active and verified", reading the
boolean an OTP sets. Activation is ministry-authorized (`platform:manage_users`
plus a ministry role), so this is a **misinformed human decision**, not a
self-service escalation. That is why it is recorded and tested rather than
silently re-gated: *what assurance a ministry actor must have before linking
health data is a policy decision, not a patch.*

---

## 4. Assurance model (Phase 3) — fixed in this batch

### What was wrong

Assurance was a single ladder L0–L5, and `AssuranceEngine.level_for()` took the
**maximum** across all results. Measured:

```
level_for(organization verification only) = L4
require(..., L2)  →  PASSED
```

L2 is `official_identity`. So an account whose *employer* was verified
out-ranked one whose *holder's identity* was proven, and any caller asking for
"at least L2 — we know who this person is" was satisfied by an organization
check. The ladder contradicted the record model, which had the four purposes
separated correctly all along.

A second vocabulary had the same defect in different notation:
`AssuranceService._calculate_overall` **averages** IAL, AAL and FAL. Measured:

```
IAL1 + AAL3 + FAL3  →  overall IAL2
```

A hardware key and a strong federation lift an identity that was never proofed.

### What it is now

Assurance is a **profile**, not a scalar — a level per purpose:

| Level | Means | Reached by |
|---|---|---|
| **L0** | nothing established | any non-verified status; OCR; NFC |
| **L1** | a self-asserted channel was demonstrated | email, phone |
| **L2** | an authoritative source was consulted | `official_identity`, `professional_registry`, `organization_registry` |
| **L3** | in-person or government-attested | **no method reaches it** — reserved so a future high-assurance operation has somewhere to point that today's methods cannot satisfy |

Four levels, applied per purpose. L4/L5 are gone: they existed only to rank
organization and professional checks above identity proofing on one ladder.

`require(results, purpose, required)` — the purpose is **mandatory**. A caller
that does not say which question it is asking gets a `TypeError` at the call
site rather than a number meaning something other than it assumed. That is the
fail-closed property that makes the fix worth making now: there are zero
consumers today, so the first one cannot inherit the defect.

`nid_verified`, `national_biometrics.is_verified`, and the rest stay as they
are; this batch adds no column.

---

## 5. Verification method matrix (Phase 4)

Assurance is stated as (purpose, level). **Decision** is the Phase-25 verdict.

| # | Method | Purpose / Level | Proves | Does **not** prove | Retained | Internet | Offline | External dep. | Cost | Decision |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **Email code** | contact L1 | control of an inbox | who the person is | result + timestamp | yes | queue only | SMTP | free (self-hosted) | **REQUIRED NOW** |
| 2 | **Phone code (SMS)** | contact L1 | control of a number at one moment | who the person is; SIM-swap resistant | result + timestamp | yes | no | **SMS vendor** | per-message, recurring | **OPTIONAL** |
| 3 | **Passkey / WebAuthn** | — (authentication, not proofing) | possession of a device-bound key | who the person is | public key, sign count | no (local ceremony) | yes | none | free | **REQUIRED NOW** for staff; **REQUIRED LATER** for citizens |
| 4 | **TOTP** | — (authentication) | possession of a shared secret | who the person is | encrypted secret | no | yes | none | free | **REQUIRED NOW** (staff) |
| 5 | **Recovery codes** | — (authentication fallback) | possession of a one-time code | who the person is | hashes | no | yes | none | free | **REQUIRED NOW** |
| 6 | **Government identity API** | identity L2 | an authority asserts the identity | continued validity | assertion ref + expiry | yes | no | **MoI** | unknown | **BLOCKED PENDING EXTERNAL INTEGRATION** |
| 7 | **Civil/national document check** | identity L2 (with an authority) | a document was presented | that it is genuine, alone | reference + expiry | depends | partial | varies | varies | **REQUIRED LATER** |
| 8 | **NFC document read** | identity L0 today | a chip was read | authenticity, without signature validation | reference | no | yes | NFC handset | free (device) | **OPTIONAL** |
| 9 | **OCR** | identity L0 | text was extracted | authenticity | extracted fields only | no | yes | local engine present | free | **OPTIONAL** |
| 10 | **Face matching** | identity — | a face resembles a photo | who the person is, alone | template (avoidable) | varies | varies | varies | varies | **NOT JUSTIFIED** |
| 11 | **Liveness** | identity — | a live human is present | who they are | video/template | usually | no | vendor | recurring | **NOT JUSTIFIED** |
| 12 | **Manual / in-person** | identity L2–L3 | a trusted official saw the person | anything unrecorded | officer id + reference | no | **yes** | none | staff time | **REQUIRED NOW** |
| 13 | **Organization licence** | organization L2 | the entity is licensed | who its staff are | licence ref + expiry | yes | no | registry | varies | **REQUIRED LATER** |
| 14 | **Professional registry** | professional L2 | a licence exists | that this human holds it | licence ref + expiry | yes | no | registry | varies | **REQUIRED LATER** |
| 15 | **Trusted institutional identity** | identity L2 | an employer vouches | independence from that employer | attestation ref | yes | no | the institution | free | **REQUIRED NOW** (Cohort 0/1) |

Methods 3–5 appear with no purpose deliberately: **they are authentication, not
proofing** (Phase 16). They belong in a token/session decision, never in an
assurance profile.

**Minimum stack, no paid services:** email code (contact L1) + TOTP/passkey
(authentication) + recovery codes + manual in-person or institutional
attestation (identity L2). Every element is free, self-hostable and already
present in the repository except the wiring.

---

## 6. Biometrics (Phase 10) — NOT JUSTIFIED

1. *What problem does it solve?* Binding a document to the presenter at a
   distance — only needed for **remote unsupervised** identity proofing.
2. *Stronger evidence?* Only against an attacker holding someone else's genuine
   document. A government assertion (method 6) removes that need entirely by
   not relying on document presentation.
3. *Can government verification replace it?* **Yes** — and it is the preferred
   path (Phase 12).
4. *Can NFC replace document capture?* Partly — chip signature validation would
   raise NFC from L0 to L2 **without any biometric**.
5. *Without biometrics?* Yes: methods 6, 12 and 15 all reach identity L2.
6–8. *No NFC / poor camera / failure?* Fall back to method 12 (in-person),
   which needs no device at all — the decisive argument in Iraqi field
   conditions.
9. *Fallback?* In-person, always.
10–11. *Retention?* A template is a lifelong identifier that cannot be
   reissued after a breach. **GULA should retain none.**

`national_biometrics` is declared with a `data_url` pointing at raw biometric
data. It is **not built** (part of NR-022's unbuilt National Core). Recorded as
**AUTH-V7**: redesign before it is ever migrated; a URL to raw biometrics is the
repository Phase 17 says not to create.

---

## 7. SMS (Phase 11) — OPTIONAL, never load-bearing

SMS proves control of a number at one instant. It is not identity, is defeated
by SIM swap, costs per message forever, and depends on carriers unreachable
during outages. Email reaches the same contact L1 for free.

**Rule:** phone may be *a* contact factor and *a* recovery factor. It must never
be the only route to account control, and no identity assurance may derive from
it. GULA's architecture must survive SMS being unavailable — today it does,
because `/auth/verification` accepts either channel.

---

## 8. Government integration boundary (Phase 12)

The boundary already exists and is well-built: `app/gateways/mode.py` gives every
external adapter **STUB / LIVE / SHADOW**, defaulting to STUB, falling back to
STUB when credentials are absent. `national_identity_gateway` is
`DataTrustLevel.NON_CRITICAL` and documents that clinical decisions must use
internal records only.

Critically, `POST /national-id/verify` **refuses with 503 in production while
the adapter is STUB** rather than returning a synthetic pass. That is the
correct failure mode and must not be relaxed.

```
Citizen → GULA → authorized government verification → verified assertion → GULA identity
```

GULA stores the **assertion**, never a copy of the government's database.

| Concern | Rule |
|---|---|
| Minimum data | the identifier queried and a yes/no plus assertion reference |
| Evidence | reference + authority + timestamp + policy version + expiry |
| Failure / timeout | verification stays `pending`; **never** a downgrade to a locally-decided pass |
| Provider unavailable | fall back to method 12, at the assurance method 12 earns — not the assurance the API would have given |
| Provider compromise | revoke by provider + date range; `revoke()` already drops assurance to L0 |

No API is invented here and no fake service is built.

---

## 9. Offline boundary (Phase 13)

| Offline | Online only |
|---|---|
| account UI, cached low-risk state | authoritative identity proofing |
| queueing a verification request | any government verification |
| passkey/TOTP ceremonies (local) | raising an assurance level |
| **in-person proofing captured for later submission** | linking Health Identity or Patient |

The invariant: **offline state may record that evidence was collected; it may
never compute an assurance level.** A queued in-person verification arrives as
`pending` and is raised by the server when it syncs.

---

## 10. Identity, duplicates and collisions (Phases 6, 7)

Compatible with NR-035 and extending it from tokens to identities.

Never sufficient to link or merge, alone or combined: integer id, username,
name, phone, email, role, `lab_id`, organization, or any matching
non-authoritative field.

```
deterministic authoritative evidence present → VALIDATE → AUDIT → LINK
evidence absent or ambiguous                 → BLOCK (never guess)
disputed                                     → REVIEW (human), stays BLOCKED meanwhile
```

`LegacyAccountLink` already models `pending / validated / migrated / collision /
rolled_back / blocked`, and the MPI already refuses to auto-merge on weak
fields. The policy above is what those states are *for*; AUTH-F10 blocks
because nobody has yet decided the operational handling of `collision`.

---

## 11. State machine (Phase 8)

One machine, already implemented in `VerificationRecordService.LEGAL_TRANSITIONS`:

```
not_started → pending → in_progress → verified | failed | requires_review
verified    → expired | revoked            (terminal)
failed      → pending                       (retry)
requires_review → verified | failed
```

Invalid transitions raise `InvalidVerificationTransition` — fail closed.
`expired` and `revoked` set assurance to L0 and `is_active=False`.

Each transition already records actor, timestamps, method, assurance, provider
reference and failure code on the record. **Missing: `policy_version`.** Without
it a record verified under an old policy cannot be re-evaluated when the policy
changes. Recorded as a gap; not added here, because adding a column is a schema
change and Phase 22 forbids unnecessary ones in this batch.

---

## 12. Evidence and retention (Phases 9, 17)

The model is already right, and this is the part of the existing design most
worth preserving: `VerificationRecord` stores *"canonical, minimal verification
evidence; never a raw provider payload."*

**Store:** result, purpose, method, provider/authority, assurance, timestamps,
expiry, opaque provider reference, failure reason code, and `verified_attributes`
scoped by `attributes_purpose`.

**Never store:** document images, biometric templates, raw provider payloads, or
national identity data beyond what `patients.national_id` already holds
encrypted.

```
Verify → store minimum proof → discard raw evidence
```

---

## 13. Recovery and re-verification (Phases 14, 15)

**Recovery invariant:** recovery may restore *access*; it may never restore
*assurance*.

```
lost factor → recover account access → assurance for the affected purpose drops
            → restricted operations → re-verify → privileges restored
```

Concretely: recovering an account must not leave an identity-L2 profile
standing when the proof that established it can no longer be relied on. The
record service already implements the mechanism — `revoke()` drops assurance to
L0 and deactivates. What is missing is a recovery flow that calls it.

**Re-verification is risk-based, never periodic for its own sake.** Triggers:
document or licence expiry (already modelled as `expires_at`), credential
revocation, a recovery event, a disputed identity, or a specific
high-assurance operation. A calendar alone is not a trigger.

---

## 14. Threat / control matrix (Phase 18)

| Threat | Control | Detection | Residual |
|---|---|---|---|
| Fake account | contact L1 + rate limiting | registration velocity | high — contact assurance is cheap by design |
| Account takeover | MFA (staff), `perm_version` revocation, `jti` blacklist | login protection | **citizens have no second factor** (AUTH-V6) |
| Identity theft | identity L2 requires an authority | audit of L2 grants | high until method 6 or 12 is wired |
| Synthetic identity | no auto-merge on weak fields | MPI review queue | medium |
| Duplicate identity | BLOCK on ambiguity | `collision` state | medium — no operational policy yet (AUTH-F10) |
| Document forgery | authority attestation, not appearance | — | resolved by design (OCR/NFC stay L0) |
| Replayed verification | `verification_session_id` unique; one-way state machine | duplicate session ids | low |
| Compromised provider | revoke by provider + date range | — | medium — no bulk revoke helper |
| **Client-asserted assurance** | **none** | — | **AUTH-V1 — open** |
| Insider abuse | ministry-role gating, hash-chained audit | audit chain | medium |
| Recovery abuse | assurance must drop on recovery | — | **no recovery flow exists yet** |
| Organization impersonation | organization L2 via registry | — | high until method 13 |
| Credential forgery | professional L2 via registry | — | high until method 14 |
| Cross-tenant identity access | `lab_id` filtering; NR-035 discriminator | tenant isolation suite | low |
| Identity collision | fail closed (NR-035, proven) | error logs | **low — closed** |

---

## 15. Cohort readiness (Phase 19)

| | Cohort 0 internal | Cohort 1 controlled pilot | Cohort 2 expanded | Cohort 3 general |
|---|---|---|---|---|
| Account | admin-created | admin-created | invitation | self-registration |
| Contact | L1 email | L1 email | L1 | L1 |
| Identity | L2 institutional attestation | L2 in-person | L2 in-person or government | L2 government |
| Authentication | TOTP/passkey (staff) | + citizen second factor | + passkey default | + passkey default |
| Health Identity | not created | on identity L2 only | on identity L2 | on identity L2 |
| Patient record | none | existing records only | + new, on clinical event | as Cohort 2 |
| Recovery | admin-mediated | admin-mediated | self-service + assurance drop | as Cohort 2 |
| Organization | none | L2 manual attestation | L2 registry | L2 registry |
| Professional | none | L2 manual attestation | L2 registry | L2 registry |

---

## 16. Public registration gates (Phase 20)

Technical gates only. **Governance and operational GO are separate decisions
this batch cannot make**, and no claim of legal compliance, certification or
government authorization is made anywhere in this document.

| Gate | Requires | Status |
|---|---|---|
| **A** Citizen account registration | contact L1; account ≠ identity enforced | **MET** |
| **B** Citizen identity verification | purpose-scoped assurance; an identity-L2 method wired; verification records written | **NOT MET** — AUTH-V4 (nothing writes records), AUTH-V3 (boolean conflation) |
| **C** Health ID creation | B, plus a policy for when identity L2 justifies a Health Identity | **NOT MET** |
| **D** Patient record creation | C, plus a clinical event; never automatic | **NOT MET** |
| **E** Real clinical record access | D, plus AUTH-F5 decided and credential expiry enforced | **NOT MET** |
| **F** Organization registration | organization L2 method | **NOT MET** |
| **G** Organization production access | F + AUTH-F5 | **NOT MET** |
| **H** Professional workspace access | professional L2 + expiry/revocation enforcement | **NOT MET** |
| **I** Nationwide rollout | all of the above + AUTH-F10 + NR-003 | **NOT MET** |

**Gate A is met and gate B is not.** That is the whole position: GULA can create
accounts safely today and cannot yet prove who holds them. Opening public
registration before B converts every unproven account into a migration problem
at exactly the moment AUTH-F10 has no policy for it.

---

## 17. Evidence

`backend/tests/test_identity_assurance_boundaries.py` — 15 tests, plus four
rewritten in `tests/identity/`.

| Group | What it proves |
|---|---|
| Vocabulary | the purposes the record persists are the purposes the policy scores |
| Substitution | organization and professional checks never raise identity assurance; a code proves contact and nothing further |
| Capture ≠ attestation | OCR and NFC stay at L0 for identity |
| Provider honesty | a provider cannot declare its own level; any non-verified status carries L0 whatever it claims |
| State machine | `failed → verified` is refused; revocation drops assurance to L0 and deactivates |
| Registration | `/register/citizen` creates no Patient and no Person, and marks both its claims unproven |
| Defects | AUTH-V1/V2/V3/V4 each pinned with the evidence that identifies them |

**Negative proof.** Folding `organization_registry` back onto the identity
purpose — the exact shape of the original defect — fails two tests:

```
assert VerificationPolicy.purpose_for(method) == purpose
E   AssertionError: assert <...identity: 'identity'> == <...organization: 'organization'>
assert AssuranceEngine.level_for(results, VerificationPurpose.organization) == AssuranceLevel.L2
E   AssertionError: assert <AssuranceLevel.L0: 'L0'> == <AssuranceLevel.L2: 'L2'>
```

Restored after measurement.

**Suite:** 2977 passed, 34 skipped. **Lint:** clean on every changed file.

**CI evidence.** The defect-pinning tests are worth nothing unless they run, and
this workflow executes *named files* — so the suite was bound into the
security-regression job and the job log read on `6a8c5c42` (run 34546587086,
job 103100431515, Python 3.12.14):

```
======================= 104 passed, 3 warnings in 39.39s =======================
```

The same invocation collected 89 on the previous head; 104 − 89 = 15, exactly
the number of tests in the new file, and a named file that failed to collect
would have failed the step rather than passing it. All six checks green on that
head. The `Failed to CreateArtifact` line is the known storage-quota condition
on the evidence-upload step, which carries `continue-on-error` precisely so
archival cannot fail the gate it documents; the pytest step is blocking and
passed.

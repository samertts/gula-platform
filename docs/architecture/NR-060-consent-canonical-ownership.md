# NR-060 — Consent: canonical ownership

**Status:** DECIDED. Canonical owner established; no consent code changed.
**Unblocks:** NR-050's last blocked disposition (`healthcare_consent`).
**Guard:** `backend/tests/test_consent_canonical_ownership.py` (5 tests, gated in the IAM job).

## 1. What the problem actually was

NR-051 recorded consent as "7 tables, 6 domains" and left it BLOCKED. Measured
against the layer that decides truth, that framing is right about the count and
wrong about the kind of problem.

**No two consent implementations share a table.** The persistence layer is
828/828 canonical and consent is not an exception to it. What exists is eight
different concepts sharing an English word:

| Table | Owner | Migration | Registered surface |
| --- | --- | --- | --- |
| `consents` | `models.consent.Consent` | `20260417_0001` | `/consent/{grant,revoke,check}` |
| `niam_consents` | `identity.models.consent.NiamConsent` | `20260814_0006` | `/niam/consents*` |
| `niam_lifecycle_consents` | `identity.lifecycle.models.ConsentRecord` | `20260723_0002` | `/niam/lifecycle/citizen/{id}/consent` |
| `trust_consent_records` | `trust.models.ConsentRecord` | `20260716_0013` | `/api/v1/trust/consent*` |
| `dp_consent_directives` | `national_data…ConsentDirective` | **none** | `/national-data/consent-directives` |
| `national_consents` | `national.domain.consent.Consent` | **none** | none (`national_router` unregistered) |
| `rp_consent_records` | `research_platform.base.ConsentRecord` | **none** | `/research/privacy/consent` |
| *(not an ORM model)* | `citizen_platform.privacy.ConsentEngine` | n/a | `/citizen-platform/consents/{citizen_id}` |

Only **four of seven** tables physically exist. The three that do not are
already declared in `test_schema_fidelity`'s unbuilt ledger, so they are visible
there rather than hidden here.

## 2. The decision, and what decided it

**Canonical owner: `app/models/consent.py::Consent` over table `consents`,**
written through `app/services/consent_service.py`, enforced by
`app/security/consent_dep.py::require_consent`.

This is not a preference between eight designs. Of the eight, **exactly one is
wired into an authorization decision**:

- `require_consent(scope)` is a FastAPI route dependency. It guards
  `services/mpi/api.py:316` — a citizen read.
- It resolves consent by querying `consents`: subject `gpid`, actor
  `grantee_id`, `scope`, `status='active'`, `expires_at > now`.
- It writes an audit row through `log_access_decision` on **all five** decision
  branches: owner bypass, emergency denied (non-doctor), emergency allowed,
  no-consent deny, and allow.

Every other implementation is read and written only by its own endpoints. None
of them is consulted by an access check anywhere in the repository.

Supporting evidence, in order of weight:

1. **Enforcement.** Above. The store authorization consults is the canonical one
   by definition; the rest are records of intent.
2. **Audit.** It is the only implementation that leaves evidence of a *denial*.
   A consent gate that allows without auditing is worse than no gate, because it
   looks like one.
3. **Invariants.** `expires_at` is NOT NULL (no open-ended consent, API caps at
   72h), status is one-way `active → revoked/expired`, and
   `(gpid, grantee_id, scope, status)` is unique so overlapping active grants
   cannot exist. No PII — ULIDs, scopes and timestamps only.
4. **Break-glass.** Doctor-only emergency access, audited loudly, with review
   mandatory. A real clinical requirement none of the others carry.
5. **Age.** Migration-backed since `20260417_0001`, continuously present.

## 3. What is NOT being consolidated, and why

Merging the other implementations into `consents` is **not** recommended and was
not done. They are different relations, not copies:

- `niam_consents` — account-to-account grants (`subject_account_id` →
  `grantee_account_id`). Its subject is an *account*, not a citizen.
- `niam_lifecycle_consents` — keyed on `person_id`, part of identity lifecycle.
- `trust_consent_records` — keyed on `patient_id` and **the only tenant-scoped
  one** (`lab_id`). The canonical store has no tenant column, correctly: it is a
  national register keyed on citizen ULID. That divergence is real and worth
  stating rather than flattening.

Collapsing these would be an irreversible data decision with no evidence
requiring it. The brief reserves those.

## 4. Two dormant hazards — guarded, not executed

### 4.1 `ConsentEnforcementService` is fail-open

`app/national/security/consent_enforcement.py` returns
`ConsentCheckResult(granted=True)` for **any** input, from both `check_consent`
and `verify_consent_before_access`, and its `log_consent_check` body is `pass`.

It is unreachable for **two independent reasons**:

1. `factory.py` does not register `national_router`, so
   `/national/security/consent/check` does not exist in the running app —
   confirmed against a live OpenAPI schema (1787 paths, none under
   `/national/security`).
2. Its only call site (`national/api/routes/security.py:89`) passes
   `citizen_id=` to a parameter named `patient_id` and omits the required
   `requestor_id`. The call raises `TypeError` before returning anything.

**The signature mismatch was deliberately left unfixed.** A correct call to a
fail-open service is strictly worse than a broken call to one. Instead the guard
ties the two facts together: *if the service still grants unconditionally, that
router must not be registered.* Wiring it up — or "fixing" the call — now fails a
test instead of quietly turning consent into an unconditional ALLOW.

### 4.2 `ConsentEngine` is per-process

`citizen_platform/privacy.py` stores consent in `self._consents`, a plain dict on
the instance. `/citizen-platform/consents/{citizen_id}` is registered and live.
A grant made there does not survive a restart and is invisible to the other
gunicorn workers (`WEB_CONCURRENCY` defaults to 3), so the next request may not
see it.

This is survivable **only** because nothing authorizes on it — its consumers
build the citizen privacy dashboard. It misinforms rather than mis-authorizes.
The guard asserts that no enforcement module consults it, so the day one does,
the test fails first.

## 5. Contradictions recorded

| # | Contradiction |
| --- | --- |
| C-1 | A class named `ConsentEnforcementService` returns ALLOW unconditionally and audits nothing. |
| C-2 | A registered consent endpoint (`/citizen-platform/consents/…`) persists nothing. |
| C-3 | Consent is tenant-scoped in `trust` (`lab_id`) and nation-scoped in the canonical store (`gpid`). Both are defensible; neither is written down as the rule. |
| C-4 | Three consent tables exist in the ORM with no migration — visible only because `test_schema_fidelity` declares them. |

## 6. Verification

Five tests, all executed locally, lint clean, gated in the IAM backend job in
the same commit:

- the consent-table ledger is exact in both directions;
- each declared migration still builds the table it claims;
- the enforced path resolves to `consents` and audits all five branches;
- a fail-open consent service is not reachable;
- no enforcement module consults the in-memory `ConsentEngine`.

**Negative-proven:** registering `national_router` in `factory.py` makes the
reachability test fail with its intended message; restoring `factory.py`
byte-identically makes it pass again.

## 7. Remaining

Nothing blocks NR-060. `healthcare_consent` (NR-050) is unblocked: its canonical
owner is named, and the capability should bind to `consents` rather than
introduce a ninth store.

Open, and belonging to other findings: whether the three unbuilt consent tables
are built or retired (NR-022 class), and whether the tenancy rule in C-3 is
written down (Phase 2 Core map).

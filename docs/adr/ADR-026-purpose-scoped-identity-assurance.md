# ADR-026 — Identity assurance is scoped per purpose, never a single scale

* **Status** Accepted (AUTH-004)
* **Date** 2026-09-11
* **Supersedes** the single `L0…L5` assurance ladder introduced with the IAM
  Phase 3 verification domain
* **Related** ADR-024 (Platform Constitution), NR-035 / AUTH-003,
  `docs/architecture/identity/verification-architecture.md`

## Context

GULA verifies four independent things about an account: that its holder can be
reached at an address (**contact**), who the real-world person is
(**identity**), that they are licensed to practise (**professional**), and that
an organization is real and eligible (**organization**). The persisted
`VerificationRecord` has always separated these as `VerificationRecordType`.

The scoring did not. `VerificationPolicy` mapped each method to a bare level on
one ladder and `AssuranceEngine.level_for()` returned the maximum across all of
them. Measured at head before this change:

```
level_for([organization_registry verified]) = L4
require([...], L2)  ->  PASSED          # L2 is official_identity
```

Because `organization_registry` sat at L4 and `official_identity` at L2, an
account whose *employer* had been verified out-ranked one whose *holder's
identity* had been proven. Any caller writing `require(results, L2)` meaning
"we know who this person is" would have been satisfied by an organization
check. A second vocabulary in `app/identity/trust` had the same defect by
averaging IAL, AAL and FAL, so authentication strength lifted identity
assurance:

```
IAL1 + AAL3 + FAL3  ->  overall IAL2
```

Nothing in `app/` consumed either engine yet. The first consumer would have
inherited the conflation, and by then the fix would have had callers to migrate.

## Decision

1. **Assurance is a profile, not a scalar.** `AssuranceProfile` holds one level
   per `VerificationPurpose`. There is no combined number and none will be
   added — a single figure cannot express "we can reach this person and their
   employer is a real hospital, and we do not know who they are" without lying
   in one direction or the other.

2. **A method establishes exactly one purpose.** `VerificationPolicy` maps
   method → `(purpose, level)`. Purposes are not comparable, so they do not
   share a ladder.

3. **The purpose is a required argument.** `AssuranceEngine.level_for()` and
   `.require()` take the purpose explicitly. A call that omits it raises
   `TypeError` — failing closed at the call site rather than answering a
   different question from the one the caller believed it asked.

4. **Four levels, per purpose.** L0 nothing; L1 a self-asserted channel was
   demonstrated; L2 an authoritative source was consulted; L3 in-person or
   government-attested. No method reaches L3 today; it exists so a future
   high-assurance operation has somewhere to point that current methods cannot
   satisfy. L4 and L5 are removed — they existed only to rank organization and
   professional checks above identity proofing.

5. **A provider never grades its own work.** `assurance_for()` ignores the
   provider's self-reported level and an unmapped method yields L0.

## Consequences

**Positive.** The conflation is not expressible. Capture techniques (OCR, NFC)
sit at L0 for the identity purpose, so a deployment cannot reach identity
assurance by buying a scanner. The scoring vocabulary now matches the persisted
`VerificationRecordType`, so a record cannot be filed under a category the
engine cannot reason about.

**Cost.** Four existing tests asserted the old semantics — including one that
asserted the defect directly. They were rewritten to pin the resolution rather
than deleted. No production call sites changed, because there were none.

**Not addressed here.** The `app/identity/trust` IAL/AAL/FAL averaging
(AUTH-V2, second half) is recorded and pinned by a test but not changed: that
route lets the client supply its own levels (AUTH-V1), and fixing the averaging
without fixing the input would be cosmetic. `users.is_verified` still serves two
purposes (AUTH-V3); splitting it is a schema change and a policy decision about
what assurance gates a health-data linkage, so it is recorded for a later batch
with explicit approval.

## Alternatives rejected

* **Keep one ladder, reorder it.** Any total order asserts that one purpose
  substitutes for another at some level. There is no correct ordering because
  the purposes answer different questions.
* **Adopt NIST IAL/AAL/FAL wholesale.** It is a third vocabulary in a codebase
  that already has too many, and the brief's instruction was not to copy
  external standards blindly. The three axes are kept conceptually — identity
  proofing, authentication, federation are separated — without importing the
  notation.
* **Document the rule and leave the code.** A live engine that collapses the
  purposes, beside a document saying they must not collapse, guarantees the
  first consumer wires in the defect.

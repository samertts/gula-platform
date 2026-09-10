# GULA Clinical State Registry — NR-007

**Batch:** BATCH-2.5 (analysis + registry model; the state machine is **not**
modified here)
**Subject:** `backend/app/blood_bank/domain/state_machine.py`
**Method:** enum reflection and exact string matching against `_TRANSITIONS`.
Every count below is reproducible; none is estimated.

---

## 1. The defect, restated precisely

```python
def transition(current: str, target: str, *, entity: str = "blood_bank_resource") -> str:
    allowed = _TRANSITIONS.get(current)          # keyed on state ALONE
    if allowed is None or target not in allowed:
        raise BloodBankWorkflowError(f"Invalid {entity} transition: {current} -> {target}")
    return target
```

`entity` reaches the error message and nothing else. One flat `dict[str, set[str]]`
governs blood units, donations, donors, orders, samples, crossmatches,
transfusions and reactions. Any state name shared by two entity types collides,
and the second definition silently loses.

NR-004 and NR-020 were both realised instances of this, five months apart.

## 2. Measured shape

| Quantity | Value |
|---|---|
| Keys in `_TRANSITIONS` | 39 |
| Distinct state vocabulary (keys ∪ targets) | 43 |
| Lifecycle enums | 5 |
| States claimed by more than one entity | **4** |
| Keys that are no entity's enum value | **28** |
| Enum values with no key (unreachable as a source state) | **18** |
| Distinct `entity=` values passed at any call site | **2** (`blood_unit`, `transfusion`) |

The last row is the sharpest number in this document. The table carries keys
for orders, samples, crossmatches and reactions, but **no call site ever passes
those entity names**. Those rows govern nothing today and would govern the
wrong thing the moment they were wired up.

## 3. Lifecycle enums

| Entity | Enum | Values |
|---|---|---|
| `blood_unit` | `ComponentStatus` | available, discarded, expired, issued, pending_processing, processing, quarantined, recalled, reserved, transfused |
| `donation` | `DonationStatus` | completed, discarded, in_progress, registered, rejected, screened |
| `donor` | `DonorStatus` | active, deferred, expired, inactive, permanently_deferred |
| `crossmatch` | `CrossmatchStatus` | compatible, incompatible, partially_compatible, pending, waived |
| `transfusion` | `TransfusionStatus` | cancelled, completed, dispensed, in_progress, ordered, reacted, verified |

## 4. Collision table — the four shared states

| State | Claimed by | Key in table? | What the single shared row means today | Clinical significance | Owner |
|---|---|---|---|---|---|
| `completed` | `donation`, `transfusion` | **yes** — `set()` (terminal) | Terminal for both. Correct for a transfusion. A **donation** that is `completed` also cannot advance — but a completed donation must still be processable into components. | **HIGH** — a completed donation is the *input* to component processing, not an end state. | **BLOCKED — CLINICAL OWNER REQUIRED** |
| `in_progress` | `donation`, `transfusion` | **yes** — `{completed, reaction_suspected}` | A **donation in progress is validated against transfusion rules**: it may transition to `reaction_suspected`, which is a transfusion-reaction state and meaningless for a collection. | **HIGH** — a donation can be moved into a transfusion-reaction workflow. | **BLOCKED — CLINICAL OWNER REQUIRED** |
| `expired` | `blood_unit`, `donor` | **yes** — `{discarded}` | A blood unit that expires is discarded — correct. A **donor** whose eligibility expires would be "discarded", which is not a thing that happens to a person. | **HIGH** — the donor lifecycle has no legal transition out of `expired` other than a nonsensical one. | **BLOCKED — CLINICAL OWNER REQUIRED** |
| `discarded` | `blood_unit`, `donation` | **no** | Not a key, so it is terminal by absence for both. Probably correct for both, but by accident rather than by statement. | MEDIUM | **BLOCKED — CLINICAL OWNER REQUIRED** |

Three of the four are live keys, so in three cases one entity's rules already
govern another's.

## 5. The 28 synthetic keys

Names invented to dodge collisions — the workaround, made visible. Four are
explicit: `issued_order`, `received_sample`, `testing_crossmatch`,
`ordered_transfusion` are `<state>_<entity>` compounds, which is `(entity,
state)` keying implemented by hand in the string.

```
classification, clinical_assessment, collected, compatibility_pending,
crossmatch_requested, draft, identified, investigation, issued_order,
ordered_transfusion, reaction_suspected, ready, received, received_at_bedside,
received_sample, released, requested, resolution, returned, reviewed,
sample_received, sample_required, started, testing, testing_crossmatch,
transfusion_stopped, validated, verification
```

Each needs an owning entity before it can be keyed. That attribution is
clinical, not mechanical.

## 6. The 18 unreachable enum values

Declared as legal states but present as no key, so nothing can transition
*out* of them:

| Entity | Values with no transition row |
|---|---|
| `blood_unit` | discarded, pending_processing, processing, recalled |
| `donation` | discarded, registered, rejected, screened |
| `donor` | active, deferred, inactive, permanently_deferred |
| `crossmatch` | partially_compatible, pending, waived |
| `transfusion` | cancelled, dispensed, ordered, reacted |

Some are genuinely terminal (`discarded`, `permanently_deferred`). Others are
plainly not: a `registered` donation must be able to start; a `pending` crossmatch
must be able to resolve; an `ordered` transfusion must be able to be verified.
Distinguishing "terminal" from "unreachable by omission" is exactly the
per-entity work that has never been written down.

## 7. Vocabulary drift

`BloodBankState` is declared as the canonical vocabulary but does not match the
table it is supposed to describe:

- In `BloodBankState`, not a table key: `cancelled`, `crossmatch_testing`,
  `discarded`, `rejected`, `sample_expired`, `sample_rejected`
- Table keys absent from `BloodBankState`: `available`, `issued_order`,
  `ordered_transfusion`, `received_sample`, `testing_crossmatch`, `verified`

The enum is therefore not a reliable index of the transition table.

## 8. Target registry model — mechanical part

```python
_TRANSITIONS: dict[tuple[str, str], frozenset[str]]   # (entity, state) -> targets

def transition(current: str, target: str, *, entity: str) -> str:
    """Fail closed on an unknown entity as well as an unknown state."""
    allowed = _TRANSITIONS.get((entity, current))
    if allowed is None:
        raise BloodBankWorkflowError(f"No transition rules for {entity} state {current!r}")
    if target not in allowed:
        raise BloodBankWorkflowError(f"Invalid {entity} transition: {current} -> {target}")
    return target
```

`entity` loses its default: an unnamed entity must be a refusal, not a silent
fallback to a shared table.

**This mechanical change is safe and small. It is deliberately not applied
here**, because applying it without the attribution in §9 would convert every
currently-permitted transition into a refusal at runtime — a clinical
regression dressed as a correctness fix.

## 9. What is blocked

**BLOCKED — CLINICAL OWNER REQUIRED**, on two questions:

1. For each of the **4 colliding states**, which entity owns it, and what are
   *that* entity's legal transitions out of it?
2. For each of the **28 synthetic keys**, which entity owns it, and does its
   real name differ from the collision-dodging one?

A blood-bank clinical owner must answer. Guessing a clinical state machine is a
stop condition, and this document does not guess.

## 10. Sequencing note

The mechanical keying in §8 must land **in the same change** as the attribution
in §9 — never before it. Keying by `(entity, state)` against a table whose rows
have no attributed entity fails every transition in the system.

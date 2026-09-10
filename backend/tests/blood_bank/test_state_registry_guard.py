"""NR-007 — a fail-closed guard against new global-state collisions.

The Blood Bank transition table is keyed on a state name alone, so any state
value shared by two entity enums collides and one entity's rules silently
govern the other's. NR-004 and NR-020 were both realised instances.

BATCH-2.6 measured which entities actually reach the state machine, and the
answer attributes every existing collision without guessing: only two entity
values are ever passed to ``transition()`` — ``blood_unit`` and
``transfusion``. For each of the four colliding states, exactly one claimant is
a state-machine participant and the other never reaches the machine at all. The
live row therefore belongs to the participant, provably.

That also corrects the BATCH-2.5 description of this finding. It said "a
donation in progress is validated against transfusion rules". Donations are
never passed to ``transition()``, so no such validation happens today. The
defect is a latent trap that fires when a new entity is wired up — which is
exactly how NR-004 and NR-020 happened — not an active mis-validation.

This guard does not rewrite the state machine. It fails when the shape that
makes the trap possible gets worse: a new colliding state, or a new entity
reaching ``transition()`` while the table is still keyed on state alone.
"""
from __future__ import annotations

import collections
import pathlib
import re

from app.blood_bank.domain import enums
from app.blood_bank.domain.state_machine import _TRANSITIONS

BLOOD_BANK = pathlib.Path(__file__).resolve().parents[3] / "app" / "blood_bank"

# The enums that name a lifecycle state, as opposed to a classification.
LIFECYCLE_ENUMS = {
    "blood_unit": "ComponentStatus",
    "donation": "DonationStatus",
    "donor": "DonorStatus",
    "crossmatch": "CrossmatchStatus",
    "transfusion": "TransfusionStatus",
}

# Measured, and attributed by call-site evidence rather than by judgement:
# state -> (claimants, the claimant that actually reaches the state machine).
KNOWN_COLLISIONS = {
    "completed": (("donation", "transfusion"), "transfusion"),
    "discarded": (("blood_unit", "donation"), "blood_unit"),
    "expired": (("blood_unit", "donor"), "blood_unit"),
    "in_progress": (("donation", "transfusion"), "transfusion"),
}

# Entities observed at a transition() call site. Adding one without keying the
# table by (entity, state) is what turns a latent collision into a live defect.
STATE_MACHINE_PARTICIPANTS = frozenset({"blood_unit", "transfusion"})


def _states_by_entity() -> dict[str, set[str]]:
    return {
        entity: {member.value for member in getattr(enums, enum_name)}
        for entity, enum_name in LIFECYCLE_ENUMS.items()
    }


def _transition_call_entities() -> set[str]:
    found: set[str] = set()
    for path in BLOOD_BANK.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        source = path.read_text(encoding="utf-8", errors="ignore")
        found.update(re.findall(r'transition\([^)]*entity="(\w+)"', source))
    return found


def test_no_new_state_name_is_claimed_by_two_entities() -> None:
    """A new collision must be a deliberate decision, not a merge-time surprise."""
    claimants: dict[str, list[str]] = collections.defaultdict(list)
    for entity, states in _states_by_entity().items():
        for state in states:
            claimants[state].append(entity)

    collisions = {s: tuple(sorted(e)) for s, e in claimants.items() if len(e) > 1}
    expected = {s: tuple(sorted(c)) for s, (c, _) in KNOWN_COLLISIONS.items()}
    assert collisions == expected, (
        "the set of state names shared by two entity enums changed. The "
        "transition table is keyed on state alone, so a new shared name means "
        "one entity's rules now govern another's. Attribute it before adding "
        f"it here. Found: {collisions}"
    )


def test_no_new_entity_reaches_a_state_keyed_transition_table() -> None:
    """Wiring a third entity into transition() is how NR-004 and NR-020 happened."""
    observed = _transition_call_entities()
    unexpected = observed - STATE_MACHINE_PARTICIPANTS
    assert not unexpected, (
        f"new entities reach transition(): {sorted(unexpected)}. The table is "
        "still keyed on state alone, so their states collide with the entities "
        "already there. Key the table by (entity, state) in the same change "
        "that wires them up."
    )


def test_each_collision_is_owned_by_the_entity_that_reaches_the_machine() -> None:
    """The attribution this guard rests on, asserted rather than assumed."""
    states = _states_by_entity()
    for state, (claimants, owner) in KNOWN_COLLISIONS.items():
        participants = [c for c in claimants if c in STATE_MACHINE_PARTICIPANTS]
        assert participants == [owner], (
            f"state {state!r} no longer has exactly one claimant that reaches "
            f"the state machine: {participants}. Its transition row is now "
            "ambiguous and needs a clinical owner."
        )
        assert state in states[owner]


def test_the_transition_table_is_still_keyed_on_state_alone() -> None:
    """When this fails, NR-007's mechanical half is done — retire the guard."""
    assert all(isinstance(key, str) for key in _TRANSITIONS), (
        "the transition table is now keyed by something other than a bare "
        "state name. If it is keyed by (entity, state), NR-007's mechanical "
        "half is complete: update this guard rather than deleting it."
    )

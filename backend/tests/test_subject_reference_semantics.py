"""NR-022 — every reference to an unbuilt subject table has a declared semantic class.

The approved decision rejects a universal data subject. Person/Identity is the
canonical national subject; Patient and Citizen are contextual roles. So the 263
foreign keys that name the four unbuilt subject tables are not one migration
waiting to happen -- they are five different migrations, and which one each
reference belongs to is a semantic question answered per column.

Measured across `app/`:

    national_practitioners  88   national_citizens  77
    national_patients       63   national_encounters 35

Classified by explicit per-column rules (never regex-guessed, so every call can
be argued at review):

     75  CITIZEN      portal / registry context
     63  PATIENT      clinical subject
     57  PRACTITIONER licensed role -- licensure is load-bearing
     35  ENCOUNTER    clinical episode; not a subject at all
     11  PERSON       actor identity ("who did this"), licensure not implied
     11  ASSIGNMENT   posting or coordination role, not the human
      9  REVIEW       clinically may require licensure; decided per call site
      2  PERSON       kinship, which is between persons

The practitioner split is the result that matters: **only 57 of the 88
practitioner references actually require practitioner semantics.** Eleven are
actor identity and eleven are assignment. Pointing all 88 at a Practitioner
table would be as wrong as pointing all 88 at Person.

This file holds the classification while the transition is in flight. A new
foreign key to any of the four may be added -- it may not be added without a
declared class.
"""

from __future__ import annotations

import ast
import collections
import pathlib

# NR-069. `built_tables()` derives from the migration chain. Reading
# `evidence-created-tables.json` directly is how three tables created through a
# migration helper were treated as unbuilt; one source of truth, derived.
from tests.orm_resolution import built_tables

BACKEND = pathlib.Path(__file__).resolve().parents[1]
APP = BACKEND / "app"

SUBJECT_TABLES = frozenset({
    "national_practitioners",
    "national_citizens",
    "national_patients",
    "national_encounters",
})

# Licensure is load-bearing: the reference is only meaningful for someone
# holding a professional licence and a scope of practice.
_PRACTITIONER = frozenset({
    "practitioner_id", "attending_practitioner_id", "admitting_practitioner_id",
    "discharging_practitioner_id", "referring_practitioner_id",
    "receiving_practitioner_id", "responding_practitioner_id",
    "visiting_practitioner_id", "from_practitioner_id", "to_practitioner_id",
    "actor_practitioner_id", "uploaded_by_practitioner_id", "prescriber_id",
    "midwife_id", "diagnosed_by", "administered_by", "cosigned_by", "signed_by",
    "witnessed_by",
})

# Who performed a system action. The name does not imply licensure.
_ACTOR = frozenset({
    "created_by", "uploaded_by", "recorded_by", "assigned_by", "enrolled_by",
    "resolved_by", "author_id",
})

# A posting or coordination role rather than the human holding it.
_ASSIGNMENT = frozenset({
    "coordinator_id", "care_coordinator_id", "care_manager_id", "team_lead_id",
    "visit_lead_id", "facilitator_id", "administrator_id",
})

# Genuinely undecidable from the column name: in a clinical context these may
# require licensure (result verification, clinical review) and in an operational
# one they may not. Named rather than guessed.
_REVIEW = frozenset({
    "verified_by", "completed_by", "reviewed_by", "assessed_by", "performer_id",
})

# Kinship is a relation between persons, not between portal accounts.
_CITIZEN_AS_PERSON = frozenset({"mother_id", "father_id"})

PRACTITIONER = "PRACTITIONER"
PERSON_ACTOR = "PERSON_ACTOR"
PERSON_KIN = "PERSON_KIN"
ASSIGNMENT = "ASSIGNMENT"
CITIZEN = "CITIZEN"
PATIENT = "PATIENT"
ENCOUNTER = "ENCOUNTER"
REVIEW = "REVIEW"
UNCLASSIFIED = "UNCLASSIFIED"

#: The measured distribution. Counts may change as the transition proceeds;
#: what may not change is a reference existing with no class at all.
DECLARED_DISTRIBUTION = {
    CITIZEN: 74,
    PATIENT: 63,
    PRACTITIONER: 57,
    ENCOUNTER: 35,
    PERSON_ACTOR: 11,
    ASSIGNMENT: 11,
    REVIEW: 9,
    PERSON_KIN: 2,
}

#: The nine sites whose class cannot be read off the column name. Each must be
#: decided against its call site before the practitioner transition lands.
#: This ledger may shrink. It may never grow.
DECLARED_REVIEW_SITES = frozenset({
    ("cc_clinical_pathway_enrollments", "completed_by"),
    ("cc_risk_stratification", "assessed_by"),
    ("cc_self_monitoring_records", "reviewed_by"),
    ("cc_patient_tasks", "completed_by"),
    ("cc_patient_tasks", "verified_by"),
    ("cc_self_follow_up_tasks", "verified_by"),
    ("cc_program_enrollments", "completed_by"),
    ("cc_clinical_handovers", "verified_by"),
    ("ehr_care_plan_activities", "performer_id"),
})


def _classify(target: str, column: str) -> str:
    if target == "national_patients":
        return PATIENT
    if target == "national_encounters":
        return ENCOUNTER
    if target == "national_citizens":
        return PERSON_KIN if column in _CITIZEN_AS_PERSON else CITIZEN
    if column in _PRACTITIONER:
        return PRACTITIONER
    if column in _ACTOR:
        return PERSON_ACTOR
    if column in _ASSIGNMENT:
        return ASSIGNMENT
    if column in _REVIEW:
        return REVIEW
    return UNCLASSIFIED


def _subject_references() -> list[tuple[str | None, str, str, str]]:
    """(owner_table, column, target_table, semantic_class) for every FK."""
    found: list[tuple[str | None, str, str, str]] = []
    for path in APP.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError:
            continue
        for cls in (n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)):
            owner: str | None = None
            for stmt in cls.body:
                if isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Constant):
                    for target in stmt.targets:
                        if isinstance(target, ast.Name) and target.id == "__tablename__":
                            owner = stmt.value.value
            for stmt in cls.body:
                if not isinstance(stmt, ast.Assign):
                    continue
                column = next(
                    (t.id for t in stmt.targets if isinstance(t, ast.Name)), None
                )
                if column is None:
                    continue
                for node in ast.walk(stmt.value):
                    if (
                        isinstance(node, ast.Call)
                        and getattr(node.func, "id", None) == "ForeignKey"
                        and node.args
                        and isinstance(node.args[0], ast.Constant)
                        and isinstance(node.args[0].value, str)
                    ):
                        table = node.args[0].value.split(".")[0]
                        if table in SUBJECT_TABLES:
                            found.append(
                                (owner, column, table, _classify(table, column))
                            )
    return found


def test_the_reference_scan_still_finds_the_dependency_surface() -> None:
    """Guard the guard: a scan finding nothing would classify nothing."""
    refs = _subject_references()
    assert len(refs) >= 250, (
        f"only {len(refs)} references to the four subject tables found; the scan "
        "has drifted"
    )


def test_every_subject_reference_has_a_declared_semantic_class() -> None:
    """The decision in one assertion.

    Person/Identity is canonical and Patient/Citizen are contextual roles, so a
    reference with no declared class is a reference nobody has decided the
    meaning of -- and it would be migrated by whichever bulk rewrite ran first.
    """
    unclassified = sorted(
        {(owner, column, table)
         for owner, column, table, cls in _subject_references()
         if cls == UNCLASSIFIED}
    )
    assert unclassified == [], (
        "these foreign keys name an unbuilt subject table and have no semantic "
        "class. Add the column to the right rule set rather than letting a bulk "
        f"re-point decide: {unclassified}"
    )


def test_the_practitioner_references_are_not_all_practitioners() -> None:
    """The finding that shapes NR-061.

    Of the practitioner references, a substantial minority are actor identity or
    an assignment role. If this ever becomes all-PRACTITIONER, someone has
    flattened the distinction the decision exists to preserve.
    """
    classes = collections.Counter(
        cls for _, _, table, cls in _subject_references()
        if table == "national_practitioners"
    )
    assert classes[PERSON_ACTOR] > 0 and classes[ASSIGNMENT] > 0, (
        "every practitioner reference is now classified as a licensed role. "
        "Actor identity and assignment references were folded into it: "
        f"{dict(classes)}"
    )


def test_the_review_ledger_does_not_grow() -> None:
    """Undecidable sites must be decided, not accumulated."""
    review = {
        (owner, column)
        for owner, column, _, cls in _subject_references()
        if cls == REVIEW
    }
    appeared = sorted(review - DECLARED_REVIEW_SITES)
    assert appeared == [], (
        "new references whose class cannot be read from the column name. Decide "
        f"them against their call site rather than adding to the backlog: {appeared}"
    )


def test_the_declared_distribution_still_describes_the_code() -> None:
    """A distribution that has silently drifted means the map is stale.

    This is not a freeze: counts are expected to move as references migrate to
    real tables. It fails when they move without the ledger being updated, so
    the recorded classification cannot quietly stop describing the repository.
    """
    actual = collections.Counter(cls for _, _, _, cls in _subject_references())
    drifted = {
        cls: (declared, actual.get(cls, 0))
        for cls, declared in DECLARED_DISTRIBUTION.items()
        if actual.get(cls, 0) != declared
    }
    assert drifted == {}, (
        "the semantic distribution changed (declared -> now). Update "
        f"DECLARED_DISTRIBUTION in the same commit as the change: {drifted}"
    )


#: References to an unbuilt subject table that live in a table the migration
#: chain actually builds -- the entire live surface of the 263.
#:
#: It was two. `citizen_id` left in NR-064: it now names `niam_persons`, the
#: canonical person, and has a real foreign key (`20260914_0001`) where the
#: declared one could never be created. `patient_id` remains because there is
#: nothing to point it at -- it is VARCHAR(26) and the built clinical patient
#: table keys on INTEGER -- so the API refuses the input instead, and the column
#: waits on NR-022's clinical-subject decision.
#:
#: This ledger may shrink; it may not grow, and a resolved entry must be removed
#: rather than left behind.
DECLARED_LIVE_SUBJECT_REFERENCES = frozenset({
    ("niam_citizen_relationships", "patient_id", "national_patients"),
})


def test_the_subject_transition_stays_latent() -> None:
    """NR-061's dependency proof, generalised -- and the precondition it implies.

    261 of the 263 references live in tables no migration builds, including
    **every one** of the 57 practitioner references. So nothing is currently
    depending on these subject tables at runtime, and no re-pointing is owed.

    That is what makes building one of them dangerous rather than overdue:
    a built owner table turns its subject reference into a live dependency, and
    from then on the reference has to resolve to whatever the class says owns it
    -- the composition for PRACTITIONER, the canonical Person for PERSON_ACTOR.
    Build the owner after the target is decided, not before.
    """
    built = set(built_tables())
    live = sorted({
        (owner, column, table)
        for owner, column, table, _ in _subject_references()
        if owner in built
    })
    undeclared = [ref for ref in live if ref not in DECLARED_LIVE_SUBJECT_REFERENCES]
    assert undeclared == [], (
        "a built table now references an unbuilt subject table, which makes the "
        "reference a live dependency. Decide its target against its semantic "
        f"class before the owner is built: {undeclared}"
    )
    stale = sorted(DECLARED_LIVE_SUBJECT_REFERENCES - set(live))
    assert stale == [], (
        "these declared live references no longer exist -- they were resolved or "
        f"removed. Delete them from the ledger in the same commit: {stale}"
    )

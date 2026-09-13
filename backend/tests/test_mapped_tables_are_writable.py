"""NR-086 — a mapper that cannot resolve its own foreign keys cannot be written.

SQLAlchemy resolves every `ForeignKey` target during flush, when it sorts the
mapper's tables. A target that lives in a *different* `MetaData` cannot be found,
so the write raises before any SQL is emitted:

    session.add(ConsentRecord(...)); session.flush()
    NoReferencedTableError: Foreign key associated with column
    'trust_consent_records.guardian_id' could not find table 'lab_users'

Reads are unaffected, which is exactly why this hides. `SELECT` never sorts
tables, so the table looks healthy to `test_mapped_tables_are_readable.py`, to
any migration check, and to a route that only lists. It fails the first time
something tries to persist.

**This is the same defect NR-075 recorded on `niam_citizen_relationships`, and
it is not one table.** Asking which mappers can resolve every foreign key target
inside their own `MetaData` gives **76 tables carrying 310 unresolvable foreign
keys** — independently equal to the cross-base foreign-key population NR-078
measured by a different route. NR-078 recorded those 310 as a *topology*
problem, something that stops `alembic autogenerate` from running. They are also
76 tables that **no ORM write can reach**, and that consequence had not been
stated.

Found by running the proof this repository had never run: a real
`Session`, a real model instance, a real `flush`. Every earlier NR-085 proof
used Core `select()` and raw SQL, which never trigger table sorting — so the
trust platform's write path had been described as working when it has never
worked.

The live instance: `app/trust/routes.py` serves 13 registered paths, of which
**six are writes** (`POST /api/v1/trust/consent`, `/consent/{id}/withdraw`,
`/sign`, `/timestamp`, `/compliance/check`, `/compliance/evidence`). All six
land on the four trust tables that carry a cross-base foreign key, and all six
fail. Consent capture and consent withdrawal are among them.

**This guard is static and needs no database**, which is why it runs in the unit
job: the question is whether a mapper's declared targets exist in its own
metadata, and that is answerable from the registry alone.

The ledger may shrink. It may never grow. It empties when the metadata topology
is resolved (NR-078 Option A) or when the cross-base declarations are replaced
with the plain columns they should be — and NR-078 has measured that not one of
these 76 tables carries a `relationship()`, so nothing navigates them.
"""

from __future__ import annotations

import pytest

#: Mapped table -> number of foreign keys whose target table is absent from the
#: mapper's own MetaData. Each of these tables raises NoReferencedTableError on
#: any INSERT or UPDATE through the ORM.
DECLARED_UNWRITABLE: dict[str, int] = {
    # --- CareContinuumBase (45 tables) ---
    "cc_antenatal_care_visits": 5,
    "cc_breastfeeding_records": 4,
    "cc_care_coordination": 4,
    "cc_care_journeys": 5,
    "cc_child_development_records": 5,
    "cc_chronic_disease_registry": 6,
    "cc_clinical_handovers": 6,
    "cc_clinical_pathway_enrollments": 5,
    "cc_cold_chain_monitors": 2,
    "cc_community_care_records": 5,
    "cc_community_clinic_records": 6,
    "cc_community_visits": 3,
    "cc_contraindications": 5,
    "cc_cross_org_referrals": 8,
    "cc_delivery_records": 6,
    "cc_disease_management_plans": 4,
    "cc_educational_material_assignments": 4,
    "cc_family_medicine_records": 6,
    "cc_follow_up_plans": 5,
    "cc_growth_monitoring": 5,
    "cc_health_assessments": 5,
    "cc_health_programs": 3,
    "cc_health_promotion_activities": 3,
    "cc_home_care_plans": 5,
    "cc_immunization_schedules": 6,
    "cc_occupational_health_records": 5,
    "cc_patient_tasks": 7,
    "cc_postnatal_care_visits": 5,
    "cc_pregnancy_records": 5,
    "cc_preventive_care_records": 4,
    "cc_primary_care_encounters": 7,
    "cc_program_enrollments": 6,
    "cc_referral_attachments": 1,
    "cc_referral_requests": 10,
    "cc_referral_responses": 3,
    "cc_referral_timelines": 2,
    "cc_reminder_schedules": 2,
    "cc_risk_stratification": 4,
    "cc_school_health_visits": 3,
    "cc_screening_campaigns": 3,
    "cc_self_follow_up_tasks": 5,
    "cc_self_monitoring_records": 3,
    "cc_transitions_of_care": 12,
    "cc_vaccination_records": 5,
    "cc_vaccine_inventory": 1,
    # --- DataPlatformBase (9 tables) ---
    "dp_consent_directives": 2,
    "dp_device_registry": 2,
    "dp_duplicate_records": 1,
    "dp_golden_records": 1,
    "dp_location_registry": 2,
    "dp_provider_registry": 2,
    "dw_fact_diagnoses": 1,
    "dw_fact_lab_results": 1,
    "dw_fact_patient_visits": 1,
    # --- EHRBase (16 tables) ---
    "ehr_allergies": 4,
    "ehr_care_plan_activities": 1,
    "ehr_care_plans": 4,
    "ehr_clinical_attachments": 6,
    "ehr_clinical_notes": 10,
    "ehr_conditions": 4,
    "ehr_diagnoses": 4,
    "ehr_family_history": 3,
    "ehr_immunizations": 6,
    "ehr_medication_administrations": 4,
    "ehr_medication_requests": 4,
    "ehr_medication_statements": 4,
    "ehr_patient_timeline": 5,
    "ehr_problem_list_items": 3,
    "ehr_risk_factors": 4,
    "ehr_social_history": 4,
    # --- IdentityBase (2 tables) ---
    "niam_assignments": 2,
    "niam_citizen_relationships": 3,
    # --- TrustBase (4 tables) ---
    "trust_compliance_checks": 1,
    "trust_compliance_evidence": 1,
    "trust_consent_records": 3,
    "trust_service_logs": 3,
}

#: Measured: 640 of 716 mapped tables resolve every target. The floor sits just
#: under it so the ledger cannot be emptied by deleting mappers or unregistering
#: a base, and is not a round number chosen in advance.
MINIMUM_WRITABLE = 630

#: Likewise for the instrument. 716 tables are registered today.
MINIMUM_PROBED = 700


@pytest.fixture(scope="module")
def registry():
    import os

    from tests.test_alembic_metadata_registry import _load_registry

    saved = dict(os.environ)
    try:
        yield _load_registry()
    finally:
        os.environ.clear()
        os.environ.update(saved)


@pytest.fixture(scope="module")
def resolution(registry):
    """Per table, how many declared FK targets are missing from its own MetaData."""
    unwritable: dict[str, int] = {}
    writable: set[str] = set()
    for _label, metadata in registry:
        own = set(metadata.tables)
        for name, table in metadata.tables.items():
            missing = sum(
                1 for fk in table.foreign_keys
                if fk.target_fullname.split(".")[0] not in own
            )
            if missing:
                unwritable.setdefault(name, missing)
            else:
                writable.add(name)
    return {"unwritable": unwritable, "writable": writable}


def test_the_probe_walked_the_registry(resolution):
    """An instrument that measures nothing agrees with every ledger."""
    total = len(resolution["writable"]) + len(resolution["unwritable"])
    assert total >= MINIMUM_PROBED, (
        f"only {total} mapped tables were walked; the registry did not load"
    )


def test_no_undeclared_table_is_unwritable(resolution):
    """The invariant. A new cross-base ForeignKey makes its table unwritable."""
    unexpected = sorted(set(resolution["unwritable"]) - set(DECLARED_UNWRITABLE))
    assert not unexpected, (
        "these mapped tables declare a ForeignKey whose target is in a different "
        f"MetaData, so every ORM INSERT and UPDATE on them raises "
        f"NoReferencedTableError before emitting SQL: {unexpected}. Reads will "
        "still work, so nothing else in this suite would notice."
    )


def test_the_unwritable_ledger_does_not_rot(resolution):
    """A table that has been repaired must be removed from the ledger."""
    resolved = sorted(set(DECLARED_UNWRITABLE) - set(resolution["unwritable"]))
    assert not resolved, (
        f"these tables now resolve every foreign key and must be deleted from "
        f"DECLARED_UNWRITABLE: {resolved}"
    )


def test_the_recorded_counts_are_exact(resolution):
    """Half a repair is not a repair, and the ledger has to show which half."""
    drifted = {
        name: {"declared": DECLARED_UNWRITABLE[name], "measured": measured}
        for name, measured in sorted(resolution["unwritable"].items())
        if name in DECLARED_UNWRITABLE and measured != DECLARED_UNWRITABLE[name]
    }
    assert not drifted, (
        f"the number of unresolvable foreign keys has changed: {drifted}"
    )


def test_the_writable_population_never_shrinks(resolution):
    """The other half of the ratchet.

    Deleting a mapper, or unregistering a declarative base, would shrink the
    ledger above while making the platform strictly worse.
    """
    assert len(resolution["writable"]) >= MINIMUM_WRITABLE, (
        f"only {len(resolution['writable'])} mapped tables resolve every foreign "
        f"key, against a floor of {MINIMUM_WRITABLE}: mappers or a registered "
        "metadata object have been removed rather than reconciled"
    )

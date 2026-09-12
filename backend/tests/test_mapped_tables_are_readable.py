"""NR-083 — a mapped table that exists must be readable by the mapper that claims it.

Every schema guard in this suite until now compared *descriptions* of the
schema: metadata against metadata, migration against model, one list against
another. None ever asked PostgreSQL to run a mapper's own query. So this was
invisible:

    SELECT radiology_orders.id, ... FROM radiology_orders LIMIT 1
    ProgrammingError: column radiology_orders.encounter_id does not exist

Thirty-five mapped tables that **do** exist physically name at least one column
their table does not have. For those tables nothing works -- not a write, not a
read, not a count. SQLAlchemy builds the column list from the mapper, so the
first statement fails before a row is examined. There is no degraded mode and no
partial success: the failure is total and it is per-table.

The measurement that found it is the one this file performs: for every table in
``migrations/env.py``'s ``target_metadata`` that PostgreSQL actually has, select
that mapper's own columns and see what happens. 412 mapped tables exist; 377
answer; 35 do not.

**Two blocks dominate, and they are different defects.**

*Radiology (17 of 18 tables).* Not drift -- two generations of the same domain
sharing table names. The physical tables are integer-keyed and joined to the
platform core (``patient_id -> patients.id``, ``lab_id -> labs.id``,
``*_by -> lab_users.id``). The mappers are ULID-keyed ``String(26)`` with no
foreign key to the core and **no ``lab_id`` at all**. All eighteen primary keys
disagree on type. ``app/radiology/routes.py`` is registered and serves 50 paths
over these mappers, so radiology is a registered clinical module in which no
database operation can succeed. Reconciling it means rewriting the mappers from
the physical schema, as was done for pharmacy -- a domain-sized change with its
own review, not a line in this file.

*NHDW (14 tables).* NR-074, and measuring it showed it is the same two-generation
split rather than the simpler drift it had been recorded as. The physical tables
are denormalised -- ``nhdw_admissions`` carries ``admitting_doctor``, ``ward``,
``bed_number``, ``department``, ``insurance_provider`` as free text -- while the
mappers are normalised, carrying ``admitting_doctor_id``, ``room_id``,
``bed_id``, ``department_id``, ``insurance_id``, plus ``encounter_id``,
``extension`` and ``metadata``. Every ``id`` is ``String(26)`` in the mapper and
``integer`` in the table. ``app/nhdw/routes.py`` serves 61 paths over it. Unlike
radiology the mappers do carry ``TenantMixin``, so no protected column is
unmapped -- the repair is safer, but it is still a domain reconciliation.

**Direction of repair.** The physical schema is canonical here and the mappers
are what moves, because the physical tables are the ones carrying foreign keys
into the platform core and the tenant column. That is the opposite of dropping
anything: CLAUDE.md Security Invariant #1 needs ``lab_id`` mapped, not removed.
Nothing in this file proposes deleting a physical column, and a fix that
achieved a green ledger by deleting mapper fields would be a regression the
ledger cannot see -- which is why ``test_the_readable_population_never_shrinks``
pins the other side.

The ledger may shrink. It may never grow.
"""

from __future__ import annotations

import os

import pytest
import sqlalchemy as sa

pytestmark = pytest.mark.integration

#: Owned by this guard, like the other PostgreSQL guards: `conftest.py` pins
#: DATABASE_URL to in-memory SQLite for the whole suite before anything here
#: runs, so a value read from it would describe a different database.
DATABASE_URL = os.environ.get("GULA_SCHEMA_DATABASE_URL") or os.environ.get(
    "MIGRATION_DATABASE_URL",
)

#: Mapped table -> the columns its mapper names that the table does not have,
#: measured against a database at migration head. Entries are exact: a table
#: that loses one missing column but keeps another stays here with a shorter
#: tuple, and the guard fails until this is edited to match.
DECLARED_UNREADABLE: dict[str, tuple[str, ...]] = {
    # --- RadiologyBase (17) ---
    "radiology_appointments": ("arrival_time", "check_in_time", "contrast_details",
        "contrast_required", "duration_minutes", "extra_metadata", "preparation_instructions",
        "scheduled_time", "technologist_id",),
    "radiology_critical_findings": ("acknowledgement_time", "extra_metadata",
        "notification_time", "notified_by",),
    "radiology_dicom_storage": ("body_part", "compression_type", "deleted_at", "extra_metadata",
        "file_path", "file_size", "is_deleted", "modality", "retention_days",
        "series_instance_uid", "storage_date", "storage_tier", "study_id", "study_instance_uid",
        "version",),
    "radiology_dicom_studies": ("deleted_at", "extra_metadata", "is_archived", "is_deleted",
        "number_of_images", "storage_size_bytes", "storage_tier", "version",),
    "radiology_exams": ("contrast_amount_ml", "contrast_batch", "dose_unit", "exam_code",
        "exam_name", "extra_metadata", "image_quality", "images_count", "radiologist_id",
        "series_count", "technologist_id", "total_dose",),
    "radiology_image_annotations": ("annotated_by", "annotation_data", "extra_metadata",
        "fhir_id", "fhir_resource_type",),
    "radiology_image_measurements": ("extra_metadata", "fhir_id", "fhir_resource_type",
        "finding_code", "finding_description", "location", "measured_by",),
    "radiology_image_shares": ("access_code", "extra_metadata", "is_revoked", "share_type",
        "shared_with", "study_uid",),
    "radiology_images": ("acquisition_date", "deleted_at", "extra_metadata", "file_format",
        "is_deleted", "laterality", "storage_path", "storage_tier", "updated_at", "version",
        "view_position",),
    "radiology_modality_devices": ("department_id", "device_id", "device_model",
        "dicom_protocol", "extra_metadata", "is_active", "last_connection", "site_name",),
    "radiology_mpps": ("completed_at", "deleted_at", "extra_metadata", "is_deleted", "notes",
        "version", "worklist_entry_id",),
    "radiology_orders": ("diagnosis_system", "encounter_id", "extra_metadata",
        "ordering_department_id", "ordering_provider_id", "requested_date", "scheduled_date",),
    "radiology_protocols": ("code", "extra_metadata", "name", "name_ar",
        "positioning_instructions", "protocol_type", "series_parameters", "typical_dose",
        "typical_duration",),
    "radiology_report_templates": ("extra_metadata", "structured_template",),
    "radiology_reports": ("amended_at", "body_text", "completed_at", "critical_finding",
        "critical_finding_type", "critical_notification", "dictation_file", "draft_at",
        "extra_metadata", "ordering_provider_id", "preliminary_at", "prior_report_id",
        "radiologist_id", "recommendation", "status", "transcribed_by", "verified_at",),
    "radiology_series": ("acquisition_date", "deleted_at", "device_model", "extra_metadata",
        "fov", "image_count", "is_deleted", "manufacturer", "mas", "matrix_size",
        "slice_thickness", "version",),
    "radiology_worklist_entries": ("exam_id", "extra_metadata", "modality_device_id",
        "patient_dob", "patient_name", "patient_sex", "requested_procedure",
        "scheduled_datetime", "scheduled_step",),
    # --- NHDWBase (14) ---
    "nhdw_admissions": ("admitting_doctor_id", "bed_id", "department_id", "diagnosis",
        "diagnosis_system", "discharge_date", "discharge_type", "encounter_id", "extension",
        "hospital_id", "insurance_id", "insurance_policy", "is_emergency", "metadata",
        "referring_doctor_id", "room_id",),
    "nhdw_care_plans": ("approved_by", "care_team", "diagnosis", "encounter_id", "extension",
        "metadata", "next_review_date",),
    "nhdw_clinical_tasks": ("assigned_by", "due_date", "encounter_id", "extension",
        "is_recurring", "metadata", "recurrence_rule", "scheduled_time",),
    "nhdw_dashboard_configurations": ("config_json", "department_id", "extension", "fhir_id",
        "fhir_resource_type", "role",),
    "nhdw_discharges": ("discharge_destination", "encounter_id", "extension",
        "follow_up_instructions", "follow_up_provider_id", "medications_at_discharge",
        "metadata", "mortality_review",),
    "nhdw_hospital_alerts": ("acknowledged_by", "description", "extension", "is_resolved",
        "metadata", "patient_id", "resolved_at", "resolved_by", "source_department_id",
        "triggered_by",),
    "nhdw_hospital_messages": ("department_id", "extension", "fhir_id", "fhir_resource_type",
        "has_attachments", "metadata",),
    "nhdw_queue_entries": ("check_in_time", "clinic_id", "completed_time", "department_id",
        "encounter_id", "extension", "fhir_id", "fhir_resource_type", "metadata", "queue_date",
        "seen_time", "total_wait_minutes", "visit_reason",),
    "nhdw_resource_schedules": ("extension", "fhir_id", "fhir_resource_type", "metadata",
        "resource_id",),
    "nhdw_shift_reports": ("critical_events", "department_id", "extension", "fhir_id",
        "fhir_resource_type", "issues", "metadata", "notes", "report_author", "staffing",),
    "nhdw_telemedicine_sessions": ("extension", "metadata", "notes", "platform",
        "provider_id",),
    "nhdw_transfers": ("clinical_summary", "extension", "from_bed_id", "from_department_id",
        "from_doctor_id", "from_room_id", "metadata", "reason", "status", "to_bed_id",
        "to_department_id", "to_doctor_id", "to_room_id", "transfer_date", "transfer_type",),
    "nhdw_waiting_list_entries": ("clinical_urgency", "department_id", "extension",
        "listed_date", "metadata", "procedure_code", "procedure_name",),
    "nhdw_ward_rounds": ("clinical_summary", "department_id", "encounter_id", "extension",
        "follow_up_plan", "investigations_ordered", "lead_doctor_id", "medications_reviewed",
        "metadata", "participants",),
    # --- FinBase (3) ---
    "fin_providers": ("accredited", "contact_email", "phone", "provider_type", "status",),
    "fin_subscriptions": ("amount", "auto_renew", "billing_cycle", "currency", "end_date",
        "start_date",),
    "fin_transactions": ("description", "reference_id", "reference_type", "settled_at",
        "status", "subscription_id", "transaction_type",),
    # --- NationalBase (1) ---
    "ecosystem_partner_agreements": ("version",),
}

#: The measured readable population at the time this guard shipped. It is the
#: other half of the ratchet: DECLARED_UNREADABLE shrinking because a mapper
#: lost a field, or because a table stopped being mapped, would look like
#: progress without this. Set just under the true count so ordinary additions do
#: not trip it -- not at a round number chosen in advance. Measured population is
#: 377. It is a backstop rather than the primary assertion: reverting a repair is
#: caught first by `test_every_mapped_table_that_exists_can_be_read_by_its_own_mapper`,
#: because the repaired table is no longer in the ledger that would excuse it.
MINIMUM_READABLE = 370

#: Likewise for the probe itself. NR-079 taught this suite that a guard whose
#: instrument silently measures nothing reports success forever: its floor asked
#: for 60 registered route modules while the resolver was missing 63, and it
#: passed comfortably for years. 412 mapped tables exist physically today.
MINIMUM_PROBED = 400


def _require_database() -> str:
    if not DATABASE_URL:
        pytest.skip("GULA_SCHEMA_DATABASE_URL / MIGRATION_DATABASE_URL not set")
    return DATABASE_URL


@pytest.fixture(scope="module")
def registry():
    """Exactly what `migrations/env.py` hands Alembic, by replaying that file."""
    from tests.test_alembic_metadata_registry import _load_registry

    saved = dict(os.environ)
    try:
        yield _load_registry()
    finally:
        os.environ.clear()
        os.environ.update(saved)


@pytest.fixture(scope="module")
def probe(registry):
    """Ask PostgreSQL to run each mapper's own SELECT, and record the answer.

    The gap is computed from `information_schema` rather than parsed out of the
    driver's error, because PostgreSQL reports only the *first* unknown column
    and the ledger records all of them. The SELECT is still executed: it is what
    proves the gap is fatal rather than cosmetic.
    """
    engine = sa.create_engine(_require_database())
    with engine.connect() as connection:
        physical: dict[str, set[str]] = {}
        for table, column in connection.execute(sa.text(
            "SELECT table_name, column_name FROM information_schema.columns "
            "WHERE table_schema = 'public'",
        )):
            physical.setdefault(table, set()).add(column)

        readable: set[str] = set()
        unreadable: dict[str, tuple[str, ...]] = {}
        seen: set[str] = set()
        for _label, metadata in registry:
            for name, table in metadata.tables.items():
                if name in seen or name not in physical:
                    continue
                seen.add(name)
                missing = tuple(sorted({c.name for c in table.columns} - physical[name]))
                try:
                    connection.execute(sa.select(*table.columns).limit(1)).all()
                except sa.exc.ProgrammingError:
                    connection.rollback()
                    unreadable[name] = missing
                else:
                    readable.add(name)
    engine.dispose()
    return {"readable": readable, "unreadable": unreadable, "probed": seen}


def test_the_probe_actually_queried_the_database(probe):
    """An instrument that measures nothing agrees with every ledger."""
    assert len(probe["probed"]) >= MINIMUM_PROBED, (
        f"only {len(probe['probed'])} mapped tables were found in PostgreSQL; "
        "the probe is not reaching a database at migration head"
    )


def test_every_mapped_table_that_exists_can_be_read_by_its_own_mapper(probe):
    """The invariant. Everything not in the ledger must answer its own SELECT."""
    unexpected = sorted(set(probe["unreadable"]) - set(DECLARED_UNREADABLE))
    assert not unexpected, (
        "these mapped tables exist but their mapper names a column the table "
        f"does not have, and they are not in DECLARED_UNREADABLE: {unexpected}. "
        "Every statement against them -- including SELECT -- fails with "
        "UndefinedColumn. Reconcile the mapper against the physical schema; do "
        "not drop the physical column to silence this."
    )


def test_the_ledger_does_not_rot(probe):
    """A table that has been repaired must be removed from the ledger."""
    resolved = sorted(set(DECLARED_UNREADABLE) - set(probe["unreadable"]))
    assert not resolved, (
        f"these tables now read correctly and must be deleted from "
        f"DECLARED_UNREADABLE: {resolved}"
    )


def test_the_recorded_missing_columns_are_exact(probe):
    """Half a repair is not a repair, and the ledger has to show which half."""
    drifted = {
        name: {"declared": DECLARED_UNREADABLE[name], "measured": measured}
        for name, measured in sorted(probe["unreadable"].items())
        if name in DECLARED_UNREADABLE and tuple(measured) != DECLARED_UNREADABLE[name]
    }
    assert not drifted, (
        f"the columns missing from these tables are no longer what the ledger "
        f"records: {drifted}"
    )


def test_the_unreadable_ledger_never_grows(probe):
    """The ratchet."""
    assert len(probe["unreadable"]) <= len(DECLARED_UNREADABLE), (
        f"{len(probe['unreadable'])} mapped tables cannot be read by their own "
        f"mapper, against a declared {len(DECLARED_UNREADABLE)}"
    )


def test_the_readable_population_never_shrinks(probe):
    """The other side of the ratchet.

    Deleting a mapper field, or unregistering a base, would empty the ledger
    above while making the platform strictly worse. This is what notices.
    """
    assert len(probe["readable"]) >= MINIMUM_READABLE, (
        f"only {len(probe['readable'])} mapped tables read correctly, against a "
        f"floor of {MINIMUM_READABLE}: mapper fields or a registered metadata "
        "object have been removed rather than reconciled"
    )


# ---------------------------------------------------------------------------
# Second invariant: a readable table can still disagree about types.
#
# Reading succeeds whenever the *names* line up, so the ledger above says
# nothing about whether `Column(Integer)` sits over a `character varying`. That
# disagreement is invisible on INSERT -- parameter binding coerces, and the
# blood-bank write path passes `str(current_user.id)`, so it works today -- and
# fatal on comparison:
#
#     WHERE blood_bank_reservations.created_by = 42
#     UndefinedFunction: operator does not exist: character varying = integer
#
# So these are traps rather than outages, and they are recorded as traps. The
# first measurement of this said 35 tables, which was the instrument rather than
# the schema: rendering a column with `str(col.type)` gives SQLAlchemy's generic
# spelling, so every `Double` read as "DOUBLE vs double precision" and every
# UUID-backed TypeDecorator as "CHAR vs uuid" -- 54 false positives. Compiling
# under the PostgreSQL dialect, which is what actually reaches the database,
# gives 19 columns across 15 tables, and each was then confirmed by executing
# something against the real column rather than being assumed from the type
# names alone.
#
# The nine `trust_*` columns are a native enum over a plain varchar. Equality
# compares fine -- that was executed -- so the first reading was that they are
# harmless. They are not, and the difference is on the read side: the varchar
# column has no constraint restricting its values, while the mapper validates on
# result processing. Executed:
#
#     consentstatus.result_processor(...)("NOT_AN_ENUM_MEMBER")
#     LookupError: 'NOT_AN_ENUM_MEMBER' is not among the defined enum values
#
# So any row written by anything other than this mapper -- raw SQL, a data load,
# a migration -- with an off-list value is unreadable through the ORM, and the
# database will not stop it being written. They are recorded.
# ---------------------------------------------------------------------------

#: (table, column) -> (mapper type compiled for PostgreSQL, physical type).
#: All confirmed by executing a comparison against the real column.
DECLARED_TYPE_CONFLICTS: dict[tuple[str, str], tuple[str, str]] = {
    # `AuditMixin.created_by` is Integer. Six of the seven blood-bank tables
    # that inherit it were built with a varchar column; `blood_bank_transfusions`
    # was built with an integer one and agrees. The migrations disagreed with
    # each other, and the mapper can only match one of them.
    ("blood_bank_discards", "created_by"): ("integer", "character varying"),
    ("blood_bank_patient_samples", "created_by"): ("integer", "character varying"),
    ("blood_bank_reactions", "created_by"): ("integer", "character varying"),
    ("blood_bank_reservations", "created_by"): ("integer", "character varying"),
    ("blood_bank_returns", "created_by"): ("integer", "character varying"),
    ("blood_bank_traceability_events", "created_by"): ("integer", "character varying"),
    # Integer mappers over boolean columns. `x == True` compiles to `IS true`
    # and works; `x == 1` raises. `oauth2_tokens.is_revoked` is the one that
    # decides whether a token has been revoked.
    ("oauth2_clients", "is_active"): ("integer", "boolean"),
    ("oauth2_clients", "is_confidential"): ("integer", "boolean"),
    ("oauth2_tokens", "is_revoked"): ("integer", "boolean"),
    ("service_accounts", "is_active"): ("integer", "boolean"),
    # Native enum mappers over plain varchar columns. Equality works; the
    # exposure is on read, and the database enforces nothing.
    ("trust_compliance_checks", "result"): ("compliancestatus", "character varying"),
    ("trust_compliance_evidence", "status"): ("compliancestatus", "character varying"),
    ("trust_consent_records", "purpose"): ("consentpurpose", "character varying"),
    ("trust_consent_records", "status"): ("consentstatus", "character varying"),
    ("trust_retention_policies", "data_category"): ("datacategory", "character varying"),
    ("trust_retention_policies", "retention_period"): ("retentionpolicy", "character varying"),
    ("trust_service_logs", "service_type"): ("trustservicetype", "character varying"),
    ("trust_sovereignty_rules", "data_category"): ("datacategory", "character varying"),
    ("trust_sovereignty_rules", "sovereignty_level"): ("sovereigntylevel", "character varying"),
}

#: Types PostgreSQL resolves between without an explicit cast, so a difference
#: here is not a defect. Deliberately short: widening this list is how a real
#: conflict would be made to disappear.
_COMPATIBLE = frozenset({
    ("character varying", "text"), ("text", "character varying"),
    ("integer", "bigint"), ("bigint", "integer"),
    ("json", "jsonb"), ("jsonb", "json"),
    ("numeric", "double precision"), ("double precision", "numeric"),
    ("timestamp with time zone", "timestamp without time zone"),
    ("timestamp without time zone", "timestamp with time zone"),
})

_SPELLING = {
    "varchar": "character varying", "timestamp": "timestamp with time zone",
    "float": "double precision", "double": "double precision",
    "serial": "integer", "bigserial": "bigint", "bool": "boolean",
    "time": "time without time zone",
}


def _postgres_type(column) -> str:
    """What the mapper's type actually compiles to for PostgreSQL.

    `str(column.type)` gives the generic spelling and is the wrong instrument:
    it reports a difference for every `Double` and every UUID-backed
    TypeDecorator. An enum compiles to its own named type, which is left as-is
    so enum-over-varchar is visible rather than normalised away.
    """
    import re

    from sqlalchemy.dialects import postgresql

    try:
        rendered = column.type.compile(dialect=postgresql.dialect()).lower()
    except Exception:  # a type that cannot compile is reported in its raw spelling
        rendered = str(column.type).lower()
    stripped = re.sub(r"\(.*?\)", "", rendered).strip()
    return _SPELLING.get(stripped, stripped)


@pytest.fixture(scope="module")
def type_conflicts(registry, probe):
    """Every readable table's columns, compared by PostgreSQL-compiled type."""
    engine = sa.create_engine(_require_database())
    with engine.connect() as connection:
        physical: dict[str, dict[str, str]] = {}
        for table, column, data_type in connection.execute(sa.text(
            "SELECT table_name, column_name, data_type FROM information_schema.columns "
            "WHERE table_schema = 'public'",
        )):
            physical.setdefault(table, {})[column] = data_type
    engine.dispose()

    found: dict[tuple[str, str], tuple[str, str]] = {}
    seen: set[str] = set()
    for _label, metadata in registry:
        for name, table in metadata.tables.items():
            if name in seen or name not in probe["readable"]:
                continue
            seen.add(name)
            for column in table.columns:
                actual = physical[name].get(column.name)
                mapped = _postgres_type(column)
                if actual and mapped != actual and (mapped, actual) not in _COMPATIBLE:
                    found[(name, column.name)] = (mapped, actual)
    return found


def test_no_undeclared_type_conflict_between_a_mapper_and_its_column(type_conflicts):
    unexpected = {k: v for k, v in sorted(type_conflicts.items())
                  if k not in DECLARED_TYPE_CONFLICTS}
    assert not unexpected, (
        "these mapped columns disagree with their PostgreSQL type. Reading still "
        "works, so nothing else in this suite would notice, but a comparison "
        f"against them can raise UndefinedFunction: {unexpected}"
    )


def test_the_type_conflict_ledger_does_not_rot(type_conflicts):
    resolved = sorted(set(DECLARED_TYPE_CONFLICTS) - set(type_conflicts))
    assert not resolved, (
        f"these columns now agree and must be deleted from "
        f"DECLARED_TYPE_CONFLICTS: {resolved}"
    )


def test_the_recorded_type_conflicts_are_exact(type_conflicts):
    drifted = {
        key: {"declared": DECLARED_TYPE_CONFLICTS[key], "measured": measured}
        for key, measured in sorted(type_conflicts.items())
        if key in DECLARED_TYPE_CONFLICTS and measured != DECLARED_TYPE_CONFLICTS[key]
    }
    assert not drifted, f"the recorded types no longer match what is there: {drifted}"

"""Medical Ontology Core — canonical concepts, codes, synonyms, relations,
reference ranges, and unit conversions.

Revision ID: 20260908_0001
Revises    : 20260511_0002
Create Date: 2026-09-08

Operationalises directive §1 (Medical Ontology Core), §2 (Reference Range
Intelligence Engine), and §9 (Iraqi Medical Language Engine). Every table is
brand new; nothing existing is altered. All rows are seeded by
``scripts/seed_medical_ontology.py`` from ``data/ontology/*.yaml``; running
this migration does NOT populate anything.

Tables created
--------------
  1. medical_ontology_concepts       — canonical entities (biomarker, symptom,
                                       disease, medication, panel, organ_system,
                                       specimen, unit). Stable ``concept_key``
                                       slug is the join key everywhere else.
  2. medical_ontology_codes          — external code-system mappings (LOINC /
                                       SNOMEDCT / ICD10 / RxNorm / CPT).
                                       One concept → many codes.
  3. medical_ontology_synonyms       — multilingual terms + Iraqi dialect +
                                       Arabizi variants. Backs the
                                       normaliser (``services.medical_ontology.
                                       normalize``).
  4. medical_ontology_relations      — directed graph edges
                                       (panel_includes, part_of, indicates,
                                       is_a, associated_with, measured_in).
  5. medical_ontology_reference_ranges — demographic-aware normal/critical
                                       bands per (concept, unit, age band,
                                       sex, pregnancy status, specimen,
                                       analyzer). Provenance mandatory.
  6. medical_ontology_unit_conversions — canonical-unit + inter-unit
                                       conversion factors (optionally
                                       concept-scoped for mass↔molar).

Production-safety rules
-----------------------
  • All operations idempotent (``_table_exists`` / ``_index_exists`` guards).
  • Zero changes to existing tables — no ALTER, no data mutation.
  • All new tables start empty; loader is the only writer.
  • ``concept_key`` unique across the ontology so every row can be located by
    stable slug rather than opaque UUID.
  • ``ENABLE_MEDICAL_ONTOLOGY`` flag defaults OFF — tables exist but no code
    path reads them until the flag is flipped.

Downgrade
---------
Drops tables in reverse-dependency order. Safe on empty schemas; safe on
seeded schemas provided no ai_* rows FK into these tables (they do not).
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text
from sqlalchemy.dialects import postgresql
import contextlib


revision      = "20260908_0001"
down_revision = "20260908_0000"
branch_labels = None
depends_on    = None


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _table_exists(table: str) -> bool:
    return inspect(op.get_bind()).has_table(table)


def _index_exists(index: str) -> bool:
    inspector = inspect(op.get_bind())
    for table in inspector.get_table_names():
        if any(i["name"] == index for i in inspector.get_indexes(table)):
            return True
    return False


def _pg() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def _uuid_col() -> sa.types.TypeEngine:
    return postgresql.UUID(as_uuid=True) if _pg() else sa.String(36)


def _json_col() -> sa.types.TypeEngine:
    return postgresql.JSONB if _pg() else sa.JSON


# ─── Upgrade ─────────────────────────────────────────────────────────────────

def upgrade() -> None:
    if _pg():
        op.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))

    pk_default = sa.text("gen_random_uuid()") if _pg() else None
    now = sa.func.now()

    # 1. medical_ontology_concepts ────────────────────────────────────────────
    if not _table_exists("medical_ontology_concepts"):
        op.create_table(
            "medical_ontology_concepts",
            sa.Column("id", _uuid_col(), primary_key=True,
                      server_default=pk_default, nullable=False),
            sa.Column("concept_key", sa.String(128), nullable=False, unique=True),
            sa.Column("category", sa.String(32), nullable=False),
            sa.Column("display_en", sa.String(256), nullable=True),
            sa.Column("display_ar", sa.String(256), nullable=True),
            sa.Column("description_en", sa.Text(), nullable=True),
            sa.Column("description_ar", sa.Text(), nullable=True),
            sa.Column("canonical_unit_key", sa.String(128), nullable=True),
            sa.Column("default_specimen_key", sa.String(128), nullable=True),
            sa.Column("attributes", _json_col(), nullable=True),
            sa.Column("status", sa.String(16), nullable=False,
                      server_default=sa.text("'active'")),
            sa.Column("version", sa.Integer(), nullable=False,
                      server_default=sa.text("1")),
            sa.Column("source_provenance", sa.String(256), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True),
                      server_default=now, nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True),
                      server_default=now, nullable=False),
        )
    if not _index_exists("ix_medonto_concepts_category"):
        op.create_index("ix_medonto_concepts_category",
                        "medical_ontology_concepts", ["category"])
    if not _index_exists("ix_medonto_concepts_status"):
        op.create_index("ix_medonto_concepts_status",
                        "medical_ontology_concepts", ["status"])

    # 2. medical_ontology_codes ───────────────────────────────────────────────
    if not _table_exists("medical_ontology_codes"):
        op.create_table(
            "medical_ontology_codes",
            sa.Column("id", _uuid_col(), primary_key=True,
                      server_default=pk_default, nullable=False),
            sa.Column("concept_id", _uuid_col(),
                      sa.ForeignKey("medical_ontology_concepts.id",
                                    ondelete="CASCADE"),
                      nullable=False),
            sa.Column("code_system", sa.String(32), nullable=False),
            sa.Column("code", sa.String(64), nullable=False),
            sa.Column("display", sa.String(256), nullable=True),
            sa.Column("is_primary", sa.Boolean(), nullable=False,
                      server_default=sa.text("false")),
            sa.Column("created_at", sa.DateTime(timezone=True),
                      server_default=now, nullable=False),
            sa.UniqueConstraint("code_system", "code", "concept_id",
                                name="uq_medonto_codes_system_code_concept"),
        )
    if not _index_exists("ix_medonto_codes_lookup"):
        op.create_index("ix_medonto_codes_lookup",
                        "medical_ontology_codes",
                        ["code_system", "code"])
    if not _index_exists("ix_medonto_codes_concept"):
        op.create_index("ix_medonto_codes_concept",
                        "medical_ontology_codes", ["concept_id"])

    # 3. medical_ontology_synonyms ────────────────────────────────────────────
    if not _table_exists("medical_ontology_synonyms"):
        op.create_table(
            "medical_ontology_synonyms",
            sa.Column("id", _uuid_col(), primary_key=True,
                      server_default=pk_default, nullable=False),
            sa.Column("concept_id", _uuid_col(),
                      sa.ForeignKey("medical_ontology_concepts.id",
                                    ondelete="CASCADE"),
                      nullable=False),
            sa.Column("term", sa.String(256), nullable=False),
            sa.Column("term_normalized", sa.String(256), nullable=False),
            sa.Column("locale", sa.String(16), nullable=False),
            sa.Column("variant", sa.String(24), nullable=True),
            sa.Column("source", sa.String(64), nullable=True),
            sa.Column("confidence", sa.Float(), nullable=False,
                      server_default=sa.text("1.0")),
            sa.Column("created_at", sa.DateTime(timezone=True),
                      server_default=now, nullable=False),
            sa.UniqueConstraint("concept_id", "term_normalized", "locale",
                                name="uq_medonto_syn_concept_norm_locale"),
        )
    if not _index_exists("ix_medonto_syn_norm"):
        op.create_index("ix_medonto_syn_norm",
                        "medical_ontology_synonyms",
                        ["term_normalized"])
    if not _index_exists("ix_medonto_syn_norm_locale"):
        op.create_index("ix_medonto_syn_norm_locale",
                        "medical_ontology_synonyms",
                        ["term_normalized", "locale"])
    if not _index_exists("ix_medonto_syn_concept"):
        op.create_index("ix_medonto_syn_concept",
                        "medical_ontology_synonyms", ["concept_id"])

    # 4. medical_ontology_relations ───────────────────────────────────────────
    if not _table_exists("medical_ontology_relations"):
        op.create_table(
            "medical_ontology_relations",
            sa.Column("id", _uuid_col(), primary_key=True,
                      server_default=pk_default, nullable=False),
            sa.Column("source_concept_id", _uuid_col(),
                      sa.ForeignKey("medical_ontology_concepts.id",
                                    ondelete="CASCADE"),
                      nullable=False),
            sa.Column("target_concept_id", _uuid_col(),
                      sa.ForeignKey("medical_ontology_concepts.id",
                                    ondelete="CASCADE"),
                      nullable=False),
            sa.Column("relation_type", sa.String(32), nullable=False),
            sa.Column("strength", sa.Float(), nullable=True),
            sa.Column("provenance", sa.String(128), nullable=True),
            sa.Column("attributes", _json_col(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True),
                      server_default=now, nullable=False),
            sa.UniqueConstraint("source_concept_id", "target_concept_id",
                                "relation_type",
                                name="uq_medonto_rel_src_tgt_type"),
        )
    if not _index_exists("ix_medonto_rel_type"):
        op.create_index("ix_medonto_rel_type",
                        "medical_ontology_relations", ["relation_type"])
    if not _index_exists("ix_medonto_rel_source"):
        op.create_index("ix_medonto_rel_source",
                        "medical_ontology_relations", ["source_concept_id"])
    if not _index_exists("ix_medonto_rel_target"):
        op.create_index("ix_medonto_rel_target",
                        "medical_ontology_relations", ["target_concept_id"])

    # 5. medical_ontology_reference_ranges ────────────────────────────────────
    if not _table_exists("medical_ontology_reference_ranges"):
        op.create_table(
            "medical_ontology_reference_ranges",
            sa.Column("id", _uuid_col(), primary_key=True,
                      server_default=pk_default, nullable=False),
            sa.Column("concept_id", _uuid_col(),
                      sa.ForeignKey("medical_ontology_concepts.id",
                                    ondelete="CASCADE"),
                      nullable=False),
            sa.Column("unit_key", sa.String(128), nullable=False),
            sa.Column("age_min_years", sa.Float(), nullable=True),
            sa.Column("age_max_years", sa.Float(), nullable=True),
            sa.Column("sex", sa.String(8), nullable=False,
                      server_default=sa.text("'any'")),
            sa.Column("pregnancy_status", sa.String(24), nullable=False,
                      server_default=sa.text("'any'")),
            sa.Column("specimen_key", sa.String(128), nullable=True),
            sa.Column("analyzer", sa.String(64), nullable=True),
            sa.Column("lab_id", sa.Integer(),
                      sa.ForeignKey("labs.id", ondelete="CASCADE"),
                      nullable=True),
            sa.Column("low", sa.Float(), nullable=True),
            sa.Column("high", sa.Float(), nullable=True),
            sa.Column("critical_low", sa.Float(), nullable=True),
            sa.Column("critical_high", sa.Float(), nullable=True),
            sa.Column("severity_bands", _json_col(), nullable=True),
            sa.Column("source", sa.String(64), nullable=False),
            sa.Column("source_version", sa.String(64), nullable=True),
            sa.Column("source_url", sa.String(512), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("status", sa.String(16), nullable=False,
                      server_default=sa.text("'active'")),
            sa.Column("created_at", sa.DateTime(timezone=True),
                      server_default=now, nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True),
                      server_default=now, nullable=False),
        )
    if not _index_exists("ix_medonto_ranges_concept"):
        op.create_index("ix_medonto_ranges_concept",
                        "medical_ontology_reference_ranges",
                        ["concept_id"])
    if not _index_exists("ix_medonto_ranges_lookup"):
        op.create_index("ix_medonto_ranges_lookup",
                        "medical_ontology_reference_ranges",
                        ["concept_id", "status", "lab_id"])

    # 6. medical_ontology_unit_conversions ────────────────────────────────────
    if not _table_exists("medical_ontology_unit_conversions"):
        op.create_table(
            "medical_ontology_unit_conversions",
            sa.Column("id", _uuid_col(), primary_key=True,
                      server_default=pk_default, nullable=False),
            sa.Column("from_unit_key", sa.String(128), nullable=False),
            sa.Column("to_unit_key", sa.String(128), nullable=False),
            sa.Column("factor", sa.Float(), nullable=False),
            sa.Column("offset", sa.Float(), nullable=False,
                      server_default=sa.text("0")),
            sa.Column("concept_scope_key", sa.String(128), nullable=True),
            sa.Column("source", sa.String(128), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True),
                      server_default=now, nullable=False),
            sa.UniqueConstraint("from_unit_key", "to_unit_key",
                                "concept_scope_key",
                                name="uq_medonto_units_from_to_scope"),
        )
    if not _index_exists("ix_medonto_units_lookup"):
        op.create_index("ix_medonto_units_lookup",
                        "medical_ontology_unit_conversions",
                        ["from_unit_key", "to_unit_key",
                         "concept_scope_key"])


# ─── Downgrade ───────────────────────────────────────────────────────────────

_DROP_ORDER = [
    ("medical_ontology_unit_conversions",
     ["ix_medonto_units_lookup"]),
    ("medical_ontology_reference_ranges",
     ["ix_medonto_ranges_lookup", "ix_medonto_ranges_concept"]),
    ("medical_ontology_relations",
     ["ix_medonto_rel_target", "ix_medonto_rel_source", "ix_medonto_rel_type"]),
    ("medical_ontology_synonyms",
     ["ix_medonto_syn_concept", "ix_medonto_syn_norm_locale",
      "ix_medonto_syn_norm"]),
    ("medical_ontology_codes",
     ["ix_medonto_codes_concept", "ix_medonto_codes_lookup"]),
    ("medical_ontology_concepts",
     ["ix_medonto_concepts_status", "ix_medonto_concepts_category"]),
]


def downgrade() -> None:
    for table, indexes in _DROP_ORDER:
        if not _table_exists(table):
            continue
        for idx in indexes:
            if _index_exists(idx):
                with contextlib.suppress(Exception):
                    op.drop_index(idx, table_name=table)
        with contextlib.suppress(Exception):
            op.drop_table(table)

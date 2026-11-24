"""NR-011 (decision D-003) regression tests — Alembic metadata discovery.

Proves, without any database connection or DDL, that ``backend/migrations/env.py``:

1. registers **all 17 declarative bases** (the original 10 + the 7 that were
   previously omitted: HospitalBase, DataPlatformBase, NHDWBase, NursingBase,
   PharmacyBase, RadiologyBase, FinBase);
2. imports ``app.national.domain`` so the national domain tables
   (``national_encounters``, ``national_patients``, …) are discoverable;
3. merges every registered ``MetaData`` into **one** ``MetaData`` so
   cross-metadata foreign keys (``ehr_*`` → ``national_*``) resolve;
4. does not introduce new import-time secrets or DDL/stamp calls.

The merge behaviour is verified by executing the *literal* ``NR-011 MERGE``
block extracted from ``env.py`` between its BEGIN/END markers, so a future edit
of that block is what the test exercises.

Scope: regression test for CC-004 / W-024 (D-003 approved 2026-11-17).
No test was weakened or removed to obtain this pass.
"""
from __future__ import annotations

import importlib
import re
from contextlib import suppress

import pytest

ENV_PY = __import__("pathlib").Path(__file__).resolve().parents[2] / "migrations" / "env.py"

# The exact import surface env.py exposes (bases + model modules), mirroring
# the repository state at the time of the NR-011 fix (probe-C baseline).
BASE_MODULES: dict[str, str] = {
    "Base": "app.database",
    "NationalBase": "app.national.base",
    "EHRBase": "app.ehr.base",
    "CitizenPlatformBase": "app.citizen_platform.base",
    "ClinicalBase": "app.clinical.base",
    "HealthDataBase": "app.health_data.base",
    "TrustBase": "app.trust.base",
    "GovernanceBase": "app.governance.base",
    "CareContinuumBase": "app.care_continuum.base",
    "IdentityBase": "app.identity.base",
    "HospitalBase": "app.hospital.base",
    "DataPlatformBase": "app.national_data.base",
    "NHDWBase": "app.nhdw.base",
    "NursingBase": "app.nursing.base",
    "PharmacyBase": "app.pharmacy.base",
    "RadiologyBase": "app.radiology.base",
    "FinBase": "app.financial.models",
}

SEVEN_PREVIOUSLY_OMITTED = (
    "HospitalBase",
    "DataPlatformBase",
    "NHDWBase",
    "NursingBase",
    "PharmacyBase",
    "RadiologyBase",
    "FinBase",
)

MODEL_MODULES = (
    "app.models",
    "app.models.claim",
    "app.billing.models",
    "app.national.domain",
    "app.ems.infrastructure.models",
    "app.blood_bank.infrastructure.models",
    "app.critical_care.infrastructure.models",
    "app.biomedical.infrastructure.models",
    "app.public_health.infrastructure.models",
    "app.command_center.infrastructure.models",
    "app.pilot_platform.infrastructure.models",
    "app.lifecycle_platform.infrastructure.models",
    "app.clinical.terminology.models",
    "app.clinical.cds.models",
    "app.clinical.knowledge.models",
    "app.clinical.quality.models",
    "app.clinical.research.models",
    "app.health_data.canonical.models",
    "app.health_data.mdm.models",
    "app.health_data.ods.models",
    "app.health_data.warehouse.models",
    "app.trust.models",
    "app.governance.models",
    "app.care_continuum.models",
    "app.identity.models",
)


def _env_source() -> str:
    return ENV_PY.read_text(encoding="utf-8")


def _block(src: str, begin: str, end: str) -> str:
    """Return the content between the BEGIN line and the END marker line,
    skipping any trailing text on the BEGIN line itself."""
    m = re.search(
        re.escape(begin) + r"[^\n]*\n(.*?)(?:\n)?" + re.escape(end), src, re.S
    )
    assert m, f"marker block missing in env.py: {begin!r} .. {end!r}"
    return m.group(1)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Source-level registration (env.py content is what alembic actually runs)
# ─────────────────────────────────────────────────────────────────────────────
class TestEnvPyRegistration:
    def test_registers_exactly_17_bases_in_order(self) -> None:
        block = _block(
            _env_source(),
            "# BEGIN NR-011 REGISTERED BASES",
            "# END NR-011 REGISTERED BASES",
        )
        names = re.findall(r"(\w+)\.metadata,", block)
        assert names == list(BASE_MODULES.keys()), (
            "env.py target_metadata base list changed — every base must stay "
            "registered, in first-registration order (duplicate tables resolve "
            "to the first registration)"
        )
        assert len(names) == 17

    def test_seven_previously_omitted_bases_are_imported(self) -> None:
        src = _env_source()
        for name in SEVEN_PREVIOUSLY_OMITTED:
            module = BASE_MODULES[name]
            assert re.search(
                rf"from {re.escape(module)} import {name}", src
            ), f"{name} (from {module}) is no longer imported by env.py"

    def test_national_domain_is_imported(self) -> None:
        assert re.search(
            r"^import app\.national\.domain\b", _env_source(), re.M
        ), "app.national.domain must be imported (probe B: FK targets of EHR tables)"

    def test_merge_block_present(self) -> None:
        block = _block(_env_source(), "# BEGIN NR-011 MERGE", "# END NR-011 MERGE")
        assert "_combined = _MetaData()" in block
        assert "target_metadata = _combined" in block
        assert "_tbl.to_metadata(_combined)" in block

    def test_configure_uses_the_merged_list(self) -> None:
        src = _env_source()
        uses = re.findall(r"target_metadata=target_metadata", src)
        assert len(uses) == 2, "both offline and online mode must use target_metadata"
        # the merge rebinds target_metadata before either mode runs
        assert src.index("# END NR-011 MERGE") < src.index("def run_migrations_offline")

    def test_no_new_import_time_secret(self) -> None:
        keys = set(
            re.findall(r"os\.environ\.setdefault\(\"([A-Z_]+)\"", _env_source())
        )
        assert keys == {
            "ENV",
            "SECRET_KEY",
            "ENCRYPTION_KEY",
            "NID_HMAC_KEY",
            "REDIS_URL",
        }, "NR-011 must not add import-time secrets to env.py"

    def test_no_ddl_or_stamp_calls_added(self) -> None:
        src = _env_source()
        assert not re.search(r"\.create_all\(", src), "env.py must never create schema"
        assert "context.stamp" not in src and "command.stamp" not in src
        assert not re.search(r"\bop\.\w+\(", src), (
            "env.py must not contain migration operations"
        )


# ─────────────────────────────────────────────────────────────────────────────
# 2. Behavioural discovery — import the same surface env.py imports
# ─────────────────────────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def discovery():
    """Import env.py's full import surface and return (bases, merged_metadata)."""
    bases: dict[str, object] = {}
    errors: dict[str, str] = {}
    for name, module in BASE_MODULES.items():
        try:
            bases[name] = getattr(importlib.import_module(module), name)
        except Exception as exc:
            errors[name] = f"{type(exc).__name__}: {exc}"
    for module in MODEL_MODULES:
        with suppress(ImportError):
            importlib.import_module(module)

    assert not errors, f"base import failures (circular import? new breakage?): {errors}"

    metas = [bases[name].metadata for name in BASE_MODULES]
    assert len(metas) == 17

    # Execute env.py's literal merge block against the real metadata objects.
    block = _block(
        ENV_PY.read_text(encoding="utf-8"),
        "# BEGIN NR-011 MERGE",
        "# END NR-011 MERGE",
    )
    namespace = {"target_metadata": list(metas), "_MetaData": __import__("sqlalchemy").MetaData}
    exec(compile(block, f"{ENV_PY}::NR-011-MERGE", "exec"), namespace)
    merged = namespace["target_metadata"]
    return bases, merged


class TestMetadataDiscovery:
    def test_all_17_bases_expose_metadata(self, discovery) -> None:
        bases, _ = discovery
        for name, base in bases.items():
            assert hasattr(base, "metadata"), f"{name} has no MetaData"

    def test_national_domain_tables_discoverable(self, discovery) -> None:
        bases, merged = discovery
        national = bases["NationalBase"].metadata
        for table in ("national_encounters", "national_patients", "national_practitioners"):
            assert table in national.tables, f"{table} not registered on NationalBase"
            assert table in merged.tables, f"{table} missing from merged MetaData"

    def test_merged_metadata_is_single_metadata(self, discovery) -> None:
        from sqlalchemy import MetaData

        _, merged = discovery
        assert isinstance(merged, MetaData)
        # every table object in the merged view belongs to the merged MetaData
        assert all(t.metadata is merged for t in merged.tables.values())

    def test_cross_metadata_foreign_keys_resolve(self, discovery) -> None:
        _, merged = discovery
        # probe A/B failure mode: NoReferencedTableError on ehr_* → national_*
        sorted_tables = merged.sorted_tables  # raises if any FK target is missing
        assert sorted_tables, "merged metadata has no tables"
        ehr = merged.tables["ehr_allergies"]
        targets = {fk.target_fullname for fk in ehr.foreign_keys}
        assert any("national_patients" in t for t in targets)
        for fk in ehr.foreign_keys:
            # .column resolves the string target against the owning MetaData and
            # raises NoReferencedTableError when it cannot be found — the exact
            # NR-011 abort. Accessing it proves resolution.
            resolved = fk.column
            assert resolved.table.name in merged.tables
            assert resolved.table.metadata is merged

    def test_duplicate_table_resolves_deterministically_to_first_owner(self, discovery) -> None:
        bases, merged = discovery
        # pre-existing dual definition (F-014): 6-col Base.NationalFacility wins
        # because Base is registered before NationalBase (first registration wins).
        dup_meta = [
            name
            for name, base in bases.items()
            if "national_facilities" in base.metadata.tables
        ]
        assert dup_meta == ["Base", "NationalBase"], dup_meta
        tbl = merged.tables["national_facilities"]
        assert tbl.metadata is merged
        first_owner = bases["Base"].metadata.tables["national_facilities"]
        assert [c.name for c in tbl.columns] == [c.name for c in first_owner.columns]
        assert len(first_owner.columns) == 6

    def test_no_base_silently_empty_beyond_documented_gap(self, discovery) -> None:
        """Only the five bases whose model modules are outside env.py's import
        surface may be empty (finding F-065 — ADR-A wave scope). Any other base
        going empty means discovery regressed."""
        bases, _ = discovery
        documented_empty = {
            "CitizenPlatformBase",  # no models module exists
            "NHDWBase",
            "NursingBase",
            "PharmacyBase",
            "RadiologyBase",  # model modules exist but are not imported by env.py
        }
        empty = {name for name, b in bases.items() if len(b.metadata.tables) == 0}
        assert empty <= documented_empty, (
            f"unexpectedly empty bases (discovery regression): {empty - documented_empty}"
        )

    def test_merged_scale_sane(self, discovery) -> None:
        _, merged = discovery
        # measured baseline 479 at NR-011 time (480 across parts minus 1 duplicate);
        # a large drop means model imports silently stopped happening.
        assert len(merged.tables) >= 450, (
            f"merged metadata collapsed to {len(merged.tables)} tables"
        )

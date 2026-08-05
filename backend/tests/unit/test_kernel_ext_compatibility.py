"""Unit tests for GULA-KERNEL-EXT-001 Phase 3 — Compatibility Framework."""

from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.kernel.core import ENGINE_REGISTRY, KERNEL_CONTRACT_FIELDS
from scripts.kernel.ext.compatibility import (
    CompatibilityError,
    CompatibilityMatrix,
    CompatibilityRecord,
    compare_versions,
    engine_matrix,
    is_breaking_change,
    is_contract_conformant,
    parse_version,
    check_contract,
)


class TestSemVer:
    def test_parse_valid(self):
        assert parse_version("1.2.3") == (1, 2, 3)

    def test_parse_invalid(self):
        for bad in ("1.2", "1.2.x", "v1.2.3", "01.2.3", "1.2.3.4", ""):
            with pytest.raises(CompatibilityError):
                parse_version(bad)

    def test_compare(self):
        assert compare_versions("1.0.0", "2.0.0") == -1
        assert compare_versions("2.0.0", "1.9.9") == 1
        assert compare_versions("1.2.3", "1.2.3") == 0

    def test_breaking_only_major(self):
        assert is_breaking_change("1.0.0", "2.0.0")
        assert not is_breaking_change("1.0.0", "1.1.0")
        assert not is_breaking_change("1.0.0", "1.0.1")


class TestContractCheck:
    def test_kernel_fields_exist(self):
        assert len(KERNEL_CONTRACT_FIELDS) == 16

    def test_all_engines_conformant(self):
        for engine, contract in ENGINE_REGISTRY.items():
            assert check_contract(contract) == [], engine

    def test_is_contract_conformant(self):
        assert is_contract_conformant(ENGINE_REGISTRY["architect"])

    def test_missing_field_detected(self):
        missing = dict(ENGINE_REGISTRY["architect"])
        missing.pop("version")
        assert check_contract(missing) == ["version"]
        assert not is_contract_conformant(missing)


class TestMatrix:
    def test_add_and_entries(self):
        matrix = CompatibilityMatrix()
        matrix.add("plugin", "demo", "1.0.0", "1.1.0", True)
        assert len(matrix.entries()) == 1
        assert len(matrix.entries("plugin")) == 1
        assert matrix.entries("policy") == []

    def test_add_invalid_kind(self):
        matrix = CompatibilityMatrix()
        with pytest.raises(CompatibilityError):
            matrix.add("nope", "x", "1.0.0", "1.1.0", True)

    def test_add_invalid_version(self):
        matrix = CompatibilityMatrix()
        with pytest.raises(CompatibilityError):
            matrix.add("plugin", "x", "1.0", "1.1.0", True)

    def test_breaking_and_is_compatible(self):
        matrix = CompatibilityMatrix()
        matrix.add("plugin", "demo", "1.0.0", "1.1.0", True)
        matrix.add("plugin", "demo", "1.1.0", "2.0.0", False, "renamed entrypoint")
        assert matrix.is_compatible("demo") is False
        assert matrix.for_name("demo")[1].compatible is False

    def test_is_compatible_no_records(self):
        assert CompatibilityMatrix().is_compatible("anything") is True

    def test_unknown_name_defaults_compatible(self):
        matrix = CompatibilityMatrix()
        matrix.add("plugin", "demo", "1.0.0", "1.1.0", False)
        assert matrix.is_compatible("other") is True

    def test_snapshot_roundtrip(self, tmp_path):
        matrix = CompatibilityMatrix()
        matrix.add("contract", "architect", "1.0.0", "1.1.0", True)
        matrix.add("schema", "patient", "1.0.0", "2.0.0", False, "drop field")
        path = matrix.save(tmp_path / "compat.json")
        loaded = CompatibilityMatrix.load(path)
        assert [r.to_dict() for r in loaded.records] == [r.to_dict() for r in matrix.records]

    def test_render_markdown(self):
        matrix = CompatibilityMatrix()
        matrix.add("contract", "architect", "1.0.0", "1.1.0", True)
        rendered = matrix.render_markdown()
        assert "# COMPATIBILITY MATRIX" in rendered
        assert "architect" in rendered
        assert "PASS" in rendered

    def test_engine_matrix_all_pass(self):
        matrix = engine_matrix(ENGINE_REGISTRY)
        assert len(matrix.entries("contract")) == len(ENGINE_REGISTRY)
        assert matrix.breaking() == []

    def test_engine_matrix_detects_broken(self):
        broken = dict(ENGINE_REGISTRY)
        architect = dict(broken["architect"])
        architect.pop("capabilities")
        broken["architect"] = architect
        matrix = engine_matrix(broken)
        breaking = matrix.breaking()
        assert len(breaking) == 1
        assert breaking[0].name == "architect"


class TestRecord:
    def test_record_defaults_timestamp(self):
        record = CompatibilityRecord("plugin", "demo", "1.0.0", "1.1.0", True)
        assert record.checked_at

"""Verify every curated code and provenance claim against the offline checkout.

These tests read source files only. They extract literals with the AST (not
string matching) so a claim such as "the UCUM set came from validation.py" is
checked against the file itself.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
from app.health_core.terminology import (
    CHECKOUT_HEAD,
    CHECK_DIGIT_CANONICAL_URL,
    ICD10_CODES,
    ICD10_RELEASE,
    LOINC_CODES,
    LOINC_RELEASE,
    TERMINOLOGY_RELEASES,
    UCUM_RELEASE,
    UCUM_UNITS,
    VERIFICATION_DATE,
    CheckDigitOutcome,
    CheckDigitStatus,
    CoverageLevel,
    IcdValidator,
    LoincValidator,
    TerminologySystem,
    all_releases,
    compute_loinc_check_digit,
    validate_loinc_check_digit,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def _read(relative_path: str) -> str:
    path = REPO_ROOT / relative_path
    assert path.is_file(), f"missing offline source: {relative_path}"
    return path.read_text(encoding="utf-8")


def _assigned_value(relative_path: str, name: str) -> ast.AST:
    tree = ast.parse(_read(relative_path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name for target in node.targets
        ):
            return node.value
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == name:
            assert node.value is not None, f"{name} has no assigned value"
            return node.value
    raise AssertionError(f"{name} not assigned in {relative_path}")


def _string_constants(node: ast.AST) -> set[str]:
    return {item.value for item in ast.walk(node) if isinstance(item, ast.Constant) and isinstance(item.value, str)}


def _source_line(source_ref: str) -> str:
    relative_path, _, line_text = source_ref.rpartition(":")
    line_number = int(line_text)
    lines = _read(relative_path).splitlines()
    assert 1 <= line_number <= len(lines), f"source ref out of range: {source_ref}"
    return lines[line_number - 1]


VALIDATION = "backend/app/health_core/clinical/validation.py"
FHIR_TERMINOLOGY = "backend/app/fhir/terminology.py"
CDS_ENGINE = "backend/app/national/services/cds_engine.py"
INTEGRATIONS_STATUS = "backend/app/routes/advanced_integrations.py"
FHIR_REFERENCE = "backend/app/fhir/_reference.py"
STANDARDS_TERMINOLOGY = "backend/app/integration/standards/terminology.py"


def test_every_curated_entry_points_to_a_line_containing_its_code() -> None:
    for entries in (ICD10_CODES, LOINC_CODES, UCUM_UNITS):
        for entry in entries:
            line = _source_line(entry.source_ref)
            assert entry.code in line, f"{entry.code} not found at {entry.source_ref}: {line}"


def test_ucum_curated_set_equals_offline_ucum_units_allowlist() -> None:
    value = _assigned_value(VALIDATION, "UCUM_UNITS")
    assert isinstance(value, ast.Call)
    assert isinstance(value.func, ast.Name) and value.func.id == "frozenset"
    offline = _string_constants(value)
    curated = {entry.code for entry in UCUM_UNITS}
    assert offline == curated
    assert len(offline) == 15


def test_loinc_curated_set_includes_every_controlled_fhir_mapping() -> None:
    value = _assigned_value(FHIR_TERMINOLOGY, "_COMMON_LOINC_CODES")
    offline: set[str] = set()
    for item in ast.walk(value):
        if (
            isinstance(item, ast.Call)
            and isinstance(item.func, ast.Name)
            and item.func.id == "LaboratoryCode"
            and item.args
        ):
            first = item.args[0]
            if isinstance(first, ast.Constant) and isinstance(first.value, str):
                offline.add(first.value)
    curated = {
        entry.code for entry in LOINC_CODES if "fhir/terminology.py" in entry.source_ref
    }
    assert offline == curated
    assert len(offline) == 11


def test_loinc_curated_set_includes_every_health_core_code_unit_key() -> None:
    value = _assigned_value(VALIDATION, "CODE_UNITS")
    assert isinstance(value, ast.Dict)
    offline = {
        key.value
        for key in value.keys
        if isinstance(key, ast.Constant) and isinstance(key.value, str)
    }
    curated = {
        entry.code for entry in LOINC_CODES if "clinical/validation.py" in entry.source_ref
    }
    assert offline == curated
    assert len(offline) == 5


def test_icd_codes_are_actually_tagged_as_icd10_in_the_offline_source() -> None:
    engine_text = _read(CDS_ENGINE)
    validation_text = _read(VALIDATION)
    for entry in ICD10_CODES:
        assert entry.code in _source_line(entry.source_ref)
    for entry in ICD10_CODES:
        if "cds_engine.py" in entry.source_ref:
            assert '"system": "ICD10"' in _source_line(entry.source_ref)
        else:
            assert "e.g. ``J18.9``" in validation_text
    assert '"system": "ICD10"' in engine_text
    assert "ICD-style code (e.g. ``J18.9``)" in validation_text


def test_structural_patterns_are_documented_including_the_loinc_discrepancy() -> None:
    text = _read(VALIDATION)
    assert r'ICD_CODE_RE = re.compile(r"^[A-TV-Z][0-9]{2}(?:\.[0-9A-Z]{1,4})?$")' in text
    assert r'LOINC_CODE_RE = re.compile(r"^[0-9]{4,6}-[0-9]$")' in text
    result = IcdValidator().validate("J18.9")
    assert result.status.value == "VALID"
    assert result.release.version == "UNDECLARED"
    # The offline pattern rejects two codes that the same checkout curates.
    assert "3-6 digit structural pattern" in LOINC_RELEASE.notes
    assert LoincValidator().validate("718-7").status.value == "VALID"
    assert LoincValidator().validate("777-3").status.value == "VALID"
    assert "718-7" in _read(FHIR_TERMINOLOGY)


def test_declared_versions_are_copied_from_offline_sources_not_invented() -> None:
    status_text = _read(INTEGRATIONS_STATUS)
    assert '"LOINC", "version": "2.81"' in status_text
    assert '"ICD-11", "version": "2026"' in status_text
    assert LOINC_RELEASE.version == "2.81"
    assert ICD10_RELEASE.version == "UNDECLARED"
    assert UCUM_RELEASE.version == "UNDECLARED"
    assert "ICD-11" in ICD10_RELEASE.notes
    assert "different code system" in ICD10_RELEASE.notes
    assert "declared runtime status value" in LOINC_RELEASE.notes


def test_canonical_uris_are_present_in_offline_reference_sources() -> None:
    reference_text = _read(FHIR_REFERENCE)
    standards_text = _read(STANDARDS_TERMINOLOGY)
    for release in all_releases():
        assert release.canonical_uri in reference_text or release.canonical_uri in standards_text
    assert LOINC_RELEASE.canonical_uri == "http://loinc.org"
    assert ICD10_RELEASE.canonical_uri == "http://hl7.org/fhir/sid/icd-10"
    assert UCUM_RELEASE.canonical_uri == "http://unitsofmeasure.org"


def test_licence_statements_cite_offline_policy_sources() -> None:
    policy = _read("GLOSI/SECURITY_AND_LICENSE_POLICY.md")
    catalog = _read("GLOSI/SOURCE_CATALOG.md")
    assert "SNOMED/LOINC/ICD" in policy
    assert "ترخيص LOINC" in catalog
    assert "ICD | https://icd.who.int/" in catalog
    assert "UCUM | https://ucum.org/" in catalog
    for release in all_releases():
        assert "GLOSI/" in release.license
        assert release.license not in {"", "UNKNOWN", "NONE"}


def test_check_digit_uses_official_algorithm_with_declared_boundaries() -> None:
    """Phase B M5 supersedes the old 'not implemented' contract.

    A curated numeric LOINC code now carries a locally recomputed official
    check digit (VERIFIED). The honest boundaries are retained and asserted:
    the letter-prefixed Algorithm C.2 remains NOT_IMPLEMENTED, licensed release
    dataset acquisition remains BLOCKED, and coverage stays PARTIALLY_VERIFIED.
    """
    result = LoincValidator().validate("8867-4")
    assert result.status.value == "VALID"
    assert result.check_digit is CheckDigitStatus.VERIFIED
    assert "official LOINC Mod-10 check digit recomputed" in result.reason

    # Provenance names the authoritative source and the hand-verified vectors.
    assert CHECK_DIGIT_CANONICAL_URL == "https://loinc.org/check-digit"
    assert CHECK_DIGIT_CANONICAL_URL in LOINC_RELEASE.notes
    for vector in ("12345->5", "718->7", "777->3", "4544->3", "2345->7"):
        assert vector in LOINC_RELEASE.notes
    assert "Appendix C.2, which is NOT IMPLEMENTED" in LOINC_RELEASE.notes
    assert "licensed acquisition remains BLOCKED" in LOINC_RELEASE.notes
    assert "coverage remains PARTIALLY_VERIFIED" in LOINC_RELEASE.notes
    assert "check-digit" in (LoincValidator.__doc__ or "").lower()

    # Static implementation module: no network/runtime dependency.
    checkdigit_source = (
        REPO_ROOT / "backend/app/health_core/terminology/checkdigit.py"
    ).read_text(encoding="utf-8")
    assert "def compute_loinc_check_digit" in checkdigit_source
    assert "def validate_loinc_check_digit" in checkdigit_source
    assert compute_loinc_check_digit("12345") == 5

    # Letter-prefixed codes fail closed (Appendix C.2 out of scope).
    prefixed = validate_loinc_check_digit("LP123-4")
    assert prefixed.status is CheckDigitOutcome.NOT_IMPLEMENTED
    assert not prefixed.valid

    # Diagnostics are fixed constants: no caller-controlled value is echoed.
    malformed = validate_loinc_check_digit("8867-4\x00")
    assert malformed.status is CheckDigitOutcome.MALFORMED
    assert "\x00" not in malformed.reason


def test_no_official_release_dataset_is_bundled_in_the_package() -> None:
    package_dir = REPO_ROOT / "backend/app/health_core/terminology"
    files = sorted(package_dir.rglob("*"))
    python_files = [path for path in files if path.is_file() and path.suffix == ".py"]
    data_files = [path for path in files if path.is_file() and path.suffix in {".json", ".csv", ".xml", ".zip"}]
    assert len(python_files) >= 8
    assert data_files == []
    forbidden_roots = {"httpx", "requests", "socket", "urllib", "sqlalchemy", "alembic"}
    for path in python_files:
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            module = ""
            if isinstance(node, ast.ImportFrom) and node.module:
                module = node.module.split(".")[0]
            elif isinstance(node, ast.Import) and node.names:
                module = node.names[0].name.split(".")[0]
            if module:
                assert module not in forbidden_roots, f"{path.name} imports {module}"


@pytest.mark.parametrize("release", all_releases(), ids=lambda release: release.system)
def test_provenance_metadata_is_complete_and_consistent(release) -> None:
    assert release.system in {system.value for system in TerminologySystem}
    assert release.version
    assert release.canonical_uri.startswith("http://")
    assert release.source.startswith("offline checkout:")
    assert release.verification_method
    assert CHECKOUT_HEAD in release.verification_method
    assert release.license
    assert release.verified_on == VERIFICATION_DATE
    assert release.coverage is CoverageLevel.PARTIALLY_VERIFIED
    assert release.coverage is not CoverageLevel.FULL_RELEASE
    payload = release.to_dict()
    assert len(payload) == 9
    assert payload["coverage"] == CoverageLevel.PARTIALLY_VERIFIED.value
    assert payload["system"] == release.system


def test_release_registry_contains_exactly_three_partially_verified_records() -> None:
    assert set(TERMINOLOGY_RELEASES) == {system.value for system in TerminologySystem}
    assert all(release.coverage is CoverageLevel.PARTIALLY_VERIFIED for release in TERMINOLOGY_RELEASES.values())
    assert all(release.verified_on == VERIFICATION_DATE for release in TERMINOLOGY_RELEASES.values())

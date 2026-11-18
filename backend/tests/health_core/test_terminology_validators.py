"""Behavioural tests for the release-aware terminology adapters.

Every accept/reject is asserted against a structured result that carries the
release record used. No test is skipped; unknown codes must be UNVERIFIED or
INVALID, never silently accepted.
"""

from __future__ import annotations

import pytest
from app.health_core.terminology import (
    ICD10_CODES,
    LOINC_CODES,
    TERMINOLOGY_RELEASES,
    UCUM_UNITS,
    CheckDigitStatus,
    CoverageLevel,
    IcdValidator,
    LoincValidator,
    TerminologyError,
    TerminologySystem,
    TerminologyValidator,
    UcumValidator,
    UnknownTerminologySystemError,
    ValidationStatus,
    VerificationStage,
    all_releases,
    all_validator_releases,
    compute_loinc_check_digit,
    get_release,
    get_validator,
    validator_systems,
)

ADAPTERS = (
    (TerminologySystem.ICD10, IcdValidator),
    (TerminologySystem.LOINC, LoincValidator),
    (TerminologySystem.UCUM, UcumValidator),
)


def test_all_adapters_satisfy_the_validator_protocol() -> None:
    for system, adapter_type in ADAPTERS:
        validator = get_validator(system)
        assert isinstance(validator, adapter_type)
        assert isinstance(validator, TerminologyValidator)
        assert validator.system == system.value
        assert validator.release is validator.provenance()
        assert validator.release.system == system.value


def test_registry_returns_the_correct_validator_and_fails_closed() -> None:
    assert validator_systems() == tuple(system.value for system, _ in ADAPTERS)
    assert set(TERMINOLOGY_RELEASES) == set(validator_systems())
    with pytest.raises(UnknownTerminologySystemError) as exc:
        get_validator("SNOMED-CT")
    assert "SNOMED-CT" in str(exc.value)
    assert isinstance(exc.value, TerminologyError)
    assert exc.value.details["available"] == validator_systems()
    with pytest.raises(TypeError):
        TERMINOLOGY_RELEASES["LOINC"] = get_release("LOINC")  # type: ignore[index]


@pytest.mark.parametrize("entry", ICD10_CODES, ids=lambda entry: entry.code)
def test_icd_curated_codes_are_accepted_with_release_version(entry) -> None:
    result = IcdValidator().validate(entry.code)
    assert result.status is ValidationStatus.VALID
    assert result.accepted is True
    assert result.stage is VerificationStage.CURATED_ALLOWLIST
    assert result.normalized_code == entry.code
    assert result.source_ref == entry.source_ref
    assert result.system == "ICD-10"
    assert result.version == "UNDECLARED"
    assert result.release is get_release("ICD-10")


@pytest.mark.parametrize(
    "candidate",
    ["J", "J1", "J1890", "J18.12345", "U18.9", "1J8.9", "J18.9 extra", "J18.ABCDE"],
)
def test_icd_malformed_codes_are_invalid(candidate: str) -> None:
    result = IcdValidator().validate(candidate)
    assert result.status is ValidationStatus.INVALID
    assert result.accepted is False
    assert result.stage is VerificationStage.STRUCTURAL
    assert result.normalized_code is None
    assert result.source_ref is None
    assert result.release.version == "UNDECLARED"


@pytest.mark.parametrize("candidate", ["A01.1", "Z99.9", "Q00.0"])
def test_icd_well_formed_unknown_codes_are_unverified(candidate: str) -> None:
    result = IcdValidator().validate(candidate)
    assert result.status is ValidationStatus.UNVERIFIED
    assert result.accepted is False
    assert result.normalized_code == candidate
    assert result.source_ref is None
    assert "not present in the curated offline allowlist" in result.reason
    assert result.release.coverage is CoverageLevel.PARTIALLY_VERIFIED


@pytest.mark.parametrize("entry", LOINC_CODES, ids=lambda entry: entry.code)
def test_loinc_curated_codes_are_accepted_with_declared_version(entry) -> None:
    result = LoincValidator().validate(entry.code)
    assert result.status is ValidationStatus.VALID
    assert result.stage is VerificationStage.CURATED_ALLOWLIST
    assert result.normalized_code == entry.code
    assert result.source_ref == entry.source_ref
    assert result.version == "2.81"
    assert result.release is get_release("LOINC")
    # Phase B M5: the official Appendix C.1 Mod-10 digit is now recomputed for
    # curated numeric codes, so a curated+match result is VERIFIED. The full
    # official release DATASET is still absent; verified check digit != full
    # release conformance (asserted separately below).
    assert result.check_digit is CheckDigitStatus.VERIFIED
    assert compute_loinc_check_digit(entry.code.split("-", 1)[0]) == int(entry.code.split("-", 1)[1])
    assert "official LOINC Mod-10 check digit recomputed" in result.reason
    assert "VERIFIED for curated codes" in result.reason


@pytest.mark.parametrize(
    "candidate",
    ["99999-9", "00000-0", "12345-1", "12345-0"],
)
def test_loinc_unknown_but_well_formed_codes_are_unverified(candidate: str) -> None:
    result = LoincValidator().validate(candidate)
    assert result.status is ValidationStatus.UNVERIFIED
    assert result.accepted is False
    assert result.normalized_code == candidate
    assert result.check_digit is CheckDigitStatus.NOT_VERIFIED_OFFLINE
    assert result.release.version == "2.81"


@pytest.mark.parametrize("candidate", ["8867", "8867-44", "1234567-1", "12-1", "8867-A", "8867-4 "])
def test_loinc_malformed_codes_are_invalid(candidate: str) -> None:
    result = LoincValidator().validate(candidate)
    assert result.status is ValidationStatus.INVALID
    assert result.stage is VerificationStage.STRUCTURAL
    assert result.normalized_code is None
    assert result.source_ref is None


@pytest.mark.parametrize("candidate", ["1" * 10, "A" * 12, "SYN-PAT-3F2A00000000", "9851234567"])
def test_real_identifier_shaped_values_are_rejected_by_every_adapter(candidate: str) -> None:
    for system, _ in ADAPTERS:
        result = get_validator(system).validate(candidate)
        assert result.status is ValidationStatus.INVALID
        assert result.accepted is False
        assert result.normalized_code is None
        assert result.release.coverage is CoverageLevel.PARTIALLY_VERIFIED


@pytest.mark.parametrize("entry", UCUM_UNITS, ids=lambda entry: entry.code)
def test_ucum_curated_units_are_accepted_exactly(entry) -> None:
    result = UcumValidator().validate(entry.code)
    assert result.status is ValidationStatus.VALID
    assert result.stage is VerificationStage.CURATED_ALLOWLIST
    assert result.normalized_code == entry.code
    assert result.source_ref == entry.source_ref
    assert result.version == "UNDECLARED"
    assert result.release.canonical_uri == "http://unitsofmeasure.org"


@pytest.mark.parametrize("candidate", ["mg/dl", "MG/DL", "cel", "Ml", "KG"])
def test_ucum_case_mismatches_are_invalid(candidate: str) -> None:
    result = UcumValidator().validate(candidate)
    assert result.status is ValidationStatus.INVALID
    assert result.stage is VerificationStage.STRUCTURAL
    assert "case-sensitive" in result.reason
    assert result.normalized_code is None
    assert result.accepted is False


@pytest.mark.parametrize("candidate", ["mg/dL ", " mg/dL", "mg\tdL", "", "kg*", "kg\nL"])
def test_ucum_format_negatives_are_invalid(candidate: str) -> None:
    result = UcumValidator().validate(candidate)
    assert result.status is ValidationStatus.INVALID
    assert result.source_ref is None
    assert result.release.version == "UNDECLARED"


@pytest.mark.parametrize("candidate", ["10^3/uL", "mg/L", "U/L", "mol/L", "mmHg", "mmol//L"])
def test_ucum_unlisted_but_plausible_units_are_unverified(candidate: str) -> None:
    result = UcumValidator().validate(candidate)
    assert result.status is ValidationStatus.UNVERIFIED
    assert result.accepted is False
    assert result.normalized_code == candidate
    assert "not present in the curated offline allowlist" in result.reason


@pytest.mark.parametrize("candidate", [None, 42, b"8867-4", ["J18.9"], {"code": "mg/dL"}])
def test_non_string_inputs_are_invalid_for_every_adapter(candidate: object) -> None:
    for system, _ in ADAPTERS:
        result = get_validator(system).validate(candidate)
        assert result.status is ValidationStatus.INVALID
        assert result.stage is VerificationStage.STRUCTURAL
        assert result.release.system == system.value


def test_every_result_carries_consistent_provenance() -> None:
    samples = {
        "ICD-10": ("J18.9", "A01.1", "bad!"),
        "LOINC": ("8867-4", "99999-9", "bad!"),
        "UCUM": ("mg/dL", "mol/L", "mg/dl"),
    }
    for system, codes in samples.items():
        validator = get_validator(system)
        for code in codes:
            result = validator.validate(code)
            assert result.release is validator.release
            assert result.version == validator.release.version
            assert result.release.verified_on == "2026-11-18"
            assert result.release.verification_method
            assert result.release.source
            assert result.release.license
            assert result.release.canonical_uri
            assert result.release.coverage is CoverageLevel.PARTIALLY_VERIFIED
            payload = result.to_dict()
            assert payload["version"] == result.version
            assert payload["provenance"] == result.release.to_dict()
            assert payload["status"] == result.status.value
            assert payload["stage"] == result.stage.value
            assert payload["code"] == code


def test_no_result_ever_claims_full_release_conformance() -> None:
    """VERIFIED check digit is permitted, but full-release conformance never is.

    Phase B M5 adds a locally recomputed official check digit. It is a narrow,
    per-code claim: it may appear ONLY on a curated LOINC code that passed the
    Appendix C.1 algorithm. It must never be read as full-release conformance,
    and no ICD-10/UCUM result may claim a verified check digit.
    """
    curated_loinc = {entry.code for entry in LOINC_CODES}
    for system, codes in {
        "ICD-10": ("J18.9", "A01.1"),
        "LOINC": ("8867-4", "99999-9"),
        "UCUM": ("mg/dL", "mol/L"),
    }.items():
        for code in codes:
            result = get_validator(system).validate(code)
            assert result.stage is not VerificationStage.FULL_RELEASE_CONFORMANCE
            assert result.release.coverage is not CoverageLevel.FULL_RELEASE
            if result.check_digit is CheckDigitStatus.VERIFIED:
                assert system == "LOINC"
                assert result.status is ValidationStatus.VALID
                assert result.code in curated_loinc
            else:
                assert result.check_digit in {
                    CheckDigitStatus.NOT_VERIFIED_OFFLINE,
                    CheckDigitStatus.NOT_APPLICABLE,
                }


def test_release_registry_and_validator_registry_are_lockstep() -> None:
    assert all_releases() == all_validator_releases()
    for system in TerminologySystem:
        assert get_release(system) is get_validator(system).provenance()
    assert len(TERMINOLOGY_RELEASES) == 3
    with pytest.raises(UnknownTerminologySystemError):
        get_release("NOT-A-SYSTEM")


def test_curated_sets_are_non_empty_unique_and_source_referenced() -> None:
    for entries in (ICD10_CODES, LOINC_CODES, UCUM_UNITS):
        assert entries
        codes = [entry.code for entry in entries]
        assert len(codes) == len(set(codes))
        for entry in entries:
            assert entry.code
            assert entry.source_ref.startswith("backend/app/")
            assert ":" in entry.source_ref

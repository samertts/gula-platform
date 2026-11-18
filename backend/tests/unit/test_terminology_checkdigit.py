"""T1/M5: official LOINC Mod-10 check digit and honest release provenance.

The algorithm is transcribed from the authoritative canonical source
https://loinc.org/check-digit (LOINC Users' Guide Appendix C.1). All tests are
synthetic; no licensed dataset, network call or production claim is involved.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest
from app.health_core.terminology import (
    CHECK_DIGIT_CANONICAL_URL,
    LOINC_CODES,
    LOINC_RELEASE,
    RELEASE_LINEAGE,
    AmbiguousReleaseVersionError,
    CheckDigitOutcome,
    CheckDigitStatus,
    CoverageLevel,
    CuratedCode,
    IcdValidator,
    InvalidLoincBodyError,
    LoincValidator,
    NoPreviousReleaseError,
    ReleaseLineageRecord,
    TerminologySystem,
    UcumValidator,
    UnknownReleaseVersionError,
    UnknownTerminologySystemError,
    ValidationStatus,
    VerificationStage,
    compute_loinc_check_digit,
    get_release,
    previous_release,
    resolve_release,
    validate_loinc_check_digit,
)

REFERENCE_VECTORS = (
    ("12345", 5),  # official Appendix C example
    ("718", 7),  # 718-7
    ("777", 3),  # 777-3
    ("4544", 3),  # 4544-3
    ("2345", 7),  # 2345-7
)
REFERENCE_CODES = ("12345-5", "718-7", "777-3", "4544-3", "2345-7")
PREFIXED_CODES = ("LP12345-6", "LL1234-5", "LA1234-5", "LG1234-5", "LP12345")


# ---------------------------------------------------------------------------
# Official algorithm: reference vectors and exact arithmetic
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(("body", "expected"), REFERENCE_VECTORS)
def test_compute_matches_every_hand_verified_reference_vector(body: str, expected: int) -> None:
    assert compute_loinc_check_digit(body) == expected


@pytest.mark.parametrize("code", REFERENCE_CODES)
def test_validate_full_reference_codes_is_valid_with_correct_digits(code: str) -> None:
    body, actual = code.split("-", 1)
    result = validate_loinc_check_digit(code)
    assert result.status is CheckDigitOutcome.VALID
    assert result.valid is True
    assert result.expected == compute_loinc_check_digit(body)
    assert result.actual == int(actual)
    assert result.expected == result.actual
    assert result.canonical_url == CHECK_DIGIT_CANONICAL_URL
    assert "Appendix C.1" in result.algorithm_source


def test_doubled_products_are_reduced_to_digit_sums_not_used_raw() -> None:
    # 5*2=10 -> 1+0=1 -> check 9; 7*2=14 -> 1+4=5 -> check 5.
    # Using the raw products (10, 14) would instead yield 0 and 6.
    assert compute_loinc_check_digit("5") == 9
    assert compute_loinc_check_digit("7") == 5


def test_positions_are_numbered_from_the_right_not_the_left() -> None:
    def left_to_right(body: str) -> int:
        total = 0
        for index, character in enumerate(body):
            digit = int(character)
            if index % 2 == 0:
                doubled = digit * 2
                total += doubled // 10 + doubled % 10
            else:
                total += digit
        return (10 - total % 10) % 10

    # Right-to-left numbering yields 5; left-to-right numbering would yield 6.
    assert compute_loinc_check_digit("12") == 5
    assert left_to_right("12") == 6
    assert left_to_right("12") != compute_loinc_check_digit("12")


# ---------------------------------------------------------------------------
# compute_loinc_check_digit fails closed
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "body",
    [
        "",
        " 123",
        "123 ",
        "12 3",
        "12\t3",
        "12\n3",
        "12\r3",
        "12\x003",
        "12\x7f3",
        "12a3",
        "12-3",
        "1.2",
        "١٢٣",  # non-ASCII digits must not be silently coerced
        None,
        123,
        b"123",
        ["123"],
    ],
)
def test_compute_rejects_every_non_numeric_or_control_body(body: object) -> None:
    with pytest.raises(InvalidLoincBodyError) as exc:
        compute_loinc_check_digit(body)  # type: ignore[arg-type]
    assert isinstance(exc.value, ValueError)
    assert exc.value.code == "INVALID_LOINC_BODY"


# ---------------------------------------------------------------------------
# validate_loinc_check_digit fails closed
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "code",
    [
        "",
        "8867",
        "8867-",
        "-4",
        "8867-44",
        "8867-4-2",
        "8867-A",
        "8867-" + chr(0xFF14),  # fullwidth digit check digit
        " 8867-4",
        "8867-4 ",
        "8867\t-4",
        "8867-4\n",
        "8867\x004",
        None,
        88674,
        b"8867-4",
    ],
)
def test_malformed_codes_are_reported_malformed_without_digits(code: object) -> None:
    result = validate_loinc_check_digit(code)  # type: ignore[arg-type]
    assert result.status is CheckDigitOutcome.MALFORMED
    assert result.valid is False
    assert result.expected is None
    assert result.actual is None
    assert result.reason
    assert result.canonical_url == CHECK_DIGIT_CANONICAL_URL


@pytest.mark.parametrize("code", PREFIXED_CODES)
def test_letter_prefixed_codes_are_not_implemented_and_never_guessed(code: str) -> None:
    result = validate_loinc_check_digit(code)
    assert result.status is CheckDigitOutcome.NOT_IMPLEMENTED
    assert result.valid is False
    assert result.expected is None
    assert result.actual is None
    assert "Appendix C.2" in result.reason
    assert "not implemented" in result.reason


@pytest.mark.parametrize(
    ("code", "expected", "actual"),
    [("12345-6", 5, 6), ("718-8", 7, 8), ("777-0", 3, 0), ("2345-9", 7, 9)],
)
def test_mismatch_reports_expected_and_actual_digits(code: str, expected: int, actual: int) -> None:
    result = validate_loinc_check_digit(code)
    assert result.status is CheckDigitOutcome.MISMATCH
    assert result.valid is False
    assert result.expected == expected
    assert result.actual == actual
    assert result.expected != result.actual


def test_checkdigit_result_serialisation_is_stable_and_provenance_bearing() -> None:
    result = validate_loinc_check_digit("718-7")
    payload = result.to_dict()
    assert payload == {
        "status": "VALID",
        "valid": True,
        "expected": 7,
        "actual": 7,
        "reason": result.reason,
        "algorithm_source": result.algorithm_source,
        "canonical_url": CHECK_DIGIT_CANONICAL_URL,
    }


# ---------------------------------------------------------------------------
# No identifier leakage in diagnostics (I-2)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("code", ["LPSYNSECRET42-9", "SYNSECRET-4 ", "8867-SYNSECRET"])
def test_diagnostics_never_echo_the_inspected_code(code: str) -> None:
    result = validate_loinc_check_digit(code)
    assert "SYNSECRET" not in result.reason
    assert "SYNSECRET" not in str(result.to_dict())
    validator_result = LoincValidator().validate(code)
    # ValidationResult.code intentionally records the submitted value as the
    # subject of the decision; diagnostic reason text must never echo it.
    assert validator_result.normalized_code is None
    assert "SYNSECRET" not in validator_result.reason


# ---------------------------------------------------------------------------
# LoincValidator integration
# ---------------------------------------------------------------------------


def test_every_curated_loinc_code_has_a_correct_official_check_digit() -> None:
    for entry in LOINC_CODES:
        verdict = validate_loinc_check_digit(entry.code)
        assert verdict.valid is True, entry.code
        assert verdict.expected == verdict.actual, entry.code


@pytest.mark.parametrize("entry", LOINC_CODES, ids=lambda entry: entry.code)
def test_curated_valid_codes_stay_valid_with_verified_check_digit(entry: CuratedCode) -> None:
    result = LoincValidator().validate(entry.code)
    assert result.status is ValidationStatus.VALID
    assert result.accepted is True
    assert result.stage is VerificationStage.CURATED_ALLOWLIST
    assert result.check_digit is CheckDigitStatus.VERIFIED
    assert result.normalized_code == entry.code
    assert result.source_ref == entry.source_ref
    assert "VERIFIED" in result.reason
    assert CHECK_DIGIT_CANONICAL_URL in result.reason
    assert result.release is get_release("LOINC")
    assert result.release.coverage is CoverageLevel.PARTIALLY_VERIFIED
    assert result.stage is not VerificationStage.FULL_RELEASE_CONFORMANCE


def test_curated_code_with_mismatched_digit_is_rejected_invalid() -> None:
    # Inject a synthetic curated entry carrying a deliberately wrong digit.
    validator = LoincValidator()
    forged = CuratedCode("12345-6", "backend/tests/unit/test_terminology_checkdigit.py")
    validator._by_code = {forged.code: forged}
    result = validator.validate("12345-6")
    assert result.status is ValidationStatus.INVALID
    assert result.accepted is False
    assert result.check_digit is CheckDigitStatus.MISMATCH
    assert result.normalized_code is None
    assert result.source_ref is None
    assert result.stage is VerificationStage.CURATED_ALLOWLIST
    assert "check-digit verification failed" in result.reason
    assert result.release is get_release("LOINC")
    assert result.release.coverage is CoverageLevel.PARTIALLY_VERIFIED


@pytest.mark.parametrize("code", ["99999-9", "00000-0", "12345-1", "12345-0", "4544-3"])
def test_non_curated_well_formed_codes_remain_unverified_even_with_valid_checksum(code: str) -> None:
    result = LoincValidator().validate(code)
    assert result.status is ValidationStatus.UNVERIFIED
    assert result.accepted is False
    assert result.check_digit is CheckDigitStatus.NOT_VERIFIED_OFFLINE
    assert result.normalized_code == code
    assert result.source_ref is None
    assert "curated offline allowlist" in result.reason
    assert result.release is get_release("LOINC")


@pytest.mark.parametrize("code", PREFIXED_CODES)
def test_prefixed_codes_fail_closed_in_the_validator(code: str) -> None:
    result = LoincValidator().validate(code)
    assert result.status is ValidationStatus.INVALID
    assert result.accepted is False
    assert result.stage is VerificationStage.STRUCTURAL
    assert "Appendix C.2" in result.reason
    assert result.release is get_release("LOINC")


@pytest.mark.parametrize(
    "code",
    ["8867", "8867-44", "1234567-1", "12-1", "8867-A", "8867-4 ", "", "8867-4-2"],
)
def test_malformed_loinc_codes_are_invalid_with_provenance(code: str) -> None:
    result = LoincValidator().validate(code)
    assert result.status is ValidationStatus.INVALID
    assert result.stage is VerificationStage.STRUCTURAL
    assert result.normalized_code is None
    assert result.source_ref is None
    assert result.release is get_release("LOINC")


# ---------------------------------------------------------------------------
# ICD-10 and UCUM behaviour is unchanged
# ---------------------------------------------------------------------------


def test_icd10_behaviour_is_unchanged() -> None:
    validator = IcdValidator()
    valid = validator.validate("J18.9")
    assert valid.status is ValidationStatus.VALID
    assert valid.check_digit is CheckDigitStatus.NOT_APPLICABLE
    assert valid.release is get_release("ICD-10")
    unknown = validator.validate("A01.1")
    assert unknown.status is ValidationStatus.UNVERIFIED
    assert unknown.check_digit is CheckDigitStatus.NOT_APPLICABLE
    malformed = validator.validate("J")
    assert malformed.status is ValidationStatus.INVALID
    assert malformed.stage is VerificationStage.STRUCTURAL


def test_ucum_behaviour_is_unchanged() -> None:
    validator = UcumValidator()
    valid = validator.validate("mg/dL")
    assert valid.status is ValidationStatus.VALID
    assert valid.check_digit is CheckDigitStatus.NOT_APPLICABLE
    assert valid.release is get_release("UCUM")
    mismatched_case = validator.validate("mg/dl")
    assert mismatched_case.status is ValidationStatus.INVALID
    assert "case-sensitive" in mismatched_case.reason
    unknown = validator.validate("mol/L")
    assert unknown.status is ValidationStatus.UNVERIFIED
    assert unknown.check_digit is CheckDigitStatus.NOT_APPLICABLE


# ---------------------------------------------------------------------------
# Release provenance, lineage and rollback (fail closed)
# ---------------------------------------------------------------------------


def test_loinc_release_notes_cite_source_vectors_and_honest_boundary() -> None:
    notes = LOINC_RELEASE.notes
    assert "https://loinc.org/check-digit" in notes
    assert "Appendix C.1" in notes
    assert "2026-09-30" in notes
    for body, expected in REFERENCE_VECTORS:
        assert f"{body}->{expected}" in notes
    assert "Appendix C.2" in notes
    assert "NOT IMPLEMENTED" in notes
    assert "BLOCKED" in notes
    assert "PARTIALLY_VERIFIED" in notes
    assert "NOT claimed" in notes
    assert LOINC_RELEASE.coverage is CoverageLevel.PARTIALLY_VERIFIED
    assert "GLOSI/" in LOINC_RELEASE.license


def test_release_lineage_is_frozen_honest_and_lockstep() -> None:
    assert isinstance(RELEASE_LINEAGE, tuple)
    assert len(RELEASE_LINEAGE) == 3
    for record in RELEASE_LINEAGE:
        assert isinstance(record, ReleaseLineageRecord)
        assert record.official_artifact is False
        assert record.release is get_release(record.system)
        assert record.system in {system.value for system in TerminologySystem}
        assert record.note
        with pytest.raises(FrozenInstanceError):
            record.version = "FORGED"  # type: ignore[misc]
    loinc_record = resolve_release("2.81")
    assert loinc_record.system == TerminologySystem.LOINC.value
    assert loinc_record.release is LOINC_RELEASE
    assert "BLOCKED" in loinc_record.note


def test_resolve_release_fails_closed_on_unknown_or_ambiguous_versions() -> None:
    with pytest.raises(AmbiguousReleaseVersionError) as exc:
        resolve_release("UNDECLARED")
    assert exc.value.details["systems"] == ("ICD-10", "UCUM")
    for version in ("", "9.99", "2.81 ", None, 42):
        with pytest.raises(UnknownReleaseVersionError):
            resolve_release(version)  # type: ignore[arg-type]


def test_previous_release_fails_closed_on_every_unavailable_transition() -> None:
    with pytest.raises(NoPreviousReleaseError) as exc:
        previous_release(TerminologySystem.LOINC, "2.81")
    assert exc.value.details["system"] == "LOINC"
    with pytest.raises(UnknownReleaseVersionError):
        previous_release("LOINC", "9.99")
    with pytest.raises(UnknownTerminologySystemError):
        previous_release("SNOMED-CT", "2.81")
    with pytest.raises(UnknownReleaseVersionError):
        previous_release("LOINC", "")
    with pytest.raises(UnknownReleaseVersionError):
        previous_release("LOINC", None)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "result",
    [
        LoincValidator().validate("8867-4"),
        LoincValidator().validate("99999-9"),
        LoincValidator().validate("LP12345-6"),
        LoincValidator().validate("bad!"),
        IcdValidator().validate("J18.9"),
        UcumValidator().validate("mg/dL"),
    ],
)
def test_every_result_preserves_complete_provenance(result: object) -> None:
    payload = result.to_dict()  # type: ignore[attr-defined]
    assert payload["provenance"] == result.release.to_dict()  # type: ignore[attr-defined]
    assert payload["version"] == result.release.version  # type: ignore[attr-defined]
    assert result.release.coverage is CoverageLevel.PARTIALLY_VERIFIED  # type: ignore[attr-defined]
    assert result.release.verified_on == "2026-11-18"  # type: ignore[attr-defined]
    assert result.stage is not VerificationStage.FULL_RELEASE_CONFORMANCE  # type: ignore[attr-defined]

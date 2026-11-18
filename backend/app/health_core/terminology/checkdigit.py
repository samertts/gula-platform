"""Official LOINC Mod-10 check-digit algorithm (LOINC Users' Guide, Appendix C).

Authoritative source (independently fetched and hand-verified BEFORE this
implementation; no network access at import time or runtime)::

    LOINC Users' Guide, Appendix C "Calculating Mod 10 check digits"
    Canonical URL: https://loinc.org/check-digit
    Last updated: 2026-09-30

The algorithm below is a static transcription of Appendix C.1 (numeric LOINC
codes). It is deliberately narrow:

* Input is the numeric LOINC *body* (the digits before the dash), read
  left-to-right.
* Positions are assigned to the body digits FROM THE RIGHT (1st = rightmost).
* Digits in ODD positions from the right are multiplied by 2 and the digits of
  each product are summed (e.g. 5*2=10 -> 1+0=1; 7*2=14 -> 1+4=5).
* Digits in EVEN positions from the right are added directly.
* ``total`` is the sum of all those contributions.
* ``check_digit = (10 - (total % 10)) % 10``.

Hand-verified reference vectors (body -> check digit)::

    12345 -> 5   (official Appendix C example)
    718   -> 7   (718-7)
    777   -> 3   (777-3)
    4544  -> 3   (4544-3)
    2345  -> 7   (2345-7)

SCOPE BOUNDARY: LOINC codes with letter prefixes (LP/LL/LA/LG, etc.) use the
DIFFERENT Appendix C.2 algorithm. That algorithm is NOT implemented and NOT
verified here; such inputs are reported as NOT_IMPLEMENTED and never guessed.

This module never emits the inspected code in a diagnostic string. Reason texts
are fixed constants so identifiers cannot leak into logs, audit records or API
error payloads (I-2: no identifier leakage in diagnostics).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

CHECK_DIGIT_ALGORITHM_SOURCE = "LOINC Users' Guide Appendix C.1 - Calculating Mod 10 check digits"
CHECK_DIGIT_CANONICAL_URL = "https://loinc.org/check-digit"
CHECK_DIGIT_SOURCE_LAST_UPDATED = "2026-09-30"
CHECK_DIGIT_PREFIX_ALGORITHM_NOT_IMPLEMENTED = (
    "LOINC Users' Guide Appendix C.2 (letter-prefixed codes) is NOT implemented and NOT verified"
)

# Fixed, bounded reason strings. No caller-controlled value is ever interpolated.
_REASON_VALID = "official Mod-10 check digit recomputed and matches"
_REASON_MISMATCH = "official Mod-10 check digit does not match the code's check digit"
_REASON_NOT_STRING = "code must be a string"
_REASON_EMPTY = "code must not be empty"
_REASON_CONTROL = "code must not contain whitespace or control characters"
_REASON_PREFIX = (
    "letter-prefixed LOINC codes require Appendix C.2, which is not implemented or verified here"
)
_REASON_DASH = "LOINC code requires exactly one dash between the numeric body and the check digit"
_REASON_BODY = "LOINC body must contain ASCII digits only"
_REASON_DIGIT = "LOINC check digit must be a single ASCII digit"


class InvalidLoincBodyError(ValueError):
    """Raised when a value is not a numeric LOINC body suitable for Mod-10."""

    code = "INVALID_LOINC_BODY"


class CheckDigitOutcome(StrEnum):
    """Deterministic outcome of validating one LOINC check digit."""

    VALID = "VALID"
    MISMATCH = "MISMATCH"
    MALFORMED = "MALFORMED"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"


@dataclass(frozen=True, slots=True)
class CheckDigitResult:
    """Structured, provenance-bearing result of one check-digit verification.

    ``expected`` and ``actual`` are single digits (or ``None`` when the input
    could not be evaluated). ``reason`` is always a fixed constant from this
    module; the inspected code is never echoed into diagnostics.
    """

    status: CheckDigitOutcome
    expected: int | None
    actual: int | None
    reason: str
    algorithm_source: str = CHECK_DIGIT_ALGORITHM_SOURCE
    canonical_url: str = CHECK_DIGIT_CANONICAL_URL

    @property
    def valid(self) -> bool:
        """True only when the official check digit was recomputed and matched."""
        return self.status is CheckDigitOutcome.VALID

    def to_dict(self) -> dict[str, object]:
        """Return an audit-friendly serialisation of this verdict."""
        return {
            "status": self.status.value,
            "valid": self.valid,
            "expected": self.expected,
            "actual": self.actual,
            "reason": self.reason,
            "algorithm_source": self.algorithm_source,
            "canonical_url": self.canonical_url,
        }


def _is_ascii_digits(value: str) -> bool:
    """Return True only for a non-empty string of ASCII 0-9 characters."""
    return bool(value) and all("0" <= character <= "9" for character in value)


def _has_control_or_whitespace(value: str) -> bool:
    """Detect ASCII control characters, DEL and any Unicode whitespace."""
    return any(character.isspace() or ord(character) < 0x20 or ord(character) == 0x7F for character in value)


def compute_loinc_check_digit(body: str) -> int:
    """Compute the official LOINC Mod-10 check digit for a numeric body.

    Fails closed with :class:`InvalidLoincBodyError` for every non-numeric,
    empty, whitespace-bearing, control-character-bearing or non-ASCII input.
    """
    if not isinstance(body, str):
        raise InvalidLoincBodyError(_REASON_NOT_STRING)
    if not body:
        raise InvalidLoincBodyError(_REASON_EMPTY)
    if _has_control_or_whitespace(body):
        raise InvalidLoincBodyError(_REASON_CONTROL)
    if not _is_ascii_digits(body):
        raise InvalidLoincBodyError(_REASON_BODY)

    total = 0
    for index, character in enumerate(reversed(body)):
        digit = ord(character) - ord("0")
        position_from_right = index + 1
        if position_from_right % 2 == 1:
            doubled = digit * 2
            total += (doubled // 10) + (doubled % 10)
        else:
            total += digit
    return (10 - (total % 10)) % 10


def validate_loinc_check_digit(code: str) -> CheckDigitResult:
    """Validate a numeric LOINC code's check digit, failing closed on ambiguity.

    Letter-prefixed codes are reported as NOT_IMPLEMENTED (Appendix C.2 is out
    of scope). Malformed, empty, control-character-bearing, non-string,
    dash-less and multi-dash values are reported as MALFORMED. Only a numeric
    code whose recomputed digit matches can be VALID.
    """
    if not isinstance(code, str):
        return CheckDigitResult(CheckDigitOutcome.MALFORMED, None, None, _REASON_NOT_STRING)
    if not code:
        return CheckDigitResult(CheckDigitOutcome.MALFORMED, None, None, _REASON_EMPTY)
    if _has_control_or_whitespace(code):
        return CheckDigitResult(CheckDigitOutcome.MALFORMED, None, None, _REASON_CONTROL)

    first_segment = code.split("-", 1)[0]
    if any(character.isalpha() for character in first_segment):
        return CheckDigitResult(CheckDigitOutcome.NOT_IMPLEMENTED, None, None, _REASON_PREFIX)

    if code.count("-") != 1:
        return CheckDigitResult(CheckDigitOutcome.MALFORMED, None, None, _REASON_DASH)

    body, actual_text = code.split("-", 1)
    if not _is_ascii_digits(body):
        return CheckDigitResult(CheckDigitOutcome.MALFORMED, None, None, _REASON_BODY)
    if len(actual_text) != 1 or not _is_ascii_digits(actual_text):
        return CheckDigitResult(CheckDigitOutcome.MALFORMED, None, None, _REASON_DIGIT)

    expected = compute_loinc_check_digit(body)
    actual = ord(actual_text) - ord("0")
    status = CheckDigitOutcome.VALID if expected == actual else CheckDigitOutcome.MISMATCH
    reason = _REASON_VALID if status is CheckDigitOutcome.VALID else _REASON_MISMATCH
    return CheckDigitResult(status, expected, actual, reason)


__all__ = [
    "CHECK_DIGIT_ALGORITHM_SOURCE",
    "CHECK_DIGIT_CANONICAL_URL",
    "CHECK_DIGIT_PREFIX_ALGORITHM_NOT_IMPLEMENTED",
    "CHECK_DIGIT_SOURCE_LAST_UPDATED",
    "CheckDigitOutcome",
    "CheckDigitResult",
    "InvalidLoincBodyError",
    "compute_loinc_check_digit",
    "validate_loinc_check_digit",
]

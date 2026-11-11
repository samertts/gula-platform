"""Controlled terminology helpers for the GULA FHIR laboratory bridge.

This intentionally conservative catalogue maps only unambiguous, commonly named
laboratory tests.  Local catalogue governance remains authoritative for broader
coverage and specimen-specific LOINC selection.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class LaboratoryCode:
    code: str
    display: str
    aliases: tuple[str, ...]


_COMMON_LOINC_CODES: tuple[LaboratoryCode, ...] = (
    LaboratoryCode("2345-7", "Glucose [Mass/volume] in Serum or Plasma", ("glucose", "blood glucose", "serum glucose", "fbs", "rbs")),
    LaboratoryCode("2160-0", "Creatinine [Mass/volume] in Serum or Plasma", ("creatinine", "serum creatinine")),
    LaboratoryCode("718-7", "Hemoglobin [Mass/volume] in Blood", ("hemoglobin", "haemoglobin", "hb", "hgb")),
    LaboratoryCode("6690-2", "Leukocytes [#/volume] in Blood", ("white blood cell", "white blood cell count", "wbc", "leukocytes")),
    LaboratoryCode("777-3", "Platelets [#/volume] in Blood", ("platelet", "platelet count", "plt")),
    LaboratoryCode("2823-3", "Potassium [Moles/volume] in Serum or Plasma", ("potassium", "serum potassium", "k")),
    LaboratoryCode("2951-2", "Sodium [Moles/volume] in Serum or Plasma", ("sodium", "serum sodium", "na")),
    LaboratoryCode("17861-6", "Calcium [Mass/volume] in Serum or Plasma", ("calcium", "serum calcium", "ca")),
    LaboratoryCode("4548-4", "Hemoglobin A1c/Hemoglobin.total in Blood", ("hba1c", "hb a1c", "glycated hemoglobin")),
    LaboratoryCode("1742-6", "Alanine aminotransferase [Enzymatic activity/volume] in Serum or Plasma", ("alanine aminotransferase", "alt", "sgpt")),
    LaboratoryCode("1920-8", "Aspartate aminotransferase [Enzymatic activity/volume] in Serum or Plasma", ("aspartate aminotransferase", "ast", "sgot")),
)


def normalize_lab_test_name(value: str | None) -> str:
    """Normalize a locally entered test name for controlled alias lookup."""
    return re.sub(r"\s+", " ", (value or "").strip().casefold())


def find_loinc_code(test_name: str | None) -> LaboratoryCode | None:
    """Return an unambiguous LOINC mapping or ``None`` for a local test."""
    normalized = normalize_lab_test_name(test_name)
    return next(
        (candidate for candidate in _COMMON_LOINC_CODES if normalized in candidate.aliases),
        None,
    )


def observation_code(test_name: str | None) -> dict:
    """Build a FHIR CodeableConcept with LOINC or a stable local code system."""
    display = (test_name or "Unspecified laboratory test").strip() or "Unspecified laboratory test"
    mapped = find_loinc_code(display)
    if mapped:
        return {
            "coding": [{"system": "http://loinc.org", "code": mapped.code, "display": mapped.display}],
            "text": display,
        }
    return {
        "coding": [
            {
                "system": "urn:gula:lab-test-name",
                "code": normalize_lab_test_name(display).replace(" ", "-"),
                "display": display,
            },
        ],
        "text": display,
    }


def test_matches_code(test_name: str | None, query: str) -> bool:
    """Match a FHIR token query against a recognized LOINC or local display."""
    candidate = (query or "").strip()
    if not candidate:
        return True
    mapped = find_loinc_code(test_name)
    if mapped and candidate == mapped.code:
        return True
    return candidate.casefold() in normalize_lab_test_name(test_name)


@dataclass(frozen=True)
class SearchNarrowing:
    """A database-side filter that cannot drop a row ``test_matches_code`` accepts.

    ``matches_everything`` means the query imposes no restriction at all, so the
    caller must not add a predicate. Otherwise the caller ORs the two branches:
    rows whose lowercased name is in ``exact_names``, and rows whose lowercased
    name contains ``substring``.
    """

    matches_everything: bool
    exact_names: tuple[str, ...]
    substring: str | None


def search_narrowing(query: str | None) -> SearchNarrowing:
    """Build a superset filter so a code search can be applied before LIMIT.

    ``fhir_search_observation`` used to fetch the newest 100 results and only
    then apply ``test_matches_code`` in Python. For a patient with more than 100
    results that silently dropped real matches: a glucose search returned an
    empty Bundle with ``total: 0`` while a glucose result was on file. Measured
    on PostgreSQL — 121 results, 1 of them Glucose, 0 returned.

    Replacing the Python pass with ``ILIKE %query%`` would trade that false
    negative for two new defects, so it is not what this does:

    * ``%`` and ``_`` in a caller-supplied string are LIKE wildcards, so
      ``code=%`` would match every test on file. The substring is escaped here
      and the caller passes ``escape="\\"``.
    * ``test_matches_code`` also resolves a LOINC *code* — ``2345-7`` matches a
      result named "Glucose" — which no predicate over ``test_name`` can express.
      Those names are enumerated into ``exact_names`` instead.

    The contract is one-directional on purpose: this filter is a **superset**, so
    it may admit rows that ``test_matches_code`` then rejects, and never the
    reverse. ``test_matches_code`` stays the single authority on what matches;
    this only makes the database narrow the candidate set before the limit.

    Why a single token is a sound superset: ``normalize_lab_test_name`` differs
    from ``lower()`` only by collapsing runs of whitespace and trimming, neither
    of which alters non-whitespace characters or their order. So if the whole
    query appears in the normalized name, every whitespace-free token of that
    query appears verbatim in the lowercased name. The longest token is used
    because it is the most selective. Deliberately no ``regexp_replace``: the
    test suite runs on SQLite and this must behave identically on both.
    """
    candidate = (query or "").strip()
    if not candidate:
        return SearchNarrowing(matches_everything=True, exact_names=(), substring=None)

    # A query that is exactly a known LOINC code matches every alias of that
    # code, however the local catalogue happens to spell the test.
    exact_names: tuple[str, ...] = ()
    for entry in _COMMON_LOINC_CODES:
        if candidate == entry.code:
            exact_names = entry.aliases
            break

    tokens = [token for token in candidate.casefold().split() if token]
    longest = max(tokens, key=len) if tokens else None
    return SearchNarrowing(
        matches_everything=False,
        exact_names=exact_names,
        substring=_escape_like(longest) if longest else None,
    )


def _escape_like(value: str) -> str:
    """Escape LIKE metacharacters so a caller's text cannot act as a pattern."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


# ── Observation.status ───────────────────────────────────────────────────────
#
# `Observation.status` is required and carries clinical weight: a consumer is
# entitled to act on "final". GULA tracks verification on the *order* — a doctor
# or admin verifying a result sets `lab_orders.status = "validated"` and locks
# the row — so the order's state is what decides this, and the builder already
# holds the order.
#
# Mapped onto FHIR's own vocabulary rather than an invented one:
#   pending / completed  results exist but no clinician has verified them
#                        -> "preliminary" ("initial or interim ... unverified")
#   validated            verified and locked          -> "final"
#   cancelled            the order was withdrawn      -> "cancelled"
#
# Anything unrecognised resolves to "preliminary", never "final": claiming a
# result is final is the one direction in which being wrong is unsafe.
_OBSERVATION_STATUS_BY_ORDER_STATUS: dict[str, str] = {
    "pending": "preliminary",
    "completed": "preliminary",
    "validated": "final",
    "cancelled": "cancelled",
}

_FALLBACK_OBSERVATION_STATUS = "preliminary"


def observation_status(order_status: str | None) -> str:
    """Return the FHIR Observation.status for a GULA order state."""
    return _OBSERVATION_STATUS_BY_ORDER_STATUS.get(
        (order_status or "").strip().casefold(),
        _FALLBACK_OBSERVATION_STATUS,
    )


# ── Observation.interpretation ───────────────────────────────────────────────

_INTERPRETATION_SYSTEM = "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation"

# The codes this system actually defines, with their official displays. GULA's
# internal flag vocabulary ("critical", "normal", "unknown") is not this
# vocabulary, and emitting an internal value under this system's URI publishes a
# code that does not exist in it.
_INTERPRETATION_DISPLAYS: dict[str, str] = {
    "H": "High",
    "L": "Low",
    "N": "Normal",
    "HH": "Critical high",
    "LL": "Critical low",
    "AA": "Critical abnormal",
}


def interpretation_code(
    flag: str | None,
    value: float | None = None,
    normal_low: float | None = None,
    normal_high: float | None = None,
) -> str | None:
    """Return a v3-ObservationInterpretation code, or None when there is none.

    "H" and "L" are already codes in this system. "normal" is "N". "critical"
    has no single code because the system distinguishes direction, so direction
    is read off the data that is already present — a value at or below the lower
    reference bound is critically low, at or above the upper bound critically
    high — and falls back to "AA" (Critical abnormal) when no bound is available
    to decide. That is the system's own code for a critical result of
    unstated direction; it is not a guess about the clinical meaning.

    GULA's "unknown" flag means the platform could not classify the result.
    There is no interpretation code for that, so this returns None and the
    caller omits the element. An absent optional element is honest; a fabricated
    code is not.
    """
    normalized = (flag or "").strip()
    if not normalized:
        return None
    upper = normalized.upper()
    if upper in ("H", "L"):
        return upper
    lowered = normalized.casefold()
    if lowered == "normal":
        return "N"
    if lowered == "critical":
        if value is not None:
            if normal_low is not None and value <= normal_low:
                return "LL"
            if normal_high is not None and value >= normal_high:
                return "HH"
        return "AA"
    # "unknown", or any flag this function does not recognise.
    return None


def interpretation_concept(
    flag: str | None,
    value: float | None = None,
    normal_low: float | None = None,
    normal_high: float | None = None,
) -> dict | None:
    """Build the Observation.interpretation CodeableConcept, or None."""
    code = interpretation_code(flag, value, normal_low, normal_high)
    if code is None:
        return None
    return {
        "coding": [
            {
                "system": _INTERPRETATION_SYSTEM,
                "code": code,
                "display": _INTERPRETATION_DISPLAYS[code],
            },
        ],
        "text": flag,
    }


# ── ServiceRequest.status ────────────────────────────────────────────────────
#
# FHIR R4 ServiceRequest.status is a required binding:
#   draft | active | on-hold | revoked | completed | entered-in-error | unknown
#
# GULA's LabOrder state machine (app/domain/order_state.py) is four states, and
# three of them are not codes in that value set at all:
#
#   pending     the request is in force, awaiting results   -> "active"
#   completed   results entered                             -> "completed"
#   validated   verified and locked; the request is served  -> "completed"
#   cancelled   the order was withdrawn                     -> "revoked"
#
# "cancelled" is the trap: FHIR spells a withdrawn request "revoked", so the
# internal word is not merely unmapped, it is a code this resource does not
# define. Anything unrecognised resolves to FHIR's own "unknown" and never to
# "active" -- "active" invites a consumer to act on a request that may have been
# withdrawn, which is the one direction in which being wrong is unsafe. Same
# reasoning, and the same mapping, as _map_order_status in app/lims for the LIMS
# twelve-state machine (IA-036).
_SERVICE_REQUEST_STATUS_BY_ORDER_STATUS: dict[str, str] = {
    "pending": "active",
    "completed": "completed",
    "validated": "completed",
    "cancelled": "revoked",
}

_FALLBACK_SERVICE_REQUEST_STATUS = "unknown"


def service_request_status(order_status: str | None) -> str:
    """Return the FHIR ServiceRequest.status for a GULA LabOrder state."""
    return _SERVICE_REQUEST_STATUS_BY_ORDER_STATUS.get(
        (order_status or "").strip().casefold(),
        _FALLBACK_SERVICE_REQUEST_STATUS,
    )


# ── DiagnosticReport.status ──────────────────────────────────────────────────
#
# FHIR R4 DiagnosticReport.status is a required binding:
#   registered | partial | preliminary | final | amended | corrected |
#   appended | cancelled | entered-in-error | unknown
#
#   pending     ordered, nothing reported yet              -> "registered"
#   completed   results entered, not yet verified          -> "preliminary"
#   validated   verified by an authorised person and locked -> "final"
#   cancelled   the order was withdrawn                    -> "cancelled"
#
# "completed" maps to "preliminary", not "final": FHIR reserves "final" for a
# report "complete and verified by an authorized person", which in GULA is
# precisely the validated state -- the same reading already applied to
# Observation.status. Anything unrecognised resolves to "partial", which claims
# less than the data supports rather than more.
_DIAGNOSTIC_REPORT_STATUS_BY_ORDER_STATUS: dict[str, str] = {
    "pending": "registered",
    "completed": "preliminary",
    "validated": "final",
    "cancelled": "cancelled",
}

_FALLBACK_DIAGNOSTIC_REPORT_STATUS = "partial"

# LabOrder.status is Column(String(20), default="pending") -- nullable, so an
# absent status is reachable. It means an order exists with no asserted
# progress, which is exactly FHIR's "registered": "the existence of the report
# is registered, but there is nothing yet available". The call site this
# replaced read `order.status or "pending"`, so this also keeps that behaviour
# rather than quietly reclassifying those rows as "partial".
_EMPTY_DIAGNOSTIC_REPORT_STATUS = "registered"


def diagnostic_report_status(order_status: str | None) -> str:
    """Return the FHIR DiagnosticReport.status for a GULA LabOrder state."""
    normalized = (order_status or "").strip().casefold()
    if not normalized:
        return _EMPTY_DIAGNOSTIC_REPORT_STATUS
    return _DIAGNOSTIC_REPORT_STATUS_BY_ORDER_STATUS.get(
        normalized,
        _FALLBACK_DIAGNOSTIC_REPORT_STATUS,
    )

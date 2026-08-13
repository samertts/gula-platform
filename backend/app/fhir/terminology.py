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

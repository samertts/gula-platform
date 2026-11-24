"""Curated code sets copied verbatim from read-only offline sources.

These are deliberately small allowlists, NOT official release datasets. Every
entry records the file and line it was inspected at. No code or unit is invented
here: unknown or merely plausible values are never accepted silently.

Excluded on purpose:
* ``backend/app/health_core/lab/catalogue.py`` units (``10^3/uL``, ``mg/L``,
  ``U/L``) are local synthetic fixtures, not entries in the UCUM allowlist at
  ``clinical/validation.py``; they are not curated UCUM codes.
* The large ``LOINC:`` seed list in ``backend/app/ai/knowledge_graph.py`` is a
  knowledge-graph fixture and was not adopted as a validated release.
"""

from __future__ import annotations

from app.health_core.terminology.models import CuratedCode

# ICD-10-shaped codes present in the offline checkout: three guideline codes
# explicitly tagged system="ICD10" and one documented structural example.
ICD10_CODES: tuple[CuratedCode, ...] = (
    CuratedCode("J18.9", "backend/app/health_core/clinical/validation.py:108"),
    CuratedCode("I10", "backend/app/national/services/cds_engine.py:961"),
    CuratedCode("E11", "backend/app/national/services/cds_engine.py:976"),
    CuratedCode("E78", "backend/app/national/services/cds_engine.py:991"),
)

# Eleven controlled lab LOINC mappings from fhir/terminology.py, plus the five
# observation-code keys from health_core/clinical/validation.py CODE_UNITS.
LOINC_CODES: tuple[CuratedCode, ...] = (
    CuratedCode(
        "2345-7",
        "backend/app/fhir/terminology.py:21",
        "Glucose [Mass/volume] in Serum or Plasma",
    ),
    CuratedCode(
        "2160-0",
        "backend/app/fhir/terminology.py:22",
        "Creatinine [Mass/volume] in Serum or Plasma",
    ),
    CuratedCode("718-7", "backend/app/fhir/terminology.py:23", "Hemoglobin [Mass/volume] in Blood"),
    CuratedCode("6690-2", "backend/app/fhir/terminology.py:24", "Leukocytes [#/volume] in Blood"),
    CuratedCode("777-3", "backend/app/fhir/terminology.py:25", "Platelets [#/volume] in Blood"),
    CuratedCode(
        "2823-3",
        "backend/app/fhir/terminology.py:26",
        "Potassium [Moles/volume] in Serum or Plasma",
    ),
    CuratedCode(
        "2951-2",
        "backend/app/fhir/terminology.py:27",
        "Sodium [Moles/volume] in Serum or Plasma",
    ),
    CuratedCode(
        "17861-6",
        "backend/app/fhir/terminology.py:28",
        "Calcium [Mass/volume] in Serum or Plasma",
    ),
    CuratedCode(
        "4548-4",
        "backend/app/fhir/terminology.py:29",
        "Hemoglobin A1c/Hemoglobin.total in Blood",
    ),
    CuratedCode(
        "1742-6",
        "backend/app/fhir/terminology.py:30",
        "Alanine aminotransferase [Enzymatic activity/volume] in Serum or Plasma",
    ),
    CuratedCode(
        "1920-8",
        "backend/app/fhir/terminology.py:31",
        "Aspartate aminotransferase [Enzymatic activity/volume] in Serum or Plasma",
    ),
    CuratedCode("8867-4", "backend/app/health_core/clinical/validation.py:47"),
    CuratedCode("8310-5", "backend/app/health_core/clinical/validation.py:48"),
    CuratedCode("8480-6", "backend/app/health_core/clinical/validation.py:49"),
    CuratedCode("8462-4", "backend/app/health_core/clinical/validation.py:50"),
    CuratedCode("59408-5", "backend/app/health_core/clinical/validation.py:51"),
)

# Exact UCUM_UNITS entries from backend/app/health_core/clinical/validation.py.
# Case is significant; no full UCUM grammar is parsed.
UCUM_UNITS: tuple[CuratedCode, ...] = (
    CuratedCode("/min", "backend/app/health_core/clinical/validation.py:27"),
    CuratedCode("bpm", "backend/app/health_core/clinical/validation.py:28"),
    CuratedCode("Cel", "backend/app/health_core/clinical/validation.py:29"),
    CuratedCode("degC", "backend/app/health_core/clinical/validation.py:30"),
    CuratedCode("mm[Hg]", "backend/app/health_core/clinical/validation.py:31"),
    CuratedCode("kg", "backend/app/health_core/clinical/validation.py:32"),
    CuratedCode("cm", "backend/app/health_core/clinical/validation.py:33"),
    CuratedCode("m", "backend/app/health_core/clinical/validation.py:34"),
    CuratedCode("%", "backend/app/health_core/clinical/validation.py:35"),
    CuratedCode("mmol/L", "backend/app/health_core/clinical/validation.py:36"),
    CuratedCode("mg/dL", "backend/app/health_core/clinical/validation.py:37"),
    CuratedCode("g/dL", "backend/app/health_core/clinical/validation.py:38"),
    CuratedCode("umol/L", "backend/app/health_core/clinical/validation.py:39"),
    CuratedCode("L", "backend/app/health_core/clinical/validation.py:40"),
    CuratedCode("mL", "backend/app/health_core/clinical/validation.py:41"),
)


__all__ = ["ICD10_CODES", "LOINC_CODES", "UCUM_UNITS"]

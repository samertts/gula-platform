from __future__ import annotations

from app._compat import StrEnum


class TerminologySystem(StrEnum):
    ICD10 = "ICD10"
    ICD11 = "ICD11"
    SNOMED_CT = "SNOMED_CT"
    LOINC = "LOINC"
    UCUM = "UCUM"
    ATC = "ATC"
    RXNORM = "RXNORM"
    CPT = "CPT"
    ISCN = "ISCN"
    LOCAL = "LOCAL"


class TerminologyStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    RETIRED = "retired"
    SUPERSEDED = "superseded"


class GuidelineStatus(StrEnum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    ACTIVE = "active"
    REVISED = "revised"
    RETIRED = "retired"


class EvidenceLevel(StrEnum):
    IA = "1a"
    IB = "1b"
    IIA = "2a"
    IIB = "2b"
    III = "3"
    IV = "4"
    V = "5"


class QualityIndicatorType(StrEnum):
    STRUCTURE = "structure"
    PROCESS = "process"
    OUTCOME = "outcome"
    PATIENT_EXPERIENCE = "patient_experience"


class RegistryType(StrEnum):
    DISEASE = "disease"
    PROCEDURE = "procedure"
    DEVICE = "device"
    OUTCOME = "outcome"
    QUALITY = "quality"

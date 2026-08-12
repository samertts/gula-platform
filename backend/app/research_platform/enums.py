from __future__ import annotations

from app._compat import StrEnum


class ResearchProjectStatus(StrEnum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class StudyType(StrEnum):
    OBSERVATIONAL = "observational"
    INTERVENTIONAL = "interventional"
    RETROSPECTIVE = "retrospective"
    PROSPECTIVE = "prospective"
    CASE_CONTROL = "case_control"
    COHORT = "cohort"
    RCT = "rct"


class DatasetCategory(StrEnum):
    CLINICAL = "clinical"
    LAB = "lab"
    RADIOLOGY = "radiology"
    PHARMACY = "pharmacy"
    CLAIMS = "claims"
    PUBLIC_HEALTH = "public_health"
    GENOMICS = "genomics"


class RegistryType(StrEnum):
    CANCER = "cancer"
    BIRTH = "birth"
    DEATH = "death"
    DIABETES = "diabetes"
    CARDIOVASCULAR = "cardiovascular"
    RARE_DISEASE = "rare_disease"
    CONGENITAL = "congenital"


class KpiCategory(StrEnum):
    CLINICAL = "clinical"
    LAB = "lab"
    OPERATIONAL = "operational"
    FINANCIAL = "financial"
    POPULATION = "population"
    QUALITY = "quality"
    SECURITY = "security"

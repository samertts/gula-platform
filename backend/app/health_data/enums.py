from __future__ import annotations

from enum import Enum


class DataSourceType(Enum):
    EHR = "ehr"
    LAB = "lab"
    RADIOLOGY = "radiology"
    PHARMACY = "pharmacy"
    CLAIMS = "claims"
    WEARABLE = "wearable"
    PUBLIC_HEALTH = "public_health"
    RESEARCH = "research"


class DataClassification(Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    CRITICAL = "critical"


class StorageTier(Enum):
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"
    ARCHIVE = "archive"


class DataQuality(Enum):
    RAW = "raw"
    VALIDATED = "validated"
    CURATED = "curated"
    ENRICHED = "enriched"
    MASTER = "master"

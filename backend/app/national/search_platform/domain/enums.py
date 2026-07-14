from __future__ import annotations

from app._compat import StrEnum


class SearchIndexType(StrEnum):
    PATIENT = "patient"
    ENCOUNTER = "encounter"
    LAB_RESULT = "lab_result"
    DOCUMENT = "document"
    CITIZEN = "citizen"
    ORGANIZATION = "organization"
    PRACTITIONER = "practitioner"
    APPOINTMENT = "appointment"
    REFERRAL = "referral"
    CONSENT = "consent"
    FAMILY = "family"


class SearchMode(StrEnum):
    EXACT = "exact"
    FUZZY = "fuzzy"
    PHRASE = "phrase"
    BOOLEAN = "boolean"
    SEMANTIC = "semantic"


class SortOrder(StrEnum):
    ASC = "asc"
    DESC = "desc"


class SearchOperator(StrEnum):
    AND = "and"
    OR = "or"
    NOT = "not"


class FilterOperator(StrEnum):
    EQ = "eq"
    NEQ = "neq"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    IN = "in"
    BETWEEN = "between"

from __future__ import annotations

from app._compat import StrEnum


class DocumentStatus(StrEnum):
    DRAFT = "draft"
    FINAL = "final"
    ARCHIVED = "archived"
    DELETED = "deleted"


class DocumentCategory(StrEnum):
    REPORT = "report"
    CONSENT_FORM = "consent_form"
    IDENTITY_DOC = "identity_doc"
    LAB_RESULT = "lab_result"
    PRESCRIPTION = "prescription"
    REFERRAL = "referral"
    CERTIFICATE = "certificate"
    CONTRACT = "contract"
    POLICY = "policy"
    OTHER = "other"


class DocumentFormat(StrEnum):
    PDF = "pdf"
    DOCX = "docx"
    XLSX = "xlsx"
    PNG = "png"
    JPEG = "jpeg"
    TIFF = "tiff"
    CSV = "csv"
    JSON = "json"
    XML = "xml"
    HL7 = "hl7"
    DICOM = "dicom"
    OTHER = "other"


class SignatureStatus(StrEnum):
    PENDING = "pending"
    SIGNED = "signed"
    VERIFIED = "verified"
    EXPIRED = "expired"
    REVOKED = "revoked"


class RetentionPolicy(StrEnum):
    STANDARD_1Y = "standard_1y"
    EXTENDED_5Y = "extended_5y"
    INDEFINITE = "indefinite"
    LEGAL_HOLD = "legal_hold"

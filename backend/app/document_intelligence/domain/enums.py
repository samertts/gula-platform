from __future__ import annotations

from enum import StrEnum, auto


class DocumentCategory(StrEnum):
    laboratory_report = "laboratory_report"
    radiology_report = "radiology_report"
    prescription = "prescription"
    referral = "referral"
    medical_certificate = "medical_certificate"
    national_id = "national_id"
    passport = "passport"
    driving_license = "driving_license"
    insurance_document = "insurance_document"
    employment_letter = "employment_letter"
    official_government_letter = "official_government_letter"
    research_paper = "research_paper"
    unknown = "unknown"


class DocumentStatus(StrEnum):
    pending_ingestion = auto()
    ingested = auto()
    ocr_pending = auto()
    ocr_completed = auto()
    ocr_failed = auto()
    classification_pending = auto()
    classified = auto()
    classification_failed = auto()
    entity_extraction_pending = auto()
    entity_extraction_completed = auto()
    entity_extraction_failed = auto()
    fhir_mapping_pending = auto()
    fhir_mapped = auto()
    fhir_mapping_failed = auto()
    knowledge_indexed = auto()
    archived = auto()
    deleted = auto()


class OcrEngine(StrEnum):
    unlimited_ocr = "unlimited_ocr"
    paddle_ocr = "paddle_ocr"
    tesseract = "tesseract"
    easy_ocr = "easy_ocr"
    future_provider = "future_provider"


class OcrEngineStatus(StrEnum):
    available = auto()
    unavailable = auto()
    degraded = auto()
    benchmarking = auto()


class OcrLanguage(StrEnum):
    arabic = "ara"
    english = "eng"
    kurdish = "kur"
    arabic_english = "ara+eng"
    arabic_english_kurdish = "ara+eng+kur"
    auto = "auto"


class ProcessingPhase(StrEnum):
    ingestion = auto()
    preprocessing = auto()
    ocr = auto()
    classification = auto()
    entity_extraction = auto()
    fhir_mapping = auto()
    knowledge_extraction = auto()
    search_indexing = auto()


class ProcessingPriority(StrEnum):
    low = auto()
    normal = auto()
    high = auto()
    urgent = auto()


class StorageBackend(StrEnum):
    local = "local"
    s3 = "s3"
    minio = "minio"
    azure_blob = "azure_blob"
    gcs = "gcs"
    encrypted_local = "encrypted_local"


class EntityType(StrEnum):
    patient_name = auto()
    health_id = auto()
    national_id = auto()
    doctor_name = auto()
    license_number = auto()
    laboratory_name = auto()
    hospital_name = auto()
    facility_name = auto()
    date = auto()
    diagnosis = auto()
    loinc_code = auto()
    snomed_code = auto()
    icd_code = auto()
    medication_name = auto()
    dosage = auto()
    test_name = auto()
    test_result = auto()
    reference_range = auto()
    unit = auto()
    qr_code = auto()
    barcode = auto()
    signature = auto()
    address = auto()
    phone_number = auto()
    email = auto()
    blood_type = auto()
    specimen_type = auto()
    collection_date = auto()
    report_date = auto()
    accession_number = auto()
    encounter_type = auto()
    custom = auto()


class ExtractedFieldType(StrEnum):
    text = auto()
    number = auto()
    date = auto()
    boolean = auto()
    table = auto()
    image = auto()
    barcode = auto()
    qr_code = auto()
    signature = auto()
    unknown = auto()


class ClassificationConfidence(StrEnum):
    very_high = "very_high"
    high = "high"
    medium = "medium"
    low = "low"
    very_low = "very_low"

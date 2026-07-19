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
    administrative_order = "administrative_order"
    circular = "circular"
    committee_decision = "committee_decision"
    employment_order = "employment_order"
    promotion_order = "promotion_order"
    contract = "contract"
    procurement = "procurement"
    inspection_report = "inspection_report"
    legal_document = "legal_document"
    research_paper = "research_paper"
    academic_record = "academic_record"
    financial_statement = "financial_statement"
    invoice = "invoice"
    bank_statement = "bank_statement"
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
    extraction_pending = auto()
    extraction_completed = auto()
    extraction_failed = auto()
    fhir_mapping_pending = auto()
    fhir_mapped = auto()
    fhir_mapping_failed = auto()
    knowledge_indexed = auto()
    vector_indexed = auto()
    graph_indexed = auto()
    preservation_pending = auto()
    preserved = auto()
    preservation_failed = auto()
    archived = auto()
    deleted = auto()
    purged = auto()


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
    stamp = auto()
    logo = auto()
    photo = auto()
    fingerprint = auto()
    unknown = auto()


class ClassificationConfidence(StrEnum):
    very_high = "very_high"
    high = "high"
    medium = "medium"
    low = "low"
    very_low = "very_low"


class ConfidentialityLevel(StrEnum):
    unrestricted = "unrestricted"
    internal = "internal"
    confidential = "confidential"
    restricted = "restricted"
    secret = "secret"
    top_secret = "top_secret"


class CollaborationRole(StrEnum):
    viewer = "viewer"
    commenter = "commenter"
    reviewer = "reviewer"
    approver = "approver"
    editor = "editor"
    owner = "owner"


class ReviewDecision(StrEnum):
    approved = auto()
    rejected = auto()
    needs_changes = auto()
    deferred = auto()


class ArchiveStatus(StrEnum):
    active = auto()
    pending_archive = auto()
    archived = auto()
    pending_preservation = auto()
    preserved = auto()
    pending_purge = auto()
    purged = auto()
    restored = auto()


class RetentionPolicy(StrEnum):
    standard_1y = "1Y"
    standard_3y = "3Y"
    standard_5y = "5Y"
    standard_7y = "7Y"
    standard_10y = "10Y"
    permanent = "permanent"
    legal_hold = "legal_hold"


class GovernancePolicyAction(StrEnum):
    notify = auto()
    flag = auto()
    quarantine = auto()
    block = auto()
    expire = auto()
    archive = auto()
    purge = auto()
    escalate = auto()


class GovernanceRuleSeverity(StrEnum):
    info = auto()
    warning = auto()
    critical = auto()
    breach = auto()


class DigitalPreservationStandard(StrEnum):
    oais = "OAIS"
    premis = "PREMIS"
    mets = "METS"
    dublin_core = "Dublin_Core"
    custom = "custom"


class IntegrityCheckMethod(StrEnum):
    sha256 = "sha256"
    sha512 = "sha512"
    blake2b = "blake2b"
    hmac_signed = "hmac_signed"
    merkle_tree = "merkle_tree"


class KnowledgeGraphRelation(StrEnum):
    belongs_to = auto()
    authored_by = auto()
    refers_to = auto()
    derived_from = auto()
    same_as = auto()
    supersedes = auto()
    superseded_by = auto()
    associated_with = auto()
    located_in = auto()
    treats = auto()
    diagnoses = auto()
    prescribed_by = auto()
    administered_by = auto()
    reported_by = auto()
    verified_by = auto()


class GovernanceDomain(StrEnum):
    document_classification = auto()
    data_retention = auto()
    access_control = auto()
    privacy = auto()
    compliance = auto()
    archival = auto()
    preservation = auto()
    quality = auto()


class EventChannel(StrEnum):
    document_ingested = auto()
    document_updated = auto()
    document_archived = auto()
    document_deleted = auto()
    document_classified = auto()
    document_reviewed = auto()
    document_approved = auto()
    document_rejected = auto()
    extraction_completed = auto()
    governance_breach = auto()
    preservation_completed = auto()
    fhir_resource_created = auto()
    knowledge_graph_updated = auto()

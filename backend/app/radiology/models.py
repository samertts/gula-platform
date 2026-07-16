from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)

from app._compat import UTC
from app.radiology.base import RadiologyBaseEntity
from app.radiology.enums import (
    AnnotationType,
    ArchiveTier,
    ContrastType,
    CriticalFindingStatus,
    DeviceStatus,
    ExamStatus,
    ImageQuality,
    ModalityType,
    ProtocolType,
    ReportStatus,
    SharingType,
    StorageCompressionType,
)

# ==============================================================================
# Workflow Models
# ==============================================================================


class RadiologyOrder(RadiologyBaseEntity):
    __tablename__ = "radiology_orders"

    patient_id = Column(String(26), nullable=False, index=True)
    encounter_id = Column(String(26), nullable=True, index=True)
    ordering_provider_id = Column(String(26), nullable=True)
    order_number = Column(String(64), unique=True, nullable=False, index=True)
    modality = Column(Enum(ModalityType), nullable=False)
    body_part = Column(String(128), nullable=True)
    clinical_indication = Column(Text, nullable=True)
    diagnosis_code = Column(String(32), nullable=True)
    diagnosis_system = Column(String(32), nullable=True)
    priority = Column(String(16), default="routine")
    status = Column(String(20), default="pending")
    requested_date = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    scheduled_date = Column(DateTime(timezone=True), nullable=True)
    ordering_department_id = Column(String(26), nullable=True)
    notes = Column(Text, nullable=True)
    metadata = Column(JSON, default=dict)


class RadiologyAppointment(RadiologyBaseEntity):
    __tablename__ = "radiology_appointments"

    order_id = Column(String(26), ForeignKey("radiology_orders.id"), nullable=False, index=True)
    patient_id = Column(String(26), nullable=False, index=True)
    scheduled_date = Column(DateTime(timezone=True), nullable=False)
    scheduled_time = Column(String(8), nullable=True)
    duration_minutes = Column(Integer, default=30)
    modality = Column(Enum(ModalityType), nullable=False)
    room = Column(String(64), nullable=True)
    technologist_id = Column(String(26), nullable=True)
    status = Column(String(20), default="scheduled")
    preparation_instructions = Column(Text, nullable=True)
    contrast_required = Column(Boolean, default=False)
    contrast_details = Column(String(256), nullable=True)
    arrival_time = Column(DateTime(timezone=True), nullable=True)
    check_in_time = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    metadata = Column(JSON, default=dict)


class Protocol(RadiologyBaseEntity):
    __tablename__ = "radiology_protocols"

    code = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(256), nullable=False)
    name_ar = Column(String(256), nullable=True)
    modality = Column(Enum(ModalityType), nullable=False)
    body_part = Column(String(128), nullable=True)
    protocol_type = Column(Enum(ProtocolType), default=ProtocolType.STANDARD)
    contrast_protocol = Column(String(256), nullable=True)
    typical_duration = Column(Integer, nullable=True)
    typical_dose = Column(String(64), nullable=True)
    preparation_instructions = Column(Text, nullable=True)
    positioning_instructions = Column(Text, nullable=True)
    series_parameters = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    metadata = Column(JSON, default=dict)


# ==============================================================================
# Exam Models
# ==============================================================================


class RadiologyExam(RadiologyBaseEntity):
    __tablename__ = "radiology_exams"

    order_id = Column(String(26), ForeignKey("radiology_orders.id"), nullable=True, index=True)
    appointment_id = Column(String(26), ForeignKey("radiology_appointments.id"), nullable=True)
    patient_id = Column(String(26), nullable=False, index=True)
    accession_number = Column(String(64), unique=True, nullable=False, index=True)
    modality = Column(Enum(ModalityType), nullable=False)
    body_part = Column(String(128), nullable=True)
    laterality = Column(String(8), nullable=True)
    protocol_id = Column(String(26), ForeignKey("radiology_protocols.id"), nullable=True)
    status = Column(Enum(ExamStatus), default=ExamStatus.SCHEDULED, nullable=False)
    exam_code = Column(String(32), nullable=True)
    exam_name = Column(String(256), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    technologist_id = Column(String(26), nullable=True)
    radiologist_id = Column(String(26), nullable=True)
    contrast_used = Column(Boolean, default=False)
    contrast_type = Column(Enum(ContrastType), nullable=True)
    contrast_amount_ml = Column(Float, nullable=True)
    contrast_batch = Column(String(64), nullable=True)
    total_dose = Column(Float, nullable=True)
    dose_unit = Column(String(16), nullable=True)
    images_count = Column(Integer, default=0)
    series_count = Column(Integer, default=0)
    image_quality = Column(Enum(ImageQuality), nullable=True)
    notes = Column(Text, nullable=True)
    metadata = Column(JSON, default=dict)


class RadiologySeries(RadiologyBaseEntity):
    __tablename__ = "radiology_series"

    exam_id = Column(String(26), ForeignKey("radiology_exams.id"), nullable=False, index=True)
    series_instance_uid = Column(String(128), unique=True, nullable=False, index=True)
    series_number = Column(Integer, nullable=True)
    series_description = Column(String(256), nullable=True)
    modality = Column(Enum(ModalityType), nullable=False)
    body_part = Column(String(128), nullable=True)
    laterality = Column(String(8), nullable=True)
    protocol_name = Column(String(128), nullable=True)
    image_count = Column(Integer, default=0)
    manufacturer = Column(String(128), nullable=True)
    device_model = Column(String(128), nullable=True)
    acquisition_date = Column(DateTime(timezone=True), nullable=True)
    kvp = Column(Float, nullable=True)
    mas = Column(Float, nullable=True)
    slice_thickness = Column(Float, nullable=True)
    fov = Column(String(32), nullable=True)
    matrix_size = Column(String(32), nullable=True)
    metadata = Column(JSON, default=dict)


class RadiologyImage(RadiologyBaseEntity):
    __tablename__ = "radiology_images"

    series_id = Column(String(26), ForeignKey("radiology_series.id"), nullable=False, index=True)
    sop_instance_uid = Column(String(128), unique=True, nullable=False, index=True)
    instance_number = Column(Integer, nullable=True)
    image_type = Column(String(64), nullable=True)
    laterality = Column(String(8), nullable=True)
    view_position = Column(String(32), nullable=True)
    acquisition_date = Column(DateTime(timezone=True), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    file_format = Column(String(16), default="dcm")
    storage_path = Column(String(512), nullable=False)
    storage_tier = Column(Enum(ArchiveTier), default=ArchiveTier.HOT)
    checksum = Column(String(128), nullable=True)
    metadata = Column(JSON, default=dict)


class ImageAnnotation(RadiologyBaseEntity):
    __tablename__ = "radiology_image_annotations"

    image_id = Column(String(26), ForeignKey("radiology_images.id"), nullable=False, index=True)
    exam_id = Column(String(26), ForeignKey("radiology_exams.id"), nullable=False, index=True)
    annotated_by = Column(String(26), nullable=False)
    annotation_type = Column(Enum(AnnotationType), nullable=False)
    annotation_data = Column(JSON, nullable=False)
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)


class ImageMeasurement(RadiologyBaseEntity):
    __tablename__ = "radiology_image_measurements"

    image_id = Column(String(26), ForeignKey("radiology_images.id"), nullable=False, index=True)
    exam_id = Column(String(26), ForeignKey("radiology_exams.id"), nullable=False, index=True)
    measured_by = Column(String(26), nullable=False)
    measurement_type = Column(String(64), nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String(32), nullable=False)
    location = Column(String(128), nullable=True)
    finding_code = Column(String(32), nullable=True)
    finding_description = Column(String(256), nullable=True)
    metadata = Column(JSON, default=dict)


# ==============================================================================
# Reporting Models
# ==============================================================================


class RadiologyReport(RadiologyBaseEntity):
    __tablename__ = "radiology_reports"

    exam_id = Column(String(26), ForeignKey("radiology_exams.id"), nullable=False, index=True)
    accession_number = Column(String(64), nullable=False, index=True)
    patient_id = Column(String(26), nullable=False, index=True)
    ordering_provider_id = Column(String(26), nullable=True)
    radiologist_id = Column(String(26), nullable=True, index=True)
    status = Column(Enum(ReportStatus), default=ReportStatus.DRAFT, nullable=False)
    clinical_indication = Column(Text, nullable=True)
    technique = Column(Text, nullable=True)
    comparison = Column(Text, nullable=True)
    findings = Column(Text, nullable=True)
    impression = Column(Text, nullable=True)
    conclusion = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=True)
    body_text = Column(Text, nullable=True)
    critical_finding = Column(Boolean, default=False)
    critical_finding_type = Column(String(64), nullable=True)
    critical_notification = Column(String(256), nullable=True)
    transcribed_by = Column(String(26), nullable=True)
    draft_at = Column(DateTime(timezone=True), nullable=True)
    preliminary_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    amended_at = Column(DateTime(timezone=True), nullable=True)
    version = Column(Integer, default=1)
    prior_report_id = Column(String(26), nullable=True)
    dictation_file = Column(String(256), nullable=True)
    metadata = Column(JSON, default=dict)


class CriticalFinding(RadiologyBaseEntity):
    __tablename__ = "radiology_critical_findings"

    exam_id = Column(String(26), ForeignKey("radiology_exams.id"), nullable=False, index=True)
    report_id = Column(String(26), ForeignKey("radiology_reports.id"), nullable=True)
    finding_type = Column(String(64), nullable=False)
    finding_description = Column(Text, nullable=False)
    notified_by = Column(String(26), nullable=True)
    notified_to = Column(String(26), nullable=True)
    notification_time = Column(DateTime(timezone=True), nullable=True)
    acknowledgement_time = Column(DateTime(timezone=True), nullable=True)
    acknowledged_by = Column(String(26), nullable=True)
    status = Column(Enum(CriticalFindingStatus), default=CriticalFindingStatus.PENDING, nullable=False)
    notes = Column(Text, nullable=True)
    metadata = Column(JSON, default=dict)


class ReportTemplate(RadiologyBaseEntity):
    __tablename__ = "radiology_report_templates"

    template_code = Column(String(64), unique=True, nullable=False, index=True)
    template_name = Column(String(256), nullable=False)
    template_name_ar = Column(String(256), nullable=True)
    modality = Column(Enum(ModalityType), nullable=True)
    body_part = Column(String(128), nullable=True)
    structured_template = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    metadata = Column(JSON, default=dict)


# ==============================================================================
# Device Models
# ==============================================================================


class ModalityDevice(RadiologyBaseEntity):
    __tablename__ = "radiology_modality_devices"

    device_id = Column(String(64), unique=True, nullable=False, index=True)
    device_name = Column(String(128), nullable=False)
    device_model = Column(String(128), nullable=True)
    manufacturer = Column(String(128), nullable=True)
    modality_type = Column(Enum(ModalityType), nullable=False)
    site_name = Column(String(128), nullable=True)
    department_id = Column(String(26), nullable=True)
    ip_address = Column(String(64), nullable=True)
    ae_title = Column(String(64), nullable=True)
    port = Column(Integer, nullable=True)
    dicom_protocol = Column(String(32), nullable=True)
    is_active = Column(Boolean, default=True)
    last_connection = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum(DeviceStatus), default=DeviceStatus.OFFLINE)
    software_version = Column(String(64), nullable=True)
    serial_number = Column(String(128), nullable=True)
    metadata = Column(JSON, default=dict)


class WorklistEntry(RadiologyBaseEntity):
    __tablename__ = "radiology_worklist_entries"

    modality_device_id = Column(String(26), ForeignKey("radiology_modality_devices.id"), nullable=True)
    exam_id = Column(String(26), ForeignKey("radiology_exams.id"), nullable=True)
    accession_number = Column(String(64), nullable=False, index=True)
    patient_id = Column(String(26), nullable=False)
    patient_name = Column(String(256), nullable=True)
    patient_sex = Column(String(8), nullable=True)
    patient_dob = Column(String(16), nullable=True)
    requested_procedure = Column(String(256), nullable=True)
    modality = Column(Enum(ModalityType), nullable=False)
    scheduled_step = Column(String(64), nullable=True)
    scheduled_datetime = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), default="scheduled")
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)
    metadata = Column(JSON, default=dict)


class MPPS(RadiologyBaseEntity):
    __tablename__ = "radiology_mpps"

    worklist_entry_id = Column(String(26), ForeignKey("radiology_worklist_entries.id"), nullable=True)
    exam_id = Column(String(26), ForeignKey("radiology_exams.id"), nullable=True)
    status = Column(String(20), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    performed_steps = Column(JSON, default=list)
    notes = Column(Text, nullable=True)
    metadata = Column(JSON, default=dict)


# ==============================================================================
# PACS Models
# ==============================================================================


class DICOMStorage(RadiologyBaseEntity):
    __tablename__ = "radiology_dicom_storage"

    sop_instance_uid = Column(String(128), unique=True, nullable=False, index=True)
    study_instance_uid = Column(String(128), nullable=False, index=True)
    series_instance_uid = Column(String(128), nullable=False, index=True)
    patient_id = Column(String(26), nullable=False, index=True)
    study_id = Column(String(64), nullable=True)
    modality = Column(Enum(ModalityType), nullable=False)
    body_part = Column(String(128), nullable=True)
    file_path = Column(String(512), nullable=False)
    file_size = Column(Integer, nullable=True)
    checksum = Column(String(128), nullable=True)
    storage_date = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    storage_tier = Column(Enum(ArchiveTier), default=ArchiveTier.HOT)
    compression_type = Column(Enum(StorageCompressionType), default=StorageCompressionType.NONE)
    retention_days = Column(Integer, nullable=True)
    is_archived = Column(Boolean, default=False)
    metadata = Column(JSON, default=dict)


class DICOMStudy(RadiologyBaseEntity):
    __tablename__ = "radiology_dicom_studies"

    study_instance_uid = Column(String(128), unique=True, nullable=False, index=True)
    patient_id = Column(String(26), nullable=False, index=True)
    accession_number = Column(String(64), nullable=True, index=True)
    study_date = Column(DateTime(timezone=True), nullable=True)
    study_description = Column(String(256), nullable=True)
    modality = Column(Enum(ModalityType), nullable=True)
    referring_physician = Column(String(256), nullable=True)
    number_of_series = Column(Integer, default=0)
    number_of_images = Column(Integer, default=0)
    storage_size_bytes = Column(Integer, default=0)
    storage_tier = Column(Enum(ArchiveTier), default=ArchiveTier.HOT)
    is_archived = Column(Boolean, default=False)
    metadata = Column(JSON, default=dict)


class ImageShare(RadiologyBaseEntity):
    __tablename__ = "radiology_image_shares"

    study_uid = Column(String(128), nullable=False, index=True)
    shared_by = Column(String(26), nullable=False)
    shared_with = Column(String(256), nullable=True)
    share_type = Column(Enum(SharingType), default=SharingType.LINK)
    access_code = Column(String(64), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    access_count = Column(Integer, default=0)
    metadata = Column(JSON, default=dict)

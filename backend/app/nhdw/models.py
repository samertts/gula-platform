from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import relationship

from app._compat import UTC

from .base import NHDWBaseEntity
from .enums import (
    AdmissionType,
    AlertSeverity,
    ClinicalTaskStatus,
    DischargeType,
    QueuePriority,
    QueueStatus,
    ShiftType,
)


class Admission(NHDWBaseEntity):
    __tablename__ = "nhdw_admissions"

    patient_id = Column(Integer, nullable=False, index=True)
    encounter_id = Column(String(64), nullable=True, index=True)
    hospital_id = Column(Integer, nullable=False, index=True)
    department_id = Column(Integer, nullable=False, index=True)
    room_id = Column(Integer, nullable=True, index=True)
    bed_id = Column(Integer, nullable=True, index=True)
    admission_type = Column(SAEnum(AdmissionType), nullable=False, index=True)
    admission_date = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    expected_discharge_date = Column(DateTime(timezone=True), nullable=True)
    discharge_date = Column(DateTime(timezone=True), nullable=True)
    discharge_type = Column(SAEnum(DischargeType), nullable=True)
    diagnosis = Column(Text, nullable=True)
    diagnosis_code = Column(String(50), nullable=True, index=True)
    diagnosis_system = Column(String(50), nullable=True)
    admitting_doctor_id = Column(Integer, nullable=True, index=True)
    referring_doctor_id = Column(Integer, nullable=True)
    insurance_id = Column(String(100), nullable=True)
    insurance_policy = Column(String(100), nullable=True)
    is_emergency = Column(Boolean, default=False, nullable=False)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    patient = relationship("Patient", foreign_keys=[patient_id])
    hospital = relationship("HospitalMaster", foreign_keys=[hospital_id])
    department = relationship("HospitalDepartment", foreign_keys=[department_id])
    room = relationship("Room", foreign_keys=[room_id])
    bed = relationship("Bed", foreign_keys=[bed_id])

    __table_args__ = (
        Index("ix_nhdw_admissions_patient", "patient_id"),
        Index("ix_nhdw_admissions_date", "admission_date"),
        Index("ix_nhdw_admissions_status_dept", "department_id"),
    )


class Discharge(NHDWBaseEntity):
    __tablename__ = "nhdw_discharges"

    admission_id = Column(String(26), ForeignKey("nhdw_admissions.id", ondelete="RESTRICT"), nullable=False, index=True)
    patient_id = Column(Integer, nullable=False, index=True)
    encounter_id = Column(String(64), nullable=True, index=True)
    discharge_date = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    discharge_type = Column(SAEnum(DischargeType), nullable=False, index=True)
    discharge_destination = Column(String(300), nullable=True)
    discharge_summary = Column(Text, nullable=True)
    medications_at_discharge = Column(JSON, nullable=True)
    follow_up_instructions = Column(Text, nullable=True)
    follow_up_date = Column(DateTime(timezone=True), nullable=True)
    follow_up_provider_id = Column(Integer, nullable=True)
    discharged_by = Column(Integer, nullable=False, index=True)
    mortality_review = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    admission = relationship("Admission", foreign_keys=[admission_id])
    patient = relationship("Patient", foreign_keys=[patient_id])

    __table_args__ = (
        Index("ix_nhdw_discharges_admission", "admission_id"),
        Index("ix_nhdw_discharges_date", "discharge_date"),
    )


class Transfer(NHDWBaseEntity):
    __tablename__ = "nhdw_transfers"

    patient_id = Column(Integer, nullable=False, index=True)
    from_department_id = Column(Integer, nullable=False, index=True)
    to_department_id = Column(Integer, nullable=False, index=True)
    from_room_id = Column(Integer, nullable=True)
    to_room_id = Column(Integer, nullable=True)
    from_bed_id = Column(Integer, nullable=True)
    to_bed_id = Column(Integer, nullable=True)
    from_doctor_id = Column(Integer, nullable=True)
    to_doctor_id = Column(Integer, nullable=True)
    reason = Column(String(500), nullable=False)
    clinical_summary = Column(JSON, nullable=True)
    transferred_by = Column(Integer, nullable=False)
    transfer_date = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    transfer_type = Column(String(50), nullable=True)
    status = Column(String(50), nullable=False, default="completed", index=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    patient = relationship("Patient", foreign_keys=[patient_id])

    __table_args__ = (
        Index("ix_nhdw_transfers_patient", "patient_id"),
        Index("ix_nhdw_transfers_date", "transfer_date"),
        Index("ix_nhdw_transfers_from_to", "from_department_id", "to_department_id"),
    )


class QueueEntry(NHDWBaseEntity):
    __tablename__ = "nhdw_queue_entries"

    patient_id = Column(Integer, nullable=False, index=True)
    encounter_id = Column(String(64), nullable=True, index=True)
    department_id = Column(Integer, nullable=False, index=True)
    clinic_id = Column(Integer, nullable=True, index=True)
    priority = Column(SAEnum(QueuePriority), nullable=False, default=QueuePriority.MEDIUM, index=True)
    queue_date = Column(Date, nullable=False, index=True)
    check_in_time = Column(DateTime(timezone=True), nullable=True)
    seen_time = Column(DateTime(timezone=True), nullable=True)
    completed_time = Column(DateTime(timezone=True), nullable=True)
    total_wait_minutes = Column(Integer, nullable=True)
    status = Column(SAEnum(QueueStatus), nullable=False, default=QueueStatus.WAITING, index=True)
    visit_reason = Column(String(300), nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    patient = relationship("Patient", foreign_keys=[patient_id])
    department = relationship("HospitalDepartment", foreign_keys=[department_id])
    clinic = relationship("Clinic", foreign_keys=[clinic_id])

    __table_args__ = (
        Index("ix_nhdw_queue_dept_date", "department_id", "queue_date"),
        Index("ix_nhdw_queue_patient", "patient_id"),
        Index("ix_nhdw_queue_status", "status"),
    )


class WaitingListEntry(NHDWBaseEntity):
    __tablename__ = "nhdw_waiting_list_entries"

    patient_id = Column(Integer, nullable=False, index=True)
    department_id = Column(Integer, nullable=False, index=True)
    procedure_code = Column(String(50), nullable=True, index=True)
    procedure_name = Column(String(300), nullable=True)
    priority = Column(SAEnum(QueuePriority), nullable=False, default=QueuePriority.MEDIUM, index=True)
    listed_date = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    clinical_urgency = Column(String(50), nullable=True)
    status = Column(String(50), nullable=False, default="active", index=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    patient = relationship("Patient", foreign_keys=[patient_id])
    department = relationship("HospitalDepartment", foreign_keys=[department_id])

    __table_args__ = (
        Index("ix_nhdw_waiting_patient", "patient_id"),
        Index("ix_nhdw_waiting_dept_status", "department_id", "status"),
    )


class ClinicalTask(NHDWBaseEntity):
    __tablename__ = "nhdw_clinical_tasks"

    patient_id = Column(Integer, nullable=False, index=True)
    encounter_id = Column(String(64), nullable=True, index=True)
    assigned_to = Column(Integer, nullable=False, index=True)
    assigned_by = Column(Integer, nullable=False)
    task_type = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=False)
    priority = Column(SAEnum(QueuePriority), nullable=False, default=QueuePriority.MEDIUM, index=True)
    status = Column(SAEnum(ClinicalTaskStatus), nullable=False, default=ClinicalTaskStatus.PENDING, index=True)
    due_date = Column(DateTime(timezone=True), nullable=True)
    scheduled_time = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    completed_by = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)
    is_recurring = Column(Boolean, default=False, nullable=False)
    recurrence_rule = Column(String(500), nullable=True)

    patient = relationship("Patient", foreign_keys=[patient_id])

    __table_args__ = (
        Index("ix_nhdw_tasks_patient", "patient_id"),
        Index("ix_nhdw_tasks_assigned", "assigned_to"),
        Index("ix_nhdw_tasks_status", "status"),
        Index("ix_nhdw_tasks_due", "due_date"),
    )


class WardRound(NHDWBaseEntity):
    __tablename__ = "nhdw_ward_rounds"

    patient_id = Column(Integer, nullable=False, index=True)
    encounter_id = Column(String(64), nullable=True, index=True)
    department_id = Column(Integer, nullable=False, index=True)
    lead_doctor_id = Column(Integer, nullable=False, index=True)
    round_date = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    participants = Column(JSON, nullable=True)
    clinical_summary = Column(Text, nullable=True)
    assessment = Column(Text, nullable=True)
    plan = Column(Text, nullable=True)
    medications_reviewed = Column(JSON, nullable=True)
    investigations_ordered = Column(JSON, nullable=True)
    follow_up_plan = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    patient = relationship("Patient", foreign_keys=[patient_id])
    department = relationship("HospitalDepartment", foreign_keys=[department_id])

    __table_args__ = (
        Index("ix_nhdw_rounds_patient", "patient_id"),
        Index("ix_nhdw_rounds_dept_date", "department_id", "round_date"),
    )


class CarePlan(NHDWBaseEntity):
    __tablename__ = "nhdw_care_plans"

    patient_id = Column(Integer, nullable=False, index=True)
    encounter_id = Column(String(64), nullable=True, index=True)
    diagnosis = Column(Text, nullable=True)
    goals = Column(JSON, nullable=True)
    interventions = Column(JSON, nullable=True)
    start_date = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    review_date = Column(DateTime(timezone=True), nullable=True)
    next_review_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), nullable=False, default="active", index=True)
    created_by = Column(Integer, nullable=False)
    approved_by = Column(Integer, nullable=True)
    care_team = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    patient = relationship("Patient", foreign_keys=[patient_id])

    __table_args__ = (
        Index("ix_nhdw_care_plans_patient", "patient_id"),
        # ix_nhdw_care_plans_status is auto-generated by index=True on status column
    )


class HospitalAlert(NHDWBaseEntity):
    __tablename__ = "nhdw_hospital_alerts"

    alert_type = Column(String(100), nullable=False, index=True)
    severity = Column(SAEnum(AlertSeverity), nullable=False, default=AlertSeverity.INFO, index=True)
    title = Column(String(300), nullable=False)
    title_ar = Column(String(300), nullable=True)
    description = Column(Text, nullable=True)
    source_department_id = Column(Integer, nullable=True, index=True)
    triggered_by = Column(Integer, nullable=False)
    patient_id = Column(Integer, nullable=True, index=True)
    is_resolved = Column(Boolean, default=False, nullable=False, index=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(Integer, nullable=True)
    acknowledged_by = Column(JSON, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    source_department = relationship("HospitalDepartment", foreign_keys=[source_department_id])
    patient = relationship("Patient", foreign_keys=[patient_id])

    __table_args__ = (
        Index("ix_nhdw_alerts_severity", "severity"),
        Index("ix_nhdw_alerts_type", "alert_type"),
    )


class HospitalMessage(NHDWBaseEntity):
    __tablename__ = "nhdw_hospital_messages"

    sender_id = Column(Integer, nullable=False, index=True)
    recipient_id = Column(Integer, nullable=False, index=True)
    subject = Column(String(300), nullable=False)
    body = Column(Text, nullable=False)
    priority = Column(String(20), nullable=False, default="normal", index=True)
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    department_id = Column(Integer, nullable=True, index=True)
    parent_message_id = Column(String(26), ForeignKey("nhdw_hospital_messages.id", ondelete="SET NULL"), nullable=True)
    has_attachments = Column(Boolean, default=False, nullable=False)
    metadata_ = Column("metadata", JSON, nullable=True)

    department = relationship("HospitalDepartment", foreign_keys=[department_id])
    parent = relationship("HospitalMessage", remote_side="HospitalMessage.id", foreign_keys=[parent_message_id])

    __table_args__ = (
        Index("ix_nhdw_messages_sender", "sender_id"),
        Index("ix_nhdw_messages_recipient", "recipient_id"),
        Index("ix_nhdw_messages_read", "is_read"),
    )


class TelemedicineSession(NHDWBaseEntity):
    __tablename__ = "nhdw_telemedicine_sessions"

    patient_id = Column(Integer, nullable=False, index=True)
    provider_id = Column(Integer, nullable=False, index=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    session_type = Column(String(50), nullable=False, default="video")
    platform = Column(String(100), nullable=True)
    meeting_url = Column(String(500), nullable=True)
    recording_url = Column(String(500), nullable=True)
    status = Column(String(50), nullable=False, default="scheduled", index=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    patient = relationship("Patient", foreign_keys=[patient_id])

    __table_args__ = (
        Index("ix_nhdw_telemed_patient", "patient_id"),
        Index("ix_nhdw_telemed_provider", "provider_id"),
        Index("ix_nhdw_telemed_scheduled", "scheduled_at"),
        Index("ix_nhdw_telemed_status", "status"),
    )


class ResourceSchedule(NHDWBaseEntity):
    __tablename__ = "nhdw_resource_schedules"

    resource_type = Column(String(100), nullable=False, index=True)
    resource_id = Column(Integer, nullable=False, index=True)
    scheduled_date = Column(Date, nullable=False, index=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(50), nullable=False, default="scheduled", index=True)
    booked_by = Column(Integer, nullable=True)
    booked_for_patient_id = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    booked_for_patient = relationship("Patient", foreign_keys=[booked_for_patient_id])

    __table_args__ = (
        Index("ix_nhdw_resource_type_date", "resource_type", "scheduled_date"),
        Index("ix_nhdw_resource_id", "resource_id"),
    )


class DashboardConfiguration(NHDWBaseEntity):
    __tablename__ = "nhdw_dashboard_configurations"

    user_id = Column(Integer, nullable=True, index=True)
    role = Column(String(50), nullable=True, index=True)
    department_id = Column(Integer, nullable=True, index=True)
    config_json = Column(JSON, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)

    __table_args__ = (
        Index("ix_nhdw_dashboard_user", "user_id"),
        Index("ix_nhdw_dashboard_role", "role"),
    )


class ShiftReport(NHDWBaseEntity):
    __tablename__ = "nhdw_shift_reports"

    department_id = Column(Integer, nullable=False, index=True)
    shift_type = Column(SAEnum(ShiftType), nullable=False, index=True)
    shift_date = Column(Date, nullable=False, index=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    report_author = Column(Integer, nullable=False)
    patient_count = Column(Integer, default=0)
    admissions_count = Column(Integer, default=0)
    discharges_count = Column(Integer, default=0)
    transfers_count = Column(Integer, default=0)
    critical_events = Column(JSON, nullable=True)
    staffing = Column(JSON, nullable=True)
    issues = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    department = relationship("HospitalDepartment", foreign_keys=[department_id])

    __table_args__ = (
        Index("ix_nhdw_shift_reports_dept_date", "department_id", "shift_date"),
        Index("ix_nhdw_shift_reports_shift", "shift_type"),
    )


__all__ = [
    "Admission",
    "CarePlan",
    "ClinicalTask",
    "DashboardConfiguration",
    "Discharge",
    "HospitalAlert",
    "HospitalMessage",
    "QueueEntry",
    "ResourceSchedule",
    "ShiftReport",
    "TelemedicineSession",
    "Transfer",
    "WaitingListEntry",
    "WardRound",
]
